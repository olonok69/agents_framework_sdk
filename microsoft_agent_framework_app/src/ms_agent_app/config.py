from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    foundry_project_endpoint: str = Field(..., alias="FOUNDRY_PROJECT_ENDPOINT")
    foundry_model_deployment_name: str = Field(..., alias="FOUNDRY_MODEL_DEPLOYMENT_NAME")
    azure_tenant_id: str | None = Field(None, alias="AZURE_TENANT_ID")

    mcp_finance_server_path: Path | None = Field(None, alias="MCP_FINANCE_SERVER_PATH")
    mcp_finance_python: str | None = Field(None, alias="MCP_FINANCE_PYTHON")

    azure_deployment_name: str | None = Field(None, alias="AZURE_DEPLOYMENT_NAME")
    azure_api_key: str | None = Field(None, alias="AZURE_API_KEY")
    azure_endpoint: str | None = Field(None, alias="AZURE_ENDPOINT")
    azure_api_version: str | None = Field("2024-12-01-preview", alias="AZURE_API_VERSION")

    @field_validator("mcp_finance_server_path", mode="before")
    @classmethod
    def _resolve_server_path(cls, v):
        if not v:
            return None
        return Path(v).expanduser().resolve()

    def mcp_python(self) -> str:
        """Interpreter for the MCP server subprocess; falls back to current sys.executable."""
        return self.mcp_finance_python or sys.executable
