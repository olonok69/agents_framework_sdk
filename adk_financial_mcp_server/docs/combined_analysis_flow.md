# Combined Technical + Fundamental Analysis (API / Agent Flow)

## Purpose
- Produce a single report that merges technical analysis (4 strategies) with fundamental analysis in one call.
- Delivers a balanced thesis: timing + company quality.

## How It Works
- Technical side: runs the four low-level strategies (Bollinger+Fibonacci, MACD+Donchian, Connors RSI+Z-Score, Dual MA) via CodeAgent or via the comprehensive high-level tool (ToolCallingAgent path).
- Fundamental side: pulls financial statements and ratios via the fundamental analysis tool.
- The agent stitches both into a unified markdown with recommendations.

## Implementation in This Repo
- FastAPI endpoint: `POST /combined` in `stock_analyzer_bot/api.py`.
  - ToolCallingAgent path: calls `comprehensive_performance_report` (tech) + `fundamental_analysis_report` (fundamentals) in two MCP calls.
  - CodeAgent path: calls the four low-level technical tools + `fundamental_analysis_report` via Python orchestration.
- Streamlit tab: "🔄 Combined Analysis" in `streamlit_app.py`, configurable periods for tech and fundamental.
- CodeAgent prompt: `COMBINED_ANALYSIS_PROMPT` in `stock_analyzer_bot/main_codeagent.py`.

## Key Parameters
- `symbol` (required).
- `technical_period` (default 1y).
- `fundamental_period` (default 3y).
- `agent_type`: `tool_calling` or `code_agent`; `executor_type` for CodeAgent.

## Outputs
- Markdown report with executive summary, per-strategy technical highlights, fundamental highlights, and a merged recommendation.

## Quick Usage
- FastAPI: `POST /combined` with symbol, periods, and agent_type.
- Streamlit: Combined tab form.
