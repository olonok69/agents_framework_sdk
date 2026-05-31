"""Unit tests for environment loading and provider-specific settings validation."""

import pytest

from ms_agent_app.config import Settings


def test_settings_requires_foundry_endpoint(monkeypatch):
    """Foundry provider should fail validation when endpoint/model are absent."""
    monkeypatch.setenv("MODEL_PROVIDER", "foundry")
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", raising=False)
    # Use _env_file=None so pydantic-settings does not re-read the on-disk .env,
    # which may contain these vars even after monkeypatch.delenv.
    with pytest.raises(ValueError):
        Settings(_env_file=None)


def test_settings_loads_from_env(monkeypatch):
    """Settings should load Foundry endpoint and deployment from environment."""
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    # Default constructor should consume environment and resolve aliases.
    s = Settings()
    assert s.foundry_project_endpoint == "https://x/api/projects/p"
    assert s.foundry_model_deployment_name == "gpt-4.1"


def test_mcp_server_path_resolves_relative(monkeypatch, tmp_path):
    """MCP path should be materialized as a resolved `Path` object."""
    server = tmp_path / "main.py"
    server.write_text("# stub")
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    monkeypatch.setenv("MCP_FINANCE_SERVER_PATH", str(server))
    s = Settings()
    assert s.mcp_finance_server_path == server


def test_settings_openai_provider_does_not_require_foundry(monkeypatch):
    """OpenAI provider path should not enforce Foundry-only variables."""
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_CHAT_MODEL", "gpt-4.1")
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", raising=False)

    # Disable .env loading so test observes only patched environment values.
    s = Settings(_env_file=None)
    assert s.model_provider == "openai"
    assert s.openai_chat_model == "gpt-4.1"


def test_settings_openai_provider_requires_key_and_model(monkeypatch):
    """OpenAI provider should fail without API key and model values."""
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_CHAT_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with pytest.raises(ValueError):
        Settings(_env_file=None)
