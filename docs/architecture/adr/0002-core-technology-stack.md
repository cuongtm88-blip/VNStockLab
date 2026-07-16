# ADR-0002: Use React, TypeScript, FastAPI, PostgreSQL, and Redis

## Status

Accepted

## Date

2026-07-16

## Context

VNStockLab requires a maintainable technology stack for browser-based dashboards, backend APIs, persistent market and application data, caching, temporary task state, charting, and local service orchestration. The stack must support deterministic, testable technical-analysis calculations and remain portable from the Mac development environment to a server.

AI capabilities may provide explanations and reports, but they must not be the source of market data or indicator values.

## Decision

VNStockLab will use the following core technologies:

- Frontend: React with TypeScript
- Frontend build tool: Vite
- Backend: FastAPI with Python
- Primary database: PostgreSQL
- Cache and temporary task state: Redis
- Local service orchestration: Docker Compose
- Charting foundation: TradingView Lightweight Charts
- Communication: REST API, with optional WebSocket support where real-time updates are required

PostgreSQL and Redis will initially run in Docker containers. Technical-analysis calculations will remain deterministic and testable. AI will be used for explanations and reports, not as the source of market data or indicator values.

## Consequences

- React, TypeScript, and Vite provide a typed, component-based frontend development environment with a fast local build workflow.
- FastAPI and Python support API development and integration with deterministic technical-analysis code.
- PostgreSQL provides durable primary storage, while Redis supports caching and temporary task state.
- Docker Compose provides consistent local orchestration for PostgreSQL, Redis, and other services as they are introduced.
- REST is the default communication model, while WebSockets may be added selectively for real-time updates.
- TradingView Lightweight Charts provides the foundation for financial charting.
- The project must maintain container configuration and clear service boundaries to preserve portability from macOS development to server deployment.
