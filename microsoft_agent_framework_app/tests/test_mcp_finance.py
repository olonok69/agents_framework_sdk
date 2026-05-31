"""Unit tests for MCP finance tool construction and validation behavior."""

from pathlib import Path
from unittest.mock import patch

from ms_agent_app.config import Settings
from ms_agent_app.mcp_finance import build_finance_mcp_tool


def _settings(monkeypatch, tmp_path: Path) -> Settings:
    """Create valid test settings including a temporary MCP server script."""
    server = tmp_path / "main.py"
    server.write_text("# stub server")
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    monkeypatch.setenv("MCP_FINANCE_SERVER_PATH", str(server))
    monkeypatch.setenv("MCP_FINANCE_PYTHON", "/usr/bin/python3")
    return Settings()


def test_build_finance_mcp_tool_uses_configured_command(monkeypatch, tmp_path):
    """MCPStdioTool should be created with configured python and script path."""
    settings = _settings(monkeypatch, tmp_path)
    with patch("ms_agent_app.mcp_finance.MCPStdioTool") as ToolMock:
        tool = build_finance_mcp_tool(settings)
        # Ensure subprocess command-line is sourced from Settings.
        ToolMock.assert_called_once()
        _, kwargs = ToolMock.call_args
        assert kwargs["name"] == "finance_tools"
        assert kwargs["command"] == "/usr/bin/python3"
        assert kwargs["args"] == [str(settings.mcp_finance_server_path)]
        assert tool is ToolMock.return_value


def test_build_finance_mcp_tool_requires_server_path(monkeypatch):
    """Tool creation should fail when MCP_FINANCE_SERVER_PATH is missing."""
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://x/api/projects/p")
    monkeypatch.setenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    monkeypatch.delenv("MCP_FINANCE_SERVER_PATH", raising=False)
    import pytest

    # Use _env_file=None so pydantic-settings does not re-read the on-disk .env,
    # which may contain MCP_FINANCE_SERVER_PATH even after monkeypatch.delenv.
    with pytest.raises(ValueError):
        build_finance_mcp_tool(Settings(_env_file=None))
