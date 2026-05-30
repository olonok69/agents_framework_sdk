# Bollinger Band Breakout Strategy

## What the Strategy Measures
- Price breakouts beyond upper Bollinger Band
- Volume confirmation to filter false breakouts
- ATR-based volatility for dynamic position sizing

## Strategy Logic

### Entry Conditions
- **Price Breakout**: Close > Upper Bollinger Band
- **Volume Confirmation**: Volume > 1.2x 20-day average
- **Position Sizing**: ATR-inverse (lower volatility = larger size)

### Exit Conditions
- **Lower Band Touch**: Price touches lower Bollinger Band
- **Middle Band Touch**: Price reverts to middle band (20 SMA)

### Indicator Configuration
- **Bollinger Bands**: 20-period, 2 standard deviations
- **ATR**: 14-period Average True Range
- **Volume SMA**: 20-period volume average

## Implementation Details

### Symbols
- **SPY**: S&P 500 ETF (primary trading vehicle)

### Technical Indicators
- **BB Upper**: SMA(20) + 2σ
- **BB Middle**: SMA(20)
- **BB Lower**: SMA(20) - 2σ
- **ATR(14)**: Volatility measure for position sizing
- **Volume SMA(20)**: Volume baseline

### Parameters
- `bb_period`: 20 (Bollinger Band period)
- `bb_std`: 2.0 (standard deviation multiplier)
- `atr_period`: 14 (ATR calculation period)
- `volume_multiplier`: 1.2 (volume confirmation threshold)
- `warmup_period`: 25 days

### Position Sizing Formula
```python
position_size = min(0.95, (2.0 / atr_value) * 0.1)
```
- **Low ATR** (low volatility) → Larger position
- **High ATR** (high volatility) → Smaller position
- **Max Position**: 95% of portfolio

## Strategy Characteristics

### Momentum-Following
- Rides breakouts expecting continuation
- Opposite of mean reversion
- Assumes trend will persist short-term

### Volume Confirmation
- Filters weak breakouts lacking conviction
- 20% above average volume required
- Reduces false signals significantly

### Volatility-Adjusted Sizing
- Adapts to current market conditions
- Reduces position during volatile periods
- Increases position during calm periods

## Strategy Strengths
1. **Trend Following**: Captures strong momentum moves
2. **Risk Management**: ATR-based sizing controls volatility exposure
3. **Volume Filter**: Reduces false breakouts
4. **Clear Exit**: Multiple exit conditions prevent large losses
5. **Adaptive**: Position size adjusts to market conditions

## Strategy Weaknesses
1. **Whipsaw Risk**: Breakouts can quickly reverse
2. **Late Entry**: Enters after move already started
3. **No Stop Loss**: Relies on band touches for exits
4. **Bull Market Bias**: Primarily long-only strategy
5. **Gap Risk**: Overnight gaps can bypass bands

## Bollinger Band Theory

### Band Squeeze
- Bands narrow during low volatility
- Often precedes large moves
- Strategy capitalizes on expansion phase

### Band Walk
- Strong trends can "walk the band"
- Price stays near upper/lower band
- Strategy rides these sustained moves

### Band Penetration
- Breakouts signal momentum
- Volume confirms genuine moves
- False breakouts lack volume support

## Optimization Opportunities
- **BB Period**: Test 10-30 range for band period
- **Std Dev**: Try 1.5-3.0 for band width
- **Volume Threshold**: Optimize 1.0-2.0 multiplier
- **ATR Sizing**: Adjust (2.0 / ATR) coefficient
- **Add Stop Loss**: Implement trailing stop below entry
- **Time Filter**: Exit if no follow-through within N days

## Usage with MCP Tools

### Compile & Test
```python
# Via AI assistant with MCP
"Compile the Bollinger breakout strategy"
"Run a backtest from 2020 to 2022"
```

### Optimization
```python
{
  "name": "Bollinger Breakout Optimization",
  "target": {"target": "SharpeRatio", "extremum": "max"},
  "parameters": [
    {"name": "bb_period", "min": 10, "max": 30, "step": 5},
    {"name": "bb_std", "min": 1.5, "max": 3.0, "step": 0.25},
    {"name": "volume_multiplier", "min": 1.0, "max": 2.0, "step": 0.2}
  ],
  "constraints": [
    {"target": "Drawdown", "operator": "Less", "targetValue": 0.15}
  ]
}
```

### Live Deployment
```python
# Deploy to paper trading
"Deploy Bollinger breakout to paper trading"
```

## Code Reference
- **File**: `main_bollinger_breakout.py`
- **Class**: `BollingerBreakoutStrategy`
- **Algorithm Type**: Momentum breakout with volatility sizing
- **Data Frequency**: Daily bars
- **Built-in Indicators**: BB, ATR, SMA

## Related Strategies
- Earnings Momentum (volume-based entry)
- Multi-Timeframe (combines multiple timeframes)
- Gap Fade (opposite approach - fades breakouts)

## References
- "Bollinger on Bollinger Bands" by John Bollinger
- Volatility-based position sizing studies
- Volume-price confirmation in technical analysis
- Average True Range (ATR) by J. Welles Wilder

## Example Trade Flow

### Successful Breakout Trade
```
Day 1:
- Price: $450 (above upper band $448)
- Volume: 120M (avg: 90M) ✓
- ATR: 5.0 → Position: 40%
- Action: BUY

Day 5:
- Price continues to $460
- Upper band adjusts higher

Day 10:
- Price touches middle band $452
- Action: SELL → +4.4% gain
```

### Failed Breakout (Volume Filter Saves)
```
Day 1:
- Price: $450 (above upper band $448)
- Volume: 80M (avg: 90M) ✗
- Action: NO TRADE (volume too low)

Day 2:
- Price reverses to $445
- Avoided false breakout
```
