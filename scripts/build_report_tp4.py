"""Academic TP4 report from executed application/ML/functional evidence only."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,Preformatted

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/tp4'
summary=json.loads((OUT/'classification_summary.json').read_text(encoding='utf-8'))
conversation=json.loads((OUT/'agent_conversation.json').read_text(encoding='utf-8'))
api=json.loads((OUT/'functional_api.json').read_text(encoding='utf-8'))
suite=ET.parse(ROOT/'reports/tests_tp4.xml').getroot().find('testsuite')
assert suite is not None and int(suite.attrib['failures'])==0 and int(suite.attrib['errors'])==0
tests=int(suite.attrib['tests'])
metrics=pd.read_csv(OUT/'metrics.csv')
perclass=pd.read_csv(OUT/'metrics_by_class.csv',index_col=0)
grid=pd.read_csv(OUT/'grid_search.csv')
repository='https://github.com/lenagomesz/tourshield-api-pb-tp1'
branch=repository+'/tree/tp4-classifier-agent'
NAVY,TEAL,LIGHT=[colors.HexColor(x) for x in ['#12334A','#16898C','#EAF3F5']]
styles=getSampleStyleSheet()
for name,font,size,lead,color in [
    ('TitleTS','Helvetica-Bold',30,35,NAVY),('SubTS','Helvetica',15,21,TEAL),
    ('AuthorsTS','Helvetica-Bold',17,25,NAVY),('BodyTS','Helvetica',10,15,NAVY),
    ('SmallTS','Helvetica',8,11,NAVY),('H1TS','Helvetica-Bold',20,25,NAVY),
    ('H2TS','Helvetica-Bold',12,17,TEAL),('CodeTS','Courier',8,11,NAVY)]:
    styles.add(ParagraphStyle(name=name,fontName=font,fontSize=size,leading=lead,
                            textColor=color,spaceAfter=9))
styles['CodeTS'].backColor=LIGHT
styles['CodeTS'].borderPadding=7
story=[]
def p(t,s='BodyTS'):story.append(Paragraph(t,styles[s]))
def title(n,t):p(f'{n:02d} / {t}','H1TS')
def page():story.append(PageBreak())
def table(rows,widths,small=False):
    t=Table([[Paragraph(escape(str(x)).replace('\n','<br/>'),styles['SmallTS' if small else 'BodyTS']) for x in r] for r in rows],colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),LIGHT),
        ('LINEBELOW',(0,0),(-1,0),1,TEAL),('LEFTPADDING',(0,0),(-1,-1),7),
        ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([t,Spacer(1,12)])
def image(name,width=495):
    pic=Image(str(OUT/'figures'/name))
    pic.drawHeight=width*pic.imageHeight/pic.imageWidth
    pic.drawWidth=width
    story.append(pic)
def code(lines):story.append(Preformatted('\n'.join(lines),styles['CodeTS']))

story.append(Spacer(1,35))
p('TOURSHIELD','TitleTS')
p('API de Turismo e Reservas','SubTS')
p('TP4 - Integração de Classificador de Intenções, Agente Autônomo e Avaliação de Segurança de API','H1TS')
story.append(Spacer(1,20))
p('Helena Gomes','AuthorsTS')
p('Maria Paula','AuthorsTS')
p('Projeto de Bloco: Análise e Segurança de Agentes de IA [26E3_5]')
p('21 de novembro de 2026')
story.append(Spacer(1,15))
table([['Classificador','Integração','Verificação'],
       ['20 intenções\n93,67% de acurácia','FastAPI + JWT\nAgents SDK + ferramenta',f'{tests} testes aprovados\n3 turnos demonstrados']],[165,165,165])
p('<b>Recorte desta entrega:</b> desenvolvimento da aplicação, aprendizado de máquina, integração e testes funcionais. A avaliação de segurança do título geral do TP4 será tratada em etapa separada e não integra os resultados deste relatório.')
p('<b>Transparência da demonstração:</b> o SDK, a ferramenta e a inferência HTTP foram executados; a geração textual é determinística e simulada. Não houve execução com um modelo OpenAI hospedado por falta de chave configurada.')
p(f'<link href="{branch}" color="#16898C">Repositório de continuidade - branch TP4</link>')
page()

title(1,'Introdução e objetivos')
p('O TourShield organiza atendimento turístico em intenções como reserva de hotel, voo, bagagem, localização e recompensas. Os TPs anteriores construíram o domínio analítico e a API modular. Nesta etapa, a mensagem passa a ser classificada por um pipeline supervisionado e consultada por uma ferramenta do agente.')
p('O objetivo é encaminhar solicitações, sem realizar compras, cancelar reservas reais, comprovar localização ou conceder benefícios. A aplicação continua usando os mesmos dados e convenções; a nova função não substitui o histórico estatístico.')
table([['Continuidade','Implementação atual'],['Dados','CLINC150 curado, 3.000 mensagens em inglês; 20 intenções e splits originais.'],
       ['Arquitetura','main.py; app/routes; SQLModel; modelos Pydantic; JWT e middleware preservados.'],
       ['Novos componentes','app/classifier.py, rota /classify, app/agent.py e scripts de demonstração.'],
       ['Compatibilidade','/predict conserva seu contrato placeholder; notebooks e PDFs TP1-TP3 permanecem disponíveis.'],
       ['Identificação','Helena Gomes e Maria Paula; versão da API 0.4.0.']],[125,370])
p('Os requisitos priorizados são: treinamento e avaliação confiáveis; persistência do pipeline; inferência autenticada; integração Agent/Runner/function_tool; conversa reproduzível; testes e documentação. A geração remota é identificada como integração implementada ainda não validada com credenciais.')
p('Fluxo da aplicação','H2TS')
code(['Mensagem -> Agent + Runner.run -> classify_intent',
      '   -> HTTP POST /classify + JWT do contexto',
      '   -> TF-IDF + LogisticRegression',
      '   -> intent + probability + model_version -> resposta'])
page()

title(2,'Metodologia e dados')
p('Foi reutilizado data/tourshield_clean.csv, derivado do CLINC150 e preservado desde os TPs anteriores. Cada intenção tem 150 mensagens. Não houve tradução, geração de novos exemplos ou troca de rótulos; o hash dos dados acompanha o manifesto do artefato.')
table([['Partição','Exemplos','Papel'],['Treino','2.000 (100/classe)','Aprender vocabulário, IDF e pesos nos candidatos.'],['Validação','400 (20/classe)','Selecionar hiperparâmetros por macro-F1.'],['Teste','600 (30/classe)','Avaliação final após congelar a configuração.'],['Refit final','2.400','Reajustar melhor pipeline em treino + validação.']],[100,125,270])
p('Somente message é entrada do modelo. Intent, ID, split e comprimentos não são features. A checagem de mensagens normalizadas encontrou zero duplicatas entre as partições. Todo pré-processamento permanece dentro do Pipeline; não houve fit do TF-IDF na base inteira antes da avaliação.')
p('Escolhas de modelagem','H2TS')
code(['Pipeline([',
      '  ("tfidf", TfidfVectorizer(ngram_range=(1, 2),',
      '      lowercase=True, max_features=10000,',
      '      sublinear_tf=True, min_df=2)),',
      '  ("classifier", LogisticRegression(C=1,',
      '      solver="lbfgs", max_iter=2000))',
      '])'])
p('A configuração inicial segue o plano TP3. Não se removem stopwords automaticamente, preservando possíveis negações. A logística L2 oferece inferência leve em texto esparso e probabilidades por classe. Uma baseline de frequência permite distinguir aprendizado útil de acerto devido ao balanceamento.')
p('<b>Limite metodológico:</b> a EDA anterior descreveu também a partição teste. O protocolo de ajuste não a utiliza, mas isso não transforma o benchmark em avaliação externa totalmente intocada. Confirmação em português e dados operacionais exige nova amostra.')
page()

title(3,'GridSearchCV e seleção')
p('A grade pesquisa dois hiperparâmetros com três valores cada: min_df em {1, 2, 3} e C em {0,1; 1; 10}, totalizando nove combinações. PredefinedSplit preserva o treino/validação já combinado no TP3: é um holdout fixo, não validação de múltiplos folds.')
table([['C','min_df','F1 treino','F1 validação','Rank']]+[[f'{r["param_classifier__C"]:g}',str(int(r['param_tfidf__min_df'])),f'{r["mean_train_f1_macro"]:.4f}',f'{r["mean_test_f1_macro"]:.4f}',str(int(r['rank_test_f1_macro']))] for r in grid.to_dict('records')],[65,70,115,140,105])
p(f'<b>Melhores parâmetros:</b> C=10 e min_df=1. Macro-F1 validação inicial: {summary["initial_validation_macro_f1"]:.5f}; otimizado: {summary["best_validation_macro_f1"]:.5f}; ganho de {summary["validation_gain_pp"]:.4f} ponto percentual.')
p('O ganho de validação compara os mesmos exemplos de treino e validação. Após a escolha, o melhor pipeline é reajustado nos 2.400 exemplos. A configuração inicial também recebe esse mesmo refit para que a comparação de teste não confunda quantidade de dados com efeito de hiperparâmetro.')
p('O F1 de treino quase perfeito em C=10 alerta para memorizações do benchmark; o teste mais baixo reforça que o modelo não deve ser apresentado como solução geral de atendimento. Os resultados de uma única validação não permitem estimar estabilidade entre folds ou intervalos de confiança.')
p('Evidência: reports/tp4/grid_search.csv e notebook executado. O score chamado mean_test_f1_macro no objeto GridSearchCV corresponde ao holdout de validação, não aos 600 exemplos de teste final.')
page()

title(4,'Métricas e comparação com baseline')
table([['Modelo','Acurácia','Macro-F1','AUC OvR macro']]+[[r['modelo'],f'{r["accuracy"]:.4f}',f'{r["macro_f1"]:.4f}',f'{r["roc_auc_ovr_macro"]:.4f}'] for r in summary['test_metrics']],[170,100,100,125])
p('O modelo final acerta 562 de 600 mensagens e erra 38. O ganho de macro-F1 sobre a configuração inicial é de 1,1575 ponto percentual. Há aprendizado útil de relações lexicais entre mensagem e intenção: a melhora supera amplamente a baseline, cuja acurácia é 5% por prever sempre uma das classes balanceadas.')
p('Precision mede a proporção correta das previsões de uma classe; recall mede quanto daquela classe verdadeira foi recuperado. F1 equilibra essas duas medidas. Macro-F1 dá o mesmo peso a cada intenção; como há 30 exemplos por classe, weighted-F1 coincide numericamente com a média macro neste teste.')
table([['Intenção','Precision','Recall','F1','n']]+[[label,f'{r["precision"]:.3f}',f'{r["recall"]:.3f}',f'{r["f1-score"]:.3f}',str(int(r['support']))] for label,r in perclass.iterrows()],[215,70,70,70,70],small=True)
page()

title(5,'Matriz de confusão')
image('confusion_matrix.png',495)
p('Linhas: rótulo verdadeiro; colunas: previsão. Cada linha contém 30 mensagens. Reservas de hotel, voo, cancelamento e confirmação apresentam recall 1,0 neste recorte. Isso não garante o mesmo desempenho em textos novos ou outro idioma.')
p('A classe distance tem recall 0,667: dez de seus trinta exemplos são confundidos com outras intenções. Redeem_rewards tem sete mensagens previstas como rewards_balance. Priorizar esses pares para revisão de exemplos e esclarecimento ao usuário, sem mudar o modelo usando os erros do teste.')
p('Fonte: classificação executada em eda/classification_tp4.ipynb; imagem gerada por confusion_matrix e ConfusionMatrixDisplay. Não é figura ilustrativa ou captura reconstruída.')
page()

title(6,'ROC-AUC e interpretação')
image('roc.png',470)
p('ROC-AUC foi calculada sobre probabilidades, com one-vs-rest e média macro, respeitando a ordem model.classes_. Cada intenção é comparada às demais. O gráfico mostra quatro classes para legibilidade; auc_by_class.csv contém as vinte.')
p('AUC final 0,99807 indica bom ranking neste benchmark. Ela não equivale a 99,8% de acerto de rótulo, não mede calibração e não garante que o maior escore seja confiável em entradas desconhecidas. A acurácia efetiva continua sendo 93,67%.')
p('O classificador é fechado: sempre seleciona uma das vinte classes. Não há classe out-of-scope treinada, múltiplas intenções ou detecção de idioma. Produção em português exige outro conjunto rotulado e avaliação específica; probabilidade máxima isolada não substitui essa validação.')
p('As classes com menor F1 são distance (0,800), redeem_rewards (0,836) e rewards_balance (0,862). Esses resultados delimitam o aprendizado útil e motivam perguntas de esclarecimento antes de encaminhamentos sensíveis.')
page()

title(7,'Persistência e integração FastAPI')
p('models/intent_classifier.joblib serializa TF-IDF e classificador juntos. manifest.json registra SHA-256, classes, versão tourshield-intents-tp4-v1, sklearn 1.9.1, hash do CSV e parâmetros. O artefato tem aproximadamente 1,13 MiB.')
p('O lifespan da API carrega e verifica o artefato. O loader confere o hash dos bytes e só depois desserializa o mesmo conteúdo, mantendo cache por processo. Somente arquivos confiáveis do projeto devem ser carregados; substituir modelo e manifesto não é impedido por checksum sozinho.')
code(['@router.post("/classify", response_model=ClassifyResponse)',
      'def classify(payload: ClassifyRequest,',
      '             username: str = Depends(current_user)):',
      '    return classify_text(payload.text)'])
p('Trecho resumido da rota; o arquivo completo também trata indisponibilidade. ClassifyRequest exige text como string estrita, sem branco, até 4.000 caracteres e sem extras. current_user reutiliza o JWT e as contas existentes. O servidor não armazena texto e não devolve o token.')
table([['Resposta','Condição'],['200','Texto válido, sessão válida e modelo carregado.'],['401','JWT ausente ou inválido.'],['422','Texto vazio, tipo inválido, limite excedido ou campos extras.'],['503','Artefato ausente, incompatível ou com integridade inválida.']],[80,415])
p('Exemplo executado','H2TS')
sample=next(x for x in api if x['case']=='classificacao')
code(['POST /classify','Authorization: Bearer [REDACTED]',
      json.dumps(sample['request_json']),
      'HTTP 200',f'intent: {sample["response"]["intent"]}',
      f'probability: {sample["response"]["probability"]:.6f}',
      f'model_version: {sample["response"]["model_version"]}'])
page()

title(8,'Agente de atendimento e ferramenta')
p('app/agent.py usa OpenAI Agents SDK 0.25.0: Agent com system prompt TourShield, ferramenta decorada e Runner.run. O token fica em AgentContext e não aparece nos argumentos visíveis ao modelo. A ferramenta consulta a API autenticada, valida a resposta e retorna JSON.')
code(['@function_tool',
      'async def classify_intent(ctx, text: str) -> str:',
      '    response = await ctx.context.client.post(',
      '        "/classify", json={"text": text},',
      '        headers={"Authorization":',
      '                 "Bearer " + ctx.context.token})',
      '    # O arquivo completo valida entrada, status e resposta.',
      '    return ClassifyResponse.model_validate(',
      '        response.json()).model_dump_json()',
      '',
      'result = await Runner.run(agent, history,',
      '    context=context, max_turns=4,',
      '    run_config=RunConfig(tracing_disabled=True))'])
p('As instruções pedem classificação do texto original, esclarecimento de ambiguidades e comunicação sem prometer reservas, preços, localização ou benefícios. A única ferramenta disponível classifica; não executa transações. O histórico é mantido em memória durante a sessão.')
p('Configuração e tratamento de falhas','H2TS')
p('No modo remoto, OPENAI_API_KEY e OPENAI_MODEL são obrigatórios e ficam no .env ignorado pelo Git. A senha da API é solicitada sem eco. O cliente usa timeout de dez segundos, não segue redirects e não herda proxy ambiental. Falhas HTTP e do ciclo remoto produzem orientação genérica de indisponibilidade.')
p('<b>O que foi executado:</b> Agent, Runner.run, function_tool, API por HTTP loopback e classificador treinado. <b>O que foi simulado:</b> geração/decisão do modelo de linguagem, por DemonstrationModel local. <b>Pendente:</b> validação com um modelo OpenAI hospedado e credencial real. Não se atribui a conversa a uma chamada remota inexistente.')
page()

title(9,'Demonstração de três turnos')
p('scripts/demo_agent_tp4.py cria uma instância descartável da mesma aplicação e executa três ciclos com histórico. Cada turno produz uma chamada real à ferramenta e uma resposta /classify. A fala é formatada pelo modelo determinístico de demonstração.')
for i,turn in enumerate(conversation['conversation'],1):
    p(f'Turno {i}','H2TS')
    p('<b>Usuário:</b> '+escape(turn['user']))
    p('<b>TourShield:</b> '+escape(turn['assistant']))
    table([['Intenção retornada pela API','Probabilidade'],[turn['tool_result']['intent'],f'{turn["tool_result"]["probability"]:.4%}']],[350,145])
p('Os três turnos representam intenções diferentes: book_hotel, rewards_balance e cancel_reservation. O resultado comprova a integração da ferramenta com a API e a preservação do histórico do Runner. Não comprova raciocínio autônomo de um LLM remoto, eficácia em português ou realização de operações de negócio.')
p('Evidências: reports/tp4/agent_conversation.md e agent_conversation.json; teste test_sdk_runner_really_invokes_api. Nenhum token ou senha é exportado nesses arquivos.')
page()

title(10,'Testes funcionais e evidências')
p(f'<b>Resultado real: {tests} testes aprovados, zero falhas e zero erros.</b> A suíte mantém os testes de regressão das entregas anteriores e acrescenta casos para a nova rota, startup do modelo, respostas de erro e ciclo SDK/ferramenta. O XML está em reports/tests_tp4.xml.')
table([['Exemplo HTTP executado','Status','Evidência'],*[[x['case'],str(x['status']),x['path']] for x in api]],[180,70,245])
p('Os exemplos HTTP são executados em loopback com banco, conta e segredo descartáveis. Os testes automatizados usam a mesma app via ASGI e um banco isolado por teste; nenhum usuário ou banco persistente anterior é alterado. 503 para modelo ausente/corrompido é coberto por pytest, não por falha em produção.')
table([['Caso','Verificação'],['Startup','Modelo carregado no lifespan; classifier_ready=True.'],['Inferência','book_hotel para exemplo conhecido; probabilidade no intervalo e versão correta.'],['Erros de entrada','Branco, tipo numérico, texto longo, campos extras e body ausente retornam 422.'],['Artefato','Bytes com checksum inválido não são desserializados; ausência retorna 503.'],['Ferramenta','Schema visível contém somente text; sessão inválida é tratada; Runner invoca a API.']],[110,385])
p('A execução local confirma o comportamento observado. Não equivale a teste de carga, teste com modelo remoto ou avaliação de segurança completa. O check já existente do GitHub Actions foi preservado; seu resultado remoto deve ser consultado no repositório.')
page()

title(11,'Verificação do escopo e reprodução')
criteria=[
('Continuidade','docs/implementation_tp4.md','Concluído'),
('Pipeline TF-IDF + logística','eda/classification_tp4.ipynb','Concluído'),
('Separação treino/val/teste','eda/classification_tp4.py','Concluído'),
('Grid 2 parâmetros x 3 valores','reports/tp4/grid_search.csv','Concluído'),
('Métricas e gráficos','reports/tp4/metrics_by_class.csv','Concluído'),
('Baseline e interpretação','reports/tp4/metrics.csv','Concluído'),
('Joblib e startup','models/manifest.json; main.py','Concluído'),
('/classify autenticado','app/routes/classify.py','Concluído'),
('Validação e erros HTTP','tests/test_tp4.py','Concluído'),
('SDK e ferramenta integrada','app/agent.py','Concluído'),
('Conversa com modelo remoto','reports/tp4/agent_conversation.md','Parcial'),
('Testes e documentação','reports/tests_tp4.xml; README.md','Concluído')]
table([['Critério do escopo atual','Arquivo principal','Status']]+[list(x) for x in criteria],[170,245,80],small=True)
p('A matriz de 12 itens é uma decomposição técnica do recorte solicitado, não a rubrica oficial completa do professor e não uma estimativa de nota. Há 11 itens concluídos e um parcial: a conversa executa o SDK/API, mas não um modelo hospedado. Segurança está fora desta matriz por decisão de escopo.')
code(['python -m pip install -r requirements-lock.txt',
      'python -m scripts.build_classification_notebook',
      'python -m scripts.demo_classify_tp4',
      'python -m scripts.demo_agent_tp4',
      'pytest tests/ -v --junitxml=reports/tests_tp4.xml',
      'uvicorn main:app --reload --no-proxy-headers --no-server-header'])
p('O modelo serializado já está no repositório; treinar de novo é necessário apenas para reprodução. Para novo ambiente, configurar JWT_SECRET aleatório e cadastrar usuário com scripts.create_user; para ambiente existente, reutilizar .env sem sobrescrevê-lo. Modo remoto: configurar OPENAI_API_KEY/OPENAI_MODEL e executar python -m app.agent.')
verification=['# TourShield TP4 - Verificação do escopo atual','Helena Gomes e Maria Paula | 21/11/2026',
              '| Critério | Arquivo | Status |','|---|---|---|']
verification += [f'| {a} | {b} | {c} |' for a,b,c in criteria]
verification += ['', '11/12 itens concluídos (91,7%) neste recorte funcional, com pesos iguais e parciais contados como zero. Não é percentual da rubrica oficial completa ou previsão de nota.',
                 'Parcial: a conversa de três turnos usa SDK/API reais, com geração determinística simulada; não houve modelo OpenAI hospedado.',
                 'A avaliação de segurança é uma etapa separada e não integra esta matriz.']
(ROOT/'docs/verification_tp4.md').write_text('\n\n'.join(verification)+'\n',encoding='utf-8')
page()

title(12,'Conclusão e referências')
p('O TourShield evoluiu da base exploratória para uma aplicação com classificação supervisionada persistida e inferência autenticada. A melhora sobre a baseline e sobre a configuração inicial indica aprendizado útil no benchmark. A integração entre SDK, ferramenta, HTTP e pipeline foi exercitada em três turnos e confirmada por testes.')
p('Os principais limites são cobertura restrita às vinte intenções em inglês, ausência de dados operacionais/out-of-scope, probabilidades não calibradas e falta de execução com modelo OpenAI remoto. O sistema deve encaminhar pedidos e solicitar esclarecimentos, sem apresentar inferência como autorização de negócio.')
p('Próximos passos: validar o agente hospedado com credenciais do operador; avaliar português e entradas desconhecidas; coletar métricas de latência e calibração; obter amostra temporal externa; e realizar a avaliação de segurança em etapa própria. O histórico dos TPs permanece disponível.')
sources=[
('Larson et al. (2019). An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction.','https://aclanthology.org/D19-1131/'),
('CLINC150: código e dataset original; licença CC BY 3.0.','https://github.com/clinc/oos-eval'),
('Scikit-learn: Pipeline e boas práticas contra vazamento.','https://scikit-learn.org/stable/common_pitfalls.html'),
('Scikit-learn: GridSearchCV e PredefinedSplit.','https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html'),
('Scikit-learn: ROC-AUC multiclasse.','https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html'),
('OpenAI Agents SDK: Agent, Runner e ferramentas.','https://openai.github.io/openai-agents-python/quickstart/'),
('OpenAI Agents SDK: interface Model para a demonstração determinística.','https://openai.github.io/openai-agents-python/ref/models/interface/'),
('FastAPI: dependências e integração de aplicações.','https://fastapi.tiangolo.com/tutorial/dependencies/')]
for text,url in sources:p(f'<link href="{escape(url)}" color="#16898C">{escape(text)}</link>','SmallTS')
p('Referências consultadas em 21/11/2026. O dataset e a licença preservados nos TPs anteriores constam em data/provenance.json e data/LICENSE-CLINC150.txt.','SmallTS')
p(f'<b>Repositório:</b> <link href="{repository}" color="#16898C">{repository}</link>','SmallTS')
p(f'<b>Entrega TP4:</b> <link href="{branch}" color="#16898C">branch tp4-classifier-agent</link>','SmallTS')

def footer(canvas,doc):
    canvas.setStrokeColor(TEAL);canvas.line(50,41,A4[0]-50,41)
    canvas.setFont('Helvetica',8);canvas.setFillColor(NAVY)
    canvas.drawString(50,27,'TourShield | Helena Gomes e Maria Paula | TP4')
    canvas.drawRightString(A4[0]-50,27,str(doc.page))
pdf=ROOT/'output/pdf/helena_gomes_PB_TP4.PDF'
SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=45,bottomMargin=55,
                  title='TP4 - Integração de Classificador de Intenções, Agente Autônomo e Avaliação de Segurança de API',
                  author='Helena Gomes e Maria Paula').build(story,onFirstPage=footer,onLaterPages=footer)
print('PDF gerado:',pdf)
