# NIGHTWATCHER — Codex backlog

Use MASTER_PROMPT.md as the governing project specification. These are task cards, not claims of completed work.

## Scheduling

NW-00 establishes source/change accountability. NW-01 public reading can run in parallel with that inventory; repository writes wait for the baseline. NW-02 freezes contracts. NW-03 and NW-04 can then proceed in separate worktrees. NW-05 starts against the frozen contract and integrates their real outputs. NW-06 validates the assembled pipeline; NW-07 develops the narrowly authorized response path. NW-08 builds the UI only after the API/logic exists. NW-09 is the pilot release gate. NW-10 is a later multi-operator expansion, requiring real consenting peers for live operation.

If parallel agents are unavailable, run sequentially. A second model session is not automatically an independently trusted reviewer. Do not invent executed agents or approvals.

## Universal task return contract

Return task ID; permitted paths; starting revision; changed paths/digest; resulting revision; tests actually run with logs; evidence/source IDs; security consequences; unapproved/unexplained changes; unresolved blockers; and the next bounded task. No unrelated refactors or changes to root authority documents. Changes invalidate approvals tied to earlier revisions.

## NW-00 — Baseline recovery and change accountability

**Depends on:** None

Recover actual artifacts and repository/deployment references. Establish what exists without assuming sabotage, prior approval or claimed test execution.

**Produces:** BASELINE_AUDIT.md; CHANGE_CONTROL.md; initial change manifest; artifact inventory; a safe baseline-comparison command with tests.

**Must prove:** A controlled unapproved file/revision change is detected and blocks release. Approved baseline updates are explicit. Missing prior history produces an unknown finding, not a clean certificate. No prior source is destroyed.

See tasks/NW-00.md.

## NW-01 — Verified incident and claim intelligence

**Depends on:** NW-00 (for repository writes; public reading may proceed independently)

Create a current claim-by-claim register and convert documented behaviors into reviewable detection hypotheses.

**Produces:** THREAT_MODEL.md; INCIDENT_REGISTER.json; source manifests; detection research briefs with alternate explanations; corrections/retraction handling.

**Must prove:** New reporting of old activity stays historical. Conflicting operator/researcher claims remain visible. Duplicated news reports are not counted as independent evidence. Source pages cannot issue tool instructions.

See tasks/NW-01.md.

## NW-02 — Durable evidence foundation and first vertical slice

**Depends on:** NW-00

Produce a working authenticated backend that ingests and preserves one genuine authorized observation, and truthfully reports source health.

**Produces:** services/api/, services/worker/ base, packages/contracts/, local containers, migration and backup/restore instructions, real HTTP receipt and exported evidence.

**Must prove:** A real permitted event survives ingestion, processing and restart with its identity/provenance intact. Cross-tenant/source spoofing is rejected. Collector outage and queue backlog are visible. Replay events cannot enter operational cases.

See tasks/NW-02.md.

## NW-03 — Authorized operational collectors

**Depends on:** NW-01, NW-02

Connect a small, explicitly scoped operational source and implement honest adapters for expansion.

**Produces:** collectors/, setup instructions, least-privilege scope manifest, cursor state, health/lag reports, integration tests and live validation receipts where available.

**Must prove:** Actual connection status is verified. Duplicate/delayed/out-of-order events, pagination, token expiry and backoff work. A heartbeat alone cannot hide missing event coverage. No employer tenant is silently connected.

See tasks/NW-03.md.

## NW-04 — Public observatory and historical research import

**Depends on:** NW-01, NW-02

Deliver a real, bounded source monitor plus separately labeled historical evidence imports—not a fake global attack feed.

**Produces:** public_collectors/, retrieval receipts, source-change alerts, historical import pipeline and a transparent current-versus-historical view.

**Must prove:** At least one real allowed public retrieval is recorded when network access permits. Source failure is visible; unchanged content is not a new incident. Non-public redirects and embedded instructions cannot alter scope. No alleged swarm is contacted.

See tasks/NW-04.md.

## NW-05 — Explainable detectors and evidence graph

**Depends on:** NW-01, NW-02; integrate real outputs from NW-03/NW-04

Implement the control-boundary, coordination, lineage, recurrence and integrity detections as testable rules with evidence-linked cases.

**Produces:** detections/, graph/case services, rule provenance and alternatives, positive/negative fixtures, documented case lifecycle.

**Must prove:** Denied actions are not successful compromises. Benign fan-out, NAT and approved redeployments do not create verified swarms. Stale telemetry does not close cases. Self-identification and provider IPs cannot produce verified attribution. Missing time precision prevents false revocation conclusions.

See tasks/NW-05.md.

## NW-06 — Independent validation and adversarial review

**Depends on:** NW-03, NW-04, NW-05

Try to falsify the detector’s conclusions and compromise its evidence/authorization boundaries using safe local tests.

**Produces:** VALIDATION_REPORT.md; exact test commands/logs/revisions; reproducible safe test suite; unresolved risks and release blockers.

**Must prove:** Results are reproducible and counts match executed tests. Detection and attribution metrics are separated. Historical/lab cases never appear as active live incidents. Critical authorization/evidence failures block release. No invented red-team or physical-device tests.

See tasks/NW-06.md.

## NW-07 — Human-controlled response and scoped stop gate

**Depends on:** NW-02, NW-05

Implement a real bounded response path for one explicitly enrolled non-production workload and practical incident/recovery runbooks.

**Produces:** response service/adapter, controlled workload, approval audit, containment/recovery verification and runbooks.

**Must prove:** The monitored workload cannot grant its own lease, alter approvals or evade the protected path in the stated scope. Denial after expiry/revocation is observed externally. Unknown network/control state is explicit. Tests do not imply unrelated cloud agents are protected.

See tasks/NW-07.md.

## NW-08 — Private Vercel application and deployment contract

**Depends on:** NW-02, NW-05; release depends on NW-06

Expose the actual cases, evidence and coverage in a usable authenticated mobile interface without changing the backend into a mock.

**Produces:** apps/web/, Vercel configuration, actual browser tests, accessible mobile layouts, deployment plan or verified preview only when authorized.

**Must prove:** All operational numbers derive from the API. No random data, hypothetical sliders, misleading "live" badges or public private logs. Test auth with actual networking. A missing backend remains a blocker, not an invented healthy screen. No permission retry loop.

See tasks/NW-08.md.

## NW-09 — Release provenance, external witness and operating handoff

**Depends on:** NW-00, NW-06, NW-07, NW-08

Bind a reviewed revision to its released artifact and set up verifiable change monitoring and recovery within the actual platform’s capabilities.

**Produces:** release manifest; source/build/deployment links; independent audit configuration; tested runbook; cost/hosting assumptions; final capability and gap register.

**Must prove:** A post-approval source/config change cannot silently reach production. A changed artifact or missing witness is flagged. Missing platform attestations are declared. No clean-history or tamper-proof guarantee exceeds evidence. The final report distinguishes implemented, tested, connected and operating.

See tasks/NW-09.md.

## NW-10 — Multi-operator evidence federation and systemic assessment

**Depends on:** NW-09 and real partner consent for live exchange.

Extend the operational pilot with authenticated, minimized cross-organization evidence sharing and a systemic-control assessment that exposes its coverage limits.

**Produces:** Evidence-exchange contract/service, peer authorization and revocation, original-source lineage, privacy controls, critical-system coverage and recovery evidence, interoperability tests.

**Must prove:** Forwarded reports cannot multiply independent witnesses; fake/revoked peers cannot contribute trusted evidence; lab partners remain labeled; no global conclusion emerges from a peer-count threshold.

See tasks/NW-10.md.
