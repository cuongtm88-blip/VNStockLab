# VNStockLab Version 1 Data and Analysis Flow

## Purpose

This document defines the canonical flow from received market data to user-facing decision support. Each stage must preserve lineage and temporal correctness so that derived outputs can be explained, tested, and reproduced.

## Canonical flow

```text
raw data
-> validation and normalization
-> adjusted market data
-> indicators and market structure
-> patterns and support/resistance
-> versioned strategy evaluation
-> Technical Score
-> signal and trade plan
-> AI explanation
```

## Stage contracts

### 1. Raw data

Raw inputs enter through the `market_data` module and retain source and observation context required for audit and reprocessing. Raw values are not treated as analysis-ready merely because they were received successfully.

### 2. Validation and normalization

The `market_data` module checks required structure, types, instrument mapping, timestamps, and internally consistent market fields, then converts accepted data into canonical representations. Invalid or unresolved input must not silently pass into analysis.

### 3. Adjusted market data

Validated data is transformed into the adjusted representation used by downstream calculations. Adjustment policy and relevant version or processing context must be traceable. Consumers must be able to distinguish the effective instrument and time basis of the data they use.

### 4. Indicators and market structure

The `technical_analysis` module calculates deterministic indicators, Ichimoku, volume and money-flow measures, and market-structure evidence from approved adjusted data. Calculations must identify their parameters and implementation version where required for reproducibility.

### 5. Patterns and support/resistance

The `technical_analysis` module derives candlestick patterns, price patterns, support and resistance, Dow Theory evidence, and Elliott Wave scenarios. Outputs must distinguish detected evidence and scenarios from guaranteed outcomes.

### 6. Versioned strategy evaluation

The shared Strategy Engine in `strategies` evaluates a specific strategy version against the available point-in-time evidence. Scanner, backtesting, and alerts invoke this same implementation. Each evaluation records the strategy version, evaluation context, evidence references, and outcome.

### 7. Technical Score

The strategy evaluation produces or supplies evidence for the Technical Score using the frozen version 1 weights:

| Category | Points |
| --- | ---: |
| Trend | 25 |
| Momentum | 20 |
| Volume | 15 |
| Money Flow | 15 |
| Market Structure | 15 |
| Pattern Confirmation | 10 |

The score must expose category contributions and supporting evidence. Its maximum is 100. A high score alone is not a buy recommendation.

### 8. Signal and trade plan

The `signals` module derives deterministic signals and trade plans from versioned strategy outcomes and applicable risk rules. The result retains the originating evaluation, score details, time context, assumptions, and risk parameters. It remains decision support and cannot place an order.

### 9. AI explanation

The `ai_explanations` module receives selected deterministic data and outputs and expresses them in natural language. It must preserve uncertainty and limitations, cite the supplied evidence within the product context, and never invent or modify market data, indicators, patterns, scores, signals, or trade plans. It must not generate price forecasts.

## Consumer paths

- The scanner applies the shared Strategy Engine across an instrument universe and returns traceable evaluations.
- Backtesting replays the shared Strategy Engine using only data available at each simulated point in time.
- Alerts invoke or consume shared strategy evaluations and retain the strategy version and triggering context.
- Market dashboard, breadth, and sector rotation views may consume validated market data and deterministic analytics without bypassing ownership boundaries.
- Watchlists and portfolios select user-relevant contexts; they do not alter the analytical pipeline.

## Temporal and backtest integrity

Every historical evaluation must be limited to information available at the evaluation time. Later observations, later adjustments not valid for that simulation context, and future-derived features must not influence earlier decisions. Backtest execution ordering, costs, stops, position sizing, position limits, and capital reinvestment must be applied deterministically. These constraints prevent look-ahead bias and data leakage.

## Failure and traceability rules

- A failed validation or unresolved instrument prevents dependent analysis for that input; failure must not be replaced with fabricated values.
- Derived outputs must retain enough lineage to identify input data, effective time, parameters, calculation version, and strategy version as applicable.
- Reprocessing must not erase the ability to identify which versions produced persisted results.
- AI explanation failure must not alter or invalidate the underlying deterministic result.
- Delivery mechanisms may retry alerts, but retries must not create a different analytical outcome for the same recorded evaluation.

