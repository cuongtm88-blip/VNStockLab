# ADR-0001: Use a Web Application Architecture

## Status

Accepted

## Date

2026-07-16

## Context

VNStockLab needs an architecture that supports multiple users, interactive dashboards, alerts, and future expansion. The application will be developed locally on macOS first, but it must remain flexible enough to be deployed to a server later.

A desktop-only application was considered unsuitable because it would limit access across devices and reduce deployment flexibility.

## Decision

VNStockLab will be developed as a web application with a separate frontend and backend.

The frontend will run in a web browser. The backend will expose APIs that provide data and application capabilities to the frontend. Initial development will take place locally on macOS, and the application will later be deployable to a server using containers.

## Consequences

- Users can access VNStockLab through a web browser without installing a desktop application.
- Separating the frontend and backend allows each part to evolve independently behind stable API contracts.
- The architecture supports multiple users, dashboards, alerts, and future expansion.
- Container-based deployment provides a portable path from local macOS development to a server.
- The project must manage the operational and integration complexity of separate frontend and backend services.
