# VNStockLab Version 1 Delivery Roadmap

## Purpose

This roadmap sequences the frozen version 1 scope into controlled delivery phases. It defines dependency order and phase outcomes, not calendar dates. A later phase may be prepared earlier, but it may not bypass the acceptance dependencies of the preceding foundations.

## Phase 0 — Baseline and design

**Objective:** Freeze the implementation contract before application construction.

**Outcomes:**

- Product scope and explicit exclusions are agreed.
- Architecture baseline, backend module ownership, and canonical data flow are frozen.
- Delivery process, quality gates, and roadmap are established.
- Baseline exceptions require the defined ADR process.

**Exit criteria:** The version 1 documentation set is internally consistent, accepted, and marked frozen where required.

## Phase 1 — Technical foundation

**Objective:** Establish the modular-monolith application and its mandatory development infrastructure.

**Outcomes:**

- React, TypeScript, Vite, Material UI, routing, server-state, and client-state foundations.
- Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, and Alembic foundations.
- PostgreSQL, Redis, Celery, and Docker Compose foundations for local macOS development.
- REST API conventions, selective WebSocket boundaries, identity foundation, and module boundaries.
- Automated quality toolchain using Pytest, Ruff, Mypy, ESLint, Prettier, Vitest, Playwright, and pre-commit.

**Exit criteria:** The technical stack runs coherently in the local development model, module boundaries are represented, persistence migration works, and applicable quality checks pass.

## Phase 2 — Market data

**Objective:** Provide trustworthy, analysis-ready Vietnamese market data.

**Outcomes:**

- Canonical instruments.
- Raw-data intake and retained source context.
- Validation, normalization, and adjusted market data.
- Traceable retrieval interfaces for downstream current and historical analysis.

**Exit criteria:** Accepted data moves through the defined market-data stages deterministically; invalid data is contained; downstream consumers receive traceable adjusted data.

## Phase 3 — Technical analysis

**Objective:** Deliver reusable, deterministic stock-analysis capabilities and visual foundations.

**Outcomes:**

- Candlestick and volume financial charts using TradingView Lightweight Charts.
- Technical indicators, Ichimoku, volume, and money-flow analysis.
- Candlestick patterns, price patterns, support and resistance.
- Market structure, Dow Theory, and Elliott Wave scenarios.
- Dashboard and analytical chart support using Apache ECharts where appropriate.

**Exit criteria:** Calculations and detections are tested against deterministic expectations, expose required parameters and lineage, and are reusable by strategy consumers.

## Phase 4 — Strategy, scanner, and signals

**Objective:** Convert technical evidence into consistent, traceable decision support.

**Outcomes:**

- One shared, versioned Strategy Engine.
- Version 1 Technical Score with frozen category weights and evidence breakdown.
- Stock scanner using the shared Strategy Engine.
- Deterministic signals and trade plans with applicable risk context.
- Strategy-driven foundations required by alerts.

**Exit criteria:** Scanner, signals, and strategy evaluation share one implementation; every material result identifies its strategy version and evidence; a score is not represented as a buy recommendation.

## Phase 5 — Backtesting

**Objective:** Evaluate versioned strategies with reproducible, bias-controlled simulations.

**Outcomes:**

- Long-only backtesting on daily data through the shared Strategy Engine.
- Initial capital, fees, taxes, slippage, stop loss, take profit, trailing stop, position sizing, position limits, and capital reinvestment.
- Reproducible configuration, results, and strategy-version traceability.
- Explicit safeguards against look-ahead bias and data leakage.

**Exit criteria:** Deterministic scenarios verify accounting and risk rules, shared-strategy consistency, point-in-time behavior, and absence of known look-ahead or leakage paths.

## Phase 6 — Market intelligence

**Objective:** Provide market-level context for stock-level analysis.

**Outcomes:**

- Market dashboard.
- Market breadth.
- Sector rotation.
- Analytical views based on validated data and deterministic calculations.

**Exit criteria:** Market-level outputs are traceable to approved data, render through the defined charting stack, and remain consistent with module ownership.

## Phase 7 — User tools

**Objective:** Deliver persistent, user-specific decision-support workflows.

**Outcomes:**

- Watchlists.
- Portfolios.
- Risk-management tools.
- Trading journal.
- In-app, email, and Telegram alerts.
- Basic multi-user access across user-owned capabilities.

**Exit criteria:** User-owned data is correctly isolated and authorized; alert delivery retains triggering context; user tools integrate without duplicating analytical or strategy logic.

## Phase 8 — AI explanations

**Objective:** Explain deterministic results clearly without transferring analytical authority to AI.

**Outcomes:**

- Grounded explanations for supported technical, strategy, score, signal, trade-plan, backtest, and market-intelligence outputs.
- Explicit presentation of evidence, limitations, and scenario uncertainty.
- Enforcement that AI never invents market data, indicators, patterns, scores, signals, or trade plans and does not generate price forecasts.

**Exit criteria:** Grounding and non-invention tests pass; explanations are traceable to supplied deterministic context; failure of explanation does not modify the underlying result.

## Phase 9 — Stabilization and deployment

**Objective:** Verify the complete version 1 contract and prepare server deployment.

**Outcomes:**

- Integrated automated and manual acceptance across the frozen scope.
- Security, data-integrity, numerical-correctness, traceability, and operational review.
- Performance and reliability stabilization within the modular-monolith and Docker Compose baseline.
- Server deployment preparation and verified operational procedures.

**Exit criteria:** All accepted version 1 capabilities meet their contracts, applicable quality gates pass, blocking risks are resolved through the approved process, and the deployment is accepted.

## Roadmap control

All phase work follows `DELIVERY_PROCESS.md`. New ideas are added to `docs/product/BACKLOG_V2.md` and do not change phase outcomes or version 1 implementation. Any permitted architecture-baseline change requires an approved ADR.

