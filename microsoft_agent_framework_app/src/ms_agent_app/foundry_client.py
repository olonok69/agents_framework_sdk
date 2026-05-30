from __future__ import annotations

from agent_framework.foundry import FoundryChatClient
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
        kwargs["additionally_allowed_tenants"] = [settings.azure_tenant_id]
    credential = DefaultAzureCredential(**kwargs)

    return FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.foundry_model_deployment_name,
        credential=credential,
    )
