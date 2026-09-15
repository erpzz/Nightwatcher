# NIGHTWATCHER — Research-grounded execution handoff

Prepared September 14, 2026 (America/New_York).

## What this package is

A master implementation prompt, eleven bounded Codex task cards (ten for the pilot, one for later federation), and a verified public-source reading register. It is not a running monitor, source-code release, repository audit or Vercel deployment. No private GitHub history, account configuration or live operational telemetry was inspected to create this handoff. No swarm currently active against the user was identified.

## How to use it

Give MASTER_PROMPT.md, CODEX_BACKLOG.md and SOURCE_REGISTER.json to the coordinating model. Assign one tasks/NW-XX.md card at a time to Codex, with the governing prompt and actual authorized repository context. Begin with baseline recovery and current research, then the real ingestion vertical slice. Do not begin by generating a dashboard.

This package includes no access tokens and requires no connector authorization to read. A failed connector consent flow is not evidence of compromise. Do not repeatedly retry it; finish independent work and report the exact blocker.

## Scope of integrity checks

CHECKSUMS.sha256 records the bytes of these handoff documents as generated. It does not attest to prior project code, to their benevolence, or to owner approval. Store a copy independently before using checksums as a later comparison. A malicious actor able to edit both files and their adjacent checksum list can defeat an unanchored comparison.

## Data realism

The operational interface must use real authorized observations. Historical research and synthetic tests remain explicitly separated. Unknown, disconnected, delayed, disputed, and unavailable are valid outputs. A researched public incident is not proof of present activity, and a matching pattern is not proof of AI origin.

## Deployment target

Vercel for the authenticated application; an explicitly approved durable backend/worker and evidence store for collection and analysis. The worker's hosting/access/costs and the Vercel-to-backend path must be real and verified. No worker provider is purchased or presumed in this handoff.
