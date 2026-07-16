# VNStockLab Logical Data Model V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Purpose and legend

This document describes the logical persistence model by frozen bounded domain. “Authority” identifies the record that governs its own fact; derived records are authoritative only as historical outputs, not as replacements for their source facts. “History” states whether prior versions or point-in-time outputs remain. Natural identity is the business key protected in addition to the UUID.

## Identity

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| User | Authentication and ownership boundary; normalized email | display name, password hash, state, timestamps | Own identity; mutable profile/security state | roles, refresh tokens, all owned roots, audit actor | transactional, authoritative; history retained/audited |
| Role | Shared authorization role; role name | description, permission set, active state | Shared; mutable under audit | many users | reference, authoritative; retired history retained |
| RefreshToken | Revocable session; secure token hash | issued, expiry, revoked, rotation lineage, client context | User-owned; issuance immutable, controlled revocation | user, predecessor token | transactional, authoritative security record; retained by policy |
| AuditLog | Important action fact; audit UUID | occurred time, actor/system, owner, action, subject, correlation, outcome, safe details | Governance record; append-only | optional actor user and logical subject | event/evidence, authoritative; permanent/configurable archive |

`User`–`Role` membership is represented by the storage-only `user_roles` junction and does not add a domain entity.

## Instruments

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| Exchange | Trading venue; code | name, IANA timezone, currency, state | Shared; mutable reference | instruments, calendars | reference, authoritative; identity retained |
| Sector | Classification; scheme + version + code | name, effective dates, state | Shared; versioned reference | industries, instruments | reference, authoritative; yes |
| Industry | Sector subdivision; scheme + version + code | name, effective dates, state | Shared; versioned reference | sector, instruments | reference, authoritative; yes |
| Instrument | Canonical security; exchange + symbol + listing date | name, type, ISO-4217 currency, classifications, lifecycle (`active`, `suspended`, `delisted`, `merged`) | Shared; controlled mutable reference; never physically deleted | aliases, bars, actions, analytics, signals, backtests, portfolios, user tools | permanent reference, authoritative; all historical references remain valid |
| InstrumentAlias | Time-bounded alternate identity; context + type + value + effective-from | effective-to, source, status | Shared; immutable effective fact, correction supersedes | instrument, optional provider/exchange | reference, authoritative; yes |
| Index | Market index; context + code | name, currency, methodology reference, state | Shared; mutable reference | constituents, intelligence | reference, authoritative; yes |
| IndexConstituent | Membership; index + instrument + effective-from | effective-to, weight, source | Shared; immutable effective fact | index, instrument | reference, authoritative; yes |

## Market Data

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| DataProvider | Source identity; source code | name, supported types, timezone conventions, state | Shared; mutable under audit | batches and records | reference, authoritative; yes |
| ImportBatch | One intake attempt; provider + source reference/checksum + start | requested/covered range, mode, status, counts, diagnostics | Shared; mutable until terminal, then frozen | provider, raw records, outputs, issues | transactional, authoritative operational record; yes |
| RawMarketRecord | Lossless received fact; provider + source key + checksum + receipt | source/received timestamps, payload/reference, parse state | Shared; immutable | provider, batch, optional instrument and outputs | event/evidence, authoritative source record; yes |
| TradingCalendar | Effective session definition; exchange + session date + version | session times, type, closure reason, source | Shared; immutable once effective | exchange, timestamp validation | reference, authoritative; versions retained |
| CorporateAction | Price-comparability event; instrument + type + effective/ex date + provider identity | announcement dates, ratio/amount, currency, evidence, status, supersession | Shared; immutable event version | instrument, provider, batch, adjusted bars | event/evidence, authoritative; yes |
| PriceBar | Normalized unadjusted bar; instrument + canonical timeframe + time + representation/version + provider policy | OHLC, volume/value, provider/batch, normalization version, source lineage, supersession | Shared; append-only | instrument, raw/batch/provider, adjusted bars | transactional market record, authoritative normalized representation; incorrect imports are superseded through new batches and retained evidence |
| AdjustedPriceBar | Adjusted bar; source bar + policy/version | adjusted OHLC/volume/value, factors, action evidence, lineage | Shared; immutable when published | price bar, actions, provider/batch | derived snapshot, rebuildable; published versions retained |
| DataQualityIssue | Preserved finding; rule + affected context + detection time | severity, status, details, resolution/supersession | Shared; immutable finding, controlled status | provider, batch, optional instrument/record | event/evidence, authoritative finding; yes |

## Technical Analysis

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| IndicatorDefinition | Versioned calculation meaning; name + version | schemas, defaults, warm-up, output contract, implementation version | Shared; immutable once active | results | configuration, authoritative; versions retained |
| IndicatorResult | Reproducible output; definition + instrument + timeframe + as-of + configuration/input identity | representation, parameter snapshot, implementation version, hash, input range/evidence, payload | Shared; immutable published evidence | definition, instrument, bars, downstream evidence | derived event/evidence, rebuildable; published history retained |
| PatternDefinition | Versioned pattern meaning; name + version | family, input/parameter schemas, implementation version | Shared; immutable once active | detections | configuration, authoritative; versions retained |
| PatternDetection | Pattern outcome; definition + instrument + timeframe + as-of + configuration/input identity | classification, confidence, parameters, range, evidence/pivots | Shared; immutable published evidence | definition, instrument, bars, signal evidence | derived event/evidence, rebuildable; history retained |
| SupportResistanceLevel | As-of level/zone; instrument + timeframe + as-of + method/version + kind/ordinal | prices, strength, touches, input range, invalidation/expiry | Shared; immutable snapshot | instrument, bars, signals/plans | derived snapshot, rebuildable; yes |
| MarketStructureSnapshot | As-of structure; instrument + timeframe + as-of + method/version | state, pivots, breaks, confidence, input range/evidence | Shared; immutable | instrument, bars, evaluations | derived snapshot, rebuildable; yes |
| ElliottScenario | Scenario; instrument + timeframe + as-of + method/version + class/ordinal | pivots/waves, primary/alternative, confidence, invalidation, evidence, limitations | Shared; immutable scenario | instrument, bars, evidence/explanations | derived event/evidence, rebuildable; yes |

## Strategies

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| Strategy | Stable family; owner scope + owner + name | description, state, timestamps | Shared or user-owned; mutable metadata | versions | configuration, authoritative; yes |
| StrategyVersion | Executable configuration; strategy + version label | timeframe scope, hash, implementation/effective/publication data, status | Inherits scope; immutable once published | parameters, rules, risk rules; scans/signals/alerts/backtests | configuration, authoritative; all versions retained |
| StrategyParameter | Typed value; version + name | type, value/default, range, unit, order | Inherits scope; immutable with published version | strategy version | configuration, authoritative; retained with version |
| StrategyRule | Deterministic rule; version + order | type, expression/specification, group, evidence requirements, contribution | Inherits scope; immutable with version | strategy version, analytical contracts | configuration, authoritative; retained |
| StrategyRiskRule | Risk constraint; version + priority | type, parameters, applicability, limits | Inherits scope; immutable with version | strategy version, plan/risk context | configuration, authoritative; retained |

## Scanner and Signals

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| ScanDefinition | Repeatable scan; scope/owner + name | universe policy, timeframe, strategy version, bindings, schedule, state | Shared or user-owned; mutable | strategy version, runs | configuration, authoritative; run snapshots retain history |
| ScanRun | One execution; definition + run UUID | frozen definition/universe, strategy/hash, data cutoff, timestamps, status, diagnostics | Inherits definition; context frozen after start | definition, strategy version, results | transactional execution, authoritative; yes |
| ScanResult | Per-instrument outcome; run + instrument | evaluation time, classification, score, matched rules, evidence, rank, outcome | Inherits run; immutable | run, instrument, optional signal | derived event/evidence, rebuildable from frozen inputs; retained |
| Signal | Published decision support; generation context/idempotency key | instrument, timeframe, strategy version, generated/data-cutoff times, classification, score/confidence, trigger, status, configuration | Shared or user-owned; immutable after publication | evidence, optional plan, scans/alerts/explanations | derived event/evidence, rebuildable but authoritative published record; retained |
| SignalEvidence | Structured support; signal + sequence/type/reference | observed value, outcome, score category/contribution, safe facts, lineage | Inherits signal; append-only/frozen | signal and deterministic evidence | event/evidence, rebuildable; retained with signal |
| TradePlan | Advisory plan; one per signal | buy zone, entry, stop, risk/reward, ratio, invalidation, timestamps/status | Inherits signal; immutable when published | signal, ordered target rows, risk evidence | derived event/evidence, rebuildable; retained |

Trade-plan target levels use relational `trade_plan_targets` ordered by `target_number`. This storage table is part of `TradePlan`, not a new frozen domain entity.

## Backtesting

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| BacktestDefinition | Reusable long-only daily simulation setup; scope/owner + name | strategy, universe, dates, capital/currency, costs, execution/risk/sizing assumptions | Shared or user-owned; mutable definition | strategy version, runs | configuration, authoritative; run snapshots retained |
| BacktestRun | Immutable execution; definition + run UUID | StrategyVersion, indicator implementation version, dataset cutoff, configuration hash, data snapshot identity/equivalent reproducibility reference, warm-up, timings, status, diagnostics | Inherits definition; immutable after start except terminal state | definition, strategy version, trades, equity points, metrics | reproducible transactional execution, authoritative historical run; retained |
| BacktestTrade | Simulated long trade; run + sequence | instrument, evidence, decision/fill times and prices, quantity/costs, stops/targets, result | Inherits run; immutable | run, instrument, signal/evidence | derived event/evidence, rebuildable; retained |
| BacktestEquityPoint | Ordered equity state; run + timestamp | cash, invested value, equity, P&L, drawdown, count | Inherits run; immutable | run | derived snapshot, rebuildable; retained |
| BacktestMetric | Versioned metric; run + name + definition version + period | value, unit, inputs, calculation time, defined state | Inherits run; immutable | run | derived, rebuildable; retained |

## Watchlists, Portfolios, and Risk

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| Watchlist | User collection; user + normalized name | description, state, timestamps | User-owned; mutable | user, items | transactional, authoritative; archive retained |
| WatchlistItem | Membership; watchlist + instrument + active period | added/removed times, note, order | User-owned; mutable membership/history | watchlist, instrument | transactional, authoritative; configurable history |
| Portfolio | Tracked account context; user + name | base currency, inception, description, state | User-owned; mutable metadata | transactions, positions, valuations | transactional, authoritative root; retained |
| PortfolioTransaction | Financial event; portfolio + idempotency/source identity | instrument, type, effective time, quantity/price/costs/cash/currency, correction lineage | User-owned; append-only | portfolio, instrument, corrected record | transactional, authoritative financial fact; permanent |
| PortfolioPosition | Derived holding; portfolio + instrument + as-of + derivation version | quantity, basis/cost, P&L, transaction range | User-owned; immutable snapshot | portfolio, instrument, transactions | derived snapshot, rebuildable; policy-based |
| PortfolioValuation | Portfolio value; portfolio + as-of + calculation version | cash, holdings/total value, P&L, currency, price references | User-owned; immutable snapshot | portfolio, positions/market data | derived snapshot, rebuildable; policy-based |
| RiskProfile | Effective risk constraints; user + name + effective-from/version | capital basis, per-trade/position/concentration limits, state | User-owned; effective-version mutable workflow | recommendations, risk snapshots | configuration, authoritative; versions retained |
| PositionSizeRecommendation | Advisory calculation; user + opportunity context + as-of + hash | profile snapshot, instrument, entry/stop, capital, recommended size/value, risk, constraints | User-owned; immutable | profile, instrument, optional plan/portfolio | derived event/evidence, rebuildable; policy-based |
| PortfolioRiskSnapshot | As-of portfolio risk; portfolio + as-of + method version | exposures, concentration, liquidity/risk measures, breaches, inputs | User-owned; immutable | profile, portfolio, positions/valuation | derived snapshot, rebuildable; policy-based |

## Market Intelligence

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| MarketBreadthSnapshot | Participation state; market/index/universe + timeframe + as-of + method | counts, measures, coverage, data references | Shared; immutable | index/universe, market data | derived snapshot, rebuildable; retained |
| RelativeStrengthSnapshot | Comparative strength; subject + benchmark + timeframe + as-of + lookback + method | value, rank, coverage, inputs | Shared; immutable | instrument/sector/index subjects, market data | derived snapshot, rebuildable; retained |
| SectorRotationSnapshot | Sector comparison; universe/benchmark + timeframe + as-of + method | sector measures/ranks/state, coverage, inputs | Shared; immutable | sectors, benchmark, relative strength | derived snapshot, rebuildable; retained |
| MarketRegimeSnapshot | Deterministic regime; market/index + timeframe + as-of + method | classification, confidence, components, range | Shared; immutable | index, breadth, technical evidence | derived snapshot, rebuildable; retained |

## Alerts, Journal, and AI

| Logical entity | Purpose and natural identity | Main attributes | Ownership; mutability | Principal relationships | Class; history |
| --- | --- | --- | --- | --- | --- |
| AlertRule | User condition; user + name | instrument/universe, timeframe, condition, strategy/bindings, channels, schedule, state | User-owned; mutable definition | strategy version, evaluations | configuration, authoritative; audit/run history retained |
| AlertEvaluation | Frozen evaluation; rule + evaluated time/dedup key | rule snapshot, data cutoff, strategy/hash, outcome, evidence, status, diagnostics | User-owned; immutable terminal record | rule, strategy, deliveries | event/evidence, authoritative outcome and rebuildable analysis; retained |
| NotificationDelivery | One attempt; evaluation + channel + attempt number | destination reference, template/version, timestamps, status, provider diagnostics, retry lineage | User-owned; terminal attempt immutable | evaluation, prior attempt | event/evidence, authoritative operational fact; configurable retention |
| JournalEntry | Decision/observation; user + entry UUID | times, title/body/type, optional context, tags, state/finalization | User-owned; draft mutable, finalized versioned | instrument, signal/plan/portfolio, attachments/reviews | transactional, authoritative personal record; retained by user policy |
| JournalAttachment | Controlled file metadata; entry + checksum/storage reference | filename/type/size, uploaded time, validation state | User-owned; immutable available metadata; removal recorded | journal entry/user | transactional, authoritative metadata; content policy-based |
| JournalReview | Retrospective; entry + review UUID | time, assessment, adherence, lessons, evidence/version, state | User-owned; draft mutable, finalized immutable | journal entry | transactional, authoritative personal record; retained |
| ExplanationRequest | Frozen grounded input; user + request UUID | subject, evidence snapshot, constraints, provider/model/template, checksum, timestamps/status | User-owned; input immutable, status controlled | user, deterministic evidence, results | event/evidence, authoritative request; configurable retention |
| ExplanationResult | Separate generated prose; request + attempt | text, citations, disclaimer, provider/model/template, time, status, diagnostics | User-owned; immutable output | request only; never source evidence | derived event/evidence, regenerable but not analytical truth; configurable retention |

AI explanation modules consume grounded `IndicatorResult`, `Signal`, `SignalEvidence`, and `TradePlan` records. They must not independently derive analytical truth from raw `PriceBar` records; explanation output remains prose grounded in cited deterministic evidence.

## Authority and rebuildability summary

Authoritative records include identities and roles, canonical reference data, provider intake and raw records, normalized published bars, corporate actions, versioned definitions and strategy configurations, user definitions, portfolio transactions, immutable published execution records, notification attempts, journal content, AI requests, and audit facts. Derived and rebuildable data include adjusted bars; all technical-analysis outputs; scan results; signals, evidence, and plans; backtest trades/equity/metrics when frozen inputs remain; positions, valuations, recommendations, risk snapshots; market-intelligence snapshots; and explanation prose. A persisted derived record is still the authoritative account of what VNStockLab published at that time and must not be silently replaced.
