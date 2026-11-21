"""Execute real Agents SDK/tool/API with a deterministic, explicitly simulated LLM."""
import asyncio
import json
from pathlib import Path
from uuid import uuid4
import httpx
from agents import Model, ModelResponse, Usage, Runner, RunConfig
from openai.types.responses import ResponseFunctionToolCall,ResponseOutputMessage,ResponseOutputText
from app.agent import build_agent,AgentContext
from scripts.local_lab import local_lab


class DemonstrationModel(Model):
    """Test double for generation only. Does not emulate a hosted language model."""
    async def get_response(self,system_instructions,input,model_settings,tools,output_schema,
                           handoffs,tracing,**kwargs):
        items=[{'role':'user','content':input}] if isinstance(input,str) else input
        if items and items[-1].get('type')=='function_call_output':
            result=json.loads(items[-1]['output'])
            if 'intent' in result:
                answer=(f'Intenção: {result["intent"]}; probabilidade estimada: {result["probability"]:.1%}. '
                        'Posso encaminhar sua solicitação. Nenhuma reserva ou benefício foi autorizado.')
            else:
                answer='Não foi possível classificar; confirme sua sessão e procure atendimento humano.'
            output=[ResponseOutputMessage(id='msg_'+uuid4().hex,type='message',role='assistant',
                     status='completed',content=[ResponseOutputText(type='output_text',text=answer,annotations=[])])]
        else:
            latest=next(x for x in reversed(items) if x.get('role')=='user')
            text=latest['content']
            output=[ResponseFunctionToolCall(type='function_call',name='classify_intent',
                        arguments=json.dumps({'text':text}),call_id='call_'+uuid4().hex)]
        return ModelResponse(output=output,usage=Usage(),response_id=None)

    async def stream_response(self,*args,**kwargs):
        raise NotImplementedError('Demonstração usa Runner.run, sem streaming.')
        yield


async def demonstrate(lab):
    agent=build_agent(model=DemonstrationModel())
    messages=['I would like to book a hotel in Lisbon',
              'What is my rewards balance?',
              'Please cancel my reservation']
    conversation=[]
    async with httpx.AsyncClient(base_url=lab.url,timeout=10,trust_env=False,follow_redirects=False) as client:
        login=await client.post('/auth/token',data={'username':'lab-a','password':lab.password})
        login.raise_for_status()
        context=AgentContext(client,login.json()['access_token'])
        history=[]
        for text in messages:
            history.append({'role':'user','content':text})
            result=await Runner.run(agent,history,context=context,max_turns=4,
                                    run_config=RunConfig(tracing_disabled=True))
            tool_outputs=[item.output for item in result.new_items if item.type=='tool_call_output_item']
            assert len(tool_outputs)==1
            parsed=json.loads(tool_outputs[0]) if isinstance(tool_outputs[0],str) else tool_outputs[0]
            assert 'intent' in parsed and 0<=parsed['probability']<=1
            conversation.append({'user':text,'assistant':result.final_output,'tool_result':parsed})
            history=result.to_input_list()
    return {'sdk_execution':'real','api_transport':'HTTP real em loopback',
            'generation':'simulada: DemonstrationModel determinístico, sem LLM remoto',
            'openai_remote_execution':False,'conversation':conversation}


def main():
    with local_lab() as lab:
        evidence=asyncio.run(demonstrate(lab))
    root=Path(__file__).resolve().parents[1]
    out=root/'reports/tp4'
    out.mkdir(parents=True,exist_ok=True)
    (out/'agent_conversation.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf-8')
    lines=['# TourShield - conversa demonstrativa (três turnos)',
           'Helena Gomes e Maria Paula | 21/11/2026',
           'Agent, Runner.run, @function_tool e API HTTP executados. Geração de resposta simulada por modelo determinístico; não é conversa com LLM OpenAI remoto.']
    for i,turn in enumerate(evidence['conversation'],1):
        lines += [f'## Turno {i}',f'**Usuário:** {turn["user"]}',f'**TourShield:** {turn["assistant"]}',
                  f'**Ferramenta /classify:** `{json.dumps(turn["tool_result"],ensure_ascii=False)}`']
    (out/'agent_conversation.md').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
    print('Demonstração concluída: 3 turnos; SDK/API reais, geração simulada.')


if __name__=='__main__':main()
