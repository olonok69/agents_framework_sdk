# Reporte Integral de Desempeño (Herramienta de Alto Nivel)

## Propósito
- Reporte técnico multiestrategia en una sola llamada para un símbolo.
- Ejecuta las cuatro estrategias de bajo nivel (Bollinger+Fibonacci, MACD+Donchian, Connors RSI+Z-Score, Dual Moving Average) y compila un informe ejecutivo en markdown con métricas, señales y guía.

## Datos y Fuentes
- OHLCV de Yahoo Finance vía `yfinance` (velas diarias), periodo configurable por usuario (p. ej., 3mo, 6mo, 1y, 2y, 5y).

## Qué Produce
- Resumen ejecutivo con recomendación y confianza.
- Detalle por estrategia: puntaje, señal (BUY/SELL/HOLD), retorno vs. buy-and-hold, Sharpe, drawdown máximo y fundamento.
- Tabla comparativa agregada y notas de riesgo/sizeo de posición.

## Implementación en este Repo
- Herramienta MCP: `generate_comprehensive_analysis_report` en `server/strategies/comprehensive_analysis.py` (registrada en `server/main.py`).
- Wrapper Smolagents: `comprehensive_performance_report` en `stock_analyzer_bot/tools.py` (HIGH_LEVEL_TOOLS).
- FastAPI: usada por `/technical` cuando `agent_type = "tool_calling"`.
- Streamlit: la pestaña Technical (modo ToolCallingAgent) llama esta herramienta para un análisis de una sola acción.

## Parámetros Clave
- `symbol`: ticker (requerido).
- `period`: ventana histórica (por defecto 1y).

## Uso Rápido
- Wrapper Python: `comprehensive_performance_report(symbol="AAPL", period="1y")`.
- FastAPI: `POST /technical` con `agent_type="tool_calling"`.

## Cuándo Usar
- Visión técnica rápida y determinista de una acción con una llamada MCP.
- Ideal para producción: baja latencia y bajo costo/token.
