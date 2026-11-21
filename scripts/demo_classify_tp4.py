"""Functional request/response examples from the existing API over real loopback HTTP."""
import json
from pathlib import Path
import httpx
from scripts.local_lab import local_lab


def main():
    evidence=[]
    with local_lab() as lab:
        with httpx.Client(base_url=lab.url,timeout=10,trust_env=False) as client:
            login=client.post('/auth/token',data={'username':'lab-a','password':lab.password})
            login.raise_for_status()
            token=login.json()['access_token']
            cases=[('health','GET','/health',None,None,200),
                   ('sem_token','POST','/classify',{'text':'book a hotel'},None,401),
                   ('token_invalido','POST','/classify',{'text':'book a hotel'},'invalid',401),
                   ('classificacao','POST','/classify',{'text':'I would like to book a hotel'},token,200),
                   ('texto_vazio','POST','/classify',{'text':' '},token,422),
                   ('campo_extra','POST','/classify',{'text':'hotel','unexpected':True},token,422)]
            for case,method,path,payload,auth,expected in cases:
                headers={'Authorization':'Bearer '+auth} if auth else {}
                r=client.request(method,path,json=payload,headers=headers)
                assert r.status_code==expected,(case,r.text)
                evidence.append({'case':case,'method':method,'path':path,'request_json':payload,
                                 'authentication':'presente (redigida)' if auth else 'ausente',
                                 'status':r.status_code,'response':r.json(),
                                 'transport':'HTTP real em loopback; banco e sessão descartáveis'})
    root=Path(__file__).resolve().parents[1]
    (root/'reports/tp4/functional_api.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Seis exemplos funcionais executados e registrados, sem tokens exportados.')


if __name__=='__main__':main()
