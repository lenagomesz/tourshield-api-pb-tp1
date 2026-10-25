"""Generate the academic report from the executed EDA and test evidence."""
import json
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)
summary = json.loads((ROOT / "reports" / "summary.json").read_text(encoding="utf-8"))
provenance = json.loads((ROOT / "data" / "provenance.json").read_text(encoding="utf-8"))
smoke = json.loads((ROOT / "reports" / "smoke.json").read_text(encoding="utf-8"))
suite = ElementTree.parse(ROOT / "reports" / "tests.xml").getroot().find("testsuite")
assert suite is not None and suite.attrib["failures"] == "0" and suite.attrib["errors"] == "0"
tests = int(suite.attrib["tests"])
NAVY = colors.HexColor("#12334A")
TEAL = colors.HexColor("#16898C")
LIGHT = colors.HexColor("#EAF3F5")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleTS", fontName="Helvetica-Bold", fontSize=30, leading=34, textColor=NAVY, spaceAfter=16))
styles.add(ParagraphStyle(name="SubTS", fontName="Helvetica", fontSize=15, leading=21, textColor=TEAL, spaceAfter=14))
styles.add(ParagraphStyle(name="BodyTS", fontName="Helvetica", fontSize=10, leading=15, spaceAfter=9, textColor=NAVY))
styles.add(ParagraphStyle(name="SmallTS", fontName="Helvetica", fontSize=8, leading=11, spaceAfter=6, textColor=NAVY))
styles.add(ParagraphStyle(name="H1TS", fontName="Helvetica-Bold", fontSize=20, leading=25, spaceAfter=15, textColor=NAVY))
styles.add(ParagraphStyle(name="H2TS", fontName="Helvetica-Bold", fontSize=12, leading=17, spaceBefore=9, spaceAfter=7, textColor=TEAL))
styles.add(ParagraphStyle(name="CodeTS", fontName="Courier", fontSize=8, leading=12, spaceAfter=8, textColor=NAVY, backColor=LIGHT, borderPadding=7))
story = []


def p(text, style="BodyTS"):
    story.append(Paragraph(text, styles[style]))


def title(number, text):
    p(f"{number:02d} / {text}", "H1TS")


def table(rows, widths, header=True, small=False):
    data = [[Paragraph(escape(str(x)).replace("\n", "<br/>"), styles["SmallTS" if small else "BodyTS"]) for x in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    instructions = [("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 8),
                    ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 4), ("LINEBELOW", (0,0), (-1,0), 1, TEAL)]
    if header:
        instructions += [("BACKGROUND", (0,0), (-1,0), LIGHT)]
    t.setStyle(TableStyle(instructions))
    story.append(t)
    story.append(Spacer(1, 10))


def image(name, width=495):
    img = Image(str(ROOT / "reports" / "figures" / name))
    img.drawHeight = img.imageHeight / img.imageWidth * width
    img.drawWidth = width
    story.append(img)


def page():
    story.append(PageBreak())


def code(lines):
    p("<br/>".join(escape(line).replace(" ", "&nbsp;") for line in lines), "CodeTS")


def dfd():
    d = Drawing(495, 365)
    def boundary(x,y,w,h,label):
        d.add(Rect(x,y,w,h,fillColor=colors.HexColor("#F7FAFC"),strokeColor=TEAL,strokeDashArray=[4,3]))
        d.add(String(x+8,y+h-16,label,fontName="Helvetica-Bold",fontSize=9,fillColor=NAVY))
    def box(x,y,w,h,label):
        d.add(Rect(x,y,w,h,rx=5,fillColor=LIGHT,strokeColor=NAVY))
        lines=label.split("\n")
        for i,line in enumerate(lines):
            d.add(String(x+w/2,y+h/2+(len(lines)-1)*5-i*10,line,textAnchor="middle",fontSize=8,fillColor=NAVY))
    def arrow(x1,y1,x2,y2,label=None,lx=None,ly=None):
        import math
        d.add(Line(x1,y1,x2,y2,strokeColor=NAVY,strokeWidth=1))
        angle=math.atan2(y2-y1,x2-x1)
        points=[x2,y2,x2-6*math.cos(angle-.45),y2-6*math.sin(angle-.45),x2-6*math.cos(angle+.45),y2-6*math.sin(angle+.45)]
        d.add(Polygon(points,fillColor=NAVY,strokeColor=NAVY))
        if label: d.add(String(lx if lx is not None else (x1+x2)/2,ly if ly is not None else (y1+y2)/2,label,fontSize=7,fillColor=NAVY,textAnchor="middle"))
    boundary(5,285,485,75,"TB0 - Cliente não confiável")
    box(190,298,110,32,"Cliente / Swagger")
    boundary(5,115,485,145,"")
    d.add(String(350,132,"TB1 - Processo FastAPI",fontName="Helvetica-Bold",fontSize=9,fillColor=NAVY))
    box(20,186,105,38,"/auth/token\nvalidar senha")
    box(160,186,96,38,"Validar JWT\ne conta ativa")
    box(293,186,105,38,"/predict\nplaceholder")
    box(410,186,65,38,"/health\npúblico")
    box(20,130,105,30,"CLI create_user")
    arrow(190,299,72,225,"credenciais",105,268)
    arrow(243,299,208,225,"Bearer JWT",225,268)
    arrow(285,299,345,225,"JSON",325,268)
    arrow(300,311,443,225,"GET",406,280)
    arrow(256,205,293,205,"identidade",275,235)
    boundary(5,5,485,85,"")
    d.add(String(13,15,"TB2 - Arquivos locais; permissões do sistema operacional",fontName="Helvetica-Bold",fontSize=9,fillColor=NAVY))
    box(75,33,170,36,"SQLite\nusuário / hash / ativo")
    box(315,33,140,36,".env\nsegredo JWT")
    arrow(125,186,145,70,"consulta",160,104)
    arrow(208,186,208,70,"conta",225,104)
    arrow(72,130,105,70,"INSERT hash",63,95)
    arrow(340,70,252,186,"chave",296,102)
    d.add(String(248,351,"",fontSize=1))
    return d


# 1
story.append(Spacer(1, 55))
p("TOURSHIELD", "TitleTS")
p("API de Turismo e Reservas", "SubTS")
p("Fraude de benefícios e geolocalização", "SubTS")
story.append(Spacer(1, 24))
p("Projeto de Bloco | Trabalho Prático 1", "H2TS")
p("<b>Helena Gomes</b><br/>25 de outubro de 2026")
p("Competência integradora: definir o domínio do sistema com EDA exploratória e API FastAPI autenticada como base.")
story.append(Spacer(1, 20))
table([["Dados analisados", "API verificada", "Evidências"],
       ["3.000 mensagens\n20 intenções", f"JWT funcional\n{tests} testes aprovados", "Notebook executado\nDFD e análise CIA"]], [165,165,165])
p("O projeto organiza a base de atendimento e estabelece autenticação desde o início. Predição, agente, identificação de fraude e autorização de benefícios ficam para etapas posteriores.")
p('Repositório público:<br/><link href="https://github.com/lenagomesz/tourshield-api-pb-tp1" color="#16898C">github.com/lenagomesz/tourshield-api-pb-tp1</link>')
p("Este relatório acompanha o código, os dados e o notebook versionados. O dataset não contém fraude confirmada ou coordenadas GPS.", "SmallTS")
page()
# 2
title(1, "Domínio e escolha do dataset")
p("O TourShield atende solicitações de reservas, viagens, localização e recompensas. A intenção será futuramente usada para encaminhar o atendimento; autenticação não equivale a autorização de resgate ou comprovação de localização.")
table([["Item", "Escolha documentada"],
    ["Nome e autoria", "CLINC150 - recorte curado TourShield. Stefan Larson et al., Clinc, 2019."],
    ["Fonte", "github.com/clinc/oos-eval; arquivo data/data_full.json"],
    ["Licença", "CC BY 3.0 Unported. Cópia em data/LICENSE-CLINC150.txt. Código do projeto sob MIT."],
    ["Origem e idioma", "Enunciados de crowdsourcing em inglês, com intenção única; não são tickets reais de uma agência."],
    ["Recorte", "20 rótulos selecionados explicitamente; 150 mensagens por rótulo. IDs e split adicionados; sem tradução."],
    ["Justificativa", "Texto e intenção disponíveis, mais de 500 exemplos e categorias úteis de turismo, reservas, localização e recompensas."]], [105,390])
p("Intenções selecionadas", "H2TS")
p(", ".join(provenance["selected_intents"]), "SmallTS")
p("Rastreabilidade", "H2TS")
p("Revisão fixada: " + provenance["revision"], "SmallTS")
p("SHA-256 do arquivo bruto:<br/>" + provenance["raw_sha256"], "SmallTS")
p("O manifesto data/provenance.json guarda URL exata, hash do CSV e transformações. O script prepare_data.py reutiliza a revisão fixada. Os CSVs presentes permitem executar a EDA sem rede.")
p("Limitação temática: recompensas são genéricas. Não há evidência de que pertençam a programa turístico. Elas apoiam o desenho do atendimento, sem permitir avaliar abuso de benefícios.", "SmallTS")
page()
# 3
title(2, "Qualidade e preparação dos dados")
table([["Verificação com Pandas", "Resultado"],
    ["Shape original", "(3.000, 4)"], ["Dtypes", "sample_id, message, intent, split: string"],
    ["describe(include='all')", "3.000 IDs distintos; 3.000 textos distintos; 20 intenções; 3 splits"],
    ["Ausentes por coluna", "sample_id=0; message=0; intent=0; split=0"],
    ["Duplicatas", "0 integrais; 0 mensagem/intenção; 0 normalizadas"],
    ["Conflitos e perdas", "0 conflitos de rótulo; 0 linhas removidas ou imputadas"],
    ["Exportação limpa", "(3.000, 6), incluindo n_chars e n_words"],
    ["Splits preservados", "Treino 2.000; validação 400; teste 600. Sobreposição textual normalizada entre splits: 0."]], [215,280])
p("Decisões de limpeza", "H2TS")
p("A rotina remove texto/intenção ausentes ou vazios, caso existam. Aplica strip ao texto e cria chave auxiliar casefold com espaços uniformizados para auditar duplicatas; não remove pontuação, entidades ou palavras.")
p("Se ocorrer repetição da mesma chave e intenção, preserva primeiro teste, depois validação, depois treino, sem mover amostras. Conflitos de rótulo são exportados e excluídos para revisão. Nesta execução nenhuma dessas regras removeu linhas.")
p("Mensagens longas são mantidas: 98 registros (3,27%) ultrapassam 18 palavras, limite Q3 + 1,5 IQR. O tamanho, sozinho, não justifica excluir um chamado.")
p("Toda seleção, limpeza e estatística usa Pandas. Auditorias completas em reports/; códigos equivalentes em eda/eda.py e eda/eda.ipynb.", "SmallTS")
page()
# 4
title(3, "Distribuições e estatísticas")
table([["Medida", "Caracteres", "Palavras"], ["n", "3.000", "3.000"],
    ["Média / desvio padrão", "50,09 / 17,37", "10,26 / 3,65"],
    ["Mínimo / máximo", "8 / 136", "2 / 28"],
    ["Q1 / mediana / Q3", "38 / 48 / 60", "8 / 10 / 12"]], [215,140,140])
image("01_histogram.png", 490)
p("Figura 1. Comprimento em palavras; tokens definidos por espaços. Fonte: CLINC150, recorte e elaboração própria.", "SmallTS")
p("O centro está próximo de 10 palavras, com cauda à direita até 28. Os percentis e o desvio padrão descrevem dispersão; não foi assumida distribuição normal nem executado teste inferencial.")
p("Os comprimentos são derivados dos textos. Não existem variáveis numéricas de GPS ou transações que possam sustentar análise de fraude ou deslocamento.")
page()
# 5
title(4, "Distribuição das intenções")
image("02_categories.png", 490)
p("Figura 2. Contagens após a limpeza. Fonte: CLINC150, recorte e elaboração própria.", "SmallTS")
p("Todas as 20 classes possuem 150 mensagens, correspondentes a 5% do total. Por classe, foram preservados 100 exemplos de treino, 20 de validação e 30 de teste.")
p("<b>Hipótese 1:</b> a demanda real por atendimento terá distribuição diferente da uniforme. O gráfico reflete a amostragem balanceada do benchmark, e não a popularidade de cada intenção entre turistas.")
p("<b>Como validar:</b> coletar chamados reais autorizados, contar intenções por período e região e comparar as proporções, documentando o método de amostragem. Nesta base não se pode estimar prevalência operacional.")
page()
# 6
title(5, "Comprimento e hipóteses")
image("03_boxplot.png", 490)
p("Figura 3. Medianas, intervalos interquartis e valores extremos por intenção. Fonte: elaboração própria sobre CLINC150.", "SmallTS")
p("<b>Hipótese 2:</b> pedidos de reserva exigem mais contexto textual que consultas de localização. Reservas: n=750, mediana 12 palavras; localização: n=600, mediana 8. book_flight tem mediana 15; book_hotel, 14; current_location e share_location, 7.")
p("<b>Hipótese 3:</b> comprimento isolado pode não distinguir saldo e resgate de recompensas. rewards_balance e redeem_rewards têm mediana 10; médias 10,03 e 10,32, com sobreposição no boxplot.")
p("H2: validar a diferença em amostra externa com bootstrap e teste não paramétrico predefinido. H3: comparar futuramente um baseline de comprimento com representação textual, usando macro-F1 e matriz de confusão. Não há modelo ou conclusão causal neste TP.")
page()
# 7
title(6, "API modular e autenticação")
table([["Rota", "Entrada / acesso", "Saída"],
    ["GET /health", "Pública", '200: status="ok"'],
    ["POST /auth/token", "Form username/password", "200: JWT bearer; falha 401"],
    ["POST /predict", "Bearer JWT e JSON message; GPS opcional em par", "200: placeholder; sem token 401; entrada inválida 422"]], [110,225,160])
p("Arquitetura", "H2TS")
p("main.py monta a aplicação; app/routes organiza endpoints; models.py define schemas Pydantic; database.py encapsula SQLite; security.py cuida de hashing e JWT; config.py carrega configuração. Cadastro de usuário ocorre por CLI local.")
p("Fluxo autenticado", "H2TS")
p("OAuth2PasswordBearer obtém o Bearer token. O login verifica hash Argon2 e emite JWT HS256 de 15 minutos. A validação exige sub, iat, exp, iss e aud, aceita apenas HS256 e consulta se a conta permanece ativa. Sem segredo externo de pelo menos 32 bytes, o startup falha.")
p("O JWT é assinado, não cifrado; não inclui senha, texto ou GPS. A resposta de token usa no-store. O banco armazena apenas usuário, hash e estado ativo, com SQL parametrizado e fechamento explícito das conexões.")
p("Contrato do placeholder", "H2TS")
code(['{"intent": null, "status": "placeholder",', ' "detail": "Modelo não implementado; nenhum benefício', '            ou reserva foi autorizado."}'])
p("Texto em branco é rejeitado; limite de 4.000 caracteres. Latitude [-90,90] e longitude [-180,180] devem ser informadas juntas. Campos extras e valores não finitos são rejeitados. Texto e localização não são persistidos nem retornados.")
page()
# 8
title(7, "DFD e fronteiras de confiança")
story.append(dfd())
p("Figura 4. DFD básico da API. As áreas tracejadas marcam trust boundaries. A versão Mermaid completa está em docs/security.md.", "SmallTS")
p("<b>TB0/TB1:</b> senha, token, mensagem e coordenadas atravessam a fronteira entre cliente e servidor. Saídas: status público, JWT ou 401, e placeholder ou erro. No desenvolvimento o transporte usa HTTP em loopback; HTTPS é requisito antes de exposição externa.")
p("<b>TB1/TB2:</b> SQLite fornece usuário, hash e flag ativo; .env fornece a chave para emissão e validação JWT. É fronteira lógica de permissões sobre arquivos na mesma máquina, sem isolamento físico. A CLI administrativa grava usuário e hash.")
p("As saídas voltam ao cliente pelo mesmo canal HTTP. Não há acesso a motor de reservas, serviço de GPS, provedor de benefícios ou modelo. Dataset e notebook pertencem ao fluxo offline de análise.")
p("Localização declarada pelo cliente é não confiável. Um token válido demonstra sessão, mas não comprova local físico, titularidade de uma reserva ou elegibilidade para benefício.")
page()
# 9
title(8, "CIA e riscos do domínio")
table([["Componente", "Confidencialidade", "Integridade", "Disponibilidade"],
 ["Cliente / canal", "Senha, JWT, texto e GPS; HTTPS externo pendente", "Validar tudo recebido; GPS pode ser falso", "Timeouts e limites no proxy pendentes"],
 ["/health", "Somente serviço e status", "Sem entrada variável", "Sonda pública de vida; não verifica banco"],
 ["Login / JWT", "Argon2; token sem PII adicional; no-store", "Assinatura, algoritmo fixo, claims e conta ativa", "Expiração 15 min; rate limiting pendente"],
 ["/predict", "Não armazena ou reflete texto/GPS", "Schemas, faixas, campos extras rejeitados", "Placeholder leve; limite pré-parsing pendente"],
 ["SQLite / CLI", "Hash, não senha; ACL do SO necessária", "Parâmetros SQL, PK e transações", "Timeout 5 s; backup a configurar"],
 [".env / chave", "Fora do Git; proteger permissões", "Segredo sem valor padrão", "Rotação invalida todos os tokens"],
 ["Dataset / EDA", "Benchmark público; sem novos dados pessoais", "Commit fixo, SHA-256 e bruto preservado", "Dados presentes; execução offline"]], [75,140,140,140], small=True)
p("Fraude de benefícios", "H2TS")
p("Nos próximos TPs, saldo e elegibilidade devem ficar no servidor. Vincular reserva ao usuário autenticado, autorizar por recurso, usar transações e idempotência e auditar resgates. JWT sozinho não impede acesso indevido por ID ou resgate duplicado.")
p("Geolocalização e limites atuais", "H2TS")
p("Geofence isolada não comprova presença: GPS declarado pode ser falsificado. Dados independentes e consentidos serão necessários. Esta versão não tem TLS/proxy, MFA, rate limiting, revogação individual de JWT, backup automatizado ou monitoramento. Não está pronta para produção.")
page()
# 10
title(9, "Execução, evidências e referências")
p("Instalação e execução", "H2TS")
code(["python -m venv .venv", r".\.venv\Scripts\Activate.ps1", "python -m pip install -r requirements.txt", "# Configure .env com JWT_SECRET aleatório (ver README).", "python -m scripts.create_user helena", "uvicorn main:app --reload", "# Em outro terminal:", "python eda/eda.py", "python -m pytest -q"])
p("O README inclui geração segura do segredo, exemplos PowerShell para obter token e chamar a API, estrutura de pastas e alternativas à ativação do ambiente. O notebook também executa a partir da pasta eda/ com o dataset presente.")
table([["Verificação executada", "Evidência / resultado"],
 ["Notebook", "9 células executadas, com tabelas e três imagens; sem erro"],
 ["Testes automatizados", f"{tests} aprovados; reports/tests.xml"],
 ["HTTP real com Uvicorn", f"/health {smoke['health']}; /predict sem token {smoke['predict_without_token']}; login {smoke['auth_token']}; /predict autenticado {smoke['predict_with_token']}"],
 ["Segurança testada", "Credencial incorreta, JWT expirado/assinatura/claims/algoritmo inválidos, conta inativa e validação de entrada"]], [180,315], small=True)
p("Um aviso de depreciação do TestClient/httpx permanece no ambiente verificado; não houve falha de teste. Relatórios estão em reports/ e o DFD em docs/security.md.", "SmallTS")
p("Referências e entrega", "H2TS")
p('Larson et al. (2019). <i>An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction</i>. EMNLP-IJCNLP. <link href="https://aclanthology.org/D19-1131/">aclanthology.org/D19-1131</link>.<br/>Dataset e licença: <link href="https://github.com/clinc/oos-eval">github.com/clinc/oos-eval</link>; CC BY 3.0.<br/>FastAPI: <link href="https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/">documentação oficial de OAuth2 e JWT</link>.', "SmallTS")
p('Entrega: <link href="https://github.com/lenagomesz/tourshield-api-pb-tp1">github.com/lenagomesz/tourshield-api-pb-tp1</link>. Enviar o link e este PDF no campo da disciplina. O repositório contém os artefatos executáveis; o relatório não os substitui.', "SmallTS")


def footer(canvas, doc):
    width, height = A4
    canvas.setStrokeColor(TEAL)
    canvas.line(50, height-35, width-50, height-35)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(NAVY)
    canvas.drawString(50, height-28, "TOURSHIELD API | PB TP1")
    canvas.drawString(50, 27, "Helena Gomes | 25/10/2026")
    canvas.drawRightString(width-50, 27, str(doc.page))


path = OUT / "Helena_Gomes_PB_TP1.PDF"
document = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=50, rightMargin=50,
    topMargin=55, bottomMargin=48, title="TourShield API - PB TP1", author="Helena Gomes")
document.build(story, onFirstPage=footer, onLaterPages=footer)
print(path)
