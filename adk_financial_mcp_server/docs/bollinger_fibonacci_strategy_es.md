# Estrategia Bollinger + Fibonacci

## Qué mide la estrategia
- Detecta sobrecompra/sobreventa usando Bollinger Bands y confluencia con niveles de retroceso Fibonacci.
- Usa %B y el ancho de banda para evaluar posición de volatilidad; combina con niveles Fib en swing points para soporte/resistencia.

## Datos y preparación
- Fuente: Yahoo Finance OHLCV vía `yfinance` (velas diarias, período configurable).
- Defaults: `period=1y`, `window=20`, `num_std=2.0`, `window_swing_points=10`.

## Cálculo
- Calcular SMA sobre `window` y bandas superior/inferior a `num_std` desviaciones estándar.
- Calcular %B (posición dentro de las bandas) y el ancho de banda.
- Detectar swing highs/lows en `window_swing_points`; derivar niveles Fib entre el último swing high/low.
- Evaluar proximidad del precio a niveles Fib y extremos de banda; agregar en un score compuesto y señal.

## Salidas (MCP Tool)
- Métricas: score de estrategia, señal actual (BUY/SELL/HOLD), retornos vs. buy-and-hold, Sharpe, max drawdown.
- Interpretación con notas de confluencia band/Fib y apuntes de riesgo.

## Implementación en este repo
- MCP tool: `analyze_bollinger_fibonacci_performance` en `server/strategies/bollinger_fibonacci.py` (registrado en `server/main.py`).
- Wrapper smolagents: `bollinger_fibonacci_analysis` en `stock_analyzer_bot/tools.py`.
- Usado por ToolCallingAgent (reportes de una llamada), CodeAgent (loops multi-acción), endpoints FastAPI (`/technical`, `/scanner`, `/multisector`, `/combined`).

## Parámetros clave
- `period`: lookback (ej. 3mo, 6mo, 1y).
- `window`: ventana SMA Bollinger (default 20).
- `num_std`: ancho de banda en std dev (default 2.0).
- `window_swing_points`: ventana de detección de swings para anclas Fib (default 10).

## Uso rápido
- Llamada wrapper: `bollinger_fibonacci_analysis(symbol="AAPL", period="1y")`.
- Disponible en la pestaña Technical y en Market Scanner vía API/Streamlit.
