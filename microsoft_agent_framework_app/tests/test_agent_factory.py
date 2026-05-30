from unittest.mock import MagicMock, patch

from ms_agent_app.agent_factory import build_chat_agent
from ms_agent_app.config import Settings


def _stub_settings(monkeypatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    return Settings()


def test_build_chat_agent_uses_foundry_client(monkeypatch):
    settings = _stub_settings(monkeypatch)
    with (
        patch("ms_agent_app.foundry_client.FoundryChatClient") as foundry_mock,
        patch("ms_agent_app.foundry_client.DefaultAzureCredential") as cred_mock,
        patch("ms_agent_app.agent_factory.Agent") as agent_mock,
    ):
        foundry_instance = MagicMock()
        foundry_mock.return_value = foundry_instance
        cred_mock.return_value = MagicMock()
        agent_mock.return_value = MagicMock()

        agent = build_chat_agent(settings, name="TestAgent", instructions="hi")

        foundry_mock.assert_called_once()
        _, foundry_kwargs = foundry_mock.call_args
        assert foundry_kwargs["project_endpoint"] == "https://x/api/projects/p"
        assert foundry_kwargs["model"] == "gpt-4.1"
        agent_mock.assert_called_once()
        _, agent_kwargs = agent_mock.call_args
        assert agent_kwargs["name"] == "TestAgent"
        assert agent_kwargs["instructions"] == "hi"
        assert agent_kwargs["client"] is foundry_instance
        assert agent is agent_mock.return_value
