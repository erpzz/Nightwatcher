# ADR-001: SQLite for the first executed local path, PostgreSQL still required

Status: development-only deviation; production decision unchanged.

The specification calls for PostgreSQL. The execution environment has no PostgreSQL binary, Docker or installed PostgreSQL Python driver, and a public Git clone failed with `Could not resolve host: github.com`. No alternate credentials, tunnels or paid service were used to work around that boundary.

To verify real ingestion, transactionality, idempotence, processing and restart now, the local pilot uses Python's SQLite with WAL and FULL synchronous mode. This is not an in-memory mock, but it is also not a validated PostgreSQL implementation. SQLite's documented semantics: https://www.sqlite.org/wal.html and https://www.sqlite.org/pragma.html#pragma_synchronous . No physical power-loss or filesystem durability experiment was performed.

The API/store contract isolates the backend replacement. Production remains gated on real PostgreSQL migrations, least-privilege DB roles, backup/restore, concurrency/load tests, durable worker deployment and secret handling. No PostgreSQL adapter or container is advertised as working without executing it. Do not host this SQLite development service directly on Vercel or expose it to the public internet.

Installed-package version pins identify the versions used here; they are not a hash-locked reproducible supply chain or a completed dependency security audit. Such release assurance is still required.
