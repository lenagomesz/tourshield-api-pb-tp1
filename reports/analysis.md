# Resultados e interpretação da EDA

Helena Gomes | TourShield | PB TP1 | 25/10/2026

## Qualidade e decisões

O recorte tem **3.000 linhas e 4 colunas originais**: `sample_id`, `message`, `intent`,
`split`, todas lidas como string do Pandas. Há 3.000 IDs e mensagens distintos,
20 intenções e três splits. A análise `describe(include='all')` e o `describe()`
numérico são exportados em CSV e exibidos no notebook/script.

Ausentes: zero em cada coluna. Duplicatas integrais: zero; pares mensagem/intenção
repetidos: zero; repetições após normalização de caixa e espaços: zero; conflitos
de intenção: zero. Nenhuma linha foi removida ou imputada. A normalização existe
apenas em chave auxiliar; o texto original é preservado, salvo strip das bordas.
Mensagens longas foram mantidas: tamanho não prova erro. Exportação limpa tem
3.000 linhas e seis colunas, após adicionar `n_chars` e `n_words`.

Splits preservados: treino 2.000, validação 400, teste 600; cada intenção possui
100/20/30 exemplos, respectivamente. Não há chave textual normalizada compartilhada
entre splits após a auditoria. Para futuro ML, manter esses splits e evitar ajuste
de parâmetros pelo teste. A exploração atual é descritiva, sem treinamento.

## Estatísticas de comprimento

| Estatística | Caracteres | Palavras |
|---|---:|---:|
| n | 3.000 | 3.000 |
| Média | 50,09 | 10,26 |
| Desvio padrão amostral | 17,37 | 3,65 |
| Mínimo | 8 | 2 |
| Q1 | 38 | 8 |
| Mediana | 48 | 10 |
| Q3 | 60 | 12 |
| Máximo | 136 | 28 |

Palavras são tokens delimitados por espaços, não tokens de um modelo de linguagem.
IQR de palavras = 4; limite superior Q3 + 1,5 IQR = 18. Há 98 mensagens acima do
limite (3,27%), mantidas por poderem conter detalhes legítimos de atendimento.

## Visualizações e hipóteses

1. **Histograma** (`figures/01_histogram.png`): centro em torno de 10 palavras,
   com cauda até 28. Não é justificativa para truncar todas as mensagens maiores.
2. **Barras** (`figures/02_categories.png`): todas as 20 intenções têm 150 registros
   (5%). **H1:** esse equilíbrio não deve se repetir em produção. O padrão decorre
   do desenho do benchmark, não da demanda por atendimento. Validar em chamados
   reais, com contagens por período e região, mantendo amostragem documentada.
3. **Boxplot** (`figures/03_boxplot.png`): `book_flight` tem mediana 15 palavras,
   `book_hotel` 14, `current_location` e `share_location` 7.
   **H2:** solicitações de reservas exigem mais contexto que localização. Grupo
   reservas (750 mensagens) tem mediana 12, contra 8 para localização (600).
   A diferença é descritiva e os grupos são curados. Validar em amostra externa
   com bootstrap do efeito e teste não paramétrico previamente definido.
4. **H3:** tamanho sozinho pode ser insuficiente para distinguir consulta de saldo
   de resgate de benefícios: `rewards_balance` e `redeem_rewards` têm ambas mediana
   10 e médias 10,03 e 10,32. O boxplot mostra sobreposição. Futuramente comparar
   baseline baseado em comprimento e representação textual, usando macro-F1,
   recall por classe e matriz de confusão nos splits preservados. Não foi treinado
   modelo neste TP, e esses rótulos não identificam fraude.

## Limites de validade

Enunciados em inglês obtidos por crowdsourcing e de intenção única; não representam
integralmente chamados reais em português, multi-intenção ou desbalanceados.
Categorias de benefício são genéricas, não específicas de turismo. O recorte não
retém amostras out-of-scope do benchmark e não avalia rejeição de intenções desconhecidas.
Não há GPS, reserva vinculada a pessoa, saldo, transação ou fraude confirmada.
Não inferir elegibilidade, prevalência de fraude, geofence ou spoofing a partir desta EDA.

Fonte: Stefan Larson et al. (2019), CLINC150, https://github.com/clinc/oos-eval,
licença CC BY 3.0. Transformações e hashes documentados em `data/provenance.json`.
