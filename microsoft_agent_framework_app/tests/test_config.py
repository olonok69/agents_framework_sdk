import pytest

from ms_agent_app.config import Settings


def test_settings_requires_foundry_endpoint(monkeypatch):
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", raising=False)
    # Use _env_file=None so pydantic-settings does not re-read the on-disk .env,
    # which may contain these vars even after monkeypatch.delenv.
    with pytest.raises(ValueError):
        Settings(_env_file=None)


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    s = Settings()
    assert s.foundry_project_endpoint == "https://x/api/projects/p"
    assert s.foundry_model_deployment_name == "gpt-4.1"


def test_mcp_server_path_resolves_relative(monkeypatch, tmp_path):
    server = tmp_path / "main.py"
    server.write_text("# stub")
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    monkeypatch.setenv("MCP_FINANCE_SERVER_PATH", str(server))
    s = Settings()
    assert s.mcp_finance_server_path == server
