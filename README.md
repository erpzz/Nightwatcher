# NIGHTWATCHER

Evidence first. Human control. Detection-only.

## What works now

This branch contains a **local evidence-service pilot**, not internet-wide surveillance. It has source-bound bearer authentication, four separated data planes, a durable event/job store, a worker, three explainable candidate rules, evidence export, collector health, owner-recorded case review, and integrity checks. No source can supply its own organization, trust domain, or plane in an event payload.

The first network validation used **one actual observation of this service**, not a fabricated attack. Actual localhost HTTP, a separate worker process, process restart, stale-source timing, recovery and credential revocation were exercised. Offline fixtures stay in disposable test databases.

**Storage is currently SQLite, not the planned PostgreSQL production backend.** See `docs/ADR-001-local-proof.md`. No Vercel deployment, external continuous collector, independent audit witness, production release, swarm attribution or verified containment is claimed.

## Run locally (Python 3.11+)

Use a trusted terminal in this checkout. Do not use production credentials.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/verify_http.py private/http-validation.json
python -m nightwatcher init
python -m nightwatcher serve
```

In a second terminal using the same environment:

```sh
python -m nightwatcher worker
```

The service binds only to `127.0.0.1:8787`. Initialization writes owner/reader credentials to `private/credentials.json`; it never prints them. Keep that directory private. These are CLI/API credentials, not browser sessions. The worker runs only while you run it. Ctrl+C stops it. Nothing in this conversation runs it continuously for you.

`docs/API.md` documents enrollment, ingestion, health, export and review. `tools/verify_http.py` is the fully runnable example. `docs/OPERATIONS.md` covers backup, recovery and boundaries.

## What the rules actually mean

- **NW-R001:** a repository revision differs from a reference set by the owner. This can be an authorized development change awaiting review.
- **NW-R002:** a collector reports a successful operation with denied authorization. This is a discrepancy to investigate, not proven AI activity.
- **NW-R003:** matching-content write/read observations cross owner-enrolled isolation groups outside the reported authorization. Clock uncertainty, ordinary permitted sharing and same-group work prevent matches.

Every result is an unreviewed candidate with evidence IDs and benign alternatives. There is no AI probability, provider attribution, automatic global verdict or automatic shutdown. Independent post-revocation control-failure verification is **not implemented**.

## Project records

`AGENTS.md` is the current execution policy. `docs/handoff/` preserves the current original handoff. `research/INCIDENT_REGISTER.json` is the new, bounded recheck of primary sources; historical reports are not a live-attack feed. `audit/` records the observed base, changes, validation and remaining gates.

The owner requested work by the current assistant; no Codex or subagent executor was used. All changes remain proposed on the working branch. Do not equate successful tests or a matching digest with owner approval.
