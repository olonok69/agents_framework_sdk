# Overnight Gaps / Midnight Returns Strategy

## What the Strategy Measures
- Compares each session’s open to the prior close to find gap-up/gap-down events.
- Focuses on **intraday fill**: whether price revisits the prior close the same day.
- Captures same-day drift from the open to the close for context.

## Data Pipeline
- Source: Yahoo Finance daily candles via `yfinance` at 1d interval.
- Lookback: configurable days (default 120), fetches a few extra days to ensure the previous close is available.
- Filters out gaps whose absolute size is below a user threshold (default 1%).

## Computation
- Gap % = (today_open - prev_close) / prev_close * 100.
- Direction: `up` if gap % > 0 else `down`.
- Intraday fill test (same day):
  - Up gap is filled if day’s low ≤ prior close.
  - Down gap is filled if day’s high ≥ prior close.
- Same-day close return: (close - open) / open * 100.

## Outputs (MCP Tool)
- Summary markdown with totals, up/down counts, fill rates (all/up/down), average gaps, average same-day drift, and last gap info.
- Metrics dict with aggregates and recent gaps (last 5), plus the full `timeseries` (capped to 200 rows for safety).
- Timeseries rows: date, gap_pct, direction, filled, prev_close, open, high, low, close, same_day_close_ret.

## Implementations in This Repo
- MCP tool: `analyze_overnight_gaps` in `server/strategies/gap_strategy.py` (registered via `register_gap_strategy_tools` in `server/main.py`).
- FastAPI endpoint: `POST /overnight_gaps` in `stock_analyzer_bot/api.py` with two modes:
  - `agent_type = "mcp_tool"` (default): returns the MCP tool summary/metrics (and timeseries in response root for UI).
  - `agent_type = "code_agent"`: CodeAgent reads the tool JSON and writes a concise brief.
- Streamlit tab: "🌙 Overnight Gaps" in `streamlit_app.py`, with agent toggle and Altair bar/diamond chart from timeseries.
- Agent prompt: `OVERNIGHT_GAP_PROMPT` in `stock_analyzer_bot/main_codeagent.py`, includes JSON parsing guards.

## Configuration Knobs
- `lookback_days` (default 120; UI allows 30–400).
- `min_gap_pct` (default 1.0%; UI allows 0.1–10%).
- Agent type: deterministic MCP tool vs CodeAgent summarization.

## Operational Notes
- Uses only daily data (no intraday history needed).
- Intraday fill is based solely on the same day’s high/low vs the prior close—no 30–60 minute bars required.
- Timeseries is clipped to avoid oversized payloads; metrics carry recent gap highlights.

## Quick Call Examples
- MCP tool via Python wrapper: `overnight_gap_analysis(symbol="AAPL", lookback_days=120, min_gap_pct=1.0)` from `stock_analyzer_bot.tools`.
- API deterministic: `POST /overnight_gaps` with `agent_type="mcp_tool"`.
- API with LLM summary: `POST /overnight_gaps` with `agent_type="code_agent"`.
