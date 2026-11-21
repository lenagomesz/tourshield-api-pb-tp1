"""Bounded defensive HTTP checks on owned TourShield; no scanners or third-party targets."""
from datetime import datetime,timedelta,timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
from uuid import uuid4
import httpx
import jwt
from scripts.local_lab import local_lab

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'pentest/evidencias/defensiva_tp4'


def main():
    from app.config import ISSUER,AUDIENCE
    from app.database import User,connect
    from main import app
    OUT.mkdir(parents=True,exist_ok=True)
    ledger=[]
    with local_lab() as lab:
        with httpx.Client(base_url=lab.url,timeout=10,trust_env=False,follow_redirects=False) as http:
            def check(identifier,control,method,path,expected,*,token=None,body=None,form=None,raw=None):
                headers={'Authorization':'Bearer '+token} if token else {}
                if raw is not None:headers['Content-Type']='application/json'
                r=http.request(method,path,json=body,data=form,content=raw,headers=headers)
                try:response=r.json()
                except ValueError:response=r.text[:500]
                if isinstance(response,dict) and 'access_token' in response:
                    response={**response,'access_token':'[REDACTED]'}
                request=body if body is not None else ({**form,'password':'[REDACTED]'} if form else raw)
                ledger.append({'id':identifier,'control':control,'execution':'executado',
                               'method':method,'path':path,'request':request,
                               'token':'presente; não exportado' if token else 'ausente',
                               'expected_status':expected,'actual_status':r.status_code,
                               'response':response,'passed':r.status_code==expected,
                               'headers':{k:r.headers[k] for k in ['www-authenticate','cache-control','x-content-type-options'] if k in r.headers}})
                assert r.status_code==expected,(identifier,r.status_code,r.text)
                return r
            a=check('SESSION-A','permissoes','POST','/auth/token',200,form={'username':'lab-a','password':lab.password}).json()['access_token']
            b=check('SESSION-B','permissoes','POST','/auth/token',200,form={'username':'lab-b','password':lab.password}).json()['access_token']
            admin=check('SESSION-ADMIN','administracao','POST','/auth/token',200,form={'username':'lab-admin','password':lab.password}).json()['access_token']
            check('JWT-VALID','jwt','POST','/classify',200,token=a,body={'text':'I want to book a hotel'})
            check('JWT-ABSENT','jwt','POST','/classify',401,body={'text':'hotel'})
            check('JWT-MALFORMED','jwt','POST','/classify',401,token='invalid-fixture-token',body={'text':'hotel'})
            now=datetime.now(timezone.utc)
            original={'sub':'lab-a','iat':now,'exp':now+timedelta(minutes=15),'iss':ISSUER,'aud':AUDIENCE}
            for condition in ['none','expired','signature','HS384','issuer','audience','future_nbf','missing_exp','missing_sub']:
                claims=dict(original)
                key=os.environ['JWT_SECRET'];algorithm='HS256'
                if condition=='none':key,algorithm='','none'
                if condition=='expired':claims['exp']=now-timedelta(seconds=5)
                if condition=='signature':key=secrets.token_urlsafe(48)
                if condition=='HS384':algorithm='HS384'
                if condition=='issuer':claims['iss']='different-issuer'
                if condition=='audience':claims['aud']='different-audience'
                if condition=='future_nbf':claims['nbf']=now+timedelta(hours=1)
                if condition=='missing_exp':claims.pop('exp')
                if condition=='missing_sub':claims.pop('sub')
                fixture=jwt.encode(claims,key,algorithm=algorithm)
                check('JWT-'+condition.upper(),'jwt','POST','/classify',401,token=fixture,body={'text':'hotel'})
            resource_a=check('OWNER-CREATE-A','isolamento','POST','/reservations',201,token=a,body={'destination':'Recife-A'}).json()['id']
            resource_b=check('OWNER-CREATE-B','isolamento','POST','/reservations',201,token=b,body={'destination':'Natal-B'}).json()['id']
            check('OWNER-READ-A','isolamento','GET','/reservations/'+resource_a,200,token=a)
            check('OWNER-READ-B','isolamento','GET','/reservations/'+resource_b,200,token=b)
            denied=check('OWNER-CROSS-B-TO-A','isolamento','GET','/reservations/'+resource_a,404,token=b)
            check('OWNER-CROSS-A-TO-B','isolamento','GET','/reservations/'+resource_b,404,token=a)
            absent=check('OWNER-MISSING','isolamento','GET','/reservations/'+str(uuid4()),404,token=b)
            assert denied.json()==absent.json()
            check('OWNER-EXTRA','parametros','POST','/reservations',422,token=b,body={'destination':'Natal','owner':'lab-a'})
            check('STATUS-EXTRA','parametros','POST','/reservations',422,token=b,body={'destination':'Natal','status':'approved'})
            check('ADMIN-ABSENT','administracao','GET','/admin/status',401)
            check('ADMIN-REGULAR','administracao','GET','/admin/status',403,token=b)
            check('ADMIN-AUTHORIZED','administracao','GET','/admin/status',200,token=admin)
            role_fixture=jwt.encode({**original,'role':'admin'},os.environ['JWT_SECRET'],algorithm='HS256')
            check('ADMIN-ROLE-CLAIM','administracao','GET','/admin/status',403,token=role_fixture)
            os.environ['TOURSHIELD_ADMIN_USERS']=''
            check('ADMIN-EMPTY-ALLOWLIST','administracao','GET','/admin/status',403,token=admin)
            os.environ['TOURSHIELD_ADMIN_USERS']='lab-admin'
            with connect() as db:
                user=db.get(User,'lab-b');user.active=False;db.add(user);db.commit()
            check('USER-DEACTIVATED','permissoes','POST','/classify',401,token=b,body={'text':'hotel'})
            for identifier,payload,expected in [
                ('TEXT-BLANK',{'text':' '},422),('TEXT-NUMBER',{'text':7},422),
                ('TEXT-NULL',{'text':None},422),('TEXT-EXTRA',{'text':'hotel','extra':True},422),
                ('TEXT-MISSING',{},422),('TEXT-MIN',{'text':'x'},200),
                ('TEXT-MAX',{'text':'x'*4000},200),('TEXT-OVER',{'text':'x'*4001},422)]:
                check(identifier,'parametros','POST','/classify',expected,token=a,body=payload)
            malformed=check('JSON-MALFORMED','erros','POST','/classify',422,token=a,raw='{"text":"private-marker')
            assert 'private-marker' not in malformed.text
            check('UUID-MALFORMED','erros','GET','/reservations/not-a-uuid',422,token=a)
            check('METHOD-NOT-ALLOWED','erros','GET','/classify',405)
            check('ROUTE-ABSENT','erros','GET','/route-not-implemented',404)
            check('BODY-LIMIT','erros','POST','/classify',413,token=a,raw='x'*16385)
            openapi=check('INVENTORY-OPENAPI','inventario','GET','/openapi.json',200).json()
            (OUT/'openapi_snapshot.json').write_text(json.dumps(openapi,indent=2,ensure_ascii=False),encoding='utf-8',newline='\n')
            operations=[{'method':method.upper(),'path':path,'authentication':'JWT' if operation.get('security') else 'pública',
                         'summary':operation.get('summary','')}
                        for path,methods in openapi['paths'].items() for method,operation in methods.items()
                        if method in {'get','post','put','patch','delete','head','options'}]
            ledger[-1]['response']={'title':openapi['info']['title'],'version':openapi['info']['version'],'operations':operations}
            ledger[-1]['response_recording']='Resumo dos campos do contrato; resposta JSON completa em openapi_snapshot.json'
            runtime=[]
            def collect_routes(routes):
                for route in routes:
                    included=getattr(route,'original_router',None)
                    if included is not None:
                        collect_routes(included.routes)
                    elif hasattr(route,'path'):
                        runtime.append({'path':route.path,'methods':sorted(getattr(route,'methods',[]) or []),
                                        'type':type(route).__name__,'in_openapi':bool(getattr(route,'include_in_schema',False))})
            collect_routes(app.routes)
            assert {row['path'] for row in operations}.issubset({row['path'] for row in runtime})
            assert {'/docs','/static','/openapi.json'}.issubset({row['path'] for row in runtime})
            inventory={'methodology':'OpenAPI HTTP real e inspeção de app.routes; sem descoberta por scanner',
                       'service':'Uvicorn / FastAPI TourShield 0.4.0; processo criado pelo harness',
                       'network':'127.0.0.1:porta efêmera, encerrada ao concluir',
                       'contract_operations':operations,'runtime_routes':runtime}
    source_files=['app/security.py','app/routes/admin.py','app/routes/reservations.py','app/models.py',
                  'app/middleware.py','main.py','tests/test_defensive_tp4.py','scripts/evaluate_defensive_tp4.py']
    summary={'authors':['Helena Gomes','Maria Paula'],'scope':'API própria, testes defensivos locais autorizados',
             'executed_at_utc':datetime.now(timezone.utc).isoformat(),
             'code_commit_before_evaluation':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'requests':len(ledger),'passed':sum(x['passed'] for x in ledger),'failed':sum(not x['passed'] for x in ledger),
             'by_control':{control:sum(x['control']==control for x in ledger) for control in sorted({x['control'] for x in ledger})},
             'external_targets':False,'scanner_execution':False,'simulation_used_for_http_results':False,
             'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_files}}
    for name,value in [('http_results.json',ledger),('route_inventory.json',inventory),('summary.json',summary)]:
        (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8',newline='\n')
    print(f'Avaliação defensiva: {len(ledger)} verificações HTTP, {summary["passed"]} aprovadas; zero alvos externos.')


if __name__=='__main__':main()
