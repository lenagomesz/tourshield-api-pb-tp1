"""Temporary TourShield lab on a kernel-assigned loopback port; no existing DB touched."""
from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import secrets
import socket
import tempfile
import threading
import time
import httpx
import uvicorn


@dataclass
class Lab:
    url:str
    password:str
    directory:Path


@contextmanager
def local_lab():
    from app.database import initialize,add_user,engine_for
    from app.security import password_hash
    from app.middleware import login_limiter
    from main import app
    root=Path(__file__).resolve().parents[1]
    (root/'tmp').mkdir(exist_ok=True)
    previous={key:os.environ.get(key) for key in ['JWT_SECRET','DATABASE_PATH','TOURSHIELD_ADMIN_USERS']}
    server=None
    thread=None
    with tempfile.TemporaryDirectory(prefix='tp4-lab-',dir=root/'tmp') as temp:
        directory=Path(temp)
        database=str(directory/'lab.sqlite3')
        try:
            os.environ['JWT_SECRET']=secrets.token_urlsafe(48)
            os.environ['DATABASE_PATH']=database
            os.environ['TOURSHIELD_ADMIN_USERS']='lab-admin'
            initialize()
            password=secrets.token_urlsafe(24)
            for username in ['lab-a','lab-b','lab-admin']:
                add_user(username,password_hash.hash(password))
            login_limiter.reset()
            sock=socket.socket()
            sock.bind(('127.0.0.1',0))
            port=sock.getsockname()[1]
            server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False,
                                  proxy_headers=False,server_header=False))
            thread=threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True)
            thread.start()
            url=f'http://127.0.0.1:{port}'
            with httpx.Client(base_url=url,timeout=2,trust_env=False) as client:
                for attempt in range(50):
                    try:
                        if client.get('/health').status_code==200:break
                    except httpx.HTTPError:pass
                    time.sleep(.1)
                else:raise RuntimeError('Laboratório não iniciou')
            yield Lab(url,password,directory)
        finally:
            if server:server.should_exit=True
            if thread:thread.join(timeout=10)
            engine_for(database).dispose()
            login_limiter.reset()
            for key,value in previous.items():
                if value is None:os.environ.pop(key,None)
                else:os.environ[key]=value
