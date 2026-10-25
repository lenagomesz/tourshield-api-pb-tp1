# Regressão linear - consolidação TP3

Helena Gomes | 25/10/2026

## Problema e pipeline

Experimento didático: prever número de palavras por mensagem, alvo numérico derivado
por separação em espaços. Fonte CLINC150, recorte TourShield de 3.000 mensagens.
Splits originais preservados: 2.000 treino, 400 validação e 600 teste. Não houve busca
de hiperparâmetros ou escolha do modelo pela métrica de teste.

Baseline: DummyRegressor (média do treino). Regressão simples: n_chars. Regressão
múltipla: n_chars, n_digits, n_punctuation e uppercase_ratio inicialmente propostos.
Pipeline completo: ColumnTransformer -> SimpleImputer(mediana) -> VarianceThreshold
-> StandardScaler -> LinearRegression. Componentes aprendidos ajustados só no treino.
uppercase_ratio é constante zero no treino e foi removida automaticamente; permanecem
três preditores. Não usar n_words em X nem a média de comprimento de palavra, que
reconstruiria diretamente o alvo com n_chars.

## Métricas no teste (600 mensagens)

| Modelo | R² | RMSE (palavras) | MAE (palavras) |
|---|---:|---:|---:|
| Baseline média | -0,0116 | 3,7874 | 3,0443 |
| Linear simples | 0,8747 | 1,3331 | 1,0559 |
| Linear múltipla | 0,8789 | 1,3102 | 1,0401 |

R² mede ganho em erro quadrático frente à média do conjunto avaliado; não é acurácia.
O baseline usa média do treino, por isso pode ter R² negativo no teste. RMSE enfatiza
erros maiores; a múltipla erra cerca de 1,31 palavra nessa escala. Ganho sobre a simples
é pequeno: ΔR²≈0,0043 e redução de RMSE≈0,023 palavra. Não exagerar relevância prática.
Treino/validação/teste completos em regression_metrics.csv.

## Resíduos e Q-Q

Resíduo = observado - previsto. Média no teste -0,0904 palavra (leve superestimação),
DP 1,3082, assimetria 0,2636 e excesso de curtose 0,3521. O residual plot mostra faixas
diagonais porque y é contagem discreta, com dispersão variável. Correlação Spearman
entre |resíduo| e previsto é 0,1611, descritiva, sugerindo cautela com variância constante.
Não foi feito teste formal de homoscedasticidade nem calculado intervalo clássico.

O Q-Q acompanha a reta na região central e se desvia nas caudas, sobretudo a superior.
Não afirmar normalidade exata. A normalidade dos resíduos não é condição para calcular
predições OLS, mas afeta inferência paramétrica e intervalos tradicionais. Não foram
feitas inferências causais sobre coeficientes. Não houve predições negativas no teste;
isso não garante o mesmo fora da amostra, e OLS pode produzir frações/valores negativos.

## Limitações e próximos passos

O comprimento em palavras pode ser contado diretamente, sem ML. A relação estrutural
com caracteres explica boa parte do R²; não é prova de semântica, intenção ou fraude.
As features fixas são computáveis em uma nova mensagem, sem usar rótulo de intenção,
mas o exercício não agrega valor operacional ao problema real. Não o chamar de
classificador nem afirmar que a API faz inferência.

Base em inglês, balanceada e crowdsourced, sem IDs de autores; independência e validade
externa são limitadas. Val/test já foram vistos na EDA. Uppercase_ratio ASCII não
generaliza automaticamente para português. Não há GPS ou fraude rotulada.

Próximo passo: Pipeline TF-IDF + regressão logística multiclasse, baselines, seleção
na validação e macro-F1/recall/matriz de confusão. Pergunta de classificação e protocolo
estão em docs/classification_question_tp3.md e docs/t2_plan_tp3.md.
