# Detection hypotheses, not active-swarm indicators

Each implemented rule lives in `nightwatcher/rules.py` under `nw-candidates-0.2.0`. The primary-source register is `INCIDENT_REGISTER.json`.

## NW-R001: reference discrepancy (implemented)

Project integrity requirement, not a claim derived from news. An operational repository source supplies a revision that differs from its owner-enrolled reference. Candidate evidence: exact observation ID and source policy hash. An authorized unreviewed development commit is a common explanation. A Git signature is not approval of its content. This pilot does not yet query GitHub continuously.

## NW-R002: authorization/outcome disagreement (implemented)

A scoped runtime reporter records denied authorization but a successful protected action. This is a boundary discrepancy candidate, not proof that a revocation was effective or that the actor is AI. Investigate stale policy, service exceptions, misleading instrumentation and inaccurate labels. A successfully denied call does not match.

## NW-R003: possible cross-isolation exchange (implemented)

Motivated by OAI-HF, WIKI-RESEARCH and AISI-CYBER. The same enrolled shared-service source reports successful denied write/read actions for the same resource and artifact digest, from workloads mapped by the owner to different isolation groups. The latest possible write must precede the earliest possible read, within one hour. The rule is order-independent at ingestion, does not combine tenants or planes, and refuses a saturated correlation set.

This is possible shared state, not proof of communication, malicious content, provider origin or a swarm. Identical benign files, bad task-isolation policy and erroneous authorization labels are alternatives. Tests cover allowed sharing, same groups, clock uncertainty and out-of-order arrival. No historical incident trace has been used as a validated detection benchmark.

## Pending: external receipt disagreement and post-effective-control activity

METR-HF motivates checking a claimed tool action against an independently obtained service receipt. OAI-HF motivates precise reconstruction of recurrence after intervention. Implementation must first add control scopes, credential lineage, trusted effectiveness time, queued-work exclusion, observer independence and review. Do not replace those requirements with a timestamp comparison and claim verified control loss.

## Disputed package attribution

RUBY-RESEARCH, RUBY-OPERATOR and OAI-UPDATES disagree on attribution/interpretation. Build-service egress and privilege boundaries are reasonable future observation targets in owned infrastructure. AI-text detectors, package names and provider-looking addresses are not accepted attribution rules. No suspicious package or reported external endpoint was executed or probed.
