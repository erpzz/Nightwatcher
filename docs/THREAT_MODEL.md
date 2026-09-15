# Threat model and evidence standard

The useful target is unauthorized activity and loss of enforceable human authority, not the amount of AI-generated content. Legitimate automation, human-directed abuse, coordinated agents and persistent control failure are different hypotheses.

NIGHTWATCHER currently observes only explicitly enrolled sources. An ingestion token cannot grant itself a new tenant, data plane, workload or resource. The owner defines the source scope. This avoids a report promoting itself into another organization's independent evidence, but cannot establish reporter honesty.

Protected assets: source code and approved revisions; enrollment policy; normalized evidence; processing state; case history; secrets; operator authority. Adversaries may send false or replayed events, poison report text, mislabel identities, omit logs, modify the local database or compromise the development host. The last two require independent witnesses and release controls beyond the current pilot.

Trust boundaries: reporter to API; API to durable storage; storage to worker; worker to review; owner review to any future response; development branch to release. Retrieved pages and model narration are data, not authorization. There is no response-execution boundary implemented yet.

Four planes are stored at source enrollment: operational, public_intelligence, historical, lab. Rules run only for operational observations. Lab fixtures exercise the operational contract in disposable databases; they never become operational evidence in the retained local run. The executed pilot receipt contains a normal observation of the owned API.

Evidence axes remain separate: behavior, authorization, impact, coordination, AI linkage, provider attribution, persistence, containment, scope and coverage. This version emits only candidates with no AI/provider attribution. One source's false labels can create false candidates; they cannot trigger a shutdown or a global conclusion.

A stronger post-intervention finding would require a correctly scoped effective control, a demonstrably new action, known timing uncertainty, independent service-side corroboration and operator review. Queueing, propagation, different credentials and authorized redeployment must be excluded. No such detector is implemented in this release.

Internet-scale control would require independent representative evidence across consequential systems and demonstrated recovery failures. Alert counts, shared IPs and copied articles cannot establish it. There is no internet-wide coverage denominator here.

See `research/INCIDENT_REGISTER.json` for claim provenance and disagreements. These primary reports motivate tests; none is a list of currently active targets. See `research/DETECTION_BRIEFS.md` for the implemented hypotheses and their gaps.
