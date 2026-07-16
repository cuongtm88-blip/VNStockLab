# VNStockLab Domain Rules V1

**Status:** Frozen  
**Version:** 1.0  
**Date:** 2026-07-16

## Purpose

These rules are normative, implementation-neutral, and testable. “Must” and “must not” indicate requirements of the frozen version 1 domain. Tests may verify them through domain services, persisted records, batch processing, or end-to-end behavior without changing their meaning.

## Instrument identity

**II-001 — Canonical mapping.** Every `InstrumentAlias` must map to exactly one canonical `Instrument`. Resolving an effective alias must return that instrument and must not create a new canonical instrument.

**II-002 — Contextual uniqueness.** For any overlapping effective period, the same normalized alias type and value must not map to conflicting instruments within the same provider or exchange context. A detected conflict must be rejected or recorded for resolution before the alias is effective.

**II-003 — Historical retention.** Ending, replacing, or correcting an alias must retain the earlier alias, its effective dates, source, context, status, and canonical-instrument mapping.

**II-004 — Immutable effective aliases.** Once an `InstrumentAlias` has been effective, its alias value, type, context, effective dates, source, and instrument mapping must not be overwritten. A correction creates a superseding alias record with explicit lineage.

**II-005 — No duplicate canonical identity.** A provider-specific symbol, former exchange symbol, abbreviation, or former company name that resolves through an alias must not cause creation of a duplicate canonical `Instrument`.

## A. Market data

**MD-001 — OHLC validity.** For every `PriceBar` and `AdjustedPriceBar`, `high` must be greater than or equal to `open`, `close`, and `low`; `low` must be less than or equal to `open`, `close`, and `high`; and all four prices must be present, finite, and valid for the instrument's price conventions. A violating bar must not be published as valid analysis input.

**MD-002 — Non-negative activity values.** Bar volume must be present and greater than or equal to zero. Trading value, when supplied, must be greater than or equal to zero. Missing trading value must remain distinguishable from zero.

**MD-003 — Bar uniqueness.** At most one effective published bar may exist for a given instrument, timeframe, timestamp, and representation identity. Representation identity must distinguish normalized data from each adjusted policy/version. A correction must supersede rather than overwrite the earlier bar.

**MD-004 — Provider traceability.** Every raw record and published bar must identify its `DataProvider`, `ImportBatch`, and ingestion timestamp. A published bar must also be traceable to one or more raw source records or to a documented provider-derived source record within the batch.

**MD-005 — Raw immutability.** Once a `RawMarketRecord` is received, its source content, provider, source timestamp, ingestion timestamp, checksum, and batch association must not be altered. A provider correction or re-import creates a new raw record and batch lineage.

**MD-006 — Separate representations.** Normalized `PriceBar` and `AdjustedPriceBar` records must remain separately identifiable. Adjustment processing must never replace the normalized source representation.

**MD-007 — Adjustment evidence.** Every non-identity price or volume adjustment must identify the adjustment policy/version, source normalized bar, applied factor, and supporting `CorporateAction` evidence. If the effective factor is one because no action applies, that fact and the policy/version must still be traceable.

**MD-008 — Corporate-action temporal validity.** Only corporate actions effective under the recorded adjustment policy at the bar's timestamp may affect that adjusted bar. Cancelled or unconfirmed actions must not be applied unless the policy explicitly permits their recorded status.

**MD-009 — Trading-calendar validation.** A regular-session bar must correspond to a valid session in the applicable `TradingCalendar`; any permitted exception must be explicitly classified and traceable.

**MD-010 — Quality failure recording.** A structural, mapping, timestamp, range, OHLC, duplicate, adjustment, completeness, or consistency failure must create or update the resolution state of a `DataQualityIssue`. The invalid input must not silently enter downstream analysis and must not be repaired with fabricated values.

**MD-011 — Ingestion terminal history.** Failed, partially completed, and cancelled import batches must retain processed counts, failure diagnostics, and the range attempted. A retry is a distinct `ImportBatch`.

## B. Technical analysis

**TA-001 — Warm-up requirement.** An `IndicatorResult` must not be published until the definition's required warm-up observations are available. Warm-up observations may contribute to calculation state but must be distinguishable from the requested output period.

**TA-002 — Deterministic reproducibility.** Given the same ordered input representation, input range, parameter values, definition/implementation version, and time conventions, a technical calculation must produce the same result. Any controlled numeric tolerance must be defined by the calculation contract.

**TA-003 — Input traceability.** Every published indicator result, pattern detection, support/resistance level, market-structure snapshot, and Elliott scenario must identify its instrument, timeframe, as-of timestamp, exact input range, source representation or bar set, parameters, and calculation/definition version.

**TA-004 — No future data.** No technical result with as-of time `T` may read a market observation, corporate-action state, or derived fact that was not available under the evaluation context at `T`.

**TA-005 — Indicator parameter validity.** Indicator parameter values must satisfy the active definition's types, ranges, and inter-parameter constraints. Invalid parameters must produce a recorded validation failure, not a calculated value.

**TA-006 — Pattern evidence preservation.** Every published `PatternDetection` must retain the input bars or immutable references, pivots/features, definition version, direction or classification, and confidence used. Re-detection creates a new result rather than changing this evidence.

**TA-007 — Support/resistance evidence.** A support or resistance level/zone must identify its derivation method, price or bounds, as-of time, supporting observations, strength measure, and invalidation or expiry semantics.

**TA-008 — Market-structure point-in-time state.** A `MarketStructureSnapshot` must retain the pivots, breaks, or other structure evidence available at its as-of timestamp and must not be revised to incorporate later confirmation.

**TA-009 — Elliott scenario requirements.** Every `ElliottScenario` must contain the labeled pivots supporting the interpretation, a bounded confidence value, and a price-based invalidation level. It must be presented as a scenario, not a guaranteed fact or price forecast.

**TA-010 — Canonical implementation.** Scanner, backtesting, signals, alerts, dashboards, and AI evidence must use the same versioned canonical technical-analysis implementation and definitions for the same indicator or analytical calculation. A consumer must not maintain an independent implementation or silently substitute a different formula, warm-up policy, rounding policy, or parameter default.

**TA-011 — Equivalent execution forms.** A technical result may be persisted, cached, materialized, or calculated on demand; the system is not required to physically calculate every indicator only once. Given identical ordered input bars, input representation, definition version, exact parameter snapshot, implementation version, and configuration hash, each execution form must produce a reproducible and equivalent result within the calculation's declared numeric tolerance.

**TA-012 — Immutable indicator evidence.** A published `IndicatorResult` must preserve its exact parameter snapshot, definition version, implementation version, input range, source representation, and configuration hash and must not be altered. Recalculation or correction creates a new result with lineage.

**TA-013 — Backtest calculation parity.** Backtesting must use the same technical-analysis calculation semantics as live scanning while limiting inputs to data available at each simulated point in time. Reuse of canonical semantics must not weaken no-future-data, no-look-ahead-bias, or warm-up requirements.

## C. Strategies

**ST-001 — Immutable execution version.** Every strategy execution must use exactly one published, immutable `StrategyVersion`. A draft or partially specified strategy must not execute.

**ST-002 — Shared evaluation implementation.** Scanner, backtesting, and strategy-derived alerts must invoke the same Strategy Engine evaluation implementation and rule semantics. Consumer-specific orchestration must not duplicate or reinterpret strategy rules.

**ST-003 — Version on change.** Any change to executable rules, parameters, parameter defaults, risk rules, scoring behavior, timeframe applicability, or other execution semantics must create a new `StrategyVersion`.

**ST-004 — Configuration hash.** A published StrategyVersion must retain a configuration hash covering its ordered canonical parameters, rules, risk rules, scoring configuration, and relevant implementation version. Every execution result must preserve that hash or an immutable reference to it.

**ST-005 — Evidence-required outcome.** The Strategy Engine must not emit a successful classification, score, matched-rule outcome, signal candidate, or trigger without immutable references to the deterministic inputs and rule outcomes supporting it.

**ST-006 — Frozen Technical Score.** Technical Score category maximums must be Trend 25, Momentum 20, Volume 15, Money Flow 15, Market Structure 15, and Pattern Confirmation 10. Contributions must be individually retained, the total must equal their sum, and the total must be between 0 and 100 inclusive.

**ST-007 — Point-in-time parameters.** An execution must preserve the exact effective parameter values, including defaults resolved at execution time. Later changes to a strategy definition must not affect the recorded execution.

## D. Signals

**SG-001 — Decision-support classification.** A Signal classification is decision-support output and must not be represented as a guaranteed investment outcome, guaranteed recommendation, or broker instruction.

**SG-002 — Score is insufficient alone.** A high Technical Score alone must not create or imply a Buy classification. The applicable StrategyVersion's explicit rules and required evidence must independently support the classification.

**SG-003 — Required signal lineage.** Every published Signal must include instrument, timeframe, generated timestamp, exact market-data timestamp, StrategyVersion, resolved parameter snapshot or configuration hash, classification, score, confidence, trigger price when applicable, status, and immutable evidence references.

**SG-004 — Contextual evidence.** A Signal must include or explicitly mark the availability of liquidity, support/resistance, expected risk-reward, and market-regime context. When the context is available for the as-of time, it must be referenced in `SignalEvidence`; when unavailable, it must not be invented and the absence must be explicit.

**SG-005 — Evidence immutability.** After a Signal is published, its evidence references, observed values, rule outcomes, category contributions, input timestamps, StrategyVersion, and parameters must not be altered.

**SG-006 — Historical re-evaluation.** Re-evaluating an instrument or strategy context must create a new Signal or an explicit immutable revision/supersession record. It must not overwrite historical evidence or make the old Signal appear to have used later information.

**SG-007 — Trade-plan completeness.** A published `TradePlan` must contain a buy zone, entry trigger, stop loss, one or more targets, expected risk, expected reward, risk-reward ratio, and invalidation condition. A value that is not applicable must be explicitly classified rather than silently omitted.

**SG-008 — Trade-plan coherence.** Expected risk, expected reward, and risk-reward ratio must be reproducible from the recorded entry assumption, stop, target assumption, sizing basis, and costs where applicable. The plan must follow the associated StrategyRiskRule constraints.

**SG-009 — Advisory boundary.** A Signal or TradePlan must not submit, amend, cancel, or imply execution of a broker order.

## E. Backtesting

**BT-001 — No look-ahead bias.** At each simulated decision time, the run may access only data and derived evidence available under the recorded point-in-time context. Later bars, later-confirmed pivots, revised future classifications, and future corporate-action knowledge must not affect that decision.

**BT-002 — No data leakage.** Instrument selection, preprocessing, normalization statistics, rankings, parameters, and filters for a simulated time must not use observations outside the information set available at that time.

**BT-003 — Warm-up exclusion.** Indicator warm-up data may initialize calculations but must be excluded from the tradable period. No order or trade may be generated before both the requested start and all required warm-up conditions are satisfied.

**BT-004 — Realistic execution timing.** A decision based on a completed daily bar must not execute at a price or time preceding that bar's availability. The run must record its decision timing, order timing, fill timing, and fill-price policy.

**BT-005 — Explicit costs.** Every run must record fee, tax, and slippage assumptions. Every simulated trade must record the amounts actually applied, including explicit zero values when the configured amount is zero.

**BT-006 — Version 1 scope.** Every version 1 backtest must use daily data, permit long positions only, and reject short-sale behavior or intraday execution assumptions.

**BT-007 — Frozen run configuration.** Once a `BacktestRun` starts, its StrategyVersion, configuration hash, universe, date range, initial capital, execution policy, fees, taxes, slippage, stop loss, take profit, trailing stop, sizing, position limits, reinvestment policy, data representation, and data snapshot/version must not change.

**BT-008 — Shared Strategy Engine.** Backtest decisions must be produced by the same Strategy Engine implementation used by scanner and strategy-derived alerts, using the recorded StrategyVersion.

**BT-009 — Accounting reconciliation.** Trades, cash movements, positions, fees, taxes, and equity points must reconcile under the recorded accounting rules. A completed run with a reconciliation failure must be marked invalid or failed rather than published as successful.

**BT-010 — Failure preservation.** A failed or cancelled run must retain its frozen configuration, status history, last safe progress marker, and diagnostic information. Partial results must be explicitly identified as partial and must not be represented as completed metrics.

**BT-011 — Reproducible metrics.** Each metric must identify its definition/version, evaluation period, unit, and source run. Recalculation under changed metric semantics creates a new metric record or version.

## F. User data

**UD-001 — User isolation.** Every read, mutation, execution, export, attachment access, evaluation, and notification involving user-owned data must enforce the owning `user_id`. Knowledge of an identifier alone must not grant cross-user access.

**UD-002 — Ownership inheritance.** A child of a user-owned aggregate must have the same owner as its root. Cross-references between two user-owned aggregates are valid only when their owners match, unless an explicit frozen shared-data relationship applies.

**UD-003 — Positions derived from transactions.** `PortfolioPosition` must be derived from the portfolio's effective transaction history and must not be the authoritative source for financial history. Recalculation must reconcile to the referenced transaction range.

**UD-004 — Financial history preservation.** A recorded portfolio transaction must not be silently edited or deleted. Corrections and reversals must be separate, traceable transactions that preserve the original fact and actor context.

**UD-005 — Valuation traceability.** Every portfolio valuation must identify its as-of timestamp, positions or transaction-derived state, market-price references, base currency, and calculation version.

**UD-006 — Journal attachment ownership.** A `JournalAttachment` may be created, read, replaced, or removed only in the context of a same-owner `JournalEntry`. Stored attachment references must remain access-controlled and checksummed.

**UD-007 — No domain secrets.** Plaintext passwords, refresh-token secrets, provider credentials, email credentials, Telegram credentials/tokens, API keys, and equivalent secrets must never be stored in domain records. Non-reversible fingerprints or references to approved secret storage may be retained where required.

**UD-008 — Ownership-preserving archive.** Archiving a watchlist, portfolio, alert, journal entry, or risk profile must not remove its owner identity or required historical children.

## G. AI

**AI-001 — No invented analytical facts.** AI must not create, estimate, fill in, or alter market data, indicator values, Technical Score values, patterns, support/resistance, market structure, Elliott scenarios, signals, or trade plans.

**AI-002 — Deterministic evidence only.** Every `ExplanationRequest` must reference a frozen snapshot of stored deterministic evidence. Every analytical factual claim in an `ExplanationResult` must be supportable by those references.

**AI-003 — Separate output.** Explanation text must be stored as `ExplanationResult`, separately from deterministic evidence and analytical truth. It must not be written back into fields owned by Market Data, Technical Analysis, Strategies, Signals, Backtesting, or Market Intelligence.

**AI-004 — Failure independence.** An AI timeout, refusal, invalid output, provider failure, or validation failure must not block, change, invalidate, or roll back the deterministic analysis being explained.

**AI-005 — Required disclaimer.** Every available explanation must include an investment-risk disclaimer stating that the output is decision support, not a guarantee, and that investment decisions carry risk.

**AI-006 — No AI price forecasts.** An explanation must not generate future price targets, paths, or forecasts. It may restate a deterministic TradePlan target only when clearly attributed to the stored plan and not presented as an AI prediction.

**AI-007 — Evidence and model traceability.** Each result must retain its request, evidence citations, generation timestamp, and model/provider configuration reference sufficient for audit, subject to the prohibition on storing credentials.

## H. Audit

**AU-001 — Audited security changes.** User activation/disablement, role assignment changes, refresh-token revocation/security events, and authorization failures designated important by policy must create an `AuditLog` record with actor, time, action, subject, and outcome.

**AU-002 — Audited configuration and strategy changes.** Important changes to provider/import configuration, active calculation definitions, strategy metadata, StrategyVersion publication/retirement, alert rules, and risk profiles must be audited without recording secrets.

**AU-003 — Audited portfolio changes.** Portfolio creation/archive and transaction creation, correction, or reversal must be audited with owner, actor, affected record, time, and outcome.

**AU-004 — Audited alert activity.** Alert-rule activation, pause, retirement, and important delivery-configuration changes must be audited. Evaluation and delivery histories remain separately traceable in their own domain records.

**AU-005 — Append-only audit.** An `AuditLog` record must never be updated or deleted through normal domain behavior. A correction or clarification is a new audit record linked to the earlier record.

**AU-006 — Audit safety.** Audit details must contain sufficient before/after or event context for accountability while excluding plaintext credentials, tokens, attachment content, and other prohibited secrets.

**AU-007 — System actor traceability.** Scheduled and background actions must identify a system actor and correlation context; they must not be falsely attributed to a user.

## Assumptions

- Timeframes are canonical domain values, and version 1 backtesting accepts only the daily timeframe even though analysis and market-data entities can represent other supported timeframes.
- Price and quantity precision follows instrument and exchange conventions; the domain requires exact financial arithmetic but does not prescribe a storage numeric type.
- “Published” means available as a durable analytical fact to downstream consumers, regardless of the internal workflow used to reach that state.
- Shared analytical outputs may be produced once and reused across users, while any user-specific execution context and resulting user-owned records retain their owner.
- Confidence is a bounded, documented measure defined by the producing calculation; it is not a probability of profit unless a definition explicitly and validly establishes that meaning.
- Historical corrections preserve supersession lineage so consumers can select an effective version without erasing what earlier computations used.

## Open implementation questions

- What canonical identifier format and timestamp precision will be used consistently across modules?
- How will canonical timeframe values, exchange session timestamps, and timezone conversion be represented at module boundaries?
- What numeric precision and rounding policies will be used for prices, quantities, ratios, fees, taxes, valuations, and indicator outputs?
- What canonical serialization and field ordering will be used when calculating configuration and evidence hashes?
- How will immutable evidence references and supersession chains be represented efficiently while preserving module boundaries?
- What storage partitioning, indexing, and retention mechanisms will meet expected market-data and analytical-query volumes?
- How will transaction isolation and idempotency keys be applied to ingestion, background evaluations, and notification retries?
- How will deterministic calculation implementation versions be assigned and included in cached-result invalidation?
- How will point-in-time corporate-action availability and adjustment-policy versions be represented for historical backtests?
- What validation tolerances will be defined for floating-point analytical calculations, and where will exact decimal arithmetic be required?
- How will attachment storage references, checksums, size limits, and malware-validation states integrate with journal ownership checks?
- What structured redaction mechanism will ensure audit logs, diagnostics, and notification provider responses never persist secrets?
