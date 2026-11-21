"""Build a source-and-evidence-only defensive log; never infer unexecuted results."""
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'pentest/evidencias/defensiva_tp4'


def main():
    summary=json.loads((EVIDENCE/'summary.json').read_text(encoding='utf-8'))
    results=json.loads((EVIDENCE/'http_results.json').read_text(encoding='utf-8'))
    inventory=json.loads((EVIDENCE/'route_inventory.json').read_text(encoding='utf-8'))
    suite=ET.parse(ROOT/'reports/tests_defensive_tp4.xml').getroot().find('testsuite')
    assert suite is not None and suite.attrib['failures']=='0' and suite.attrib['errors']=='0'
    assert summary['failed']==0 and all(row['passed'] for row in results)
    tests=int(suite.attrib['tests'])
    controls=[
        {'name':'Validação de tokens JWT','group':'jwt','source':'app/security.py',
         'method':'Comparar uma sessão válida com ausência de token, formato inválido e nove fixtures: none, expiração, chave divergente, HS384, emissor/audiência incorretos, nbf futuro e claims obrigatórios ausentes. As fixtures usam somente identidades e chaves descartáveis.',
         'result':'JWT válido: 200. Os outros onze casos: 401. Algoritmo permitido é HS256, fixado no servidor; a assinatura e os claims são verificados antes de consultar a conta.',
         'risk':'Não há denylist/jti nem endpoint de logout com revogação individual. O código verifica conta ativa a cada chamada, mas um token válido de conta ativa pode permanecer utilizável até expirar. Revogação individual não foi validada: pendente de desenho/implementação.'},
        {'name':'Permissões e estado dos usuários','group':'permissoes','source':'app/security.py; app/database.py',
         'method':'Autenticar A e B pelo endpoint real, com credenciais fictícias. Desativar B apenas no banco descartável e reutilizar sua sessão previamente válida.',
         'result':'Logins de A e B: 200. O token ainda não expirado de B passa a receber 401 após active=False. O acesso depende de uma conta existente e ativa, além da integridade criptográfica.',
         'risk':'As permissões dependem da configuração e da integridade do banco. Não foram avaliados diretório externo de identidades, múltiplas organizações ou propagação distribuída de revogação.'},
        {'name':'Isolamento de recursos entre contas (BOLA/IDOR)','group':'isolamento','source':'app/routes/reservations.py',
         'method':'Criar uma reserva de A e outra de B. Ler ambas com o proprietário correto e repetir cada leitura com o outro usuário, mantendo o mesmo UUID. Comparar a resposta negativa com um UUID inexistente.',
         'result':'Criações: 201; leituras próprias: 200; leituras cruzadas e recurso inexistente: 404. O corpo da leitura negada coincide com o do recurso inexistente e não contém o destino. A query usa id e owner obtido da sessão.',
         'risk':'UUID não é controle de autorização por si só. O resultado cobre GET/POST de reservas existentes; a API não possui edição/exclusão de reservas. Futuras rotas devem repetir a checagem de ownership.'},
        {'name':'Restrições administrativas (BFLA)','group':'administracao','source':'app/routes/admin.py',
         'method':'Criar conta administrativa fictícia e autorizar somente seu username na allowlist do servidor. Comparar ausência de sessão, usuário comum, administrador e allowlist vazia. Uma fixture assinada com role=admin para usuário comum verifica que esse claim extra não concede privilégio.',
         'result':'Login administrativo: 200; /admin/status sem sessão: 401; usuário comum: 403; administrador autorizado: 200; usuário comum com claim role=admin: 403; allowlist vazia: 403.',
         'risk':'O único recurso administrativo atual é a prontidão /admin/status. Configuração de TOURSHIELD_ADMIN_USERS exige gestão de acesso e mudanças em implantação; não se avaliou RBAC granular, painel administrativo ou funções que não existem neste projeto.'},
        {'name':'Validação de parâmetros','group':'parametros','source':'app/models.py; app/routes/classify.py',
         'method':'Verificar string estrita, branco, null, número, ausência do campo, campo extra e fronteiras de 1/4000/4001 caracteres. Tentar fornecer owner/status no corpo de criação, sem alterar a implementação da API.',
         'result':'Tipos/campos inválidos e 4001 caracteres: 422. Strings de 1 e 4000 caracteres: 200. owner/status enviados pelo cliente: 422. Isso demonstra validação estrutural, não adequação semântica do texto.',
         'risk':'Strings arbitrárias dentro do limite podem ser classificadas em uma das vinte intenções, mesmo sem relação com o domínio. Não há rejeição out-of-scope validada nem rate limit específico por usuário em /classify; capacidade e quotas permanecem pendentes de avaliação.'},
        {'name':'Inventário de rotas e serviço local','group':'inventario','source':'main.py; app/routes/',
         'method':'Ler /openapi.json por HTTP e inspecionar recursivamente os routers carregados pela mesma aplicação, incluindo rotas omitidas do contrato e mount estático. A instância é iniciada por Uvicorn com socket limitado a loopback e porta efêmera.',
         'result':f'GET /openapi.json: 200; {len(inventory["contract_operations"])} operações no contrato, além de /docs, /openapi.json e /static. Serviço conhecido por inicialização/inspeção do código, não inferido por banner ou varredura.',
         'risk':'Documentação pública revela a superfície por decisão do projeto. O inventário não prova inexistência de outros serviços na máquina. Não houve varredura de portas, Kiterunner, Nmap ou Gobuster nesta complementação.'},
        {'name':'Entradas inválidas e respostas HTTP','group':'erros','source':'main.py; app/middleware.py',
         'method':'Enviar JSON truncado, UUID inválido, método não permitido, rota inexistente e corpo acima de 16 KiB. Confirmar que o JSON de erro não reflete um marcador privado da entrada. Consultar também o teste de exceção interna genérica da suíte completa.',
         'result':'JSON/UUID inválidos: 422; método incorreto: 405; rota inexistente: 404; corpo excessivo: 413. O marcador não foi refletido. O teste test_exception_is_generic_and_logged confirma 500 com detail=Erro interno sem stack trace exposto; testes do modelo cobrem 503.',
         'risk':'Os testes de aplicação não validam proxy reverso, TLS, rede pública ou resistência a carga. /health é liveness e permanece 200 quando o classificador está indisponível; /classify retorna 503. Readiness operacional do modelo continua como melhoria pendente.'}
    ]
    lines=['# TourShield - Log parcial de avaliação defensiva da API',
           '**Helena Gomes e Maria Paula | 21/11/2026**',
           '## 1. Escopo e autorização',
           'Avaliação autorizada nesta solicitação, restrita ao código do próprio TourShield e a instância local descartável. Foram usadas contas fictícias lab-a, lab-b e lab-admin, banco temporário e chave aleatória por execução. Nenhum sistema de colega, domínio externo ou serviço público foi alvo de testes. O banco persistente e o .env existentes foram preservados.',
           '## 2. Metodologia e rastreabilidade',
           f'Execução HTTP real: {summary["requests"]} verificações, {summary["passed"]} aprovadas e {summary["failed"]} divergências. Suíte pytest completa: {tests} testes aprovados, zero falhas/erros, incluindo 19 casos adicionais neste complemento. A classificação do resultado usa comparação explícita de status/corpo e controles positivos e negativos, sem simular respostas de servidor.',
           'Ferramentas efetivamente utilizadas: Python, pytest, FastAPI TestClient/ASGI, HTTPX, Uvicorn e PyJWT. Não foram executados scanners, wordlists de reconhecimento ou ferramentas ofensivas nesta complementação. Evidências antigas de outras atividades não foram reaproveitadas como prova desta execução.',
           f'Data/hora UTC: `{summary["executed_at_utc"]}`. Commit base: `{summary["code_commit_before_evaluation"]}`. Os hashes dos arquivos avaliados e do harness estão em evidencias/defensiva_tp4/summary.json; os arquivos novos ainda não pertenciam ao commit base no instante da coleta.',
           'Evidências: [requisições/respostas](evidencias/defensiva_tp4/http_results.json), [inventário](evidencias/defensiva_tp4/route_inventory.json), [resumo e hashes](evidencias/defensiva_tp4/summary.json), [JUnit completo](../reports/tests_defensive_tp4.xml), [testes adicionais](../tests/test_defensive_tp4.py). Tokens, senhas e chaves não são exportados.',
           'Reprodução, a partir da raiz do repositório:',
           '```powershell\npython -m scripts.evaluate_defensive_tp4\npytest tests/ -v --junitxml=reports/tests_defensive_tp4.xml\npython -m scripts.build_defensive_log_tp4\npython -m scripts.build_report_tp4\n```',
           '## 3. Controles avaliados']
    for index,control in enumerate(controls,1):
        cases=[x for x in results if x['control']==control['group']]
        lines += [f'### 3.{index}. {control["name"]}',f'**Metodologia:** {control["method"]}',
                  f'**Resultado executado:** {control["result"]}',
                  f'**Código examinado:** `{control["source"]}`.',
                  '**Evidência HTTP:** '+', '.join('`'+x['id']+'`' for x in cases)+'.',
                  f'**Risco ou limite:** {control["risk"]}',
                  '**Status:** executado e aprovado nos casos descritos; o risco residual não foi declarado resolvido.']
    lines+=['## 4. Inventário consolidado','| Método | Rota | Acesso |','|---|---|---|']
    for item in inventory['contract_operations']:
        access=item['authentication']
        if item['path']=='/admin/status':access+=' + allowlist administrativa'
        if item['path']=='/auth/token':access='Pública para apresentação de credenciais; emissão exige validação'
        lines.append(f'| {item["method"]} | `{item["path"]}` | {access} |')
    lines += ['','Auxiliares fora da OpenAPI: GET/HEAD /openapi.json, GET /docs e mount /static. O inventário descreve os routers do processo avaliado; não resulta de descoberta externa.',
              '## 5. Registros das verificações HTTP',
              'Entradas longas estão abreviadas abaixo; o JSON original preserva integralmente os dados fictícios enviados. A senha é redigida e o token não é exportado.']
    def abbreviate(value):
        text=json.dumps(value,ensure_ascii=False)
        return text if len(text)<=300 else text[:230]+f' ... [abreviado; {len(text)} caracteres JSON; conteúdo completo no arquivo de evidência]'
    for row in results:
        lines += [f'### {row["id"]}',f'- Método/rota: `{row["method"]} {row["path"]}`.',
                  '- Entrada: `'+abbreviate(row['request']).replace('`','\\`')+'`.',
                  f'- Autenticação: {row["token"]}.',
                  f'- HTTP observado/esperado: **{row["actual_status"]}/{row["expected_status"]}**; verificação aprovada.',
                  '- Resposta: `'+abbreviate(row['response']).replace('`','\\`')+'`.']
        if row.get('response_recording'):
            lines.append('- Registro da resposta: '+row['response_recording']+'.')
    lines += ['## 6. Avaliação preliminar',
              'Não foi observado descumprimento dos controles exercitados. Isso não demonstra ausência de vulnerabilidades em toda a API. Isolamento e restrição administrativa foram confirmados com controles positivos; respostas 404 de rotas ausentes não foram usadas como prova de BFLA. A rejeição de algoritmo não permitido não equivale à auditoria de um fluxo RS256, que a aplicação não utiliza.',
              'O modelo não foi retreinado ou alterado neste complemento. Classificação não concede permissões: owner depende do usuário autenticado e administrador depende da configuração do servidor, não da intenção prevista ou de um role extra no token.',
              '## 7. Atividades pendentes e riscos residuais',
              '| Atividade | Situação | Motivo |','|---|---|---|',
              '| Revogação individual de JWT e sessões | Pendente | Não há denylist/jti ou fluxo de logout/revogação no projeto atual |',
              '| Quotas e carga em /classify | Pendente | Não foi executado teste de carga; limite atual específico é do login |',
              '| Readiness operacional do classificador | Pendente | /health é liveness; indisponibilidade de inferência aparece como 503 em /classify |',
              '| TLS/proxy/ambiente de implantação | Pendente | Validação limitada a HTTP loopback e ASGI |',
              '| RBAC granular e novas operações de recurso | Não implementado / fora do escopo | Somente a função /admin/status e GET/POST de reservas existem |',
              '| Reconhecimento por scanners e exploração de terceiros | Não executado / fora do escopo | Este complemento é defensivo, local e baseado em código |',
              '| Modelo OpenAI remoto | Pendente | Mantém-se a limitação de credencial já registrada no relatório funcional |',
              '## 8. Conclusão',
              f'Os sete controles solicitados possuem evidências de testes locais, com {summary["requests"]} verificações HTTP e {tests} testes automatizados aprovados na suíte completa. As observações são limitadas ao TourShield avaliado, às fixtures e aos casos documentados. Nenhum resultado pendente foi apresentado como execução real.']
    document=re.sub(r'(?m)^(\|.*\|)\n\n(?=\|)',r'\1\n','\n\n'.join(lines))
    (ROOT/'pentest/log_parcial.md').write_text(document+'\n',encoding='utf-8',newline='\n')
    manifest={'controls':controls,'http_checks':summary['requests'],'pytest_passed':tests,
              'scope':'avaliação defensiva da própria API; sem alvos externos',
              'evidence':{'http':'pentest/evidencias/defensiva_tp4/http_results.json',
                          'routes':'pentest/evidencias/defensiva_tp4/route_inventory.json',
                          'pytest':'reports/tests_defensive_tp4.xml'}}
    (EVIDENCE/'controls.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8',newline='\n')
    files=sorted(p for p in EVIDENCE.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt')
    (EVIDENCE/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name for p in files)+'\n',encoding='utf-8',newline='\n')
    print(f'Log defensivo gerado: 7 controles; {summary["requests"]} verificações HTTP; {tests} testes pytest.')


if __name__=='__main__':main()
