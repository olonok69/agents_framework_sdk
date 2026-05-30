# 📊 Stock Analyzer Bot

The **ADK-powered orchestration layer** for the MCP Financial Markets Analysis Tool. This module runs the production multi-agent pipeline used by the FastAPI backend.

---

## 🎯 Overview

Current production path:

| Layer | Implementation | Purpose |
|-------|----------------|---------|
| **API Runtime** | `api.py` | FastAPI endpoints for analysis/strategy routes |
| **Agentic Pipeline** | `adk_bot.py` | Orchestrator + specialist + critic + reporter flow |
| **MCP Integration** | `mcp_tools.py`, `mcp_client.py` | Deterministic tool calls and session management |
| **Compatibility Exports** | `main.py` | Re-export ADK runner functions |

Legacy smolagents files may exist for reference, but they are not the active API runtime path.

---

## 📁 Module Structure

```
stock_analyzer_bot/
├── __init__.py              # Package initialization
├── adk_bot.py               # ADK multi-agent pipeline + guardrails
├── adk_bridge.py            # ADK bridge helper
├── main.py                  # ADK compatibility exports
├── api.py                   # FastAPI endpoints
├── mcp_tools.py             # MCP wrappers used by ADK pipeline
├── mcp_client.py            # MCP session management
└── README.md                # This file
```

---

## 🤖 ADK Pipeline

The ADK pipeline in `adk_bot.py` runs the following stages:

1. **Orchestrator** creates analysis plan.
2. **Financial specialist** interprets MCP output with numeric grounding.
3. **Critic/guardrail** checks unsupported claims and risk framing.
4. **Reporter** produces the final markdown response.
5. **Post-check validator** enforces taxonomy contract (`analysis` vs `strategy`) and can rewrite/block non-compliant outputs.

## 🔧 MCP Tool Access

`mcp_tools.py` contains the normalized wrappers used by the ADK pipeline.

- Each wrapper calls a named MCP tool with typed parameters.
- Errors are captured and returned in a consistent format.
- API routes often call both ADK interpretation and raw MCP output to expose `timeseries` fields.

---

## 📡 API Endpoints

The `api.py` module exposes all analysis and strategy functions via FastAPI and routes requests into `adk_bot.py`.

### Configuration

```python
# Environment variables
DEFAULT_MODEL_ID = os.getenv("ADK_MODEL_ID", "gpt-4.1")
DEFAULT_MODEL_PROVIDER = os.getenv("ADK_MODEL_PROVIDER", "openai")
DEFAULT_AGENT_TYPE = "adk_agentic"
```

### Endpoints

#### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "3.1.0",
  "features": [
    "technical_analysis",
    "market_scanner",
    "fundamental_analysis",
    "multi_sector_analysis",
    "combined_analysis",
    "trin_breadth",
    "overnight_gaps"
  ],
  "agent_types": {
    "tool_calling": true,
    "code_agent": true
  },
  "default_agent_type": "adk_agentic"
}
```

#### Technical Analysis

```http
POST /technical
Content-Type: application/json

{
  "symbol": "AAPL",
  "period": "1y",
  "technical_mode": "strategy",
  "risk_profile": "balanced",
  "agent_type": "adk_agentic",
  "model_id": "gpt-4.1"
}
```

Uses MCP technical tooling + ADK multi-agent reporting pipeline.

Mode/risk controls:
- `technical_mode`: `strategy` (default) | `score`
- `risk_profile`: `conservative` | `balanced` (default) | `aggressive`

#### Market Scanner

```http
POST /scanner
Content-Type: application/json

{
  "symbols": "AAPL,MSFT,GOOGL,META,NVDA",
  "period": "1y",
  "scanner_mode": "strategy",
  "risk_profile": "balanced",
  "agent_type": "adk_agentic"
}
```

Uses MCP scanner tooling + ADK synthesis/critique.

Mode/risk controls:
- `scanner_mode`: `strategy` (default) | `score`
- `risk_profile`: `conservative` | `balanced` (default) | `aggressive`

#### Fundamental Analysis

```http
POST /fundamental
Content-Type: application/json

{
  "symbol": "MSFT",
  "period": "3y",
  "agent_type": "adk_agentic"
}
```

Uses `fundamental_analysis_report` tool with 70+ row aliases for robust data extraction.

#### Multi-Sector Analysis

```http
POST /multisector
Content-Type: application/json

{
  "sectors": [
    {"name": "Banking", "symbols": "JPM,BAC,WFC"},
    {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL"}
  ],
  "period": "1y",
  "multisector_mode": "strategy",
  "risk_profile": "balanced",
  "agent_type": "adk_agentic"
}
```

Uses MCP multi-sector data assembly + ADK reporting.

Mode/risk controls:
- `multisector_mode`: `strategy` (default) | `score`
- `risk_profile`: `conservative` | `balanced` (default) | `aggressive`

#### Combined Analysis

```http
POST /combined
Content-Type: application/json

{
  "symbol": "TSLA",
  "technical_period": "1y",
  "fundamental_period": "3y",
  "technical_mode": "strategy",
  "risk_profile": "balanced",
  "agent_type": "adk_agentic"
}
```

Combines technical and fundamental analysis into a unified investment thesis.

Mode/risk controls:
- `technical_mode` (technical branch): `strategy` (default) | `score`
- `risk_profile`: `conservative` | `balanced` (default) | `aggressive`

#### TRIN Breadth (Arms Index)

```http
POST /trin
Content-Type: application/json

{
  "period": "6mo",
  "window": 20,
  "band_k": 1.5,
  "use_log": true,
  "agent_type": "adk_agentic"
}
```

Returns ADK narrative grounded on MCP TRIN metrics and timeseries.

#### Overnight Gaps / Midnight Returns

```http
POST /overnight_gaps
Content-Type: application/json

{
  "symbol": "AAPL",
  "lookback_days": 120,
  "min_gap_pct": 1.0,
  "agent_type": "mcp_tool"   // or "code_agent" to let the LLM summarize
}
```

- Computes prior close → next open gaps, classifies up/down, checks intraday fills only
- Returns summary, metrics (fill rates, averages, recent gaps), and timeseries

### Response Format

All endpoints return:

```json
{
  "report": "# AAPL Comprehensive Technical Analysis\n...",
  "symbol": "AAPL",
  "analysis_type": "technical",
  "duration_seconds": 35.2,
  "agent_type": "adk_agentic",
  "tools_approach": "MCP tools + ADK multi-agent review"
}
```

For mode-aware routes (`/technical`, `/scanner`, `/multisector`, technical branch of `/combined`),
the returned report begins with a deterministic metadata line, for example:

- `> Mode used: Technical=strategy | risk=balanced`
- `> Mode used: Scanner=score | risk=aggressive`

---

## ⚙️ Configuration

### Runtime Configuration

```python
# Model settings
DEFAULT_MODEL_ID = "gpt-4.1"
DEFAULT_MODEL_PROVIDER = "openai"
DEFAULT_AGENT_TYPE = "adk_agentic"
```

---

## 📝 Prompt Templates

All prompts follow strict formatting guidelines for clean output:

### Formatting Rules

1. **Currency:** Use "USD" prefix instead of "$" (avoids LaTeX interpretation)
2. **Tables:** Avoid pipe characters `|` (render poorly in Streamlit)
3. **Structure:** Each data point on its own line
4. **Headers:** Numbered sections with clear hierarchy
5. **No Italics:** Avoid `*text*` formatting

### Technical Analysis Prompt Structure

```
1. EXECUTIVE SUMMARY
   - Overall recommendation (BUY/HOLD/SELL)
   - Confidence level
   - Key metrics

2. STRATEGY ANALYSIS
   - Bollinger-Fibonacci: Signal, metrics, interpretation
   - MACD-Donchian: Signal, metrics, interpretation
   - Connors RSI-ZScore: Signal, metrics, interpretation
   - Dual Moving Average: Signal, metrics, interpretation

3. RISK ASSESSMENT
   - Position sizing guidance
   - Stop loss levels

4. FINAL RECOMMENDATION
   - Actionable conclusion
```

### Market Scanner Prompt Structure

```
1. MARKET OVERVIEW
   - Total stocks analyzed
   - Market conditions

2. RANKED OPPORTUNITIES
   - Stock rankings with scores
  - Strategy evidence per stock (or score synthesis when score mode is selected):
     * Bollinger Z-Score
     * Bollinger-Fibonacci
     * MACD-Donchian
     * Connors RSI-ZScore
     * Dual Moving Average

3. TOP RECOMMENDATIONS
   - Best opportunities with rationale

4. PORTFOLIO ALLOCATION
   - Suggested allocation percentages
```

---

## 🧪 Usage Examples

### Python - Direct Import

```python
from stock_analyzer_bot.mcp_tools import configure_finance_tools, shutdown_finance_tools

# Initialize MCP connection
configure_finance_tools()

try:
    # ADK runtime analysis
    from stock_analyzer_bot.main import run_technical_analysis
    report = run_technical_analysis(symbol="AAPL", period="1y")

    from stock_analyzer_bot.main import run_market_scanner
    report = run_market_scanner(
      symbols="AAPL,MSFT,GOOGL",
      period="1y"
    )
    
    print(report)
finally:
    shutdown_finance_tools()
```

### CLI - ADK Runtime

```bash
python -m stock_analyzer_bot.main AAPL --mode technical --period 1y
python -m stock_analyzer_bot.main "AAPL,MSFT" --mode scanner
python -m stock_analyzer_bot.main MSFT --mode fundamental
```

### cURL - API

```bash
# Technical (ADK runtime)
curl -X POST "http://localhost:8000/technical" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "technical_mode": "strategy", "risk_profile": "balanced", "agent_type": "adk_agentic"}'

# Scanner (ADK runtime)
curl -X POST "http://localhost:8000/scanner" \
  -H "Content-Type: application/json" \
  -d '{"symbols": "AAPL,MSFT", "scanner_mode": "score", "risk_profile": "aggressive", "agent_type": "adk_agentic"}'

# Multi-sector (ADK runtime)
curl -X POST "http://localhost:8000/multisector" \
  -H "Content-Type: application/json" \
  -d '{
    "sectors": [
      {"name": "Banking", "symbols": "JPM,BAC,WFC"},
      {"name": "Tech", "symbols": "AAPL,MSFT,GOOGL"}
    ],
    "multisector_mode": "strategy",
    "risk_profile": "conservative",
    "agent_type": "adk_agentic"
  }'
```

---

## 📊 Runtime Notes

- ADK provides a consistent reporting path across all analysis and strategy routes.
- Throughput depends mainly on MCP data retrieval and model latency.
- Guardrail rewrite/block behavior prioritizes grounded outputs over speed.

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "MCP server not found" | Server path incorrect | Check `server/main.py` exists at project root |
| "Connection refused" | FastAPI not running | Start with `uvicorn stock_analyzer_bot.api:app --port 8000` |
| "Timeout" | Too many stocks / slow market data | Reduce scope or increase timeout |
| "Authentication error" | Invalid API key | Check `OPENAI_API_KEY` environment variable |
| "Guardrail blocked" | Taxonomy or grounding violation | Inspect MCP output + taxonomy contract |
| "Truncated output" | Token limit exceeded | Increase `max_tokens` to 8192+ |
| "LaTeX formatting" | Dollar signs in output | Code uses USD prefix instead of $ |

### Debugging Tips

**Enable verbose logging:**
```python
import logging

logging.getLogger("stock_analyzer_bot.adk_bot").setLevel(logging.DEBUG)
```

**Check agent output:**
```python
import asyncio
from stock_analyzer_bot.adk_bot import run_technical_analysis_adk

result = asyncio.run(run_technical_analysis_adk("AAPL"))
print(result)
```

**Test MCP connection:**
```python
from stock_analyzer_bot.tools import configure_finance_tools
from stock_analyzer_bot.mcp_client import get_session

configure_finance_tools()
session = get_session()
print(f"Session active: {session is not None}")
```

---

## 📚 Related Documentation

- [Root README](../README.md) - Project overview
- [Server README](../server/README.md) - MCP tools reference
- [Analysis vs Strategy Catalog](../docs/analysis_strategy_catalog.md) - Taxonomy and endpoint contract
- [Architecture Diagram](../docs/architecture_adk.svg) - ADK runtime topology

---

## 🔄 Recent Changes

### v4.x - ADK consolidation

- Unified runtime flow on ADK (orchestrator, specialist, critic, reporter).
- Added taxonomy contract integration from `docs/analysis_strategy_catalog.json`.
- Enforced post-check rewrite/block path for invalid outputs.
- Standardized strategy route classification and labels in API/UI.
- Updated docs and architecture diagram to current production path.

---

