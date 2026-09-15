# Milestone 02 — evidence-service pilot

Base inspected: `3e92c9b7a2c017798d07140a65b82991e40c947f` on `nightwatcher/bootstrap-nw00`. Main was unchanged at `ed98f478d270946ed2da431fdcb23ee701a1a5d7` at the starting read.

## IMPLEMENTED

Current handoff import, current execution instructions, source-grounded incident register, a local authenticated evidence API and transactional SQLite worker, candidate rules R001-R003, bounded inputs/outputs, health and export, owner-attested case review, and ledger/source checks. Missing bootstrap audit records are documented rather than backdated.

## EXECUTED AND VERIFIED

See `audit/VALIDATION.md` and its receipts. Ninety-five unique unit/in-process tests and nineteen actual localhost HTTP/process checks passed before publication preparation. Hash comparison matched all eleven observed original repository blobs after reconciling two textual differences in the local import copy. Remote Git history was not cloned into the execution container.

## NOT CONNECTED OR UNVERIFIED

PostgreSQL, a persistent external collector, Vercel, workplace telemetry, autonomous-agent runtimes, source-control audit logs, independent witness storage and owner-approved release controls. No independent review or subagents. No browser/iOS test. No internet-wide visibility or swarm attribution.

## BLOCKED / RELEASE GATES

The code-execution container could not resolve external GitHub DNS and has no PostgreSQL/server/container runtime available. Connected GitHub and research browsing are distinct, working paths; neither establishes an always-on collector in this runtime. SQLite is a declared local validation step. Branches were reported unprotected. A previous PR-creation safety block is not retried or bypassed.

## NEXT BOUNDED TASK

Implement and validate the PostgreSQL store against the same contract suite, with transactional outbox/retries, migration, backup/restore and role isolation. Then validate one approved external collector with actual DNS/TLS/API access and cursor/failure receipts. Independent release controls remain required before production. UI follows working backend/networking, not simulated counters.
