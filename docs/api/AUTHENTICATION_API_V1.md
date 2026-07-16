# VNStockLab Authentication API V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Scope

This document freezes the version 1 API contract for login, token refresh, logout, current-user profile access, password change, and limited administrative account management. It is subordinate to the frozen product, architecture, domain, and database contracts and uses `API_CONVENTIONS_V1.md` and `ERROR_CATALOG_V1.md`.

Password recovery and public self-registration are not defined in API Contract Part 1. Their omission does not imply endpoints or product behavior.

## Security assumptions

- Production traffic uses HTTPS. Tokens and passwords must never be transmitted over plaintext production connections.
- Passwords are verified against secure password hashes and are never stored or logged in plaintext.
- Raw refresh tokens are never stored in PostgreSQL. Only secure, non-reversible refresh-token hashes and required rotation, revocation, expiry, user, and safe client-context metadata are persisted.
- Authentication failures use generic messages where revealing a distinction could enable account enumeration.
- User-owned records remain isolated to the authenticated owner. Administrative access is explicit, role-gated, and audited.
- Authentication and authorization logs, traces, diagnostics, and audit summaries exclude passwords, raw tokens, cookie values, token hashes, secrets, and unnecessary personal data.

## Token model

- The access token is a short-lived JWT used as `Authorization: Bearer <access_token>`.
- The refresh token is an opaque rotating credential used through the preferred browser cookie model described below.
- Refresh-token rotation occurs on every successful refresh. The consumed token is revoked or marked rotated and linked safely to its successor.
- Reuse of a rotated or otherwise invalidated refresh token triggers revocation of the affected token family and requires re-authentication.
- Access tokens contain only necessary claims, such as stable subject identity, necessary roles, issuer/audience, issued/expiry times, and a token identifier where required. They do not contain passwords, password hashes, refresh tokens, provider credentials, or unnecessary profile data.
- Version 1 roles are `admin` and `user`. A user may hold one or both roles.
- Exact access-token and refresh-token lifetimes are configurable deployment security settings. `expires_in` reports the issued access token's lifetime in seconds; examples use `900` without freezing that value as the deployment setting.
- Access-token revocation before expiry is not promised as a universal JWT property. Protected operations must still enforce current account state, and security-sensitive changes revoke applicable refresh sessions.

## Endpoint summary

| Method and path | Access-token authentication | Success | Purpose |
| --- | --- | --- | --- |
| `POST /api/v1/auth/login` | No | 200 | Authenticate credentials and establish a refresh session. |
| `POST /api/v1/auth/refresh` | No; refresh cookie required | 200 | Rotate the refresh token and issue a new access token. |
| `POST /api/v1/auth/logout` | No access token required; active refresh cookie identifies the browser session | 204 | Revoke the active refresh session and clear its cookie. |
| `POST /api/v1/auth/logout-all` | Yes | 204 | Revoke every refresh-token family for the current user. |
| `GET /api/v1/auth/me` | Yes | 200 | Return the current user's safe profile. |
| `PUT /api/v1/auth/me` | Yes | 200 | Update the current user's display name. |
| `POST /api/v1/auth/change-password` | Yes; refresh cookie required to preserve the current session | 200 | Change the password, rotate the current session, and revoke all other sessions. |
| `GET /api/v1/admin/users` | `admin` role | 200 | List accounts. |
| `GET /api/v1/admin/users/{user_id}` | `admin` role | 200 | Retrieve an account. |
| `PATCH /api/v1/admin/users/{user_id}/status` | `admin` role | 200 | Change account status. |
| `PUT /api/v1/admin/users/{user_id}/roles` | `admin` role | 200 | Replace account role assignments. |

## Common user representation

API-visible user status values are:

- `active` — authentication and authorized activity are permitted.
- `disabled` — authenticated activity is prohibited and refresh sessions are revoked.

Role values are `admin` and `user`. Representations never expose password hashes, refresh-token hashes, raw tokens, internal security metadata, or internal authorization storage identifiers.

## `POST /api/v1/auth/login`

Authenticates a normalized email and password. No access token is required.

### Request

```http
POST /api/v1/auth/login
Content-Type: application/json
Accept: application/json
```

```json
{
  "email": "user@example.com",
  "password": "string"
}
```

Email normalization is deterministic and applied before lookup: surrounding whitespace is removed and the email is case-normalized according to the application's documented canonicalization policy. Normalization does not authorize silently repairing an invalid email address. The original password string is used for verification and is never normalized.

### Successful response

The service sets the refresh-token cookie and returns:

```json
{
  "data": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
      "user_id": "9a3c78dc-bf58-47f5-81fc-6055d54fbe87",
      "email": "user@example.com",
      "display_name": "Example User",
      "roles": ["user"],
      "status": "active"
    }
  },
  "meta": {
    "request_id": "7bb7c908-c2c1-48e8-9ddf-9944e88fa08e"
  }
}
```

### Failure and security behavior

- An unknown email and an incorrect password return `401` with `invalid_credentials`, the same generic message, and no field diagnostics.
- A disabled account cannot establish authenticated activity. When returning `account_disabled` would reveal account existence, login returns the same generic `invalid_credentials` response used for other credential failure. Account state may be exposed as `account_disabled` only when identity is already safely established and enumeration risk is controlled.
- Malformed input returns `400 invalid_request`; field validation returns `422 validation_failed`.
- Login is rate-limited by safe combinations such as source context and normalized account key. Exceeded limits return `429 rate_limit_exceeded`; limits are configurable and must not reveal detection rules.
- Successful and security-relevant failed attempts emit safe audit events with outcome, correlation identity, and safe client context. An event records no password and does not unnecessarily preserve the submitted email.
- Neither request nor response passwords are returned, logged, placed in URLs, included in analytics, or copied to audit details.

## `POST /api/v1/auth/refresh`

Issues a new access token and rotates the refresh token. The endpoint does not require a bearer access token; the refresh cookie is the credential.

### Request

```http
POST /api/v1/auth/refresh
Accept: application/json
Cookie: <refresh-cookie>=<redacted>
```

There is no normal JSON request body and raw refresh tokens must not be placed in JSON.

### Successful response

The service replaces the refresh cookie and returns:

```json
{
  "data": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 900
  },
  "meta": {
    "request_id": "eef38dd1-f606-4f54-a4f8-66c85558ec77"
  }
}
```

### Behavior

- Rotation is atomic: a successful response consumes the presented refresh token and creates one successor in the same family.
- Reuse of a consumed token revokes the affected family, emits a security audit event, and returns a generic `401` response using `refresh_token_revoked` or `invalid_refresh_token` according to what can be safely disclosed.
- An expired token returns `401 refresh_token_expired`; a revoked token returns `401 refresh_token_revoked`; an unverifiable or missing token returns `401 invalid_refresh_token`. Implementations may collapse these to a generic code/message when distinctions create a security risk.
- A disabled account receives `403 account_disabled`; its refresh sessions are revoked.
- Successful rotation and security-relevant failure are audited without token contents or hashes.
- Concurrent refresh attempts with the same token allow only one successful rotation; another use is treated under reuse-detection policy.

## `POST /api/v1/auth/logout`

Revokes the active refresh token or its token family as defined by the authenticated browser session, clears the refresh-token cookie using matching cookie attributes, and returns `204 No Content` with no body.

```http
POST /api/v1/auth/logout
Cookie: <refresh-cookie>=<redacted>

HTTP/1.1 204 No Content
```

Repeated logout requests are safe. An absent, expired, or already-revoked refresh cookie does not reveal session existence and still results in the cookie being cleared and a `204` response. Security-relevant revocation is safely audited. The endpoint is intentionally usable without a valid access token so that an expired access token cannot prevent browser logout.

## `POST /api/v1/auth/logout-all`

Requires a valid bearer access token. It revokes all refresh-token families for the current user, including the current family, clears the refresh cookie, emits an audit event, and returns `204 No Content`.

```http
POST /api/v1/auth/logout-all
Authorization: Bearer <access_token>

HTTP/1.1 204 No Content
```

Missing or invalid access authentication returns the corresponding `401` catalog error. A disabled account receives `403 account_disabled` where its established identity can safely be reported.

## `GET /api/v1/auth/me`

Requires a valid bearer access token and returns the current safe profile.

```json
{
  "data": {
    "user_id": "9a3c78dc-bf58-47f5-81fc-6055d54fbe87",
    "email": "user@example.com",
    "display_name": "Example User",
    "roles": ["user"],
    "status": "active",
    "created_at": "2026-07-01T03:15:00Z",
    "updated_at": "2026-07-16T08:30:00Z"
  },
  "meta": {
    "request_id": "e7d74e5b-66c4-4d66-a438-d1c51557db25"
  }
}
```

The response excludes password hashes, refresh-token hashes, rotation lineage, login diagnostics, internal security metadata, and internal role records.

## `PUT /api/v1/auth/me`

Requires a valid bearer access token. It updates only `display_name`.

### Request

```json
{
  "display_name": "Updated Display Name"
}
```

`user_id`, `email`, `roles`, `status`, and password fields are not writable here. Supplying unknown or prohibited fields returns `422 validation_failed`; they are not silently ignored.

### Successful response

```json
{
  "data": {
    "user_id": "9a3c78dc-bf58-47f5-81fc-6055d54fbe87",
    "email": "user@example.com",
    "display_name": "Updated Display Name",
    "roles": ["user"],
    "status": "active",
    "created_at": "2026-07-01T03:15:00Z",
    "updated_at": "2026-07-16T08:35:00Z"
  },
  "meta": {
    "request_id": "3696506e-4550-42e6-a7b2-fefefc9e485a"
  }
}
```

No version field is exposed in this Part 1 contract. Therefore this limited profile update uses last-write behavior for `display_name`. The accepted update advances `updated_at` and is audited where required by the baseline. Optimistic concurrency must not be claimed unless a version or precondition field is formally added through change control.

## `POST /api/v1/auth/change-password`

Requires a valid bearer access token and the current refresh cookie so the current browser session can be preserved through rotation.

### Request

```json
{
  "current_password": "current-secret",
  "new_password": "new-secret"
}
```

The exact minimum length and complexity are configurable security settings. Contract failures remain stable: structurally invalid password input returns `422 validation_failed`; a current password that cannot be accepted returns `401 invalid_credentials` with a generic message and no password diagnostics.

### Successful response

The password hash is replaced securely, the current refresh token is rotated, every other refresh-token session is revoked, and the response supplies a new access token:

```json
{
  "data": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 900
  },
  "meta": {
    "request_id": "09b171ad-aec0-40eb-ad2d-e216ea93804e"
  }
}
```

The rotated current refresh token is returned only through the secure cookie. If the current refresh session cannot be safely rotated, the password change does not claim session preservation and the operation fails atomically with the applicable authentication or conflict error.

Success and security-relevant failure are audited with safe outcome context. Current and new passwords are never logged, echoed, retained in diagnostics, or included in audit payloads.

## Administrative account endpoints

These are contract summaries only. Every endpoint requires a valid access token with the `admin` role; otherwise it returns `401` authentication errors or `403 admin_role_required`. All successful changes and denied or security-relevant attempts are audited.

### `GET /api/v1/admin/users`

Returns the standard collection envelope and supports:

- `page` and `page_size` under the common pagination policy;
- `q` search over documented safe account fields, at minimum normalized email and display name;
- `status` filter with `active` or `disabled`;
- `role` filter with `admin` or `user`; and
- `sort` using only `email`, `display_name`, `status`, `created_at`, or `updated_at`, with `-` for descending.

The default order is `created_at` descending with `user_id` as the deterministic tie-breaker.

```http
GET /api/v1/admin/users?page=1&page_size=50&q=example&status=active&role=user&sort=-created_at
Authorization: Bearer <access_token>
```

Each item uses the safe user representation from `GET /auth/me`. Search and filters apply before pagination.

### `GET /api/v1/admin/users/{user_id}`

Returns one safe user representation. An invalid UUID returns `422 validation_failed`. An authenticated administrator requesting an unavailable administrative resource receives `404 resource_not_found`, including where disclosure should be limited.

### `PATCH /api/v1/admin/users/{user_id}/status`

Accepts only:

```json
{
  "status": "disabled"
}
```

Allowed values are `active` and `disabled`. A successful update returns `200` with the safe user representation. Disabling an account revokes all of that user's refresh-token families. A repeated request for the already-effective state is safe and returns the current representation. Invalid lifecycle changes return `409 invalid_state_transition`; field failures return `422 validation_failed`.

### `PUT /api/v1/admin/users/{user_id}/roles`

Replaces the complete role set with unique values from `admin` and `user`:

```json
{
  "roles": ["admin", "user"]
}
```

A successful update returns `200` with the safe user representation. The operation is atomic and audited. The system must reject any change that would remove the last active `admin` role from the system with `409 resource_conflict`. Duplicate, empty, or unknown role input returns `422 validation_failed`.

## Authorization behavior

- Protected endpoints first require valid authentication and then enforce current account state, roles, ownership, and domain lifecycle.
- Missing, invalid, or expired access credentials return the corresponding `401` catalog error.
- An authenticated caller lacking permission receives `403 permission_denied`, `resource_ownership_required`, or `admin_role_required` as applicable.
- Administrative resource lookup may return `404 resource_not_found` so a caller cannot infer inaccessible resource existence.
- Role or status claims in a JWT do not authorize bypassing current security state where the operation requires a current database decision.

## Cookie policy

The preferred browser model transports refresh tokens only in a cookie with these production properties:

- `Secure`;
- `HttpOnly`;
- an explicitly configured `SameSite` value appropriate to the deployed same-site architecture;
- a narrow `Path` covering the required authentication endpoints; and
- an explicit expiry consistent with the refresh-token lifetime.

The exact cookie name is an implementation constant to be documented later. It is not frozen by Part 1. The cookie must not be readable by browser JavaScript. Cookie scope must not be broader than deployment requires, and production must apply appropriate CSRF defenses consistent with the selected `SameSite` and deployment topology.

Development over `localhost` may use environment-appropriate Secure-cookie handling when the local transport cannot support production HTTPS. This exception must be explicitly environment-gated and must not weaken production requirements.

## Token storage guidance

- Browser clients should keep access tokens in memory and avoid persistent JavaScript-accessible storage where practical.
- Browser clients must not copy refresh tokens out of the HttpOnly cookie or place them in local storage, session storage, URLs, logs, or normal JSON bodies.
- Non-browser client transport is not defined in Part 1 and requires a later approved contract; implementations must not improvise raw-token JSON responses.
- Server persistence stores only refresh-token hashes and necessary safe lifecycle metadata. Backups, replicas, logs, caches, and audit records follow the same no-raw-token rule.

## Account-state behavior

- `active` accounts may authenticate and act according to their roles and ownership.
- `disabled` accounts cannot create authenticated activity. Disabling revokes all refresh-token families.
- Requests with an otherwise valid identity for a disabled account return `403 account_disabled` when safe. Login continues to use generic failure behavior where needed to prevent enumeration.
- Re-enabling an account does not restore revoked sessions; the user must authenticate again.
- Status and role changes are durable, atomic at their consistency boundary, and audited.

## Rate limiting

Login, refresh, password change, and administrative mutations are rate-limited. Limits and windows are configurable deployment security settings and may consider endpoint, account key, token family, and source context. A rejection uses `429 rate_limit_exceeded` and `Retry-After` where a reliable delay is available. Rate-limit responses must not confirm account existence or disclose abuse-detection thresholds.

## Audit events

At minimum, safe append-only audit events cover:

- login success and security-relevant login failure;
- refresh success, failure, and detected token reuse;
- logout and logout-all revocation actions;
- password-change success and security-relevant failure;
- account status changes;
- role changes, including rejected last-active-admin removal; and
- security-relevant authorization denials.

Events include occurred time, actor or safe unauthenticated/system context, subject and owner context where known, correlation identity, outcome, and a redacted summary. They never include passwords, access tokens, raw refresh tokens, token hashes, cookie values, provider credentials, or security-sensitive request payloads.

## HTTP status usage

| Status | Authentication API use |
| ---: | --- |
| 200 | Successful response containing data. |
| 204 | Successful logout or logout-all with no body. |
| 400 | Malformed request or required request-level input missing. |
| 401 | Failed or required authentication. |
| 403 | Authenticated but insufficiently authorized, or safely disclosed disabled account. |
| 404 | Administrative resource unavailable to an authenticated caller. |
| 409 | Relevant concurrency, state, idempotency, or last-active-admin conflict. |
| 422 | Field or cross-field validation failure. |
| 429 | Rate limit exceeded. |

## Acceptance criteria

The version 1 authentication API is conformant only when:

- every endpoint, method, path, status, envelope, and writable field matches this contract;
- access tokens are short-lived JWTs and refresh credentials rotate on every successful refresh;
- raw refresh tokens never enter PostgreSQL, normal JSON responses, logs, diagnostics, or audit payloads;
- refresh-token reuse revokes the affected family and is audited;
- the preferred browser refresh token uses the production cookie protections defined here;
- generic authentication failures prevent account enumeration;
- only `admin` and `user` roles and API-visible `active` and `disabled` statuses are accepted;
- user profile updates are limited to `display_name` and use the documented last-write behavior;
- password change preserves the current session by rotation and revokes every other session;
- logout operations return `204` without a body and repeated logout is safe;
- administrative changes require `admin`, preserve the last active administrator, and are audited;
- responses never expose password hashes, refresh-token hashes, raw tokens beyond the required access token, or internal security metadata; and
- password recovery and public self-registration remain explicitly undefined in Part 1.
