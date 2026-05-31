"""Unit tests for evaluation message normalization and trajectory recording."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from ms_agent_app.eval.runner import Trajectory, to_query_messages, to_response_messages


def test_to_query_messages_wraps_text_in_openai_schema():
    """User text should be wrapped in evaluator-compatible query schema."""
    msgs = to_query_messages("hello there")
    assert msgs == [{"role": "user", "content": [{"type": "text", "text": "hello there"}]}]


def test_to_response_messages_handles_plain_text():
    """Plain assistant text should produce one assistant text content item."""
    msgs = to_response_messages(text="hi back", tool_calls=[])
    assert msgs == [{"role": "assistant", "content": [{"type": "text", "text": "hi back"}]}]


def test_to_response_messages_includes_tool_calls():
    """Tool call metadata should be included alongside final assistant text."""
    msgs = to_response_messages(
        text="done",
        tool_calls=[{"tool_name": "finance_tools.dual_ma", "arguments": {"symbol": "AAPL"}}],
    )
    # One assistant message should contain both tool-call events and final text.
    assert msgs[0]["role"] == "assistant"
    assert any(c["type"] == "tool_call" for c in msgs[0]["content"])
    assert any(c["type"] == "text" for c in msgs[0]["content"])


@pytest.mark.asyncio
async def test_trajectory_records_run():
    """Trajectory.record should capture assistant text and empty tool calls."""
    fake_agent = SimpleNamespace(
        run=AsyncMock(
            return_value=SimpleNamespace(
                text="42",
                messages=[],
            )
        )
    )
    traj = Trajectory(case_id="t", prompt="what is 6*7?")
    await traj.record(fake_agent)
    assert traj.response_text == "42"
    assert traj.tool_calls == []
    assert traj.query_messages[0]["role"] == "user"
    assert traj.response_messages[0]["role"] == "assistant"


@pytest.mark.asyncio
async def test_trajectory_extracts_tool_calls_from_messages():
    """Mirrors the real AgentResponse shape: tool calls live in
    result.messages[*].contents[*] on assistant messages, with `call_id`,
    `name`, and JSON-string `arguments`."""
    tool_call_content = SimpleNamespace(
        call_id="call_abc",
        name="analyze_dual_ma_strategy",
        arguments='{"symbol":"AAPL","period":"2y"}',
    )
    final_text_content = SimpleNamespace(text="Here are the results...")
    fake_response = SimpleNamespace(
        text="Here are the results...",
        messages=[
            SimpleNamespace(role="assistant", contents=[tool_call_content]),
            SimpleNamespace(role="tool", contents=[SimpleNamespace(call_id="call_abc")]),
            SimpleNamespace(role="assistant", contents=[final_text_content]),
        ],
    )
    # Simulate real agent output shape, then assert normalized extraction.
    fake_agent = SimpleNamespace(run=AsyncMock(return_value=fake_response))

    traj = Trajectory(case_id="t", prompt="Run dual MA on AAPL")
    await traj.record(fake_agent)

    assert len(traj.tool_calls) == 1
    call = traj.tool_calls[0]
    assert call["id"] == "call_abc"
    assert call["tool_name"] == "analyze_dual_ma_strategy"
    assert call["arguments"] == {"symbol": "AAPL", "period": "2y"}
