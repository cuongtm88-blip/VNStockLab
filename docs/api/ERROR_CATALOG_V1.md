# VNStockLab Error Catalog V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Purpose

This catalog freezes the stable machine-readable error codes for VNStockLab API version 1. Endpoint contracts reference these codes and may narrow when they apply. Codes use lowercase snake_case and retain their meaning for the lifetime of `/api/v1`.

## Error representation

Errors use the envelope defined in `API_CONVENTIONS_V1.md`:

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

The HTTP status communicates the protocol outcome; `error.code` communicates the stable API condition. `details` is always an array. “Field details” below means that safe field-level diagnostics may be included, not that they are mandatory.

Retry guidance is conditional. A client must also respect idempotency, `Retry-After`, operation state, and endpoint-specific rules before retrying a state-changing request.

## General errors

| Error code | HTTP status | Meaning | Typical causes | Retry may be appropriate | Field details |
| --- | ---: | --- | --- | --- | --- |
| `invalid_request` | 400 | The server cannot process the request as valid API input. | Malformed JSON, invalid syntax, contradictory request structure, or invalid header format. | No, until corrected. | Yes, when a safe location can be identified. |
| `validation_failed` | 422 | One or more syntactically valid fields fail the endpoint contract. | Missing required values, invalid formats, ranges, enum values, or cross-field constraints. | No, until corrected. | Yes. |
| `resource_not_found` | 404 | The requested resource is absent or is intentionally undisclosed to this caller. | Unknown UUID, inaccessible owner-scoped resource, or resource no longer addressable. | Usually no. | No. |
| `resource_conflict` | 409 | The request conflicts with an existing resource or current state. | Duplicate unique value, incompatible current state, or conflicting relationship. | Only after reading current state or changing input. | Sometimes, for safe conflicting fields. |
| `method_not_allowed` | 405 | The HTTP method is not supported for the target path. | Using `POST` where only `GET` is contracted. | No, until the method is corrected. | No. |
| `unsupported_media_type` | 415 | The request body media type is unsupported. | Missing or non-JSON `Content-Type` for a JSON request. | No, until corrected. | No. |
| `rate_limit_exceeded` | 429 | The applicable request limit has been exceeded. | Excessive login attempts, bursts, or endpoint/user limits. | Yes, after `Retry-After` or suitable backoff. | No. |
| `internal_error` | 500 | An unexpected server failure prevented completion. | Unhandled internal fault. | Possibly, with backoff and only when safe to repeat. | No. |
| `service_unavailable` | 503 | A required service is temporarily unable to process the request. | Maintenance, dependency outage, overload, or unavailable worker capacity. | Yes, with backoff and `Retry-After` when supplied. | No. |

## Authentication errors

| Error code | HTTP status | Meaning | Typical causes | Retry may be appropriate | Field details |
| --- | ---: | --- | --- | --- | --- |
| `authentication_required` | 401 | A valid authenticated identity is required. | Missing bearer access token on a protected endpoint. | Yes, after authenticating. | No. |
| `invalid_credentials` | 401 | Login credentials were not accepted. | Unknown normalized email, incorrect password, or another condition intentionally hidden to prevent enumeration. | Only after correcting credentials; repeated attempts are rate-limited. | No. |
| `invalid_access_token` | 401 | The bearer access token cannot be accepted. | Invalid signature, issuer, audience, claims, format, or otherwise unusable token. | Yes, after obtaining a valid token. | No. |
| `access_token_expired` | 401 | The access token lifetime has ended. | Expired JWT. | Yes, after a successful refresh or login. | No. |
| `invalid_refresh_token` | 401 | The refresh credential cannot be accepted. | Missing, malformed, unverifiable, or unknown refresh cookie; security-sensitive distinctions may be concealed. | Usually by logging in again, not by repeating refresh. | No. |
| `refresh_token_expired` | 401 | The refresh token lifetime has ended. | Refresh attempted after expiry. | No; re-authentication is required. | No. |
| `refresh_token_revoked` | 401 | The refresh token or its family is revoked. | Logout, logout-all, password/security action, administrative action, or rotation reuse response. | No; re-authentication is required. | No. |
| `account_disabled` | 403 | The account is disabled and cannot perform authenticated activity. | Administrative account disablement. | No, until account state changes. | No. |

Login responses must not reveal whether an email exists. Where exposing `account_disabled` during credential verification would enable account enumeration, the endpoint returns the same generic status, code, message, timing posture, and detail shape as `invalid_credentials`. `account_disabled` remains available for already-authenticated or otherwise safely established account-state handling.

## Authorization errors

| Error code | HTTP status | Meaning | Typical causes | Retry may be appropriate | Field details |
| --- | ---: | --- | --- | --- | --- |
| `permission_denied` | 403 | The authenticated caller lacks permission for the operation. | Missing capability, prohibited action, or lifecycle restriction. | No, unless authorization changes. | No. |
| `resource_ownership_required` | 403 or 404 | The operation requires ownership of a user-owned resource. | Cross-user access or mutation attempt. `404` is used when existence must be concealed. | No. | No. |
| `admin_role_required` | 403 | The operation requires the `admin` role. | A `user` caller invokes an administrative operation. | No, unless roles change. | No. |

## Concurrency and idempotency errors

| Error code | HTTP status | Meaning | Typical causes | Retry may be appropriate | Field details |
| --- | ---: | --- | --- | --- | --- |
| `idempotency_key_required` | 400 | The endpoint requires an `Idempotency-Key` header. | Omitted key on a protected financial, alert, import, or backtest creation operation. | Yes, after adding a new valid key. | No. |
| `idempotency_conflict` | 409 | An idempotency key was reused for a conflicting request. | Same user and operation key with a different semantic payload. | No with that key; reconcile or use a new key for a genuinely new operation. | No. |
| `optimistic_lock_conflict` | 409 | The resource changed since the caller's expected version. | Stale version, ETag, lock value, or contracted timestamp precondition. | Yes, after retrieving current state and reconciling. | Sometimes, for the safe concurrency field. |

## Domain-oriented generic errors

| Error code | HTTP status | Meaning | Typical causes | Retry may be appropriate | Field details |
| --- | ---: | --- | --- | --- | --- |
| `invalid_state_transition` | 409 | The requested lifecycle transition is not allowed from the current state. | Starting a completed run, publishing from an invalid state, or unsupported account transition. | Only after state changes or the request is corrected. | Sometimes, for a state field. |
| `immutable_record` | 409 | The request would modify a frozen historical record. | Editing published evidence, a started backtest configuration, financial history, or an audit fact. | No; create the contracted correction or successor instead. | Sometimes, for prohibited fields. |
| `data_quality_failure` | 422 | Required data fails documented quality rules. | Invalid market bars, unresolved mapping, inconsistent source input, or failed validation threshold. | After correcting or replacing source data. | Yes, for safe data fields or issue references. |
| `analytical_evidence_unavailable` | 409 | Required deterministic evidence cannot be resolved for the operation. | Missing indicator result, signal evidence, lineage, or point-in-time context. | Possibly after evidence generation or restoration. | No field details; safe evidence references may be supplied. |
| `strategy_version_unavailable` | 409 | The required immutable strategy version is not available for execution. | Unknown, unpublished, retired from new execution, or inaccessible strategy version. | After selecting an available version or state changes. | Sometimes, for `strategy_version_id`. |
| `insufficient_market_data` | 422 | Available validated market data is insufficient for the requested calculation. | Missing date coverage, warm-up history, timeframe, or point-in-time observations. | After data becomes available or input range changes. | Yes, for safe range/timeframe diagnostics. |
| `backtest_configuration_invalid` | 422 | A backtest configuration violates the frozen backtest contract. | Non-daily data, non-long-only behavior, invalid dates/capital/costs, or inconsistent risk settings. | No, until corrected. | Yes. |
| `operation_in_progress` | 409 | A conflicting or duplicate operation is already running. | Repeated import, scan, backtest, or state transition while active work exists. | Yes, after polling or waiting; do not resubmit blindly. | No field details; a safe operation identifier may be supplied. |

## Detail safety and stability

Field-level diagnostics use this shape:

```json
{
  "field": "email",
  "code": "invalid_format",
  "message": "A valid email address is required."
}
```

- `field` is a stable request-field path, not a database column or internal model path.
- Detail `code` values describe local diagnostics and do not replace the top-level catalog code.
- Details must not include stack traces, SQL, table or constraint names, password contents, raw tokens, credential fragments, provider secrets, or unsafe payload echoes.
- Authentication messages and detail presence must not expose whether an account, token-family member, or protected resource exists when that distinction would aid enumeration or abuse.
- An endpoint may omit otherwise permitted details when security requires less disclosure.
