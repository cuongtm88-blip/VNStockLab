# VNStockLab Entity Persistence Matrix V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Conventions

Every frozen Domain Model v1 entity appears exactly once below. “Authoritative” means the persisted record governs its stated fact; a derived published record may be authoritative as the historical output without replacing its source truth. “Rebuildable” assumes all frozen inputs, versions, hashes, and implementations remain. Mixed scope means explicitly shared or user-owned. Storage-only junction/child tables do not introduce domain entities.

| Entity | Domain | Physical table or tables | Persisted or computed | Authoritative or derived | Shared or user-owned | Mutable or immutable | Versioned | Rebuildable | Primary retention class | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| User | Identity | `users` | Persisted | Authoritative | User identity | Mutable/audited | Lifecycle history | No | R17 User content | Role membership is in storage-only `user_roles`. |
| Role | Identity | `roles` | Persisted | Authoritative | Shared | Mutable/audited; retire | Yes by retained reference state | No | R1 Permanent reference | Permissions are constrained JSONB metadata. |
| RefreshToken | Identity | `refresh_tokens` | Persisted | Authoritative | User-owned | Issuance immutable; controlled revocation | Rotation lineage | No | R15 Security session | Secure hash only, never raw token. |
| AuditLog | Identity/Audit | `audit_logs` | Persisted | Authoritative | Governance with owner context | Immutable/append-only | Superseding clarification events | No | R14 Audit | Logical subjects may span domains. |
| Exchange | Instruments | `exchanges` | Persisted | Authoritative | Shared | Mutable reference | Retained lifecycle | No | R1 Permanent reference | Stable venue identity. |
| Sector | Instruments | `sectors` | Persisted | Authoritative | Shared | Immutable effective version | Yes | No | R1 Permanent reference | Scheme/version is part of natural identity. |
| Industry | Instruments | `industries` | Persisted | Authoritative | Shared | Immutable effective version | Yes | No | R1 Permanent reference | Belongs to one sector. |
| Instrument | Instruments | `instruments` | Persisted | Authoritative | Shared | Mutable lifecycle/reference | History retained | No | R1 Permanent reference | One canonical instrument table. |
| InstrumentAlias | Instruments | `instrument_aliases` | Persisted | Authoritative | Shared | Immutable; supersede correction | Effective versions | No | R1 Permanent reference | Provider/exchange context and effective interval retained. |
| Index | Instruments | `indices` | Persisted | Authoritative | Shared | Mutable reference | Retained lifecycle | No | R1 Permanent reference | Methodology reference retained. |
| IndexConstituent | Instruments | `index_constituents` | Persisted | Authoritative | Shared | Immutable effective fact | Effective versions | No | R1 Permanent reference | Membership history is time-bounded. |
| DataProvider | Market Data | `data_providers` | Persisted | Authoritative | Shared | Mutable/audited | Retained lifecycle | No | R1 Permanent reference | Credentials excluded. |
| ImportBatch | Market Data | `import_batches` | Persisted | Authoritative operational record | Shared | Mutable to terminal, then immutable | Retry creates new batch | No | R2 Raw imported market data | Counts and safe diagnostics retained. |
| RawMarketRecord | Market Data | `raw_market_records` | Persisted | Authoritative source record | Shared | Immutable | Supersession lineage | No | R2 Raw imported market data | Payload or durable payload reference. |
| TradingCalendar | Market Data | `trading_calendars` | Persisted | Authoritative | Shared | Immutable once effective | Yes | No | R1 Permanent reference | One entity represents sessions/closures; no extra domain entity. |
| CorporateAction | Market Data | `corporate_actions` | Persisted | Authoritative event/evidence | Shared | Immutable event version | Yes/superseding | No | R2 Raw imported market data | Adjustment evidence retained. |
| PriceBar | Market Data | `price_bars` | Persisted | Authoritative normalized representation | Shared | Immutable published version | Yes/superseding | Re-normalizable, but published fact retained | R3 Normalized market data | Distinct from adjusted representation. |
| AdjustedPriceBar | Market Data | `adjusted_price_bars` | Persisted computed output | Derived | Shared | Immutable published version | Policy/versioned | Yes | R4 Adjusted market data | References source bar and validated action-evidence UUIDs. |
| DataQualityIssue | Market Data | `data_quality_issues` | Persisted | Authoritative finding | Shared | Finding immutable; resolution controlled | Supersession/resolution | No | R2 Raw imported market data | Failures are never silently discarded. |
| IndicatorDefinition | Technical Analysis | `indicator_definitions` | Persisted | Authoritative configuration | Shared | Draft mutable; active immutable | Yes | No | R1 Permanent reference | Calculation semantics and schemas. |
| IndicatorResult | Technical Analysis | `indicator_results` | Persisted computed output | Derived evidence | Shared | Immutable published result | Definition/implementation/config versioned | Yes | R5 Analytical evidence | Parameter snapshot and input range retained; no separate parameter-snapshot entity. |
| PatternDefinition | Technical Analysis | `pattern_definitions` | Persisted | Authoritative configuration | Shared | Draft mutable; active immutable | Yes | No | R1 Permanent reference | Pattern semantics. |
| PatternDetection | Technical Analysis | `pattern_detections` | Persisted computed output | Derived evidence | Shared | Immutable published result | Yes | Yes | R5 Analytical evidence | Detection and rejection evidence supported. |
| SupportResistanceLevel | Technical Analysis | `support_resistance_levels` | Persisted computed output | Derived evidence/snapshot | Shared | Immutable snapshot | Method/config versioned | Yes | R5 Analytical evidence | Later invalidation is new evidence, not rewrite. |
| MarketStructureSnapshot | Technical Analysis | `market_structure_snapshots` | Persisted computed output | Derived snapshot | Shared | Immutable | Yes | Yes | R5 Analytical evidence | Includes pivots and breaks. |
| ElliottScenario | Technical Analysis | `elliott_scenarios` | Persisted computed output | Derived scenario/evidence | Shared | Immutable scenario | Yes | Yes | R5 Analytical evidence | Primary/alternative class, confidence, invalidation. |
| Strategy | Strategies | `strategies` | Persisted | Authoritative family | Mixed scope | Mutable metadata/audited | Versions via child | No | R7 Versioned configuration | Executable meaning is not on family row. |
| StrategyVersion | Strategies | `strategy_versions` | Persisted | Authoritative configuration | Inherits strategy | Draft mutable; published immutable | Yes | No | R7 Versioned configuration | Exact version/hash used by all consumers. |
| StrategyParameter | Strategies | `strategy_parameters` | Persisted | Authoritative configuration | Inherits strategy | Immutable with published version | Parent version | No | R7 Versioned configuration | One typed named value per version. |
| StrategyRule | Strategies | `strategy_rules` | Persisted | Authoritative configuration | Inherits strategy | Immutable with published version | Parent version | No | R7 Versioned configuration | Shared-engine deterministic rule. |
| StrategyRiskRule | Strategies | `strategy_risk_rules` | Persisted | Authoritative configuration | Inherits strategy | Immutable with published version | Parent version | No | R7 Versioned configuration | Advisory risk/trade-plan constraints only. |
| ScanDefinition | Scanner | `scan_definitions` | Persisted | Authoritative configuration | Mixed scope | Mutable/audited | Run freezes snapshot | No | R17 User content / R7 configuration | Uses a published strategy version. |
| ScanRun | Scanner | `scan_runs` | Persisted execution | Authoritative run record | Inherits definition | Context immutable after start; status controlled | Snapshot/hash | Re-executable, historical run retained | R5 Analytical evidence | Freezes universe and market-data cutoff. |
| ScanResult | Scanner | `scan_results` | Persisted computed output | Derived evidence | Inherits run | Immutable | Run/config versioned | Yes | R5 Analytical evidence | One result per run/instrument. |
| Signal | Signals and Trade Plans | `signals` | Persisted computed output | Derived; authoritative published output | Context scope | Immutable after publication | Strategy/config versioned | Yes | R6 Signals and trade plans | Lifecycle events cannot rewrite evidence. |
| SignalEvidence | Signals and Trade Plans | `signal_evidence` | Persisted computed output | Derived evidence | Inherits signal | Immutable/append-only | Evidence/config versioned | Yes | R6 Signals and trade plans | Includes Technical Score category contributions. |
| TradePlan | Signals and Trade Plans | `trade_plans`, `trade_plan_targets` | Persisted computed output | Derived advisory output | Inherits signal | Immutable after publication | Strategy/risk versioned | Yes | R6 Signals and trade plans | Targets are relational ordered child rows, not a new domain entity. |
| BacktestDefinition | Backtesting | `backtest_definitions` | Persisted | Authoritative configuration | Mixed scope | Mutable/audited | Run snapshots | No | R8 Backtests | V1 daily and long-only checks. |
| BacktestRun | Backtesting | `backtest_runs` | Persisted execution | Authoritative historical execution | Inherits definition | Configuration immutable after start | Dataset/strategy/config versioned | Re-executable if inputs retained | R8 Backtests | Preserves cutoff, costs, assumptions, and failures. |
| BacktestTrade | Backtesting | `backtest_trades` | Persisted computed output | Derived result | Inherits run | Immutable | Run version context | Yes | R8 Backtests | Long trade accounting only. |
| BacktestEquityPoint | Backtesting | `backtest_equity_points` | Persisted computed output | Derived snapshot | Inherits run | Immutable | Run version context | Yes | R8 Backtests | Ordered by run/time. |
| BacktestMetric | Backtesting | `backtest_metrics` | Persisted computed output | Derived result | Inherits run | Immutable | Metric definition/version | Yes | R8 Backtests | Undefined values are explicit. |
| Watchlist | Watchlists | `watchlists` | Persisted | Authoritative organization | User-owned | Mutable/archive | No | No | R17 User content | Exactly one owner. |
| WatchlistItem | Watchlists | `watchlist_items` | Persisted | Authoritative membership | User-owned | Mutable membership; optional history | Effective add/remove | No | R17 User content | Owner inherited from watchlist. |
| Portfolio | Portfolios | `portfolios` | Persisted | Authoritative root | User-owned | Mutable metadata/archive | No | No | R9 Financial history | No broker authority. |
| PortfolioTransaction | Portfolios | `portfolio_transactions` | Persisted | Authoritative financial fact | User-owned | Immutable/append-only | Correction/reversal lineage | No | R9 Financial history | Never silently edited or deleted. |
| PortfolioPosition | Portfolios | `portfolio_positions` | Persisted computed output | Derived snapshot | User-owned | Immutable snapshot | Derivation version | Yes | R10 Portfolio/risk snapshots | Transactions remain source of truth. |
| PortfolioValuation | Portfolios | `portfolio_valuations` | Persisted computed output | Derived snapshot | User-owned | Immutable snapshot | Calculation version | Yes | R10 Portfolio/risk snapshots | Currency and price references retained. |
| RiskProfile | Risk Management | `risk_profiles` | Persisted | Authoritative configuration | User-owned | Draft mutable; effective version immutable | Yes | No | R7 Versioned configuration | Recommendations retain profile snapshot. |
| PositionSizeRecommendation | Risk Management | `position_size_recommendations` | Persisted computed output | Derived advisory evidence | User-owned | Immutable | Profile/method/config versioned | Yes | R10 Portfolio/risk snapshots | Cannot place orders. |
| PortfolioRiskSnapshot | Risk Management | `portfolio_risk_snapshots` | Persisted computed output | Derived snapshot | User-owned | Immutable | Calculation version | Yes | R10 Portfolio/risk snapshots | Same-owner portfolio/profile required. |
| MarketBreadthSnapshot | Market Intelligence | `market_breadth_snapshots` | Persisted computed output | Derived snapshot | Shared | Immutable | Calculation version | Yes | R5 Analytical evidence | Universe and coverage explicit. |
| RelativeStrengthSnapshot | Market Intelligence | `relative_strength_snapshots` | Persisted computed output | Derived snapshot | Shared | Immutable | Method version | Yes | R5 Analytical evidence | Subject/benchmark are typed references. |
| SectorRotationSnapshot | Market Intelligence | `sector_rotation_snapshots` | Persisted computed output | Derived snapshot | Shared | Immutable | Method version | Yes | R5 Analytical evidence | Sector measures remain structured evidence. |
| MarketRegimeSnapshot | Market Intelligence | `market_regime_snapshots` | Persisted computed output | Derived snapshot | Shared | Immutable | Method version | Yes | R5 Analytical evidence | Deterministic classification; no engine entity. |
| AlertRule | Alerts | `alert_rules` | Persisted | Authoritative configuration | User-owned | Mutable/audited | Evaluations freeze snapshots | No | R17 User content | V1 channels only. |
| AlertEvaluation | Alerts | `alert_evaluations` | Persisted execution/output | Authoritative outcome; derived analysis | User-owned | Terminal immutable | Rule/strategy/config snapshot | Re-evaluable, original retained | R11 Alert evaluations | Records what was checked and cutoff. |
| NotificationDelivery | Alerts | `notification_deliveries` | Persisted | Authoritative operational event | User-owned | Controlled to terminal, then immutable | Attempts/retry lineage | No | R12 Delivery logs | Provider diagnostics are safe/redacted. |
| JournalEntry | Trading Journal | `journal_entries` | Persisted | Authoritative personal record | User-owned | Draft mutable; finalized revised explicitly | Revision lineage | No | R17 User content | Optional same-owner/shared context. |
| JournalAttachment | Trading Journal | `journal_attachments` | Persisted metadata; external binary | Authoritative file metadata | User-owned | Available metadata immutable; removal recorded | Validation/removal state | No | R17 User content | Storage reference is access-controlled. |
| JournalReview | Trading Journal | `journal_reviews` | Persisted | Authoritative personal record | User-owned | Draft mutable; finalized revision | Review version | No | R17 User content | Does not rewrite entry/evidence. |
| ExplanationRequest | AI Explanations | `explanation_requests` | Persisted | Authoritative request/input | User-owned | Input immutable; status controlled | Template/model/input snapshot | No | R13 AI interactions | References only frozen deterministic evidence; no keys. |
| ExplanationResult | AI Explanations | `explanation_results` | Persisted computed output | Derived prose, not analytical truth | User-owned | Immutable terminal output | Model/template | Yes | R13 AI interactions | At most one per request; regeneration uses a new request. |

## Storage-only representations

- `user_roles` is the required relational junction for the frozen many-to-many `User`–`Role` relationship. It is not a new domain entity.
- `trade_plan_targets` is an ordered value collection owned by `TradePlan`. Relational storage gives each stable target exact numeric typing, ordering, uniqueness, and allocation checks.
- Polymorphic evidence lists, provider payloads, versioned configurations, and safe diagnostics use documented JSONB where stable relational columns cannot express variable shapes. Their owning domain entity remains the primary matrix row.
