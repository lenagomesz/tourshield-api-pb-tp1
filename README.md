# TourShield API - Turismo e Reservas | PB TP2

**Helena Gomes | 25/10/2026**

Atendimento turístico com EDA completa e API FastAPI autenticada, agora com SQLModel,
ownership, headers, CORS e rate limiting. Foco: fraude de benefícios e geolocalização.
Não há modelo de ML nem agente; /predict é placeholder e as reservas são recursos locais
de demonstração, sem efetuar compra ou conceder benefícios.

Repositório: https://github.com/lenagomesz/tourshield-api-pb-tp1 (continuação do TP1).

## Evidências TP2

| Artefato | Local |
|---|---|
| Notebook executado / fonte | [eda_tp2.ipynb](eda/eda_tp2.ipynb), [eda_tp2.py](eda/eda_tp2.py) |
| EDA estruturada | [Relatório](reports/tp2/eda_report.md) |
| ZAP exportado | [HTML](reports/zap/zap-report.html), [JSON](reports/zap/zap-report.json) |
| Findings e método | [findings.md](reports/zap/findings.md) |
| OWASP, rate limit, DFD | [owasp_tp2.md](docs/owasp_tp2.md) |
| Testes executados | [tests_tp2.xml](reports/tests_tp2.xml) |
| PDF | [Helena_Gomes_PB_TP2.PDF](output/pdf/Helena_Gomes_PB_TP2.PDF) |

O GitHub pode mostrar o código do HTML: baixe o arquivo e abra no navegador. O JSON
também é evidência válida. O ZAP passivo não substitui pentest nem certifica ausência
de vulnerabilidades. Detalhes de escopo e aceites constam no documento de findings.

## Instalação (Python 3.12)

PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -c "import secrets; from pathlib import Path; Path('.env').write_text('JWT_SECRET=' + secrets.token_urlsafe(48) + '\nDATABASE_PATH=./tourshield.sqlite3\nCORS_ORIGINS=http://localhost:3000\n', encoding='utf-8')"
python -m scripts.create_user helena
uvicorn main:app --reload --no-proxy-headers --no-server-header
```

A geração de `.env` é para primeira instalação: sobrescrevê-lo troca a chave e invalida
tokens. A CLI pede senha de 12-1024 caracteres sem eco. Não há senha padrão nem registro
público. Se a política de execução bloquear a ativação, use os executáveis em
`.\.venv\Scripts\` diretamente. Em Linux/macOS: `source .venv/bin/activate`.
`requirements.txt` lista dependências diretas; `requirements-lock.txt` fixa também
as transitivas. O banco TP1 tem campos de usuários compatíveis; SQLModel cria a tabela
de reservas sem apagar usuários existentes.

Servidor local: http://127.0.0.1:8000. /health é público; contrato em /openapi.json.
Swagger (/docs) e Redoc foram desativados para manter CSP fechada. HSTS não protege
HTTP puro: HTTPS é obrigatório fora do desenvolvimento em loopback. O scan usa HTTPS.
`--reload` é de desenvolvimento; o limiter deste TP suporta apenas um processo/worker.

## Rotas e exemplos

| Rota | Acesso / resultado |
|---|---|
| GET /health | Público; 200 |
| POST /auth/token | Form username/password; JWT ou 401; campos extras 422; excesso 429 |
| POST /predict | Bearer + JSON message/GPS opcional; placeholder; sem token 401 |
| POST /reservations | Bearer + JSON destination; cria recurso local (201) com owner do token |
| GET /reservations/{id} | Somente proprietário; 404 tanto para inexistente quanto de outro usuário |

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$credential = Get-Credential -UserName helena
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/token -Body @{username=$credential.UserName; password=$credential.GetNetworkCredential().Password}
$headers = @{Authorization="Bearer $($login.access_token)"}
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/predict -Headers $headers -ContentType application/json -Body '{"message":"Quero reservar hotel"}'
$reservation = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/reservations -Headers $headers -ContentType application/json -Body '{"destination":"Recife"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/reservations/$($reservation.id)" -Headers $headers
```

JWT HS256 de 15 min, Argon2id, conta ativa checada em cada requisição. Inputs herdam
`extra='forbid'`, inclusive formulário de login. Não enviar owner/status no body: serão
rejeitados. SQLModel usa expressões parametrizadas, sem SQL raw. Texto/GPS não são
persistidos; destino da reserva é armazenado e protegido por ownership.

Login: **5 requisições/IP/60 s**, janela deslizante, sexta retorna 429 + Retry-After.
Conta sucessos/falhas, antes de parsing e Argon2. Não usa X-Forwarded-For; mantenha
`--no-proxy-headers`. Estado em memória, limitado a 10.000 IPs; reinício limpa os buckets.
Produção com vários workers precisa de limiter compartilhado e política para NAT/proxy.

Headers obrigatórios e CSP aplicados também aos erros. CORS padrão só aceita
http://localhost:3000; configure `CORS_ORIGINS` com origens exatas separadas por vírgula,
sem wildcard ou caminho, antes de iniciar. Host allowlist: localhost/127.0.0.1 (e testserver
para pytest). Body limitado a 16 KiB e leitura a 10 s. Logs JSON guardam metadados de
requisição/status, sem senha, Bearer, mensagem ou GPS. Consultar a matriz OWASP para limites.

## EDA, teste estatístico e pytest

```powershell
python eda/eda.py
python eda/eda_tp2.py
python -m scripts.build_notebook_tp2
pytest tests/
# Para regenerar a evidência XML:
pytest tests/ --junitxml=reports/tests_tp2.xml
```

Não requer rede para EDA: dataset presente em data/. O notebook TP2 foi executado e
inclui heatmaps Pearson/Spearman, dois scatters, violin plot e Mann-Whitney U bilateral
da H2 do TP1, com efeito e IC bootstrap. Resultado é exploratório e não valida fraude.
O TP1 permanece em eda/eda.ipynb e reports/analysis.md.

## Dataset, licença e justificativa

**CLINC150**, recorte curado de 20 intenções, 3.000 mensagens. Autores: Stefan Larson
et al. (2019), Clinc. [Fonte original](https://github.com/clinc/oos-eval),
[artigo EMNLP-IJCNLP](https://aclanthology.org/D19-1131/),
[licença CC BY 3.0 Unported](https://creativecommons.org/licenses/by/3.0/).
Cópia em data/LICENSE-CLINC150.txt. Código do projeto sob MIT.

Escolhido por conter texto e intenção supervisionada, reservas de voo/hotel, bagagem,
aluguel, localização e recompensas. É seleção própria de 20 rótulos, não domínio oficial
único. Textos em inglês e de crowdsourcing, não chamados reais. Recompensas são genéricas;
não há GPS, transações ou fraude confirmada. Não inferir elegibilidade de benefício.

data/provenance.json registra commit, URLs e SHA-256. Transformações: seleção de rótulos,
ID/split adicionados, sem tradução. `python -m scripts.prepare_data` reconstrói o recorte
pela revisão fixada (requer rede); `python eda/eda.py` reconstrói a versão limpa.

## Reproduzir o ZAP e gerar PDF

```powershell
# Windows; requer OpenSSL (ex.: Git for Windows):
python -m scripts.setup_zap
python -m scripts.run_zap
# Auditoria de dependências (requer rede):
python -m pip install -r requirements-security.txt
python -m pip_audit -r requirements-lock.txt -f json -o reports/dependency-audit.json
# PDF (após EDA, testes e ZAP):
python -m pip install -r requirements-report.txt
python -m scripts.build_report_tp2
```

O runner usa ferramentas portáteis em tmp/, somente loopback, contas/chaves/certificado
descartáveis e modo safe/passivo. Exporta HTML, JSON, regras habilitadas e ledger de
requisições. Apenas segredos efêmeros são redigidos na exportação. Não muda trust store
do sistema. Veja reports/zap/findings.md antes de reproduzir.

## Estrutura

```text
main.py                  # FastAPI + configuração de middleware
app/                     # SQLModel, schemas, JWT, limiter, auditoria
  routes/                # health, auth, predict, reservations
data/                    # bruto, CSVs, licença, proveniência
eda/                     # TP1 e TP2: scripts + notebooks executados
tests/                   # autenticação, BOLA, input, headers, CORS, limiter
scripts/                 # cadastro, dados, notebooks, ZAP, PDF
reports/tp2/             # EDA estruturada, estatística, heatmap e scatters
reports/zap/             # HTML/JSON ZAP, findings e escopo
docs/                    # OWASP, DFD, CIA e entrega
output/pdf/              # Helena_Gomes_PB_TP1.PDF e Helena_Gomes_PB_TP2.PDF
```

Orientações finais: [entrega TP2](docs/delivery_tp2.md). O relatório TP1 permanece como
histórico; os controles e limites atuais são os documentados em docs/owasp_tp2.md.
