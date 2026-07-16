# Development Principles

## Modular Design

Organize the system into cohesive modules with clear responsibilities, stable boundaries, and minimal coupling. Domain logic should remain independent of presentation and infrastructure concerns wherever practical.

## Traceable Signals

Every generated signal must identify the data, rules, parameters, strategy version, and calculation time that produced it. Users and developers should be able to inspect the evidence behind a result.

## Reproducible Calculations

Given the same validated input data, configuration, and software version, calculations must produce the same results. Relevant assumptions, rounding rules, time zones, and data adjustments must be explicit.

## Versioned Strategies

Strategies and material rule changes must be versioned. Historical signals and backtests must retain the exact strategy version and parameters used to generate them.

## No Secrets Committed to Git

Credentials, API keys, tokens, private certificates, and other secrets must never be committed to Git. Secrets must be supplied through appropriately secured runtime configuration.

## Automated Tests

Critical domain calculations, data validation, APIs, strategy behavior, and failure paths must be covered by automated tests. Tests should be deterministic, maintainable, and run as part of the normal development workflow.

## Prevent Look-Ahead Bias

Backtests must use only information that would have been available at each simulated point in time. Data alignment, indicator warm-up periods, corporate actions, execution assumptions, and signal timing must be handled explicitly to prevent look-ahead bias.

## AI Explains; It Does Not Calculate

AI may explain deterministic technical-analysis outputs, but it must not calculate or invent market data, indicator values, patterns, or signals. Quantitative results must originate from tested and traceable platform logic.

## Small, Reviewable Git Commits

Changes should be delivered in small, focused Git commits that are easy to understand, test, review, and revert. Each commit should represent one coherent unit of work.
