# Estrategia Connors RSI + Z-Score

## Qué mide la estrategia
- Reversión a la media de corto plazo combinando componentes de Connors RSI con un overlay estadístico Z-Score.
- Detecta movimientos extendidos que pueden revertir en pocas sesiones.

## Datos y preparación
- Fuente: Yahoo Finance OHLCV vía `yfinance` (velas diarias, período configurable).
- Defaults típicos: `period=1y`, `rsi_period=3`, `streak_period=2`, `rank_period=100`, `zscore_window=20`, pesos (connors_weight=0.7, zscore_weight=0.3).

## Cálculo
- Componentes Connors RSI:
  - Price RSI sobre `rsi_period`.
  - Streak RSI sobre `streak_period` (longitud de rachas up/down).
  - Percent rank de retornos diarios sobre `rank_period`.
- Combinar los tres en un Connors RSI score.
- Calcular Z-Score de retornos/precios sobre `zscore_window`.
- Mezclar Connors RSI y Z-Score con los pesos; derivar bandas de señal (overbought/oversold) y score compuesto.

## Salidas (MCP Tool)
- Métricas: score compuesto, señal (BUY/SELL/HOLD), retornos vs. buy-and-hold, Sharpe, max drawdown.
- Interpretación sobre estado de sobrecompra/sobreventa, nota de riesgo y expectativa de mean reversion.

## Implementación en este repo
- MCP tool: `analyze_connors_zscore_performance` en `server/strategies/connors_zscore.py`.
- Wrapper smolagents: `connors_zscore_analysis` en `stock_analyzer_bot/tools.py`.
- Usado en flujos ToolCallingAgent y CodeAgent; accesible vía `/technical`, `/scanner`, `/multisector`, `/combined`.

## Parámetros clave
- `period`: lookback (ej. 6mo, 1y).
- `rsi_period`, `streak_period`, `rank_period`: componentes Connors RSI.
- `zscore_window`: lookback para Z-Score.
- `connors_weight`, `zscore_weight`: pesos de mezcla.

## Uso rápido
- Llamada wrapper: `connors_zscore_analysis(symbol="AAPL", period="1y")`.
- Disponible en pestaña Technical y Market Scanner.
