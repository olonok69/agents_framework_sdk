# TRIN (Arms Index) Breadth Strategy

## What the Strategy Measures
- TRIN compares advancing vs. declining issues **and** their volumes to gauge intraday buying vs. selling pressure.
- Interpretation:
  - TRIN > 1 → selling pressure; TRIN < 1 → buying pressure.
  - Extreme highs often mark capitulation (contrarian bullish); extreme lows can mark euphoria (contrarian cautious).

## Data Pipeline
- Primary source: Yahoo Finance ticker `^TRIN` (with fallbacks to `TRIN`, `TRINQ`).
- Fallback source: Nasdaq Data Link URC datasets (`URC/NYSE_ADV`, `URC/NYSE_DEC`, `URC/NYSE_ADV_VOL`, `URC/NYSE_DEC_VOL`) when `NASDAQ_DATA_LINK_API_KEY` or `QUANDL_API_KEY` is set.
- Period fallbacks: requested period → 1y → 2y → 5y → max; final explicit range from 2000-01-01 if needed.

## Indicator Construction
- Optional log transform (default: on) to stabilize variance.
- Rolling mean and standard deviation over a configurable window (default 20 days).
- Bollinger-style bands using `band_k` std dev (default 1.5) to flag extremes.

## Outputs (MCP Tool)
- Summary markdown with current TRIN, moving average, bands, band state, 5-day change, and rationale.
- Metrics dict including: `signal`, `bias`, `band_state`, `trin`, `ma`, `upper`, `lower`, `change_5d_pct`, `rationale`, and `timeseries` (capped for safety).
- Timeseries rows: date, trin, ma, upper, lower (for charting in Streamlit).

## Implementations in This Repo
- MCP tool: `analyze_trin_breadth` in `server/strategies/trin_strategy.py` (registered via `register_trin_strategy_tools` in `server/main.py`).
- FastAPI endpoint: `POST /trin` in `stock_analyzer_bot/api.py` with two modes:
  - `agent_type = "mcp_tool"` (default): returns the raw MCP tool summary/metrics.
  - `agent_type = "code_agent"`: lets CodeAgent read the JSON and produce a concise brief.
- Streamlit tab: "🧮 TRIN Breadth" in `streamlit_app.py`, supports CodeAgent interpretation toggle and Altair chart from timeseries.
- Agent prompt: `TRIN_ANALYSIS_PROMPT` in `stock_analyzer_bot/main_codeagent.py` guides CodeAgent summarization.

## Configuration Knobs
- `period` (e.g., 3mo, 6mo, 1y, 2y).
- `window` (rolling mean/std, default 20).
- `band_k` (band width in std dev, default 1.5).
- `use_log` (bool, default true).

## Operational Notes
- Nasdaq Data Link requires `NASDAQ_DATA_LINK_API_KEY` or `QUANDL_API_KEY` for the fallback path.
- If CodeAgent is unavailable, the API falls back to the deterministic MCP tool.
- Timeseries is clipped to avoid oversized payloads for UI/clients.

## Quick Call Examples
- MCP tool (direct): handled internally by `/trin` when `agent_type = "mcp_tool"`.
- MCP tool via Python wrapper: `trin_market_breadth_analysis(period="6mo", window=20, band_k=1.5, use_log=True)` from `stock_analyzer_bot.tools`.
- CodeAgent summary: call `/trin` with `agent_type = "code_agent"` or `run_trin_breadth_analysis` in `main_codeagent.py`.
