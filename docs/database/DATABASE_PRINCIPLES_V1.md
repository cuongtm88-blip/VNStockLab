# VNStockLab Database Principles V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Purpose

This document freezes the database conventions for VNStockLab version 1. It translates the frozen modular-monolith and Domain Model v1 contracts into PostgreSQL persistence rules without defining executable SQL, ORM mappings, or migrations.

## Authority and storage roles

PostgreSQL is the primary persistent database and authoritative system of record. All durable identity, reference, market, analytical, strategy, user-owned, operational, and audit records are committed there. The application uses one PostgreSQL application schema in version 1; module ownership is expressed by table names and application boundaries rather than separate PostgreSQL schemas.

Redis is not a system of record. It may hold caches, locks, temporary task state, queues, and short-lived coordination data. Loss or eviction of Redis data must not destroy an authoritative fact; durable task outcomes and state transitions must be recoverable from PostgreSQL.

Secrets and credentials—including plaintext passwords, raw refresh tokens, provider credentials, mail credentials, Telegram tokens, and API keys—are never stored in ordinary domain tables. Only password hashes, non-reversible token hashes, safe fingerprints, or references to approved secret storage may be persisted where the domain requires them.

## Naming conventions

- PostgreSQL identifiers use `snake_case`.
- Table names use plural `snake_case`; for example, `price_bars`, `strategy_versions`, and `portfolio_risk_snapshots`.
- Column names use `snake_case`; for example, `market_data_cutoff_at` and `configuration_hash`.
- Primary-key columns use `<entity>_id`; for example, `instrument_id` on `instruments` and `signal_id` on `signals`.
- Foreign-key columns use the referenced primary-key name; for example, `signals.strategy_version_id` references `strategy_versions.strategy_version_id`.
- Boolean columns use affirmative names such as `is_active`. Timestamps use an `_at` suffix and dates use an `_date` suffix. Hashes use `_hash`; version strings use `_version`.
- Constraint and index names should be deterministic and identify their table and columns; migration tooling may shorten names only to meet PostgreSQL limits.

## Keys and relationships

- Primary keys use `uuid` unless a documented technical reason requires another type. UUIDs are application- or database-generated and have no business meaning.
- Natural identities are protected by unique constraints in addition to surrogate primary keys.
- Every foreign key states an explicit delete behavior. Reference and historical relationships normally restrict deletion; aggregate children may cascade only where deletion is itself permitted and cannot erase required history.
- Foreign-key columns used in joins, ownership checks, or delete validation are indexed unless already covered by a useful composite index.
- Many-to-many relationships use explicit junction tables. `user_roles` supports future multiple roles per user without changing the frozen `User` or `Role` entities.

## Time and timestamps

- All application timestamps use `timestamptz` and are stored in UTC.
- Trading dates use `date` where a time is not meaningful.
- Market timestamps preserve exchange-time semantics while being stored as UTC instants. The applicable exchange time zone and calendar remain traceable.
- Mutable records use `created_at` and `updated_at`. Database and application rules must advance `updated_at` on an accepted mutation.
- Immutable records use `created_at`, `recorded_at`, or a domain-specific event timestamp and are never silently updated.
- Time-zone identifiers use IANA names. Rendering in exchange or user-local time is an application concern; ambiguous local timestamps must not be persisted.

## Exact numeric conventions

- Prices and financial values use `numeric`, never floating-point types and never PostgreSQL `money`.
- General price and monetary columns use `numeric(24,8)`. This supports Vietnamese-market values while retaining room for calculated and foreign-currency values. Currency is always explicit at the owning record or unambiguously inherited from it. Every persisted currency code uses ISO-4217, such as `VND`, `USD`, or `JPY`; arbitrary currency strings are prohibited.
- Quantities and whole-unit volumes use `bigint` when fractions are impossible; fractional quantities use `numeric(28,8)`. Trading value and turnover use `numeric(28,8)`.
- Ratios, scores, confidence, weights, percentages, adjustment factors, fees, taxes, slippage, indicator outputs, and risk measures use explicitly declared precision. The default analytical precision is `numeric(24,10)`; bounded scores and confidence use `numeric(7,4)` with explicit checks; percentages and rates use `numeric(18,10)`.
- Counts use `integer` or `bigint` according to expected scale. Ordering and small bounded categories may use `smallint`.
- Every calculation defines scale, rounding mode, and unit at its domain boundary. A wider intermediate precision may be used, but persisted output conforms to its declared type.

## Enumerations and structured data

Version 1 stores lifecycle states and domain classifications as constrained `varchar`, not PostgreSQL enum types. Check constraints freeze accepted values where the set is stable; versioned definitions or reference tables are used when values require metadata or controlled evolution. This keeps migrations reversible and avoids hiding domain meaning in application-only constants.

Persisted timeframes use the canonical vocabulary `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`, and `1M`. Consumers may render friendly labels, but must translate them to these exact, case-sensitive values before persistence; in particular, `1m` means one minute and `1M` means one month.

`jsonb` is allowed only for variable structured metadata, evidence payloads, lossless provider payloads, safe diagnostics, and versioned configurations. Every JSONB column has a documented shape/version or an adjacent version field where interpretation may change. JSONB must not replace stable relational columns, ownership keys, important query keys, monetary columns, timestamps, lifecycle state, or integrity-enforced relationships. Frequently filtered JSON paths require measured justification before indexing.

## Mutation, deletion, and history

- Mutable definitions and user organization records may be updated under optimistic concurrency and audit rules.
- Instrument identities are permanent and are never physically deleted because historical market data, signals, backtests, and portfolios depend on them. Their conceptual lifecycle is constrained to `active`, `suspended`, `delisted`, or `merged`; lifecycle changes never invalidate historical references.
- Raw provider data, effective historical facts, published analytical evidence, published strategy versions and contents, published signals and plans, completed execution results, portfolio transactions, terminal alert evaluations and delivery attempts, AI inputs/results, and audit logs are immutable.
- Price bars are append-only. Corrections create a new import batch and superseding evidence with explicit lineage; neither incorrect imported bars nor raw provider data are silently rewritten. Normalized and adjusted representations remain distinct, and historical provider data remains traceable.
- Soft deletion is not a universal default. User-facing roots that need removal semantics use explicit lifecycle states such as `archived`, `retired`, or `disabled`, with timestamps where useful. Immutable history is not hidden by an untraceable `deleted_at` flag.
- Physical deletion is limited to approved retention processing, expired security material, failed temporary intake with no historical obligation, and user erasure after dependency and audit review. It must not silently rewrite financial or analytical history.

## Ownership, isolation, and auditability

Every user-owned aggregate root carries a required `user_id`; high-value children also carry `user_id` where this materially strengthens row-level isolation and composite ownership checks. All reads, writes, jobs, exports, attachments, evaluations, and deliveries enforce that owner. Cross-user references are prohibited unless the target is frozen shared data. Database foreign keys and unique constraints reinforce ownership where practical; application authorization remains mandatory.

Important security, configuration, strategy, portfolio, alert, and ownership changes emit append-only `audit_logs`. Audit payloads contain safe structured context, actor or system identity, affected owner, correlation identity, action, subject, and outcome, but no secrets. Evidence records retain definition versions, configuration hashes, point-in-time cutoffs, provider/batch lineage, and input ranges sufficient for reproducibility.

## Migrations

- Schema evolution is performed only through reviewed, forward migrations in delivery work outside this specification.
- Migrations are deterministic, transactional where PostgreSQL permits, backward-compatible during rolling application changes, and independently reversible by a corrective forward migration.
- Large backfills are resumable, observable, idempotent, and separated from blocking definition changes.
- Constraints are introduced with validation plans appropriate to table size. Destructive changes require retention, backup, and rollback approval.
- No migration may reinterpret or silently rewrite historical financial or analytical facts. Configuration and calculation semantic changes require new versions.

## Transactions and concurrency

Transaction boundaries follow aggregate invariants: user-role assignment, import finalization, strategy publication, signal publication with evidence and plan, portfolio transaction correction, and alert evaluation outcome are committed atomically at their required consistency boundary. Long calculations and provider/network calls occur outside open database transactions; their durable start and terminal outcomes use short transactions.

The default isolation level is PostgreSQL `READ COMMITTED`. Operations requiring a stable multi-row decision use explicit locking, a higher isolation level, or compare-and-swap version checks. Mutable roots use optimistic concurrency through `updated_at` or a lock-version value. Idempotency keys and unique constraints protect ingestion, task completion, scan results, alert evaluation/deduplication, and notification attempts. Locks are narrowly scoped and acquired in stable order. Append-only facts never use last-write-wins behavior.

Backtests and point-in-time analytics freeze their configuration and dataset cutoff before execution. Every `BacktestRun` preserves its `StrategyVersion`, indicator implementation version, dataset cutoff, configuration hash, and data snapshot identity or equivalent reproducibility reference. No transaction or cache may expose later data to an earlier decision context. Redis locks improve coordination only; PostgreSQL uniqueness and state transitions preserve correctness.

AI explanation modules consume only grounded analytical records: `IndicatorResult`, `Signal`, `SignalEvidence`, and `TradePlan`. AI must not independently derive analytical truth from raw `PriceBar` records; generated prose remains separate from deterministic analytical truth.
