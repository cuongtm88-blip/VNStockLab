# VNStockLab OpenAPI Governance V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Purpose

This document governs how VNStockLab version 1 will represent, review, validate, and publish its API through OpenAPI once backend implementation begins. It does not create an OpenAPI document or authorize implementation in this documentation phase.

## Role of OpenAPI

OpenAPI is the executable, machine-readable representation of the implemented API contract. The FastAPI-generated OpenAPI document must conform to the frozen Markdown contracts. It supports interactive documentation, client understanding, validation, compatibility review, and later contract testing; generation alone does not prove semantic conformance.

## Source of truth

- Frozen Markdown contracts define product and semantic intent: allowed capabilities, ownership, authorization, lifecycle behavior, exact numeric meaning, idempotency, errors, and compatibility obligations.
- OpenAPI defines machine-readable implementation detail: paths, operations, parameters, request and response schemas, media types, examples, and security requirements.
- Backend declarations generate the implemented OpenAPI document, but implementation must not silently override frozen Markdown semantics.
- A conflict requires review. Until resolved through the approved change-control process, the frozen semantic contract prevails and the implementation is non-conformant.
- OpenAPI must not introduce a product feature, state, endpoint, field, or authorization behavior absent from the approved v1 contracts.

## Schema naming

- Component schema names use stable PascalCase, such as `UserResponse`, `ValidationError`, and `Pagination`.
- Names express API meaning rather than framework, ORM, database-table, or internal module names.
- Request, response, summary, and detail schemas are distinct when their allowed fields or security exposure differ.
- Shared schemas are defined once under components and reused with references rather than copied.
- Exact financial and high-precision decimals are described as JSON strings with appropriate formats, patterns, and examples; they must not be documented as binary floating-point numbers.
- Requiredness, nullability, defaults, bounds, UUIDs, RFC 3339 timestamps, ISO dates, and enum values must match the frozen contracts.

## Operation IDs

- Every operation has an explicit, unique, stable `operationId` using lowerCamelCase.
- Names describe the domain operation and avoid generated handler names or implementation details.
- Examples include `login`, `refreshAccessToken`, `getCurrentUser`, `updateCurrentUser`, `listAdminUsers`, and `updateAdminUserRoles`.
- Renaming an existing `operationId` is treated as a compatibility-affecting change because generated clients may depend on it.

## Tags

Operations use a small, stable domain-oriented tag vocabulary. Authentication operations use `Authentication`; administrative account operations use `Administration`. Later contracts may approve tags aligned to frozen domain areas. Tags must not expose internal package structure or create undocumented product groupings.

Each operation should have one primary tag. Additional tags require a documentation use case and review to prevent duplicate or confusing navigation.

## Examples

- Contracted requests, successes, and material errors have representative examples.
- Examples conform to actual schemas, envelopes, formats, enum values, and decimal-string conventions.
- Examples use unmistakably synthetic UUIDs, emails, names, market values, and tokens.
- Examples never contain real secrets, access or refresh tokens, cookie values, credentials, provider keys, production hostnames, or personal data.
- Authentication examples use placeholders such as `string`, `<access_token>`, or redacted cookie notation. Normal JSON examples never contain raw refresh tokens.
- Example data must not imply unsupported forecasts, brokerage execution, or other out-of-scope behavior.

## Security schemes

Bearer JWT authentication is represented as a reusable HTTP bearer security scheme with `type: http`, `scheme: bearer`, and `bearerFormat: JWT`. Protected operations explicitly apply that scheme.

Authentication endpoints that do not require access tokens explicitly omit the bearer security requirement; they must not accidentally inherit a global requirement. Refresh-cookie transport and cookie requirements are documented on the relevant operations without representing the raw refresh token in examples. Role, ownership, current account-state, and last-active-admin rules remain semantic authorization obligations even where OpenAPI cannot fully express them.

## Shared error schemas

The standard error envelope, error object, and field-diagnostic shape are reusable component schemas. Operations reference the stable codes in `ERROR_CATALOG_V1.md` and document only the applicable subset. Implementations must not generate framework-default validation or exception bodies that bypass the standard envelope.

Every documented error response includes the appropriate HTTP status, `application/json`, standard envelope reference, safe examples, and `X-Request-ID` response header. Security-sensitive endpoints may use intentionally generic examples.

## Shared pagination schemas

The collection pagination object is a reusable component with:

- one-based `page`;
- `page_size` with default `50` and maximum `200`;
- non-negative `total_items`; and
- non-negative `total_pages`, including `0` for an empty collection.

Common pagination query parameters should also be reused where the framework permits without obscuring endpoint-specific documentation. Each paginated operation still documents its default stable sort and allowed filter and sort fields. Collection schemas compose their typed data array, shared pagination object, and response metadata without duplicating the pagination definition.

## Compatibility checks

CI will later generate OpenAPI deterministically and compare it with the reviewed contract representation to detect unintended changes. Compatibility checks must identify at least:

- removed or changed paths, methods, parameters, operations, request bodies, responses, or security requirements;
- newly required request fields or narrowed accepted values;
- removed, renamed, retyped, or newly nullable/non-nullable response fields;
- changed enum values, defaults, bounds, formats, decimal representation, or operation IDs;
- changed status codes, media types, envelopes, pagination behavior, or stable error codes; and
- accidental schema duplication or exposure of internal/security fields.

Automated diff classification informs review but does not replace semantic review. Additive changes can still be breaking when clients exhaustively match enums, rely on authorization behavior, or process strict response schemas.

## Documentation generation

FastAPI-generated OpenAPI is the input to generated reference documentation once implementation begins. Generated reference material must link or otherwise preserve the governing semantic context from the frozen Markdown contracts. Generation is deterministic for the same reviewed source, excludes internal-only routes and schemas, and is validated before publication.

Published documentation must clearly identify API version, environment/base URL, authentication requirements, supported media type, examples, errors, pagination, and deprecation status. Interactive documentation must not ship with real credentials or pre-populated personal data.

## Contract testing

Later automated contract tests will validate that:

- implemented routes and generated OpenAPI agree;
- requests and responses conform to documented schemas and `application/json` behavior;
- standard success, collection, error, and request-ID envelopes are used;
- authentication and access-token exemptions match each operation;
- representative authorization, ownership, status, and last-active-admin rules hold;
- decimal strings, UUIDs, dates, UTC timestamps, enum values, pagination, and validation details match the contract;
- refresh tokens are not exposed in ordinary JSON; and
- examples validate against their referenced schemas.

Contract tests supplement domain, security, integration, and end-to-end tests; they do not prove financial correctness, ownership isolation, token security, or audit completeness by themselves.

## Review and approval

OpenAPI-affecting changes require review by the owners of the affected domain and API contract. Security-sensitive authentication or authorization changes require security-focused review. Reviewers compare generated detail against the frozen Markdown semantics, v1 scope, database constraints, error catalog, and compatibility report.

An OpenAPI change is approved only when its semantic intent is already approved, its examples and shared schemas conform, compatibility impact is understood, and required tests are present. Generated output must not be hand-edited to conceal a mismatch with implementation.

## Deprecation

Deprecated operations, parameters, or schemas use OpenAPI deprecation metadata and human-readable documentation that identifies the replacement, migration guidance, approval reference, and support window. Deprecation does not permit semantic breakage during the support window. Removal from `/api/v1` is breaking unless an approved ADR explicitly authorizes the exception.

## Change control

- Non-breaking implementation detail changes still require generated-document review and CI compatibility checks.
- Breaking changes require a new API version or an approved ADR.
- The ADR must explain the constraint or risk, affected clients and semantics, migration and rollout, compatibility consequences, and contract updates.
- Frozen Markdown and machine-readable representations are updated together through review; neither may silently lag an approved semantic change.
- Security fixes follow the frozen exception process and receive explicit compatibility and disclosure review.
- Convenience, framework defaults, speculative future use, or generated-schema behavior are not sufficient reasons to alter frozen v1 semantics.
