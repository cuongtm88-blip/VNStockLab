# VNStockLab Version 1 Backend Module Map

## Purpose

This document defines responsibility boundaries for the VNStockLab modular-monolith backend. Each domain capability has one primary owning module. Modules may collaborate through explicit service contracts, but must not duplicate another module's rules or reach through its internal implementation.

## Module responsibilities

| Module | Owns | Key collaborations |
| --- | --- | --- |
| `identity` | Basic multi-user identity, authentication context, and ownership context for user-specific records. | Supplies user context to watchlists, portfolios, alerts, journal, and other protected operations. |
| `instruments` | Canonical Vietnamese market instrument identity and instrument reference information used throughout the platform. | Provides instrument references to market data and all analytical and user-tool modules. |
| `market_data` | Raw-data intake, validation, normalization, adjustment, storage, and retrieval of market data. | Supplies adjusted, time-aware inputs to technical analysis, strategies, backtesting, and market intelligence. |
| `technical_analysis` | Indicators, Ichimoku, volume and money-flow analysis, market structure, candlestick patterns, price patterns, support and resistance, Dow Theory, and Elliott Wave scenarios. | Consumes market data and provides deterministic evidence to strategies, signals, scanner, backtesting, and explanations. |
| `strategies` | The shared, versioned Strategy Engine; strategy definitions and evaluation; Technical Score calculation and trace details. | Is invoked by scanner, backtesting, and alerts; consumes technical evidence and supplies evaluations to signals. |
| `scanner` | Universe-level execution of strategy criteria and presentation-ready scan results. | Uses instruments, market data, technical analysis, and the shared Strategy Engine. |
| `signals` | Materialization and lifecycle of deterministic signals and trade plans produced from strategy evaluations. | Receives versioned strategy results and exposes grounded outputs to alerts and AI explanations. |
| `backtesting` | Long-only daily simulation, portfolio accounting, execution assumptions, risk controls, results, and bias safeguards. | Uses historical market data and the shared Strategy Engine; must preserve point-in-time correctness. |
| `watchlists` | User-owned collections of instruments. | Uses identity and instruments; provides selected instruments to relevant analysis workflows. |
| `portfolios` | User portfolio records and portfolio-level holdings context used by version 1 tools. | Uses identity, instruments, market data, and risk. |
| `risk` | Risk-management calculations and rules, including position sizing and position limits where used by trade planning and backtesting. | Supports signals, portfolios, and backtesting. |
| `market_intelligence` | Market dashboard analytics, market breadth, and sector rotation. | Aggregates instrument, market-data, and appropriate technical-analysis outputs. |
| `alerts` | Alert definitions, evaluation scheduling or triggering, alert records, and in-app, email, and Telegram delivery. | Uses identity and the shared Strategy Engine; may consume signals while preserving source traceability. |
| `journal` | User-owned trading journal entries and their associations with relevant instruments or decision-support context. | Uses identity and instruments and may reference signals, trade plans, or portfolio context. |
| `ai_explanations` | Grounded natural-language explanations of supplied deterministic outputs and their limitations. | Reads approved outputs from technical analysis, strategies, signals, backtesting, and market intelligence; does not calculate or alter them. |

## Shared contracts and rules

- `instruments` supplies canonical identifiers; other modules must not create competing instrument identities.
- `market_data` owns data validation, normalization, and adjustment. Downstream modules consume its approved representations rather than silently repairing inputs.
- `technical_analysis` owns reusable analytical calculations. Strategy rules compose this evidence rather than duplicating indicator or pattern calculations.
- `strategies` owns the only Strategy Engine implementation. Scanner, backtesting, and alerts are consumers of this implementation.
- `signals` turns strategy evaluations into signals and trade plans; it does not redefine strategy logic.
- `risk` supplies reusable risk rules to live decision-support and simulation contexts so their meanings remain consistent.
- `ai_explanations` is downstream and read-only with respect to deterministic outputs. Its text must be grounded in provided facts and must not become a source of market facts or decisions.
- User-owned records must retain identity ownership. Authorization must be enforced at the relevant module boundary.

## Traceability requirements

Material derived records must preserve the applicable instrument, market-data time or snapshot, calculation version, strategy identifier and version, evaluation time, and user context. Scanner results, alerts, backtests, Technical Scores, signals, and trade plans must be traceable to the shared strategy evaluation and its deterministic evidence.

## Boundary enforcement

The modular monolith may share infrastructure, transactions, and process deployment, but domain code must follow the ownership map above. Any proposal that changes module ownership or introduces a new backend module changes the frozen architecture and is subject to the baseline change-control rules.

