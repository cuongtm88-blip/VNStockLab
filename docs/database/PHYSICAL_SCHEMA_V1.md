# VNStockLab Physical Schema V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16
**Target:** PostgreSQL

## Reading this catalog

Version 1 uses one application schema (normally `public`) with modular plural table names. Separate PostgreSQL schemas add operational complexity without a v1 isolation requirement. Each table below is an implementation contract, not executable SQL.

Notation: `R` means required, `N` nullable; `D:` gives a default. Every UUID primary key is required and generated with the platform UUID policy. `created_at` defaults to the transaction timestamp. Mutable tables also have required `updated_at`, initially equal to `created_at`. All timestamps are `timestamptz`; all persisted instants are UTC. `price`/money means `numeric(24,8)`, analytical value means `numeric(24,10)`, bounded score/confidence means `numeric(7,4)`, rate means `numeric(18,10)`, and fractional quantity means `numeric(28,8)`. Currency codes are `varchar(3)` constrained to ISO-4217 values such as `VND`, `USD`, and `JPY`; arbitrary strings are invalid. Every persisted timeframe is one of the exact, case-sensitive canonical values `{1m,5m,15m,30m,1h,4h,1d,1w,1M}`. Consumers may display friendly labels but must persist only these values. Statuses and classifications are constrained `varchar`; values listed in braces are check-constraint values. JSONB shapes are versioned application contracts. Delete behavior is `RESTRICT` unless explicitly stated.

## Identity

### `users`

- Purpose/PK: authenticated identity and ownership boundary; `user_id uuid`.
- Columns: `email varchar(320) R`, `normalized_email varchar(320) R`, `display_name varchar(160) R`, `password_hash text R`, `status varchar(24) R D:'active'`, `is_active boolean R D:true`, `created_at timestamptz R`, `updated_at timestamptz R`, `disabled_at timestamptz N`.
- Integrity: unique `normalized_email`; status in `{invited,active,disabled}`; normalized email must equal the application canonicalization result; disabled state requires `disabled_at`.
- Mutation/index/owner/retention: mutable security/profile state under audit; unique email index plus `(status)` where measured; self-owned identity; identity/audit dependencies retained, erasure policy applies to personal fields.

### `roles`

- Purpose/PK: shared authorization role; `role_id uuid`.
- Columns: `name varchar(80) R`, `description text N`, `permissions jsonb R D:{}`, `is_active boolean R D:true`, `created_at timestamptz R`, `updated_at timestamptz R`.
- Integrity: unique case-normalized `name`; permissions must be a JSON object.
- Mutation/index/owner/retention: mutable under audit, retirement preferred to deletion; unique name index; shared; permanent reference.

### `user_roles` (storage junction)

- Purpose/PK: many-to-many membership; composite primary key `(user_id, role_id)`.
- Columns/FKs: `user_id uuid R` → `users`; `role_id uuid R` → `roles`; `assigned_at timestamptz R`; `assigned_by_user_id uuid N` → `users`.
- Integrity: primary key prevents duplicates.
- Mutation/index/owner/retention: assignment insert/delete only with audit; index `(role_id,user_id)`; inherits user ownership; membership history remains in audit logs.

### `refresh_tokens`

- Purpose/PK: revocable refresh session; `refresh_token_id uuid`.
- Columns/FKs: `user_id uuid R` → `users`; `token_hash varchar(128) R`; `issued_at timestamptz R`; `expires_at timestamptz R`; `revoked_at timestamptz N`; `rotated_to_refresh_token_id uuid N` → same table; `client_context jsonb N`; `created_at timestamptz R`.
- Integrity: unique `token_hash`; `expires_at > issued_at`; `revoked_at >= issued_at`; no raw token; a token cannot rotate to itself.
- Mutation/index/owner/retention: issuance immutable, revocation/rotation fields controlled; `(user_id,expires_at)`, partial `(user_id)` where `revoked_at` is null; user-owned; delete after configurable expired/revoked security-retention window.

### `audit_logs`

- Purpose/PK: append-only action fact; `audit_log_id uuid`.
- Columns/FKs: `occurred_at timestamptz R`, `actor_user_id uuid N` → `users`, `system_actor varchar(120) N`, `owner_user_id uuid N` → `users`, `action varchar(120) R`, `subject_type varchar(80) R`, `subject_id uuid N`, `correlation_id uuid R`, `outcome varchar(24) R`, `change_summary jsonb N`, `recorded_at timestamptz R`.
- Integrity: exactly one of actor user/system actor is normally present; outcome in `{succeeded,failed,denied}`; details exclude secrets.
- Mutation/index/owner/retention: append-only; `(owner_user_id,occurred_at desc)`, `(actor_user_id,occurred_at desc)`, `(subject_type,subject_id,occurred_at desc)`, `(correlation_id)`; governance record with owner context; permanent or approved archival policy.

## Instruments

### `exchanges`

- Purpose/PK: venue reference; `exchange_id uuid`.
- Columns: `code varchar(20) R`, `name varchar(160) R`, `timezone varchar(64) R`, `currency varchar(3) R`, `is_active boolean R D:true`, timestamps.
- Integrity: unique `code`; nonblank values and valid application-known IANA timezone/currency.
- Mutation/index/owner/retention: mutable under audit; unique code; shared; permanent.

### `sectors`

- Purpose/PK: versioned sector reference; `sector_id uuid`.
- Columns: `classification_scheme varchar(80) R`, `scheme_version varchar(40) R`, `code varchar(40) R`, `name varchar(160) R`, `effective_from date R`, `effective_to date N`, `status varchar(24) R`, `created_at timestamptz R`.
- Integrity: unique `(classification_scheme,scheme_version,code)`; `effective_to >= effective_from`; status `{active,retired}`.
- Mutation/index/owner/retention: effective version immutable, correction adds version; effective-date lookup index; shared; permanent reference.

### `industries`

- Purpose/PK: versioned industry reference; `industry_id uuid`.
- Columns/FKs: `sector_id uuid R` → `sectors`; scheme/version/code/name/effective dates/status as for sectors; `created_at`.
- Integrity: unique `(classification_scheme,scheme_version,code)`; valid interval.
- Mutation/index/owner/retention: effective version immutable; `(sector_id,status)`; shared; permanent.

### `instruments`

- Purpose/PK: canonical listed instrument; `instrument_id uuid`.
- Columns/FKs: `exchange_id uuid R` → `exchanges`; `sector_id uuid N` → `sectors`; `industry_id uuid N` → `industries`; `symbol varchar(40) R`, `name varchar(240) R`, `instrument_type varchar(40) R`, `currency varchar(3) R`, `listing_date date N`, `delisting_date date N`, `trading_status varchar(24) R`, timestamps.
- Integrity: unique `(exchange_id,symbol,listing_date)` with null listing date normalized by implementation; delisting not before listing; industry must belong to sector (enforced by service or composite reference); `trading_status` is constrained to `{active,suspended,delisted,merged}`.
- Mutation/index/owner/retention: mutable lifecycle/reference; `(exchange_id,trading_status)`, `(sector_id,trading_status)`, `(industry_id,trading_status)`; shared; permanent identity that is never physically deleted because market data, signals, backtests, and portfolios depend on it. Lifecycle changes preserve every historical reference.

### `instrument_aliases`

- Purpose/PK: effective alternate identity; `instrument_alias_id uuid`.
- Columns/FKs: `instrument_id uuid R` → `instruments`; `data_provider_id uuid N` → `data_providers`; `exchange_id uuid N` → `exchanges`; `alias_type varchar(40) R`, `alias_value varchar(240) R`, `effective_from date R`, `effective_to date N`, `source varchar(240) R`, `status varchar(24) R`, `supersedes_instrument_alias_id uuid N` → same; `created_at`.
- Integrity: valid interval; one context type as documented; exclusion/no-overlap enforcement prevents the same normalized alias/context/effective interval mapping to conflicting instruments; no self-supersession.
- Mutation/index/owner/retention: immutable fact; context/value/effective lookup and `(instrument_id,effective_from desc)`; shared; permanent.

### `indices`

- Purpose/PK: market-index identity; `index_id uuid`.
- Columns/FKs: `exchange_id uuid N` → `exchanges`; `code varchar(40) R`, `name varchar(160) R`, `market_context varchar(80) R`, `currency varchar(3) R`, `methodology_reference text N`, `is_active boolean R D:true`, timestamps.
- Integrity: unique `(market_context,code)`.
- Mutation/index/owner/retention: mutable reference; `(exchange_id,is_active)`; shared; permanent.

### `index_constituents`

- Purpose/PK: effective index membership; `index_constituent_id uuid`.
- Columns/FKs: `index_id uuid R` → `indices`; `instrument_id uuid R` → `instruments`; `effective_from date R`, `effective_to date N`, `weight numeric(18,10) N`, `source varchar(240) R`, `supersedes_index_constituent_id uuid N` → same; `created_at`.
- Integrity: unique `(index_id,instrument_id,effective_from)`; valid interval; weight `>=0`; overlapping effective membership prohibited.
- Mutation/index/owner/retention: immutable; `(index_id,effective_from,effective_to)`, `(instrument_id,effective_from desc)`; shared; permanent.

## Market data

### `data_providers`

- Purpose/PK: provider reference; `data_provider_id uuid`.
- Columns: `source_code varchar(40) R`, `name varchar(160) R`, `data_types jsonb R`, `timezone_conventions jsonb R`, `status varchar(24) R`, timestamps.
- Integrity: unique `source_code`; JSON values are objects/arrays under versioned contracts; status `{active,suspended,retired}`.
- Mutation/index/owner/retention: mutable under audit; unique source code; shared; permanent.

### `import_batches`

- Purpose/PK: one traceable ingestion attempt; `import_batch_id uuid`.
- Columns/FKs: `data_provider_id uuid R` → `data_providers`; `requested_from_at timestamptz N`, `requested_to_at timestamptz N`, `covered_from_at timestamptz N`, `covered_to_at timestamptz N`, `ingestion_mode varchar(40) R`, `source_reference text N`, `source_checksum varchar(128) N`, `started_at timestamptz R`, `completed_at timestamptz N`, `status varchar(32) R`, `received_count bigint R D:0`, `parsed_count bigint R D:0`, `rejected_count bigint R D:0`, `diagnostics jsonb N`, `created_at`.
- Integrity: counts non-negative; ranges ordered; completion required only for terminal status; status `{pending,running,completed,partially_completed,failed,cancelled}`.
- Mutation/index/owner/retention: controlled until terminal, then immutable; `(data_provider_id,started_at desc)`, `(status,started_at)`; shared; retain with source lineage.

### `raw_market_records`

- Purpose/PK: lossless received record; `raw_market_record_id uuid`.
- Columns/FKs: `data_provider_id uuid R` → providers; `import_batch_id uuid R` → batches; `instrument_id uuid N` → instruments; `source_record_key varchar(240) N`, `source_timestamp timestamptz N`, `received_at timestamptz R`, `payload jsonb N`, `payload_reference text N`, `payload_schema_version varchar(40) R`, `checksum varchar(128) R`, `parse_status varchar(24) R`, `supersedes_raw_market_record_id uuid N` → same; `created_at`.
- Integrity: exactly one or both of payload/payload reference must preserve lossless content; unique `(data_provider_id,source_record_key,checksum)` when key exists; no self-supersession.
- Mutation/index/owner/retention: immutable; `(import_batch_id)`, `(instrument_id,source_timestamp desc)`, `(data_provider_id,received_at desc)`; shared; raw-import retention/archival policy, never silent overwrite.

### `trading_calendars`

- Purpose/PK: effective daily exchange session; `trading_calendar_id uuid`.
- Columns/FKs: `exchange_id uuid R` → exchanges; `session_date date R`, `open_at timestamptz N`, `close_at timestamptz N`, `session_type varchar(24) R`, `closure_reason text N`, `source varchar(240) R`, `effective_version varchar(40) R`, `supersedes_trading_calendar_id uuid N` → same; `created_at`.
- Integrity: unique `(exchange_id,session_date,effective_version)`; close after open when open; closed session has no required times; session type constrained.
- Mutation/index/owner/retention: immutable once effective; `(exchange_id,session_date)`; shared; permanent.

### `corporate_actions`

- Purpose/PK: adjustment event/evidence; `corporate_action_id uuid`.
- Columns/FKs: instrument/provider required; import batch nullable; `action_type varchar(40) R`, `announcement_date date N`, `ex_date date R`, `effective_date date R`, `ratio numeric(24,10) N`, `amount numeric(24,8) N`, `currency varchar(3) N`, `evidence jsonb R`, `status varchar(24) R`, `supersedes_corporate_action_id uuid N`, `created_at`.
- Integrity: ratio/amount non-negative when supplied; amount requires currency; no self-supersession; action-type-specific validation.
- Mutation/index/owner/retention: immutable event version; `(instrument_id,ex_date,action_type)`, `(data_provider_id,ex_date)`; shared; permanent market history.

### `price_bars`

- Purpose/PK: normalized, unadjusted bar; `price_bar_id uuid`.
- Columns/FKs: instrument/provider/import batch required; `timeframe varchar(16) R`, `bar_at timestamptz R`, `representation varchar(32) R D:'normalized'`, OHLC `numeric(24,8) R`, `volume bigint R`, `trading_value numeric(28,8) N`, `normalization_version varchar(40) R`, `provider_policy varchar(80) R`, `source_evidence jsonb R`, `ingested_at timestamptz R`, `status varchar(24) R`, `supersedes_price_bar_id uuid N`, `created_at`.
- Integrity: unique `(instrument_id,timeframe,bar_at,representation,normalization_version,data_provider_id,provider_policy)`; high ≥ low/open/close, low ≤ open/close, prices non-negative, volume/value non-negative; no self-supersession.
- Mutation/index/owner/retention: append-only; series `(instrument_id,timeframe,bar_at desc)` plus batch/provider lineage indexes; shared; normalized market data retained/archived by policy. An incorrect import is corrected by a new import batch and a new row linked through `supersedes_price_bar_id` and source evidence, never by silently rewriting the historical bar; provider history remains traceable.

### `adjusted_price_bars`

- Purpose/PK: separate adjusted representation; `adjusted_price_bar_id uuid`.
- Columns/FKs: `price_bar_id uuid R` → price bars; instrument/provider/import batch required; timeframe/bar time required; adjusted OHLC required, `volume bigint R`, `trading_value numeric(28,8) N`, `adjustment_policy varchar(80) R`, `adjustment_version varchar(40) R`, `price_factor numeric(24,10) R`, `volume_factor numeric(24,10) R`, `action_evidence jsonb R`, `ingested_at`, `status`, optional supersedes FK, `created_at`.
- Integrity: unique `(instrument_id,timeframe,bar_at,adjustment_policy,adjustment_version,data_provider_id)`; valid OHLC/non-negative volumes and positive factors; source bar identity must match instrument/timeframe/time.
- Mutation/index/owner/retention: published row immutable; series index and `(price_bar_id)`; shared rebuildable derivation; adjusted-data retention with evidence/version.

### `data_quality_issues`

- Purpose/PK: preserved finding; `data_quality_issue_id uuid`.
- Columns/FKs: provider/batch required, instrument/raw record/price bar nullable; `entity_type varchar(80) R`, `entity_id uuid N`, `affected_range jsonb N`, `rule_code varchar(80) R`, `severity varchar(16) R`, `details jsonb R`, `detected_at timestamptz R`, `status varchar(24) R`, `resolved_at timestamptz N`, `resolution_details jsonb N`, `supersedes_data_quality_issue_id uuid N`, timestamps.
- Integrity: severity `{info,warning,error,critical}`; status `{open,acknowledged,resolved,accepted}`; resolution timestamps/status coherent.
- Mutation/index/owner/retention: finding immutable; resolution fields controlled; `(status,severity,detected_at)`, batch/instrument indexes; shared; retain with affected lineage.

## Technical analysis

### `indicator_definitions` and `pattern_definitions`

- Purpose/PK: versioned analytical meanings; respectively `indicator_definition_id uuid` and `pattern_definition_id uuid`.
- Columns: both have `name varchar(120) R`, `version varchar(40) R`, `input_requirements jsonb R`, `parameter_schema jsonb R`, `implementation_version varchar(80) R`, `status varchar(24) R`, `published_at timestamptz N`, `created_at`; indicators add `parameter_defaults jsonb R`, `warm_up_rule jsonb R`, `output_schema jsonb R`; patterns add `pattern_family varchar(80) R`.
- Integrity: unique `(name,version)`; status `{draft,active,retired}`; active requires publication; schema payloads objects.
- Mutation/index/owner/retention: draft mutable, active immutable; `(status,name)`; shared; permanent versioned configuration.

### `indicator_results`

- Purpose/PK: deterministic output evidence; `indicator_result_id uuid`.
- Columns/FKs: definition/instrument required; `timeframe varchar(16) R`, `as_of_at timestamptz R`, `input_representation varchar(40) R`, `input_from_at timestamptz R`, `input_to_at timestamptz R`, `parameter_snapshot jsonb R`, `definition_version varchar(40) R`, `implementation_version varchar(80) R`, `configuration_hash varchar(128) R`, `input_evidence jsonb R`, `result_payload jsonb R`, `calculated_at timestamptz R`, `status varchar(24) R`, `created_at`.
- Integrity: unique `(indicator_definition_id,instrument_id,timeframe,as_of_at,input_representation,configuration_hash,input_from_at,input_to_at)`; ordered input range ending no later than as-of; definition version matches referenced row; status constrained.
- Mutation/index/owner/retention: immutable; `(instrument_id,timeframe,as_of_at desc,indicator_definition_id)`, `(configuration_hash)`; shared derived evidence; retained while published evidence depends on it, otherwise rebuild policy.

### `pattern_detections`

- Purpose/PK: pattern outcome evidence; `pattern_detection_id uuid`.
- Columns/FKs: definition/instrument required; timeframe/as-of/input range/representation, `parameter_snapshot jsonb R`, `definition_version`, `implementation_version`, `configuration_hash`, `classification varchar(40) R`, `direction varchar(24) N`, `confidence numeric(7,4) N`, `evidence jsonb R`, `calculated_at`, `status`, `created_at`.
- Integrity: unique context/hash; input ends no later than as-of; confidence between 0 and 100; version matches definition.
- Mutation/index/owner/retention: immutable; `(instrument_id,timeframe,as_of_at desc,pattern_definition_id)`, `(classification,as_of_at desc)`; shared derived evidence; evidence retention.

### `support_resistance_levels`

- Purpose/PK: immutable level/zone snapshot; `support_resistance_level_id uuid`.
- Columns/FKs: instrument required; timeframe/as-of; `level_kind varchar(16) R`, `lower_price numeric(24,8) R`, `upper_price numeric(24,8) R`, `strength numeric(7,4) N`, `evidence_touches jsonb R`, input range, `method_version varchar(80) R`, `configuration_hash`, `invalidation_price numeric(24,8) N`, `expires_at timestamptz N`, `created_at`.
- Integrity: kind `{support,resistance}`; non-negative prices; upper ≥ lower; strength bounded; input range ≤ as-of.
- Mutation/index/owner/retention: immutable; `(instrument_id,timeframe,as_of_at desc,level_kind)`; shared derived evidence; retain dependencies or rebuild.

### `market_structure_snapshots`

- Purpose/PK: immutable as-of structure; `market_structure_snapshot_id uuid`.
- Columns/FKs: instrument required; timeframe/as-of; `structure_state varchar(40) R`, `pivots jsonb R`, `breaks jsonb R`, input range, `method_version`, `configuration_hash`, `confidence numeric(7,4) N`, `created_at`.
- Integrity: unique `(instrument_id,timeframe,as_of_at,method_version,configuration_hash)`; bounded confidence; no future input.
- Mutation/index/owner/retention: immutable; latest-series index; shared derived snapshot; rebuildable retention.

### `elliott_scenarios`

- Purpose/PK: evidence-backed scenario; `elliott_scenario_id uuid`.
- Columns/FKs: instrument required; timeframe/as-of; `scenario_class varchar(16) R`, `scenario_ordinal smallint R D:1`, `wave_labels jsonb R`, `pivots jsonb R`, `confidence numeric(7,4) R`, `invalidation_level numeric(24,8) R`, input range, `method_version`, `configuration_hash`, `evidence jsonb R`, `limitations text R`, `status varchar(24) R`, `created_at`.
- Integrity: unique context/class/ordinal/version/hash; class `{primary,alternative}`; confidence bounded; ordinal positive; no future input.
- Mutation/index/owner/retention: immutable scenario; `(instrument_id,timeframe,as_of_at desc,scenario_class)`; shared derived evidence; retained while referenced or rebuildable.

## Strategies, scanner, and signals

### `strategies`

- Purpose/PK: stable strategy family; `strategy_id uuid`.
- Columns/FKs: `owner_scope varchar(16) R`, `user_id uuid N` → users, `name varchar(160) R`, `description text N`, `status varchar(24) R`, timestamps.
- Integrity: scope `{shared,user}` and user required iff user scope; unique `(owner_scope,user_id,name)` with null-safe shared uniqueness.
- Mutation/index/owner/retention: mutable metadata under audit; `(user_id,status)`; scope-defined; permanent while versions/results exist.

### `strategy_versions`

- Purpose/PK: frozen executable version; `strategy_version_id uuid`.
- Columns/FKs: `strategy_id uuid R`; `version_label varchar(40) R`, `timeframe_scope jsonb R`, `configuration_hash varchar(128) R`, `implementation_version varchar(80) R`, `effective_at timestamptz N`, `published_at timestamptz N`, `status varchar(24) R`, `created_at`.
- Integrity: unique `(strategy_id,version_label)` and `(strategy_id,configuration_hash)`; published state requires timestamp; status `{draft,published,retired}`.
- Mutation/index/owner/retention: draft mutable; published version immutable including children; `(strategy_id,status,published_at desc)`; inherits strategy; permanent version.

### `strategy_parameters`, `strategy_rules`, and `strategy_risk_rules`

- Purpose/PK: immutable version contents; respective UUID PK named for each table; all require `strategy_version_id` FK and `created_at`.
- Columns: parameters: `name varchar(120)`, `value_type varchar(32)`, `value jsonb`, `default_value jsonb N`, `allowed_range jsonb N`, `unit varchar(40) N`, `display_order smallint R`; rules: `rule_type varchar(40)`, `specification jsonb`, `rule_order smallint`, `rule_group varchar(80) N`, `required_evidence jsonb`, `outcome_contribution numeric(7,4) N`; risk rules: `rule_type varchar(40)`, `parameters jsonb`, `priority smallint`, `applicability jsonb`, `limits jsonb` (all otherwise R).
- Integrity: parameters unique `(strategy_version_id,name)`; rules unique `(strategy_version_id,rule_order)`; risk rules unique `(strategy_version_id,priority,rule_type)`; orders/priorities non-negative; contribution bounded. JSON contracts are versioned by the parent configuration.
- Mutation/index/owner/retention: mutable only while parent draft, immutable after publication; parent FK indexes; inherit scope; permanent with version.

### `scan_definitions`

- Purpose/PK: reusable scan; `scan_definition_id uuid`.
- Columns/FKs: owner scope/user as strategies; `strategy_version_id uuid R`; `name`, `universe_policy jsonb R`, `timeframe`, `parameter_bindings jsonb R`, `schedule_config jsonb N`, `status`, timestamps.
- Integrity: user/scope coherence; unique scoped name; strategy version must be published to activate.
- Mutation/index/owner/retention: mutable/audited; `(user_id,status)`, `(strategy_version_id)`; scope-defined; retain while runs exist.

### `scan_runs`

- Purpose/PK: frozen scan execution; `scan_run_id uuid`.
- Columns/FKs: definition/strategy required; `owner_user_id uuid N`; `definition_snapshot jsonb R`, `universe_snapshot jsonb R`, `market_data_cutoff_at timestamptz R`, `configuration_hash`, `started_at`, `completed_at N`, `status`, `diagnostics jsonb N`, `created_at`.
- Integrity: terminal completion coherence; status constrained; owner matches definition scope.
- Mutation/index/owner/retention: context immutable after start, status controlled; `(scan_definition_id,started_at desc)`, `(owner_user_id,started_at desc)`, `(status,started_at)`; inherited; execution history retained.

### `scan_results`

- Purpose/PK: one evaluated instrument result; `scan_result_id uuid`.
- Columns/FKs: run/instrument/strategy required; `owner_user_id uuid N`; `evaluated_at`, `classification`, `score numeric(7,4) N`, `matched_rules jsonb R`, `evidence jsonb R`, `rank integer N`, `outcome varchar(24) R`, `signal_id uuid N` → signals, `created_at`.
- Integrity: unique `(scan_run_id,instrument_id)`; bounded score; rank positive; owner inherited.
- Mutation/index/owner/retention: immutable; `(scan_run_id,rank,instrument_id)`, `(instrument_id,evaluated_at desc)`; inherited; analytical evidence retention/rebuildable.

### `signals`

- Purpose/PK: published deterministic decision support; `signal_id uuid`.
- Columns/FKs: instrument/strategy required; `user_id uuid N`; `source_context_type varchar(40) R`, `source_context_id uuid N`, `timeframe`, `generated_at`, `market_data_cutoff_at`, `classification varchar(24)`, `score numeric(7,4)`, `confidence numeric(7,4)`, `trigger_price numeric(24,8) N`, `status`, `parameter_snapshot jsonb`, `configuration_hash`, `publication_key varchar(128) R`, `created_at`.
- Integrity: unique `publication_key`; scores/confidence 0..100; cutoff ≤ generation; scope/owner consistent; classification/status constrained.
- Mutation/index/owner/retention: immutable after publication; `(instrument_id,timeframe,generated_at desc)`, `(user_id,status,generated_at desc)`, `(strategy_version_id,generated_at desc)`; context-owned/shared; signals retention.

### `signal_evidence`

- Purpose/PK: append-only structured evidence; `signal_evidence_id uuid`.
- Columns/FKs: `signal_id uuid R`; `sequence_number smallint R`, `evidence_type varchar(40) R`, `evidence_entity_type varchar(80) N`, `evidence_entity_id uuid N`, `as_of_at timestamptz R`, `observed_value numeric(24,10) N`, `rule_outcome varchar(24) N`, `score_category varchar(40) N`, `contribution numeric(7,4) N`, `category_maximum numeric(7,4) N`, `safe_facts jsonb R`, `input_lineage jsonb R`, `created_at`.
- Integrity: unique `(signal_id,sequence_number)`; contributions non-negative and ≤ category maximum; frozen category maxima and total ≤100 enforced at publication.
- Mutation/index/owner/retention: append-only/frozen with signal; evidence reference index and `(signal_id,score_category)`; inherits signal; retain with signal.

### `trade_plans` and `trade_plan_targets`

- Purpose/PK: immutable advisory plan and ordered target storage; `trade_plan_id uuid`; targets use `trade_plan_target_id uuid`.
- Plan columns/FKs: `signal_id uuid R` unique; `buy_zone_low`, `buy_zone_high`, `entry_trigger`, `stop_loss`, `expected_risk`, `expected_reward` as price/money R; `risk_reward_ratio numeric(24,10) R`; `invalidation_condition text R`; `risk_evidence jsonb R`; `generated_at`, `status`, `created_at`.
- Target columns/FKs: `trade_plan_id uuid R` → plans; `target_number smallint R`; `target_price numeric(24,8) R`; `allocation_percent numeric(7,4) N`; `rationale text N`; `created_at`.
- Integrity: one plan/signal; buy high ≥ low; values non-negative, stop/entry/targets obey long-only plan arithmetic validated at publication; ratio non-negative; targets unique `(trade_plan_id,target_number)`, positive ordinal/price, allocation 0..100 and sum ≤100.
- Mutation/index/owner/retention: both immutable after publication; targets indexed by parent/order; inherit signal; retain with signal. Relational targets are selected for exact numeric validation, stable ordering, and direct queryability; JSONB is unsuitable for these stable facts.

## Backtesting

### `backtest_definitions`

- Purpose/PK: reusable v1 simulation configuration; `backtest_definition_id uuid`.
- Columns/FKs: owner scope/user and strategy version; `name`, `universe_config jsonb`, `start_date date`, `end_date date`, `initial_capital numeric(24,8)`, `currency`, `fee_rate`, `tax_rate`, `slippage_rate` as rates; `execution_assumptions jsonb`, `risk_assumptions jsonb`, `sizing_assumptions jsonb`, `reinvestment_policy jsonb`, `timeframe varchar(16) D:'1d'`, `position_side varchar(8) D:'long'`, `status`, timestamps.
- Integrity: dates ordered; capital positive; rates non-negative; timeframe exactly daily and side long in v1; scoped name unique.
- Mutation/index/owner/retention: mutable/audited definition; owner/status and strategy indexes; scope-defined; retain while runs exist.

### `backtest_runs`

- Purpose/PK: immutable simulation execution; `backtest_run_id uuid`.
- Columns/FKs: definition/strategy required; owner nullable; `definition_snapshot jsonb`, `configuration_hash`, `indicator_implementation_version varchar(80) R`, `data_snapshot_identity varchar(240) R`, `dataset_version varchar(80) R`, `dataset_cutoff_at timestamptz R`, `warm_up_from_date date R`, `simulation_from_date date R`, `simulation_to_date date R`, `run_assumptions jsonb R`, `started_at`, `completed_at N`, `status`, `random_seed bigint N`, `diagnostics jsonb N`, `last_progress_at N`, `created_at`.
- Integrity: ordered dates with warm-up not tradable; terminal status/completion coherent; the required strategy-version FK, indicator implementation version, dataset cutoff, configuration hash, and data snapshot identity (or an equivalent reproducibility reference stored by the implementation) are frozen together with costs, taxes, slippage, execution, dataset, and daily/long-only assumptions.
- Mutation/index/owner/retention: configuration immutable after start; controlled progress/status only; definition/owner/status indexes; inherited; backtest retention.

### `backtest_trades`

- Purpose/PK: simulated long trade; `backtest_trade_id uuid`.
- Columns/FKs: run/instrument required; `trade_number integer R`, optional signal/evidence refs in `evidence jsonb`; entry/exit decision and execution timestamps (exit nullable only while run partial), entry/exit prices, `quantity numeric(28,8) R`, `fees`, `taxes`, `slippage`, `stop_price N`, `target_price N`, `realized_pnl N`, `exit_reason N`, `created_at`.
- Integrity: unique `(backtest_run_id,trade_number)`; positive quantity/prices; costs non-negative; execution times do not precede decisions and exit follows entry; no short quantities.
- Mutation/index/owner/retention: immutable result once emitted/finalized; `(backtest_run_id,trade_number)`, `(instrument_id,entry_executed_at)`; inherited; with run.

### `backtest_equity_points`

- Purpose/PK: ordered equity curve; `backtest_equity_point_id uuid`.
- Columns/FKs: run required; `point_at timestamptz R`, `cash numeric(24,8) R`, `invested_value numeric(24,8) R`, `total_equity numeric(24,8) R`, `realized_pnl numeric(24,8) R`, `unrealized_pnl numeric(24,8) R`, `drawdown numeric(18,10) R`, `position_count integer R`, `created_at`.
- Integrity: unique `(backtest_run_id,point_at)`; count non-negative; reconciliation and drawdown bounds enforced by run validation.
- Mutation/index/owner/retention: immutable; unique ordered run/time index (covering values when measured); inherited; with run/rebuildable.

### `backtest_metrics`

- Purpose/PK: versioned performance metric; `backtest_metric_id uuid`.
- Columns/FKs: run required; `metric_name varchar(120) R`, `metric_version varchar(40) R`, `metric_value numeric(24,10) N`, `unit varchar(40) R`, `period_from date R`, `period_to date R`, `calculation_inputs jsonb R`, `calculated_at`, `is_defined boolean R`, `created_at`.
- Integrity: unique `(backtest_run_id,metric_name,metric_version,period_from,period_to)`; period ordered; defined iff value supplied.
- Mutation/index/owner/retention: immutable; parent/name index; inherited; with run/rebuildable.

## User tools and risk

### `watchlists` and `watchlist_items`

- Purpose/PK: user collection and membership; `watchlist_id uuid`, `watchlist_item_id uuid`.
- Columns/FKs: watchlist has required user, name/description, status, timestamps; item has watchlist/instrument required, `added_at`, `removed_at N`, `note text N`, `display_order integer N`, `created_at`.
- Integrity: unique user/normalized watchlist name; item active uniqueness `(watchlist_id,instrument_id)` via partial unique index; removal after addition; parent owner enforced.
- Mutation/index/owner/retention: mutable/archive and membership history; `(user_id,status)`, `(watchlist_id,display_order)`; user-owned; archive retained, removed item duration configurable.

### `portfolios`

- Purpose/PK: tracked account context; `portfolio_id uuid`.
- Columns/FKs: `user_id uuid R`; `name varchar(160) R`, `base_currency varchar(3) R`, `inception_date date R`, `description text N`, `status varchar(24) R`, timestamps.
- Integrity: unique `(user_id,name)` under normalization; status `{active,archived}`.
- Mutation/index/owner/retention: mutable metadata; `(user_id,status)`; user-owned; permanent while financial history exists.

### `portfolio_transactions`

- Purpose/PK: authoritative financial event; `portfolio_transaction_id uuid`.
- Columns/FKs: portfolio/user required; instrument nullable; `transaction_type varchar(32) R`, `effective_at timestamptz R`, `quantity numeric(28,8) N`, `price numeric(24,8) N`, `fees numeric(24,8) R D:0`, `taxes numeric(24,8) R D:0`, `cash_amount numeric(24,8) N`, `currency varchar(3) R`, `source_reference varchar(240) N`, `idempotency_key varchar(128) R`, `note text N`, `corrects_portfolio_transaction_id uuid N`, `reversal_of_portfolio_transaction_id uuid N`, `recorded_at`, `created_by_user_id uuid R`.
- Integrity: unique `(portfolio_id,idempotency_key)`; owner equals portfolio owner; costs non-negative; type-specific required fields/signs; correction/reversal references same portfolio and not self.
- Mutation/index/owner/retention: append-only; `(portfolio_id,effective_at,portfolio_transaction_id)`, `(user_id,effective_at desc)`, `(instrument_id,effective_at)`; user-owned; permanent financial history.

### `portfolio_positions` and `portfolio_valuations`

- Purpose/PK: derived point-in-time holdings/value; `portfolio_position_id uuid`, `portfolio_valuation_id uuid`.
- Position columns/FKs: portfolio/user/instrument; `as_of_at`, fractional `quantity`, `cost_basis`, `average_cost`, `realized_value`, `unrealized_value`, `currency`, `derivation_version`, `source_transaction_from_id N`, `source_transaction_to_id N`, `configuration_hash`, `created_at`.
- Valuation columns/FKs: portfolio/user; `as_of_at`, `cash`, `holdings_value`, `total_value`, `pnl`, `currency`, `price_references jsonb`, `calculation_version`, `configuration_hash`, `created_at`.
- Integrity: position unique `(portfolio_id,instrument_id,as_of_at,derivation_version)`; valuation unique `(portfolio_id,as_of_at,calculation_version)`; owner consistency; arithmetic/reconciliation; quantities may be zero but not silently contradict effective transactions.
- Mutation/index/owner/retention: immutable snapshots; latest position `(portfolio_id,instrument_id,as_of_at desc)` and valuation `(portfolio_id,as_of_at desc)`; user-owned; configurable snapshot retention, rebuildable from permanent transactions and market inputs.

### `risk_profiles`

- Purpose/PK: effective user risk configuration; `risk_profile_id uuid`.
- Columns/FKs: user required; `name`, `version integer R`, `capital_basis numeric(24,8) R`, `currency`, risk/position/concentration limits as rates, `effective_from timestamptz R`, `effective_to N`, `status`, `configuration jsonb R`, timestamps.
- Integrity: unique `(user_id,name,version)`; positive capital, non-negative/bounded limits, valid interval; effective active versions do not overlap for same named profile.
- Mutation/index/owner/retention: draft mutable, effective version immutable; `(user_id,status,effective_from desc)`; user-owned; permanent versioned configuration while referenced.

### `position_size_recommendations`

- Purpose/PK: deterministic advisory calculation; `position_size_recommendation_id uuid`.
- Columns/FKs: user/profile/instrument required; optional signal/trade plan/portfolio; `as_of_at`, `risk_profile_snapshot jsonb`, entry/stop price, available capital, recommended fractional quantity, recommended value, risk amount, currency, `constraints_applied jsonb`, `evidence jsonb`, `configuration_hash`, `status`, `created_at`.
- Integrity: owner consistency; non-negative results/capital/risk; entry/stop valid for long context; unique opportunity/as-of/hash identity as applicable.
- Mutation/index/owner/retention: immutable; `(user_id,as_of_at desc)`, instrument/profile indexes; user-owned; analytical evidence policy/rebuildable.

### `portfolio_risk_snapshots`

- Purpose/PK: point-in-time portfolio risk; `portfolio_risk_snapshot_id uuid`.
- Columns/FKs: user/portfolio/risk profile required; `as_of_at`, `exposures jsonb`, `concentration numeric(18,10)`, `liquidity_measures jsonb`, `risk_measures jsonb`, `breaches jsonb`, `input_references jsonb`, `calculation_version`, `configuration_hash`, `created_at`.
- Integrity: unique `(portfolio_id,as_of_at,calculation_version,configuration_hash)`; owner consistency; concentration bounded.
- Mutation/index/owner/retention: immutable; `(user_id,as_of_at desc)`, latest portfolio index; user-owned; configurable/rebuildable.

## Market intelligence

### Snapshot tables

The four tables are immutable shared derived snapshots with UUID PKs and `created_at`:

- `market_breadth_snapshots`: optional `index_id`; `market_context`, `universe_snapshot jsonb`, timeframe/as-of, advancing/declining/unchanged counts, `measures jsonb`, `coverage numeric(7,4)`, `input_references jsonb`, `calculation_version`, `configuration_hash`. Unique context/index/timeframe/as-of/version/hash; counts non-negative and coverage bounded.
- `relative_strength_snapshots`: `subject_type`, `subject_id uuid`, `benchmark_type`, `benchmark_id uuid`, timeframe/as-of, `lookback_period integer`, `strength_value numeric(24,10)`, `rank integer N`, coverage, inputs, method/version/hash. Unique subject/benchmark/context; lookback/rank positive.
- `sector_rotation_snapshots`: optional `index_id`; `benchmark_type/id`, `universe_snapshot`, timeframe/as-of, `sector_measures jsonb`, `coverage`, inputs, method/version/hash. Unique benchmark/context/version/hash.
- `market_regime_snapshots`: optional `index_id`; `market_context`, timeframe/as-of, `regime_classification`, confidence, `component_evidence jsonb`, input range, method/version/hash. Unique context/index/time/version/hash; confidence bounded; input ends by as-of.

Indexes support `(index_id,timeframe,as_of_at desc)` or `(subject_type,subject_id,timeframe,as_of_at desc)` as applicable. Data is shared, rebuildable, and retained under analytical-snapshot policy; referenced evidence must remain resolvable.

## Alerts

### `alert_rules`

- Purpose/PK: user-owned alert definition; `alert_rule_id uuid`.
- Columns/FKs: user required; optional instrument/strategy; `name`, `universe_config jsonb N`, `timeframe`, `condition_type`, `condition_config jsonb`, `parameter_bindings jsonb`, `channels jsonb`, `schedule_config jsonb`, `status`, `last_evaluated_at N`, timestamps.
- Integrity: unique normalized `(user_id,name)`; exactly an instrument or documented universe where required; channels subset `{in_app,email,telegram}`; strategy condition requires published version.
- Mutation/index/owner/retention: mutable/audited; `(user_id,status,last_evaluated_at)`, partial scheduling index for active rules, instrument/strategy indexes; user-owned; retired rules retained with evaluation history.

### `alert_evaluations`

- Purpose/PK: frozen deterministic evaluation; `alert_evaluation_id uuid`.
- Columns/FKs: rule/user required; optional strategy; `rule_snapshot jsonb`, `evaluated_at`, `market_data_cutoff_at`, `configuration_hash N`, `condition_outcome boolean N`, `evidence jsonb`, `deduplication_key varchar(128)`, `status`, `diagnostics jsonb N`, `created_at`.
- Integrity: unique `(alert_rule_id,deduplication_key)`; owner consistent; cutoff ≤ evaluation; triggered/not-triggered require outcome; status constrained.
- Mutation/index/owner/retention: terminal immutable; `(alert_rule_id,evaluated_at desc)`, `(user_id,status,evaluated_at desc)`; user-owned; configurable alert-evaluation retention.

### `notification_deliveries`

- Purpose/PK: one channel attempt; `notification_delivery_id uuid`.
- Columns/FKs: evaluation/user required; optional prior delivery; `channel`, `destination_reference`, `payload_template_version`, `payload_metadata jsonb`, `attempt_number smallint`, `queued_at`, `attempted_at N`, `delivered_at N`, `status`, `provider_diagnostics jsonb N`, `created_at`.
- Integrity: unique `(alert_evaluation_id,channel,attempt_number)`; attempt positive; channel frozen set; timestamp/status coherence; no credentials.
- Mutation/index/owner/retention: controlled until terminal, then immutable; `(user_id,status,queued_at)`, `(alert_evaluation_id,channel,attempt_number)`, partial failed/pending indexes; user-owned; configurable delivery-log retention.

## Trading journal

### `journal_entries`

- Purpose/PK: user decision/observation; `journal_entry_id uuid`.
- Columns/FKs: user required; optional instrument/signal/trade plan/portfolio; `occurred_at`, `title`, `body`, `entry_type`, `tags jsonb`, `status`, `finalized_at N`, `revision_of_journal_entry_id N`, timestamps.
- Integrity: referenced user-owned contexts share owner; finalized state requires timestamp; revisions point to same owner and not self.
- Mutation/index/owner/retention: draft mutable; finalized immutable and revised by new row; `(user_id,occurred_at desc)`, `(instrument_id,occurred_at desc)`; user-owned; retained by configurable personal-data policy.

### `journal_attachments`

- Purpose/PK: access-controlled file metadata; `journal_attachment_id uuid`.
- Columns/FKs: entry/user required; `storage_reference text R`, `filename varchar(255) R`, `media_type varchar(160) R`, `size_bytes bigint R`, `checksum varchar(128) R`, `uploaded_at`, `status`, `removed_at N`, `validation_metadata jsonb N`, `created_at`.
- Integrity: unique `(journal_entry_id,checksum,filename)`; positive size; owner matches entry; state/timestamps coherent.
- Mutation/index/owner/retention: available identity immutable, removal recorded; `(user_id,uploaded_at desc)`, `(journal_entry_id)`; user-owned; metadata follows entry, binary retention configurable.

### `journal_reviews`

- Purpose/PK: structured retrospective; `journal_review_id uuid`.
- Columns/FKs: entry/user required; `reviewed_at`, `outcome_assessment text`, `adherence_notes text N`, `lessons text N`, `linked_evidence jsonb N`, `review_version integer R`, `status`, `revision_of_journal_review_id N`, timestamps.
- Integrity: unique `(journal_entry_id,review_version)`; owner consistency; positive version; revision same entry/owner.
- Mutation/index/owner/retention: draft mutable, finalized immutable; entry/version index; user-owned; with entry.

## AI explanations

### `explanation_requests`

- Purpose/PK: frozen grounded input; `explanation_request_id uuid`.
- Columns/FKs: user required; `subject_type`, `subject_id uuid`, `evidence_snapshot jsonb`, `locale varchar(16)`, `style_constraints jsonb N`, `ai_provider varchar(80)`, `model_name varchar(120)`, `template_version varchar(40)`, `input_checksum varchar(128)`, `requested_at`, `processing_started_at N`, `completed_at N`, `status`, `diagnostic_metadata jsonb N`, `created_at`.
- Integrity: evidence is nonempty/versioned and references only grounded `indicator_results`, `signals`, `signal_evidence`, and `trade_plans`; unique user/input/template/model attempt identity as policy defines; timestamp/status coherence; no API key. Explanation modules must not consume raw `price_bars` to independently derive analytical truth.
- Mutation/index/owner/retention: input immutable after submission, status controlled; `(user_id,requested_at desc)`, `(status,requested_at)`; user-owned; configurable AI retention.

### `explanation_results`

- Purpose/PK: generated language separate from truth; `explanation_result_id uuid`.
- Columns/FKs: `explanation_request_id uuid R` → requests; `user_id uuid R` → users; `ai_provider varchar(80) R`, `model_name varchar(120) R`, `template_version varchar(40) R`, `generated_at timestamptz N`, `result_text text N`, `evidence_citations jsonb R`, `limitations text R`, `risk_disclaimer text R`, `status varchar(24) R`, `diagnostic_metadata jsonb N`, `output_checksum varchar(128) N`, `created_at timestamptz R`.
- Integrity: unique `explanation_request_id`; owner consistency; available requires text/time/disclaimer; no credentials; citations limited to request evidence.
- Mutation/index/owner/retention: immutable terminal output; `(user_id,generated_at desc)`; user-owned derived prose, regenerable only through a new request and never analytical truth; configurable AI retention.

## Cross-table enforcement notes

Application services and database constraints jointly enforce polymorphic evidence references because PostgreSQL foreign keys cannot validate multiple target tables through one column. Every evidence payload includes a schema version, stable referenced UUIDs, source type, and configuration/input hash. Publication transactions validate targets before freezing the record.

High-value user-owned children duplicate `user_id` deliberately for isolation and indexing. Composite owner consistency should be enforced with suitable unique parent keys and composite foreign keys where migration design permits. The duplicate value is not independent ownership state.

Corporate-action evidence for an adjusted bar is preserved in `action_evidence` as a versioned list of action UUIDs and factors because the relationship is calculation evidence rather than mutable membership; every referenced UUID is validated at publication. This avoids inventing a frozen-domain entity while retaining exact lineage.
