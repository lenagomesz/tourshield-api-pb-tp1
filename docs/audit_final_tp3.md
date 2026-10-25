# Auditoria final e prontidão de pentest - TP3

Helena Gomes | 25/10/2026 | TourShield v0.3.0

## Checklist de segurança

| Item | Status | Evidência e limite |
|---|---|---|
| Health e startup sem erro | Resolvido | Tráfego local real no ZAP; ausência de segredo falha fechada |
| JWT e senhas | Resolvido | Argon2id, JWT 15 min, claims obrigatórias, conta ativa; pytest |
| Ownership / BOLA | Resolvido | Consulta ID+owner; outro usuário e inexistente 404; testes e ledger ZAP |
| Entrada e mass assignment | Resolvido | extra=forbid nos modelos; owner/status fora do body; 422 |
| Consultas parametrizadas | Resolvido | SQLModel, sem SQL raw na API/CLI/testes |
| Rate limit login | Resolvido | 5/IP/60s; 429+Retry-After; teste de janela e spoofing XFF |
| Headers, CORS e host | Resolvido | Middleware, allowlists, teste em sucesso/erros |
| /docs e OpenAPI | Resolvido | Swagger self-hosted, assets fixados/verificados, CSP restritiva, contrato v0.3.0 |
| Limite de corpo / exceções | Resolvido | 16 KiB, timeout 10s, 500 sem detalhes, auditoria de status |
| Logs sem credenciais | Resolvido | JSON com metadados; teste assegura ausência de JWT, senha e mensagem |
| Dependências | Resolvido no snapshot | pip-audit em reports/tp3/dependency-audit.json; reavaliar antes de implantar |
| Medium/High ZAP | Resolvido no escopo | Zero no TP2 e no scan final com /docs; não é prova de ausência global |
| Low/Info ZAP | Aceito | 33 Low e 10 Info revisados; justificativas em reports/zap_tp3/findings.md |
| Testes no CI | Resolvido após execução verificada | Workflow security-tests.yml; evidência em reports/tp3/ci_evidence.json |
| Check obrigatório para merge | Resolvido após configuração verificada | security-tests exigido na main, inclusive administradores; evidência JSON |
| Dados fictícios de laboratório | Resolvido | Duas contas e recurso próprio/alheio exercitados; seed_pentest.py para recriar |
| MFA, revogação individual, limiter distribuído | Aceito no laboratório | Não implementados; um processo, limitação conhecida; pendência de produção |
| TLS público, backup e alertas externos | Aceito no laboratório | Scan em TLS local; implantação externa exige configuração e revisão próprias |
| Confirmação de colega/alvo | Pendente externo | Não informados; não equivale a risco técnico aceito nem a confirmação fictícia |

O status de CI/merge é sustentado pelo snapshot JSON quando preenchido; se a execução
ou API de proteção falhar, a pendência deve ser registrada, sem afirmar controle ativo.
Os demais controles foram exercitados localmente e no scan passivo final.

## Laboratório reprodutível

Na instalação local, gerar `.env` com segredo aleatório e **DATABASE_PATH=./pentest.sqlite3**.
`python -m scripts.seed_pentest` cria lab_alice e lab_bob e uma reserva para cada uma.
Senhas aleatórias e IDs são gravados somente em `tmp/pentest-credentials.json`, ignorado
pelo Git. Não versionar ou expor esse arquivo. O script não sobrescreve contas existentes.

Rodar `uvicorn main:app --reload --no-proxy-headers --no-server-header` em loopback.
Consultar /health e /docs; obter token de cada usuário; consultar recurso próprio e
de outro usuário. O scanner já executou esse roteiro com contas/banco efêmeros separados.
Para colega remoto, loopback não é endereço acessível: combinar hospedagem/túnel autorizado,
TLS válido e contas fictícias, sem usar --reload em exposição pública.

## Resultado final

O código está consolidado como alvo **local** de pentest, sem novas funções de negócio.
Regressão é notebook separado; /predict continua placeholder. A liberação para os
TP4/TP5 contra colega depende de nome, URL e confirmação ainda pendentes.
