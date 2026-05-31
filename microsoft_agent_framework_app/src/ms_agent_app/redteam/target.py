"""PyRIT `PromptTarget` adapter that calls a Microsoft Agent Framework `Agent`.

PyRIT (>=0.13) targets implement a single abstract coroutine,
`send_prompt_async(*, message: Message) -> list[Message]`. We pull the
user-visible text out of the inbound `MessagePiece`, forward it to
`agent.run(...)`, and wrap the reply with `construct_response_from_request`
so memory + identifiers stay consistent with PyRIT's bookkeeping.

`pyrit` is imported lazily so this module remains importable when the
optional `redteam` extra is not installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyrit.models import Message
    from pyrit.prompt_target import PromptTarget
else:
    try:
        from pyrit.prompt_target import PromptTarget
    except ImportError:  # pragma: no cover - pyrit is an optional extra
        PromptTarget = object  # type: ignore[assignment,misc]


class AgentFrameworkTarget(PromptTarget):  # type: ignore[misc]
    """Wrap an `agent_framework.Agent` instance as a PyRIT prompt target."""

    def __init__(self, agent: Any) -> None:
        super().__init__()
        self._agent = agent

    async def send_prompt_async(self, *, message: Message) -> list[Message]:
        from pyrit.models import construct_response_from_request

        # Enforce PromptTarget input contract before touching message payload.
        self._validate_request(message=message)
        request_piece = message.message_pieces[0]
        prompt_text = request_piece.converted_value

        result = await self._agent.run(prompt_text)
        reply_text = getattr(result, "text", "") or str(result)

        # Reuse request metadata so PyRIT memory/threading remains consistent.
        response = construct_response_from_request(
            request=request_piece,
            response_text_pieces=[reply_text],
        )
        return [response]
