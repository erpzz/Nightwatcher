"""Authenticated loopback API. No website, remote shell, URL fetcher or response action."""
import asyncio
from collections import deque
import json
import re
import sqlite3
import time
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .contracts import Enrollment, Event, Checkpoint, Review, Plane
from .store import Store, Rejected

MAX_BODY=32768
SECRET=re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN .*PRIVATE KEY|Bearer\s+[A-Za-z0-9._-]+|eyJ[A-Za-z0-9_-]{10,}\.)')

def unique_object(pairs):
    obj={}
    for k,v in pairs:
        if k in obj: raise ValueError('duplicate key')
        obj[k]=v
    return obj

class Boundary:
    """Bound bytes/time/clients before parsing. Single-process localhost pilot limits."""
    def __init__(self,app,rate=600):self.app=app;self.rate=rate;self.clients={}
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        headers={k.lower():v for k,v in scope.get('headers',[])}
        async def reject(status,code):
            await JSONResponse({'error':code},status_code=status)(scope,receive,send)
        if b'origin' in headers:return await reject(403,'browser_origin_not_supported')
        client=(scope.get('client') or ['unknown'])[0];now=time.monotonic()
        self.clients={k:v for k,v in self.clients.items() if v and v[-1]>now-60}
        if client not in self.clients and len(self.clients)>=1024:return await reject(429,'client_limit')
        queue=self.clients.setdefault(client,deque())
        while queue and queue[0]<=now-60:queue.popleft()
        if len(queue)>=self.rate:return await reject(429,'request_limit')
        queue.append(now)
        chunks=[];size=0;deadline=now+5
        while True:
            try:message=await asyncio.wait_for(receive(),timeout=max(0.001,deadline-time.monotonic()))
            except asyncio.TimeoutError:return await reject(408,'body_timeout')
            if message['type']=='http.disconnect':return
            chunk=message.get('body',b'');size+=len(chunk)
            if size>MAX_BODY:return await reject(413,'body_too_large')
            chunks.append(chunk)
            if not message.get('more_body'):break
        body=b''.join(chunks)
        if body:
            if headers.get(b'content-type',b'').split(b';')[0].lower()!=b'application/json':return await reject(415,'json_required')
            try:
                text=body.decode('utf-8')
                if SECRET.search(text):return await reject(422,'sensitive_value_rejected')
                parsed=json.loads(text,object_pairs_hook=unique_object,parse_constant=lambda x: (_ for _ in ()).throw(ValueError()))
                if SECRET.search(json.dumps(parsed,ensure_ascii=False)):return await reject(422,'sensitive_value_rejected')
            except (ValueError,RecursionError):return await reject(422,'invalid_json')
        delivered=False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered=True;return {'type':'http.request','body':body,'more_body':False}
            return await receive()
        async def secured(message):
            if message['type']=='http.response.start':
                message['headers']=list(message.get('headers',[]))+[(b'cache-control',b'no-store'),(b'x-content-type-options',b'nosniff'),(b'content-security-policy',b"default-src 'none'; frame-ancestors 'none'")]
            await send(message)
        await self.app(scope,replay,secured)

def create_app(db,rate=600):
    store=Store(db)
    app=FastAPI(title='NIGHTWATCHER local evidence API',docs_url=None,redoc_url=None,openapi_url=None)
    app.state.store=store
    app.add_middleware(Boundary,rate=rate)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])

    @app.exception_handler(RequestValidationError)
    async def invalid(request,exc):
        p=getattr(request.state,'principal',None);store.rejected(p)
        return JSONResponse({'error':'invalid_payload'},status_code=422)

    @app.exception_handler(sqlite3.Error)
    async def database_error(request,exc):
        return JSONResponse({'error':'database_unavailable'},status_code=503)

    @app.exception_handler(Rejected)
    async def rejected(request,exc):
        store.rejected(getattr(request.state,'principal',None))
        return JSONResponse({'error':exc.code},status_code=exc.status)

    def principal(request:Request):
        auth=request.headers.get('authorization','')
        if not auth.startswith('Bearer '):raise Rejected(401,'unauthorized')
        p=store.authenticate(auth[7:]);request.state.principal=p;return p

    @app.get('/healthz')
    def health():return {'service':'nightwatcher','mode':'local_pilot','live_monitoring_claim':False}

    @app.post('/v1/sources',status_code=201)
    def enroll(policy:Enrollment,p=Depends(principal)):return store.enroll(p,policy)

    @app.post('/v1/sources/{source_id}/disable')
    def disable(source_id:str,p=Depends(principal)):return store.disable(p,source_id)

    @app.post('/v1/events',status_code=202)
    def ingest(event:Event,p=Depends(principal)):return store.ingest(p,event)

    @app.post('/v1/checkpoints')
    def checkpoint(cp:Checkpoint,p=Depends(principal)):return store.checkpoint(p,cp)

    @app.post('/v1/process')
    def process(p=Depends(principal)):
        store.require(p,'owner');return store.process(p['org_id'])

    @app.get('/v1/status')
    def status(p=Depends(principal)):return store.status(p)

    @app.get('/v1/export')
    def export(plane:Plane='operational',after:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=500),p=Depends(principal)):
        return store.export(p,plane,after,limit)

    @app.get('/v1/integrity')
    def integrity(expected_head:str|None=Query(None,pattern=r'^[a-f0-9]{64}$'),p=Depends(principal)):
        return store.verify(p,expected_head)

    @app.post('/v1/findings/{finding_id}/reviews')
    def review(finding_id:str,body:Review,p=Depends(principal)):return store.review(p,finding_id,body)
    return app
