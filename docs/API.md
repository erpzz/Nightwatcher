# Local evidence API v1

Bind: `127.0.0.1:8787`. JSON only; 32 KiB request maximum. Browser Origin headers are rejected. Requests are limited to 600 per client IP per minute in one API process, with at most 1024 tracked clients. This is a localhost pilot limit, not distributed rate limiting. There is no CORS, browser login, public web UI, arbitrary outbound URL fetcher, or shell interface.

Use `Authorization: Bearer <token>` from the private credentials file. Do not put tokens in URLs, a public issue, or browser localStorage. Owner and reader credentials belong to one organization; a collector credential is additionally bound to exactly one enrolled source.

| Method/path | Role | Purpose |
|---|---|---|
| GET /healthz | none | Service liveness only; no security-health claim. |
| POST /v1/sources | owner | Enroll immutable source scope and return a collector token once. |
| POST /v1/sources/{id}/disable | owner | Revoke that collector. Does not stop any external workload. |
| POST /v1/events | collector | Validate scope, persist event+job+ledger atomically; returns 202. |
| POST /v1/checkpoints | collector | Record reported completion/incompleteness of enrolled scope. |
| POST /v1/process | owner | Drain up to 100 jobs for this organization. |
| GET /v1/status | owner/reader | Freshness, rejected records, pending/dead-letter jobs and candidate count. |
| GET /v1/export | owner/reader | Plane-specific event pages with hashes and linked candidates. |
| GET /v1/integrity | owner/reader | Compare local chain and objects; optional separately retained head. |
| POST /v1/findings/{id}/reviews | owner | Record review status and scoped evidence references. |

An event cannot carry organization/source/trust-domain/plane overrides. Unknown keys, naive timestamps, duplicate JSON keys, non-finite numbers, known secret patterns and oversized requests are rejected without echoing their values. Source enrollment fixes allowed resources, workloads and their isolation groups, source kind, plane, expected refs and a staleness limit.

Event IDs deduplicate within organization+source. Reusing an ID with different content returns 409; a repeat of the same record returns the same internal ID. Operational events must not be older than 24 hours or more than five minutes into the future. This is an explicit pilot ingestion window; delayed historical imports need separately enrolled historical sources.

`event_time` describes the observed action, not a report's publication date or a commit's original author date. Clock uncertainty is mandatory. `artifact_digest` is a collector-supplied reference, not independently verified evidence; `payload_hash` covers the server-normalized event. Source scope is bound by `policy_hash`.

The export's `after`/`limit` pagination covers events (maximum 500). Findings are limited to 500 with an explicit `findings_truncated` flag. A full large-case export is a release gap, not silent completeness. Plane defaults to operational. No lab/history/public-intelligence event enters operational candidate rules.

Statuses: UNKNOWN means no completed checkpoint; FRESH_COLLECTOR_REPORTED means a recent collector assertion; DEGRADED means stale/incomplete; DISABLED means credentials revoked. None establishes complete security-event coverage. Candidate closure is owner-attested and recorded, not independent recovery proof.

The executable example is `tools/verify_http.py`; it creates temporary credentials, makes actual HTTP calls, restarts the service, verifies persistence and destroys the temporary environment without printing keys.
