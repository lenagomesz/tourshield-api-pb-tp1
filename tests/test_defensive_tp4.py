"""Defensive regression checks against the same application and isolated fixtures."""
from datetime import datetime,timedelta,timezone
import os
import secrets
from uuid import uuid4
import jwt
import pytest
from app.config import ISSUER,AUDIENCE
from app.database import User,add_user,connect
from app.security import issue_token,password_hash
from tests.test_api import client,login


def bearer(token):
    return {'Authorization':'Bearer '+token}


@pytest.mark.parametrize('condition',['none','expired','signature','HS384','issuer','audience','future_nbf','missing_exp','missing_sub'])
def test_classify_enforces_jwt_contract(client,condition):
    now=datetime.now(timezone.utc)
    claims={'sub':'tester','iat':now,'exp':now+timedelta(minutes=15),'iss':ISSUER,'aud':AUDIENCE}
    key=os.environ['JWT_SECRET']
    algorithm='HS256'
    if condition=='none':algorithm,key='none',''
    if condition=='expired':claims['exp']=now-timedelta(seconds=5)
    if condition=='signature':key=secrets.token_urlsafe(48)
    if condition=='HS384':algorithm='HS384'
    if condition=='issuer':claims['iss']='other-issuer'
    if condition=='audience':claims['aud']='other-audience'
    if condition=='future_nbf':claims['nbf']=now+timedelta(hours=1)
    if condition=='missing_exp':claims.pop('exp')
    if condition=='missing_sub':claims.pop('sub')
    token=jwt.encode(claims,key,algorithm=algorithm)
    response=client.post('/classify',headers=bearer(token),json={'text':'book hotel'})
    assert response.status_code==401
    assert response.headers['www-authenticate']=='Bearer'
    assert token not in response.text


def test_deactivation_applies_to_existing_classify_session(client):
    token=login(client)
    assert client.post('/classify',headers=bearer(token),json={'text':'hotel'}).status_code==200
    with connect() as db:
        user=db.get(User,'tester')
        user.active=False
        db.add(user)
        db.commit()
    assert client.post('/classify',headers=bearer(token),json={'text':'hotel'}).status_code==401


def test_both_accounts_are_isolated_in_both_directions(client):
    token_a=login(client)
    add_user('fixture-b',password_hash.hash('fixture-b-test-password'))
    token_b=issue_token('fixture-b')
    a=client.post('/reservations',headers=bearer(token_a),json={'destination':'Recife-A'}).json()['id']
    b=client.post('/reservations',headers=bearer(token_b),json={'destination':'Natal-B'}).json()['id']
    assert client.get('/reservations/'+a,headers=bearer(token_a)).status_code==200
    assert client.get('/reservations/'+b,headers=bearer(token_b)).status_code==200
    for token,resource in [(token_a,b),(token_b,a)]:
        denied=client.get('/reservations/'+resource,headers=bearer(token))
        absent=client.get('/reservations/'+str(uuid4()),headers=bearer(token))
        assert denied.status_code==absent.status_code==404
        assert denied.json()==absent.json()
        assert 'destination' not in denied.json()


def test_extra_role_claim_does_not_grant_admin_permission(client,monkeypatch):
    monkeypatch.setenv('TOURSHIELD_ADMIN_USERS','another-account')
    now=datetime.now(timezone.utc)
    claims={'sub':'tester','iat':now,'exp':now+timedelta(minutes=15),
            'iss':ISSUER,'aud':AUDIENCE,'role':'admin'}
    fixture=jwt.encode(claims,os.environ['JWT_SECRET'],algorithm='HS256')
    assert client.get('/admin/status',headers=bearer(fixture)).status_code==403


def test_admin_allowlist_defaults_to_deny_and_changes_take_effect(client,monkeypatch):
    token=login(client)
    monkeypatch.setenv('TOURSHIELD_ADMIN_USERS','')
    assert client.get('/admin/status',headers=bearer(token)).status_code==403
    monkeypatch.setenv('TOURSHIELD_ADMIN_USERS','tester')
    assert client.get('/admin/status',headers=bearer(token)).status_code==200
    monkeypatch.setenv('TOURSHIELD_ADMIN_USERS','')
    assert client.get('/admin/status',headers=bearer(token)).status_code==403


def test_classifier_malformed_json_is_generic(client):
    token=login(client)
    marker='private-malformed-marker'
    response=client.post('/classify',headers={**bearer(token),'Content-Type':'application/json'},
                         content='{"text":"'+marker)
    assert response.status_code==422
    assert marker not in response.text
    assert 'input' not in response.text


@pytest.mark.parametrize('length,expected',[(1,200),(4000,200),(4001,422)])
def test_classify_boundaries(client,length,expected):
    token=login(client)
    assert client.post('/classify',headers=bearer(token),json={'text':'x'*length}).status_code==expected


def test_unknown_resource_and_malformed_identifier_have_distinct_http_semantics(client):
    headers=bearer(login(client))
    assert client.get('/reservations/invalid-uuid',headers=headers).status_code==422
    assert client.get('/reservations/'+str(uuid4()),headers=headers).status_code==404


def test_openapi_inventory_preserves_protected_contracts(client):
    schema=client.get('/openapi.json').json()
    for path,method in [('/classify','post'),('/predict','post'),('/reservations','post'),
                        ('/reservations/{reservation_id}','get'),('/admin/status','get')]:
        assert schema['paths'][path][method].get('security')
    assert schema['components']['schemas']['ClassifyRequest']['additionalProperties'] is False
    assert '401' in schema['paths']['/admin/status']['get']['responses']
    assert '403' in schema['paths']['/admin/status']['get']['responses']
