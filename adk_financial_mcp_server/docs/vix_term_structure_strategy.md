# VIX Term Structure Strategy

## What the Strategy Measures
- Volatility term structure (contango vs. backwardation)
- Short-term vs. long-term implied volatility relationship
- Market fear/complacency regime changes

## Strategy Logic

### Term Structure Calculation
```python
term_ratio = back_month_volatility / front_month_volatility
```

### Volatility Proxy (Synthetic VIX)
Since direct VIX futures access may be limited:
- **Front Month**: 10-day rolling volatility of SPY
- **Back Month**: 30-day rolling volatility of SPY
- **Annualized**: Multiply by √252 × 100

### Entry Conditions

#### Long Position (Backwardation)
- **Term Ratio < 0.95**: Back month < Front month
- **Interpretation**: Fear spike, volatility elevated short-term
- **Action**: Long SPY at 80%
- **Rationale**: Markets tend to mean-revert after panic

#### Short Position (Steep Contango)
- **Term Ratio > 1.05**: Back month > Front month significantly
- **Interpretation**: Calm markets, low current volatility
- **Action**: Short SPY at 50%
- **Rationale**: Complacency can reverse quickly

### Exit Conditions
- **Exit Long**: Term ratio normalizes above 1.0
- **Exit Short**: Term ratio flattens below 1.0

## Implementation Details

### Symbols
- **SPY**: S&P 500 ETF (for volatility calculation and trading)

### Volatility Calculation
```python
returns = price.pct_change()
volatility = returns.std() * sqrt(252) * 100
```

### Parameters
- `vix_window`: 10 (front month proxy days)
- `vix_long_window`: 30 (back month proxy days)
- `contango_threshold`: 1.05 (steep contango)
- `backwardation_threshold`: 0.95 (backwardation)
- `long_position_size`: 0.8 (80%)
- `short_position_size`: -0.5 (50%)
- `warmup_period`: 35 days

## VIX Term Structure Concepts

### Normal Contango (Ratio > 1.0)
- **Meaning**: Future volatility expected higher than current
- **Market State**: Calm, complacent
- **Historical Norm**: VIX futures typically in contango
- **Trading Opportunity**: Fade extremes (short overconfidence)

### Backwardation (Ratio < 1.0)
- **Meaning**: Current volatility higher than future expectations
- **Market State**: Fearful, stressed
- **Occurs During**: Market selloffs, crashes
- **Trading Opportunity**: Buy the fear (contrarian long)

### Contango Flattening
- **Signal**: Term ratio approaching 1.0 from above
- **Interpretation**: Fear building
- **Action**: Reduce or exit shorts

### Backwardation Normalizing
- **Signal**: Term ratio approaching 1.0 from below
- **Interpretation**: Fear subsiding
- **Action**: Exit longs

## Strategy Characteristics

### Volatility Regime Trading
- Profits from shifts in market fear levels
- Not directional - based on volatility structure
- Contrarian at extremes

### Mean Reversion Component
- Assumes term structure reverts to normal contango
- Capitalizes on overreactions (fear/complacency)

## Strategy Strengths
1. **Regime Detection**: Identifies major market sentiment shifts
2. **Contrarian Edge**: Buys fear, sells complacency
3. **Diversifying**: Low correlation to trend-following
4. **Event Capture**: Positions for volatility spikes
5. **Clear Signals**: Quantitative thresholds

## Strategy Weaknesses
1. **Synthetic VIX**: Uses rolling volatility proxy, not actual VIX futures
2. **Directional Risk**: Long/short SPY, not pure volatility play
3. **Timing Risk**: Regimes can persist longer than expected
4. **No Stop Loss**: Relies on regime normalization
5. **Complex Interpretation**: Term structure signals can be noisy

## Real VIX vs. Synthetic Implementation

### Real VIX Term Structure
```
- VIX Index: Current 30-day implied volatility
- VIX Front Month: Nearest futures contract
- VIX Back Month: Second nearest futures contract
- Term Structure: Back/Front futures ratio
```

### This Implementation (Synthetic)
```
- Front Month: 10-day realized volatility
- Back Month: 30-day realized volatility
- Proxy: Approximates VIX structure behavior
```

**Note**: Real VIX futures data would improve strategy accuracy.

## Optimization Opportunities
- **Window Sizes**: Test 5-15 (front) and 20-40 (back)
- **Thresholds**: Optimize 0.90-0.98 (backwardation) and 1.03-1.10 (contango)
- **Position Sizing**: Scale by extremity of ratio
- **Add Filters**: Combine with trend or momentum filters
- **Real VIX Data**: Use actual VIX futures if available
- **Multiple Exits**: Partial exits as structure normalizes

## Usage with MCP Tools

### Compile & Test
```python
# Via AI assistant with MCP
"Compile the VIX term structure strategy"
"Run a backtest from 2020 to 2022"
```

### Optimization
```python
{
  "name": "VIX Term Structure Optimization",
  "target": {"target": "SharpeRatio", "extremum": "max"},
  "parameters": [
    {"name": "vix_window", "min": 5, "max": 15, "step": 2},
    {"name": "vix_long_window", "min": 20, "max": 40, "step": 5},
    {"name": "contango_threshold", "min": 1.03, "max": 1.10, "step": 0.01},
    {"name": "backwardation_threshold", "min": 0.90, "max": 0.98, "step": 0.01}
  ]
}
```

### Live Deployment
```python
# Deploy to paper trading
"Deploy VIX term structure strategy to paper trading"
```

## Code Reference
- **File**: `main_vix_term_structure.py`
- **Class**: `VixTermStructureStrategy`
- **Algorithm Type**: Volatility regime / Term structure
- **Data Frequency**: Daily bars
- **Custom Calculation**: Rolling volatility proxy

## Related Strategies
- Volatility Regime Switch (related volatility-based)
- TRIN Breadth (contrarian market timing)
- Pairs Trading (mean reversion concept)

## References
- VIX futures term structure research
- "The VIX Index and Volatility-Based Global Indexes" by CBOE
- Volatility risk premium literature
- Contango and backwardation in derivatives markets

## Historical Context

### 2008 Financial Crisis
- VIX spiked to 80+
- Severe backwardation (front > back)
- Perfect buying opportunity post-panic

### COVID-19 Crash (March 2020)
- VIX hit 85
- Backwardation signal
- Strong recovery followed

### Calm Bull Markets
- VIX typically 10-15
- Steep contango structure
- Vulnerable to sudden spikes
