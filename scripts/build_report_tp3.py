"""Generate TP3 PDF from executed regression, pytest, CI and ZAP evidence."""
import json
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf"
OUT.mkdir(parents=True, exist_ok=True)
reg = json.loads((ROOT / "reports/tp3/regression_summary.json").read_text(encoding="utf-8"))
zap = json.loads((ROOT / "reports/zap_tp3/scan-metadata.json").read_text(encoding="utf-8"))
ci = json.loads((ROOT / "reports/tp3/ci_evidence.json").read_text(encoding="utf-8"))
audit = json.loads((ROOT / "reports/tp3/dependency-audit.json").read_text(encoding="utf-8"))
suite = ElementTree.parse(ROOT / "reports/tests_tp3.xml").getroot().find("testsuite")
assert suite is not None and suite.attrib["failures"] == "0" and suite.attrib["errors"] == "0"
tests = int(suite.attrib["tests"])
success = next(r for r in ci["latest_runs"] if r["conclusion"] == "success")
assert ci["enforce_admins"] and "security-tests" in ci["required_status_checks"]["contexts"]
vulnerabilities = sum(len(x["vulns"]) for x in audit["dependencies"])
metrics = pd.DataFrame(reg["metrics"])
NAVY, TEAL, LIGHT = [colors.HexColor(x) for x in ["#12334A", "#16898C", "#EAF3F5"]]
styles = getSampleStyleSheet()
for name, font, size, lead, color in [
    ("TitleTS", "Helvetica-Bold", 30, 35, NAVY), ("SubTS", "Helvetica", 15, 21, TEAL),
    ("BodyTS", "Helvetica", 10, 15, NAVY), ("SmallTS", "Helvetica", 8, 11, NAVY),
    ("H1TS", "Helvetica-Bold", 20, 25, NAVY), ("H2TS", "Helvetica-Bold", 12, 17, TEAL),
    ("CodeTS", "Courier", 8, 12, NAVY)]:
    styles.add(ParagraphStyle(name=name, fontName=font, fontSize=size, leading=lead,
                             textColor=color, spaceAfter=10 if name != "SmallTS" else 6))
styles["CodeTS"].backColor = LIGHT
styles["CodeTS"].borderPadding = 7
story = []


def p(text, style="BodyTS"):
    story.append(Paragraph(text, styles[style]))


def title(number, text):
    p(f"{number:02d} / {text}", "H1TS")


def page():
    story.append(PageBreak())


def table(rows, widths, small=False):
    t = Table([[Paragraph(escape(str(v)).replace("\n", "<br/>"), styles["SmallTS" if small else "BodyTS"])
                for v in row] for row in rows], colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("BACKGROUND", (0,0), (-1,0), LIGHT),
        ("LINEBELOW", (0,0), (-1,0), 1, TEAL), ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4)]))
    story.append(t)
    story.append(Spacer(1, 12))


def image(name, width=495):
    img = Image(str(ROOT / "reports/tp3/figures" / name))
    img.drawHeight = img.imageHeight / img.imageWidth * width
    img.drawWidth = width
    story.append(img)


def code(lines):
    p("<br/>".join(escape(s).replace(" ", "&nbsp;") for s in lines), "CodeTS")


# Cover
story.append(Spacer(1, 50))
p("TOURSHIELD", "TitleTS")
p("API de Turismo e Reservas", "SubTS")
p("Consolidação e transição preditiva", "SubTS")
story.append(Spacer(1, 20))
p("Projeto de Bloco | Trabalho Prático 3", "H2TS")
p("<b>Helena Gomes</b><br/>25 de outubro de 2026")
p("Competência integradora: consolidar o sistema estatístico e a API segura, documentando a transição para a fase preditiva.")
story.append(Spacer(1, 18))
table([["Regressão didática", "Segurança e CI", "Planejamento T2"],
       ["R² teste: 0,879\nRMSE: 1,31 palavra", f"{tests} testes aprovados\nCheck exigido na main",
        "TF-IDF + classificação\n20 intenções definidas"]], [165,165,165])
p("A API permanece sem modelo de classificação e sem novas funções de negócio. /docs e CI consolidam a base para o laboratório de pentest.")
p("<b>Pendência externa declarada:</b> colega adversário, URL/IP da API e confirmação de acesso ainda não foram definidos. A aluna solicitou concluir os demais itens; essa confirmação não foi inventada.")
p('<link href="https://github.com/lenagomesz/tourshield-api-pb-tp1" color="#16898C">github.com/lenagomesz/tourshield-api-pb-tp1</link>')
page()
# 1
title(1, "Consolidação do Trimestre 1")
table([["Componente", "Estado consolidado"],
    ["Dados", "CLINC150, recorte TourShield de 3.000 mensagens em inglês, 20 intenções, licença CC BY 3.0."],
    ["Qualidade", "Shape original (3.000, 4), limpo (3.000, 6). Zero ausentes, duplicatas normalizadas ou conflitos; nenhuma linha removida."],
    ["Splits", "2.000 treino / 400 validação / 600 teste, preservados desde TP1."],
    ["EDA e estatística", "Histogramas, barras, boxplot, correlações, scatters e teste Mann-Whitney de reservas/localização no TP2."],
    ["API v0.3.0", "FastAPI, JWT/Argon2, SQLModel, ownership, extra=forbid, headers, CORS e limite de autenticação."],
    ["Transição", "Regressão numérica didática separada da API; classificação de intenção planejada para T2."]], [125,370])
p("A EDA do TP2 encontrou Pearson 0,935 entre caracteres e palavras e diferença exploratória de comprimento entre reservas e localização. Os achados ajudam a formular experiências, mas não resolvem classificação nem fraude.")
p("Por que o pivô é necessário", "H2TS")
p("Análise descritiva explica composição e limitações da base; regressão mostra um problema numérico; o futuro classificador responderá qual intenção corresponde à mensagem. São objetivos e métricas distintos.")
p("Permanecem as limitações: crowdsourcing, idioma inglês, intenção única, balanceamento artificial, autores desconhecidos e ausência de GPS, transações ou fraude confirmada. Os dados de teste já foram descritos na EDA; será necessária confirmação externa.")
p("Fonte: Stefan Larson et al. (2019), CLINC150, github.com/clinc/oos-eval. Atribuição, licença, revisão e hashes estão em data/ e no manifesto de proveniência.", "SmallTS")
page()
# 2
title(2, "Pipeline de regressão linear")
p("<b>Alvo:</b> n_words, número de palavras delimitadas por espaços. Baseline pela média do treino, regressão simples por n_chars e regressão múltipla por atributos textuais. Experimento didático, sem acionar /predict.")
code(["ColumnTransformer (features numéricas)", "  -> SimpleImputer (mediana do treino)", "  -> VarianceThreshold (remove constantes)", "  -> StandardScaler (ajustado no treino)", "  -> LinearRegression"])
p("Preditores propostos: caracteres, dígitos, pontuação e proporção de maiúsculas ASCII. A última é constante zero no treino e foi excluída pela pipeline. A múltipla mantém três variáveis. Intenção, ID, split e n_words não entram em X; comprimento médio da palavra é omitido para não reconstruir o alvo diretamente.")
p("Resultados no teste - 600 mensagens", "H2TS")
rows = [["Modelo", "R²", "RMSE (palavras)", "MAE (palavras)"]]
labels = {"baseline_mean": "Média do treino", "linear_simple": "Linear simples", "linear_multiple": "Linear múltipla"}
for row in metrics.loc[metrics["split"].eq("test")].itertuples():
    rows.append([labels[row.model], f"{row.r2:.4f}", f"{row.rmse_words:.4f}", f"{row.mae_words:.4f}"])
table(rows, [155,85,135,120])
p("A múltipla melhora pouco sobre a simples: ΔR² aproximadamente 0,0043 e redução de RMSE de 0,023 palavra. Não exagerar importância prática. O baseline pode ter R² negativo porque usa a média do treino, não a média do próprio teste.")
p("R² não é acurácia; RMSE enfatiza erros maiores e tem unidade de palavras. Transformações aprendidas são ajustadas só no treino. Não houve busca de hiperparâmetros, remoção de outliers ou escolha guiada pelo teste.")
p("Coeficientes padronizados são associações: caracteres 3,1976; dígitos 0,2633; pontuação -0,2028 palavra por desvio padrão do treino, mantendo os demais fixos. Não há interpretação causal.", "SmallTS")
page()
# 3
title(3, "Resíduos e Q-Q plot")
image("01_residual_qq.png")
p("Figura 1. Resíduo observado - previsto e Q-Q dos resíduos padronizados, no teste. Fonte: elaboração própria sobre CLINC150.", "SmallTS")
p("As faixas diagonais no residual plot refletem o alvo discreto. Os erros se distribuem em torno de zero, com dispersão variável e alguns extremos. Média residual: -0,0904 palavra, indicando pequena superestimação; DP: 1,3082.")
p("O Q-Q acompanha a reta na região central e se desvia nas caudas, principalmente na superior. Assimetria 0,2636 e excesso de curtose 0,3521 não demonstram normalidade exata. Não foi realizado teste formal de homoscedasticidade; a correlação descritiva entre |resíduo| e previsto é 0,1611.")
image("02_observed_predicted.png", 310)
p("Figura 2. Observado e previsto; linha tracejada indica igualdade. A dispersão mostra erros mesmo com R² elevado.", "SmallTS")
page()
# 4
title(4, "Limitações da regressão")
p("Relação estrutural e utilidade", "H2TS")
p("Caracteres e palavras são medidas do mesmo texto. O R² alto é em grande parte explicado por essa relação estrutural. O número de palavras pode ser contado diretamente, sem ML: esta regressão não tem utilidade operacional para encaminhar atendimento.")
p("Limites estatísticos", "H2TS")
p("OLS produz valores contínuos e pode prever frações ou números negativos fora da amostra. Não houve predição negativa no teste, mas isso não garante suporte correto em produção. O Q-Q indica desvios nas caudas e não autoriza intervalos paramétricos sem avaliar premissas.")
p("Normalidade de resíduos não é requisito para calcular previsões lineares; seria relevante para certas inferências e intervalos tradicionais. Não foram estimados intervalos de previsão, causalidade ou significância de coeficientes.")
p("Limites de dados e validação", "H2TS")
p("A proporção de maiúsculas ASCII é constante nesta amostra e não generaliza automaticamente para português. Autores repetidos podem criar dependência não auditável. Validação e teste já foram descritos no TP1/TP2: não constituem amostra externa nova.")
p("Conclusão para a transição", "H2TS")
p("O exercício cumpre a tarefa numérica, mas não responde qual é a intenção do usuário. R² e RMSE não medem classificação de intenção, localização física ou fraude. T2 deverá usar rótulos nominais, representação de texto e métricas de classificação, mantendo segurança independente da saída do modelo.")
p("Notebook executado: eda/regression_tp3.ipynb, com fonte equivalente .py e seção Limitações e próximos passos. Métricas por split, coeficientes e resíduos rastreáveis por ID estão em reports/tp3/.", "SmallTS")
page()
# 5
title(5, "Auditoria final da API")
table([["Controle", "Status / evidência"],
    ["Autenticação / BOLA", "Resolvido: JWT válido, conta ativa, Argon2 e consulta por ID+owner; sem token 401 e outro usuário 404."],
    ["Input / banco", "Resolvido: extra=forbid, faixas e limites; SQLModel sem SQL raw."],
    ["Headers / CORS / limite", "Resolvido: headers também em erros, allowlist, login 5/IP/60s, body 16 KiB e timeout 10 s."],
    ["/docs e OpenAPI", "Resolvido: Swagger UI 5.34.0 local, sem CDN/inline, CSP específica, assets verificados, sem token persistido."],
    ["Dependências", f"Snapshot pip-audit: {len(audit['dependencies'])} pacotes, {vulnerabilities} vulnerabilidades conhecidas. Reavaliar antes de implantar."],
    ["MFA / revogação / infra", "Aceito no laboratório: sem MFA, revogação individual, limiter distribuído, backup e alertas externos."],
    ["Prontidão", "Alvo local exercitado com duas contas fictícias; publicação externa e colega confirmado ainda pendentes."]], [145,350], small=True)
p(f"<b>ZAP final:</b> {zap['zap_version']}, modo safe, {len(zap['requests'])} requisições em TLS local, 61 regras passivas, fila zerada; sem spider ou active scan. Incluiu /docs e assets. High=0; Medium=0; Low=33; Informational=10.")
p("Não havia Medium/High pendente do TP2. Os 33 Low são possíveis timestamps detectados em constantes numéricas do bundle público do Swagger, como o vetor SHA-1. Foram revisados e aceitos como falsos positivos; não são datas de sessão/usuário. Nenhuma regra foi suprimida.")
p("Os informativos correspondem a cache intencional, identificação de login/sessão e comentário de biblioteca. Evidências e aceites em reports/zap_tp3/findings.md. HTML e JSON são exportados pelo ZAP, com redação apenas de segredos efêmeros.")
p("Scan passivo inspeciona mensagens exercitadas, sem provar ausência de falhas. O certificado autoassinado é de laboratório; produção requer TLS válido e revisão de implantação. Checklist completo em docs/audit_final_tp3.md.", "SmallTS")
page()
# 6
title(6, "Testes, CI e bloqueio de merge")
table([["Área", "Casos executados"],
    ["Autenticação", "401 sem token; senha incorreta; JWT expirado, assinatura/claims/algoritmo inválidos e conta inativa."],
    ["Autorização", "Reserva própria 200; outra conta 404 igual ao inexistente; owner/status não podem ser atribuídos no body."],
    ["Validação", "Campo extra, mensagem vazia, GPS inválido/isolado, body grande e erro sem echo de dados."],
    ["Rate limiting", "Sexta tentativa bloqueada, Retry-After, recuperação por relógio injetado e XFF ignorado."],
    ["Documentação / HTTP", "Assets e hashes, OpenAPI com segurança, CSP/headers, CORS e /docs sem desativar autenticação."]], [130,365])
p(f"<b>pytest tests/ -v:</b> {tests} aprovados localmente, sem falhas. Evidência em reports/tests_tp3.xml. O aviso de depreciação TestClient/httpx não altera o resultado.")
p("O workflow .github/workflows/security-tests.yml executa em push e pull_request, com Python 3.12, dependências fixadas e permissões contents:read. Não usa continue-on-error; retorno não zero do pytest falha o job. Actions são fixadas por SHA e o XML é publicado como artefato.")
p("A branch main exige o check <b>security-tests</b> atualizado (strict=true), inclusive para administradores. Force push e exclusão estão bloqueados. Essa configuração foi lida de volta da API GitHub; apenas criar YAML não impediria merge sem a regra.")
p('Execução real aprovada:<br/><link href="' + success["html_url"] + '">' + success["html_url"] + '</link>', "SmallTS")
p("Commit verificado: " + success["head_sha"] + ". Snapshot da regra e execução: reports/tp3/ci_evidence.json. A publicação dos documentos finais também deve passar pelo check antes do merge.", "SmallTS")
page()
# 7: classification document 1/2
title(7, "Pergunta de classificação (1/2)")
p("<b>Dado um texto de atendimento ao cliente, qual é a intenção do usuário?</b> Entrada: mensagem. Saída: um dos 20 rótulos nominais abaixo. É classificação supervisionada multiclasse de intenção única.")
meanings = {
"book_flight": "Reservar voo", "book_hotel": "Reservar hotel", "cancel_reservation": "Cancelar reserva",
"confirm_reservation": "Confirmar reserva", "car_rental": "Alugar carro", "flight_status": "Consultar voo",
"lost_luggage": "Bagagem perdida", "carry_on": "Bagagem de mão", "travel_alert": "Alertas de viagem",
"travel_notification": "Notificar viagem", "travel_suggestion": "Sugestão de viagem", "international_visa": "Visto internacional",
"vaccines": "Vacinas para viagem", "plug_type": "Tipo de tomada", "current_location": "Localização atual",
"directions": "Orientações de rota", "distance": "Distância", "share_location": "Compartilhar localização",
"redeem_rewards": "Resgatar recompensas", "rewards_balance": "Consultar recompensas"}
table([["Intenção", "Significado", "n (%)"], *[[k,v,"150 (5%)"] for k,v in meanings.items()]], [180,225,90], small=True)
p("Total: 3.000 mensagens. Por classe: 100 treino / 20 validação / 30 teste. Distribuição uniforme é do desenho do benchmark, não da demanda por atendimento. Exemplo semântico futuro: mensagem de reserva de hotel -> book_hotel; não é predição de modelo já treinado.")
p("Documento separado: docs/classification_question_tp3.md. Fonte: Larson et al. (2019), CLINC150, CC BY 3.0.", "SmallTS")
page()
# 8 classification document 2/2
title(8, "Pergunta de classificação (2/2)")
p("Justificativa para ML supervisionado", "H2TS")
p("A base contém pares de mensagem e intenção rotulada. Um classificador aprende associações de vocabulário com rótulos e permite avaliar seus erros. Isso oferece um ponto inicial reproduzível antes de modelos mais complexos, sem criar regras arbitrárias de tamanho de texto.")
p("O baseline majoritário tem 5% de acurácia nesta distribuição uniforme. A avaliação deve considerar macro-F1, recall por intenção e matriz de confusão; acurácia sozinha pode ocultar classes confundidas. O modelo deve ser comparado a baselines em splits preservados.")
p("Por que regressão linear é inadequada", "H2TS")
p("Intenções são categorias sem ordem ou distância. Transformar rótulos em números 0-19 faria o erro quadrático tratar uma categoria como mais distante de outra sem fundamento. OLS também pode prever frações e valores fora do conjunto de classes.")
p("A regressão deste TP estima comprimento em palavras: R² alto apenas descreve esse alvo numérico. Não mede reconhecimento de intenção nem valida a tarefa de negócio. Regressão logística, apesar do nome, é um classificador que aprende escores/probabilidades por categoria.")
p("Escopo e limites de decisão", "H2TS")
p("O recorte não contempla intenção desconhecida ou múltiplas intenções por mensagem. Não prometer rejeição out-of-scope ou bom desempenho em português sem novos dados. Saldos e resgates são intenções genéricas, não comprovação de fraude turística.")
p("Classificação encaminha atendimento. Não comprova localização, titularidade da reserva ou elegibilidade para benefício. JWT, ownership, saldo e regras de negócio continuarão sendo verificados no servidor, independentemente da predição.")
p("Essas duas páginas formam o documento de pergunta de classificação solicitado; o Markdown separado fornece o mesmo escopo e a distribuição completa.", "SmallTS")
page()
# 9
title(9, "Planejamento técnico para T2")
table([["Decisão", "Protocolo predefinido"],
    ["Candidato principal", "Regressão logística multiclasse, regularização L2, solver lbfgs, max_iter=2.000."],
    ["Features", "Pipeline TF-IDF com lowercase, n-gramas (1,2), min_df=2, max_features=10.000 e sublinear_tf=True."],
    ["Pré-processamento", "Sem tradução ou stopwords automáticas; preservar negações. Vocabulário/IDF aprendidos só no treino."],
    ["Ajuste", "Comparar C=0,1; 1; 10 na validação; selecionar por macro-F1 e desempatar pela configuração mais simples."],
    ["Baselines / alternativa", "Classe majoritária e features de comprimento; LinearSVC como alternativa justificada pela validação."],
    ["Avaliação", "Macro-F1, acurácia, recall por classe, confusão, latência e tamanho. Congelar decisões antes do teste."],
    ["Confirmação externa", "Nova amostra autorizada em português, com multi-intenção/out-of-scope; documentar limites do teste já explorado."],
    ["Integridade", "Artefato produzido pelo projeto, hash e versão; não aceitar pickle/joblib enviado por usuário."]], [135,360])
p("Nenhum resultado de classificação é antecipado. Exigir ganho sobre baseline, registrar convergência e erros, e evitar prometer limiar sem experimento. Não usar ID, split ou intenção codificada como atributos de entrada.")
p("Integração futura", "H2TS")
p("Manter contrato e autenticação de /predict; distinguir modelo indisponível de baixa confiança. CI de segurança deve continuar obrigatório. O classificador não poderá conceder benefício ou executar ferramentas a partir do texto recebido.")
p("Plano completo: docs/t2_plan_tp3.md. A regressão numérica permanece apenas no notebook; não adiciona previsão de negócio à API.", "SmallTS")
page()
# 10
title(10, "Adversário e prontidão local")
table([["Campo exigido", "Estado em 25/10/2026"],
    ["Colega adversário", "Pendente - não informado pela aluna"],
    ["URL ou IP da API adversária", "Pendente - nenhum alvo inventado"],
    ["Confirmação de acesso", "Pendente - não recebida"],
    ["Escopo e janela", "Pendente de acordo entre participantes"]], [210,285])
p("A aluna informou que esses itens estão pendentes e solicitou concluir o restante. Essa dependência externa não foi apresentada como resolvida. Antes do TP4, registrar nome, URL, data da confirmação e escopo combinado, sem versionar senhas ou tokens.")
p("Prontidão da própria API", "H2TS")
p("O ZAP exercitou a aplicação local com duas contas fictícias e reserva própria/alheia. /health e /docs responderam 200; login funcionou; acesso sem token recebeu 401; outro proprietário, 404; entrada extra, 422; excesso de login, 429. Nenhum pentest foi iniciado contra terceiro.")
p("scripts/seed_pentest.py cria lab_alice e lab_bob em banco pentest.sqlite3, com reservas e senhas aleatórias. As credenciais ficam somente em tmp/pentest-credentials.json, ignorado pelo Git. O script não sobrescreve contas existentes.")
p("Limite da prontidão", "H2TS")
p("Prontidão local de laboratório não é produção nem acessibilidade remota. 127.0.0.1 não pode ser usado pelo colega como alvo público. Exposição externa requer acordo, TLS válido, contas fictícias, configuração de host/proxy e execução sem --reload.")
p("Sequência proposta: definir parceiro/alvo; congelar protocolo analítico; treinar/validar baselines e candidato; avaliar teste; integrar artefato confiável; repetir pytest/ZAP antes da próxima entrega. Prazos dependem do professor.")
page()
# 11
title(11, "Execução e evidências da entrega")
code(["python -m venv .venv", r".\.venv\Scripts\Activate.ps1", "python -m pip install -r requirements-lock.txt", "# Configure .env: segredo aleatório; DATABASE_PATH=./pentest.sqlite3", "python -m scripts.seed_pentest", "uvicorn main:app --reload --no-proxy-headers --no-server-header", "# Em outro terminal:", "pytest tests/ -v", "python eda/regression_tp3.py", "python -m scripts.build_regression_notebook", "python -m scripts.run_zap --tp3"])
table([["Evidência", "Local"],
    ["Notebook / métricas", "eda/regression_tp3.ipynb; reports/tp3/"],
    ["Testes / Actions", "tests/; .github/workflows/security-tests.yml; ci_evidence.json"],
    ["Auditoria final", "docs/audit_final_tp3.md; reports/zap_tp3/"],
    ["Pergunta de classificação", "docs/classification_question_tp3.md (e páginas 8-9 deste PDF)"],
    ["Plano T2 / pendência", "docs/t2_plan_tp3.md; docs/delivery_tp3.md"]], [170,325], small=True)
p("Referências", "H2TS")
p('Larson et al. (2019), CLINC150: <link href="https://aclanthology.org/D19-1131/">aclanthology.org/D19-1131</link>, CC BY 3.0.<br/>Scikit-learn: <link href="https://scikit-learn.org/stable/modules/linear_model.html">modelos lineares</link>.<br/>FastAPI: <link href="https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/">documentação com assets locais</link>.<br/>ZAP: <link href="https://www.zaproxy.org/docs/api/">API oficial</link>.<br/>GitHub: <link href="https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches">branches protegidas e status checks</link>.', "SmallTS")
p('Repositório: <link href="https://github.com/lenagomesz/tourshield-api-pb-tp1">github.com/lenagomesz/tourshield-api-pb-tp1</link>. Enviar o link, PDF e documentos conforme a plataforma da disciplina. A confirmação do adversário permanece pendente e deve ser completada antes do pentest.', "SmallTS")


def footer(canvas, doc):
    w, h = A4
    canvas.setStrokeColor(TEAL)
    canvas.line(50, h-35, w-50, h-35)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(50, h-28, "TOURSHIELD API | PB TP3")
    canvas.drawString(50, 27, "Helena Gomes | 25/10/2026")
    canvas.drawRightString(w-50, 27, str(doc.page))


path = OUT / "Helena_Gomes_PB_TP3.PDF"
SimpleDocTemplate(str(path), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=55, bottomMargin=48,
    title="TourShield API - PB TP3", author="Helena Gomes").build(story, onFirstPage=footer, onLaterPages=footer)
print(path)
