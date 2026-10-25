# Auditoria passiva OWASP ZAP - TP2

Helena Gomes | TourShield API | 25/10/2026

## Execução e escopo

ZAP **2.17.0**, distribuição oficial Crossplatform; Java Temurin 21. Downloads e
SHA-256 verificados contra os fornecedores em `tool_provenance.json`. Scan executado
em modo **safe**, exclusivamente passivo, por proxy local, sem spider ou active scan.
As 61 regras passivas disponíveis estavam habilitadas; versões e regras completas
constam em `scan-metadata.json`. Não houve exclusão ou filtro para ocultar findings.

Alvo: `https://localhost:62418` (porta efêmera desta execução), somente TourShield local.
Uvicorn com TLS e certificado autoassinado descartável; cliente de teste confia no
proxy ZAP apenas neste processo (`verify=False` restrito ao script local). Nenhuma
configuração de confiança do sistema foi alterada. HSTS só tem efeito em HTTPS;
enviar esse header em HTTP não oferece a mesma proteção.

Foram enviadas **20 requisições**: health, OpenAPI, rota inexistente, login de dois
usuários, predição com e sem token, campos extras, coordenada inválida, criação e
leitura de reserva própria, BOLA, acesso sem token, tentativa de atribuir owner,
CORS permitido/negado e bloqueio de autenticação. O ledger registra os status
observados e esperados. A fila `recordsToScan` estava em **0** antes da exportação.

## Resultado exportado

| Severidade | Ocorrências |
|---|---:|
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Informational | 8 |

Há três tipos de alerta informativo. Contagens são ocorrências/instâncias retornadas
pela API ZAP; não representam oito vulnerabilidades diferentes.

| Plugin / finding | Severidade | Ocorrências | Descrição e análise | Status / justificativa |
|---|---|---:|---|---|
| 10015 - Re-examine Cache-control Directives | Informational | 4 | Regra solicita revisão de cache. Evidência: `no-store` em health, OpenAPI, predict e reserva. | Aceito: no-store é intencional para evitar armazenamento de respostas potencialmente sensíveis. Também há Pragma: no-cache. Não se remove proteção para eliminar aviso. |
| 10111 - Authentication Request Identified | Informational | 3 | ZAP reconheceu campo password no formulário de login; auxilia a configuração de autenticação do scanner. | Aceito: rota de login esperada. Senha trafegou por HTTPS; Argon2 no banco, throttling, erro genérico e no-store aplicados. |
| 10112 - Session Management Response Identified | Informational | 1 | ZAP reconheceu `access_token` na resposta JSON. | Aceito: JWT é a resposta contratual. Expira em 15 min, claims e assinatura validadas, retorno no-store e sem credencial em URL. |

**Medium/High:** nenhum foi detectado nesta execução. Portanto não há finding dessas
severidades que exija correção ou aceite de risco. Não foi inventada uma rodada
"antes/depois": o scan evidencia a versão já protegida. Caso uma futura execução
detecte Medium/High, registrar descrição, impacto, correção ou aceite motivado e reexecutar.

Os relatórios HTML e JSON foram exportados pela própria API do ZAP. Apenas segredos
efêmeros da execução (senhas/tokens de teste e chave da API ZAP, se presentes) são
substituídos por marcador; severidades, evidências de alertas e contagens permanecem.
Contas, banco, chaves e certificado são descartáveis e não pertencem a usuários reais.

## Reprodução

Ambiente verificado: Windows, Python 3.12, OpenSSL do Git for Windows.

```powershell
python -m pip install -r requirements-lock.txt
python -m scripts.setup_zap
python -m scripts.run_zap
```

O setup baixa arquivos oficiais para `tmp/tools` (ignorado pelo Git), confere hashes,
e não instala programas globalmente. Requer rede e cerca de algumas centenas de MB.
O runner cria certificados com OpenSSL, inicia ZAP/Java e Uvicorn locais, gera tráfego,
aguarda fila passiva zerar e exporta os relatórios. Ele encerra os processos ao final.
O `-silent` impede chamadas espontâneas do ZAP. Portas e data mudarão em cada execução.

Arquivos: `zap-report.html`, `zap-report.json`, `alerts.json`, `scan-metadata.json`
e `tool_provenance.json`. O HTML pode ser aberto diretamente no navegador.

## Limitações

Auditoria passiva inspeciona somente mensagens exercitadas. Não tenta explorar SQLi,
forjar tokens, descobrir endpoints ocultos ou provar ausência de BOLA; esses aspectos
têm testes automatizados separados, sem equivaler a pentest completo. Não é certificação
OWASP. Certificado local autoassinado serve ao laboratório, não a implantação pública.
As regras são as distribuídas com a versão registrada, sem atualização durante a execução.

Referências oficiais:
- https://www.zaproxy.org/docs/api/
- https://www.zaproxy.org/docs/desktop/cmdline/
- https://www.zaproxy.org/docs/alerts/10015/
- https://www.zaproxy.org/docs/alerts/10111/
- https://www.zaproxy.org/docs/alerts/10112/
