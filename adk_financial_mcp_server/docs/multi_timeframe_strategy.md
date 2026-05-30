# Multi-Timeframe Momentum Strategy

## What the Strategy Measures
- Daily trend direction using SMA crossover
- Hourly RSI for precise entry timing
- Combines swing trading (daily) with intraday signals (hourly)

## Strategy Logic

### Trend Filter (Daily Timeframe)
```python
uptrend = SMA(50, daily) > SMA(200, daily)
```
- **Golden Cross**: 50 > 200 → Bullish trend confirmed
- **Death Cross**: 50 < 200 → Bearish trend (no trades)

### Entry Timing (Hourly Timeframe)
```python
entry = uptrend AND RSI(14, hourly) < 30
```
- **RSI < 30**: Oversold condition in hourly timeframe
- **Within Uptrend**: Daily trend must be bullish
- **Position**: 95% allocation to SPY

### Exit Conditions
1. **RSI Overbought**: RSI > 70 (profit taking)
2. **Trend Reversal**: 50 SMA crosses below 200 SMA
3. **Liquidate**: Close position on either condition

## Implementation Details

### Symbols
- **SPY**: S&P 500 ETF (dual timeframe monitoring)

### Technical Indicators
- **SMA(50, Daily)**: Short-term trend
- **SMA(200, Daily)**: Long-term trend
- **RSI(14, Hourly)**: Momentum oscillator for timing

### Parameters
- `sma_short`: 50 (daily)
- `sma_long`: 200 (daily)
- `rsi_period`: 14 (hourly)
- `rsi_oversold`: 30 (entry threshold)
- `rsi_overbought`: 70 (exit threshold)
- `position_size`: 0.95
- `warmup_period`: 210 days

## Strategy Characteristics

### Timeframe Hierarchy
1. **Daily (Higher)**: Determines market regime
2. **Hourly (Lower)**: Provides entry/exit precision
3. **Alignment**: Only trade when both agree

### Trend + Mean Reversion Hybrid
- **Trend Following**: Daily SMAs filter for bull markets
- **Mean Reversion**: Hourly RSI oversold entries
- **Best of Both**: Trend direction + tactical timing

### Risk Reduction
- Avoids counter-trend trades (bear markets)
- Precise entries reduce drawdown
- Quick exits on momentum loss

## Strategy Strengths
1. **Trend Confirmation**: Won't buy falling markets
2. **Precise Timing**: Hourly RSI improves entry prices
3. **Dual Protection**: Exits on momentum OR trend change
4. **Reduced Whipsaws**: Daily filter prevents choppy trades
5. **Scalable Logic**: Can add more timeframes or assets

## Strategy Weaknesses
1. **Late Entry**: Waits for 200-day MA, misses early trends
2. **Long-Only**: No profit in bear markets
3. **Hourly Data Required**: More computational overhead
4. **Golden Cross Lag**: Slow trend identification
5. **RSI False Signals**: Can stay oversold in strong downtrends

## Multi-Timeframe Analysis Theory

### Top-Down Approach
```
Monthly → Weekly → Daily → Hourly → Entry
  (Long-term)              (Timing)
```

### Confluence Trading
- Multiple timeframes agreeing increases probability
- This strategy: Daily (trend) + Hourly (oversold)
- Additional layers could add weekly/monthly

### Timeframe Synchronization
- **Daily confirms direction**
- **Hourly confirms timing**
- Entry only when both aligned

## SMA Crossover Signals

### Golden Cross (50 > 200)
- Historically bullish signal
- Market entering uptrend
- Strategy becomes active

### Death Cross (50 < 200)
- Historically bearish signal
- Market entering downtrend
- Strategy goes flat (exits positions)

### Whipsaw Protection
- 200-day MA slow to react
- Filters out short-term noise
- Keeps strategy in major trends

## RSI Tactical Timing

### Oversold in Uptrend (RSI < 30)
- Temporary pullback in bull market
- High probability bounce point
- Optimal entry price

### Overbought Exit (RSI > 70)
- Short-term momentum exhaustion
- Take profits before reversal
- Preserves gains

## Optimization Opportunities
- **SMA Periods**: Test 20/50, 50/100, 100/200 combinations
- **RSI Thresholds**: Optimize 20-40 (entry) and 60-80 (exit)
- **Add Third Timeframe**: Weekly for macro trend
- **Alternative Indicators**: MACD, Stochastic for timing
- **Position Scaling**: Increase size at deeper RSI oversold
- **Trailing Stop**: Add trailing stop on profitable positions

## Usage with MCP Tools

### Compile & Test
```python
# Via AI assistant with MCP
"Compile the multi-timeframe momentum strategy"
"Run a backtest from 2020 to 2022"
```

### Optimization
```python
{
  "name": "Multi-Timeframe Optimization",
  "target": {"target": "SharpeRatio", "extremum": "max"},
  "parameters": [
    {"name": "sma_short", "min": 20, "max": 100, "step": 10},
    {"name": "sma_long", "min": 100, "max": 250, "step": 25},
    {"name": "rsi_oversold", "min": 20, "max": 40, "step": 5},
    {"name": "rsi_overbought", "min": 60, "max": 80, "step": 5}
  ],
  "constraints": [
    {"target": "Drawdown", "operator": "Less", "targetValue": 0.15}
  ]
}
```

### Live Deployment
```python
# Deploy to paper trading
"Deploy multi-timeframe strategy to paper trading"
```

## Code Reference
- **File**: `main_multi_timeframe.py`
- **Class**: `MultiTimeframeStrategy`
- **Algorithm Type**: Trend following + Mean reversion timing
- **Data Frequency**: Hourly bars (with daily indicators)
- **Built-in Indicators**: SMA, RSI

## Related Strategies
- Earnings Momentum (single timeframe momentum)
- Bollinger Breakout (momentum with bands)
- TRIN Breadth (contrarian timing)

## References
- "Japanese Candlestick Charting Techniques" by Steve Nison (timeframes)
- "Trading for a Living" by Dr. Alexander Elder (triple screen system)
- RSI indicator by J. Welles Wilder
- SMA crossover systems in technical analysis

## Example Trade Sequence

### Successful Trade
```
Week 1 (Daily):
- SMA(50) = 420, SMA(200) = 410
- Golden Cross confirmed ✓

Day 5, 2 PM (Hourly):
- RSI = 28 (oversold) ✓
- Action: BUY at $425

Day 8, 11 AM (Hourly):
- RSI = 72 (overbought)
- Action: SELL at $437
- Profit: +2.8%
```

### Avoided Trade (Filter Working)
```
Week 1 (Daily):
- SMA(50) = 390, SMA(200) = 410
- Death Cross active ✗

Day 5, 2 PM (Hourly):
- RSI = 25 (oversold)
- Action: NO TRADE
- Trend filter prevents counter-trend trade

Day 10:
- Price drops to $370
- Filter saved -5% loss
```

## Performance Considerations

### Best Market Conditions
- Strong bull markets with pullbacks
- Trending markets with consolidations
- Post-correction recoveries

### Worst Market Conditions
- Choppy, range-bound markets
- Bear markets (strategy inactive)
- Whipsaw around 200-day MA
