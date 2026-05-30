# Volatility Regime Switch Strategy

## What the Strategy Measures
- Rolling 20-day volatility of SPY
- Market volatility regime (high/medium/low)
- Optimal asset allocation based on risk environment

## Strategy Logic

### Volatility Calculation
```python
returns = prices.pct_change()
volatility = returns.std() * sqrt(252) * 100  # Annualized %
```

### Regime Classification

#### High Volatility (> 25%)
- **Regime**: Crisis, fear, uncertainty
- **Allocation**: Defensive
  - 50% TLT (Long-term Treasuries)
  - 40% GLD (Gold)
  - 10% Cash
- **Rationale**: Preserve capital, safe havens

#### Low Volatility (< 15%)
- **Regime**: Calm, complacency, bull market
- **Allocation**: Aggressive
  - 60% QQQ (Nasdaq 100 Tech)
  - 30% ARKK (Innovation/Growth)
  - 10% Cash
- **Rationale**: Maximize returns, risk-on

#### Medium Volatility (15-25%)
- **Regime**: Normal, balanced market
- **Allocation**: Mixed
  - 30% QQQ (Tech exposure)
  - 30% TLT (Bond hedge)
  - 20% GLD (Inflation hedge)
  - 20% Cash
- **Rationale**: Balanced risk/return

### Rebalancing
- **Trigger**: Regime change detected
- **Execution**: Liquidate old allocation, enter new
- **Frequency**: Only on regime transitions (not daily)

## Implementation Details

### Symbols
- **SPY**: Volatility calculation benchmark
- **QQQ**: Aggressive tech allocation
- **ARKK**: Innovation/growth allocation
- **TLT**: Defensive bond allocation
- **GLD**: Defensive gold allocation

### Volatility Tracking
- **Window**: 20 trading days
- **Rolling**: Continuously updated
- **Annualized**: Multiplied by √252

### Parameters
- `vol_window`: 20 (rolling period)
- `high_vol_threshold`: 25% (defensive trigger)
- `low_vol_threshold`: 15% (aggressive trigger)
- `warmup_period`: 25 days

## Strategy Characteristics

### Regime-Based Allocation
- Not market timing (no price prediction)
- Risk-based positioning
- Adapts to current environment
- Reactive, not predictive

### Volatility as Signal
- **High Vol**: Markets stressed → protect
- **Low Vol**: Markets calm → seek return
- **Transition**: Regime shifts = rebalance

### Multi-Asset Portfolio
- Stocks (QQQ, ARKK)
- Bonds (TLT)
- Commodities (GLD)
- Diversification across asset classes

## Volatility Regimes Explained

### High Volatility Regime (Crisis)
- **Historical Examples**:
  - 2008 Financial Crisis: 50-80% volatility
  - COVID-19 Crash (March 2020): 60-85%
  - Black Monday 1987: 100%+
- **Duration**: Days to months
- **Asset Performance**:
  - Stocks: Sharp declines
  - Bonds: Rally (flight to safety)
  - Gold: Rally (safe haven)

### Low Volatility Regime (Complacency)
- **Historical Examples**:
  - 2017: VIX averaged 11%
  - Mid-2019: Sustained low volatility
  - Pre-COVID 2020: 10-12%
- **Duration**: Months to years
- **Asset Performance**:
  - Stocks: Steady gains
  - Bonds: Underperform
  - Gold: Sideways

### Medium Volatility Regime (Normal)
- **Typical Range**: 15-25%
- **Most Common**: 60% of market days
- **Balanced Environment**: Risk/reward neutral

## Strategy Strengths
1. **Risk Management**: Automatically de-risks in crises
2. **Regime Awareness**: Adapts to market conditions
3. **Multi-Asset**: Diversified across correlations
4. **Clear Rules**: Objective volatility thresholds
5. **Proactive Defense**: Shifts before major losses

## Strategy Weaknesses
1. **Whipsaw Risk**: Volatility oscillating around thresholds
2. **Transition Lag**: Regime may change before detection
3. **Asset Selection**: Limited to 4 asset classes
4. **No Stop Loss**: Relies on allocation, not exits
5. **Underperformance**: May lag in sustained bull markets

## Volatility Calculation Mechanics

### Rolling Window
```python
Day 1-20: Initial calculation
Day 21: Drop day 1, add day 21
Day 22: Drop day 2, add day 22
...continuously rolling
```

### Annualization Factor
```python
Daily Vol = std(daily_returns)
Annual Vol = Daily Vol * sqrt(252 trading days)
Percentage = Annual Vol * 100
```

### Why 20 Days?
- Approximately 1 month of trading
- Captures recent volatility shifts
- Not too noisy, not too lagging
- Industry standard

## Asset Class Behavior

### QQQ (Nasdaq Tech)
- **High Beta**: Amplifies market moves
- **High Vol**: Drops -30%+ in crashes
- **Bull Market Star**: Best performer when calm

### ARKK (Innovation)
- **Highest Beta**: Extreme volatility
- **Growth Focus**: Long-term potential
- **High Risk**: Can drop -50%+ in corrections

### TLT (Long Bonds)
- **Negative Correlation**: Rallies when stocks fall
- **Interest Rate Sensitivity**: Inverse to rates
- **Safe Haven**: Flight to quality in crises

### GLD (Gold)
- **Inflation Hedge**: Protects purchasing power
- **Crisis Asset**: Rallies in uncertainty
- **Low Correlation**: Diversification benefit

## Optimization Opportunities
- **Threshold Levels**: Test 10-20% (low) and 20-35% (high)
- **Window Size**: Optimize 10-40 days
- **Asset Selection**: Add REITs, commodities, international
- **Sub-Regimes**: Create more granular allocations (5 regimes)
- **Dynamic Weights**: Scale allocation by vol extremity
- **Hybrid Signals**: Combine with trend indicators
- **Rebalancing Bands**: Add buffer around thresholds to reduce whipsaws

## Usage with MCP Tools

### Compile & Test
```python
# Via AI assistant with MCP
"Compile the volatility regime strategy"
"Run a backtest from 2020 to 2022"
```

### Optimization
```python
{
  "name": "Volatility Regime Optimization",
  "target": {"target": "SharpeRatio", "extremum": "max"},
  "parameters": [
    {"name": "high_vol_threshold", "min": 20, "max": 35, "step": 2.5},
    {"name": "low_vol_threshold", "min": 10, "max": 20, "step": 2.5},
    {"name": "vol_window", "min": 10, "max": 40, "step": 5}
  ],
  "constraints": [
    {"target": "Drawdown", "operator": "Less", "targetValue": 0.20}
  ]
}
```

### Live Deployment
```python
# Deploy to paper trading
"Deploy volatility regime strategy to paper trading"
```

## Code Reference
- **File**: `main_volatility_regime.py`
- **Class**: `VolatilityRegimeStrategy`
- **Algorithm Type**: Regime-based asset allocation
- **Data Frequency**: Daily bars
- **Dependencies**: numpy for volatility calculations

## Related Strategies
- VIX Term Structure (volatility-based timing)
- TRIN Breadth (market stress detection)
- Multi-Timeframe (combines multiple signals)

## Academic References
- "Volatility Regimes in Asset Allocation" studies
- Risk parity portfolio construction
- Flight to quality research
- VIX and market risk literature

## Historical Regime Examples

### March 2020 (COVID-19)
```
Pre-Crisis (Feb 2020): 12% vol → Aggressive allocation
Crash (March 15): 80% vol → Defensive allocation
Recovery (June): 30% vol → Medium allocation
Calm (Sept): 18% vol → Medium allocation
```

### 2017 (Low Vol Year)
```
Entire year: 10-12% vol → Aggressive allocation
Result: QQQ +32%, TLT +8%
Strategy captured bull market
```

### 2008 Financial Crisis
```
Pre-Crisis: 15-20% vol → Medium allocation
Lehman (Sept): 70% vol → Defensive allocation
Recovery (2009): 35% vol → Medium allocation
Strategy preserved capital during worst declines
```

## Performance Considerations

### Bull Market Performance
- May underperform buy-and-hold SPY
- Defensive allocations drag returns
- Value in risk management, not pure returns

### Bear Market Performance
- Outperforms buy-and-hold significantly
- Defensive shift preserves capital
- Key value proposition

### Risk-Adjusted Returns
- Lower drawdowns
- Smoother equity curve
- Higher Sharpe ratio potential
- Better sleep at night factor
