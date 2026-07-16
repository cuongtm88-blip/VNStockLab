# VNStockLab API Conventions V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Purpose

This document freezes the common HTTP API conventions for VNStockLab version 1. It applies to every v1 endpoint unless a more specific frozen contract explicitly narrows a convention. It defines transport and representation behavior; it does not add product capabilities beyond the frozen v1 scope.

## Communication model

REST over HTTPS is the default browser-to-backend communication model. Selective WebSocket use is permitted only when a specific approved contract defines the server-pushed behavior, authentication, messages, lifecycle, and failure handling. WebSockets do not replace REST as the default model.

## Base path and versioning

- All version 1 REST endpoints use the base path `/api/v1`.
- The major API version is encoded in the path. Minor, additive, backward-compatible changes do not change the base path.
- A breaking change requires a new API version or an approved Architecture Decision Record (ADR) under the frozen change-control process.
- Implementations must not reinterpret an existing field or operation while retaining the same version.

## Resource naming

- Resource paths use plural nouns and lowercase kebab-case path segments.
- Resource identifiers in paths are UUIDs and use descriptive snake_case parameter names in documentation.
- Paths model resources rather than implementation modules, database tables, or UI screens.
- Actions are used only when ordinary resource semantics are insufficient and must be explicitly contracted.

Examples:

```text
/api/v1/instruments
/api/v1/watchlists/{watchlist_id}
/api/v1/backtest-runs/{backtest_run_id}
```

## HTTP methods

| Method | Contract use |
| --- | --- |
| `GET` | Retrieve a resource or collection without changing domain state. |
| `POST` | Create a resource or invoke an explicitly contracted non-idempotent operation. |
| `PUT` | Replace the allowed representation of a resource or perform an explicitly contracted idempotent update. |
| `PATCH` | Apply a documented partial update. |
| `DELETE` | Remove or transition a resource only where the domain and retention contract permit it. |

Successful creation normally returns `201 Created` and a representation or location unless a specific contract freezes another response. Successful operations with data return `200 OK`. Successful operations intentionally returning no representation use `204 No Content`.

## Media types

- Request and response bodies use `application/json`.
- Clients sending a JSON body must use `Content-Type: application/json`.
- Clients should send `Accept: application/json`.
- Unsupported request media types return `415 Unsupported Media Type` with `unsupported_media_type`.
- JSON uses UTF-8. No alternate JSON profile is defined in version 1.

## Data representation

### Timestamps and dates

- Timestamps are RFC 3339 UTC timestamps, with the `Z` suffix. Example: `2026-07-16T08:30:00Z`.
- Calendar dates are ISO 8601 dates. Example: `2026-07-16`.
- An endpoint must document any market-date or exchange-time interpretation separately; ambiguous local timestamps are not accepted.

### UUIDs

UUIDs are represented as canonical hyphenated JSON strings and are opaque identifiers with no business meaning. Clients must not infer ordering or type information from a UUID.

### Decimal and monetary values

Exact financial and high-precision decimal values are JSON strings. Prices, money, quantities requiring fractional precision, rates, ratios, scores, and other values identified as exact by an endpoint must never depend on binary floating-point precision.

```json
{
  "price": "125000.00000000",
  "fee": "125.50000000",
  "rate": "0.0010000000"
}
```

Currency is represented separately with an uppercase ISO 4217 code where it is not unambiguously inherited.

### Booleans and nulls

- Boolean values are the JSON literals `true` and `false`; `0`, `1`, and string substitutes are not accepted.
- `null` means an explicitly absent or not-applicable value only when the field contract permits null.
- An omitted optional field and a field supplied as `null` are not assumed to have the same update semantics. Each mutable endpoint documents the distinction.
- Required fields must not be silently defaulted from `null` unless that behavior is explicitly documented.

### Enums

Enums are JSON strings using stable, case-sensitive lowercase snake_case values unless a domain contract freezes another canonical vocabulary. Unknown enum values in requests fail validation. Additive response enum values require compatibility review because clients may exhaustively match values.

## Collection queries

### Pagination

- Page-number pagination uses `page` and `page_size`.
- `page` is one-based and defaults to `1`.
- `page_size` defaults to `50` and has a maximum of `200`.
- Values outside the documented range produce `validation_failed`.
- Stable sorting, including a deterministic unique tie-breaker, is mandatory for every paginated resource.
- `total_items` is the count after authorized filtering, and `total_pages` is derived from it. An empty result has `total_items: 0` and `total_pages: 0`.

### Filtering

Filtering uses explicit, documented query parameters. Each endpoint defines allowed fields, value formats, repeated-value behavior, and combinations. Version 1 does not define an unrestricted query language.

### Sorting

The `sort` parameter selects an allowed field. Prefixing a field with `-` requests descending order; an unprefixed field requests ascending order. Every endpoint documents its allowed sort fields and default stable order. Unsupported sort fields produce a validation error.

### Search

The `q` parameter is available only where explicitly supported. Each supporting endpoint documents searched fields and normalization behavior. Its presence does not imply full-text, fuzzy, or unrestricted search.

### Field selection

Sparse fieldsets, arbitrary `fields` parameters, and client-defined response projections are not part of the general v1 contract. Endpoints return their documented representations. Any future field-selection support requires an endpoint-specific frozen contract.

## Idempotency

- `GET`, `PUT`, and `DELETE` follow HTTP idempotency semantics.
- `POST` endpoints that create financial, alert, import, or backtest operations may require `Idempotency-Key`.
- A required key is a client-generated opaque value transported in the `Idempotency-Key` header.
- Keys are scoped to the authenticated user and the specific operation.
- Repeating an accepted request with the same key and semantically equivalent payload returns the original result where applicable and must not repeat the domain effect.
- Reusing a key with a conflicting payload returns `idempotency_conflict`.
- An endpoint requiring a missing key returns `idempotency_key_required`.
- Endpoint contracts state the key requirement and retention window; absence of such a statement does not make a POST idempotent.

## Request tracing

Clients may send `X-Correlation-ID` as a valid UUID to link related calls. The service propagates an accepted value into safe logs and audit context; if absent, it establishes an internal correlation identity. Invalid values fail request validation rather than being trusted verbatim.

The service generates a unique UUID `X-Request-ID` for every request and returns it in the response header. The same value appears in `meta.request_id` for successful JSON responses or `error.request_id` for errors. A client-supplied `X-Request-ID` does not replace the server-generated value.

Neither identifier grants access and neither may contain secrets or personal data.

## Rate-limit responses

Rate limiting is applied by endpoint and security context. A rejected request returns `429 Too Many Requests` with `rate_limit_exceeded`, a normal error envelope, and `Retry-After` when a reliable retry time is known. Implementations may also return documented rate-limit headers, but clients must not require them unless a later contract freezes their names and semantics. Limits and windows are configurable operational settings and must not disclose security-sensitive detection rules.

## Authentication and authorization

Protected endpoints use:

```http
Authorization: Bearer <access_token>
```

Credentials must be sent only over HTTPS. Authentication establishes identity; authorization separately enforces roles, resource ownership, lifecycle rules, and operation permissions. User-owned data is isolated on every read, write, execution, and delivery boundary. Shared references do not transfer ownership. Denials should avoid revealing whether inaccessible resources exist when that distinction would leak information.

## Response envelopes

### Single resource

```json
{
  "data": {},
  "meta": {
    "request_id": "uuid"
  }
}
```

### Collection

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 0,
    "total_pages": 0
  },
  "meta": {
    "request_id": "uuid"
  }
}
```

The `data` member contains only the contracted resource representation. `meta` contains response metadata and must not be used to hide domain fields. A `204` response has no body and therefore no envelope.

## Error envelopes

All JSON error responses use:

```json
{
  "error": {
    "code": "stable_machine_readable_code",
    "message": "Human-readable summary",
    "details": [],
    "request_id": "uuid"
  }
}
```

`code` is the stable programmatic identifier defined in `ERROR_CATALOG_V1.md`. `message` is a safe summary intended for people and may be localized or refined without changing the code. `details` is always an array and contains only safe, structured diagnostics allowed for that error. Clients must branch on `code`, not message text.

Internal stack traces, secrets, SQL details, raw tokens, password contents, provider credentials, and security-sensitive implementation distinctions must never be exposed.

## Validation errors

Malformed JSON or an invalid request shape returns the appropriate cataloged error. Field validation normally returns `422 Unprocessable Entity` with `validation_failed`. Details may identify fields using stable request-field paths:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "One or more fields are invalid.",
    "details": [
      {
        "field": "email",
        "code": "invalid_format",
        "message": "A valid email address is required."
      }
    ],
    "request_id": "8c0645af-4e8f-45c7-b143-2b8da25f7183"
  }
}
```

Diagnostics must not echo passwords, tokens, credentials, or unsafe submitted content.

## Bulk operations

There is no general-purpose bulk API in version 1. Bulk behavior exists only where a specific frozen endpoint contract defines limits, validation, atomicity, per-item results, authorization, idempotency, and failure semantics. Clients must not infer bulk support from collection endpoints.

## Long-running operations

Long-running work such as approved imports, scans, or backtests must not hold an HTTP request or database transaction open for the duration. A specific endpoint contract defines submission, durable operation identity, state polling, terminal results, cancellation if supported, idempotency, and errors. `202 Accepted` means accepted for processing, not completed successfully. No generic long-running-operation resource is introduced by this convention.

## Deprecation

Deprecation requires an approved change record, documentation of the replacement and migration path, and a communicated support window. Deprecated fields and operations remain semantically compatible during that window. Deprecation metadata may be represented in generated API documentation, but removal from `/api/v1` is a breaking change unless an approved ADR explicitly permits it.

## Backward compatibility

Backward-compatible changes may add optional request fields, optional operations, or response fields whose addition has been reviewed for client safety. Changes to meaning, type, requiredness, authorization, numeric precision, default ordering, identifier interpretation, or existing enum behavior are potentially breaking. Security corrections may tighten behavior only through the frozen exception and ADR process.

## API documentation

Frozen Markdown contracts define product and semantic intent. Once implementation begins, the FastAPI-generated OpenAPI document provides the machine-readable implementation representation and must conform to these contracts and `OPENAPI_GOVERNANCE_V1.md`. Endpoint documentation must state authentication, authorization, parameters, allowed filters and sorts, request and response examples, statuses, stable errors, idempotency, and relevant ownership or lifecycle rules.
