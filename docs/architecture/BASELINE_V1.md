# VNStockLab Version 1 Architecture Baseline

**Status:** Frozen  
**Version:** 1.0  
**Freeze date:** 2026-07-16

## Purpose

This document freezes the technical baseline for VNStockLab version 1.0. It is the implementation contract for technology selection, system shape, data processing, quality controls, and deployment approach. `MODULE_MAP.md` and `DATA_FLOW.md` refine this baseline without replacing it.

## System architecture

VNStockLab is a modular monolith. Backend capabilities are separated into explicit modules with defined ownership, while being developed, deployed, and operated as one application system. Version 1 must not be decomposed into microservices.

The browser client communicates with the backend through REST APIs by default. WebSockets are used selectively only where server-pushed updates materially improve the in-app experience. They do not replace the default request-response API model.

Background and scheduled work uses Celery, with Redis providing the required supporting infrastructure. PostgreSQL is the system-of-record database. PostgreSQL and Redis initially run in Docker.

## Frozen technology stack

### Frontend

- React, TypeScript, and Vite.
- Material UI for the application user interface.
- TanStack Query for server-state access and synchronization.
- React Router for client-side routing.
- Zustand for appropriate client-side application state.
- TradingView Lightweight Charts for financial charts.
- Apache ECharts for dashboard and analytical charts.
- Vitest for frontend tests and Playwright for end-to-end tests.
- ESLint and Prettier for static checks and formatting.

### Backend

- Python 3.13.
- FastAPI for HTTP APIs and selective WebSocket endpoints.
- Pydantic v2 for validation and API data models.
- SQLAlchemy 2 for persistence access.
- Alembic for database schema migrations.
- Celery for background and scheduled processing.
- pandas, NumPy, and SciPy where appropriate for data and numerical analysis.
- Pytest, Ruff, and Mypy for tests, linting, and type checking.

### Data and infrastructure

- PostgreSQL for durable relational data.
- Redis for supporting cache, messaging, and background-processing needs appropriate to the architecture.
- Docker Compose for local service orchestration and version 1 deployment packaging.
- Pre-commit for consistent local quality checks.
- Local macOS development precedes server deployment.

## Architectural invariants

### Deterministic analysis

Market-derived outputs are calculated by deterministic application components from validated and normalized data. Analysis processing follows the canonical flow in `DATA_FLOW.md`. Records must carry the identifiers, timestamps, configuration, and version references needed to trace material outputs to their origin.

### Shared Strategy Engine

Scanner, backtest, and alerts must call one shared Strategy Engine implementation. They must not contain independent copies of strategy rules. Strategies are versioned and traceable; an evaluation or stored result must identify the strategy version used.

### Technical Score

Technical Score version 1 totals 100 points with these frozen weights: Trend 25, Momentum 20, Volume 15, Money Flow 15, Market Structure 15, and Pattern Confirmation 10. Score output must retain category contributions and supporting evidence. A high score alone is not a buy recommendation.

### Backtesting integrity

Version 1 backtesting is long-only and daily-data-only. It accounts for initial capital, fees, taxes, slippage, stop loss, take profit, trailing stop, position sizing, position limits, and capital reinvestment. Data access and event ordering must prevent look-ahead bias and data leakage.

### AI boundary

AI explanations operate only on supplied deterministic data and outputs. AI may explain but must never invent market data, indicators, patterns, scores, signals, or trade plans. AI-generated price forecasts are prohibited in version 1.

### Module ownership

Backend ownership follows `MODULE_MAP.md`. Cross-module behavior must use explicit application contracts rather than bypassing module boundaries or duplicating domain logic.

## Quality baseline

Implementation changes must pass the relevant automated checks from the frozen toolchain: Pytest, Ruff, Mypy, ESLint, Prettier, Vitest, Playwright, and pre-commit. The delivery process also requires manual review. Test depth must be proportionate to risk, with particular attention to numerical correctness, strategy consistency, data adjustment, score traceability, and backtest bias prevention.

## Development and deployment baseline

Development begins locally on macOS. Docker Compose provides PostgreSQL and Redis initially and is the version 1 orchestration standard. Server deployment occurs only after the stabilization and deployment phase and must preserve the same architectural boundaries and mandatory dependencies.

## Freeze and change control

Changes are allowed only for blocking technical constraints, security risks, data-loss risks, or unavailable mandatory dependencies.

Every approved change requires an ADR. The ADR must document the triggering condition, evaluated impact, approved replacement or mitigation, and consequences for the product and delivery contract. Convenience, preference, newly proposed features, or speculative scaling are not sufficient reasons to change this baseline. New ideas belong in `BACKLOG_V2.md` and do not change version 1 implementation.

