"""SQLite local-pilot store; PostgreSQL release gate is explicitly still open.

One transaction commits event+job+hash-chain record. Processing results+job completion
also commit together. Filesystem/database administrators remain inside the trust boundary.
"""
from contextlib import contextmanager
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
import time
from .contracts import Enrollment, Event
from .rules import evaluate, VERSION

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()

class Rejected(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)

DDL = """
CREATE TABLE IF NOT EXISTS sources (
 org_id TEXT NOT NULL, source_id TEXT NOT NULL, policy TEXT NOT NULL,
 disabled INTEGER NOT NULL DEFAULT 0, last_seen REAL, last_complete REAL,
 cursor TEXT, incomplete INTEGER NOT NULL DEFAULT 0, rejected INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(org_id, source_id));
CREATE TABLE IF NOT EXISTS credentials (
 digest TEXT PRIMARY KEY, org_id TEXT NOT NULL, role TEXT NOT NULL,
 source_id TEXT, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS events (
 seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
 org_id TEXT NOT NULL, source_id TEXT NOT NULL, plane TEXT NOT NULL,
 policy_hash TEXT NOT NULL, payload TEXT NOT NULL, payload_hash TEXT NOT NULL, received REAL NOT NULL,
 occurred REAL NOT NULL, resource TEXT NOT NULL, artifact_digest TEXT,
 FOREIGN KEY(org_id,source_id) REFERENCES sources(org_id,source_id));
CREATE TABLE IF NOT EXISTS jobs (
 event_id TEXT PRIMARY KEY REFERENCES events(id), state TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0, error_code TEXT, processed REAL);
CREATE TABLE IF NOT EXISTS findings (
 id TEXT PRIMARY KEY, org_id TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'triage');
CREATE TABLE IF NOT EXISTS ledger (
 seq INTEGER PRIMARY KEY AUTOINCREMENT, org_id TEXT NOT NULL,
 body TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS event_scope ON events(org_id,source_id,plane,seq);
CREATE INDEX IF NOT EXISTS ledger_scope ON ledger(org_id,seq);
CREATE TABLE IF NOT EXISTS counters (name TEXT PRIMARY KEY, value INTEGER NOT NULL);
"""

class Store:
    def __init__(self, path, clock=time.time):
        self.path = Path(path); self.clock = clock
        if self.path.is_symlink(): raise ValueError('Database must not be a symlink')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as c:
            version = c.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1): raise ValueError('Unsupported database version')
            c.executescript(DDL); c.execute('PRAGMA user_version=1')
        self.path.chmod(0o600)

    @contextmanager
    def connection(self, write=False):
        c = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        c.row_factory = sqlite3.Row
        try:
            c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=FULL')
            c.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            yield c
            c.commit()
        except BaseException:
            c.rollback(); raise
        finally: c.close()

    def _log(self, c, org, record):
        prev = c.execute('SELECT digest FROM ledger WHERE org_id=? ORDER BY seq DESC LIMIT 1', (org,)).fetchone()
        prev = prev[0] if prev else '0'*64
        body = canonical(record); d = sha(prev + '\n' + body)
        c.execute('INSERT INTO ledger(org_id,body,previous,digest) VALUES(?,?,?,?)', (org, body, prev, d))

    def issue_local(self, org, role='owner'):
        if role not in ('owner', 'reader'): raise ValueError('Unsupported local role')
        token = secrets.token_urlsafe(32)
        with self.connection(True) as c:
            c.execute('INSERT INTO credentials(digest,org_id,role) VALUES(?,?,?)', (sha(token), org, role))
            self._log(c, org, {'operation':'local_credential_issued','role':role,'at':self.clock()})
        return token

    def authenticate(self, token):
        if not isinstance(token, str) or not 32 <= len(token) <= 128: raise Rejected(401, 'unauthorized')
        with self.connection() as c:
            row = c.execute('SELECT * FROM credentials WHERE digest=? AND revoked=0', (sha(token),)).fetchone()
        if row is None: raise Rejected(401, 'unauthorized')
        return {k: row[k] for k in ('org_id', 'role', 'source_id')}

    def require(self, principal, *roles):
        if principal['role'] not in roles: raise Rejected(403, 'role_not_permitted')

    def enroll(self, principal, policy: Enrollment):
        self.require(principal, 'owner')
        token=secrets.token_urlsafe(32); org=principal['org_id']; data=policy.model_dump()
        with self.connection(True) as c:
            if c.execute('SELECT 1 FROM sources WHERE org_id=? AND source_id=?', (org,policy.source_id)).fetchone():
                raise Rejected(409, 'source_already_enrolled')
            c.execute('INSERT INTO sources(org_id,source_id,policy) VALUES(?,?,?)', (org,policy.source_id,canonical(data)))
            c.execute('INSERT INTO credentials(digest,org_id,role,source_id) VALUES(?,?,?,?)', (sha(token),org,'collector',policy.source_id))
            self._log(c,org,{'operation':'source_enrolled','policy':data,'at':self.clock()})
        return {'source_id':policy.source_id,'collector_token':token,'plane':policy.plane}

    def _source(self,c,p):
        row=c.execute('SELECT * FROM sources WHERE org_id=? AND source_id=?', (p['org_id'],p['source_id'])).fetchone()
        if row is None or row['disabled']: raise Rejected(403,'source_disabled_or_unknown')
        return row, json.loads(row['policy'])

    def ingest(self,p,event: Event):
        self.require(p,'collector'); body=event.model_dump(mode='json'); payload=canonical(body)
        now=self.clock(); at=event.event_time.timestamp()
        with self.connection(True) as c:
            row, policy=self._source(c,p)
            if event.resource not in policy['resources'] or event.workload not in policy['workloads']:
                raise Rejected(403,'event_outside_enrolled_scope')
            actions={'repository':{'repository_ref_observed'},'runtime':{'runtime_observed','protected_action'},
                     'shared_service':{'shared_state_read','shared_state_write'},'public_report':{'report_observed'}}
            if event.action not in actions[policy['kind']]: raise Rejected(403,'action_outside_source_kind')
            if at>now+300 or (policy['plane']=='operational' and at<now-86400):
                raise Rejected(422,'event_time_outside_plane_window')
            eid=sha(canonical([p['org_id'],p['source_id'],event.event_id])); ph=sha(payload)
            old=c.execute('SELECT payload_hash FROM events WHERE id=?',(eid,)).fetchone()
            if old:
                if not hmac.compare_digest(old[0],ph): raise Rejected(409,'event_id_content_conflict')
                return {'id':eid,'duplicate':True,'plane':policy['plane']}
            c.execute('INSERT INTO events(id,org_id,source_id,plane,policy_hash,payload,payload_hash,received,occurred,resource,artifact_digest) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                      (eid,p['org_id'],p['source_id'],policy['plane'],sha(row['policy']),payload,ph,now,at,event.resource,event.artifact_digest))
            c.execute('INSERT INTO jobs(event_id) VALUES(?)',(eid,))
            c.execute('UPDATE sources SET last_seen=? WHERE org_id=? AND source_id=?',(now,p['org_id'],p['source_id']))
            self._log(c,p['org_id'],{'operation':'event_ingested','id':eid,'payload_hash':ph,'source_id':p['source_id'],'plane':policy['plane'],'at':now})
        return {'id':eid,'duplicate':False,'plane':policy['plane']}

    def rejected(self,p):
        if p and p['role']=='collector':
            with self.connection(True) as c:
                c.execute('UPDATE sources SET rejected=rejected+1 WHERE org_id=? AND source_id=?',(p['org_id'],p['source_id']))

    def checkpoint(self,p,cp):
        self.require(p,'collector')
        with self.connection(True) as c:
            self._source(c,p)
            c.execute('UPDATE sources SET cursor=?,incomplete=?,last_complete=CASE WHEN ? THEN ? ELSE last_complete END WHERE org_id=? AND source_id=?',
                      (cp.cursor, int(not cp.complete), int(cp.complete), self.clock(), p['org_id'], p['source_id']))
            self._log(c,p['org_id'],{'operation':'collector_checkpoint','source_id':p['source_id'],'cursor':cp.cursor,'complete':cp.complete,'at':self.clock()})
        return {'status':'collector_reported_complete' if cp.complete else 'degraded','independently_verified':False}

    def disable(self,p,source_id):
        self.require(p,'owner')
        with self.connection(True) as c:
            result=c.execute('UPDATE sources SET disabled=1 WHERE org_id=? AND source_id=?',(p['org_id'],source_id))
            if not result.rowcount: raise Rejected(404,'source_not_found')
            c.execute('UPDATE credentials SET revoked=1 WHERE org_id=? AND source_id=?',(p['org_id'],source_id))
            self._log(c,p['org_id'],{'operation':'source_disabled','source_id':source_id,'at':self.clock()})
        return {'status':'source_disabled','external_workload_stopped':False}

    @staticmethod
    def decode(row):
        e=dict(row);e['payload']=json.loads(e['payload']);return e

    def process(self,org,limit=100):
        completed=0
        for _ in range(min(max(limit,1),100)):
            eid=None
            try:
                with self.connection(True) as c:
                    row=c.execute("SELECT e.* FROM events e JOIN jobs j ON j.event_id=e.id WHERE e.org_id=? AND j.state='pending' ORDER BY e.seq LIMIT 1",(org,)).fetchone()
                    if row is None: break
                    cur=self.decode(row);eid=cur['id']
                    sr=c.execute('SELECT policy FROM sources WHERE org_id=? AND source_id=?',(org,cur['source_id'])).fetchone(); policy=json.loads(sr[0])
                    if sha(sr[0])!=cur['policy_hash'] or sha(row['payload'])!=cur['payload_hash']:
                        raise Rejected(409,'evidence_or_policy_integrity_mismatch')
                    neighbors=[]
                    if cur['payload']['action'] in ('shared_state_read','shared_state_write'):
                        # Bounded single-source pilot. Refuse saturation rather than silently omit evidence.
                        rows=c.execute('SELECT * FROM events WHERE org_id=? AND source_id=? AND plane=? AND resource=? AND artifact_digest=? AND occurred BETWEEN ? AND ? ORDER BY seq LIMIT 1001',(org,cur['source_id'],cur['plane'],cur['payload']['resource'],cur['payload']['artifact_digest'],cur['occurred']-4200,cur['occurred']+4200)).fetchall()
                        if len(rows)>1000: raise Rejected(409,'correlation_capacity_exceeded')
                        for x in rows:
                            if sha(x['payload'])!=x['payload_hash'] or x['policy_hash']!=cur['policy_hash']:raise Rejected(409,'neighbor_integrity_mismatch')
                        neighbors=[self.decode(x) for x in rows if x['id']!=eid]
                    candidates=evaluate(cur,neighbors,policy)
                    for finding in candidates:
                        result=c.execute('INSERT OR IGNORE INTO findings(id,org_id,body) VALUES(?,?,?)',(finding['finding_id'],org,canonical(finding)))
                        if result.rowcount: self._log(c,org,{'operation':'candidate_created','finding':finding,'at':self.clock()})
                    c.execute("UPDATE jobs SET state='done',error_code=NULL,processed=? WHERE event_id=?",(self.clock(),eid))
                    self._log(c,org,{'operation':'event_processed','id':eid,'rule_version':VERSION,'candidate_count':len(candidates),'at':self.clock()})
                    completed+=1
            except Exception as exc:
                if eid is None: raise
                code=exc.code if isinstance(exc,Rejected) else 'analysis_failed'
                with self.connection(True) as c:
                    c.execute("UPDATE jobs SET attempts=attempts+1,error_code=?,state=CASE WHEN attempts>=2 THEN 'dead_letter' ELSE 'pending' END WHERE event_id=?",(code,eid))
                    job=c.execute('SELECT attempts,state FROM jobs WHERE event_id=?',(eid,)).fetchone()
                    self._log(c,org,{'operation':'event_processing_failed','id':eid,'attempts':job['attempts'],'state':job['state'],'error_code':code,'at':self.clock()})
                break
        return {'processed':completed,'scope_org':org}

    def status(self,p):
        self.require(p,'owner','reader');now=self.clock();org=p['org_id']
        with self.connection() as c:
            sources=[]
            for row in c.execute('SELECT * FROM sources WHERE org_id=? ORDER BY source_id',(org,)):
                policy=json.loads(row['policy']);age=now-row['last_complete'] if row['last_complete'] else None
                state='DISABLED' if row['disabled'] else 'UNKNOWN' if age is None else 'DEGRADED' if row['incomplete'] or age>policy['max_silence_seconds'] else 'FRESH_COLLECTOR_REPORTED'
                sources.append({'source_id':row['source_id'],'plane':policy['plane'],'state':state,'checkpoint_age_seconds':age,
                                'last_received_at':row['last_seen'],'cursor':row['cursor'],'rejected_events':row['rejected'],
                                'completeness':'not_independently_verified'})
            counts=dict(c.execute('SELECT j.state,COUNT(*) FROM jobs j JOIN events e ON e.id=j.event_id WHERE e.org_id=? GROUP BY j.state',(org,)).fetchall())
            oldest=c.execute("SELECT MIN(e.received) FROM events e JOIN jobs j ON j.event_id=e.id WHERE e.org_id=? AND j.state='pending'",(org,)).fetchone()[0]
            findings=c.execute("SELECT COUNT(*) FROM findings WHERE org_id=? AND status NOT IN ('closed','dismissed')",(org,)).fetchone()[0]
        return {'sources':sources,'jobs':counts,'oldest_pending_seconds':None if oldest is None else now-oldest,
                'open_candidates':findings,'global_control_status':'not_assessable','backend':'sqlite_local_pilot'}

    def export(self,p,plane='operational',after=0,limit=100):
        self.require(p,'owner','reader');org=p['org_id']
        with self.connection() as c:
            rows=c.execute('SELECT * FROM events WHERE org_id=? AND plane=? AND seq>? ORDER BY seq LIMIT ?', (org,plane,after,limit+1)).fetchall()
            events=[self.decode(x) for x in rows[:limit]]
            for e in events:
                policy=json.loads(c.execute('SELECT policy FROM sources WHERE org_id=? AND source_id=?',(org,e['source_id'])).fetchone()[0])
                if sha(canonical(policy))!=e['policy_hash'] or sha(canonical(e['payload']))!=e['payload_hash']:raise Rejected(409,'evidence_integrity_mismatch')
                e['source_trust_domain']=policy['trust_domain'];e['external_artifact_verified']=False
            fs=[dict(x) for x in c.execute('SELECT * FROM findings WHERE org_id=? ORDER BY id LIMIT 501',(org,))] if plane=='operational' else []
            for f in fs: f['body']=json.loads(f['body'])
            ledger=c.execute('SELECT digest FROM ledger WHERE org_id=? ORDER BY seq DESC LIMIT 1',(org,)).fetchone()
            n=c.execute('SELECT COUNT(*) FROM ledger WHERE org_id=?',(org,)).fetchone()[0]
        return {'schema_version':1,'plane':plane,'events':events,'findings':fs[:500],'findings_truncated':len(fs)>500,'next_after':events[-1]['seq'] if len(rows)>limit else None,
                'checkpoint':{'entries':n,'head':ledger[0] if ledger else '0'*64},
                'limits':'Local hash chain, not an independent witness. Event hashes cover normalized records, not external source bytes.'}

    def verify(self,p,expected_head=None):
        self.require(p,'owner','reader');prev='0'*64;logged={};policies={};created={};reviews={};processed=set();job_history={}
        mismatch={'integrity':'mismatch','release_authorized':False}
        try:
            with self.connection() as c:
                for row in c.execute('SELECT * FROM ledger WHERE org_id=? ORDER BY seq',(p['org_id'],)):
                    if row['previous']!=prev or row['digest']!=sha(prev+'\n'+row['body']):return mismatch
                    prev=row['digest'];record=json.loads(row['body']);op=record['operation']
                    if op=='event_ingested':
                        logged[record['id']]=record;job_history[record['id']]={'state':'pending','attempts':0,'error_code':None}
                    if op=='source_enrolled':policies[record['policy']['source_id']]=sha(canonical(record['policy']))
                    if op=='candidate_created':created[record['finding']['finding_id']]=canonical(record['finding'])
                    if op=='owner_review_recorded':reviews[record['finding_id']]=record['decision']
                    if op=='event_processed':
                        processed.add(record['id']);job_history[record['id']].update(state='done',error_code=None)
                    if op=='event_processing_failed':
                        job_history[record['id']]={'state':record['state'],'attempts':record['attempts'],'error_code':record['error_code']}
                actual={}
                for row in c.execute('SELECT * FROM events WHERE org_id=?',(p['org_id'],)):
                    rec=logged.get(row['id'])
                    if (rec is None or sha(row['payload'])!=row['payload_hash'] or rec['payload_hash']!=row['payload_hash']
                        or rec['source_id']!=row['source_id'] or rec['plane']!=row['plane']
                        or policies.get(row['source_id'])!=row['policy_hash']):return mismatch
                    actual[row['id']]=row['payload_hash']
                if set(logged)!=set(actual):return mismatch
                source_ids=set()
                for row in c.execute('SELECT * FROM sources WHERE org_id=?',(p['org_id'],)):
                    if policies.get(row['source_id'])!=sha(row['policy']):return mismatch
                    source_ids.add(row['source_id'])
                if source_ids!=set(policies):return mismatch
                found={}
                for row in c.execute('SELECT * FROM findings WHERE org_id=?',(p['org_id'],)):
                    if created.get(row['id'])!=row['body'] or row['status']!=reviews.get(row['id'],'triage'):return mismatch
                    found[row['id']]=row['body']
                if found!=created:return mismatch
                done={row[0] for row in c.execute("SELECT j.event_id FROM jobs j JOIN events e ON e.id=j.event_id WHERE e.org_id=? AND j.state='done'",(p['org_id'],))}
                if done!=processed:return mismatch
                actual_jobs={row['event_id']:{k:row[k] for k in ('state','attempts','error_code')} for row in c.execute('SELECT j.* FROM jobs j JOIN events e ON e.id=j.event_id WHERE e.org_id=?',(p['org_id'],))}
                if actual_jobs!=job_history:return mismatch
        except (KeyError,ValueError,TypeError):return mismatch
        return {'integrity':'matches_local_chain' if expected_head is None or hmac.compare_digest(prev,expected_head) else 'anchor_mismatch',
                'head':prev,'external_anchor_supplied':expected_head is not None,'release_authorized':False}

    def review(self,p,fid,review):
        self.require(p,'owner')
        if review.decision=='closed' and review.reason!='recovery_verified': raise Rejected(422,'closure_requires_recovery_reason')
        with self.connection(True) as c:
            found=c.execute('SELECT body FROM findings WHERE org_id=? AND id=?',(p['org_id'],fid)).fetchone()
            if not found: raise Rejected(404,'finding_not_found')
            for eid in review.evidence_event_ids:
                e=c.execute('SELECT plane FROM events WHERE org_id=? AND id=?',(p['org_id'],eid)).fetchone()
                if not e or e[0]!='operational':raise Rejected(422,'review_evidence_not_operational_or_not_in_scope')
            c.execute('UPDATE findings SET status=? WHERE org_id=? AND id=?',(review.decision,p['org_id'],fid))
            self._log(c,p['org_id'],{'operation':'owner_review_recorded','finding_id':fid,**review.model_dump(),'at':self.clock()})
        return {'status':review.decision,'verification':'owner_attestation_not_independent_verification'}
