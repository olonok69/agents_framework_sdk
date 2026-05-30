# Earnings Momentum Strategy

## What the Strategy Tracks
- Scans a basket of symbols for **earnings momentum bursts**: high-volume sessions with bullish closes.
- Assumes positive post-earnings drift persists for a fixed number of trading days (default 5).
- Limits the number of concurrent positions to focus on the strongest signals.

## Data Pipeline
- Source: Yahoo Finance via `yfinance` using daily candles (`1d` interval).
- Symbols: configurable comma-separated list (default `AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA`).
- Period: flexible lookback (`3mo`, `6mo`, `1y`, etc.).
- Indicators per symbol:
  - 20-day (configurable) simple moving average of volume.
  - Volume ratio = `Volume / VolumeSMA`.
  - Bullish flag when `Close > Open`.

## Computation Steps
1. **Download & Normalize** — Fetch OHLCV for every symbol, compute rolling volume stats via `groupby` + `rolling`.
2. **Signal Detection** — Flag sessions where `volume_ratio >= threshold` (default `2×`) and the close is above the open.
3. **Position Management** —
   - Enter positions on qualifying signals until `max_positions` (default 3) is reached.
   - Track each entry with entry date, price, and volume ratio.
   - Exit after `hold_days` trading bars (default 5) or at dataset end.
4. **Performance Metrics** — Compute wins, losses, average returns, and leader board per symbol.
5. **Recent Signals** — Capture the most recent entries for visualization in Streamlit.

## Outputs (MCP Tool)
- JSON structure with:
  - `summary`: Markdown-ready overview (universe, parameters, trade stats, recent entries).
  - `metrics`:
    - `parameters`: effective run configuration.
    - `aggregate`: total trades, hit rate, average return, average hold length.
    - `per_symbol`: trades, win rate, avg/median/best/worst returns per ticker.
    - `trades`: capped log of historical trades (entry/exit dates, returns).
    - `signals`: recent entry signals for plotting (date, symbol, volume ratio, closing price).
- Errors are returned as `{"error": "..."}` for UI handling.

## Implementations in This Repo
- **MCP Tool:** `analyze_earnings_momentum` in `server/strategies/earnings_momentum.py` (registered via `register_earnings_momentum_tools`).
- **ToolCallingAgent:** `run_earnings_momentum_analysis` in `stock_analyzer_bot/main.py` uses the low-level tool but formats the report with GPT.
- **CodeAgent:** `run_earnings_momentum_analysis` in `stock_analyzer_bot/main_codeagent.py` parses the JSON with custom Python code before writing the brief.
- **FastAPI Endpoint:** `POST /earnings_momentum` in `stock_analyzer_bot/api.py` chooses ToolCalling or CodeAgent based on `agent_type` and returns `timeseries` for charts.
- **Streamlit Tab:** "⚡ Earnings Momentum" in `streamlit_app.py` lets users tweak volume window, spike threshold, holding days, and max positions with Altair scatter plots of recent entries.

## Configuration Knobs
| Parameter | Default | Notes |
|-----------|---------|-------|
| `symbols` | `AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA` | Any comma-separated universe |
| `period` | `6mo` | Any yfinance-supported period (`3mo`, `1y`, `max`, ...) |
| `volume_window` | `20` | Rolling window for average volume (min 5) |
| `volume_multiplier` | `2.0` | Minimum spike multiple to trigger entries |
| `hold_days` | `5` | Trading bars to hold each position |
| `max_positions` | `3` | Caps concurrent exposure |

## Usage Examples
- **Python (direct MCP wrapper):**
  ```python
  from stock_analyzer_bot.tools import earnings_momentum_analysis
  print(earnings_momentum_analysis(symbols="AAPL,MSFT,TSLA", period="6mo", volume_multiplier=1.8))
  ```
- **FastAPI:**
  ```bash
  curl -X POST http://localhost:8000/earnings_momentum \
    -H "Content-Type: application/json" \
    -d '{
      "symbols": "AAPL,MSFT,NVDA",
      "period": "6mo",
      "volume_window": 20,
      "volume_multiplier": 2.2,
      "hold_days": 5,
      "max_positions": 3,
      "agent_type": "tool_calling"
    }'
  ```
- **Streamlit:** open the "⚡ Earnings Momentum" tab, adjust sliders, and click **Run Earnings Momentum**.

## Operational Notes
- The tool is intentionally **low-level**: both agents rely on it, ensuring consistent metrics regardless of LLM formatting.
- Limiting positions keeps the simulation conservative and avoids portfolio over-concentration.
- Volume statistics need at least `volume_window` warm-up bars; short periods may yield fewer signals.
- Responses cap trades/signals to 200 entries to prevent oversized payloads.
