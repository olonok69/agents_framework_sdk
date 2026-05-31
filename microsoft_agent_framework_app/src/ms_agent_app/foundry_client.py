"""Provider-specific chat client builders.

Each helper maps validated `Settings` into a concrete client from
`agent_framework` so higher layers can remain provider-agnostic.
"""

from __future__ import annotations

from typing import Any

from agent_framework.anthropic import AnthropicClient
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatClient
from azure.identity import DefaultAzureCredential

from .config import Settings


def build_foundry_client(settings: Settings) -> FoundryChatClient:
    """Create a FoundryChatClient using DefaultAzureCredential.

    DefaultAzureCredential walks a credential chain — service principal env vars
    (AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET) take precedence,
    falling back to `az login` and other sources when those are absent. This lets
    the same code run in headless shells (CI, WSL without az CLI) and on dev
    laptops without code changes.
    """
    kwargs: dict = {"exclude_interactive_browser_credential": True}
    if settings.azure_tenant_id:
        # Restrict token acquisition to the configured tenant when provided.
        kwargs["additionally_allowed_tenants"] = [settings.azure_tenant_id]
    credential = DefaultAzureCredential(**kwargs)

    return FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.foundry_model_deployment_name,
        credential=credential,
    )


def build_openai_client(settings: Settings) -> OpenAIChatClient:
    """Create an OpenAIChatClient targeting the OpenAI API."""
    # Preserve backward compatibility with either OPENAI_CHAT_MODEL or OPENAI_MODEL.
    model = settings.openai_chat_model or settings.openai_model
    return OpenAIChatClient(
        model=model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def build_azure_openai_client(settings: Settings) -> OpenAIChatClient:
    """Create an OpenAIChatClient configured for Azure OpenAI routing."""
    # Support both new and legacy variable names for Azure model deployment.
    model = settings.azure_openai_chat_model or settings.azure_openai_model
    kwargs: dict[str, Any] = {
        "model": model,
        "azure_endpoint": settings.azure_openai_endpoint,
        "api_version": settings.azure_openai_api_version,
    }
    if settings.azure_openai_api_key:
        # Prefer explicit API key when configured.
        kwargs["api_key"] = settings.azure_openai_api_key
    else:
        # Fall back to Azure identity chain for local/dev and managed environments.
        kwargs["credential"] = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    return OpenAIChatClient(**kwargs)


def build_anthropic_client(settings: Settings) -> AnthropicClient:
    """Create an AnthropicClient targeting Anthropic-hosted models."""
    return AnthropicClient(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_chat_model,
        base_url=settings.anthropic_base_url,
    )


def build_chat_client(settings: Settings, provider: str | None = None):
    """Build a chat client for the requested provider.

    Supported providers: foundry, openai, azure-openai, anthropic.
    """
    # Keep one dispatch point so all callers share provider routing behavior.
    selected = provider or settings.model_provider
    if selected == "foundry":
        return build_foundry_client(settings)
    if selected == "openai":
        return build_openai_client(settings)
    if selected == "azure-openai":
        return build_azure_openai_client(settings)
    if selected == "anthropic":
        return build_anthropic_client(settings)
    raise ValueError(f"Unsupported provider: {selected}")
