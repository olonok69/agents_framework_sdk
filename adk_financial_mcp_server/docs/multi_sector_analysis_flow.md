# Multi-Sector Analysis Flow

## Purpose
- Compare multiple sectors by scanning symbols within each sector, then ranking sectors and stocks.
- Highlights leadership, breadth of buy signals, and avoid lists across sectors.

## How It Works
- ToolCallingAgent path: for each sector, calls the high-level `market_scanner` tool (unified scanner) and aggregates results.
- CodeAgent path: nested loops over sectors → stocks → four low-level strategies, then aggregates signals and rankings in Python.

## Implementation in This Repo
- FastAPI endpoint: `POST /multisector` in `stock_analyzer_bot/api.py`.
- Streamlit tab: "🌐 Multi-Sector Analysis" in `streamlit_app.py` with default sector presets; supports CodeAgent for speed.
- CodeAgent prompt: `MULTI_SECTOR_PROMPT` in `stock_analyzer_bot/main_codeagent.py`.

## Inputs
- `sectors`: list of `{name, symbols}` (comma-separated tickers per sector).
- `period`: lookback for technical data (default 1y).
- `agent_type`: `tool_calling` or `code_agent`; `executor_type` for CodeAgent.

## Outputs
- Markdown with sector rankings, best stocks per sector, top picks/avoid lists, and summary tables.
- Uses the four low-level technical strategies under the hood (or the high-level scanner per sector in tool-calling mode).

## Quick Usage
- FastAPI: `POST /multisector` with sectors array, period, agent_type.
- Streamlit: Multi-Sector tab form with editable sectors.
