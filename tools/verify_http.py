"""Real localhost HTTP and process-restart validation, not an internet monitoring run.

Creates only disposable local files. Prints no credentials. Needs requirements-dev.txt.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import httpx

ROOT=Path(__file__).resolve().parents[1]

def run(output):
    checks=[];proc=None
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append({'name':name,'passed':True})
    with tempfile.TemporaryDirectory(prefix='nightwatcher-http-') as temp:
        temp=Path(temp);db=temp/'pilot.sqlite3';keys=temp/'keys.json'
        subprocess.run([sys.executable,'-m','nightwatcher','--db',str(db),'init','--credentials',str(keys)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        creds=json.loads(keys.read_text())
        # Port selection is bounded but has the usual bind/rebind race; fail rather than connect elsewhere.
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        base=f'http://127.0.0.1:{port}'
        def start():
            nonlocal proc
            proc=subprocess.Popen([sys.executable,'-m','nightwatcher','--db',str(db),'serve','--port',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            for _ in range(100):
                if proc.poll() is not None:raise RuntimeError('Local API process exited')
                try:
                    if client.get('/healthz').status_code==200:return
                except httpx.HTTPError:pass
                time.sleep(.05)
            raise RuntimeError('Local API did not start')
        def auth(token):return {'Authorization':'Bearer '+token}
        with httpx.Client(base_url=base,trust_env=False,timeout=5) as client:
            try:
                start();first_pid=proc.pid
                response=client.get('/healthz');check('actual_localhost_http',response.status_code==200)
                health_bytes=response.content
                check('anonymous_read_denied',client.get('/v1/status').status_code==401)
                policy={'source_id':'local-service-observer','plane':'operational','trust_domain':'local-process-observer',
                        'kind':'runtime','resources':['nightwatcher-local-api'],'workloads':{'local-api':'local-zone'},'max_silence_seconds':5}
                enrolled=client.post('/v1/sources',json=policy,headers=auth(creds['owner']));check('source_enrollment',enrolled.status_code==201)
                token=enrolled.json()['collector_token'];now=datetime.now(timezone.utc)
                event={'schema_version':1,'event_id':'local-health-'+str(time.time_ns()),'event_time':now.isoformat(),'time_uncertainty_ms':1000,
                       'action':'runtime_observed','actor':'local-observer','workload':'local-api','resource':'nightwatcher-local-api',
                       'outcome':'success','authorization':'allowed','receipt_id':'http-healthz-'+str(time.time_ns()),
                       'artifact_digest':hashlib.sha256(health_bytes).hexdigest()}
                ing=client.post('/v1/events',json=event,headers=auth(token));check('real_observation_accepted',ing.status_code==202);eid=ing.json()['id']
                dup=client.post('/v1/events',json=event,headers=auth(token));check('actual_http_idempotence',dup.json().get('duplicate') is True)
                status=client.get('/v1/status',headers=auth(creds['reader'])).json();check('durable_pending_job_visible',status['jobs'].get('pending')==1)
                check('heartbeat_not_complete',status['sources'][0]['state']=='UNKNOWN')
                cp=client.post('/v1/checkpoints',json={'cursor':eid,'complete':True},headers=auth(token));check('collector_checkpoint_recorded',cp.status_code==200)
                worker=subprocess.run([sys.executable,'-m','nightwatcher','--db',str(db),'worker','--once'],cwd=ROOT,capture_output=True,text=True,check=True)
                check('separate_worker_process',json.loads(worker.stdout)['processed']==1)
                before=client.get('/v1/export',headers=auth(creds['reader'])).json()
                check('normal_real_event_no_candidate',len(before['events'])==1 and before['findings']==[])
                check('normalized_hash_present',len(before['events'][0]['payload_hash'])==64)
                proc.terminate();proc.wait(timeout=10);start()
                after=client.get('/v1/export',headers=auth(creds['reader'])).json()
                check('restart_distinct_process',proc.pid!=first_pid)
                check('event_persists_across_process_restart',after['events']==before['events'])
                check('jobs_persist_across_restart',client.get('/v1/status',headers=auth(creds['reader'])).json()['jobs'].get('done')==1)
                time.sleep(5.2)
                stale=client.get('/v1/status',headers=auth(creds['reader'])).json();check('actual_elapsed_time_sensor_stale',stale['sources'][0]['state']=='DEGRADED')
                client.post('/v1/checkpoints',json={'cursor':eid,'complete':True},headers=auth(token))
                fresh=client.get('/v1/status',headers=auth(creds['reader'])).json();check('checkpoint_recovers_freshness',fresh['sources'][0]['state']=='FRESH_COLLECTOR_REPORTED')
                integrity=client.get('/v1/integrity',headers=auth(creds['owner'])).json();check('local_chain_verified_not_release_approval',integrity['integrity']=='matches_local_chain' and integrity['release_authorized'] is False)
                disabled=client.post('/v1/sources/local-service-observer/disable',headers=auth(creds['owner'])).json()
                check('disable_does_not_claim_external_stop',disabled['external_workload_stopped'] is False)
                check('revoked_collector_denied',client.post('/v1/events',json=event,headers=auth(token)).status_code==401)
                export=client.get('/v1/export',headers=auth(creds['reader'])).json()
                receipt={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'transport':'actual localhost TCP / HTTP; not TestClient',
                         'storage':'SQLite WAL / FULL on disposable local filesystem','public_network_collector_tested':False,
                         'checks':checks,'original_health_response':health_bytes.decode(),'evidence_export':export,
                         'processes_stopped':True,'limits':['No browser or iOS test.','No PostgreSQL runtime available.','One normal owned-runtime observation, not attack telemetry.','Local service and worker stop when this test ends.','The observer and API share the same host; this is not an independent forensic witness.']}
            finally:
                if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'checks_passed':len(checks),'receipt':str(output),'background_monitor_running':False}))

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python tools/verify_http.py OUTPUT_RECEIPT.json')
    run(sys.argv[1])
