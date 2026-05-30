from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_provider: Literal["foundry", "openai", "azure-openai", "anthropic"] = Field(
        "foundry", alias="MODEL_PROVIDER"
    )

    foundry_project_endpoint: str | None = Field(None, alias="FOUNDRY_PROJECT_ENDPOINT")
    foundry_model_deployment_name: str | None = Field(None, alias="FOUNDRY_MODEL_DEPLOYMENT_NAME")
    azure_tenant_id: str | None = Field(None, alias="AZURE_TENANT_ID")

    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    openai_chat_model: str | None = Field(None, alias="OPENAI_CHAT_MODEL")
    openai_model: str | None = Field(None, alias="OPENAI_MODEL")
    openai_base_url: str | None = Field(None, alias="OPENAI_BASE_URL")

    azure_openai_endpoint: str | None = Field(None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_chat_model: str | None = Field(None, alias="AZURE_OPENAI_CHAT_MODEL")
    azure_openai_model: str | None = Field(None, alias="AZURE_OPENAI_MODEL")
    azure_openai_api_key: str | None = Field(None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str | None = Field(None, alias="AZURE_OPENAI_API_VERSION")

    anthropic_api_key: str | None = Field(None, alias="ANTHROPIC_API_KEY")
    anthropic_chat_model: str | None = Field(None, alias="ANTHROPIC_CHAT_MODEL")
    anthropic_base_url: str | None = Field(None, alias="ANTHROPIC_BASE_URL")

    judge_provider: Literal["azure-openai", "openai"] = Field(
        "azure-openai", alias="JUDGE_PROVIDER"
    )
    judge_openai_api_key: str | None = Field(None, alias="JUDGE_OPENAI_API_KEY")
    judge_openai_model: str | None = Field(None, alias="JUDGE_OPENAI_MODEL")
    judge_openai_base_url: str | None = Field(None, alias="JUDGE_OPENAI_BASE_URL")
    judge_openai_organization: str | None = Field(None, alias="JUDGE_OPENAI_ORGANIZATION")

    mcp_finance_server_path: Path | None = Field(None, alias="MCP_FINANCE_SERVER_PATH")
    mcp_finance_python: str | None = Field(None, alias="MCP_FINANCE_PYTHON")

    azure_deployment_name: str | None = Field(None, alias="AZURE_DEPLOYMENT_NAME")
    azure_api_key: str | None = Field(None, alias="AZURE_API_KEY")
    azure_endpoint: str | None = Field(None, alias="AZURE_ENDPOINT")
    azure_api_version: str | None = Field("2024-12-01-preview", alias="AZURE_API_VERSION")

    @model_validator(mode="after")
    def _validate_model_provider_requirements(self):
        if self.model_provider == "foundry":
            missing = [
                name
                for name, val in (
                    ("FOUNDRY_PROJECT_ENDPOINT", self.foundry_project_endpoint),
                    ("FOUNDRY_MODEL_DEPLOYMENT_NAME", self.foundry_model_deployment_name),
                )
                if not val
            ]
        elif self.model_provider == "openai":
            missing = [
                name
                for name, val in (
                    ("OPENAI_API_KEY", self.openai_api_key),
                    (
                        "OPENAI_CHAT_MODEL or OPENAI_MODEL",
                        self.openai_chat_model or self.openai_model,
                    ),
                )
                if not val
            ]
        elif self.model_provider == "azure-openai":
            missing = [
                name
                for name, val in (
                    ("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint),
                    (
                        "AZURE_OPENAI_CHAT_MODEL or AZURE_OPENAI_MODEL",
                        self.azure_openai_chat_model or self.azure_openai_model,
                    ),
                )
                if not val
            ]
        else:
            missing = [
                name
                for name, val in (
                    ("ANTHROPIC_API_KEY", self.anthropic_api_key),
                    ("ANTHROPIC_CHAT_MODEL", self.anthropic_chat_model),
                )
                if not val
            ]

        if missing:
            raise ValueError(
                f"Missing env vars for MODEL_PROVIDER={self.model_provider}: {', '.join(missing)}"
            )
        return self

    @field_validator("mcp_finance_server_path", mode="before")
    @classmethod
    def _resolve_server_path(cls, v):
        if not v:
            return None
        return Path(v).expanduser().resolve()

    def mcp_python(self) -> str:
        """Interpreter for the MCP server subprocess; falls back to current sys.executable."""
        return self.mcp_finance_python or sys.executable
