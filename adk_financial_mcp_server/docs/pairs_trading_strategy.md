# Pairs Trading (Mean Reversion) Strategy

## What the Strategy Measures
- Price spread relationship between correlated assets (SPY/QQQ)
- Statistical deviations from historical mean spread
- Mean reversion opportunities when spread diverges significantly

## Strategy Logic

### Spread Calculation
```python
spread = price_SPY / price_QQQ
z_score = (current_spread - mean_spread) / std_spread
```

### Entry Conditions
- **Long SPY / Short QQQ**: Z-score < -2.0
  - Spread abnormally low, expecting reversion upward
- **Short SPY / Long QQQ**: Z-score > +2.0
  - Spread abnormally high, expecting reversion downward
- **Position Size**: ±50% each leg (market-neutral)

### Exit Conditions
- **Mean Reversion**: |Z-score| < 0.5
  - Spread returns near historical mean
  - Close both legs simultaneously

### Statistical Foundation
- **Rolling Window**: 20 days of spread history
- **Z-Score Threshold**: ±2.0 standard deviations (entry)
- **Exit Threshold**: ±0.5 standard deviations (tight exit)

## Implementation Details

### Symbols
- **SPY**: S&P 500 ETF
- **QQQ**: Nasdaq 100 ETF

### Technical Indicators
- **Spread Ratio**: SPY/QQQ price ratio
- **Rolling Mean**: 20-day average spread
- **Rolling Std Dev**: 20-day standard deviation
- **Z-Score**: Standardized deviation measure

### Parameters
- `window`: 20 (rolling statistics period)
- `entry_threshold`: 2.0 (entry z-score)
- `exit_threshold`: 0.5 (exit z-score)
- `position_size`: 0.5 (50% per leg)
- `warmup_period`: 25 days

## Strategy Characteristics

### Market-Neutral Design
- Long one asset, short the other
- Dollar-neutral positions
- Hedges against broad market moves
- Profits from relative performance

### Correlation Requirement
SPY and QQQ typically maintain high correlation (0.85+) because:
- Both track US equities
- Significant overlap in holdings (large-cap tech)
- Respond similarly to macro factors

**When correlation breaks**, spreads widen → trading opportunities.

## Strategy Strengths
1. **Market-Neutral**: Limited exposure to market direction
2. **Statistical Basis**: Z-score provides objective entry/exit points
3. **High Probability**: Mean reversion is well-documented
4. **Low Correlation to Market**: Profits from relative moves, not absolute
5. **Defined Risk**: Spread has bounds based on correlation

## Strategy Weaknesses
1. **Correlation Risk**: If correlation breaks permanently, losses mount
2. **Spread Blow-Out**: Extreme events can cause spreads to widen indefinitely
3. **Capital Intensive**: Requires margin for short positions
4. **No Stop Loss**: Relies on mean reversion, no downside protection
5. **Timing Risk**: Mean reversion can take longer than expected

## Risk Factors

### What Can Go Wrong
- **Regime Change**: SPY and QQQ fundamentals diverge permanently
- **Sector Rotation**: Tech underperforms (hurts QQQ relative to SPY)
- **Leverage Decay**: Borrowing costs for short positions
- **Gap Risk**: Overnight moves can occur before reversion

### Risk Mitigation
- Monitor correlation continuously
- Add maximum holding period
- Implement stop-loss at z-score extremes (±4σ)
- Scale position size by correlation strength

## Optimization Opportunities
- **Entry Threshold**: Test 1.5-3.0 range for z-score entry
- **Exit Threshold**: Optimize 0.3-1.0 range for exits
- **Window Size**: Try 10-40 day rolling windows
- **Correlation Filter**: Only trade when correlation > 0.80
- **Dynamic Sizing**: Increase size when z-score is more extreme
- **Other Pairs**: Test XLF/XLK, GLD/SLV, IWM/SPY

## Usage with MCP Tools

### Compile & Test
```python
# Via AI assistant with MCP
"Compile the pairs trading strategy"
"Run a backtest from 2020 to 2022"
```

### Optimization
```python
{
  "name": "Pairs Trading Z-Score Optimization",
  "target": {"target": "SharpeRatio", "extremum": "max"},
  "parameters": [
    {"name": "entry_threshold", "min": 1.5, "max": 3.0, "step": 0.25},
    {"name": "exit_threshold", "min": 0.3, "max": 1.0, "step": 0.1},
    {"name": "window", "min": 10, "max": 40, "step": 5}
  ],
  "constraints": [
    {"target": "Drawdown", "operator": "Less", "targetValue": 0.10}
  ]
}
```

### Live Deployment
```python
# Deploy to paper trading
"Deploy pairs trading to paper trading with proper margin settings"
```

## Code Reference
- **File**: `main_pairs_trading.py`
- **Class**: `PairsTradingStrategy`
- **Algorithm Type**: Statistical arbitrage / Mean reversion
- **Data Frequency**: Daily bars
- **Dependencies**: numpy for statistical calculations

## Related Strategies
- Statistical Arbitrage (multi-asset basket)
- Volatility Regime Switch (pairs within regimes)
- Gap Fade (mean reversion on single asset)

## Academic References
- "Do Arbitrageurs Exist?" by Gatev, Goetzmann & Rouwenhorst
- Pairs trading literature in statistical arbitrage
- Co-integration and mean reversion studies
- Market-neutral hedge fund strategies

## Example Trades

### Trade 1: Spread Too High
```
Day 1: Z-score = +2.3
Action: Short SPY (-50%), Long QQQ (+50%)
Day 5: Z-score = +0.4
Action: Close both positions → Profit
```

### Trade 2: Spread Too Low
```
Day 1: Z-score = -2.1
Action: Long SPY (+50%), Short QQQ (-50%)
Day 7: Z-score = -0.3
Action: Close both positions → Profit
```
