# stock_analyzer_bot  Methods and Functions Reference

This document lists all module-level functions and class methods currently defined under `stock_analyzer_bot/`.

## `stock_analyzer_bot/__init__.py`

### Module Functions

- None

### Classes and Methods

- None

## `stock_analyzer_bot/adk_bot.py`

### Module Functions

- `_load_analysis_strategy_catalog()` (line 45)
  - Load analysis strategy catalog.
- `_catalog_entry_for_analysis_type(analysis_type)` (line 54)
  - Resolve entry for analysis type.
- `_taxonomy_contract_block(entry)` (line 73)
  - Build contract block.
- `_find_taxonomy_violations(report, entry, raw_tool_output)` (line 91)
  - Find taxonomy violations.
- `_extract_mode_from_context(analysis_context)` (line 134)
  - Extract mode from context from the provided input.
- `_extract_mode_scope_from_context(analysis_context)` (line 155)
  - Extract mode scope from context from the provided input.
- `_extract_risk_profile_from_context(analysis_context)` (line 170)
  - Extract risk profile from context from the provided input.
- `_with_mode_risk_header(report, analysis_context)` (line 179)
  - Return content with mode risk header applied.
- `_find_technical_mode_violations(report, analysis_context)` (line 206)
  - Find technical mode violations.
- `_extract_metric(raw, label)` (line 235)
  - Extract metric from the provided input.
- `_format_macd_donchian_analysis_from_raw(raw, symbol, period, fast_period, slow_period, signal_period, window)` (line 244)
  - Format macd donchian analysis output from raw tool data.
- `_format_bollinger_fibonacci_analysis_from_raw(raw, symbol, period, window, num_std, window_swing_points)` (line 282)
  - Format bollinger fibonacci analysis output from raw tool data.
- `_format_dual_ma_analysis_from_raw(raw, symbol, period, short_period, long_period, ma_type)` (line 342)
  - Format dual ma analysis output from raw tool data.
- `_is_bad_adk_report(adk_report, raw_tool_output)` (line 399)
  - Return whether bad adk report.
- `_run_pipeline_sync(analysis_type, user_goal, raw_tool_output, model_id, analysis_context=)` (line 648)
  - Implement run pipeline sync.
- `_technical_mode_context(mode, risk_profile)` (line 664)
  - Implement technical mode context.
- `_scanner_mode_context(mode, risk_profile)` (line 704)
  - Implement scanner mode context.
- `_multisector_mode_context(mode, risk_profile)` (line 733)
  - Implement multisector mode context.
- `_combined_technical_mode_context(mode, risk_profile)` (line 762)
  - Implement combined technical mode context.
- `_normalize_mode(value, default=)` (line 791)
  - Normalize mode values.
- `_normalize_risk_profile(value, default=)` (line 800)
  - Normalize risk profile values.
- `run_technical_analysis(symbol, period=, technical_mode=, risk_profile=, model_id=, **_)` (line 809)
  - Run technical analysis.
- `run_market_scanner(symbols, period=, scanner_mode=, risk_profile=, model_id=, **_)` (line 865)
  - Run market scanner.
- `run_fundamental_analysis(symbol, period=, model_id=, **_)` (line 887)
  - Run fundamental analysis.
- `run_multi_sector_analysis(sectors, period=, multisector_mode=, risk_profile=, model_id=, **_)` (line 900)
  - Run multi sector analysis.
- `run_combined_analysis(symbol, technical_period=, fundamental_period=, technical_mode=, risk_profile=, model_id=, **_)` (line 926)
  - Run combined analysis.
- `run_earnings_momentum_analysis(symbols, period=, volume_window=, volume_multiplier=, hold_days=, max_positions=, model_id=, **_)` (line 981)
  - Run earnings momentum analysis.
- `run_trin_breadth_analysis(period=, window=, band_k=, use_log=, model_id=, **_)` (line 1005)
  - Run trin breadth analysis.
- `run_overnight_gap_analysis(symbol, lookback_days=, min_gap_pct=, model_id=, **_)` (line 1020)
  - Run overnight gap analysis.
- `run_bollinger_breakout_analysis(symbol=, period=, bb_period=, bb_std=, atr_period=, volume_window=, volume_multiplier=, warmup_bars=, model_id=, **_)` (line 1034)
  - Run bollinger breakout analysis.
- `run_gap_fade_analysis(symbol=, period=, gap_threshold=, hold_minutes=, position_size=, model_id=, **_)` (line 1066)
  - Run gap fade analysis.
- `run_multi_timeframe_analysis(symbol=, period=, sma_fast=, sma_slow=, rsi_period=, rsi_oversold=, rsi_exit=, warmup_days=, model_id=, **_)` (line 1091)
  - Run multi timeframe analysis.
- `run_pairs_trading_analysis(symbol_a=, symbol_b=, period=, window=, entry_threshold=, exit_threshold=, position_size=, warmup_period=, model_id=, **_)` (line 1123)
  - Run pairs trading analysis.
- `run_statistical_arbitrage_analysis(symbols=, period=, window=, entry_threshold=, exit_threshold=, position_size=, warmup_period=, model_id=, **_)` (line 1155)
  - Run statistical arbitrage analysis.
- `run_vix_term_structure_analysis(symbol=, period=, front_window=, back_window=, contango_threshold=, backwardation_threshold=, long_position_size=, short_position_size=, warmup_period=, model_id=, **_)` (line 1185)
  - Run vix term structure analysis.
- `run_volatility_regime_analysis(period=, spy_symbol=, qqq_symbol=, arkk_symbol=, tlt_symbol=, gld_symbol=, vol_window=, high_vol_threshold=, low_vol_threshold=, warmup_period=, model_id=, **_)` (line 1220)
  - Run volatility regime analysis.
- `run_bollinger_zscore_analysis(symbol=, period=, model_id=, **_)` (line 1256)
  - Run bollinger zscore analysis.
- `run_bollinger_zscore_rsi_strategy_analysis(symbol=, period=, bb_window=, bb_std=, rsi_period=, rsi_oversold=, rsi_overbought=, zscore_buy_threshold=, zscore_sell_threshold=, model_id=, **_)` (line 1269)
  - Run bollinger zscore rsi strategy analysis.
- `run_bollinger_fibonacci_analysis(symbol=, period=, window=, num_std=, window_swing_points=, model_id=, **_)` (line 1304)
  - Run bollinger fibonacci analysis.
- `run_macd_donchian_analysis(symbol=, period=, fast_period=, slow_period=, signal_period=, window=, model_id=, **_)` (line 1343)
  - Run macd donchian analysis.
- `run_dual_moving_average_analysis(symbol=, period=, short_period=, long_period=, ma_type=, model_id=, **_)` (line 1385)
  - Run dual moving average analysis.

### Classes and Methods

- **Class `AgenticFinancePipeline`** (line 432)
  - Coordinate ADK agent orchestration and guarded report generation.
  - `__init__(self, model_id=)` (line 435)
    - Initialize instance state.
  - `_normalized_model(self)` (line 441)
    - Normalize d model values.
  - `_fallback_run_agent(self, instruction, prompt)` (line 450)
    - Implement fallback run agent.
  - `async _run_agent(self, name, instruction, prompt)` (line 463)
    - Implement run agent.
  - `async execute(self, analysis_type, user_goal, raw_tool_output, analysis_context=)` (line 473)
    - Implement execute.

## `stock_analyzer_bot/adk_bridge.py`

### Module Functions

- `async make_agent_caller(agent, initial_state=)` (line 40)
  - Create agent caller.

### Classes and Methods

- **Class `AgentCaller`** (line 11)
  - Wrap ADK runner/session interactions for reusable agent calls.
  - `__init__(self, agent, runner, user_id, session_id)` (line 14)
    - Initialize instance state.
  - `async call(self, query)` (line 22)
    - Implement call.

## `stock_analyzer_bot/api.py`

### Module Functions

- `async healthcheck()` (line 431)
  - Handle API healthcheck lifecycle behavior.
- `_adk_model(request_model_id)` (line 472)
  - Resolve model.
- `async technical_analysis(request)` (line 479)
  - Implement technical analysis.
- `async market_scanner(request)` (line 512)
  - Implement market scanner.
- `async fundamental_analysis(request)` (line 545)
  - Implement fundamental analysis.
- `async multi_sector_analysis(request)` (line 570)
  - Implement multi sector analysis.
- `async combined_analysis(request)` (line 604)
  - Implement combined analysis.
- `async earnings_momentum(request)` (line 638)
  - Implement earnings momentum.
- `async trin_breadth_analysis(request)` (line 687)
  - Implement trin breadth analysis.
- `async overnight_gaps(request)` (line 727)
  - Implement overnight gaps.
- `async bollinger_breakout(request)` (line 765)
  - Implement bollinger breakout.
- `async gap_fade(request)` (line 816)
  - Implement gap fade.
- `async multi_timeframe(request)` (line 859)
  - Implement multi timeframe.
- `async pairs_trading(request)` (line 908)
  - Implement pairs trading.
- `async statistical_arbitrage(request)` (line 958)
  - Implement statistical arbitrage.
- `async vix_term_structure(request)` (line 1005)
  - Implement vix term structure.
- `async volatility_regime(request)` (line 1056)
  - Implement volatility regime.
- `async bollinger_zscore_rsi(request)` (line 1109)
  - Implement bollinger zscore rsi.
- `async bollinger_fibonacci(request)` (line 1160)
  - Implement bollinger fibonacci.
- `async macd_donchian(request)` (line 1206)
  - Implement macd donchian.
- `async dual_moving_average(request)` (line 1254)
  - Implement dual moving average.
- `async startup_event()` (line 1300)
  - Handle API startup event lifecycle behavior.
- `async shutdown_event()` (line 1313)
  - Handle API shutdown event lifecycle behavior.

### Classes and Methods

- **Class `TechnicalAnalysisRequest`** (line 84)
  - Pydantic request model for TechnicalAnalysis API payloads.
  - No methods
- **Class `MarketScannerRequest`** (line 106)
  - Pydantic request model for MarketScanner API payloads.
  - No methods
- **Class `FundamentalAnalysisRequest`** (line 128)
  - Pydantic request model for FundamentalAnalysis API payloads.
  - No methods
- **Class `SectorConfig`** (line 142)
  - Represent SectorConfig behavior and related operations.
  - No methods
- **Class `MultiSectorAnalysisRequest`** (line 149)
  - Pydantic request model for MultiSectorAnalysis API payloads.
  - No methods
- **Class `CombinedAnalysisRequest`** (line 171)
  - Pydantic request model for CombinedAnalysis API payloads.
  - No methods
- **Class `EarningsMomentumRequest`** (line 194)
  - Pydantic request model for EarningsMomentum API payloads.
  - No methods
- **Class `TrinAnalysisRequest`** (line 212)
  - Pydantic request model for TrinAnalysis API payloads.
  - No methods
- **Class `OvernightGapRequest`** (line 226)
  - Pydantic request model for OvernightGap API payloads.
  - No methods
- **Class `BollingerBreakoutRequest`** (line 239)
  - Pydantic request model for BollingerBreakout API payloads.
  - No methods
- **Class `GapFadeRequest`** (line 256)
  - Pydantic request model for GapFade API payloads.
  - No methods
- **Class `MultiTimeframeRequest`** (line 270)
  - Pydantic request model for MultiTimeframe API payloads.
  - No methods
- **Class `PairsTradingRequest`** (line 287)
  - Pydantic request model for PairsTrading API payloads.
  - No methods
- **Class `StatisticalArbitrageRequest`** (line 304)
  - Pydantic request model for StatisticalArbitrage API payloads.
  - No methods
- **Class `VixTermStructureRequest`** (line 320)
  - Pydantic request model for VixTermStructure API payloads.
  - No methods
- **Class `VolatilityRegimeRequest`** (line 338)
  - Pydantic request model for VolatilityRegime API payloads.
  - No methods
- **Class `BollingerZscoreRsiStrategyRequest`** (line 357)
  - Pydantic request model for BollingerZscoreRsiStrategy API payloads.
  - No methods
- **Class `BollingerFibonacciRequest`** (line 375)
  - Pydantic request model for BollingerFibonacci API payloads.
  - No methods
- **Class `MacdDonchianRequest`** (line 389)
  - Pydantic request model for MacdDonchian API payloads.
  - No methods
- **Class `DualMovingAverageRequest`** (line 404)
  - Pydantic request model for DualMovingAverage API payloads.
  - No methods
- **Class `AnalysisResponse`** (line 418)
  - Pydantic response model for Analysis API responses.
  - No methods

## `stock_analyzer_bot/main.py`

### Module Functions

- None

### Classes and Methods

- None

## `stock_analyzer_bot/mcp_client.py`

### Module Functions

- `_resolve_default_path()` (line 151)
  - Implement resolve default path.
- `configure_session(server_path=)` (line 160)
  - Configure (or reconfigure) the shared MCP session.
- `get_session()` (line 170)
  - Get session.
- `shutdown_session()` (line 179)
  - Shutdown session.

### Classes and Methods

- **Class `MCPFinanceSession`** (line 21)
  - Manage a long-lived connection to the finance MCP server.
  - `__init__(self, server_path=, command=)` (line 24)
    - Initialize instance state.
  - `server_path(self)` (line 39)
    - Implement server path.
  - `set_server_path(self, new_path)` (line 44)
    - Implement set server path.
  - `_ensure_started(self)` (line 53)
    - Implement ensure started.
  - `async _session_lifecycle(self)` (line 74)
    - Implement session lifecycle.
  - `async _async_call_tool(self, tool_name, parameters)` (line 94)
    - Implement async call tool.
  - `call_tool(self, tool_name, parameters)` (line 112)
    - Call tool.
  - `async _async_signal_shutdown(self)` (line 122)
    - Implement async signal shutdown.
  - `close(self)` (line 128)
    - Implement close.

## `stock_analyzer_bot/mcp_tools.py`

### Module Functions

- `configure_finance_tools(server_path=)` (line 13)
  - Configure finance tools.
- `shutdown_finance_tools()` (line 19)
  - Shutdown finance tools.
- `_normalize_symbol(symbol)` (line 25)
  - Normalize symbol values.
- `_call_finance_tool(tool_name, parameters)` (line 34)
  - Implement call finance tool.
- `comprehensive_performance_report(symbol, period=)` (line 44)
  - Implement comprehensive performance report.
- `unified_market_scanner(symbols, period=, output_format=)` (line 54)
  - Implement unified market scanner.
- `fundamental_analysis_report(symbol, period=)` (line 65)
  - Implement fundamental analysis report.
- `earnings_momentum_analysis(symbols, period=, volume_window=, volume_multiplier=, hold_days=, max_positions=)` (line 75)
  - Implement earnings momentum analysis.
- `trin_market_breadth_analysis(period=, window=, band_k=, use_log=)` (line 96)
  - Implement trin market breadth analysis.
- `overnight_gap_analysis(symbol, lookback_days=, min_gap_pct=)` (line 113)
  - Implement overnight gap analysis.
- `bollinger_breakout_analysis(symbol=, period=, bb_period=, bb_std=, atr_period=, volume_window=, volume_multiplier=, warmup_bars=)` (line 124)
  - Implement bollinger breakout analysis.
- `gap_fade_analysis(symbol=, period=, gap_threshold=, hold_minutes=, position_size=)` (line 149)
  - Implement gap fade analysis.
- `multi_timeframe_analysis(symbol=, period=, sma_fast=, sma_slow=, rsi_period=, rsi_oversold=, rsi_exit=, warmup_days=)` (line 168)
  - Implement multi timeframe analysis.
- `pairs_trading_analysis(symbol_a=, symbol_b=, period=, window=, entry_threshold=, exit_threshold=, position_size=, warmup_period=)` (line 193)
  - Implement pairs trading analysis.
- `statistical_arbitrage_analysis(symbols=, period=, window=, entry_threshold=, exit_threshold=, position_size=, warmup_period=)` (line 218)
  - Implement statistical arbitrage analysis.
- `vix_term_structure_analysis(symbol=, period=, front_window=, back_window=, contango_threshold=, backwardation_threshold=, long_position_size=, short_position_size=, warmup_period=)` (line 241)
  - Implement vix term structure analysis.
- `volatility_regime_analysis(period=, spy_symbol=, qqq_symbol=, arkk_symbol=, tlt_symbol=, gld_symbol=, vol_window=, high_vol_threshold=, low_vol_threshold=, warmup_period=)` (line 268)
  - Implement volatility regime analysis.
- `bollinger_zscore_analysis(symbol=, period=)` (line 297)
  - Implement bollinger zscore analysis.
- `bollinger_zscore_rsi_strategy_analysis(symbol=, period=, bb_window=, bb_std=, rsi_period=, rsi_oversold=, rsi_overbought=, zscore_buy_threshold=, zscore_sell_threshold=)` (line 307)
  - Implement bollinger zscore rsi strategy analysis.
- `bollinger_fibonacci_analysis(symbol=, period=, window=, num_std=, window_swing_points=)` (line 334)
  - Implement bollinger fibonacci analysis.
- `macd_donchian_analysis(symbol=, period=, fast_period=, slow_period=, signal_period=, window=)` (line 353)
  - Implement macd donchian analysis.
- `dual_moving_average_analysis(symbol=, period=, short_period=, long_period=, ma_type=)` (line 374)
  - Implement dual moving average analysis.

### Classes and Methods

- None
