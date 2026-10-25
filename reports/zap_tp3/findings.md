# Auditoria final TP3 - TourShield v0.3.0

Helena Gomes | 25/10/2026

## Escopo e execução

ZAP 2.17.0, modo safe, somente scan passivo, sem spider ou active scan; 61 regras
habilitadas. Alvo desta execução: https://localhost:61150. **25 requisições** com fila
passiva zerada antes de exportar. Certificado TLS e contas são locais e descartáveis.
Incluiu os fluxos do TP2 e **/docs + quatro assets self-hosted**, sem CDN. Tráfego e
versões em scan-metadata.json; ferramentas com proveniência em reports/zap/tool_provenance.json.

## Resultado e tratamento

| Severidade | Ocorrências | Situação |
|---|---:|---|
| High | 0 | Sem finding pendente |
| Medium | 0 | Sem finding pendente |
| Low | 33 | Aceitos como falsos positivos informativos de timestamp no bundle estático |
| Informational | 10 | Revisados e aceitos conforme tabela abaixo |

| Plugin | Descrição | n | Status e justificativa |
|---|---|---:|---|
| 10096 | Timestamp Disclosure - Unix (Low) | 33 | **Aceito / falso positivo:** números no JavaScript vendorizado são interpretados como datas Unix pela heurística. Ex.: 1518500249 aparece no vetor de constantes da implementação SHA-1 do bundle público. Não é data de operação, sessão ou usuário da API. Arquivo e hash são do pacote Swagger UI 5.34.0, sem dados de runtime. Não modificar dependência minificada só para ocultar alerta. |
| 10015 | Re-examine Cache-control Directives (Informational) | 5 | **Aceito:** no-store intencional em respostas e documentação. Não retirar proteção de cache para zerar relatório. |
| 10111 | Authentication Request Identified (Informational) | 3 | **Aceito:** login esperado com campo password; TLS no scan, Argon2, limite de tentativas e erro genérico. |
| 10112 | Session Management Response Identified (Informational) | 1 | **Aceito:** access_token é saída contratual de sessão, com expiração e no-store. |
| 10027 | Suspicious Comments (Informational) | 1 | **Aceito / falso positivo:** heurística identifica QUERY dentro do código público do bundle de documentação. Não há query de banco, senha ou comentário interno do projeto revelado. |

Todos os 33 Low foram localizados no mesmo asset `/static/swagger/swagger-ui-bundle.js`.
A revisão não demonstra que SHA-1 seria adequado para proteger senhas: a API usa Argon2id
e HS256. A referência ao algoritmo explica uma constante em biblioteca de terceiros,
não uma decisão de criptografia de autenticação do TourShield.

Não havia Medium/High pendente do TP2 e o novo scan não detectou essas severidades.
Não se relata correção inexistente. Relatórios originais HTML/JSON e alertas permanecem
sem supressão de regras. Apenas segredos efêmeros de teste são redigidos, como no TP2.

## Prontidão local

Ledger comprova: /health 200, /docs 200, login 200, /predict 401 sem token e 200 com token,
recurso próprio 200 e de outro usuário 404, campo extra 422, CORS negado 400 e rate limit
429. /docs usa JS/CSS locais, política sem unsafe-inline e sem persistir token em storage.
Os testes também verificam integridade de assets, contrato OpenAPI, headers e isolamento.

**Pronto para pentest local de laboratório**, com dados fictícios. Não é declaração
de produção segura ou autorização para atacar terceiros. A URL pública desta API e
a troca de acesso com colega não foram configuradas. O colega adversário/URL/confirmação
continuam pendentes conforme informação da aluna.

## Reprodução e limites

`python -m scripts.setup_zap` (se necessário), depois `python -m scripts.run_zap --tp3`.
O HTML e JSON são exportados pelo ZAP. A porta muda por execução. O método e limitações
do TP2 continuam válidos: scan passivo não explora SQLi, não descobre tudo e não prova
ausência de BOLA. Certificado autoassinado serve ao laboratório, não à exposição pública.
Biblioteca de docs deve ser reavaliada quando atualizada; hashes e licença em app/static/swagger/.
