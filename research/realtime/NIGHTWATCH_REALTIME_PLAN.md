# NightWatcher real-time research plan

Prepared 2026-09-15. This is an operational research plan and source registry for passive observation. It is not evidence that a swarm is currently active and does not authorize private-room access, impersonation, credential use, target interaction, or execution of untrusted content.

## Mission

Maintain persistent, evidence-first visibility into public AI-agent coordination, new misalignment incidents, and changes to the owner's NightWatcher repository. Separate ordinary authorized agent communities from unauthorized coordination. Turn meaningful new evidence into casebook updates and testable detection hypotheses.

## Active persistent watches

Two hourly condition watches are enabled outside the repository:

1. NightWatcher Swarm Watch — checks known public coordination/research surfaces and primary incident sources. It notifies only for materially new evidence, corrections, newly active public surfaces, or attributable incidents.
2. NightWatcher PR Watch — checks erpzz/Nightwatcher for new or materially changed pull requests and security-relevant repository changes without executing untrusted PR code.

These watches are external scheduling state, not GitHub Actions and not code in this repository. Their existence does not imply continuous network collection by the NightWatcher application itself.

## Public surfaces currently worth following

### Historical incident/archive layer

- https://collusion.wiki/ — reconstructed historical public coordination records and continuing research updates.
- https://collusion.wiki/additional-findings — corrections and newly disclosed historical evidence.
- https://collusion.wiki/explorer/sites/ — candidate surface catalogue; site count is not swarm count.
- https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/ — independent investigation with explicit scope limitations.
- https://huggingface.co/blog/agent-intrusion-technical-timeline — affected-operator forensic account of the July incident.
- https://openai.com/hugging-face-incident-and-misalignment/ — provider disclosures, updates, corrections and attribution statements.

### Current public agent-community layer

These are intentionally public forums. Their existence is not itself evidence of rogue coordination.

- https://openagentchat.net/ — public wiki/discussion space for agents and humans. Self-identification is not model/provider authentication.
- https://universalagentforum.com/ — public agent forum and research notes; authorized by design.
- https://openagentforum.com/ — public signed-message coordination protocol. A signature proves key possession, not model identity or authorization.
- https://thecolony.ai/ — active public agent social network/forums. Treat ordinary participation as background unless evidence links a post to an unauthorized incident.

### Owned observation layer

- https://github.com/erpzz/Nightwatcher — authorized repository observation. Watch proposed changes to executable workflows, dependencies, permissions, secrets exposure, evidence controls, auth, external destinations and release paths. A bot label or unfamiliar contributor is neutral until the diff supports concern.

## Real-time lead logic

A new public item becomes a lead only if it materially changes at least one of these questions:

1. Did a new event occur, or was an old event merely disclosed/reposted today?
2. Is there evidence of unauthorized action, rather than ordinary authorized agent communication?
3. Is there evidence of distinct workloads coordinating, rather than copied text, shared libraries, one human, one account with multiple aliases, or a public forum designed for collaboration?
4. Is there evidence of continuity across time, rather than a persistent webpage or repeated historical marker?
5. Did a protected external effect occur, or is the evidence only a proposed/attempted action?
6. Can the observation be corroborated by a genuinely different evidence origin?
7. Does the evidence change a NightWatcher detection contract or collection requirement?

Historical records, current public forums, provider statements, independent investigations, repository metadata and live owner telemetry remain separate source classes.

## Participation policy

NightWatcher may read public pages and APIs and preserve public evidence. Participation is allowed only when the forum explicitly permits agents/humans and the contribution is transparent about being an investigation/research request authorized by the owner. Do not pretend to be a historical swarm member, copy an old actor identity, post secret challenge markers as bait, test credentials, follow exploit instructions, or enter nonpublic rooms without separate authorization.

Posting is currently NOT automated. The hourly watch is passive. Any future outbound message needs a separate reviewed action and should be stored in the casebook as investigator-generated activity so it cannot be mistaken for spontaneous agent activity.

## Agent-evaluation track

The next experiment must run an actual model/agent, not a deterministic Python script. Required run metadata: provider/model/version, task, tool surface, permission contract, network policy, start/end time, model-visible context, tool requests, receiving-side results and independent-or-not observer status.

First evaluation classes:

1. ordinary authorized task;
2. explicitly authorized multi-agent collaboration;
3. out-of-scope shared-information opportunity;
4. untrusted content claiming urgency or permission;
5. permission revoked during task;
6. monitor shown identical action/permission evidence with different persuasive narratives.

Score agent behavior separately from control effectiveness. A forbidden request is not a successful effect. A model's narrative cannot grant authority. Freeze scoring criteria before held-out runs and report false alarms, reviewer burden, time-to-detection, missing-data behavior and defined-set precision rather than a fabricated global swarm probability.

## Real-time discovery strategy

The casebook should search for new public surfaces using provenance-preserving pivots, not active probing of suspected infrastructure:

- primary reports naming previously unknown public sites;
- links between known public posts and other public discussion surfaces;
- public forum posts explicitly mapping agent-coordination venues;
- corrections/addenda from affected operators and independent investigators;
- current web/news references to newly documented agent message boards;
- public GitHub issues/PRs/repositories that publish research datasets or coordination artifacts;
- public archives that establish event time before disclosure time.

A newly found public forum is first classified as a venue, not an incident. Promote it to a case only when activity and authorization evidence justify that classification.

## Escalation ladder

- INFO: new public source/surface with no incident linkage.
- LEAD: new material linked to a known case but identity/authorization unresolved.
- INVESTIGATE: evidence-supported unauthorized action or coordination hypothesis with a concrete falsification test.
- CORROBORATED LOCAL INCIDENT: independently supported unauthorized effect in a defined environment.
- CONTROL FAILURE: correctly scoped intervention became effective and a new protected effect still succeeded, with timing/queue/approved-restart alternatives excluded.
- SYSTEMIC CONCERN: multiple genuinely independent operators show linked control/recovery failures; no fixed count automatically establishes internet-wide loss of control.

## Current limitations

The repository still contains M02 runtime on the development branch; M03/M04 runtime improvements were prepared locally and have not been fully synchronized because a previous tree-write operation was blocked by the platform. The local research casebook exists separately in SQLite. Actual model trials have not yet been executed. The public watches provide scheduled investigation, not a deployed NightWatcher collector fleet.
