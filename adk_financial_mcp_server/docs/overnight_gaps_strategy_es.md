# Estrategia de Gaps Nocturnos / Midnight Returns

## Qué mide la estrategia
- Compara la apertura de cada sesión contra el cierre previo para identificar gap-up/gap-down.
- Enfatiza el **fill intradía**: si el precio vuelve al cierre previo el mismo día.
- Captura el drift del mismo día desde la apertura al cierre para contexto.

## Canal de datos
- Fuente: velas diarias de Yahoo Finance vía `yfinance` (intervalo 1d).
- Lookback configurable (default 120 días), trae días extra para asegurar el cierre previo.
- Filtra gaps cuyo tamaño absoluto sea menor al umbral definido (default 1%).

## Cálculo
- Gap % = (open de hoy - close previo) / close previo * 100.
- Dirección: `up` si gap % > 0, `down` en caso contrario.
- Test de fill intradía (mismo día):
  - Gap up: se considera filled si el low del día ≤ close previo.
  - Gap down: se considera filled si el high del día ≥ close previo.
- Retorno de cierre mismo día: (close - open) / open * 100.

## Salidas (MCP Tool)
- Resumen markdown con totales, conteo up/down, fill rates (all/up/down), promedios de gaps, drift promedio y último gap.
- Dict de métricas con agregados y gaps recientes (últimos 5), más `timeseries` (capada a 200 filas).
- Timeseries: fecha, gap_pct, dirección, filled, prev_close, open, high, low, close, same_day_close_ret.

## Implementación en este repo
- MCP tool: `analyze_overnight_gaps` en `server/strategies/gap_strategy.py` (registrado vía `register_gap_strategy_tools` en `server/main.py`).
- Endpoint FastAPI: `POST /overnight_gaps` en `stock_analyzer_bot/api.py` con dos modos:
  - `agent_type = "mcp_tool"` (default): devuelve el resumen/métricas del MCP tool (y timeseries en la raíz de la respuesta para UI).
  - `agent_type = "code_agent"`: CodeAgent lee el JSON y genera un brief conciso.
- Pestaña Streamlit: "🌙 Overnight Gaps" en `streamlit_app.py`, con toggle de agente y gráfica Altair (barras + diamantes) desde timeseries.
- Prompt del agente: `OVERNIGHT_GAP_PROMPT` en `stock_analyzer_bot/main_codeagent.py`, incluye guardas de parsing JSON.

## Parámetros
- `lookback_days` (default 120; UI permite 30–400).
- `min_gap_pct` (default 1.0%; UI permite 0.1–10%).
- `agent_type`: herramienta MCP determinista vs. resumen con CodeAgent.

## Notas operativas
- Usa solo datos diarios (no requiere históricos intradía).
- El fill intradía se basa únicamente en high/low del día vs. close previo; no requiere barras de 30–60 minutos.
- Timeseries se recorta para evitar payloads grandes; las métricas incluyen últimos gaps destacados.

## Ejemplos rápidos
- Wrapper Python: `overnight_gap_analysis(symbol="AAPL", lookback_days=120, min_gap_pct=1.0)` desde `stock_analyzer_bot.tools`.
- API determinista: `POST /overnight_gaps` con `agent_type="mcp_tool"`.
- API con resumen LLM: `POST /overnight_gaps` con `agent_type="code_agent"`.
