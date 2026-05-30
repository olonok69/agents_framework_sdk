from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    prompt: str
    expected_intent: str
    expects_tool_call: bool
    notes: str | None = None


CASES: tuple[EvalCase, ...] = (
    EvalCase(
        case_id="intent-direct",
        prompt="In one sentence, what is the Microsoft Agent Framework?",
        expected_intent="Definition / explanation of MS Agent Framework",
        expects_tool_call=False,
    ),
    EvalCase(
        case_id="tool-dual-ma",
        prompt="Run a dual moving average backtest on AAPL for the last 2 years.",
        expected_intent="Quantitative analysis using finance tools",
        expects_tool_call=True,
    ),
    EvalCase(
        case_id="tool-fundamentals",
        prompt="Give me the latest fundamental analysis snapshot for MSFT.",
        expected_intent="Fundamental analysis lookup",
        expects_tool_call=True,
    ),
    EvalCase(
        case_id="clarification",
        prompt="Help me with a strategy.",
        expected_intent="Ambiguous — agent should ask for clarification.",
        expects_tool_call=False,
        notes="Tests intent resolution under ambiguity.",
    ),
)
