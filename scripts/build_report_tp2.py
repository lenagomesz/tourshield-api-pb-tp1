"""Rebuild TP2 PDF from executed statistical, pytest and ZAP evidence."""
import json
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)
stat = json.loads((ROOT / "reports/tp2/statistics.json").read_text(encoding="utf-8"))
zap = json.loads((ROOT / "reports/zap/scan-metadata.json").read_text(encoding="utf-8"))
audit = json.loads((ROOT / "reports/dependency-audit.json").read_text(encoding="utf-8"))
suite = ElementTree.parse(ROOT / "reports/tests_tp2.xml").getroot().find("testsuite")
assert suite is not None and suite.attrib["failures"] == "0" and suite.attrib["errors"] == "0"
test_count = int(suite.attrib["tests"])
vulns = sum(len(p["vulns"]) for p in audit["dependencies"])
assert zap["passive_queue_remaining"] == 0 and not zap["active_scan_executed"]
NAVY, TEAL, LIGHT = [colors.HexColor(c) for c in ["#12334A", "#16898C", "#EAF3F5"]]
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
        ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
    story.append(t)
    story.append(Spacer(1, 12))


def image(name, width=495):
    img = Image(str(ROOT / "reports/tp2/figures" / name))
    img.drawHeight = img.imageHeight / img.imageWidth * width
    img.drawWidth = width
    story.append(img)


def code(lines):
    p("<br/>".join(escape(s).replace(" ", "&nbsp;") for s in lines), "CodeTS")


# Cover
story.append(Spacer(1, 50))
p("TOURSHIELD", "TitleTS")
p("API de Turismo e Reservas", "SubTS")
p("Estatística e segurança OWASP", "SubTS")
story.append(Spacer(1, 20))
p("Projeto de Bloco | Trabalho Prático 2", "H2TS")
p("<b>Helena Gomes</b><br/>25 de outubro de 2026")
p("Competência integradora: implementar análise estatística completa e controles OWASP Top 10 na API FastAPI auditada por ZAP.")
story.append(Spacer(1, 18))
table([["Análise", "API", "Auditoria passiva"],
       ["3.000 mensagens\nMann-Whitney + efeito + IC", f"SQLModel + ownership\n{test_count} testes aprovados",
        "ZAP 2.17.0\n0 High / Medium / Low"]], [165,165,165])
p("Foco do domínio: fraude de benefícios e geolocalização. O TP2 protege o atendimento e a posse de recursos; não implementa modelo de fraude, classificação ou agente.")
p('<link href="https://github.com/lenagomesz/tourshield-api-pb-tp1" color="#16898C">github.com/lenagomesz/tourshield-api-pb-tp1</link>')
p("O mesmo repositório do TP1 foi atualizado. Este PDF acompanha o notebook, o código, os dados, os testes e o relatório exportado pelo ZAP.", "SmallTS")
page()
# 1
title(1, "Problema e dados")
p("O objetivo analítico é caracterizar mensagens de turismo e reservas para preparar a classificação de intenções. A hipótese H2 do TP1 propôs que mensagens de reservas exigem mais contexto que consultas de localização. O objetivo de segurança é impedir que uma sessão acesse reservas de outro usuário ou atribua a si benefícios.")
table([["Propriedade", "Descrição"],
    ["Dataset", "CLINC150, recorte curado de 20 intenções; Larson et al. (2019), Clinc."],
    ["Fonte / licença", "github.com/clinc/oos-eval; CC BY 3.0 Unported. Cópia integral e atribuição em data/."],
    ["Shape e tipos", "Original (3.000, 4): sample_id, message, intent, split, como strings. Limpo (3.000, 6), com n_chars e n_words."],
    ["Qualidade", "Zero ausentes, duplicatas normalizadas e conflitos de rótulo. Nenhuma linha removida, imputada ou traduzida."],
    ["Distribuição / splits", "150 mensagens por classe (5%). Treino 2.000, validação 400, teste 600; sem sobreposição de chave textual normalizada."],
    ["Rastreabilidade", "Commit e SHA-256 em data/provenance.json. Bruto e CSVs presentes para execução offline."]], [120,375])
p("As regras do TP1 são mantidas: strip de bordas, chave auxiliar para auditar duplicatas, preservação de texto e splits; nenhum corte automático por outlier de comprimento. Há 98 mensagens acima do limite IQR de 18 palavras, mantidas como potencialmente legítimas.")
p("Os enunciados são de crowdsourcing em inglês e intenção única, não chamados reais de uma agência. Categorias de recompensas são genéricas; a base não tem coordenadas GPS, transações ou fraude confirmada. O recorte é escolha do projeto, não domínio oficial único do CLINC150.")
page()
# 2
title(2, "Análise de correlação")
image("04_heatmap.png")
p("Figura 1. Heatmaps seaborn: correlação de Pearson e Spearman de atributos textuais. Fonte: CLINC150, recorte e elaboração própria.", "SmallTS")
table([["Variável", "Definição"], ["n_chars", "Caracteres da mensagem"],
    ["n_words", "Tokens delimitados por espaços"],
    ["mean_word_length", "Média de caracteres das palavras"],
    ["unique_ratio", "Palavras distintas / total de palavras, em casefold"]], [150,345])
p(f"Caracteres e palavras apresentam Pearson <b>r={stat['pearson_chars_words']:.4f}</b> e Spearman <b>rho={stat['spearman_chars_words']:.4f}</b>. A associação forte é esperada porque ambas medem o mesmo texto. Sugere redundância entre atributos, sem provar causalidade nem utilidade preditiva.")
p("Não foi atribuído código numérico arbitrário às intenções para correlacioná-las. As demais variáveis também são derivadas do comprimento e vocabulário do texto; relações matemáticas entre elas exigem cautela na interpretação.")
p("No futuro modelo, o valor incremental desses atributos deve ser avaliado em treino/validação. A correlação global exploratória não autoriza usar o teste para selecionar hiperparâmetros.")
page()
# 3
title(3, "Scatter plots e padrões")
image("05_scatter.png")
p("Figura 2. Dispersão de caracteres/palavras e de comprimento médio das palavras. Os quatro grupos são curados para a análise; pontos translúcidos reduzem o efeito da sobreposição.", "SmallTS")
p("O primeiro scatter confirma o crescimento conjunto de palavras e caracteres. Mensagens de reservas aparecem com frequência nos comprimentos maiores, mas os grupos se sobrepõem. No segundo, número de palavras e tamanho médio da palavra não formam fronteiras claras de intenção.")
table([["Estatística", "Caracteres", "Palavras"], ["Média / DP amostral", "50,09 / 17,37", "10,26 / 3,65"],
       ["Mediana", "48", "10"], ["Q1 / Q3", "38 / 60", "8 / 12"], ["Mínimo / máximo", "8 / 136", "2 / 28"]], [215,140,140])
p("Insight: não definir um limiar de comprimento como se ele identificasse intenção. Reservas e localização incluem mensagens curtas e longas; vocabulário e semântica precisam ser considerados no futuro classificador.")
p("O balanceamento de 150 exemplos por intenção vem da construção do benchmark. Não traduz a prevalência de dúvidas reais e não permite estimar demanda ou fraude operacional.")
page()
# 4
title(4, "Teste formal da H2 do TP1")
image("06_hypothesis_violin.png", 470)
p("Figura 3. Comparação de comprimento. Reservas: 750 mensagens; localização: 600. Fonte: elaboração própria.", "SmallTS")
p("<b>H0:</b> distribuições iguais de n_words nos grupos. <b>H1:</b> distribuições diferentes. Teste bilateral Mann-Whitney U (SciPy), alfa=0,05, método assintótico com correção de empates e continuidade; um contraste principal.")
table([["Medida", "Resultado"], ["Medianas", "Reservas: 12; localização: 8 palavras"],
       ["U / p-valor", f"{stat['u']:.0f} / {stat['p_value']:.4e}"],
       ["Cliff's delta", f"{stat['cliffs_delta']:.4f} (positivo: reservas maiores)"],
       ["Diferença de medianas / IC95%", "4 palavras / [3; 5], bootstrap percentil, 5.000 reamostragens, semente 42"]], [215,280])
p("<b>Interpretação:</b> rejeita-se H0 neste benchmark. A direção observada favorece reservas mais longas; a probabilidade empírica de superioridade, contando empates pela metade, é 76,98%. O p-valor não é a chance de H0 ser verdadeira e não mede relevância prática.")
p("O teste compara distribuições; não é automaticamente teste de medianas com formatos distintos. O IC estima a diferença de medianas separadamente. A hipótese veio desta mesma base no TP1: resultado exploratório, sem confirmação externa.", "SmallTS")
page()
# 5
title(5, "Insights, limites e próximos passos")
p("Insights principais", "H2TS")
p("1. Caracteres e palavras têm informação redundante; testar ganho incremental desses atributos no futuro modelo.<br/>2. Reservas tendem a ser mais longas nesta comparação, mas com sobreposição; não transformar a diferença em regra rígida de intenção.<br/>3. Intenções balanceadas exigem cautela ao generalizar para atendimento real.<br/>4. Saldo e resgate de recompensas continuam decisões semânticas diferentes, separadas da autorização de benefício.")
p("Limitações estatísticas", "H2TS")
p("Os grupos misturam várias intenções; essa composição pode explicar parte do efeito. O teste pressupõe observações independentes, mas não há IDs de participantes para verificar enunciados do mesmo autor. A reamostragem individual não corrige dependência, viés de coleta ou validade externa.")
p("A hipótese foi sugerida pelos mesmos dados no TP1. O valor muito pequeno de p não corrige esse reuso exploratório. O idioma inglês, intenção única, crowdsourcing e exclusão de out-of-scope limitam a aplicação a clientes reais em português.")
p("Limitações do domínio", "H2TS")
p("Não existem fraude confirmada, GPS, transações ou saldo associado a usuário. A EDA não identifica fraude de benefícios ou spoofing de localização. JWT comprova sessão, sem provar local físico ou elegibilidade para desconto.")
p("Próximos passos para classificação", "H2TS")
p("Comparar TF-IDF com classificador linear a baselines majoritário e de comprimento. Ajustar apenas em treino/validação; usar teste uma vez no resultado final. Reportar macro-F1, recall por intenção e matriz de confusão. Obter base externa autorizada em português, com multi-intenção e out-of-scope.")
p("Nenhuma saída futura de classificação deverá aprovar resgate ou substituir ownership, saldo e regras de elegibilidade no servidor. Dados próprios e rótulos específicos serão necessários para estudar fraude.")
page()
# 6
title(6, "API, SQLModel e ownership")
table([["Rota", "Contrato e proteção"], ["GET /health", "Público; 200, sonda de vida"],
       ["POST /auth/token", "Form AuthInput extra=forbid; Argon2; JWT ou 401; limite 429"],
       ["POST /predict", "PredictRequest extra=forbid; Bearer; placeholder, sem modelo"],
       ["POST /reservations", "ReservationInput extra=forbid; destino; owner obtido do sub; 201"],
       ["GET /reservations/{id}", "JWT obrigatório; consulta ID + owner; 404 para outro usuário ou inexistente"]], [155,340])
p("SQLModel substitui o SQLite raw do TP1. Usuários e reservas são tabelas SQLModel; consultas usam select, where, Session.get/add/commit. Não existe SQL textual no código da API, CLI ou testes. O mecanismo gera parâmetros vinculados e oculta valores de parâmetros em erros.")
p("A reserva é um recurso local de demonstração, sem compra externa. Seu status inicial é requested. O cliente só informa destination: owner e status extras são rejeitados. O UUID dificulta enumeração, mas a proteção real é a condição owner == usuário autenticado na consulta.")
code(["select(Reservation).where(", "    Reservation.id == str(reservation_id),", "    Reservation.owner == username", ")"])
p("Dois usuários foram exercitados no pytest e no tráfego do ZAP: proprietário recebe 200; outro usuário recebe 404, sem revelar destino ou confirmar existência. Sem token recebe 401.")
p("JWT HS256 de 15 minutos mantém validação de exp, iat, sub, iss e aud e consulta de conta ativa. Mensagem/GPS não são persistidos; destino da reserva é persistido e protegido. Não há aprovação de benefício por coordenada declarada.")
page()
# 7
title(7, "Headers, CORS e rate limiting")
table([["Controle", "Configuração"],
       ["HSTS", "max-age=31536000; includeSubDomains"],
       ["X-Frame-Options / X-Content-Type-Options", "DENY / nosniff"],
       ["CSP", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"],
       ["Cache / privacidade", "no-store; Pragma no-cache; Referrer-Policy no-referrer; Permissions-Policy restritiva"],
       ["CORS", "Allowlist http://localhost:3000; GET/POST; Authorization/Content-Type; sem credenciais por cookie"],
       ["Superfície", "Debug falso; docs/redoc desativados; host allowlist; limite de body 16 KiB e leitura 10 s"]], [160,335])
p("O middleware aplica headers em sucessos e erros, inclusive 401/404/422/429. CORS não é autorização e não protege contra clientes fora do navegador. HSTS só atua em HTTPS; o scan usou TLS local. A CSP fechada dispensa scripts de Swagger, que permanece desativado; o contrato JSON segue disponível.")
p("Rate limiting de autenticação", "H2TS")
p("Janela deslizante: <b>5 requisições por IP em 60 segundos</b>, contabilizando sucessos e falhas antes de parsing e Argon2. A sexta recebe 429 e Retry-After. O limite permite erros de digitação e reduz brute force e custo de hashing na demonstração.")
p("Lock e relógio monotônico evitam corrida/variação do relógio; estado tem teto de 10.000 IPs e falha fechada quando cheio. X-Forwarded-For não é adotado na execução orientada com --no-proxy-headers. Teste confirma bloqueio e recuperação da janela.")
p("Limite: um processo/worker, memória limpa no reinício. NAT pode agrupar usuários e ataques distribuídos podem contornar limite por IP. Produção exige armazenamento compartilhado e política de proxy/conta adequada.", "SmallTS")
page()
# 8
title(8, "Cobertura OWASP Top 10")
p("IDs 2021 usados na disciplina; matriz completa e correspondência para a edição 2025 em docs/owasp_tp2.md. Controles não equivalem a certificação.")
table([["Risco 2021", "Controle / evidência"],
       ["A01 - Acesso", "JWT, ownership por ID+owner, 404 uniforme, teste BOLA"],
       ["A02 - Criptografia", "Argon2id, segredo externo, JWT validado, TLS no scan, HSTS"],
       ["A03 - Injeção", "SQLModel sem SQL raw; inputs com extra=forbid; dados nunca executados"],
       ["A04 - Design", "Owner/status no servidor; nenhum resgate autorizado; limites explícitos"],
       ["A05 - Configuração", "CSP/headers, CORS, hosts, debug falso, erros genéricos, docs desligados"],
       ["A06 - Dependências", f"{len(audit['dependencies'])} pacotes no snapshot pip-audit; {vulns} vulnerabilidades conhecidas; lock transitivo"],
       ["A07 - Autenticação", "JWT 15 min, conta ativa, erros genéricos e 5 logins/IP/minuto"],
       ["A08 - Integridade", "Dados por hash/commit, dependências fixadas e ferramentas com SHA-256"],
       ["A09 - Logs", "JSON com request_id, método, rota e status; sem senha/JWT/texto/GPS"],
       ["A10 - SSRF", "Sem HTTP externo na API, callbacks ou dereferência de URLs fornecidas"]], [125,370], small=True)
p("Edição 2025", "H2TS")
p("A matriz atual também trata A10:2025 (condições excepcionais): ausência de segredo impede startup; erro inesperado vira 500 genérico com headers e log; body/timeout geram 413/408. SQLModel oculta parâmetros. Esses comportamentos têm testes específicos.")
p("Pendências de implantação", "H2TS")
p("TLS com certificado válido, limiter distribuído, MFA quando aplicável, revogação individual, backup, coletor/retentor de logs e alertas externos não estão prontos para produção. A API não tem integrações externas de reserva ou benefícios. Para o escopo atual, SSRF não possui fluxo executável.")
page()
# 9
title(9, "Auditoria passiva OWASP ZAP")
p(f"ZAP <b>{zap['zap_version']}</b> e Java Temurin 21 portáteis; downloads oficiais com SHA-256 verificados. Modo <b>{zap['mode']}</b>, sem active scan ou spider. {len(zap['enabled_scanners']['scanners'])} regras passivas habilitadas. Alvo desta execução: {zap['target']}.")
p("A API rodou com TLS e certificado descartável. O cliente confiou no proxy ZAP somente no processo de teste; trust store do sistema não foi alterada. O runner não escaneia serviços externos e usa contas, banco e segredos efêmeros.")
p(f"Foram exercitadas <b>{len(zap['requests'])} requisições</b>, cobrindo login, health, OpenAPI, predição, reserva própria/de outro usuário, erros, CORS e rate limit. A fila recordsToScan foi conferida em <b>0</b> antes da exportação. Ledger e regras em scan-metadata.json.")
table([["Severidade", "Ocorrências"], *[[level, zap["alert_counts"][level]] for level in ["High", "Medium", "Low", "Informational"]]], [250,245])
table([["Finding", "Análise / status"],
    ["10015 - Cache-control\n4 ocorrências informativas", "Aceito: evidência no-store é proteção intencional. Evita cache de respostas potencialmente sensíveis."],
    ["10111 - Auth request\n3 ocorrências informativas", "Aceito: identifica campo password no login esperado; não é prova de exposição. TLS, hash, throttling e no-store aplicados."],
    ["10112 - Session response\n1 ocorrência informativa", "Aceito: identifica access_token, saída contratual. JWT expira em 15 min e não é enviado em URL."]], [190,305], small=True)
p("Nenhum Medium/High foi detectado; não há finding dessas severidades para corrigir ou aceitar nesta execução. O scan foi realizado após aplicar os controles; não foi inventado um relatório anterior para simular correção.")
p("HTML e JSON foram exportados pela própria API do ZAP. Apenas segredos efêmeros eventualmente presentes foram redigidos; os findings e severidades permanecem. Oito ocorrências informativas correspondem a três tipos de alerta.", "SmallTS")
page()
# 10
title(10, "Validação, execução e entrega")
table([["Verificação", "Evidência"],
       ["pytest tests/", f"{test_count} testes aprovados; reports/tests_tp2.xml"],
       ["Casos obrigatórios", "Sem token 401; reserva alheia 404; campo extra 422"],
       ["Cobertura adicional", "JWT, CORS, headers, limiter, expiração de janela, body, log sem segredos e erro genérico"],
       ["Notebook", "10 células executadas; heatmap, dois scatters, teste com p-valor e efeito"],
       ["Dependências", f"pip-audit: {vulns} vulnerabilidades conhecidas no snapshot; não é garantia futura"],
       ["Scan", "ZAP real em TLS, 20 requisições, fila zerada, sem exclusões de findings"]], [170,325], small=True)
code(["python -m venv .venv", r".\.venv\Scripts\Activate.ps1", "python -m pip install -r requirements-lock.txt", "# Configure JWT_SECRET no .env (instrução no README).", "python -m scripts.create_user helena", "uvicorn main:app --reload --no-proxy-headers --no-server-header", "# Outro terminal:", "python eda/eda_tp2.py", "pytest tests/", "python -m scripts.setup_zap", "python -m scripts.run_zap"])
p("Limites da auditoria", "H2TS")
p("ZAP passivo só analisa mensagens exercitadas; não explora SQLi ou prova ausência de BOLA. Os testes complementam o scan sem substituir pentest completo. O certificado autoassinado serve ao laboratório. Um aviso de depreciação TestClient/httpx não causou falhas.")
p("Entrega e referências", "H2TS")
p('Repositório: <link href="https://github.com/lenagomesz/tourshield-api-pb-tp1">github.com/lenagomesz/tourshield-api-pb-tp1</link>.<br/>ZAP: reports/zap/zap-report.html ou zap-report.json; findings.md.<br/>EDA estruturada: reports/tp2/eda_report.md; notebook: eda/eda_tp2.ipynb.', "SmallTS")
p('Larson et al. (2019): <link href="https://aclanthology.org/D19-1131/">aclanthology.org/D19-1131</link> (CC BY 3.0).<br/>ZAP: <link href="https://www.zaproxy.org/docs/api/">zaproxy.org/docs/api</link>.<br/>OWASP: <link href="https://owasp.org/Top10/2021/">Top 10:2021</link> e <link href="https://top10.owasp.org/2025/0x00_2025-Introduction/">Top 10:2025</link>.<br/>SQLModel: <link href="https://sqlmodel.tiangolo.com/tutorial/where/">documentação oficial</link>.', "SmallTS")


def footer(canvas, doc):
    w, h = A4
    canvas.setStrokeColor(TEAL)
    canvas.line(50, h-35, w-50, h-35)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(50, h-28, "TOURSHIELD API | PB TP2")
    canvas.drawString(50, 27, "Helena Gomes | 25/10/2026")
    canvas.drawRightString(w-50, 27, str(doc.page))


path = OUT / "Helena_Gomes_PB_TP2.PDF"
SimpleDocTemplate(str(path), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=55,
    bottomMargin=48, title="TourShield API - PB TP2", author="Helena Gomes").build(story, onFirstPage=footer, onLaterPages=footer)
print(path)
