# Clasificación de estrategias por scoring (MCP Server)

Este documento clasifica las herramientas de estrategia/análisis del MCP server según cómo producen su resultado:

- **Basadas en score:** modelo numérico explícito (score compuesto, componentes ponderados o rangos normalizados).
- **Basadas en reglas:** lógica de umbrales/eventos/régimen y/o simulación de backtest sin score compuesto como motor principal.
- **Híbridas:** orquestan o agregan resultados score-driven y rule-driven.

## 1) Herramientas basadas en score

| Módulo | Herramientas MCP principales | Motivo |
|---|---|---|
| `server/strategies/bollinger_fibonacci.py` | `calculate_bollinger_fibonacci_score`, `analyze_bollinger_fibonacci_performance` | Usa `Strategy_Score` con componentes ponderados (BB, volatilidad, Fibonacci, momentum). |
| `server/strategies/macd_donchian.py` | `calculate_macd_score_tool`, `calculate_donchian_channel_score_tool`, `calculate_combined_score_macd_donchian`, `analyze_macd_donchian_performance` | MACD y Donchian producen scores normalizados; luego se combinan. |
| `server/strategies/connors_zscore.py` | `calculate_connors_rsi_score_tool`, `calculate_zscore_indicator_tool`, `calculate_combined_connors_zscore_tool`, `analyze_connors_zscore_performance` | Connors y Z-Score generan scores y un combinado ponderado. |
| `server/strategies/dual_moving_average.py` | `calculate_dual_ma_score`, `analyze_dual_ma_performance` | Score multi-componente (posición, fuerza de señal, momentum). |
| `server/strategies/bollinger_zscore.py` | `calculate_bollinger_z_score`, `analyze_bollinger_zscore_performance` | Interpreta distancia z-score con score/señal. |

## 2) Herramientas basadas en reglas

| Módulo | Herramientas MCP principales | Motivo |
|---|---|---|
| `server/strategies/bollinger_zscore_rsi.py` | `analyze_bollinger_zscore_rsi` | Entradas/salidas por umbrales de z-score + RSI. |
| `server/strategies/bollinger_breakout.py` | `analyze_bollinger_breakout` | Reglas de breakout (bandas/ATR/volumen). |
| `server/strategies/gap_strategy.py` | `analyze_overnight_gaps` | Clasificación de gaps + fill-rate/eventos. |
| `server/strategies/earnings_momentum.py` | `analyze_earnings_momentum` | Reglas de spike de volumen + ventana fija de salida. |
| `server/strategies/trin_strategy.py` | `analyze_trin_market_breadth` | Señal por bandas/régimen de TRIN. |
| `server/strategies/gap_fade.py` | `analyze_gap_fade` | Regla de umbral de gap + fade intradía. |
| `server/strategies/multi_timeframe.py` | `analyze_multi_timeframe` | Lógica por MA trend + RSI thresholds. |
| `server/strategies/pairs_trading.py` | `analyze_pairs_trading` | Umbrales de z-score de spread para entrada/salida. |
| `server/strategies/statistical_arbitrage.py` | `analyze_statistical_arbitrage` | Umbrales de desviación respecto a cesta. |
| `server/strategies/vix_term_structure.py` | `analyze_vix_term_structure` | Reglas por contango/backwardation. |
| `server/strategies/volatility_regime.py` | `analyze_volatility_regime` | Cambio de régimen por umbrales de volatilidad. |

## 3) Herramientas híbridas / orquestación

| Módulo | Herramientas MCP principales | Nota |
|---|---|---|
| `server/strategies/comprehensive_analysis.py` | `generate_comprehensive_analysis_report` | Orquesta varias estrategias (score y reglas). |
| `server/strategies/unified_market_scanner.py` | `market_scanner` | Agrega performance + señales actuales multi-estrategia. |
| `server/strategies/comprehensive_market_scanner.py` | helper scanner legacy | Orquestador auxiliar sobre múltiples estrategias. |
| `server/strategies/fundamental_analysis.py` | `generate_fundamental_analysis_report`, `index_financial_statement_rows` | Análisis fundamental; no es modelo de score de trading principal. |

## 4) Implicación práctica para reportes ADK

- **Score-driven:** explicar evolución del score, atribución por componentes y umbrales de decisión.
- **Rule-driven:** explicar qué reglas/umbrales se activaron, frecuencia de eventos, cambios de régimen y métricas de trades.
- **Híbridas:** describir explícitamente que el resultado sintetiza señales score-based y rule-based.

## 5) Fuentes de verdad

- Registro de herramientas: `server/tool_registry.py`
- Contrato de taxonomía: `docs/analysis_strategy_catalog.json`
- Wrappers ADK: `stock_analyzer_bot/mcp_tools.py`
