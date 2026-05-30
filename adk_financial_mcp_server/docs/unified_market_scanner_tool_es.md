# Escáner de Mercado Unificado (Herramienta de Alto Nivel)

## Propósito
- Escáner multiactivo en una sola llamada: ejecuta las cuatro estrategias técnicas en cada símbolo, ordena oportunidades y devuelve un reporte estructurado en markdown.

## Datos y Fuentes
- OHLCV de Yahoo Finance vía `yfinance` (velas diarias) para cada símbolo provisto.
- `period` configurable (p. ej., 6mo, 1y) y `output_format` (detailed/summary/executive).

## Qué Produce
- Resumen ejecutivo con contexto de mercado.
- Tabla ordenada de símbolos con señales/calificaciones.
- Mini-secciones por acción con puntos clave de cada estrategia (Bollinger+Fibonacci, MACD+Donchian, Connors RSI+Z-Score, Dual MA).
- Recomendaciones tipo portafolio y notas de riesgo.

## Implementación en este Repo
- Herramienta MCP: `market_scanner` en `server/strategies/unified_market_scanner.py` (registrada en `server/main.py`).
- Wrapper Smolagents: `unified_market_scanner` en `stock_analyzer_bot/tools.py` (HIGH_LEVEL_TOOLS).
- FastAPI: usada por `/scanner` cuando `agent_type = "tool_calling"`; también invocada por sector en `/multisector` (ruta tool-calling).
- Streamlit: la pestaña Market Scanner (modo ToolCallingAgent) llama esta herramienta para escaneos multi-acción.

## Parámetros Clave
- `symbols`: tickers separados por comas (requerido).
- `period`: ventana histórica (por defecto 1y).
- `output_format`: `detailed`, `summary` o `executive` (por defecto detailed).

## Uso Rápido
- Wrapper Python: `unified_market_scanner(symbols="AAPL,MSFT,GOOGL", period="1y")`.
- FastAPI: `POST /scanner` con `agent_type="tool_calling"`.

## Cuándo Usar
- Ranking rápido y consistente de muchos símbolos en una sola llamada.
- Ideal para producción cuando latencia y costo importan más que el control granular.
