# Estrategia MACD + Donchian

## Qué mide la estrategia
- Combina momentum de MACD con contexto de breakout de Donchian Channels.
- Busca breakouts o reversiones confirmadas por momentum usando crossovers y posición en el canal.

## Datos y preparación
- Fuente: Yahoo Finance OHLCV vía `yfinance` (velas diarias, período configurable).
- Defaults: `period=1y`, `donchian_period=20`, `macd_fast=12`, `macd_slow=26`, `macd_signal=9`.

## Cálculo
- Calcular línea MACD (EMA rápida − EMA lenta), línea de señal y histograma.
- Calcular bandas Donchian superior/inferior sobre `donchian_period` de highs/lows.
- Evaluar estados de crossover (MACD vs. signal, MACD vs. cero) y precio vs. canales.
- Agregar en un score combinado y señal discreta (BUY/SELL/HOLD).

## Salidas (MCP Tool)
- Métricas: score, señal, retornos vs. buy-and-hold, Sharpe, max drawdown.
- Narrativa sobre estado de momentum, contexto de breakout/mean-reversion y notas de riesgo.

## Implementación en este repo
- MCP tool: `analyze_macd_donchian_performance` en `server/strategies/macd_donchian.py`.
- Wrapper smolagents: `macd_donchian_analysis` en `stock_analyzer_bot/tools.py`.
- Consumido por ToolCallingAgent y CodeAgent; expuesto vía `/technical`, `/scanner`, `/multisector`, `/combined`.

## Parámetros clave
- `period`: lookback (ej. 6mo, 1y, 2y).
- `donchian_period`: ventana del canal (default 20).
- `macd_fast`, `macd_slow`, `macd_signal`: longitudes EMA de MACD (12/26/9 por defecto).

## Uso rápido
- Llamada wrapper: `macd_donchian_analysis(symbol="MSFT", period="1y")`.
- Disponible en pestaña Technical y Market Scanner vía API.
