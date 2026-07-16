# VNStockLab Version 1 Scope

## Purpose

VNStockLab version 1.0 is a web-based technical-analysis and investment decision-support platform for the Vietnamese stock market. This document defines the product capabilities that the version 1 implementation must deliver. It is a scope contract, not a statement that the platform places trades or guarantees investment outcomes.

## Product principles

- Analysis must be reproducible from validated market data and explicit, versioned rules.
- Derived indicators, patterns, scores, signals, and trade plans must remain traceable to their inputs and calculation versions.
- The same Strategy Engine implementation must power scanning, backtesting, and alerts.
- AI may explain deterministic platform outputs, but must never invent market data, indicators, patterns, scores, signals, or trade plans.
- A Technical Score is decision-support evidence. A high score alone is not a buy recommendation.
- Version 1 provides basic multi-user access, with user-owned tools and data kept appropriately associated with the authenticated user.

## In-scope capabilities

### Market overview and intelligence

- A market dashboard for presenting market-level technical and analytical information.
- Market breadth analysis.
- Sector rotation analysis.
- Analytical visualizations using the charting technologies defined by the architecture baseline.

### Stock analysis

- Stock-level analysis for supported Vietnamese market instruments.
- Candlestick charts and volume views.
- Volume and money-flow analysis.
- Technical indicators.
- Ichimoku analysis.
- Candlestick-pattern detection.
- Price-pattern detection.
- Support and resistance analysis.
- Dow Theory analysis.
- Elliott Wave scenarios. These are scenarios, not deterministic forecasts.

### Strategy, scoring, and decisions

- A versioned, traceable Strategy Engine.
- A stock scanner that evaluates instruments through the shared Strategy Engine.
- A traceable Technical Score.
- Deterministic signals and trade plans based on defined strategy versions and analysis inputs.

The version 1 Technical Score has a maximum of 100 points and uses these fixed category weights:

| Category | Weight |
| --- | ---: |
| Trend | 25 |
| Momentum | 20 |
| Volume | 15 |
| Money Flow | 15 |
| Market Structure | 15 |
| Pattern Confirmation | 10 |
| **Total** | **100** |

Each score must expose enough detail to identify its category contributions, underlying evidence, relevant market-data context, and calculation or strategy version. A high score alone is not a buy recommendation and must not be presented as one.

### Backtesting

Version 1 backtesting is limited to long-only strategies on daily data. It must support:

- Initial capital.
- Fees, taxes, and slippage.
- Stop loss, take profit, and trailing stop rules.
- Position sizing and position limits.
- Capital reinvestment.

Backtests must use the shared Strategy Engine and a recorded strategy version. Execution and data handling must prevent look-ahead bias and data leakage. Results must retain sufficient configuration and version information to be reproducible and reviewable.

### User tools

- Watchlists.
- Portfolios.
- Risk-management tools.
- A trading journal.
- Basic multi-user access.

### Alerts

- In-app alerts.
- Email alerts.
- Telegram alerts.

Alert conditions derived from strategies must use the shared, versioned Strategy Engine. Alert records must identify the strategy and relevant evaluation context that produced them.

### AI explanations

AI explanations may translate deterministic analysis into clear language and describe the evidence, limitations, and conditions behind a result. They must be grounded in platform-provided data and outputs. AI must never create or alter market data, indicator values, detected patterns, Technical Scores, signals, or trade plans, and must not present AI-generated price forecasts.

## Version 1 acceptance boundary

A capability is within the version 1 contract only when it is named in this document and complies with the frozen architecture and delivery controls. Items explicitly excluded by `OUT_OF_SCOPE_V1.md` are not required and must not enter implementation through interpretation of a broader capability. New ideas are recorded in `BACKLOG_V2.md`; they do not change version 1 scope.

