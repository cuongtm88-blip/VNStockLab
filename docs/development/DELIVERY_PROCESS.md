# VNStockLab Version 1 Delivery Process

## Purpose

This document defines the required workflow for every version 1 delivery unit. The process protects the frozen product and architecture baseline, creates reviewable changes, and prevents new ideas from entering implementation without approval.

## Required workflow

### 1. Frozen task specification

Before implementation, the delivery unit must have a frozen task specification that identifies scope, acceptance criteria, affected modules, data or migration impact, required tests, and explicit exclusions. The task must conform to the version 1 product scope, architecture baseline, module map, data flow, and roadmap.

Ambiguity that changes product behavior or architectural ownership must be resolved before implementation. A new idea is not an implicit requirement.

### 2. Git feature branch

Implementation occurs on a focused Git feature branch associated with the frozen task. Unrelated work must not be mixed into the branch.

### 3. Codex implementation

Codex implements only the accepted task specification, preserves module boundaries, and follows the frozen technology choices. The implementation must include the tests and documentation necessary to satisfy the task contract. Any discovered idea outside the contract is recorded in `BACKLOG_V2.md` and is not implemented in version 1.

### 4. Automated tests

Run all checks relevant to the change. The version 1 toolchain comprises Pytest, Ruff, Mypy, ESLint, Prettier, Vitest, Playwright, and pre-commit. A delivery unit is not ready for acceptance while applicable checks fail.

Risk-focused tests must cover the affected behavior. Analytical and strategy work requires deterministic expected results and traceability checks. Backtest work requires explicit protection against look-ahead bias and data leakage. Data changes require validation and adjustment checks. AI work requires grounding and non-invention checks.

### 5. Manual review

A reviewer confirms that the change:

- Satisfies the frozen task and its acceptance criteria.
- Does not add out-of-scope behavior.
- Respects module ownership and the canonical data flow.
- Uses the shared Strategy Engine where required.
- Preserves security, data integrity, traceability, and user ownership.
- Includes appropriate automated test evidence.
- Does not let AI originate deterministic market or analysis outputs.

### 6. Focused commit

Create a focused commit containing only the accepted delivery unit. The commit must be understandable and traceable to its task specification. Generated noise, unrelated formatting, speculative refactoring, and unrelated features are excluded.

### 7. Merge only after acceptance

Merge occurs only after automated checks pass, manual review is complete, and the task is explicitly accepted. Failed acceptance returns the work to implementation and review; it does not lower the frozen criteria.

## Change control

The version 1 architecture baseline may change only for a blocking technical constraint, security risk, data-loss risk, or unavailable mandatory dependency. Every approved baseline change requires an ADR before the changed implementation is accepted.

New ideas go to `docs/product/BACKLOG_V2.md` and do not change version 1 implementation. A backlog entry is not approval to implement, schedule, or alter acceptance criteria.

## Definition of accepted delivery

A delivery unit is accepted only when its frozen specification is fulfilled, relevant automated tests pass, manual review is complete, documentation and traceability are adequate, and the focused change is approved for merge. Partial completion, an unreviewed implementation, or a passing test suite without scope acceptance is not accepted delivery.

