# System Overview

VNStockLab is planned as a web application with a React and TypeScript frontend and a FastAPI backend. The frontend will present dashboards, charts, scanners, portfolio tools, and analysis workflows. The backend will expose REST APIs for market data, analytics, strategies, backtests, portfolios, alerts, and supporting services. Optional WebSocket connections may provide timely updates where live or near-real-time interaction is useful.

PostgreSQL will serve as the primary persistent data store for application data, normalized market data, strategies, backtest results, portfolios, alerts, and journal entries. Redis will support caching, transient state, task coordination, and other short-lived workloads. Background workers will handle scheduled ingestion, computationally intensive analysis, scanning, backtesting, and alert evaluation outside the request-response cycle.

## Major Backend Modules

- **API layer:** Defines REST endpoints, request validation, response models, authentication boundaries, and optional WebSocket connections.
- **Market data:** Ingests, validates, normalizes, stores, and retrieves Vietnamese market data from approved sources.
- **Technical analysis:** Performs deterministic indicator, Ichimoku, pattern, support and resistance, Dow Theory, and Elliott Wave scenario calculations.
- **Scanner and signals:** Applies screening rules, evaluates versioned strategies, scores signals, and records traceable evidence.
- **Backtesting:** Replays strategies against historical data with reproducible assumptions and safeguards against look-ahead bias.
- **Portfolio and risk:** Tracks positions, performance, exposure, allocation, and risk-management constraints.
- **Sector analysis:** Measures sector strength and rotation using consistent market classifications and calculations.
- **Alerts:** Evaluates user-defined conditions and coordinates delivery through configured channels.
- **Trading journal:** Stores decisions, observations, trades, outcomes, and links to the analysis available at the time.
- **AI explanations:** Produces natural-language explanations from deterministic platform outputs without calculating or inventing market values.
- **Background jobs:** Coordinates scheduled data processing, scans, backtests, alert checks, and other asynchronous workloads.

## Development and Deployment Direction

Development will take place locally on macOS before the system is deployed to a server. PostgreSQL and Redis will later run through Docker Compose for consistent local infrastructure. Application packaging, deployment topology, operational monitoring, and production security controls will be defined as the project evolves.
