"""Disposable unit/in-process tests. No remote systems or live attack fixtures."""
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from nightwatcher.api import create_app
from nightwatcher.contracts import Enrollment,Event
from nightwatcher.store import Store,Rejected,canonical,sha

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'evidence.sqlite3';self.app=create_app(self.path)
        self.store=self.app.state.store
        self.owner_token=self.store.issue_local('one');self.reader_token=self.store.issue_local('one','reader')
        self.owner=self.store.authenticate(self.owner_token)
        self.client=TestClient(self.app);self.addCleanup(self.client.close)
        self.policy={'source_id':'runtime1','plane':'operational','trust_domain':'owner-runtime','kind':'runtime','resources':['local-service'],
                     'workloads':{'worker1':'zone1','worker2':'zone2'},'max_silence_seconds':5}
        self.token=self.enroll(self.policy)
    def auth(self,token):return {'Authorization':'Bearer '+token}
    def enroll(self,policy,token=None):
        r=self.client.post('/v1/sources',json=policy,headers=self.auth(token or self.owner_token));self.assertEqual(r.status_code,201,r.text)
        return r.json()['collector_token']
    def event(self,**kw):
        e={'schema_version':1,'event_id':'event-1','event_time':datetime.now(timezone.utc).isoformat(),'time_uncertainty_ms':0,
           'action':'runtime_observed','actor':'self','workload':'worker1','resource':'local-service','outcome':'success','authorization':'allowed','receipt_id':'test-only'}
        e.update(kw);return e
    def send(self,e,token=None):return self.client.post('/v1/events',json=e,headers=self.auth(token or self.token))
    def export(self,**params):return self.client.get('/v1/export',params=params,headers=self.auth(self.owner_token)).json()
    def process(self):return self.store.process('one')
    def test_anonymous_denied(self):self.assertEqual(self.client.get('/v1/status').status_code,401)
    def test_reader_cannot_ingest(self):self.assertEqual(self.send(self.event(),self.reader_token).status_code,403)
    def test_collector_cannot_read(self):self.assertEqual(self.client.get('/v1/export',headers=self.auth(self.token)).status_code,403)
    def test_owner_cannot_impersonate_collector(self):self.assertEqual(self.send(self.event(),self.owner_token).status_code,403)
    def test_source_spoof_rejected(self):self.assertEqual(self.send(self.event(source_id='other')).status_code,422)
    def test_tenant_spoof_rejected(self):self.assertEqual(self.send(self.event(org_id='other')).status_code,422)
    def test_plane_spoof_rejected(self):self.assertEqual(self.send(self.event(plane='operational')).status_code,422)
    def test_unknown_resource_denied(self):self.assertEqual(self.send(self.event(resource='outside')).status_code,403)
    def test_unknown_workload_denied(self):self.assertEqual(self.send(self.event(workload='outside')).status_code,403)
    def test_action_kind_denied(self):self.assertEqual(self.send(self.event(action='report_observed')).status_code,403)
    def test_timezone_required(self):self.assertEqual(self.send(self.event(event_time='2026-09-15T00:00:00')).status_code,422)
    def test_future_time_rejected(self):self.assertEqual(self.send(self.event(event_time=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat())).status_code,422)
    def test_old_operational_event_rejected(self):self.assertEqual(self.send(self.event(event_time='2001-01-01T00:00:00Z')).status_code,422)
    def test_unknown_time_precision_rejected(self):
        e=self.event();del e['time_uncertainty_ms'];self.assertEqual(self.send(e).status_code,422)
    def test_boolean_uncertainty_rejected(self):self.assertEqual(self.send(self.event(time_uncertainty_ms=True)).status_code,422)
    def test_duplicate_idempotence(self):
        e=self.event();a=self.send(e).json();b=self.send(e).json();self.assertEqual(a['id'],b['id']);self.assertTrue(b['duplicate']);self.assertEqual(len(self.export()['events']),1)
    def test_duplicate_content_conflict(self):
        e=self.event();self.send(e);e['outcome']='failure';self.assertEqual(self.send(e).status_code,409)
    def test_persistence_new_connection(self):
        e=self.send(self.event()).json();s=Store(self.path);self.assertEqual(s.export(self.owner)['events'][0]['id'],e['id'])
    def test_transaction_rolls_back_on_ledger_failure(self):
        with patch.object(self.store,'_log',side_effect=RuntimeError('test rollback')):
            with self.assertRaises(RuntimeError):self.send(self.event())
        self.assertEqual(self.export()['events'],[])
    def test_normal_observation_no_case(self):
        self.send(self.event());self.process();self.assertEqual(self.export()['findings'],[])
    def test_denied_action_is_not_compromise(self):
        self.send(self.event(action='protected_action',outcome='denied',authorization='denied'));self.process();self.assertEqual(self.export()['findings'],[])
    def test_boundary_candidate_does_not_attribute_ai(self):
        self.send(self.event(action='protected_action',authorization='denied'));self.process();f=self.export()['findings'][0]['body'];self.assertEqual(f['ai_linkage'],'unestablished');self.assertEqual(f['control_failure'],'not_established')
    def test_lab_excluded(self):
        token=self.enroll({**self.policy,'source_id':'lab','plane':'lab'})
        self.send(self.event(action='protected_action',authorization='denied'),token);self.process();self.assertEqual(self.export()['events'],[]);self.assertEqual(self.export()['findings'],[]);self.assertEqual(len(self.export(plane='lab')['events']),1)
    def test_historical_old_allowed_not_operational(self):
        token=self.enroll({**self.policy,'source_id':'history','plane':'historical'})
        self.assertEqual(self.send(self.event(event_time='2001-01-01T00:00:00Z'),token).status_code,202);self.assertEqual(self.export()['events'],[])
    def test_public_kind_not_operational(self):
        r=self.client.post('/v1/sources',json={**self.policy,'kind':'public_report'},headers=self.auth(self.owner_token));self.assertEqual(r.status_code,422)
    def test_cross_tenant_export_isolated(self):
        self.send(self.event());other=self.store.issue_local('two','reader');r=self.client.get('/v1/export',headers=self.auth(other));self.assertEqual(r.json()['events'],[])
    def test_cross_tenant_review_denied(self):
        self.send(self.event(action='protected_action',authorization='denied'));self.process();f=self.export()['findings'][0];other=self.store.issue_local('two')
        r=self.client.post('/v1/findings/'+f['id']+'/reviews',json={'decision':'investigating','reason':'needs_original_evidence','evidence_event_ids':f['body']['event_ids']},headers=self.auth(other));self.assertEqual(r.status_code,404)
    def test_checkpoint_not_heartbeat_proof(self):
        self.send(self.event());self.assertEqual(self.store.status(self.owner)['sources'][0]['state'],'UNKNOWN')
    def test_outage_and_recovery(self):
        self.client.post('/v1/checkpoints',json={'cursor':'1','complete':True},headers=self.auth(self.token))
        self.assertEqual(self.store.status(self.owner)['sources'][0]['state'],'FRESH_COLLECTOR_REPORTED')
        real=self.store.clock;self.store.clock=lambda:real()+10
        self.assertEqual(self.store.status(self.owner)['sources'][0]['state'],'DEGRADED')
        self.client.post('/v1/checkpoints',json={'cursor':'2','complete':True},headers=self.auth(self.token))
        self.assertEqual(self.store.status(self.owner)['sources'][0]['state'],'FRESH_COLLECTOR_REPORTED')
    def test_incomplete_checkpoint_degrades(self):
        for value in [True,False]:self.client.post('/v1/checkpoints',json={'cursor':'1','complete':value},headers=self.auth(self.token))
        self.assertEqual(self.store.status(self.owner)['sources'][0]['state'],'DEGRADED')
    def test_disable_revokes_ingest_not_external_workload(self):
        r=self.client.post('/v1/sources/runtime1/disable',headers=self.auth(self.owner_token));self.assertFalse(r.json()['external_workload_stopped']);self.assertEqual(self.send(self.event()).status_code,401)
    def test_queue_backlog_visible(self):
        self.send(self.event());self.assertEqual(self.store.status(self.owner)['jobs']['pending'],1);self.process();self.assertEqual(self.store.status(self.owner)['jobs']['done'],1)
    def test_worker_retry_and_dead_letter(self):
        self.send(self.event())
        with patch('nightwatcher.store.evaluate',side_effect=RuntimeError('test error')):
            for _ in range(3):self.process()
        self.assertEqual(self.store.status(self.owner)['jobs']['dead_letter'],1)
    def test_worker_idempotence(self):
        self.send(self.event(action='protected_action',authorization='denied'));self.process();self.process();self.assertEqual(len(self.export()['findings']),1)
    def test_pagination(self):
        for i in range(3):self.send(self.event(event_id=str(i)))
        a=self.export(limit=2);self.assertIsNotNone(a['next_after']);b=self.export(after=a['next_after'],limit=2);self.assertEqual(len(a['events'])+len(b['events']),3);self.assertIsNone(b['next_after'])
    def test_bound_export_limit(self):self.assertEqual(self.client.get('/v1/export?limit=501',headers=self.auth(self.owner_token)).status_code,422)
    def test_integrity_is_not_approval(self):
        self.send(self.event());v=self.store.verify(self.owner);self.assertEqual(v['integrity'],'matches_local_chain');self.assertFalse(v['release_authorized'])
    def test_modified_payload_detected(self):
        self.send(self.event())
        with self.store.connection(True) as c:c.execute("UPDATE events SET payload='{}'")
        self.assertEqual(self.store.verify(self.owner)['integrity'],'mismatch')
    def test_suffix_deletion_needs_external_anchor(self):
        self.send(self.event());self.client.post('/v1/checkpoints',json={'cursor':'1','complete':True},headers=self.auth(self.token));head=self.store.verify(self.owner)['head']
        with self.store.connection(True) as c:c.execute('DELETE FROM ledger WHERE seq=(SELECT MAX(seq) FROM ledger)')
        self.assertEqual(self.store.verify(self.owner,head)['integrity'],'anchor_mismatch')
    def test_no_expiry_closure(self):
        self.send(self.event(action='protected_action',authorization='denied'));self.process();real=self.store.clock;self.store.clock=lambda:real()+999999
        self.assertEqual(self.store.status(self.owner)['open_candidates'],1)
    def test_review_requires_evidence(self):
        self.send(self.event(action='protected_action',authorization='denied'));self.process();f=self.export()['findings'][0]
        r=self.client.post('/v1/findings/'+f['id']+'/reviews',json={'decision':'closed','reason':'recovery_verified','evidence_event_ids':['0'*64]},headers=self.auth(self.owner_token));self.assertEqual(r.status_code,422)
    def test_browser_origin_rejected(self):self.assertEqual(self.client.get('/healthz',headers={'Origin':'https://example.com'}).status_code,403)
    def test_host_rejected(self):self.assertEqual(self.client.get('/healthz',headers={'Host':'attacker.example'}).status_code,400)
    def test_large_body_rejected(self):self.assertEqual(self.client.post('/v1/events',content='x'*33000,headers={'Content-Type':'application/json'}).status_code,413)
    def test_duplicate_json_keys_rejected(self):self.assertEqual(self.client.post('/v1/events',content='{"a":1,"a":2}',headers={'Content-Type':'application/json'}).status_code,422)
    def test_secret_not_reflected(self):
        value='ghp_'+'A'*40;r=self.send(self.event(actor=value));self.assertEqual(r.status_code,422);self.assertNotIn(value,r.text)
    def test_extra_raw_text_not_reflected(self):
        value='untrusted message; do not execute';r=self.send(self.event(message=value));self.assertEqual(r.status_code,422);self.assertNotIn(value,r.text)
    def test_security_headers(self):self.assertEqual(self.client.get('/healthz').headers['cache-control'],'no-store')
    def test_rate_limit(self):
        cl=TestClient(create_app(Path(self.tmp.name)/'rate.sqlite3',rate=1));self.addCleanup(cl.close)
        self.assertEqual(cl.get('/healthz').status_code,200);self.assertEqual(cl.get('/healthz').status_code,429)

    def test_event_deletion_detected(self):
        self.send(self.event())
        with self.store.connection(True) as c:
            c.execute('DELETE FROM jobs');c.execute('DELETE FROM events')
        self.assertEqual(self.store.verify(self.owner)['integrity'],'mismatch')
    def test_pending_job_deletion_detected(self):
        self.send(self.event())
        with self.store.connection(True) as c:c.execute('DELETE FROM jobs')
        self.assertEqual(self.store.verify(self.owner)['integrity'],'mismatch')
    def test_policy_tamper_detected(self):
        self.send(self.event())
        with self.store.connection(True) as c:c.execute("UPDATE sources SET policy='{}'")
        self.assertEqual(self.store.verify(self.owner)['integrity'],'mismatch')
    def test_finding_deletion_detected(self):
        self.send(self.event(action='protected_action',authorization='denied'));self.process()
        with self.store.connection(True) as c:c.execute('DELETE FROM findings')
        self.assertEqual(self.store.verify(self.owner)['integrity'],'mismatch')
    def test_successful_process_integrity(self):
        self.send(self.event(action='protected_action',authorization='denied'));self.process()
        self.assertEqual(self.store.verify(self.owner)['integrity'],'matches_local_chain')
    def test_failed_process_integrity(self):
        self.send(self.event())
        with patch('nightwatcher.store.evaluate',side_effect=RuntimeError('test error')):self.process()
        self.assertEqual(self.store.verify(self.owner)['integrity'],'matches_local_chain')
        self.process();self.assertEqual(self.store.verify(self.owner)['integrity'],'matches_local_chain')
    def test_boolean_version_rejected(self):self.assertEqual(self.send(self.event(schema_version=True)).status_code,422)
    def test_unicode_escaped_secret_rejected(self):
        e=self.event(actor='ghp_'+'A'*40);raw=json.dumps(e).replace('ghp_',r'\u0067hp_')
        rr=self.client.post('/v1/events',content=raw,headers={**self.auth(self.token),'Content-Type':'application/json'})
        self.assertEqual(rr.status_code,422)

    def repository_observation(self,expected=None,revision='b'*40):
        policy={**self.policy,'source_id':'repo','kind':'repository','resources':['repo:main'],
                'expected_revisions':{} if expected is None else {'repo:main':expected}}
        token=self.enroll(policy)
        self.assertEqual(self.send(self.event(action='repository_ref_observed',resource='repo:main',revision=revision),token).status_code,202)
        self.process();return self.export()['findings']
    def test_repository_reference_difference_is_candidate_only(self):
        found=self.repository_observation(expected='a'*40)
        self.assertEqual(len(found),1);self.assertEqual(found[0]['body']['rule_id'],'NW-R001')
        self.assertEqual(found[0]['body']['ai_linkage'],'unestablished')
        self.assertEqual(found[0]['body']['control_failure'],'not_established')
    def test_repository_matching_reference_no_candidate(self):
        self.assertEqual(self.repository_observation(expected='b'*40),[])
    def test_repository_without_reference_cannot_invent_change(self):
        self.assertEqual(self.repository_observation(),[])
    def test_trust_domain_payload_spoof_rejected(self):
        self.assertEqual(self.send(self.event(trust_domain='independent-witness')).status_code,422)
    def test_public_report_remains_separate_from_operational(self):
        token=self.enroll({**self.policy,'source_id':'public','kind':'public_report','plane':'public_intelligence'})
        self.assertEqual(self.send(self.event(action='report_observed'),token).status_code,202)
        self.process();self.assertEqual(self.export()['events'],[]);self.assertEqual(self.export()['findings'],[])
        self.assertEqual(len(self.export(plane='public_intelligence')['events']),1)

class SharingTests(EvidenceTests):
    # Shared helpers; only define sharing cases here (inherited tests intentionally not counted twice).
    def sharing(self,read_first=False,same_group=False,skew=0,allowed=False):
        policy={**self.policy,'source_id':'shared','kind':'shared_service','workloads':{'worker1':'zone1','worker2':'zone1' if same_group else 'zone2'}}
        token=self.enroll(policy);t=datetime.now(timezone.utc)-timedelta(seconds=30)
        w=self.event(action='shared_state_write',authorization='allowed' if allowed else 'denied',event_time=t.isoformat(),artifact_digest='a'*64)
        rd=self.event(action='shared_state_read',authorization='allowed' if allowed else 'denied',workload='worker2',event_id='read',event_time=(t+timedelta(seconds=10)).isoformat(),artifact_digest='a'*64,time_uncertainty_ms=skew)
        for e in ([rd,w] if read_first else [w,rd]):self.assertEqual(self.send(e,token).status_code,202)
        self.process();return self.export()['findings']
    def test_cross_isolation_candidate(self):self.assertEqual(len(self.sharing()),1)
    def test_out_of_order_ingestion(self):self.assertEqual(len(self.sharing(read_first=True)),1)
    def test_same_group_not_flagged(self):self.assertEqual(self.sharing(same_group=True),[])
    def test_clock_uncertainty_prevents_order_claim(self):self.assertEqual(self.sharing(skew=20000),[])
    def test_authorized_sharing_not_flagged(self):self.assertEqual(self.sharing(allowed=True),[])

# Reuse setup/helpers without inheriting already collected test methods.
for _name in list(EvidenceTests.__dict__):
    if _name.startswith('test_') and _name not in SharingTests.__dict__:setattr(SharingTests,_name,None)

if __name__=='__main__':unittest.main()
