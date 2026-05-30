import os
from functools import lru_cache

import streamlit as st
from dotenv import load_dotenv
from azure.identity import (  # Use interactive login to avoid silent failures
    InteractiveBrowserCredential,
    TokenCachePersistenceOptions,
)
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    SharepointAgentTool,
    SharepointGroundingToolParameters,
    ToolProjectConnection,
)


AGENT_NAME = os.getenv("SHAREPOINT_AGENT_NAME", "sharepoint-cli-agent")


def get_credential():
    # Interactive login reduces "InteractionRequired" errors vs silent broker flows.
    cache_opts = TokenCachePersistenceOptions(allow_unencrypted_storage=True)
    credential = InteractiveBrowserCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        token_cache_persistence_options=cache_opts,
    )

    # Force a one-time interactive login and cache the token.
    credential.get_token("https://management.azure.com/.default")
    return credential


@lru_cache(maxsize=1)
def get_clients():
    load_dotenv()
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

    if "credential" not in st.session_state:
        st.session_state.credential = get_credential()

    project_client = AIProjectClient(endpoint=endpoint, credential=st.session_state.credential)
    openai_client = project_client.get_openai_client()
    return project_client, openai_client


def get_sharepoint_connection_id(project_client):
    connection_name = os.environ["SHAREPOINT_PROJECT_CONNECTION_NAME"]
    sharepoint_connection = project_client.connections.get(connection_name)
    return sharepoint_connection.id


def build_sharepoint_agent(project_client, connection_id):
    sharepoint_tool = SharepointAgentTool(
        sharepoint_grounding_preview=SharepointGroundingToolParameters(
            project_connections=[
                ToolProjectConnection(project_connection_id=connection_id)
            ]
        )
    )

    agent = project_client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            instructions=(
                "You are a helpful agent that can use SharePoint tools to answer questions "
                "and perform tasks for the user. Keep answers concise unless more detail "
                "is requested. Always use the SharePoint tools to look up information in the user's " \
                "If nothing relevant encontered in SharePoint, politely inform the user that you could not find the information " \
                "instead of making up an answer."
            ),
            tools=[sharepoint_tool],
        ),
    )
    return agent


def get_or_create_agent(project_client):
    for agent in project_client.agents.list():
        if getattr(agent, "name", "") == AGENT_NAME:
            return agent

    connection_name = os.environ["SHAREPOINT_PROJECT_CONNECTION_NAME"]
    sharepoint_connection = project_client.connections.get(connection_name)
    return build_sharepoint_agent(project_client, sharepoint_connection.id)


def stream_agent_reply(openai_client, agent_name, user_input, placeholder):
    stream = openai_client.responses.create(
        stream=True,
        input=user_input,
        extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
    )

    collected = []
    for event in stream:
        if event.type == "response.output_text.delta":
            chunk = event.delta
            collected.append(chunk)
            placeholder.write("".join(collected))
        elif event.type == "response.completed":
            break
    return "".join(collected)


def render_chat_ui():
    st.set_page_config(page_title="SharePoint Agent Chat", page_icon="💬")
    st.title("SharePoint Agent Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    project_client, openai_client = get_clients()
    agent = get_or_create_agent(project_client)

    st.success(f"Connected to agent: {agent.name}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("Ask a question about your SharePoint documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            reply = stream_agent_reply(openai_client, agent.name, prompt, placeholder)

        st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    render_chat_ui()



