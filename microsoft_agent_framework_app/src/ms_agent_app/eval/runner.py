from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


def to_query_messages(text: str) -> list[dict[str, Any]]:
    return [{"role": "user", "content": [{"type": "text", "text": text}]}]


def to_response_messages(
    *,
    text: str,
    tool_calls: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    for call in tool_calls:
        content.append(
            {
                "type": "tool_call",
                "tool_call_id": call.get("id", call.get("tool_name", "tool_call")),
                "name": call.get("tool_name"),
                "arguments": call.get("arguments", {}),
            }
        )
    if text:
        content.append({"type": "text", "text": text})
    return [{"role": "assistant", "content": content}]


def _extract_tool_calls(result: Any) -> list[dict[str, Any]]:
    """Walk an Agent Framework `AgentResponse` and pull out tool calls.

    The Agent Framework places tool calls inside `result.messages[*].contents[*]`
    on assistant messages — each tool-call Content has `call_id`, `name`, and a
    JSON-string `arguments` field. There is no top-level `result.tool_calls`.
    """
    normalized: list[dict[str, Any]] = []
    for msg in getattr(result, "messages", None) or []:
        if getattr(msg, "role", None) != "assistant":
            continue
        for c in getattr(msg, "contents", None) or []:
            call_id = getattr(c, "call_id", None)
            name = getattr(c, "name", None)
            if not (call_id and name):
                continue
            args = getattr(c, "arguments", None)
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    pass
            normalized.append(
                {
                    "id": call_id,
                    "tool_name": name,
                    "arguments": args or {},
                }
            )
    return normalized


@dataclass
class Trajectory:
    case_id: str
    prompt: str
    response_text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    @property
    def query_messages(self) -> list[dict[str, Any]]:
        return to_query_messages(self.prompt)

    @property
    def response_messages(self) -> list[dict[str, Any]]:
        return to_response_messages(text=self.response_text, tool_calls=self.tool_calls)

    async def record(self, agent, *, tools=None) -> None:
        kwargs: dict[str, Any] = {}
        if tools is not None:
            kwargs["tools"] = tools
        result = await agent.run(self.prompt, **kwargs)
        self.response_text = getattr(result, "text", "") or str(result)
        self.tool_calls = _extract_tool_calls(result)
