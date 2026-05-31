"""Factory helpers for constructing the runtime chat Agent.

This module centralizes how the app instantiates `agent_framework.Agent` so
all entry points (CLI, eval, red-team) share the same defaults and provider
routing behavior.
"""

from __future__ import annotations

from collections.abc import Iterable

from agent_framework import Agent

from .config import Settings
from .foundry_client import build_chat_client

DEFAULT_INSTRUCTIONS = (
    "You are a careful, concise assistant. "
    "If the user's question is about markets, equities, or trading strategies, "
    "and tools are available, prefer calling a tool over guessing. "
    "If you cannot answer from tool results, say so plainly."
)


def build_chat_agent(
    settings: Settings,
    *,
    provider: str | None = None,
    name: str | None = None,
    instructions: str = DEFAULT_INSTRUCTIONS,
    tools: Iterable[object] | None = None,
) -> Agent:
    """Build an Agent bound to the selected model provider.

    Tools are optional and may be passed per-call to `agent.run(...)` instead.

    Args:
        settings: Loaded app settings from environment.
        provider: Optional provider override. If omitted, uses
            `settings.model_provider`.
        name: Optional agent name; defaults to a provider-derived name.
        instructions: System/developer style instructions for the agent.
        tools: Optional tool set attached at agent-construction time.

    Returns:
        A configured `agent_framework.Agent` instance.
    """
    # Allow runtime override while keeping env-configured provider as default.
    selected_provider = provider or settings.model_provider
    client = build_chat_client(settings, provider=selected_provider)
    agent_name = name or f"{selected_provider.title()}Agent"
    kwargs: dict = {"client": client, "name": agent_name, "instructions": instructions}
    if tools is not None:
        # Normalize iterables (generators/tuples) into a concrete list for Agent.
        kwargs["tools"] = list(tools)
    return Agent(**kwargs)
