# Estrategia Dual Moving Average

## Qué mide la estrategia
- Trend-following clásico con cruce de medias móvil corta vs. larga.
- Detecta cambios de régimen: Golden Cross (alcista) y Death Cross (bajista).

## Datos y preparación
- Fuente: Yahoo Finance OHLCV vía `yfinance` (velas diarias, período configurable).
- Defaults: `period=2y`, `short_period=50`, `long_period=200`, `ma_type="EMA"` (SMA opcional).

## Cálculo
- Calcular medias móviles corta y larga (EMA/SMA según `ma_type`).
- Identificar crossovers y sesgo de tendencia (precio sobre/bajo la MA larga).
- Backtest de entradas/salidas en eventos de cruce; comparar vs. buy-and-hold.

## Salidas (MCP Tool)
- Métricas: retorno total, exceso vs. buy-and-hold, win rate, Sharpe, max drawdown, número de trades, último estado de cruce.
- Señal: BUY/SELL/HOLD según cruce reciente y alineación de MAs.
- Comentario sobre fuerza de tendencia y riesgo.

## Implementación en este repo
- MCP tool: `analyze_dual_ma_strategy` en `server/strategies/dual_moving_average.py`.
- Wrapper smolagents: `dual_moving_average_analysis` en `stock_analyzer_bot/tools.py`.
- Incluida en flujos ToolCallingAgent y CodeAgent; expuesta vía `/technical`, `/scanner`, `/multisector`, `/combined`.

## Parámetros clave
- `period`: ventana de lookback (ej. 1y, 2y, 5y).
- `short_period`, `long_period`: longitudes de MAs (defaults 50/200).
- `ma_type`: `EMA` (default) o `SMA`.

## Uso rápido
- Llamada wrapper: `dual_moving_average_analysis(symbol="TSLA", period="2y", short_period=50, long_period=200)`.
- Visible en pestaña Technical y en salidas de Market Scanner.
