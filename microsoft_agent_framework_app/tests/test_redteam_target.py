from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

pyrit = pytest.importorskip(
    "pyrit",
    reason="pyrit is an optional extra (install with `uv sync --extra redteam`)",
)

from pyrit.models import Message, MessagePiece  # noqa: E402
from pyrit.setup import IN_MEMORY, initialize_pyrit_async  # noqa: E402

from ms_agent_app.redteam.target import AgentFrameworkTarget  # noqa: E402


@pytest.fixture(autouse=True)
async def _init_pyrit_memory():
    await initialize_pyrit_async(IN_MEMORY)


def _user_msg(text: str) -> Message:
    return Message(message_pieces=[MessagePiece(role="user", original_value=text)])


async def test_target_forwards_prompt_and_wraps_reply():
    agent = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(text="ok reply")))
    target = AgentFrameworkTarget(agent)

    out = await target.send_prompt_async(message=_user_msg("hello"))

    agent.run.assert_awaited_once_with("hello")
    assert len(out) == 1
    piece = out[0].message_pieces[0]
    # PyRIT stores role as _role internally; check via the public accessor.
    assert piece._role == "assistant"
    assert piece.original_value == "ok reply"
