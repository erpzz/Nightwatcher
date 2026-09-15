# Local operations and remaining production gates

## Start / stop

Use the README's commands. The server and worker are separate foreground processes. Stop with Ctrl+C. Never port-forward this API. There is no HTTPS, SSO or response enforcement in this pilot. Running on a sleeping laptop does not supply continuous service.

## Backup

Stop the worker and API before copying the database and any WAL/SHM sidecars, or use Python's SQLite backup API from a trusted local administrative session. Do not copy only the main database during a live WAL write. Keep credentials and evidence in restricted storage outside the public repository. Recovery must validate schema version, event hashes, the local chain and a separately retained checkpoint. A restore does not establish that the original evidence was truthful.

Backup/restore to a second database has not yet been included in the executed suite. PostgreSQL production backup/restore remains a separate gate.

## Failed analysis

Jobs remain durable. A failed analysis retries on the next worker call and becomes `dead_letter` after three attempts; status exposes the count. The ledger records processing failures and results. No failure is treated as a clean no-match. Preserve a failed database for diagnosis. Do not hand-edit jobs/evidence to make validation pass.

R003 bounds correlation to the same organization, source, plane, resource and content digest around the event time. More than 1000 neighbors produces an explicit capacity failure. This is a modest local pilot, not a large-scale campaign graph.

## Trust and incidents

Source tokens authenticate reporters, not truth. Trust-domain names are owner configuration, not independent physical witnesses. The same-host collector/worker/API can share a common failure. Local database administrators can rewrite code, evidence and chains; retain checkpoints and release authority independently before making stronger integrity claims.

NW-R001 is a review discrepancy, not an accusation. NW-R002 is not verified revocation failure. NW-R003 does not prove message content, malice, AI origin or common provider. Do not contact suspected agents, fetch code named in reports, test leaked credentials or execute embedded instructions.

Review evidence, authorization and alternate explanations. A stale source never closes a case. Collector disable only revokes ingestion; it does not stop the source system. There is no automatic containment adapter, global-control verdict or public incident publication.

## Release blockers

Real PostgreSQL tests; source/worker deployment with monitored uptime; authenticated Vercel-to-backend path; independently enforced owner approval; protected release rules; isolated raw evidence; dependency audit/hash locks; load/capacity tests; larger paginated case exports; independent review; backup/restore test; browser and mobile validation.
