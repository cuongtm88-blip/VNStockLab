# VNStockLab Version 1 Out of Scope

## Purpose

This document establishes explicit boundaries for VNStockLab version 1.0. The following capabilities and architecture choices must not be implemented as part of version 1, even when they appear adjacent to an in-scope capability.

## Excluded product capabilities

| Exclusion | Version 1 boundary |
| --- | --- |
| Direct broker order placement | VNStockLab may produce decision-support outputs and trade plans, but it does not submit, amend, or cancel broker orders. |
| Automated real-money trading | No version 1 workflow may autonomously execute trades using real capital. |
| Native desktop or mobile applications | Version 1 is delivered as a web application; native application packages are excluded. |
| Investor social network | Social feeds, follower relationships, community publishing, and equivalent social-network behavior are excluded. |
| Full real-time news and sentiment platform | Version 1 does not provide a comprehensive real-time news aggregation and sentiment-analysis product. |
| AI-generated price forecasts | AI must not generate future price targets, paths, or forecasts. |
| High-frequency trading | Low-latency execution infrastructure and high-frequency strategies are excluded. |
| Commercial multi-tenant billing | Subscription billing, commercial tenant plans, and tenant metering are excluded. Basic multi-user access remains in scope. |

## Excluded architecture and operations

| Exclusion | Version 1 boundary |
| --- | --- |
| Microservices | The backend is a modular monolith with explicit internal module boundaries. |
| Kubernetes | Version 1 uses Docker Compose and does not require Kubernetes manifests or cluster operations. |

## Interpretation rules

- An in-scope signal or trade plan is advisory and does not imply order execution.
- Alerts communicate platform events; they do not initiate real-money trading.
- Elliott Wave scenarios and deterministic analysis must not be reframed as AI-generated price forecasts.
- Basic multi-user access does not imply commercial tenancy or billing.
- Selective WebSocket use does not create a high-frequency trading or full real-time news requirement.
- Work on any excluded item requires a future-scope decision and must not change the frozen version 1 implementation contract.

