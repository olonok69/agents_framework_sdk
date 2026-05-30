from __future__ import annotations

from typing import Optional, Dict, Any

from google.genai import types  # type: ignore
from google.adk.agents import Agent  # type: ignore
from google.adk.sessions import InMemorySessionService  # type: ignore
from google.adk.runners import Runner  # type: ignore


class AgentCaller:
    """Wrap ADK runner/session interactions for reusable agent calls."""

    def __init__(self, agent: Agent, runner: Runner, user_id: str, session_id: str):
        """Initialize instance state."""

        self.agent = agent
        self.runner = runner
        self.user_id = user_id
        self.session_id = session_id

    async def call(self, query: str) -> str:
        """Implement call."""

        content = types.Content(role="user", parts=[types.Part(text=query)])
        final_response_text = "Agent did not produce a final response."

        async for event in self.runner.run_async(
            user_id=self.user_id, session_id=self.session_id, new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                if event.author == self.agent.name:
                    break

        return final_response_text


async def make_agent_caller(agent: Agent, initial_state: Optional[Dict[str, Any]] = None) -> AgentCaller:
    """Create agent caller."""

    initial_state = initial_state or {}
    session_service = InMemorySessionService()
    app_name = f"{agent.name}_app"
    user_id = f"{agent.name}_user"
    session_id = f"{agent.name}_session_01"

    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state,
    )

    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    return AgentCaller(agent, runner, user_id, session_id)
