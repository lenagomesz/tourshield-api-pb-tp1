# TourShield API - Turismo e Reservas

**Helena Gomes | Projeto de Bloco - TP1 | 25/10/2026**

Base de atendimento ao cliente em turismo, com EDA reprodutível e API FastAPI autenticada.
Foco de segurança: fraude de benefícios e geolocalização. Não há modelo de ML nem agente
neste TP; `/predict` retorna explicitamente um placeholder e não autoriza operações.

## Dataset e justificativa

- **Nome:** CLINC150, recorte curado TourShield com 20 intenções (3.000 mensagens antes da limpeza).
- **Autores/fonte:** Stefan Larson e colaboradores, Clinc, 2019. [Repositório original](https://github.com/clinc/oos-eval).
- **Artigo:** [An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction](https://aclanthology.org/D19-1131/).
- **Licença dos dados:** [Creative Commons Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/).
  Cópia integral em `data/LICENSE-CLINC150.txt`. O código usa licença MIT separada.
- **Rastreabilidade:** commit, URL exata, SHA-256 e lista de intenções em `data/provenance.json`.
- **Escolha:** textos com intenção supervisionada, reservas de voo/hotel, aluguel de carro,
  bagagem e dúvidas de viagem. Categorias de localização e recompensas complementam o tema.
  A seleção é curada pelo projeto, não um domínio oficial único do CLINC150.
- **Transformação:** filtro explícito de 20 rótulos; acréscimo de ID e split; texto não traduzido.
  `redeem_rewards` e `rewards_balance` são intenções genéricas de recompensas e não prova de
  benefícios turísticos. Os dados são enunciados de crowdsourcing, não tickets operacionais.
  Não há GPS, transações nem rótulo de fraude. Não se pode medir fraude com esta base.
- **Atribuição:** Larson et al. (2019), *An Evaluation Dataset for Intent Classification and
  Out-of-Scope Prediction*, EMNLP-IJCNLP, https://aclanthology.org/D19-1131/.

## Instalação (Python 3.12)

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; from pathlib import Path; Path('.env').write_text('JWT_SECRET=' + secrets.token_urlsafe(48) + '\nDATABASE_PATH=./tourshield.sqlite3\n', encoding='utf-8')"
python -m scripts.create_user helena
uvicorn main:app --reload
```

O comando de geração sobrescreve `.env`: execute uma vez na instalação; regenerar a chave
invalida os tokens existentes. A CLI solicita senha de 12-1024 caracteres sem ecoar.
Não existe senha padrão nem cadastro público. Guarde a senha escolhida.
Se a política do PowerShell impedir ativação, use `.\.venv\Scripts\python.exe` e
`.\.venv\Scripts\uvicorn.exe` diretamente. No Linux/macOS: `source .venv/bin/activate`
e `cp .env.example .env`, seguidos pelos mesmos comandos Python.

Servidor: http://127.0.0.1:8000 ; Swagger: http://127.0.0.1:8000/docs .
No Swagger use **Authorize**, informe o usuário criado e a senha. Não preencha client_id/secret.
`--reload` é apenas para desenvolvimento. Não exponha externamente sem HTTPS e controles
adicionais descritos em `docs/security.md`.

## Rotas e demonstração

| Rota | Acesso | Resultado |
|---|---|---|
| GET /health | Público | 200, status ok (liveness) |
| POST /auth/token | Form username/password | 200 JWT bearer ou 401 |
| POST /predict | Bearer JWT | 200 placeholder; sem token 401; entrada inválida 422 |

Exemplo PowerShell (senha solicitada sem mostrá-la na linha de comando):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$credential = Get-Credential -UserName helena
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/token -Body @{username=$credential.UserName; password=$credential.GetNetworkCredential().Password}
$headers = @{Authorization="Bearer $($login.access_token)"}
$body = @{message='Quero reservar um hotel'; latitude=-22.9; longitude=-43.2} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/predict -Headers $headers -ContentType application/json -Body $body
# Deve retornar HTTP 401:
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/predict -ContentType application/json -Body '{"message":"Reservar hotel"}'
```

JWT HS256 expira em 15 minutos, com validação de emissor e público. SQLite armazena apenas
usuário, hash Argon2 e flag ativo. Texto e GPS não são armazenados nem refletidos na resposta.
Mensagem aceita 1-4.000 caracteres após rejeição de texto em branco; coordenadas devem vir
em par (latitude -90 a 90, longitude -180 a 180). Localização não concede benefício.

## EDA e testes

```powershell
python eda/eda.py
python -m pytest -q
```

Não requer rede: CSV original do recorte e bruto estão em `data/`. A análise exporta
shape, tipos, describe, ausentes, auditoria de duplicatas, distribuição e três gráficos.
`eda/eda.ipynb` contém células e saídas executadas; também pode ser executado no Jupyter
(instale Jupyter separadamente para usar interface web). O `.py` é equivalente e atende
à evidência solicitada. Decisões de limpeza e hipóteses estão nas células comentadas,
com resultados interpretados em `reports/analysis.md`.

Para reconstruir os dados pela fonte fixada (requer internet):

```powershell
python -m scripts.prepare_data
python eda/eda.py
```

O script reutiliza o commit registrado em `provenance.json`. Preserve os splits: a EDA
é descritiva; não usar o teste para escolher hiperparâmetros nos próximos TPs.

Para reconstruir o notebook: `python -m scripts.build_notebook`. Para gerar novamente
o PDF, instale `requirements-report.txt`, execute `python -m scripts.smoke`,
`python -m pytest --junitxml=reports/tests.xml` e `python -m scripts.build_report`.

## Estrutura de pastas

```text
main.py                  # uvicorn main:app --reload
app/
  config.py              # .env e configuração JWT
  database.py            # SQLite e consultas parametrizadas
  models.py              # schemas Pydantic
  security.py            # hashing, emissão e validação JWT
  routes/                # health.py, auth.py, predict.py
scripts/
  create_user.py         # cadastro administrativo interativo
  prepare_data.py        # reconstrução a partir da fonte fixada
eda/                     # eda.py e notebook executado
data/                    # bruto, recorte, limpo, licença e proveniência
reports/                 # tabelas, métricas e três figuras
docs/security.md         # DFD Mermaid, trust boundaries e CIA
tests/                   # testes funcionais de autenticação e validação
output/pdf/              # relatório da entrega
requirements.txt         # versões efetivamente verificadas
```

## Segurança e entrega

Leia [DFD e matriz CIA](docs/security.md). Esta base local ainda precisa de rate limiting,
TLS/proxy, backup e observabilidade antes de implantação. O benchmark não substitui dados
reais de turismo em português nem dados autorizados para investigação de fraude.

O PDF reúne resultados, gráficos, arquitetura e evidências. O código executável, dados
e notebook devem ser enviados no mesmo repositório. Consulte `docs/delivery.md` para o
estado de publicação e os passos finais de entrega.
