# Planejamento técnico T2 - TourShield

Helena Gomes | 25/10/2026

## Estado do pivô

T1 consolidado: EDA, inferência exploratória, regressão didática, API autenticada,
ownership, controles HTTP, suíte de segurança e scan passivo. Nenhum classificador
treinado ou conectado a /predict nesta entrega. Regressão de comprimento é experimento
analítico separado e não adiciona função de negócio à API.

## Modelo candidato e features

**Candidato principal:** regressão logística multiclasse regularizada (L2), por ser
baseline linear eficiente, interpretável por pesos e adequado a texto esparso.
**Alternativa predefinida:** LinearSVC caso a regressão logística tenha desempenho
insuficiente. A troca deve ser justificada por validação, sem escolher pelo teste.

Pipeline proposto: `TfidfVectorizer -> LogisticRegression`. Configuração inicial:
lowercase=True, ngram_range=(1,2), min_df=2, max_features=10.000, sublinear_tf=True;
sem stopwords automáticas (negações podem mudar intenção). Não traduzir o benchmark.
LogisticRegression: regularização L2, solver lbfgs, max_iter=2.000; comparar C em
{0,1; 1; 10} somente na validação. Não usar intent, split, ID ou rótulo numérico como X.

Vocabulário, IDF, seleção e normalização aprendida devem ser ajustados exclusivamente
no treino por Pipeline. Não fazer fit_transform no dataset inteiro antes da divisão.
Hiperparâmetros ficam registrados antes da avaliação final e convergência será verificada.

## Experimentos e critérios

1. Treino 2.000, validação 400, teste 600 preservados. Auditar duplicatas entre splits.
2. Baselines: classe majoritária e classificador baseado em comprimento. O dummy
   em base uniforme acerta 5% das classes por frequência, sem resolver intenção.
3. Escolher configuração por macro-F1 na validação; desempatar pela mais simples.
4. Reportar macro-F1, acurácia, recall por classe, matriz de confusão, latência e tamanho
   do artefato. Não prometer limiar de desempenho sem experimento; exigir ganho sobre dummy.
5. Usar teste uma vez após congelar decisões. A EDA já descreveu esse teste: documentar
   o reuso e obter conjunto externo intocado para confirmação em português.
6. Analisar confusões book_flight/book_hotel e saldo/resgate sem expor PII. Avaliar
   multi-intenção e out-of-scope com novos dados, sem prometer detecção por este recorte.

## Integração futura e integridade

Carregar somente artefato produzido pelo projeto e verificado por hash; não aceitar
pickle/joblib enviado por usuário. Versionar vocabulário, modelo, dependências e métricas.
Manter contrato de /predict e distinguir indisponibilidade de modelo de baixa confiança.
JWT, ownership e elegibilidade permanecem no servidor, independentes da predição.
Testes de segurança serão obrigatórios no CI antes de qualquer merge da integração.

## Adversário e alvo TP4/TP5

| Campo obrigatório | Estado atual |
|---|---|
| Colega adversário | **Pendente - não informado pela aluna** |
| URL ou IP da API adversária | **Pendente - nenhum alvo inventado** |
| Confirmação de acesso pelo colega | **Pendente - não recebida** |
| Autorização/escopo e janela de teste | **Pendente de acordo entre os participantes** |

Em 25/10/2026, a aluna informou que esses dados estão pendentes e solicitou concluir
o restante da atividade. O planejamento técnico está concluído; a definição externa
do alvo permanece pendente. Não afirmar que houve confirmação nem iniciar pentest
contra qualquer sistema. Antes do TP4, registrar nome, URL, data da confirmação,
contas de laboratório e escopo acordado. Não versionar senhas ou tokens.

## Prontidão local e sequência

Prontidão local: /health, /docs, JWT e duas contas fictícias exercitados na auditoria.
`scripts/seed_pentest.py` cria um laboratório isolado com dois proprietários e reservas;
credenciais ficam somente em tmp/ ignorado. 127.0.0.1 não é URL pública para colega.
Disponibilização externa, certificado válido e confirmação do parceiro ainda exigem
coordenação. Não expor diretamente dados reais ou modo --reload à rede pública.

Sequência sem inventar prazo do professor: confirmar adversário/alvo; congelar protocolo
de classificação; treinar baselines e candidato; validar erros; avaliar teste; integrar
artefato confiável; executar novamente pytest, ZAP e checklist antes da próxima entrega.
