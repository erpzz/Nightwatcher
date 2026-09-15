# Milestone 02 validation

Executed from the local reconstructed working tree, using Python 3.13.5 on Linux and the versions in `ENVIRONMENT.json`.

1. `python -m unittest discover -s tests -v`: **95 unique tests passed**. Twenty-eight are the preserved review-guard suite, sixty-seven cover evidence/API/rules. The new HTTP unit checks use FastAPI TestClient (in-process), not real browser networking.
2. `python tools/verify_http.py <outside-repo-receipt>`: **19 actual localhost TCP/HTTP and process checks passed**. One real owned-service health observation was ingested. A separate worker process processed it. The API was terminated and a new process reopened the same database. The event persisted unchanged. Actual elapsed time produced source staleness, then a new checkpoint recovered freshness. Collector revocation denied subsequent ingest. All processes stopped.
3. The original current handoff's 19 files were copied byte-for-byte from its archive. Its checksum file covers the other 18 files. The earlier v1 archive remains supplied in the prior conversation artifacts; it is not silently republished as a current specification.
4. The locally reconstructed original files were compared to GitHub's actual blob IDs. README had no final newline and the archive's test-package docstring differed; retrieving/preserving the exact remote contents reconciled both. These were import-copy differences, not a sabotage finding.

A second review strengthened event/job/case-to-ledger reconciliation and added tests for deletion and policy changes. The first run after strengthening found that an older truncation test now failed earlier with the stronger internal-mismatch result; the tests were expanded to cover both internal deletion and an independently anchored valid-chain suffix. The final suite above passed.

Not executed: PostgreSQL, container builds, remote CI, browser or physical iPhone, power-loss tests, production backup/restore, live external collector, real autonomous-agent incidents, independent security review, Vercel deployment. No precision/recall claim is made against real-world swarms.

The receipts contain normal runtime observations and test outcomes, not private user data or secrets. The source manifest is proposed, never an owner approval or independent attestation.
