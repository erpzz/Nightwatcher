"""Run with python -m nightwatcher. All credentials go to an exclusive private file."""
import argparse
import json
import os
from pathlib import Path
import time
from .store import Store

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=Path('private/nightwatcher.sqlite3'))
    sub=parser.add_subparsers(dest='command',required=True)
    init=sub.add_parser('init');init.add_argument('--credentials',type=Path,default=Path('private/credentials.json'))
    serve=sub.add_parser('serve');serve.add_argument('--port',type=int,default=8787)
    worker=sub.add_parser('worker');worker.add_argument('--org',default='local-owner');worker.add_argument('--once',action='store_true')
    args=parser.parse_args();os.umask(0o077)
    if args.command=='init':
        if args.db.exists() or args.credentials.exists():parser.error('Refusing to replace an existing database or credential file')
        args.credentials.parent.mkdir(parents=True,exist_ok=True)
        # Reserve output before issuing credentials, so a raced duplicate cannot replace it.
        fd=os.open(args.credentials,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            store=Store(args.db)
            with os.fdopen(fd,'w') as f:json.dump({'owner':store.issue_local('local-owner'),'reader':store.issue_local('local-owner','reader')},f)
        except BaseException:
            args.credentials.unlink(missing_ok=True);raise
        print('Initialized local pilot. Credentials are in the requested private file; do not publish them.')
    elif args.command=='serve':
        if not args.db.exists():parser.error('Run init first')
        import uvicorn
        from .api import create_app
        uvicorn.run(create_app(args.db),host='127.0.0.1',port=args.port,access_log=False,proxy_headers=False,limit_concurrency=32,timeout_keep_alive=5)
    else:
        if not args.db.exists():parser.error('Run init first')
        store=Store(args.db)
        try:
            while True:
                result=store.process(args.org)
                if args.once:print(json.dumps(result));return
                time.sleep(1 if result['processed'] else 5)
        except KeyboardInterrupt:pass

if __name__=='__main__':main()
