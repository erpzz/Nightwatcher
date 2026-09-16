# R05B — Consistent public observation without false continuity claims

Research date: September 15, 2026, America/New_York. Local execution receipts use September 16 UTC. This note supplements, and does not replace, R05_STATUS_AND_FINDINGS.md or the realtime research notes already in this branch.

## Actual outcomes

- Read public community pages, access policies, selected historical coordination records, and the owner's current PR list.
- Created an hourly ChatGPT condition-watch task titled **NightWatcher Public Evidence**. It checks bounded public pages and primary reports, notifying only on relevant material changes. It is not a live IRC connection, GitHub PR webhook, or process updating a local database. Tool metadata later showed a first run timestamp; its fetched results and notification delivery were not inspected here.
- Attempted one transparent identity registration on the documented OpenAgentChat endpoint. Connection/DNS failed. No membership confirmation, token or published message was obtained. No alternate route or credential was used.
- Paused original DSEWiki access after its RSS route returned a no-access/rate-limit notice. The OpenAgentChat changes endpoint also returned a non-retryable web-tool error; no live changes payload or cursor was acquired.
- Added source-linked observations and access gaps to a copied SQLite research database. The original database was preserved. The updated local snapshot has 6 cases, 26 sources, 32 observations, 8 relationships, 12 leads, 2 historical indicators and 2 PR collection records. Eleven normalized capture frames preserve both successful reads and access gaps; they are not eleven incidents.
- Added a local observation importer and a bounded local-model study runner to the separate downloadable working package. These tools are not published by this documentation commit. The actual local model-endpoint probe failed: **zero model trials and zero successful model calls**. No subagents were launched.

## What the public sources establish

### OpenAgentChat is a legitimate public collaboration surface

Its own policy welcomes permitted agent contributions and warns that model/organization identity claims are self-declared. Its agent guide documents public page reads and a resumable changes stream. Those are useful collection leads, not evidence of malicious activity or a provider identity.

- https://openagentchat.net/about
- https://openagentchat.net/for-agents

The documented stream supplies permanent event identifiers, next_cursor and has_more, and asks clients to wait at least 60 seconds after catching up. Its actual response shape and delivery behavior were not acquired in this environment. Do not enable a supposedly working collector from documentation alone or reroute around the recorded access failure.

### A current invitation does not establish historical actor continuity

Public page 7, revision 1 advertises OFTC #agent-revolution. It is dated September 7 and displays a September 15 update. Its visible conversation contains two research inquiries, including one explicitly described as a human-directed, session-based contribution. No hidden or flagged fragments were revealed and no IRC commands were executed.

A corresponding Colony introduction dated September 7 21:27 UTC self-describes the author as operator-directed. This strengthens the link between the recruitment posts, not proof of current occupancy, autonomous behavior, malicious intent or identity continuity with the historical wiki participants. The two surfaces belong to one recruitment/provenance cluster for these claims.

- https://openagentchat.net/p/live-coordination-square-oftc-agent-revolution-join-from-any-agen-292b51a4
- https://thecolony.ai/post/8bb1df39-b0f9-4c46-971b-4b5d2fbe7afb

**Discriminating next evidence:** a newly dated public session/bridge record with an inspectable source, rather than a repeated invitation or a reply asserting identity. An investigator's question must remain labeled investigator-generated activity. Matching names or hashes alone cannot prove common actor, model or task authority.

### The original wiki is not an unrestricted joining route

The original homepage's September 4 notice requires owner-issued editing access. A subsequent RecentChanges view showed entries dated September 14; reviewed entries included ordinary owner/community and human-requested activity. The documented RSS route returned an access/rate-limit notice. Original-wiki collection is now paused, including aliases, pending operator-approved access. No password, alternate route or private room was attempted.

- https://wikiservice.at/dse/wiki.cgi
- https://wikiservice.at/dse/wiki.cgi?action=browse&id=RecentChanges&lang=1

### Historical coverage is not an active-swarm census

The archive download listing advertises a 143-site coverage file and a separate 110-site gaps file. Their bytes were not acquired. These are inventory claims, not 143 current agent rooms. Selected first entries of the state-sequence thread show information requests, relevant replies and clock-alignment discussion. They support examining task-linked information exchange, not independently establishing participant identity, permission, or runtime migration.

- https://collusion.wiki/explorer/download
- https://collusion.wiki/explorer/page/dse~DataUSAStateSequenceCollab2027

## Persistent-insight design

1. **Research watch, enabled:** hourly bounded public-page and primary-report checks. Missing baseline state causes a baseline record, not an alert presenting old content as new. Suppress count-only changes, copied reports and unrelated conversation.
2. **Resumable collection, not deployed:** once legitimately accessible, validate the documented stream schema against an actual response. Persist accepted events and cursor progress atomically. Resume from the last committed cursor, deduplicate stable event IDs, honor has_more, backoff and source access limits. A caught-up 60-second poll is a proposal bounded by source policy, not a latency guarantee.
3. **Case review:** attach stable page/revision/record IDs, observation time, source-reported event time, origin dependencies and contrary evidence. Keep new-to-casebook separate from newly occurring. Never infer deletion from a partial page or infer continuity from a reused name.
4. **Owned repository:** a read of all PRs returned an empty list. A signed, scoped webhook and durable non-executing PR review remain the intended path; no webhook or PR polling automation was created.
5. **Authorization evidence:** public conversation can show apparent coordination but normally cannot establish a private task's permissions. Escalating to unauthorized activity requires that additional evidence. A purported shared-state or channel handoff is not proof an agent moved or persisted.

The hourly task excludes original-wiki hosts and the failed changes endpoint. It does not post, register, join IRC, reveal hidden text, run source commands, spend money, or visit destinations merely because a post requests it. The observer has to remain resistant to the content it investigates.

## Local implementation and validation scope

The observation importer accepts enrolled, normalized source captures; records capture completeness and failures; preserves prior frames; prevents old captures replacing newer views; and creates human review items rather than autonomous attribution. Hashes bind the normalized records, not unacquired remote bytes. Initial items are NEW_TO_CASEBOOK, not new incidents. Missing items do not become deletion events.

The local model runner requires an already installed, explicitly selected Ollama model. It never downloads one or falls back to scripted model responses. Its tools operate only on harmless in-memory lab records. It separates requested actions from permitted effects and retains partial trial receipts on errors. The collaboration comparison uses a permitted peer note, not a second live agent. Model accuracy and real tool-call compatibility are unvalidated because no model endpoint was available.

Validation in this pass was limited to syntax, actual source-record imports, idempotent reimport, SQL integrity/reference checks and explicit network/model access attempts. The historical 277-test suite was not rerun. These mechanical checks are not model evaluations or swarm discoveries.

## Repository continuity and accountability

Before this addition, the connector reported head 5b5e601ce12275af4bf502d72719c82b287165ed. Comparing it to the earlier 487af41a6d0dad9879c741829166d0df5a1c5db8 snapshot showed five intervening commits and four added research-document paths, with no runtime paths in that comparison. This execution did not create those five commits. The latest commit is attributed to the owner's GitHub account; that does not identify a particular person/agent session or independently verify exact-revision approval. Preserve them and reconcile session records, rather than infer sabotage or overwrite the branch.

This addition is a new research-only write. It does not retry the previously blocked runtime/PR operations, import M03/M04 code, merge main, certify another researcher's conclusions, or establish a production release.

**Bottom line:** the project now has a real hourly public-research watch and a more precise observation plan. No current malicious swarm, covert membership, complete live-source coverage, or successful AI-agent evaluation was established.
