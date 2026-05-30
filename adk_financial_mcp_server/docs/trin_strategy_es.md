# Estrategia de Amplitud TRIN (Arms Index)

## Qué mide la estrategia
- TRIN compara acciones en alza vs. baja **y** sus volúmenes para inferir presión compradora/vendedora intradía.
- Interpretación:
  - TRIN > 1 → presión vendedora; TRIN < 1 → presión compradora.
  - Extremos altos suelen coincidir con capitulación (señal contraria alcista); extremos bajos con euforia (contraria cautelosa).

## Canal de datos
- Fuente primaria: Yahoo Finance ticker `^TRIN` (con fallbacks `TRIN`, `TRINQ`).
- Fuente de respaldo: Nasdaq Data Link (datasets URC: `URC/NYSE_ADV`, `URC/NYSE_DEC`, `URC/NYSE_ADV_VOL`, `URC/NYSE_DEC_VOL`) cuando existe `NASDAQ_DATA_LINK_API_KEY` o `QUANDL_API_KEY`.
- Fallback de períodos: período solicitado → 1y → 2y → 5y → max; última opción rango explícito desde 2000-01-01.

## Construcción del indicador
- Log transform opcional (por defecto activado) para estabilizar varianza.
- Media y desviación estándar rodante sobre ventana configurable (default 20 días).
- Bandas tipo Bollinger usando `band_k` desviaciones (default 1.5) para señalar extremos.

## Salidas (MCP Tool)
- Resumen markdown con TRIN actual, media, bandas, estado de banda, cambio 5d y rationale.
- Dict de métricas: `signal`, `bias`, `band_state`, `trin`, `ma`, `upper`, `lower`, `change_5d_pct`, `rationale`, y `timeseries` (capado por seguridad).
- Timeseries: fecha, trin, ma, upper, lower (para graficar en Streamlit).

## Implementación en este repo
- MCP tool: `analyze_trin_breadth` en `server/strategies/trin_strategy.py` (registrado vía `register_trin_strategy_tools` en `server/main.py`).
- Endpoint FastAPI: `POST /trin` en `stock_analyzer_bot/api.py` con dos modos:
  - `agent_type = "mcp_tool"` (default): devuelve el resumen/métricas crudas del MCP tool.
  - `agent_type = "code_agent"`: CodeAgent lee el JSON y produce un brief conciso.
- Pestaña Streamlit: "🧮 TRIN Breadth" en `streamlit_app.py`, con toggle CodeAgent y gráfica Altair desde timeseries.
- Prompt de agente: `TRIN_ANALYSIS_PROMPT` en `stock_analyzer_bot/main_codeagent.py` guía la síntesis.

## Parámetros
- `period` (3mo, 6mo, 1y, 2y, etc.).
- `window` (media/std rodante, default 20).
- `band_k` (ancho de banda en std dev, default 1.5).
- `use_log` (bool, default true).

## Notas operativas
- Nasdaq Data Link requiere `NASDAQ_DATA_LINK_API_KEY` o `QUANDL_API_KEY` para el fallback.
- Si CodeAgent no está disponible, el endpoint cae al MCP tool determinista.
- Timeseries se recorta para evitar payloads grandes en UI/clients.

## Ejemplos rápidos
- MCP tool directo: manejado por `/trin` con `agent_type = "mcp_tool"`.
- Wrapper Python: `trin_market_breadth_analysis(period="6mo", window=20, band_k=1.5, use_log=True)` desde `stock_analyzer_bot.tools`.
- Resumen con CodeAgent: `/trin` con `agent_type = "code_agent"` o `run_trin_breadth_analysis` en `main_codeagent.py`.
