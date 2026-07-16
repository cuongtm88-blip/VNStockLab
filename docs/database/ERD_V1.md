# VNStockLab ERD V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

These conceptual diagrams use physical table names and show only major identity and relationship columns. Evidence payloads may contain validated polymorphic references that are summarized after the diagrams.

## 1. Identity and ownership

```mermaid
erDiagram
  users { uuid user_id PK string normalized_email }
  roles { uuid role_id PK string name }
  user_roles { uuid user_id PK,FK uuid role_id PK,FK }
  refresh_tokens { uuid refresh_token_id PK uuid user_id FK uuid rotated_to_refresh_token_id FK }
  audit_logs { uuid audit_log_id PK uuid actor_user_id FK uuid owner_user_id FK }
  watchlists { uuid watchlist_id PK uuid user_id FK }
  portfolios { uuid portfolio_id PK uuid user_id FK }
  risk_profiles { uuid risk_profile_id PK uuid user_id FK }
  alert_rules { uuid alert_rule_id PK uuid user_id FK }
  journal_entries { uuid journal_entry_id PK uuid user_id FK }
  explanation_requests { uuid explanation_request_id PK uuid user_id FK }
  users ||--o{ user_roles : receives
  roles ||--o{ user_roles : assigned_as
  users ||--o{ refresh_tokens : owns
  users o|--o{ audit_logs : acts_in
  users o|--o{ audit_logs : affected_owner
  users ||--o{ watchlists : owns
  users ||--o{ portfolios : owns
  users ||--o{ risk_profiles : owns
  users ||--o{ alert_rules : owns
  users ||--o{ journal_entries : owns
  users ||--o{ explanation_requests : owns
```

## 2. Instruments and market data

```mermaid
erDiagram
  exchanges { uuid exchange_id PK }
  sectors { uuid sector_id PK }
  industries { uuid industry_id PK uuid sector_id FK }
  instruments { uuid instrument_id PK uuid exchange_id FK uuid sector_id FK uuid industry_id FK }
  data_providers { uuid data_provider_id PK }
  instrument_aliases { uuid instrument_alias_id PK uuid instrument_id FK uuid data_provider_id FK uuid exchange_id FK }
  indices { uuid index_id PK uuid exchange_id FK }
  index_constituents { uuid index_constituent_id PK uuid index_id FK uuid instrument_id FK }
  import_batches { uuid import_batch_id PK uuid data_provider_id FK }
  raw_market_records { uuid raw_market_record_id PK uuid import_batch_id FK uuid data_provider_id FK uuid instrument_id FK }
  trading_calendars { uuid trading_calendar_id PK uuid exchange_id FK }
  corporate_actions { uuid corporate_action_id PK uuid instrument_id FK uuid data_provider_id FK uuid import_batch_id FK }
  price_bars { uuid price_bar_id PK uuid instrument_id FK uuid data_provider_id FK uuid import_batch_id FK }
  adjusted_price_bars { uuid adjusted_price_bar_id PK uuid price_bar_id FK uuid instrument_id FK }
  data_quality_issues { uuid data_quality_issue_id PK uuid import_batch_id FK uuid instrument_id FK }
  sectors ||--o{ industries : contains
  exchanges ||--o{ instruments : lists
  sectors o|--o{ instruments : classifies
  industries o|--o{ instruments : classifies
  instruments ||--o{ instrument_aliases : identified_by
  data_providers o|--o{ instrument_aliases : contextualizes
  indices ||--o{ index_constituents : contains
  instruments ||--o{ index_constituents : member
  data_providers ||--o{ import_batches : supplies
  import_batches ||--o{ raw_market_records : contains
  instruments o|--o{ raw_market_records : maps
  exchanges ||--o{ trading_calendars : schedules
  instruments ||--o{ corporate_actions : affected_by
  instruments ||--o{ price_bars : has
  price_bars ||--o{ adjusted_price_bars : source_for
  import_batches ||--o{ data_quality_issues : reports
```

## 3. Technical analysis and strategies

```mermaid
erDiagram
  instruments { uuid instrument_id PK }
  indicator_definitions { uuid indicator_definition_id PK }
  indicator_results { uuid indicator_result_id PK uuid indicator_definition_id FK uuid instrument_id FK }
  pattern_definitions { uuid pattern_definition_id PK }
  pattern_detections { uuid pattern_detection_id PK uuid pattern_definition_id FK uuid instrument_id FK }
  support_resistance_levels { uuid support_resistance_level_id PK uuid instrument_id FK }
  market_structure_snapshots { uuid market_structure_snapshot_id PK uuid instrument_id FK }
  elliott_scenarios { uuid elliott_scenario_id PK uuid instrument_id FK }
  strategies { uuid strategy_id PK uuid user_id FK }
  strategy_versions { uuid strategy_version_id PK uuid strategy_id FK }
  strategy_parameters { uuid strategy_parameter_id PK uuid strategy_version_id FK }
  strategy_rules { uuid strategy_rule_id PK uuid strategy_version_id FK }
  strategy_risk_rules { uuid strategy_risk_rule_id PK uuid strategy_version_id FK }
  indicator_definitions ||--o{ indicator_results : defines
  pattern_definitions ||--o{ pattern_detections : defines
  instruments ||--o{ indicator_results : analyzed
  instruments ||--o{ pattern_detections : analyzed
  instruments ||--o{ support_resistance_levels : analyzed
  instruments ||--o{ market_structure_snapshots : analyzed
  instruments ||--o{ elliott_scenarios : analyzed
  strategies ||--|{ strategy_versions : versions
  strategy_versions ||--o{ strategy_parameters : has
  strategy_versions ||--|{ strategy_rules : has
  strategy_versions ||--o{ strategy_risk_rules : has
```

## 4. Scanner, signals, and trade plans

```mermaid
erDiagram
  strategy_versions { uuid strategy_version_id PK }
  instruments { uuid instrument_id PK }
  scan_definitions { uuid scan_definition_id PK uuid strategy_version_id FK uuid user_id FK }
  scan_runs { uuid scan_run_id PK uuid scan_definition_id FK uuid strategy_version_id FK }
  scan_results { uuid scan_result_id PK uuid scan_run_id FK uuid instrument_id FK uuid signal_id FK }
  signals { uuid signal_id PK uuid instrument_id FK uuid strategy_version_id FK uuid user_id FK }
  signal_evidence { uuid signal_evidence_id PK uuid signal_id FK }
  trade_plans { uuid trade_plan_id PK uuid signal_id FK }
  trade_plan_targets { uuid trade_plan_target_id PK uuid trade_plan_id FK }
  strategy_versions ||--o{ scan_definitions : configures
  scan_definitions ||--o{ scan_runs : executes
  strategy_versions ||--o{ scan_runs : freezes
  scan_runs ||--o{ scan_results : yields
  instruments ||--o{ scan_results : evaluated
  scan_results o|--o| signals : may_publish
  strategy_versions ||--o{ signals : produces
  instruments ||--o{ signals : concerns
  signals ||--|{ signal_evidence : supported_by
  signals ||--o| trade_plans : may_have
  trade_plans ||--|{ trade_plan_targets : orders
```

## 5. Backtesting

```mermaid
erDiagram
  strategy_versions { uuid strategy_version_id PK }
  instruments { uuid instrument_id PK }
  backtest_definitions { uuid backtest_definition_id PK uuid strategy_version_id FK uuid user_id FK }
  backtest_runs { uuid backtest_run_id PK uuid backtest_definition_id FK uuid strategy_version_id FK }
  backtest_trades { uuid backtest_trade_id PK uuid backtest_run_id FK uuid instrument_id FK }
  backtest_equity_points { uuid backtest_equity_point_id PK uuid backtest_run_id FK }
  backtest_metrics { uuid backtest_metric_id PK uuid backtest_run_id FK }
  strategy_versions ||--o{ backtest_definitions : configures
  backtest_definitions ||--o{ backtest_runs : executes
  strategy_versions ||--o{ backtest_runs : freezes
  backtest_runs ||--o{ backtest_trades : records
  instruments ||--o{ backtest_trades : traded
  backtest_runs ||--o{ backtest_equity_points : emits
  backtest_runs ||--o{ backtest_metrics : calculates
```

## 6. Watchlists, portfolios, risk, alerts, and journal

```mermaid
erDiagram
  users { uuid user_id PK }
  instruments { uuid instrument_id PK }
  watchlists { uuid watchlist_id PK uuid user_id FK }
  watchlist_items { uuid watchlist_item_id PK uuid watchlist_id FK uuid instrument_id FK }
  portfolios { uuid portfolio_id PK uuid user_id FK }
  portfolio_transactions { uuid portfolio_transaction_id PK uuid portfolio_id FK uuid instrument_id FK }
  portfolio_positions { uuid portfolio_position_id PK uuid portfolio_id FK uuid instrument_id FK }
  portfolio_valuations { uuid portfolio_valuation_id PK uuid portfolio_id FK }
  risk_profiles { uuid risk_profile_id PK uuid user_id FK }
  position_size_recommendations { uuid position_size_recommendation_id PK uuid risk_profile_id FK uuid instrument_id FK uuid portfolio_id FK }
  portfolio_risk_snapshots { uuid portfolio_risk_snapshot_id PK uuid risk_profile_id FK uuid portfolio_id FK }
  alert_rules { uuid alert_rule_id PK uuid user_id FK uuid instrument_id FK uuid strategy_version_id FK }
  alert_evaluations { uuid alert_evaluation_id PK uuid alert_rule_id FK }
  notification_deliveries { uuid notification_delivery_id PK uuid alert_evaluation_id FK }
  journal_entries { uuid journal_entry_id PK uuid user_id FK uuid instrument_id FK uuid signal_id FK uuid portfolio_id FK }
  journal_attachments { uuid journal_attachment_id PK uuid journal_entry_id FK }
  journal_reviews { uuid journal_review_id PK uuid journal_entry_id FK }
  users ||--o{ watchlists : owns
  watchlists ||--o{ watchlist_items : contains
  instruments ||--o{ watchlist_items : selected
  users ||--o{ portfolios : owns
  portfolios ||--o{ portfolio_transactions : records
  portfolios ||--o{ portfolio_positions : derives
  portfolios ||--o{ portfolio_valuations : derives
  instruments o|--o{ portfolio_transactions : concerns
  instruments ||--o{ portfolio_positions : held
  users ||--o{ risk_profiles : owns
  risk_profiles ||--o{ position_size_recommendations : produces
  risk_profiles ||--o{ portfolio_risk_snapshots : produces
  portfolios o|--o{ position_size_recommendations : contextualizes
  portfolios ||--o{ portfolio_risk_snapshots : assessed
  users ||--o{ alert_rules : owns
  alert_rules ||--o{ alert_evaluations : evaluates
  alert_evaluations ||--o{ notification_deliveries : delivers
  users ||--o{ journal_entries : owns
  journal_entries ||--o{ journal_attachments : contains
  journal_entries ||--o{ journal_reviews : reviewed_by
```

## 7. Market intelligence and AI explanations

```mermaid
erDiagram
  indices { uuid index_id PK }
  market_breadth_snapshots { uuid market_breadth_snapshot_id PK uuid index_id FK }
  relative_strength_snapshots { uuid relative_strength_snapshot_id PK }
  sector_rotation_snapshots { uuid sector_rotation_snapshot_id PK uuid index_id FK }
  market_regime_snapshots { uuid market_regime_snapshot_id PK uuid index_id FK }
  users { uuid user_id PK }
  explanation_requests { uuid explanation_request_id PK uuid user_id FK }
  explanation_results { uuid explanation_result_id PK uuid explanation_request_id FK uuid user_id FK }
  indices o|--o{ market_breadth_snapshots : contextualizes
  indices o|--o{ sector_rotation_snapshots : benchmarks
  indices o|--o{ market_regime_snapshots : classifies
  users ||--o{ explanation_requests : owns
  explanation_requests ||--o| explanation_results : produces
```

## Cross-domain relationship summary

- Canonical `instruments` anchor market series, technical evidence, scan results, signals, backtest trades, watchlists, portfolio records, risk calculations, alerts, and journal context.
- Immutable `strategy_versions` anchor scanner, signals, backtests, and strategy-derived alerts so all consumers use the shared Strategy Engine and canonical technical semantics.
- Provider/batch/raw/bar/action lineage flows into analytical evidence. Evidence payload references are validated at publication even where a polymorphic relational foreign key is not possible.
- User-owned aggregate roots carry `user_id`; selected children repeat it to enforce isolation and must match the root owner.
- AI requests cite immutable deterministic evidence through a frozen, versioned evidence snapshot. Results relate only to their request and never become a parent or source of analytical truth.
- Adjusted bars, analytics, positions, valuations, risk/intelligence snapshots, scan/signal/backtest outputs, and AI prose are derived; their persisted historical versions remain immutable and traceable.
