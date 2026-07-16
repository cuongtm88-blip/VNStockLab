# VNStockLab Domain Model V1

**Status:** Frozen  
**Version:** 1.0  
**Date:** 2026-07-16

## Purpose

This specification defines the frozen version 1 domain language, ownership boundaries, aggregates, lineage obligations, and immutability rules for VNStockLab. It is an implementation-neutral contract for a web-based technical-analysis and investment decision-support platform for supported Vietnamese market instruments. It does not define database tables, APIs, user-interface behavior, or deployment details.

## Domain boundaries

VNStockLab version 1 covers deterministic ingestion and analysis of market data, versioned strategy evaluation, scanning, long-only daily-data backtesting, signals and trade plans, user decision-support tools, alerts, grounded AI explanations, and audit. It does not place broker orders, trade real money, provide high-frequency trading, generate AI price forecasts, operate a social network, or provide commercial multi-tenant billing.

The domain is divided into the following areas:

1. **Identity** — users, roles, authentication-session records, ownership context, and audit records.
2. **Instruments** — canonical exchanges, sectors, industries, instruments, historical and alternate instrument aliases, indices, and index membership.
3. **Market Data** — provider intake, immutable raw records, validation, normalized bars, adjusted bars, calendars, corporate actions, and data-quality findings.
4. **Technical Analysis** — deterministic indicators, patterns, support and resistance, market structure, and Elliott Wave scenarios.
5. **Strategies** — strategy definitions, immutable versions, parameters, rules, risk rules, and the shared Strategy Engine.
6. **Scanner** — definitions and executions that apply the shared Strategy Engine to an instrument universe.
7. **Signals and Trade Plans** — published deterministic decisions, evidence, Technical Score details, and risk-aware trade plans.
8. **Backtesting** — reproducible, long-only daily simulations and their immutable results.
9. **Watchlists** — user-owned collections of instruments.
10. **Portfolios** — user-owned transaction histories, derived positions, and point-in-time valuations.
11. **Risk Management** — user risk constraints, position-size recommendations, and portfolio risk snapshots.
12. **Market Intelligence** — breadth, relative-strength, sector-rotation, and market-regime snapshots.
13. **Alerts** — user-owned rules, deterministic evaluations, and in-app, email, or Telegram deliveries.
14. **Trading Journal** — user-owned entries, attachments, and reviews.
15. **AI Explanations** — requests and natural-language results grounded only in stored deterministic evidence.
16. **Audit** — append-only records of important security and domain changes.

Each domain area owns its terminology and invariants. Cross-boundary references use stable identities and explicit contracts. No area may silently duplicate another area's canonical data or rules.

## Aggregate overview

| Aggregate root | Principal contents | Boundary responsibility |
| --- | --- | --- |
| User | Roles, refresh tokens | Authentication identity and ownership context. AuditLog is append-only and references actors rather than being mutable user content. |
| Exchange / Instrument / Index | Sector, Industry, InstrumentAlias, IndexConstituent | Canonical shared security and market reference data, including time-bounded alternate identities that always resolve to one canonical Instrument. |
| ImportBatch | RawMarketRecord, DataQualityIssue | Traceable provider ingestion and immutable received payloads. |
| Instrument market series | PriceBar, AdjustedPriceBar, CorporateAction | Distinct normalized and adjusted time series with adjustment evidence. |
| IndicatorDefinition | IndicatorResult | Versioned calculation meaning and reproducible results. |
| PatternDefinition | PatternDetection | Versioned pattern meaning and evidence-preserving detections. |
| Strategy | StrategyVersion, StrategyParameter, StrategyRule, StrategyRiskRule | Immutable executable strategy configuration. |
| ScanDefinition | ScanRun, ScanResult | Reproducible universe evaluation through the shared Strategy Engine. |
| Signal | SignalEvidence, TradePlan | Published strategy outcome, exact evidence, score detail, and decision-support plan. |
| BacktestDefinition | BacktestRun, BacktestTrade, BacktestEquityPoint, BacktestMetric | Frozen simulation configuration, execution history, diagnostics, and results. |
| Watchlist | WatchlistItem | User-owned instrument collection. |
| Portfolio | PortfolioTransaction, PortfolioPosition, PortfolioValuation | User-owned financial history and its derived state. |
| RiskProfile | PositionSizeRecommendation, PortfolioRiskSnapshot | User risk constraints and point-in-time derived recommendations. |
| Market intelligence snapshot | Breadth, relative strength, sector rotation, regime | Shared, point-in-time derived market context. |
| AlertRule | AlertEvaluation, NotificationDelivery | User-owned condition, deterministic evaluation, and delivery history. |
| JournalEntry | JournalAttachment, JournalReview | User-owned decision and review history. |
| ExplanationRequest | ExplanationResult | Grounded explanation input contract and output, separate from analytical truth. |

Aggregate boundaries express consistency and ownership, not required physical storage layout.

## Ownership rules

- Instruments, instrument aliases, reference classifications, provider metadata, market data, analytical definitions, published shared analytical outputs, and market-intelligence snapshots are shared platform data.
- Watchlists, portfolios, risk profiles, alert rules, journal records, explanation requests, and their children are owned by exactly one user.
- User-owned records must be isolated by user at every read, write, execution, and delivery boundary. A reference to shared data does not transfer ownership.
- Strategy visibility may be shared or user-owned, but every strategy has an explicit owner scope. Its versions remain immutable regardless of scope.
- Audit records retain the actor and affected owner context. They are not editable user content.
- Refresh tokens belong to one user and are security records; stored token material must be non-reversible rather than a plaintext credential.

## Shared Strategy Engine

The Strategy Engine is a single shared domain capability used by scanner, backtesting, and alerts. Each consumer supplies a point-in-time evaluation context and invokes the same evaluation implementation. Consumers may orchestrate execution differently, but they must not copy, reinterpret, or replace strategy logic. Every result identifies the exact immutable StrategyVersion and configuration hash used.

## Shared technical-analysis capability

Technical Analysis supplies the versioned canonical indicator and analytical implementations and definitions used by scanner, backtesting, signals, alerts, dashboards, and AI evidence. No consumer may implement an independent version of the same calculation or silently substitute a different formula, warm-up policy, rounding policy, or parameter default.

Results may be persisted, cached, materialized, or calculated on demand; the domain does not require every indicator to be physically calculated only once. Given identical input bars, input representation, definition version, parameter snapshot, implementation version, and configuration hash, results must be reproducible and equivalent under the calculation's declared numeric tolerance. Published `IndicatorResult` records remain immutable analytical evidence. Backtesting uses the same calculation semantics as live scanning while restricting every calculation to point-in-time inputs and preventing look-ahead bias.

## Traceability requirements

Every material derived output must retain, directly or through immutable references:

- the instrument or evaluated universe;
- timeframe and exact market-data timestamp or snapshot time;
- input representation, range, provider lineage, and import batch where applicable;
- calculation definition, implementation version, parameters, and configuration hash;
- exact StrategyVersion, strategy parameters, rules, and risk rules;
- evaluation or generation timestamp and execution context;
- deterministic evidence references, including Technical Score category contributions;
- user ownership context when the record is user-owned; and
- failure or diagnostic information when processing is unsuccessful.

A Signal must preserve the exact strategy version, parameters, evidence, and market-data timestamp used. Reprocessing or re-evaluation creates new historical output; it does not rewrite the original lineage.

## Modeling clarifications

- `TradingCalendar` already represents trading dates, sessions, holidays, and closures. Version 1 does not add `Holiday` or `TradingSession` entities.
- `IndicatorResult` already preserves the exact parameter snapshot, definition version, implementation version, input range, and configuration hash. Version 1 does not add `IndicatorParameterSnapshot`.
- `Strategy` is the strategy family or template, while `StrategyVersion` represents an immutable executable version. Version 1 does not add `StrategyTemplate`.
- Market-regime calculation is a domain service that produces `MarketRegimeSnapshot`. Version 1 does not add a `MarketRegimeEngine` entity.
- Technical Score configuration is versioned through `StrategyVersion`, and its evidence is stored in `SignalEvidence`. Version 1 does not add separate scoring-definition entities.

## Data immutability principles

- Raw source data is never overwritten. Corrections arrive as new records or batches with explicit supersession lineage.
- Normalized and adjusted market data are separate representations. A normalized `PriceBar` is not mutated into an `AdjustedPriceBar`.
- An adjusted representation must reference its normalized source and corporate-action evidence or a traceable no-adjustment policy.
- StrategyVersion and its parameters, rules, risk rules, and configuration hash are immutable once available for execution.
- Published signals and their evidence, completed analytical results, started backtest configuration, backtest results, alert evaluations, financial transactions, explanation inputs/results, and audit records preserve history.
- Mutable definitions and user organization records may change only while retaining relevant history. Derived snapshots are replaced by new snapshots, never revised in place to depict a different point in time.
- AI explanations depend only on stored deterministic evidence. Explanation text is not analytical truth and cannot modify its source evidence.
- Elliott Wave results are scenarios, not guaranteed facts or deterministic forecasts. Each scenario records its pivots, confidence, and invalidation level.
