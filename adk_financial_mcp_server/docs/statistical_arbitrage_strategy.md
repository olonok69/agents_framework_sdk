# Statistical Arbitrage Strategy

## What the Strategy Measures
- Price divergence within correlated tech stock basket
- Z-score deviation from basket mean
- Market-neutral arbitrage opportunities

## Strategy Logic

### Basket Construction
- **Stocks**: AAPL, MSFT, GOOGL (large-cap tech)
- **Correlation**: Typically high (0.70+)
- **Window**: 20-day rolling statistics

### Z-Score Calculation
```python
z_score = (current_price - mean_price) / std_price
basket_mean = mean(z_scores[AAPL, MSFT, GOOGL])
deviation = individual_z_score - basket_mean
```

### Entry Conditions

#### Long Individual Stock
- **Trigger**: Deviation < -1.5 (significantly below basket)
- **Logic**: Stock underperformed, expected to catch up
- **Position**: +30% allocation

#### Short Individual Stock
- **Trigger**: Deviation > +1.5 (significantly above basket)
- **Logic**: Stock overperformed, expected to revert
- **Position**: -30% allocation

### Exit Conditions
- **Convergence**: |Deviation| < 0.3
- **Logic**: Stock rejoins basket, arbitrage closed
- **Action**: Liquidate position

### Market-Neutral Design
- Can be long some stocks, short others simultaneously
- Net exposure near zero (hedged)
- Profits from relative performance, not direction

## Implementation Details

### Symbols
- **AAPL**: Apple Inc.
- **MSFT**: Microsoft Corporation
- **GOOGL**: Alphabet Inc. Class A

### Statistical Indicators
- **Rolling Mean(20)**: Average price over window
- **Rolling Std Dev(20)**: Price volatility
- **Z-Score**: Standardized price deviation
- **Basket Mean**: Average z-score across trio

### Parameters
- `window`: 20 (rolling statistics period)
- `entry_threshold`: 1.5 (deviation for entry)
- `exit_threshold`: 0.3 (deviation for exit)
- `position_size`: 0.3 (30% per position)
- `warmup_period`: 25 days

## Strategy Characteristics

### Statistical Arbitrage Principles
1. **Mean Reversion**: Prices tend toward basket average
2. **Correlation**: Stocks move together long-term
3. **Divergence-Convergence**: Temporary mispricings correct
4. **Market-Neutral**: Hedged against broad moves

### Risk Profile
- **Low Directional Risk**: Long/short balance
- **High Specific Risk**: Individual stock news
- **Correlation Risk**: If stocks decouple permanently
- **Execution Risk**: Slippage on multiple legs

## Strategy Strengths
1. **Market-Neutral**: Profits in any market direction
2. **Statistical Basis**: Quantitative, objective signals
3. **Diversified**: Multiple positions across stocks
4. **Low Beta**: Minimal correlation to market
5. **High Win Rate**: Mean reversion is robust

## Strategy Weaknesses
1. **Correlation Decay**: Stocks can diverge permanently
2. **News Risk**: Earnings/events cause non-reversion
3. **Multiple Positions**: Complex tracking required
4. **Margin Intensive**: Short positions require borrowing
5. **No Stop Loss**: Relies on convergence, no downside protection

## Statistical Arbitrage Theory

### Why It Works
- **Information Flow**: News affects stocks differently initially
- **Sector Effects**: Tech stocks respond similarly to macro
- **Overreaction**: Markets overshoot, then correct
- **Co-integration**: Long-term relationship pulls prices together

### When It Fails
- **Fundamental Shift**: One company's business model changes
- **Merger/Acquisition**: Corporate actions break correlation
- **Sector Rotation**: Value vs. growth divergence
- **Liquidity Crisis**: Flight to quality disrupts patterns

## Z-Score Interpretation

### Individual Z-Score
- **Z = +2**: Price is 2 std dev above its mean (expensive)
- **Z = -2**: Price is 2 std dev below its mean (cheap)
- **Z = 0**: Price at its average

### Deviation from Basket
- **Dev = +1.5**: Stock is 1.5 units above basket average
- **Dev = -1.5**: Stock is 1.5 units below basket average
- **Trading signal when deviation is extreme**

## Position Management

### Long Example
```
AAPL Z-Score: -0.5
MSFT Z-Score: +0.2
GOOGL Z-Score: +0.1
Basket Mean: -0.07

AAPL Deviation: -0.5 - (-0.07) = -0.43 (no trade)
MSFT Deviation: +0.2 - (-0.07) = +0.27 (no trade)

Later:
AAPL Z-Score: -2.0
Basket Mean: -0.5
AAPL Deviation: -2.0 - (-0.5) = -1.5 → LONG AAPL
```

### Simultaneous Positions
```
Day 5:
- Long AAPL (+30%): Z-score catching up
- Short MSFT (-30%): Z-score reverting
- Flat GOOGL (0%): No extreme deviation
Net Exposure: 0% (market-neutral)
```

## Optimization Opportunities
- **Window Size**: Test 10-40 days for statistics
- **Entry Threshold**: Optimize 1.0-2.5 range
- **Exit Threshold**: Test 0.1-0.5 range
- **Basket Size**: Add more stocks (5-10 total)
- **Sector Rotation**: Rotate basket based on correlation
- **Correlation Filter**: Only trade when correlation > 0.70
- **Position Scaling**: Size by extremity of deviation

## Usage with MCP Tools

### Compile & Test
```python
# Via AI assistant with MCP
"Compile the statistical arbitrage strategy"
"Run a backtest from 2020 to 2022"
```

### Optimization
```python
{
  "name": "Statistical Arbitrage Optimization",
  "target": {"target": "SharpeRatio", "extremum": "max"},
  "parameters": [
    {"name": "entry_threshold", "min": 1.0, "max": 2.5, "step": 0.25},
    {"name": "exit_threshold", "min": 0.1, "max": 0.5, "step": 0.1},
    {"name": "window", "min": 10, "max": 40, "step": 5}
  ],
  "constraints": [
    {"target": "Drawdown", "operator": "Less", "targetValue": 0.12}
  ]
}
```

### Live Deployment
```python
# Deploy to paper trading with margin account
"Deploy statistical arbitrage to paper trading with proper margin"
```

## Code Reference
- **File**: `main_statistical_arbitrage.py`
- **Class**: `StatisticalArbitrageStrategy`
- **Algorithm Type**: Market-neutral stat arb
- **Data Frequency**: Daily bars
- **Dependencies**: numpy for z-score calculations

## Related Strategies
- Pairs Trading (2-asset version of stat arb)
- Volatility Regime Switch (regime-based allocation)
- TRIN Breadth (market-neutral timing)

## Academic References
- "Statistical Arbitrage in the U.S. Equities Market" by Avellaneda & Lee
- Pairs trading and mean reversion studies
- Market-neutral hedge fund strategies
- Co-integration analysis in finance

## Real-World Applications

### Hedge Fund Usage
- Renaissance Technologies (quant pioneer)
- D.E. Shaw (statistical models)
- Two Sigma (machine learning arb)

### Institutional Scale
- High-frequency versions (millisecond holding)
- Hundreds of stocks in baskets
- Dynamic correlation monitoring
- Automated execution systems

## Risk Management Best Practices
1. **Monitor Correlation**: Alert if falls below 0.60
2. **Maximum Positions**: Limit to 3 simultaneous
3. **Time Stop**: Exit if no convergence in 20 days
4. **Volatility Filter**: Reduce size in high vol regimes
5. **News Monitoring**: Manual override for major events
