from __future__ import annotations

from collections.abc import Iterable

from agent_framework import Agent

from .config import Settings
from .foundry_client import build_foundry_client

DEFAULT_INSTRUCTIONS = (
    "You are a careful, concise assistant. "
    "If the user's question is about markets, equities, or trading strategies, "
    "and tools are available, prefer calling a tool over guessing. "
    "If you cannot answer from tool results, say so plainly."
)


def build_chat_agent(
    settings: Settings,
    *,
    name: str = "FoundryAgent",
    instructions: str = DEFAULT_INSTRUCTIONS,
    tools: Iterable[object] | None = None,
) -> Agent:
    """Build an Agent bound to Azure AI Foundry. Tools are optional and may be passed
    per-call to `agent.run(...)` instead."""
    client = build_foundry_client(settings)
    kwargs: dict = {"client": client, "name": name, "instructions": instructions}
    if tools is not None:
        kwargs["tools"] = list(tools)
    return Agent(**kwargs)
