"""Conservative candidate rules. Never labels a swarm, provider or verified control loss."""
import hashlib
import json
from datetime import datetime

VERSION = 'nw-candidates-0.2.0'

def _t(e):
    return datetime.fromisoformat(e['payload']['event_time']).timestamp()

def _candidate(rule, current, ids, rationale, alternatives):
    ids = sorted(set(ids))
    key = hashlib.sha256(json.dumps([VERSION, rule, current['org_id'], ids], separators=(',', ':')).encode()).hexdigest()
    return {'finding_id': key, 'rule_id': rule, 'rule_version': VERSION,
            'org_id': current['org_id'], 'plane': 'operational', 'event_ids': ids,
            'rationale': rationale, 'alternatives': alternatives,
            'ai_linkage': 'unestablished', 'provider_attribution': 'unestablished',
            'control_failure': 'not_established', 'status': 'triage'}

def evaluate(current, neighbors, policy):
    if current['plane'] != 'operational': return []
    e = current['payload']; result = []
    def add(rule, ids, why, alternatives):
        result.append(_candidate(rule, current, ids, why, alternatives))
    if e['action'] == 'repository_ref_observed':
        expected = policy['expected_revisions'].get(e['resource'])
        if expected and expected != e['revision']:
            add('NW-R001', [current['id']], 'Observed revision differs from the enrolled reference.',
                ['An authorized development commit has not been reviewed against this reference.', 'Source misconfiguration or inaccurate report.'])
    if e['action'] == 'protected_action' and e['authorization'] == 'denied' and e['outcome'] == 'success':
        add('NW-R002', [current['id']], 'Collector reports a successful operation with denied authorization.',
            ['Incorrect authorization context.', 'A service-side exception or collector error.'])
    if e['action'] in ('shared_state_read', 'shared_state_write'):
        for other in neighbors:
            o = other['payload']
            if (other['org_id'], other['source_id'], other['plane']) != (current['org_id'], current['source_id'], 'operational'): continue
            if {e['action'], o['action']} != {'shared_state_read', 'shared_state_write'}: continue
            if e['resource'] != o['resource'] or e['artifact_digest'] != o['artifact_digest']: continue
            if e['outcome'] != 'success' or o['outcome'] != 'success': continue
            if e['authorization'] != 'denied' or o['authorization'] != 'denied': continue
            groups = policy['workloads']
            if e['workload'] == o['workload'] or groups[e['workload']] == groups[o['workload']]: continue
            w, rd = (current, other) if e['action'] == 'shared_state_write' else (other, current)
            latest_write = _t(w) + w['payload']['time_uncertainty_ms'] / 1000
            earliest_read = _t(rd) - rd['payload']['time_uncertainty_ms'] / 1000
            if not 0 <= earliest_read - latest_write <= 3600: continue
            add('NW-R003', [w['id'], rd['id']], 'Reported denied write/read of matching content crosses enrolled isolation groups.',
                ['Identical benign artifact rather than communication.', 'Incorrect isolation policy or collector authorization labels.'])
    return list({f['finding_id']: f for f in result}.values())
