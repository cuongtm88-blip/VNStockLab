# VNStockLab Data Retention and Audit V1

**Status:** Frozen
**Version:** 1.0
**Date:** 2026-07-16

## Policy basis

This document defines retention classes and behavior, not unapproved legal periods. Every duration marked **configurable** requires an approved operational, privacy, and legal policy before production. Until then, required history is preserved and no automated destructive purge is enabled.

## Retention classes

| Class | Included data | Retention rule |
| --- | --- | --- |
| R1 Permanent reference | exchanges, classifications, canonical instruments/aliases, indices/memberships, trading calendars, providers, active and retired analytical definitions | Preserve identities and effective versions permanently; archive cold versions only when transparently queryable/restorable. Instruments are never physically deleted; `active`, `suspended`, `delisted`, and `merged` lifecycle states preserve all historical references. |
| R2 Raw imported market data | import batches, raw records, corporate-action source evidence | Preserve lossless lineage; online/archive duration is configurable. Never overwrite; purge only after verified durable archive and dependency analysis. |
| R3 Normalized market data | published normalized price bars and supersession lineage | Append-only long-term authoritative market history; online/archive boundary configurable. Correct an import with a new import batch and superseding evidence, never a silent rewrite; retain traceability to historical provider data. |
| R4 Adjusted market data | adjusted bars and adjustment evidence | Retain published versions while referenced; otherwise rebuildable from retained normalized bars, actions, policy/version, and code. Archive/purge duration configurable. |
| R5 Analytical evidence | indicator results, pattern detections, levels, structure, Elliott scenarios, signal evidence, intelligence snapshots | Published/reference-dependent evidence retained. Unreferenced rebuildable material may be archived or purged under configurable policy if all inputs and implementation/configuration identity remain. |
| R6 Signals and trade plans | signals, evidence, plans, ordered targets | Preserve published decision-support history and exact evidence. Duration/configurable archive tier; never mutate to reflect later knowledge. |
| R7 Versioned configuration | strategy versions and their parameters/rules/risk rules; effective risk/analytical versions | Permanent while any execution or evidence references the version; published versions are immutable. |
| R8 Backtests | definitions, runs, frozen configurations, trades, equity points, metrics, diagnostics | Run record/configuration and published outcomes retained by configurable policy. Preserve StrategyVersion, indicator implementation version, dataset cutoff, configuration hash, and data snapshot identity or equivalent reproducibility reference. Large rebuildable child series may archive only with those reproducibility inputs preserved. |
| R9 Financial history | portfolios and portfolio transactions/corrections/reversals | Permanent financial history unless an approved erasure obligation explicitly governs; no silent editing/deletion. |
| R10 Portfolio/risk snapshots | positions, valuations, recommendations, risk snapshots | Configurable online/archive duration; rebuildable only while complete transactions, market inputs, currency context, and calculation versions remain. Referenced snapshots are retained. |
| R11 Alert evaluations | immutable evaluation contexts/outcomes/evidence | Configurable duration based on operational and user-history needs; referenced records retained. |
| R12 Delivery logs | notification attempts and safe provider diagnostics | Configurable, normally shorter than analytical evidence; retain enough for retry, support, and audit. Never retain credentials. |
| R13 AI interactions | explanation requests, evidence snapshots, results, model/template identities, safe diagnostics | Configurable privacy-conscious duration. Results remain separate from analytical truth; purge request/result together only after dependency review. |
| R14 Audit | append-only audit logs | Preserve under approved governance policy; archive duration configurable, deletion disabled through normal domain behavior. |
| R15 Security session | refresh-token hashes and rotation/revocation metadata | Active until expiry/revocation; post-terminal retention configurable for abuse detection. Raw tokens never stored. |
| R16 Temporary operations | failed temporary imports, transient staging references, safe diagnostics not required by an authoritative batch/issue | Short configurable duration. Promote required facts into R2 or quality records before cleanup. Redis remains disposable. |
| R17 User content | watchlists, alerts definitions, journal entries/reviews/attachment metadata and user-owned configuration | Retain while active and according to user archive/deletion policy, subject to financial, security, evidence, and audit dependencies. Binary attachment duration configurable. |

## Immutability and correction

Raw provider records, published bars, effective reference facts, published analytical evidence, published strategy versions and contents, published signals/plans, started execution configuration, completed execution results, portfolio transactions, terminal alert evaluations/delivery attempts, submitted AI input/results, and audit logs are immutable. Status fields may move only through documented lifecycle transitions; a terminal transition does not authorize changing the historical payload.

Corrections use a new superseding record, explicit portfolio correction/reversal, new calculation/output, or new audit clarification linked to the original. Consumers select the effective record without erasing what earlier calculations saw. There is no silent rewriting of financial history, provider history, analytical evidence, or point-in-time inputs.

Derived data may be rebuilt only when every authoritative input, data cutoff, representation/policy, definition and implementation version, parameter snapshot, configuration hash, and numeric convention remains available. A rebuild creates a new version unless it is a byte/semantics-identical restoration of lost derived storage. Published records already referenced by decisions remain addressable.

AI explanation retention does not broaden the AI analytical boundary. Explanation modules consume retained `IndicatorResult`, `Signal`, `SignalEvidence`, and `TradePlan` evidence; they must not independently derive analytical truth from raw `PriceBar` records.

## Archival and deletion

Archival moves cold immutable records to approved durable storage with checksums, a manifest, schema/version metadata, encryption, access controls, and a tested restore path. PostgreSQL retains searchable lineage or an archive locator where the domain requires resolution. Archival does not change record meaning or owner.

Deletion is deny-by-default for authoritative and referenced history. Approved jobs delete in bounded, auditable batches, prove that retention and dependency conditions are met, and record counts/ranges/checksums. Soft lifecycle states (`archived`, `retired`, `disabled`) are used for product behavior; they are not proof of physical erasure. Temporary/staging cleanup must never remove the only copy of a raw fact, diagnostic attached to a terminal failure, or evidence needed for reproducibility.

## User-account deletion

Account deletion requires a dependency inventory across identity, ownership, journal attachments, alerts, AI records, strategies, portfolio history, security records, and audit context. Personal data is minimized or pseudonymized where approved, while required financial, security, and governance facts retain stable non-identifying lineage. Shared market/analytical data is unaffected. User-owned content eligible for erasure is deleted or cryptographically made inaccessible only under an approved policy. Audit logs must not falsely lose actor/owner context; a pseudonymous stable identity may replace directly identifying fields. No cascade may erase portfolio transactions or evidence required by retained records.

## Privacy and safety

Persist only data required for v1. Diagnostics, JSONB payloads, audit summaries, AI prompts/results, attachment metadata, provider responses, and notification metadata are redacted before storage. Passwords, raw refresh tokens, provider/API/mail/Telegram credentials, and attachment contents do not enter audit or diagnostic JSON. Destinations use safe references rather than unnecessary full personal values. Access to user-owned archives and backups follows the same isolation obligations as online rows.

## Backup and restore

PostgreSQL backups must cover schema, authoritative data, immutable history, and necessary encryption/key-management references. The production policy defines configurable recovery-point and recovery-time objectives, full/incremental or WAL strategy, encryption, geographic separation, access control, monitoring, and backup retention. Redis backup is not relied on for authoritative recovery.

Restore verification is mandatory on a schedule defined by operational policy. A verification restores into an isolated environment, validates checksums and row/constraint counts, confirms representative ownership boundaries and time-series ranges, resolves evidence/supersession chains, reconciles sample portfolios and backtests, and records elapsed time against approved objectives. An untested backup is not considered a verified recovery capability.

## Audit-log policy

`audit_logs` is append-only through database permissions and application behavior. Normal application roles receive insert/select as appropriate but no update/delete path. Each record identifies time, actor or system actor, owner context, action, subject, correlation, outcome, and a safe summary. Clarification is a new linked event. Audit data is independently monitored and archived; it contains no secrets or unnecessary content payloads. Retention duration is a configurable governance decision until formally approved.
