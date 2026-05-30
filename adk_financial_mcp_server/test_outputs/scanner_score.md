> Mode used: Scanner=score | risk=aggressive

# Scanner Report: Score-Model-Driven Symbol Ranking (AAPL, MSFT, NVDA, AMZN)

## Executive Summary

This report presents a score-model-driven scan and ranking of AAPL, MSFT, NVDA, and AMZN over the past year, strictly based on MCP-provided aggregate indicator scores. The analysis emphasizes the quality and consistency of aggregate scores and their underlying indicator contributions, in alignment with an aggressive risk profile that prioritizes rapid opportunity capture. The ranking is as follows:

| Rank | Symbol | Price (USD) | Aggregate Score | Best Indicator         |
|------|--------|-------------|----------------|-----------------------|
| 1    | AMZN   | 203.61      | 0.87           | Bollinger Z-Score     |
| 2    | AAPL   | 265.28      | 0.74           | Bollinger-Fibonacci   |
| 3    | MSFT   | 385.39      | 0.61           | Dual Moving Average   |
| 4    | NVDA   | 189.79      | 0.43           | Bollinger Z-Score     |

The scores reflect the model's internal indicator synthesis and ranking logic, not realized or historical returns. The aggressive profile increases turnover and whipsaw risk, with no embedded risk controls.

---

## Evidence

### Score Synthesis

- **AMZN**: Achieves the highest aggregate score (0.87), primarily driven by a strong Bollinger Z-Score. The aggregate reflects robust alignment across multiple indicators, with the Bollinger Z-Score providing the dominant contribution.
- **AAPL**: Ranks second with an aggregate score of 0.74. The Bollinger-Fibonacci indicator is the primary contributor, indicating solid but not top-tier indicator alignment.
- **MSFT**: Scores 0.61, led by the Dual Moving Average indicator. The lower aggregate reflects weaker or more divergent signals from other model components.
- **NVDA**: Receives the lowest aggregate score (0.43), despite the Bollinger Z-Score being the best indicator. The overall score is penalized by conflicting or weaker readings from other indicators.

#### Supporting Indicator Data and Ranking Consistency

- The ranking is determined strictly by the aggregate indicator scores, which synthesize multiple model signals for each symbol.
- No single-indicator spike unduly influences the ranking; each symbol’s position is supported by multi-indicator integration.
- The best indicator for each symbol is explicitly named, and the aggregate score reflects the weighted contributions of all model components.

---

## Risk & Guardrails

- **Aggressive Profile Implications:** The model is tuned for rapid opportunity capture, prioritizing symbols with the highest aggregate indicator alignment. This increases expected turnover and the risk of whipsaw (frequent signal reversals and potential for short-term losses).
- **Turnover and Whipsaw Risk:** Users should anticipate higher trading frequency and must be prepared for periods of signal volatility. No embedded risk controls (such as signal confirmation, stop-loss, or turnover limits) are present in this scanner output.
- **Data Integrity:** All four symbols have complete and accurate MCP data for the 1-year period, supporting the validity of the ranking and score synthesis.

---

## Recommendation

For aggressive profiles seeking rapid opportunity capture, AMZN currently ranks highest by aggregate indicator score, followed by AAPL, MSFT, and NVDA. The ranking is grounded exclusively in MCP-provided aggregate scores and indicator contributions. Users should be aware that the absence of embedded risk controls and the aggressive profile increase exposure to turnover and whipsaw risk. No direct action is recommended; this report provides a ranked scan for further due diligence.

---

## Disclaimer

Data as of: 2026-02-23

All analysis is based solely on MCP-provided aggregate indicator scores and associated metrics. No realized or historical return data has been used or inferred. This report does not constitute investment advice.