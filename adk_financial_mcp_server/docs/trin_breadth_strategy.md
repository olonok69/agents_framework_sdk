# TRIN (Arms Index) Breadth Strategy

## What the Strategy Measures
- Market breadth using synthetic TRIN (Arms Index) proxy
- Price/volume divergence to detect buying vs. selling pressure
- Contrarian signals at market extremes (panic and euphoria)

## Strategy Logic

### TRIN Calculation (Synthetic)
Since actual TRIN data requires real-time advancing/declining issues, this implementation uses:
- **Price momentum**: Intraday price change (close - open) / open
- **Volume ratio**: Current volume / 20-day average volume
- **Price vs. MA**: Distance from 20-day moving average

### Entry Conditions
- **High TRIN (Panic)**: Log(TRIN) > Upper Band (MA + 1.5σ) → BUY
  - Indicates extreme selling pressure / capitulation
  - Contrarian bullish signal
- **Position**: 95% allocation to SPY

### Exit Conditions
- **Low TRIN (Euphoria)**: Log(TRIN) < Lower Band (MA - 1.5σ) → SELL
  - Indicates weak buying / market euphoria
  - Contrarian bearish signal

### Statistical Bands
- **Rolling Window**: 20 days of TRIN values
- **Log Transform**: Stabilizes variance for better distribution
- **Bollinger-Style**: Mean ± 1.5 standard deviations

## Implementation Details

### Symbols
- **SPY**: S&P 500 ETF (primary trading vehicle and data source)

### Technical Indicators
- **Price SMA(20)**: 20-day simple moving average
- **Volume SMA(20)**: 20-day volume average
- **Rolling Window**: TRIN history storage

### Parameters
- `window`: 20 (rolling calculation period)
- `band_k`: 1.5 (standard deviation multiplier)
- `warmup_period`: 25 days
- `position_size`: 0.95 (95% allocation)

## Backtest Results (2015-2020)

### Performance Metrics
- **Net Profit**: +24.75%
- **Annual Return**: 4.52%
- **Sharpe Ratio**: 0.273
- **Sortino Ratio**: 0.157
- **Max Drawdown**: 9.7%

### Trade Statistics
- **Total Trades**: 74
- **Win Rate**: 70%
- **Average Win**: 1.78%
- **Average Loss**: -2.07%
- **Profit-Loss Ratio**: 0.86

### Risk Metrics
- **Drawdown Recovery**: 127 days
- **Portfolio Turnover**: 3.84%
- **Total Fees**: $197.75
- **Beta**: 0.261 (low market correlation)

## Strategy Strengths
1. **Market Timing**: Captures extremes in market sentiment
2. **Low Correlation**: Beta of 0.261 indicates independence from market
3. **High Win Rate**: 70% success demonstrates reliable extreme detection
4. **Simple Logic**: Clear statistical bands for entry/exit
5. **Long Testing Period**: 5 years includes various market conditions

## Strategy Weaknesses
1. **Low Sharpe Ratio**: 0.273 indicates modest risk-adjusted returns
2. **Deep Drawdowns**: 9.7% maximum drawdown higher than earnings strategy
3. **Slow Recovery**: 127 days to recover from drawdowns
4. **Synthetic TRIN**: Uses proxy instead of actual breadth data
5. **Whipsaw Risk**: May generate false signals in ranging markets

## Real TRIN vs. Synthetic TRIN

### Real TRIN Formula
```
TRIN = (Advancing Issues / Declining Issues) / (Advancing Volume / Declining Volume)
```

### Synthetic TRIN (This Implementation)
```python
if price_change < 0:
    # Negative price + high volume = high TRIN
    synthetic_trin = volume_ratio * (1 - price_change * 10)
else:
    # Positive price + low volume = high TRIN
    synthetic_trin = (2 - volume_ratio) * (1 + price_vs_ma * 5)
```

**Note**: Real TRIN data would improve accuracy but requires market breadth data feeds.

## Optimization Opportunities
- **Band Width**: Test 1.0-2.5 range for `band_k` parameter
- **Window Size**: Try 10-30 day rolling windows
- **Position Sizing**: Scale position size by TRIN extremity
- **Partial Exits**: Exit gradually as TRIN normalizes
- **Add Filter**: Combine with trend filter (SMA crossover)
- **Real Data**: Integrate actual TRIN data from NYSE/NASDAQ

## Usage with MCP Tools

### Compile & Test
```python
# Via AI assistant with MCP
"Compile the TRIN breadth strategy"
"Run a backtest from 2015 to 2020"
```

### Optimization
```python
{
  "name": "TRIN Band Optimization",
  "target": {"target": "SharpeRatio", "extremum": "max"},
  "parameters": [
    {"name": "window", "min": 10, "max": 30, "step": 5},
    {"name": "band_k", "min": 1.0, "max": 2.5, "step": 0.25}
  ],
  "constraints": [
    {"target": "Drawdown", "operator": "Less", "targetValue": 0.12}
  ]
}
```

### Live Deployment
```python
# Deploy to paper trading
"Deploy TRIN strategy to paper trading"
```

## Code Reference
- **File**: `main.py`
- **Class**: `Firstproject`
- **Algorithm Type**: Contrarian market timing
- **Data Frequency**: Daily bars
- **Dependencies**: numpy for statistical calculations

## Related Strategies
- VIX Term Structure (volatility-based timing)
- Volatility Regime Switch (regime-based allocation)
- Pairs Trading (mean reversion approach)

## References
- Arms Index (TRIN) by Richard Arms Jr.
- Market breadth indicators in technical analysis
- Contrarian trading strategies literature
- Bollinger Bands by John Bollinger
