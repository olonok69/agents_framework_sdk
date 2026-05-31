"""Unit tests for agent construction and provider override behavior."""

from unittest.mock import MagicMock, patch

from ms_agent_app.agent_factory import build_chat_agent
from ms_agent_app.config import Settings


def _stub_settings(monkeypatch):
    """Provide minimal valid Foundry settings for agent-factory tests."""
    monkeypatch.setenv("MODEL_PROVIDER", "foundry")
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    # Keep fixture independent from developer-local .env contents.
    return Settings(_env_file=None)


def test_build_chat_agent_uses_foundry_client(monkeypatch):
    """Ensure default construction wires Foundry client into Agent."""
    settings = _stub_settings(monkeypatch)
    with (
        patch("ms_agent_app.agent_factory.build_chat_client") as client_builder,
        patch("ms_agent_app.agent_factory.Agent") as agent_mock,
    ):
        foundry_instance = MagicMock()
        # Patch the exact symbol used by build_chat_agent.
        client_builder.return_value = foundry_instance
        agent_mock.return_value = MagicMock()

        agent = build_chat_agent(settings, name="TestAgent", instructions="hi")

        # Validate both client construction and agent wiring contract.
        client_builder.assert_called_once_with(settings, provider="foundry")
        agent_mock.assert_called_once()
        _, agent_kwargs = agent_mock.call_args
        assert agent_kwargs["name"] == "TestAgent"
        assert agent_kwargs["instructions"] == "hi"
        assert agent_kwargs["client"] is foundry_instance
        assert agent is agent_mock.return_value


def test_build_chat_agent_allows_provider_override(monkeypatch):
    """Ensure explicit provider override is passed to client builder."""
    settings = _stub_settings(monkeypatch)
    with (
        patch("ms_agent_app.agent_factory.build_chat_client") as client_builder,
        patch("ms_agent_app.agent_factory.Agent") as agent_mock,
    ):
        client_instance = MagicMock()
        client_builder.return_value = client_instance
        agent_mock.return_value = MagicMock()

        build_chat_agent(settings, provider="openai", instructions="hi")

        # Provider override should flow through to chat-client dispatch.
        client_builder.assert_called_once_with(settings, provider="openai")
        _, agent_kwargs = agent_mock.call_args
        assert agent_kwargs["client"] is client_instance
        assert agent_kwargs["name"] == "OpenaiAgent"
