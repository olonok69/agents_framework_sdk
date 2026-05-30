# Gap Fade Strategy

## What the Strategy Measures
- Overnight gaps in SPY > 2%
- Mean reversion opportunity after extreme gaps
- Gap extreme price as stop-loss reference

## Strategy Logic

### Gap Detection (Market Open)
```python
gap_size = (open_price - previous_close) / previous_close
```

### Entry Conditions (9:30 AM)

#### Gap Up > 2%
- **Signal**: Opening price > yesterday close + 2%
- **Action**: SHORT SPY at 80%
- **Rationale**: Gaps often partially fill (fade up)

#### Gap Down > 2%
- **Signal**: Opening price < yesterday close - 2%
- **Action**: LONG SPY at 80%
- **Rationale**: Gaps often partially fill (fade down)

### Exit Conditions

#### Stop Loss (Gap Extreme)
- **Long Stop**: Price falls below gap open (breakdown)
- **Short Stop**: Price rises above gap open (breakout)
- **Rationale**: Gap extending = trend, not fade

#### Time Exit (2 Hours)
- **Duration**: Hold maximum 120 minutes
- **Logic**: Gaps fill quickly or not at all
- **Action**: Liquidate at market close if still open

## Implementation Details

### Symbols
- **SPY**: S&P 500 ETF (minute-level data)

### Data Requirements
- **Minute Bars**: Required for intraday tracking
- **Previous Close**: End of day (4:00 PM) price
- **Market Open**: 9:30 AM Eastern

### Parameters
- `gap_threshold`: 0.02 (2% minimum gap)
- `position_size`: 0.8 (80% allocation)
- `hold_minutes`: 120 (2 hours maximum)
- `warmup_period`: 2 days

## Strategy Characteristics

### Mean Reversion Bias
- Assumes extreme gaps overreact
- Market tends to partially correct
- High probability for small profits

### Intraday Timeframe
- Enters at market open
- Exits within hours
- No overnight holding risk

### Defined Risk
- Stop loss at gap extreme
- Maximum loss = gap size
- Known risk before entry

## Gap Theory

### Why Gaps Occur
- **News**: Earnings, economic data, geopolitical
- **After-Hours Trading**: Moves during closed market
- **Emotional Reactions**: Fear/greed at extremes
- **Algorithm Orders**: Overnight order imbalances

### Gap Types

#### Exhaustion Gap (Fade These)
- Occurs at end of strong move
- Represents climax buying/selling
- High probability of reversal
- **This strategy targets these**

#### Breakaway Gap (Don't Fade)
- Occurs at start of new trend
- Strong follow-through likely
- Stop loss protects against these

#### Common Gap (Neutral)
- Occurs in range-bound markets
- Often fills completely
- Low-volatility environment

### Gap Statistics
- **50-70%** of gaps partially fill within 1-3 days
- **Larger gaps** more likely to continue initially
- **2% threshold** balances frequency vs. extremity

## Strategy Strengths
1. **High Win Rate**: Gaps often revert partially
2. **Defined Risk**: Stop loss at gap extreme
3. **Quick Turnaround**: Hours, not days
4. **No Overnight Risk**: Closed before market close
5. **Clear Entry Signal**: Objective gap measurement

## Strategy Weaknesses
1. **Stop Loss Hit**: Gaps can extend (news-driven)
2. **Limited Opportunities**: 2%+ gaps are rare
3. **Minute Data Required**: More complex execution
4. **Slippage Risk**: Market open can be volatile
5. **No Profit Target**: Time-based exit may leave money on table

## Risk Factors

### When Gaps Extend (Strategy Loses)
- **Strong Trend**: Gap in direction of major trend
- **Fundamental News**: Earnings beat/miss, guidance change
- **Market Crash**: Gap down during panic continues
- **Short Squeeze**: Gap up on covering continues

### Ideal Conditions (Strategy Wins)
- **Exhaustion Move**: Gap after extended run
- **Overreaction**: News less significant than gap implies
- **Mean Reversion Setup**: Price extended from moving averages
- **Low Volume Gap**: Less conviction in move

## Optimization Opportunities
- **Gap Threshold**: Test 1.5%-3.0% range
- **Hold Duration**: Optimize 60-240 minutes
- **Profit Target**: Add fixed % target (e.g., 0.5% profit = exit)
- **Volume Filter**: Require volume confirmation
- **Trend Filter**: Only fade against major trend
- **Time of Day**: Exit earlier if gap filling quickly
- **Partial Exits**: Scale out as gap fills

## Usage with MCP Tools

### Compile & Test
```python
# Via AI assistant with MCP
"Compile the gap fade strategy"
"Run a backtest from 2020 to 2022"
```

### Optimization
```python
{
  "name": "Gap Fade Optimization",
  "target": {"target": "SharpeRatio", "extremum": "max"},
  "parameters": [
    {"name": "gap_threshold", "min": 0.015, "max": 0.030, "step": 0.005},
    {"name": "hold_minutes", "min": 60, "max": 240, "step": 30},
    {"name": "position_size", "min": 0.5, "max": 1.0, "step": 0.1}
  ],
  "constraints": [
    {"target": "Drawdown", "operator": "Less", "targetValue": 0.10}
  ]
}
```

### Live Deployment
```python
# Deploy to paper trading with minute data
"Deploy gap fade strategy to paper trading with minute resolution"
```

## Code Reference
- **File**: `main_gap_fade.py`
- **Class**: `GapFadeStrategy`
- **Algorithm Type**: Intraday mean reversion
- **Data Frequency**: Minute bars
- **Special Requirements**: Previous day close tracking

## Related Strategies
- Pairs Trading (mean reversion concept)
- Bollinger Breakout (opposite - follows gaps)
- TRIN Breadth (contrarian entries)

## References
- Gap trading studies in technical analysis
- Overnight returns and mean reversion research
- "Encyclopedia of Chart Patterns" by Thomas Bulkowski
- Academic studies on gap fill probabilities

## Example Trades

### Successful Gap Fade (Gap Up)
```
Previous Close: $450
Market Open (9:30 AM): $460 (+2.2% gap up)
Action: SHORT at $460

10:00 AM: Price $458 (gap partially filling)
10:45 AM: Price $455 (further reversion)
11:30 AM: Exit at $455 (120 min elapsed)
Profit: $460 - $455 = +$5 (+1.1%)
```

### Stop Loss Hit (Gap Extends)
```
Previous Close: $450
Market Open (9:30 AM): $460 (+2.2% gap up)
Action: SHORT at $460

9:45 AM: Strong buying, price $462
10:00 AM: Stop hit at $460 (gap extreme)
Action: Cover short
Loss: $460 - $462 = -$2 (-0.4%)
```

### Successful Gap Fade (Gap Down)
```
Previous Close: $450
Market Open (9:30 AM): $440 (-2.2% gap down)
Action: LONG at $440

9:45 AM: Price $442 (panic subsiding)
10:30 AM: Price $445 (gap filling)
11:30 AM: Exit at $445 (120 min elapsed)
Profit: $445 - $440 = +$5 (+1.1%)
```

## Performance Considerations

### Best Market Conditions
- Range-bound markets
- Low-conviction gaps
- Post-trend exhaustion
- Overnight overreactions

### Worst Market Conditions
- Strong trending markets
- News-driven gaps (earnings)
- Market crashes (gap down extends)
- Short squeezes (gap up extends)

## Advanced Variations
- **Partial Gap Fill**: Exit at 50% gap retracement
- **Gap and Go**: Reverse strategy - follow breakaway gaps
- **Volume-Weighted**: Scale size by volume at open
- **Multiple Exits**: Partial profit taking + trailing stop
