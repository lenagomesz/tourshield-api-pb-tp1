import asyncio
import hashlib
import json
import pytest
from app.classifier import classify_text,load_classifier
from tests.test_api import client,login


def test_classify_requires_token(client):
    assert client.post('/classify',json={'text':'book a hotel'}).status_code==401


def test_classify_invalid_token(client):
    assert client.post('/classify',json={'text':'hotel'},headers={'Authorization':'Bearer invalid'}).status_code==401


def test_model_preloaded_during_startup(client):
    from main import app
    assert app.state.classifier_ready is True


def test_admin_function_rejects_regular_user(client,monkeypatch):
    monkeypatch.setenv('TOURSHIELD_ADMIN_USERS','another-user')
    assert client.get('/admin/status',headers={'Authorization':'Bearer '+login(client)}).status_code==403


def test_admin_function_accepts_server_authorized_user(client,monkeypatch):
    monkeypatch.setenv('TOURSHIELD_ADMIN_USERS','tester')
    assert client.get('/admin/status',headers={'Authorization':'Bearer '+login(client)}).status_code==200


def test_admin_function_requires_auth(client):
    assert client.get('/admin/status').status_code==401


def test_classify_real_model(client):
    headers={'Authorization':'Bearer '+login(client)}
    response=client.post('/classify',json={'text':'I would like to book a hotel'},headers=headers)
    assert response.status_code==200
    result=response.json()
    assert result['intent']=='book_hotel'
    assert 0<=result['probability']<=1
    assert result['model_version']=='tourshield-intents-tp4-v1'
    assert 'text' not in result and 'token' not in result


@pytest.mark.parametrize('payload',[{'text':' '},{'text':'x'*4001},{'text':7},
    {'text':'hotel','role':'admin'},{'text':'hotel','latitude':-22},{}])
def test_classify_strict_inputs(client,payload):
    headers={'Authorization':'Bearer '+login(client)}
    assert client.post('/classify',json=payload,headers=headers).status_code==422


def test_corrupt_model_is_not_deserialized(client,tmp_path,monkeypatch):
    import app.classifier as classifier
    (tmp_path/'manifest.json').write_text(json.dumps({'sha256':'incorrect'}))
    (tmp_path/'intent_classifier.joblib').write_bytes(b'not-a-pickle')
    monkeypatch.setattr(classifier,'MODEL_DIR',tmp_path)
    load_classifier.cache_clear()
    try:
        headers={'Authorization':'Bearer '+login(client)}
        assert client.post('/classify',json={'text':'hotel'},headers=headers).status_code==503
    finally:load_classifier.cache_clear()


def test_model_missing_returns_503(client,tmp_path,monkeypatch):
    import app.classifier as classifier
    monkeypatch.setattr(classifier,'MODEL_DIR',tmp_path)
    load_classifier.cache_clear()
    try:
        assert client.post('/classify',json={'text':'hotel'},headers={'Authorization':'Bearer '+login(client)}).status_code==503
    finally:load_classifier.cache_clear()


def test_tool_contract_has_no_credentials():
    from app.agent import classify_intent
    assert set(classify_intent.params_json_schema['properties'])=={'text'}


def test_agent_tool_rejects_missing_session(client):
    import httpx
    from agents import Runner,RunConfig
    from app.agent import build_agent,AgentContext
    from scripts.demo_agent_tp4 import DemonstrationModel
    from main import app
    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://testserver') as http:
            result=await Runner.run(build_agent(DemonstrationModel()),'hotel',
                context=AgentContext(http,'invalid-token'),max_turns=4,
                run_config=RunConfig(tracing_disabled=True))
            value=next(item.output for item in result.new_items if item.type=='tool_call_output_item')
            data=json.loads(value) if isinstance(value,str) else value
            assert data['http_status']==401
    asyncio.run(call())


def test_agent_url_stays_in_local_scope():
    from app.agent import validate_api_url
    for url in ['http://example.org','http://127.0.0.1.example.org','http://user:pw@127.0.0.1:8000']:
        with pytest.raises(ValueError):validate_api_url(url)


def test_sdk_runner_really_invokes_api(client):
    import httpx
    from agents import Runner,RunConfig
    from app.agent import AgentContext,build_agent
    from scripts.demo_agent_tp4 import DemonstrationModel
    from main import app
    token=login(client)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://testserver') as http:
            result=await Runner.run(build_agent(DemonstrationModel()),'book a hotel',
                         context=AgentContext(http,token),max_turns=4,
                         run_config=RunConfig(tracing_disabled=True))
            assert 'book_hotel' in result.final_output
            assert any(item.type=='tool_call_output_item' for item in result.new_items)
    asyncio.run(run())
