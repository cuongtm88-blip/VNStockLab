# VNStockLab Indexing and Partitioning V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Indexing principles

Every primary key and unique constraint has its PostgreSQL-backed index. Foreign keys receive supporting indexes when not already the leading columns of another useful index. User-owned query paths lead with `user_id` or an owned aggregate key. Time-series indexes normally place equality predicates first and time last in descending order. Low-cardinality standalone indexes are avoided unless partial. Include columns may support a measured index-only query but are not part of initial correctness requirements.

Composite ordering follows the query: equality/tenant columns, then range or ordering columns, then a stable tie-breaker. An index for `(instrument_id,timeframe,bar_at desc)` does not automatically justify its reverse. Unique and primary indexes are reused rather than duplicated. JSONB GIN indexes, expression indexes, and covering indexes require observed query evidence. Write amplification, index size, cache residency, and vacuum cost are considered with read latency.

Foreign-key indexes protect join and parent-delete validation paths. For high-value owned records, indexes such as `(user_id,status,event_at desc)` enforce fast isolation before filtering. Exact index definitions are finalized and measured in migrations; this document defines initial shapes.

## Initial recommendations

| Table | Initial indexes beyond PK/unique constraints | Query served |
| --- | --- | --- |
| `price_bars` | `(instrument_id,timeframe,bar_at desc)`; `(import_batch_id)`; `(data_provider_id,bar_at desc)`; partial series index for published/effective rows if superseded rows are frequent | chart/range reads, latest bar, lineage |
| `adjusted_price_bars` | `(instrument_id,timeframe,adjustment_policy,bar_at desc)`; `(price_bar_id)`; `(import_batch_id)` | adjusted series and source lineage |
| `indicator_results` | `(instrument_id,timeframe,indicator_definition_id,as_of_at desc)`; `(indicator_definition_id,configuration_hash)`; optional partial published index | latest/range analytical output and reproducibility |
| `pattern_detections` | `(instrument_id,timeframe,as_of_at desc,pattern_definition_id)`; `(classification,as_of_at desc)` limited to published detections | instrument evidence and recent pattern screens |
| `signals` | `(instrument_id,timeframe,generated_at desc)`; `(strategy_version_id,generated_at desc)`; `(user_id,status,generated_at desc)`; partial `(generated_at desc,score desc)` for current published signals | charts, strategy history, owned inbox, market screen |
| `scan_results` | `(scan_run_id,rank,instrument_id)`; `(scan_run_id,classification,score desc)`; `(instrument_id,evaluated_at desc)` | ranked run output, class filters, instrument history |
| `backtest_equity_points` | unique `(backtest_run_id,point_at)`; optional include of equity/drawdown after measurement | efficient ordered equity curve retrieval |
| `portfolio_transactions` | `(portfolio_id,effective_at,portfolio_transaction_id)`; `(user_id,effective_at desc)`; `(portfolio_id,instrument_id,effective_at)` | ledger replay, owned history, instrument lots |
| `portfolio_positions` | `(portfolio_id,instrument_id,as_of_at desc)`; `(user_id,as_of_at desc)`; partial latest-materialization index only if an explicit current marker is introduced by a future schema revision | as-of and latest holdings |
| `alert_rules` | `(user_id,status,last_evaluated_at)`; partial `(last_evaluated_at,alert_rule_id)` where status is active; `(strategy_version_id)` | owner management and due-rule scheduling |
| `notification_deliveries` | `(user_id,status,queued_at)`; `(alert_evaluation_id,channel,attempt_number)`; partial `(queued_at,notification_delivery_id)` for queued/retryable rows | outbox processing, retry, delivery history |
| `audit_logs` | `(owner_user_id,occurred_at desc)`; `(actor_user_id,occurred_at desc)`; `(subject_type,subject_id,occurred_at desc)`; `(correlation_id)` | ownership, actor, subject, and trace investigations |

The same series principle applies to `raw_market_records`, market-intelligence snapshots, support/resistance levels, market-structure snapshots, and Elliott scenarios. Partial indexes must use stable predicates such as terminal/current lifecycle values, not volatile time expressions.

## Query-pattern guidance

Scanner screens first identify one `scan_run_id`, then order/filter results by classification, score, or rank. They must not scan all historical runs. Latest-record queries use equality on subject/instrument/timeframe/method followed by `ORDER BY ..._at DESC LIMIT 1`; callers must also specify representation, policy, definition, or configuration identity so “latest” is semantically unambiguous.

Backtest retrieval leads with `backtest_run_id`: trades by `trade_number`, equity by `point_at`, metrics by name/version. Portfolio retrieval leads with `user_id` or a previously authorized `portfolio_id`, then effective/as-of time. Alert scheduling uses a small partial active-rule index; evaluation and delivery history lead with owner/rule/evaluation. No index is a substitute for ownership authorization.

## Measurement policy

Representative production-shaped queries must be measured with `EXPLAIN (ANALYZE, BUFFERS)` in a safe non-production or controlled environment. Plans, row estimates, execution time, buffer hits/reads, sort spills, and index size are recorded before and after adding an index. PostgreSQL statistics are refreshed first. Slow-query evidence and `pg_stat_statements` guide tuning when available. Redundant-prefix, unused, and low-value indexes are reviewed periodically; removal requires workload evidence and a migration.

## Partitioning decision

Table partitioning is not required on day one. The initial local-development release uses ordinary tables to keep constraints, uniqueness, migrations, vacuum behavior, and debugging straightforward. High-volume tables remain partition-ready by carrying a required, immutable time key and by keeping uniqueness/query patterns compatible with a future range key.

Candidates for later range partitioning are:

- `raw_market_records` by `received_at`;
- `price_bars` and `adjusted_price_bars` by `bar_at`;
- `indicator_results` by `as_of_at`;
- `pattern_detections` by `as_of_at`;
- `scan_results` by `evaluated_at`;
- `signals` by `generated_at`;
- `backtest_equity_points` by `point_at`; and
- `audit_logs` by `occurred_at`.

Partitioning is introduced only after measurement shows at least one sustained trigger: approximately 100 million rows in a table; total index size exceeds practical memory/cache or 100 GB; routine vacuum/analyze or index maintenance exceeds the agreed maintenance window; retention deletion causes unacceptable bloat or locks; p95 representative time-range queries regress by at least 2× from their accepted baseline despite correct indexes/statistics; or operational restore/archive objectives cannot be met with an ordinary table. Thresholds are planning signals, not automatic commands; the chosen partition interval follows data arrival, query ranges, and retention units.

Before partitioning, the team validates partition pruning, global logical uniqueness strategy, foreign-key behavior, late arrivals, correction/supersession routing, default-partition monitoring, retention detach/archive workflow, and migration/rollback. Partitioning must preserve immutable evidence identity and cannot justify deleting or rewriting history.
