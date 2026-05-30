# Estrategia Bollinger Z-Score (Mean Reversion)

## Qué mide la estrategia
- Reversión a la media estadística pura usando Z-Score del precio frente a una media móvil.
- Señala estados de sobrecompra/sobreventa según desviaciones estándar.

## Datos y preparación
- Fuente: Yahoo Finance OHLCV vía `yfinance` (velas diarias, período configurable).
- Defaults: `period=1y`, `window=20`.

## Cálculo
- Calcular media y desviación estándar rodante sobre `window`.
- Z-Score = (precio − media) / std.
- Clasificar zonas: sobrevendido extremo (Z < -2), sobrevendido (Z < -1), neutral (|Z| < 1), sobrecomprado (Z > 1), sobrecomprado extremo (Z > 2).
- Opcional: combinar con guardas de tendencia/riesgo; derivar señal y score.

## Salidas (MCP Tool)
- Métricas: score, señal BUY/SELL/HOLD, retornos vs. buy-and-hold, Sharpe, max drawdown.
- Interpretación sobre Z-Score actual, distancia a la media y banderas de precaución.

## Implementación en este repo
- MCP tool: `analyze_bollinger_zscore_performance` en `server/strategies/bollinger_zscore.py`.
- Wrapper smolagents: `bollinger_zscore_analysis` (indirecto vía conjuntos de estrategia) y parte de reportes de alto nivel.
- Usado en el reporte integral single-stock y en el escáner multi-acción; accesible en flujos ToolCallingAgent y CodeAgent.

## Parámetros clave
- `period`: lookback (ej. 6mo, 1y, 2y).
- `window`: ventana rodante para media/std (default 20).

## Uso rápido
- Llamada de alto nivel (incluida en reporte integral): `comprehensive_performance_report(symbol="AAPL", period="1y")`.
- En escaneo multi-acción: `unified_market_scanner(symbols="AAPL,MSFT,GOOGL", period="1y")`.
