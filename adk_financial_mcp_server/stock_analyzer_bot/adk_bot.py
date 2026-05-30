"""Google ADK-based multi-agent stock analyzer orchestration."""
from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from google.adk.agents import Agent  # type: ignore
from litellm import completion  # type: ignore

from .adk_bridge import make_agent_caller
from .mcp_tools import (
    bollinger_fibonacci_analysis,
    bollinger_breakout_analysis,
    bollinger_zscore_rsi_strategy_analysis,
    bollinger_zscore_analysis,
    comprehensive_performance_report,
    dual_moving_average_analysis,
    earnings_momentum_analysis,
    fundamental_analysis_report,
    gap_fade_analysis,
    macd_donchian_analysis,
    multi_timeframe_analysis,
    overnight_gap_analysis,
    pairs_trading_analysis,
    statistical_arbitrage_analysis,
    trin_market_breadth_analysis,
    unified_market_scanner,
    vix_term_structure_analysis,
    volatility_regime_analysis,
)

DEFAULT_MODEL_ID = os.getenv("ADK_MODEL_ID", "gpt-4.1")
DEFAULT_MODEL_PROVIDER = os.getenv("ADK_MODEL_PROVIDER", "openai")
CATALOG_PATH = Path(__file__).resolve().parents[1] / "docs" / "analysis_strategy_catalog.json"
_ANALYSIS_ACTION_ALIASES = {
    "multi_sector": "multisector",
}


def _load_analysis_strategy_catalog() -> dict[str, Any]:
    """Load analysis strategy catalog."""

    try:
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"items": [], "guardrails": {}}


def _catalog_entry_for_analysis_type(analysis_type: str) -> dict[str, Any]:
    """Resolve entry for analysis type."""

    catalog = _load_analysis_strategy_catalog()
    resolved_action = _ANALYSIS_ACTION_ALIASES.get(analysis_type, analysis_type)
    for item in catalog.get("items", []):
        if isinstance(item, dict) and item.get("action") == resolved_action:
            guardrails = catalog.get("guardrails", {}).get(item.get("type", "analysis"), {})
            merged = dict(item)
            merged["guardrails"] = guardrails if isinstance(guardrails, dict) else {}
            return merged
    return {
        "action": resolved_action,
        "endpoint": f"/{resolved_action}",
        "type": "analysis",
        "guardrails": {},
    }


def _taxonomy_contract_block(entry: dict[str, Any]) -> str:
    """Build contract block."""

    guardrails = entry.get("guardrails", {}) if isinstance(entry.get("guardrails"), dict) else {}
    guardrail_lines = [f"- {k}: {v}" for k, v in guardrails.items()]
    guardrails_text = "\n".join(guardrail_lines) if guardrail_lines else "- none"
    return (
        "Taxonomy contract:\n"
        f"- action: {entry.get('action', 'unknown')}\n"
        f"- endpoint: {entry.get('endpoint', 'unknown')}\n"
        f"- type: {entry.get('type', 'analysis')}\n"
        "- reporting behavior must follow this type\n"
        "- output must be grounded on provided MCP metrics\n"
        "Guardrails:\n"
        f"{guardrails_text}"
    )


def _find_taxonomy_violations(report: str, entry: dict[str, Any], raw_tool_output: str) -> list[str]:
    """Find taxonomy violations."""

    issues: list[str] = []
    normalized_report = (report or "").lower()
    normalized_raw = (raw_tool_output or "").lower()
    report_type = str(entry.get("type", "analysis")).lower()

    if (
        ("cannot access" in normalized_report or "do not have direct access" in normalized_report)
        and normalized_raw
        and not ("error" in normalized_raw or "failed" in normalized_raw)
    ):
        issues.append("Report claims data-access limitation although MCP output contains data.")

    missing_metrics_claim_patterns = [
        "conversation does not include",
        "not provided in a retrievable form",
        "cannot be produced from the information provided",
        "no per-symbol strategy outputs",
    ]
    if (
        any(pattern in normalized_report for pattern in missing_metrics_claim_patterns)
        and normalized_raw
        and not ("error" in normalized_raw or "failed" in normalized_raw)
    ):
        issues.append("Report claims missing MCP metrics although MCP output contains scanner data.")

    if report_type == "analysis" and (
        "backtest" in normalized_report
        and "backtest" not in normalized_raw
        and "strategy total return" not in normalized_raw
    ):
        issues.append("Analysis output overstates itself as a backtest without supporting MCP evidence.")

    if report_type == "strategy" and not (
        "strategy" in normalized_report or "signal" in normalized_report or "drawdown" in normalized_report
    ):
        issues.append("Strategy output lacks explicit strategy/risk interpretation.")

    return issues


def _extract_mode_from_context(analysis_context: Optional[str]) -> Optional[str]:
    """Extract mode from context from the provided input."""

    normalized = (analysis_context or "").lower()
    if (
        "technical mode: strategy-driven" in normalized
        or "scanner mode: strategy-driven" in normalized
        or "multi-sector mode: strategy-driven" in normalized
        or "combined technical mode: strategy-driven" in normalized
    ):
        return "strategy"
    if (
        "technical mode: score-model-driven" in normalized
        or "scanner mode: score-model-driven" in normalized
        or "multi-sector mode: score-model-driven" in normalized
        or "combined technical mode: score-model-driven" in normalized
    ):
        return "score"
    return None


def _extract_mode_scope_from_context(analysis_context: Optional[str]) -> Optional[str]:
    """Extract mode scope from context from the provided input."""

    normalized = (analysis_context or "").lower()
    if "technical mode:" in normalized:
        return "Technical"
    if "scanner mode:" in normalized:
        return "Scanner"
    if "multi-sector mode:" in normalized:
        return "Multi-Sector"
    if "combined technical mode:" in normalized:
        return "Combined Technical"
    return None


def _extract_risk_profile_from_context(analysis_context: Optional[str]) -> Optional[str]:
    """Extract risk profile from context from the provided input."""

    match = re.search(r"risk profile:\s*(conservative|balanced|aggressive)", analysis_context or "", re.I)
    if not match:
        return None
    return match.group(1).lower()


def _with_mode_risk_header(report: str, analysis_context: Optional[str]) -> str:
    """Return content with mode risk header applied."""

    if not (report or "").strip() or not analysis_context:
        return report
    if re.search(r"^\s*>\s*Mode used:\s*", report, re.I):
        return report

    scope = _extract_mode_scope_from_context(analysis_context)
    mode = _extract_mode_from_context(analysis_context)
    risk_profile = _extract_risk_profile_from_context(analysis_context)

    labels = []
    if scope and mode:
        labels.append(f"{scope}={mode}")
    elif mode:
        labels.append(f"mode={mode}")
    if risk_profile:
        labels.append(f"risk={risk_profile}")

    if not labels:
        return report

    header = f"> Mode used: {' | '.join(labels)}"
    return f"{header}\n\n{report.lstrip()}"


def _find_technical_mode_violations(report: str, analysis_context: Optional[str]) -> list[str]:
    """Find technical mode violations."""

    mode = _extract_mode_from_context(analysis_context)
    if mode is None:
        return []

    normalized = (report or "").lower()
    issues: list[str] = []

    if mode == "strategy":
        if "strategy consensus" not in normalized:
            issues.append("Strategy mode report must include an Evidence subsection named 'Strategy Consensus'.")
        if "score synthesis" in normalized:
            issues.append("Strategy mode report must not include 'Score Synthesis'.")
        if "composite score" in normalized or "aggregate score" in normalized:
            issues.append("Strategy mode report must avoid composite/aggregate score framing.")

    if mode == "score":
        if "score synthesis" not in normalized:
            issues.append("Score mode report must include an Evidence subsection named 'Score Synthesis'.")
        if "strategy consensus" in normalized:
            issues.append("Score mode report must not include 'Strategy Consensus'.")
        if "strategy voting" in normalized:
            issues.append("Score mode report must avoid strategy-voting framing.")

    return issues


def _extract_metric(raw: str, label: str) -> str | None:
    """Extract metric from the provided input."""

    match = re.search(rf"{re.escape(label)}\s*:\s*([^\n\r]+)", raw)
    if not match:
        return None
    return match.group(1).strip()


def _format_macd_donchian_analysis_from_raw(
    raw: str,
    symbol: str,
    period: str,
    fast_period: int,
    slow_period: int,
    signal_period: int,
    window: int,
) -> str | None:
    """Format macd donchian analysis output from raw tool data."""

    if "PERFORMANCE COMPARISON: MACD-DONCHIAN" not in raw:
        return None

    strategy_return = _extract_metric(raw, "Strategy Total Return") or "N/A"
    buyhold_return = _extract_metric(raw, "Buy & Hold Return") or "N/A"
    excess_return = _extract_metric(raw, "Excess Return") or "N/A"
    strategy_sharpe = _extract_metric(raw, "Strategy Sharpe Ratio") or "N/A"
    buyhold_sharpe = _extract_metric(raw, "Buy & Hold Sharpe Ratio") or "N/A"
    strategy_drawdown = _extract_metric(raw, "Strategy Max Drawdown") or "N/A"
    buyhold_drawdown = _extract_metric(raw, "Buy & Hold Max Drawdown") or "N/A"
    total_trades = _extract_metric(raw, "Total Trades") or "N/A"
    win_rate = _extract_metric(raw, "Win Rate") or "N/A"
    avg_trade_return = _extract_metric(raw, "Average Return per Trade") or "N/A"
    current_signal = _extract_metric(raw, "Current Signal") or "N/A"
    macd_position = _extract_metric(raw, "MACD Position") or "N/A"
    donchian_position = _extract_metric(raw, "Donchian Position") or "N/A"
    recommendation = _extract_metric(raw, "Strategy Recommendation") or "N/A"
    verdict = _extract_metric(raw, "STRATEGY VERDICT") or "N/A"

    summary = (
        f"This report analyzes MACD-DONCHIAN strategy performance for {symbol.upper()} over {period} "
        f"using MACD({fast_period},{slow_period},{signal_period}) and Donchian window {window}. "
        f"The strategy return is {strategy_return} versus buy-and-hold {buyhold_return} "
        f"(excess {excess_return}). Current signal is {current_signal}."
    )


def _format_bollinger_fibonacci_analysis_from_raw(
    raw: str,
    symbol: str,
    period: str,
    window: int,
    num_std: int,
    window_swing_points: int,
) -> str | None:
    """Format bollinger fibonacci analysis output from raw tool data."""

    if "PERFORMANCE COMPARISON: BOLLINGER-FIBONACCI" not in raw:
        return None

    strategy_return = _extract_metric(raw, "Strategy Total Return") or "N/A"
    buyhold_return = _extract_metric(raw, "Buy & Hold Return") or "N/A"
    excess_return = _extract_metric(raw, "Excess Return") or "N/A"
    strategy_sharpe = _extract_metric(raw, "Strategy Sharpe Ratio") or "N/A"
    buyhold_sharpe = _extract_metric(raw, "Buy & Hold Sharpe Ratio") or "N/A"
    strategy_drawdown = _extract_metric(raw, "Strategy Max Drawdown") or "N/A"
    buyhold_drawdown = _extract_metric(raw, "Buy & Hold Max Drawdown") or "N/A"
    total_trades = _extract_metric(raw, "Total Trades") or "N/A"
    win_rate = _extract_metric(raw, "Win Rate") or "N/A"
    avg_trade_return = _extract_metric(raw, "Average Return per Trade") or "N/A"
    current_signal = _extract_metric(raw, "Current Signal") or "N/A"
    band_position = _extract_metric(raw, "Band Position") or "N/A"
    recommendation = _extract_metric(raw, "Strategy Recommendation") or "N/A"
    verdict = _extract_metric(raw, "STRATEGY VERDICT") or "N/A"

    summary = (
        f"This report analyzes BOLLINGER-FIBONACCI strategy performance for {symbol.upper()} over {period} "
        f"with Bollinger window={window}, std={num_std}, swing_window={window_swing_points}. "
        f"The strategy return is {strategy_return} versus buy-and-hold {buyhold_return} "
        f"(excess {excess_return}). Current signal is {current_signal}."
    )

    return (
        f"# Bollinger-Fibonacci Strategy Evaluation for {symbol.upper()} ({period})\n\n"
        "## Executive Summary\n\n"
        f"{summary}\n\n"
        "## Evidence\n\n"
        f"- Parameters: window={window}, num_std={num_std}, window_swing_points={window_swing_points}.\n"
        f"- Returns: strategy={strategy_return}, buy-and-hold={buyhold_return}, excess={excess_return}.\n"
        f"- Risk: Sharpe strategy={strategy_sharpe} vs buy-and-hold={buyhold_sharpe}; "
        f"max drawdown strategy={strategy_drawdown} vs buy-and-hold={buyhold_drawdown}.\n"
        f"- Trading stats: total trades={total_trades}, win rate={win_rate}, avg trade return={avg_trade_return}.\n"
        f"- Current state: signal={current_signal}, band position={band_position}.\n"
        f"- Tool verdict: {verdict}.\n\n"
        "## Risk & Guardrails\n\n"
        "- Validate robustness with transaction costs and slippage assumptions.\n"
        "- Re-test across different volatility regimes and symbols.\n"
        "- Watch for persistent overbought/oversold conditions in strong trends.\n\n"
        "## Recommendation\n\n"
        f"- Current action: {recommendation}.\n"
        "- Use this as a research signal and enforce portfolio risk limits before deployment.\n\n"
        "## Disclaimer\n\n"
        "This report is for informational purposes only and is not investment advice. "
        f"Data as of: {date.today().isoformat()}"
    )


def _format_dual_ma_analysis_from_raw(
    raw: str,
    symbol: str,
    period: str,
    short_period: int,
    long_period: int,
    ma_type: str,
) -> str | None:
    """Format dual ma analysis output from raw tool data."""

    if "DUAL MOVING AVERAGE ANALYSIS" not in raw:
        return None

    strategy_return = _extract_metric(raw, "Strategy Return") or "N/A"
    buyhold_return = _extract_metric(raw, "Buy & Hold Return") or "N/A"
    excess_return = _extract_metric(raw, "Excess Return") or "N/A"
    win_rate = _extract_metric(raw, "Win Rate") or "N/A"
    total_trades = _extract_metric(raw, "Total Trades") or "N/A"
    sharpe = _extract_metric(raw, "Sharpe Ratio") or "N/A"
    max_drawdown = _extract_metric(raw, "Max Drawdown") or "N/A"
    volatility = _extract_metric(raw, "Strategy Volatility") or "N/A"
    current_signal = _extract_metric(raw, "Current Signal") or "N/A"
    current_position = _extract_metric(raw, "Current Position") or "N/A"
    trend = _extract_metric(raw, "Trend") or "N/A"
    trend_strength = _extract_metric(raw, "Trend Strength") or "N/A"
    verdict = _extract_metric(raw, "STRATEGY VERDICT") or "N/A"

    summary = (
        f"This report analyzes DUAL MOVING AVERAGE strategy performance for {symbol.upper()} over {period} "
        f"using {ma_type.upper()}({short_period},{long_period}). Strategy return is {strategy_return} "
        f"versus buy-and-hold {buyhold_return} (excess {excess_return}). Current signal is {current_signal}."
    )

    return (
        f"# Dual Moving Average Strategy Evaluation for {symbol.upper()} ({period})\n\n"
        "## Executive Summary\n\n"
        f"{summary}\n\n"
        "## Evidence\n\n"
        f"- Parameters: ma_type={ma_type.upper()}, short_period={short_period}, long_period={long_period}.\n"
        f"- Returns: strategy={strategy_return}, buy-and-hold={buyhold_return}, excess={excess_return}.\n"
        f"- Risk: Sharpe={sharpe}, max drawdown={max_drawdown}, strategy volatility={volatility}.\n"
        f"- Trading stats: total trades={total_trades}, win rate={win_rate}.\n"
        f"- Current state: signal={current_signal}, position={current_position}, trend={trend}, trend_strength={trend_strength}.\n"
        f"- Tool verdict: {verdict}.\n\n"
        "## Risk & Guardrails\n\n"
        "- Long MA systems can lag in fast reversals and may underperform in sideways markets.\n"
        "- Test alternate windows only with out-of-sample validation to avoid overfitting.\n"
        "- Confirm transaction-cost sensitivity on higher turnover assets.\n\n"
        "## Recommendation\n\n"
        f"- Current action: {current_signal}.\n"
        "- Use as directional regime filter and combine with broader risk controls.\n\n"
        "## Disclaimer\n\n"
        "This report is for informational purposes only and is not investment advice. "
        f"Data as of: {date.today().isoformat()}"
    )


def _is_bad_adk_report(adk_report: str, raw_tool_output: str) -> bool:
    """Return whether bad adk report."""

    normalized = (adk_report or "").lower()
    bad_adk = "cannot access" in normalized or "do not have direct access" in normalized
    return bad_adk and bool(raw_tool_output)

    return (
        f"# MACD-Donchian Strategy Evaluation for {symbol.upper()} ({period})\n\n"
        "## Executive Summary\n\n"
        f"{summary}\n\n"
        "## Evidence\n\n"
        f"- Parameters: MACD fast={fast_period}, slow={slow_period}, signal={signal_period}; Donchian window={window}.\n"
        f"- Returns: strategy={strategy_return}, buy-and-hold={buyhold_return}, excess={excess_return}.\n"
        f"- Risk: Sharpe strategy={strategy_sharpe} vs buy-and-hold={buyhold_sharpe}; "
        f"max drawdown strategy={strategy_drawdown} vs buy-and-hold={buyhold_drawdown}.\n"
        f"- Trading stats: total trades={total_trades}, win rate={win_rate}, avg trade return={avg_trade_return}.\n"
        f"- Current state: signal={current_signal}, MACD position={macd_position}, "
        f"Donchian position={donchian_position}.\n"
        f"- Tool verdict: {verdict}.\n\n"
        "## Risk & Guardrails\n\n"
        "- Validate robustness with transaction costs/slippage sensitivity checks.\n"
        "- Re-test across additional symbols/time windows to reduce single-asset overfitting risk.\n"
        "- Monitor regime shifts where trend-following filters can underperform.\n\n"
        "## Recommendation\n\n"
        f"- Current action: {recommendation}.\n"
        "- Use this as a research signal; confirm with portfolio-level risk limits before deployment.\n\n"
        "## Disclaimer\n\n"
        "This report is for informational purposes only and is not investment advice. "
        f"Data as of: {date.today().isoformat()}"
    )


class AgenticFinancePipeline:
    """Coordinate ADK agent orchestration and guarded report generation."""

    def __init__(self, model_id: str = DEFAULT_MODEL_ID) -> None:
        """Initialize instance state."""

        self.model_id = model_id
        self.model_provider = os.getenv("ADK_MODEL_PROVIDER", DEFAULT_MODEL_PROVIDER)

    def _normalized_model(self) -> str:
        """Normalize d model values."""

        if "/" in self.model_id:
            return self.model_id
        if self.model_provider:
            return f"{self.model_provider}/{self.model_id}"
        return self.model_id

    def _fallback_run_agent(self, instruction: str, prompt: str) -> str:
        """Implement fallback run agent."""

        response = completion(
            model=self._normalized_model(),
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response["choices"][0]["message"]["content"]

    async def _run_agent(self, name: str, instruction: str, prompt: str) -> str:
        """Implement run agent."""

        try:
            agent = Agent(name=name, model=self.model_id, instruction=instruction)
            caller = await make_agent_caller(agent)
            return await caller.call(prompt)
        except Exception:
            return self._fallback_run_agent(instruction=instruction, prompt=prompt)

    async def execute(
        self,
        analysis_type: str,
        user_goal: str,
        raw_tool_output: str,
        analysis_context: Optional[str] = None,
    ) -> str:
        """Implement execute."""

        normalized_raw = (raw_tool_output or "").strip()
        if not normalized_raw:
            return "MCP tool returned no output."
        if normalized_raw.lower().startswith("error") or "Error calling" in normalized_raw:
            return normalized_raw

        as_of_date = date.today().isoformat()
        catalog_entry = _catalog_entry_for_analysis_type(analysis_type)
        taxonomy_contract = _taxonomy_contract_block(catalog_entry)

        context_block = (
            f"Analysis mode context:\n{analysis_context}\n\n" if analysis_context else ""
        )

        orchestrator_plan = await self._run_agent(
            name="orchestrator_agent",
            instruction=(
                "You are an orchestration agent for financial analysis. "
                "Create a short execution plan with: key objectives, risks to verify, and output structure."
            ),
            prompt=(
                f"Analysis type: {analysis_type}\n"
                f"User goal: {user_goal}\n\n"
                f"{context_block}"
                "When mode context is provided, include explicit checks for mode-specific constraints."
            ),
        )

        specialist_output = await self._run_agent(
            name="financial_specialist_agent",
            instruction=(
                "You are a senior financial specialist. Analyze the MCP tool output with market rigor. "
                "Extract signals, risks, confidence, and actionable implications. Use precise numeric references. "
                "Treat MCP output as authoritative data. If MCP output contains numeric metrics, quote them explicitly. "
                "Do NOT claim lack of historical data access unless MCP output explicitly says data retrieval failed. "
                "Strictly follow the provided taxonomy contract."
            ),
            prompt=(
                f"{taxonomy_contract}\n\n"
                f"{context_block}"
                f"Execution plan:\n{orchestrator_plan}\n\n"
                f"User goal:\n{user_goal}\n\n"
                f"MCP output:\n{raw_tool_output}"
            ),
        )

        critic_output = await self._run_agent(
            name="critic_guardrail_agent",
            instruction=(
                "You are a strict financial critic/guardrail agent. "
                "Identify unsupported claims, internal inconsistencies, and missing risk controls. "
                "Enforce taxonomy contract compliance (analysis vs strategy) and MCP-grounded claims. "
                "Return: PASS/FAIL, list of issues, and corrections."
            ),
            prompt=(
                f"{taxonomy_contract}\n\n"
                f"{context_block}"
                f"Plan:\n{orchestrator_plan}\n\n"
                f"Financial analysis draft:\n{specialist_output}\n\n"
                "Perform critical review."
            ),
        )

        final_report = await self._run_agent(
            name="reporting_specialist_agent",
            instruction=(
                "You are a reporting specialist. Produce a concise, professional markdown report. "
                "Include sections: Executive Summary, Evidence, Risk & Guardrails, Recommendation, Disclaimer. "
                "In Disclaimer, include a line exactly in this format: 'Data as of: YYYY-MM-DD'. "
                "Use ONLY the provided as-of date, do not invent or assume any other specific month/year/date. "
                "If MCP output includes performance metrics, include those values in Executive Summary and Evidence. "
                "Never state 'cannot access data' unless MCP output explicitly reports a retrieval/backtest error. "
                "Keep the analysis substantive: interpret what the metrics imply for risk-adjusted behavior, drawdown profile, and signal quality. "
                "Do not invent any metric not present in MCP output. "
                "If analysis mode context is provided, enforce it strictly and reflect its required output style. "
                "Strictly comply with taxonomy contract and guardrails."
            ),
            prompt=(
                f"{taxonomy_contract}\n\n"
                f"As-of date to use in disclaimer: {as_of_date}\n\n"
                f"{context_block}"
                f"User goal:\n{user_goal}\n\n"
                f"Orchestrator plan:\n{orchestrator_plan}\n\n"
                f"Financial specialist output:\n{specialist_output}\n\n"
                f"Critic output:\n{critic_output}\n\n"
                "Generate the final response and incorporate critic corrections."
            ),
        )
        violations = _find_taxonomy_violations(final_report, catalog_entry, raw_tool_output)
        if not violations:
            return final_report

        rewritten_report = await self._run_agent(
            name="taxonomy_guardrail_rewriter_agent",
            instruction=(
                "You are a deterministic guardrail rewriter. "
                "Rewrite the report so it complies with taxonomy contract and uses only MCP-grounded claims. "
                "Preserve markdown structure and keep it concise."
            ),
            prompt=(
                f"{taxonomy_contract}\n\n"
                f"Detected violations:\n- " + "\n- ".join(violations) + "\n\n"
                f"MCP output:\n{raw_tool_output}\n\n"
                f"Report to rewrite:\n{final_report}"
            ),
        )

        remaining_violations = _find_taxonomy_violations(rewritten_report, catalog_entry, raw_tool_output)
        if remaining_violations:
            issue_list = "\n".join([f"- {issue}" for issue in remaining_violations])
            return (
                "# Guardrail Enforcement Blocked\n\n"
                "## Executive Summary\n\n"
                "The response was blocked because taxonomy guardrails were violated.\n\n"
                "## Evidence\n\n"
                f"{issue_list}\n\n"
                "## Risk & Guardrails\n\n"
                "- Retry with stricter MCP-grounded drafting.\n"
                "- Avoid unsupported data-access or backtest claims.\n\n"
                "## Recommendation\n\n"
                "- Re-run the request; if this persists, inspect MCP raw output and prompt constraints.\n\n"
                "## Disclaimer\n\n"
                f"Data as of: {as_of_date}"
            )

        mode_violations = _find_technical_mode_violations(rewritten_report, analysis_context)
        if mode_violations:
            mode_rewritten_report = await self._run_agent(
                name="technical_mode_guardrail_rewriter_agent",
                instruction=(
                    "You are a deterministic technical-mode guardrail rewriter. "
                    "Rewrite the report to satisfy required mode-specific framing while keeping all claims MCP-grounded. "
                    "Preserve markdown quality and keep the same major sections."
                ),
                prompt=(
                    f"{taxonomy_contract}\n\n"
                    f"Mode context:\n{analysis_context or ''}\n\n"
                    f"Mode violations to fix:\n- " + "\n- ".join(mode_violations) + "\n\n"
                    f"MCP output:\n{raw_tool_output}\n\n"
                    f"Report to rewrite:\n{rewritten_report}"
                ),
            )

            mode_remaining_violations = _find_technical_mode_violations(mode_rewritten_report, analysis_context)
            if mode_remaining_violations:
                issue_list = "\n".join([f"- {issue}" for issue in mode_remaining_violations])
                return (
                    "# Guardrail Enforcement Blocked\n\n"
                    "## Executive Summary\n\n"
                    "The response was blocked because technical-mode guardrails were violated.\n\n"
                    "## Evidence\n\n"
                    f"{issue_list}\n\n"
                    "## Risk & Guardrails\n\n"
                    "- Retry with stricter mode-specific drafting.\n"
                    "- Ensure report structure aligns with selected technical mode.\n\n"
                    "## Recommendation\n\n"
                    "- Re-run the request; if this persists, inspect technical mode context and MCP raw output.\n\n"
                    "## Disclaimer\n\n"
                    f"Data as of: {as_of_date}"
                )

            return mode_rewritten_report

        return rewritten_report


def _run_pipeline_sync(
    analysis_type: str,
    user_goal: str,
    raw_tool_output: str,
    model_id: str,
    analysis_context: Optional[str] = None,
) -> str:
    """Implement run pipeline sync."""

    pipeline = AgenticFinancePipeline(model_id=model_id)
    report = asyncio.run(
        pipeline.execute(analysis_type, user_goal, raw_tool_output, analysis_context=analysis_context)
    )
    return _with_mode_risk_header(report, analysis_context)


def _technical_mode_context(mode: str, risk_profile: str) -> str:
    """Implement technical mode context."""

    risk_instructions = {
        "conservative": (
            "Prioritize capital preservation. Prefer HOLD unless confirmation is strong. "
            "Emphasize downside control, drawdown tolerance, and stricter invalidation triggers."
        ),
        "balanced": (
            "Balance opportunity and risk. Require moderate confirmation before directional bias shifts. "
            "Present both upside and downside conditions with neutral sizing language."
        ),
        "aggressive": (
            "Prioritize responsiveness to emerging signals while acknowledging higher whipsaw risk. "
            "Allow earlier directional framing but explicitly call out elevated drawdown/timing risk."
        ),
    }

    if mode == "strategy":
        return (
            "Technical mode: strategy-driven.\n"
            "Required behavior:\n"
            "- Base conclusions on standalone strategy outputs and cross-strategy agreement/conflict.\n"
            "- Include a subsection in Evidence named exactly: 'Strategy Consensus'.\n"
            "- In Recommendation, explicitly reference strategy alignment/disagreement.\n"
            "- Do not present the result as a composite scoring model.\n"
            f"Risk profile: {risk_profile}. {risk_instructions[risk_profile]}"
        )

    return (
        "Technical mode: score-model-driven.\n"
        "Required behavior:\n"
        "- Base conclusions on synthesized indicator/score evidence from comprehensive technical output.\n"
        "- Include a subsection in Evidence named exactly: 'Score Synthesis'.\n"
        "- In Recommendation, explicitly reference aggregate score quality/consistency of indicators.\n"
        "- Do not frame this as a strategy-voting report.\n"
        f"Risk profile: {risk_profile}. {risk_instructions[risk_profile]}"
    )


def _scanner_mode_context(mode: str, risk_profile: str) -> str:
    """Implement scanner mode context."""

    risk_suffix = {
        "conservative": "Prioritize downside resilience and ranking stability over aggressive signal chasing.",
        "balanced": "Balance opportunity ranking with downside control and robustness.",
        "aggressive": "Prioritize faster opportunity capture while explicitly acknowledging higher turnover and whipsaw risk.",
    }[risk_profile]

    if mode == "strategy":
        return (
            "Scanner mode: strategy-driven.\n"
            "Required behavior:\n"
            "- Emphasize per-symbol strategy agreement/disagreement across strategy outputs.\n"
            "- Include a subsection in Evidence named exactly: 'Strategy Consensus'.\n"
            "- Avoid composite/aggregate score phrasing as the primary decision logic.\n"
            f"Risk profile: {risk_profile}. {risk_suffix}"
        )

    return (
        "Scanner mode: score-model-driven.\n"
        "Required behavior:\n"
        "- Emphasize aggregate indicator score quality and ranking consistency across symbols.\n"
        "- Include a subsection in Evidence named exactly: 'Score Synthesis'.\n"
        "- Avoid strategy-voting language as the primary decision logic.\n"
        f"Risk profile: {risk_profile}. {risk_suffix}"
    )


def _multisector_mode_context(mode: str, risk_profile: str) -> str:
    """Implement multisector mode context."""

    risk_suffix = {
        "conservative": "Favor sector defensiveness, drawdown-aware interpretation, and robust consistency.",
        "balanced": "Balance sector opportunity and risk concentration across groups.",
        "aggressive": "Allow faster sector rotation framing with explicit risk concentration caveats.",
    }[risk_profile]

    if mode == "strategy":
        return (
            "Multi-sector mode: strategy-driven.\n"
            "Required behavior:\n"
            "- Compare sectors using strategy agreement/disagreement evidence by sector.\n"
            "- Include a subsection in Evidence named exactly: 'Strategy Consensus'.\n"
            "- Avoid composite/aggregate score wording as primary logic.\n"
            f"Risk profile: {risk_profile}. {risk_suffix}"
        )

    return (
        "Multi-sector mode: score-model-driven.\n"
        "Required behavior:\n"
        "- Compare sectors using aggregate score quality and consistency.\n"
        "- Include a subsection in Evidence named exactly: 'Score Synthesis'.\n"
        "- Avoid strategy-voting wording as primary logic.\n"
        f"Risk profile: {risk_profile}. {risk_suffix}"
    )


def _combined_technical_mode_context(mode: str, risk_profile: str) -> str:
    """Implement combined technical mode context."""

    risk_suffix = {
        "conservative": "Frame technical conclusions with stricter downside-first guardrails.",
        "balanced": "Frame technical conclusions with balanced upside/downside validation.",
        "aggressive": "Frame technical conclusions for faster signal responsiveness with explicit whipsaw risk.",
    }[risk_profile]

    if mode == "strategy":
        return (
            "Combined technical mode: strategy-driven.\n"
            "Required behavior:\n"
            "- In the technical part, emphasize strategy agreement/disagreement.\n"
            "- Include a subsection in Evidence named exactly: 'Strategy Consensus'.\n"
            "- Avoid composite/aggregate score language for the technical section.\n"
            f"Risk profile: {risk_profile}. {risk_suffix}"
        )

    return (
        "Combined technical mode: score-model-driven.\n"
        "Required behavior:\n"
        "- In the technical part, emphasize aggregate score synthesis and indicator consistency.\n"
        "- Include a subsection in Evidence named exactly: 'Score Synthesis'.\n"
        "- Avoid strategy-voting language for the technical section.\n"
        f"Risk profile: {risk_profile}. {risk_suffix}"
    )


def _normalize_mode(value: str, default: str = "strategy") -> str:
    """Normalize mode values."""

    mode = (value or default).strip().lower()
    if mode not in {"strategy", "score"}:
        return default
    return mode


def _normalize_risk_profile(value: str, default: str = "balanced") -> str:
    """Normalize risk profile values."""

    risk_profile = (value or default).strip().lower()
    if risk_profile not in {"conservative", "balanced", "aggressive"}:
        return default
    return risk_profile


def run_technical_analysis(
    symbol: str,
    period: str = "1y",
    technical_mode: str = "strategy",
    risk_profile: str = "balanced",
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run technical analysis."""

    mode = _normalize_mode(technical_mode, default="strategy")
    normalized_risk_profile = _normalize_risk_profile(risk_profile, default="balanced")

    if mode == "score":
        raw = comprehensive_performance_report(symbol=symbol, period=period)
        goal = (
            f"Run score-model technical analysis for {symbol.upper()} on period {period}. "
            "Prioritize ranked/synthesized signals and confidence scoring grounded in MCP output. "
            f"Adapt recommendation framing for risk profile: {normalized_risk_profile}."
        )
    else:
        strategy_chunks = [
            (
                "BOLLINGER_FIBONACCI",
                bollinger_fibonacci_analysis(symbol=symbol, period=period),
            ),
            (
                "MACD_DONCHIAN",
                macd_donchian_analysis(symbol=symbol, period=period),
            ),
            (
                "DUAL_MOVING_AVERAGE",
                dual_moving_average_analysis(symbol=symbol, period=period),
            ),
            (
                "BOLLINGER_ZSCORE_RSI",
                bollinger_zscore_rsi_strategy_analysis(symbol=symbol, period=period),
            ),
        ]
        sections = [
            f"## {name}\n{output}" for name, output in strategy_chunks
        ]
        raw = (
            f"# Technical Strategy Bundle ({symbol.upper()}, {period})\n\n"
            + "\n\n".join(sections)
        )
        goal = (
            f"Run strategy-driven technical analysis for {symbol.upper()} on period {period}. "
            "Base conclusions on explicit standalone strategy outputs, then synthesize agreement/disagreement across strategies. "
            f"Adapt recommendation framing for risk profile: {normalized_risk_profile}."
        )

    context = _technical_mode_context(mode, normalized_risk_profile)
    return _run_pipeline_sync("technical", goal, raw, model_id, analysis_context=context)


def run_market_scanner(
    symbols: str,
    period: str = "1y",
    scanner_mode: str = "strategy",
    risk_profile: str = "balanced",
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run market scanner."""

    mode = _normalize_mode(scanner_mode, default="strategy")
    normalized_risk_profile = _normalize_risk_profile(risk_profile, default="balanced")
    output_format = "detailed" if mode == "strategy" else "summary"
    raw = unified_market_scanner(symbols=symbols, period=period, output_format=output_format)
    goal = (
        f"Scan and rank opportunities for symbols: {symbols}. Period: {period}. "
        f"Mode={mode}. Risk profile={normalized_risk_profile}."
    )
    context = _scanner_mode_context(mode, normalized_risk_profile)
    return _run_pipeline_sync("scanner", goal, raw, model_id, analysis_context=context)


def run_fundamental_analysis(
    symbol: str,
    period: str = "3y",
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run fundamental analysis."""

    raw = fundamental_analysis_report(symbol=symbol, period=period)
    goal = f"Run fundamental analysis for {symbol.upper()} with period {period}."
    return _run_pipeline_sync("fundamental", goal, raw, model_id)


def run_multi_sector_analysis(
    sectors: Dict[str, str],
    period: str = "1y",
    multisector_mode: str = "strategy",
    risk_profile: str = "balanced",
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run multi sector analysis."""

    mode = _normalize_mode(multisector_mode, default="strategy")
    normalized_risk_profile = _normalize_risk_profile(risk_profile, default="balanced")
    output_format = "detailed" if mode == "strategy" else "summary"
    sector_chunks = []
    for sector_name, sector_symbols in sectors.items():
        sector_raw = unified_market_scanner(symbols=sector_symbols, period=period, output_format=output_format)
        sector_chunks.append(f"## Sector: {sector_name}\nSymbols: {sector_symbols}\n{sector_raw}")
    raw = "\n\n".join(sector_chunks)
    goal = (
        f"Compare sectors and rank opportunities. Sectors: {', '.join(sectors.keys())}. Period: {period}. "
        f"Mode={mode}. Risk profile={normalized_risk_profile}."
    )
    context = _multisector_mode_context(mode, normalized_risk_profile)
    return _run_pipeline_sync("multi_sector", goal, raw, model_id, analysis_context=context)


def run_combined_analysis(
    symbol: str,
    technical_period: str = "1y",
    fundamental_period: str = "3y",
    technical_mode: str = "strategy",
    risk_profile: str = "balanced",
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run combined analysis."""

    mode = _normalize_mode(technical_mode, default="strategy")
    normalized_risk_profile = _normalize_risk_profile(risk_profile, default="balanced")

    if mode == "score":
        technical_raw = comprehensive_performance_report(symbol=symbol, period=technical_period)
    else:
        strategy_chunks = [
            (
                "BOLLINGER_FIBONACCI",
                bollinger_fibonacci_analysis(symbol=symbol, period=technical_period),
            ),
            (
                "MACD_DONCHIAN",
                macd_donchian_analysis(symbol=symbol, period=technical_period),
            ),
            (
                "DUAL_MOVING_AVERAGE",
                dual_moving_average_analysis(symbol=symbol, period=technical_period),
            ),
            (
                "BOLLINGER_ZSCORE_RSI",
                bollinger_zscore_rsi_strategy_analysis(symbol=symbol, period=technical_period),
            ),
        ]
        sections = [f"## {name}\n{output}" for name, output in strategy_chunks]
        technical_raw = (
            f"# Technical Strategy Bundle ({symbol.upper()}, {technical_period})\n\n"
            + "\n\n".join(sections)
        )

    fundamental_raw = fundamental_analysis_report(symbol=symbol, period=fundamental_period)
    raw = (
        f"# Technical Output ({technical_period})\n{technical_raw}\n\n"
        f"# Fundamental Output ({fundamental_period})\n{fundamental_raw}"
    )
    goal = (
        f"Create a combined technical and fundamental thesis for {symbol.upper()} "
        f"using periods technical={technical_period}, fundamental={fundamental_period}. "
        f"Technical mode={mode}. Risk profile={normalized_risk_profile}."
    )
    context = _combined_technical_mode_context(mode, normalized_risk_profile)
    return _run_pipeline_sync("combined", goal, raw, model_id, analysis_context=context)


def run_earnings_momentum_analysis(
    symbols: str,
    period: str = "6mo",
    volume_window: int = 20,
    volume_multiplier: float = 2.0,
    hold_days: int = 5,
    max_positions: int = 3,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run earnings momentum analysis."""

    raw = earnings_momentum_analysis(
        symbols=symbols,
        period=period,
        volume_window=volume_window,
        volume_multiplier=volume_multiplier,
        hold_days=hold_days,
        max_positions=max_positions,
    )
    goal = f"Run earnings momentum scan for {symbols} in period {period}."
    return _run_pipeline_sync("earnings_momentum", goal, raw, model_id)


def run_trin_breadth_analysis(
    period: str = "6mo",
    window: int = 20,
    band_k: float = 1.5,
    use_log: bool = True,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run trin breadth analysis."""

    raw = trin_market_breadth_analysis(period=period, window=window, band_k=band_k, use_log=use_log)
    goal = f"Interpret TRIN breadth conditions for period={period}, window={window}, band_k={band_k}."
    return _run_pipeline_sync("trin", goal, raw, model_id)


def run_overnight_gap_analysis(
    symbol: str,
    lookback_days: int = 120,
    min_gap_pct: float = 1.0,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run overnight gap analysis."""

    raw = overnight_gap_analysis(symbol=symbol, lookback_days=lookback_days, min_gap_pct=min_gap_pct)
    goal = f"Interpret overnight gap behavior for {symbol.upper()}, lookback={lookback_days}, min_gap={min_gap_pct}."
    return _run_pipeline_sync("overnight_gaps", goal, raw, model_id)


def run_bollinger_breakout_analysis(
    symbol: str = "SPY",
    period: str = "2y",
    bb_period: int = 20,
    bb_std: float = 2.0,
    atr_period: int = 14,
    volume_window: int = 20,
    volume_multiplier: float = 1.2,
    warmup_bars: int = 25,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run bollinger breakout analysis."""

    raw = bollinger_breakout_analysis(
        symbol=symbol,
        period=period,
        bb_period=bb_period,
        bb_std=bb_std,
        atr_period=atr_period,
        volume_window=volume_window,
        volume_multiplier=volume_multiplier,
        warmup_bars=warmup_bars,
    )
    goal = (
        f"Evaluate Bollinger breakout strategy for {symbol.upper()} with period={period}, "
        f"bb_period={bb_period}, bb_std={bb_std}, atr_period={atr_period}, "
        f"volume_window={volume_window}, volume_multiplier={volume_multiplier}, warmup_bars={warmup_bars}."
    )
    return _run_pipeline_sync("bollinger_breakout", goal, raw, model_id)


def run_gap_fade_analysis(
    symbol: str = "SPY",
    period: str = "2y",
    gap_threshold: float = 0.02,
    hold_minutes: int = 120,
    position_size: float = 0.8,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run gap fade analysis."""

    raw = gap_fade_analysis(
        symbol=symbol,
        period=period,
        gap_threshold=gap_threshold,
        hold_minutes=hold_minutes,
        position_size=position_size,
    )
    goal = (
        f"Evaluate gap fade strategy for {symbol.upper()} with period={period}, gap_threshold={gap_threshold}, "
        f"hold_minutes={hold_minutes}, position_size={position_size}."
    )
    return _run_pipeline_sync("gap_fade", goal, raw, model_id)


def run_multi_timeframe_analysis(
    symbol: str = "SPY",
    period: str = "2y",
    sma_fast: int = 50,
    sma_slow: int = 200,
    rsi_period: int = 14,
    rsi_oversold: float = 30.0,
    rsi_exit: float = 70.0,
    warmup_days: int = 210,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run multi timeframe analysis."""

    raw = multi_timeframe_analysis(
        symbol=symbol,
        period=period,
        sma_fast=sma_fast,
        sma_slow=sma_slow,
        rsi_period=rsi_period,
        rsi_oversold=rsi_oversold,
        rsi_exit=rsi_exit,
        warmup_days=warmup_days,
    )
    goal = (
        f"Evaluate multi-timeframe strategy for {symbol.upper()} with period={period}, "
        f"sma_fast={sma_fast}, sma_slow={sma_slow}, rsi_period={rsi_period}, "
        f"rsi_oversold={rsi_oversold}, rsi_exit={rsi_exit}, warmup_days={warmup_days}."
    )
    return _run_pipeline_sync("multi_timeframe", goal, raw, model_id)


def run_pairs_trading_analysis(
    symbol_a: str = "SPY",
    symbol_b: str = "QQQ",
    period: str = "2y",
    window: int = 20,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5,
    position_size: float = 0.5,
    warmup_period: int = 25,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run pairs trading analysis."""

    raw = pairs_trading_analysis(
        symbol_a=symbol_a,
        symbol_b=symbol_b,
        period=period,
        window=window,
        entry_threshold=entry_threshold,
        exit_threshold=exit_threshold,
        position_size=position_size,
        warmup_period=warmup_period,
    )
    goal = (
        f"Evaluate pairs trading strategy for {symbol_a.upper()}/{symbol_b.upper()} with period={period}, "
        f"window={window}, entry_threshold={entry_threshold}, exit_threshold={exit_threshold}, "
        f"position_size={position_size}, warmup_period={warmup_period}."
    )
    return _run_pipeline_sync("pairs_trading", goal, raw, model_id)


def run_statistical_arbitrage_analysis(
    symbols: str = "AAPL,MSFT,GOOGL",
    period: str = "2y",
    window: int = 20,
    entry_threshold: float = 1.5,
    exit_threshold: float = 0.3,
    position_size: float = 0.3,
    warmup_period: int = 25,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run statistical arbitrage analysis."""

    raw = statistical_arbitrage_analysis(
        symbols=symbols,
        period=period,
        window=window,
        entry_threshold=entry_threshold,
        exit_threshold=exit_threshold,
        position_size=position_size,
        warmup_period=warmup_period,
    )
    goal = (
        f"Evaluate statistical arbitrage basket strategy for symbols={symbols} with period={period}, "
        f"window={window}, entry_threshold={entry_threshold}, exit_threshold={exit_threshold}, "
        f"position_size={position_size}, warmup_period={warmup_period}."
    )
    return _run_pipeline_sync("statistical_arbitrage", goal, raw, model_id)


def run_vix_term_structure_analysis(
    symbol: str = "SPY",
    period: str = "2y",
    front_window: int = 10,
    back_window: int = 30,
    contango_threshold: float = 1.05,
    backwardation_threshold: float = 0.95,
    long_position_size: float = 0.8,
    short_position_size: float = -0.5,
    warmup_period: int = 35,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run vix term structure analysis."""

    raw = vix_term_structure_analysis(
        symbol=symbol,
        period=period,
        front_window=front_window,
        back_window=back_window,
        contango_threshold=contango_threshold,
        backwardation_threshold=backwardation_threshold,
        long_position_size=long_position_size,
        short_position_size=short_position_size,
        warmup_period=warmup_period,
    )
    goal = (
        f"Evaluate VIX term-structure strategy for {symbol.upper()} with period={period}, "
        f"front_window={front_window}, back_window={back_window}, contango_threshold={contango_threshold}, "
        f"backwardation_threshold={backwardation_threshold}, long_position_size={long_position_size}, "
        f"short_position_size={short_position_size}, warmup_period={warmup_period}."
    )
    return _run_pipeline_sync("vix_term_structure", goal, raw, model_id)


def run_volatility_regime_analysis(
    period: str = "2y",
    spy_symbol: str = "SPY",
    qqq_symbol: str = "QQQ",
    arkk_symbol: str = "ARKK",
    tlt_symbol: str = "TLT",
    gld_symbol: str = "GLD",
    vol_window: int = 20,
    high_vol_threshold: float = 25.0,
    low_vol_threshold: float = 15.0,
    warmup_period: int = 25,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run volatility regime analysis."""

    raw = volatility_regime_analysis(
        period=period,
        spy_symbol=spy_symbol,
        qqq_symbol=qqq_symbol,
        arkk_symbol=arkk_symbol,
        tlt_symbol=tlt_symbol,
        gld_symbol=gld_symbol,
        vol_window=vol_window,
        high_vol_threshold=high_vol_threshold,
        low_vol_threshold=low_vol_threshold,
        warmup_period=warmup_period,
    )
    goal = (
        f"Evaluate volatility-regime allocation strategy with period={period}, vol_window={vol_window}, "
        f"high_vol_threshold={high_vol_threshold}, low_vol_threshold={low_vol_threshold}, warmup_period={warmup_period}, "
        f"assets={qqq_symbol.upper()},{arkk_symbol.upper()},{tlt_symbol.upper()},{gld_symbol.upper()} benchmark={spy_symbol.upper()}."
    )
    return _run_pipeline_sync("volatility_regime", goal, raw, model_id)


def run_bollinger_zscore_analysis(
    symbol: str = "AAPL",
    period: int = 20,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run bollinger zscore analysis."""

    raw = bollinger_zscore_analysis(symbol=symbol, period=period)
    goal = f"Evaluate Bollinger Z-Score strategy for {symbol.upper()} using rolling period={period}."
    return _run_pipeline_sync("bollinger_zscore", goal, raw, model_id)


def run_bollinger_zscore_rsi_strategy_analysis(
    symbol: str = "AAPL",
    period: str = "2y",
    bb_window: int = 20,
    bb_std: float = 2.0,
    rsi_period: int = 14,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
    zscore_buy_threshold: float = -2.0,
    zscore_sell_threshold: float = 2.0,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run bollinger zscore rsi strategy analysis."""

    raw = bollinger_zscore_rsi_strategy_analysis(
        symbol=symbol,
        period=period,
        bb_window=bb_window,
        bb_std=bb_std,
        rsi_period=rsi_period,
        rsi_oversold=rsi_oversold,
        rsi_overbought=rsi_overbought,
        zscore_buy_threshold=zscore_buy_threshold,
        zscore_sell_threshold=zscore_sell_threshold,
    )
    goal = (
        f"Evaluate Bollinger Z-Score + RSI strategy for {symbol.upper()} with period={period}, "
        f"bb_window={bb_window}, bb_std={bb_std}, rsi_period={rsi_period}, "
        f"rsi_oversold={rsi_oversold}, rsi_overbought={rsi_overbought}, "
        f"zscore_buy_threshold={zscore_buy_threshold}, zscore_sell_threshold={zscore_sell_threshold}."
    )
    return _run_pipeline_sync("bollinger_zscore_rsi", goal, raw, model_id)


def run_bollinger_fibonacci_analysis(
    symbol: str = "AAPL",
    period: str = "1y",
    window: int = 20,
    num_std: int = 2,
    window_swing_points: int = 10,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run bollinger fibonacci analysis."""

    raw = bollinger_fibonacci_analysis(
        symbol=symbol,
        period=period,
        window=window,
        num_std=num_std,
        window_swing_points=window_swing_points,
    )
    goal = (
        f"Evaluate Bollinger Fibonacci strategy for {symbol.upper()} with period={period}, window={window}, "
        f"num_std={num_std}, swing_window={window_swing_points}."
    )
    adk_report = _run_pipeline_sync("bollinger_fibonacci", goal, raw, model_id)

    if _is_bad_adk_report(adk_report, raw):
        parsed_analysis = _format_bollinger_fibonacci_analysis_from_raw(
            raw=raw,
            symbol=symbol,
            period=period,
            window=window,
            num_std=num_std,
            window_swing_points=window_swing_points,
        )
        if parsed_analysis:
            return parsed_analysis

    return adk_report


def run_macd_donchian_analysis(
    symbol: str = "AAPL",
    period: str = "1y",
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    window: int = 20,
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run macd donchian analysis."""

    raw = macd_donchian_analysis(
        symbol=symbol,
        period=period,
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period,
        window=window,
    )
    goal = (
        f"Evaluate MACD Donchian strategy performance for {symbol.upper()} with period={period}, fast={fast_period}, "
        f"slow={slow_period}, signal={signal_period}, donchian_window={window}."
    )
    adk_report = _run_pipeline_sync("macd_donchian", goal, raw, model_id)

    if _is_bad_adk_report(adk_report, raw):
        parsed_analysis = _format_macd_donchian_analysis_from_raw(
            raw=raw,
            symbol=symbol,
            period=period,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            window=window,
        )
        if parsed_analysis:
            return parsed_analysis

    return adk_report


def run_dual_moving_average_analysis(
    symbol: str = "AAPL",
    period: str = "2y",
    short_period: int = 50,
    long_period: int = 200,
    ma_type: str = "SMA",
    model_id: str = DEFAULT_MODEL_ID,
    **_: object,
) -> str:
    """Run dual moving average analysis."""

    raw = dual_moving_average_analysis(
        symbol=symbol,
        period=period,
        short_period=short_period,
        long_period=long_period,
        ma_type=ma_type,
    )
    goal = (
        f"Evaluate dual moving average strategy for {symbol.upper()} with period={period}, short={short_period}, "
        f"long={long_period}, ma_type={ma_type}."
    )
    adk_report = _run_pipeline_sync("dual_moving_average", goal, raw, model_id)

    if _is_bad_adk_report(adk_report, raw):
        parsed_analysis = _format_dual_ma_analysis_from_raw(
            raw=raw,
            symbol=symbol,
            period=period,
            short_period=short_period,
            long_period=long_period,
            ma_type=ma_type,
        )
        if parsed_analysis:
            return parsed_analysis

    return adk_report
