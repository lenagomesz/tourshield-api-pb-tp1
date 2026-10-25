# TourShield - Relatório estruturado de EDA (TP2)

Helena Gomes | Projeto de Bloco | 25/10/2026

## Problema

Caracterizar mensagens de atendimento relacionadas a turismo e reservas para preparar
um futuro classificador de intenções. O foco de segurança é fraude de benefícios e
geolocalização; não se busca detectar fraude com uma base que não contém esses rótulos.
Retoma-se H2 do TP1: mensagens de reservas podem exigir mais contexto textual que
consultas de localização. Nenhum modelo foi treinado neste TP.

## Dados

Recorte curado CLINC150, de Stefan Larson et al. (2019), fonte
https://github.com/clinc/oos-eval, licença CC BY 3.0 Unported. Manifesto fixado por commit
e SHA-256 em `data/provenance.json`, com licença integral e arquivo bruto preservados.

3.000 mensagens em inglês, de crowdsourcing; 20 intenções com 150 registros (5%) cada.
Shape original (3.000, 4): sample_id, message, intent, split (strings). Shape limpo
(3.000, 6), com n_chars e n_words. Ausentes, duplicatas normalizadas e conflitos: zero.
Nenhuma linha removida, imputada ou traduzida. Regras e auditoria detalhadas no TP1,
em `eda/eda.py` e `reports/analysis.md`. Os splits permanecem 2.000/400/600, sem
sobreposição textual normalizada. A seleção de 20 rótulos é decisão deste projeto,
não um domínio oficial único do CLINC150.

## Análise

Comprimento em palavras: média 10,26; DP amostral 3,65; mediana 10; Q1 8; Q3 12;
intervalo 2-28. Caracteres: média 50,09; DP 17,37; mediana 48; intervalo 8-136.
98 mensagens acima de 18 palavras (regra de IQR) são mantidas, pois tamanho não prova erro.

Variáveis novas: comprimento médio das palavras e razão de palavras únicas, derivados
com Pandas. Intenção não foi codificada como número para calcular correlações sem sentido.
Heatmap seaborn apresenta Pearson e Spearman; dois scatter plots mostram caracteres
versus palavras e palavras versus comprimento médio da palavra, coloridos por grupo.
Um violin plot complementa a comparação formal de reservas e localização.

Pearson entre caracteres e palavras: **r=0,9351**; Spearman: **rho=0,9214**. É associação
forte e esperada entre duas medidas do mesmo texto; sugere redundância, não causalidade.
Os scatters mostram sobreposição entre grupos: comprimento não é um classificador pronto.

### Teste formal - H2 do TP1

- Grupo reservas: book_flight, book_hotel, cancel_reservation, confirm_reservation e
  car_rental; n=750, mediana=12 palavras.
- Grupo localização: current_location, directions, distance e share_location; n=600,
  mediana=8 palavras.
- H0: distribuições de n_words iguais entre os grupos; H1: distribuições diferentes.
- Mann-Whitney U bilateral (SciPy), alfa=0,05, método assintótico com correções de
  empates e continuidade. Não pressupõe normalidade; pressupõe independência.
- **U=346.424; p=1,2825 × 10^-65**. Um único contraste principal, sem seleção por p-valor.

Rejeita-se H0 neste benchmark. Em linguagem simples: o padrão observado é pouco
compatível com distribuições iguais sob as premissas do teste. O p-valor não é a
probabilidade de H0 ser verdadeira e não mede importância prática nem prova causalidade.
Como a hipótese foi sugerida pela mesma base no TP1, é resultado **exploratório**,
não confirmação em dados externos nem em um teste intocado.

Tamanho de efeito: **Cliff's delta=0,5397** (positivo para reservas maiores). A probabilidade
de uma mensagem de reserva ter maior comprimento que uma de localização, contando
empates pela metade, é **76,98%** nesta comparação empírica. Diferença de medianas:
**4 palavras**, IC95% bootstrap percentil **[3; 5]**, com 5.000 reamostragens e semente 42.
O teste compara distribuições; com formatos diferentes não deve ser descrito apenas
como teste de medianas. O IC descreve a diferença de medianas separadamente.

## Insights principais

1. Comprimentos em palavras e caracteres carregam informação redundante. Avaliar sua
   utilidade incremental no treino/validação, sem assumir que ambos melhorem o modelo.
2. Reservas tendem a conter mais contexto textual que localização nesta base, mas há
   sobreposição; não usar um limiar de tamanho para determinar intenção.
3. O balanceamento é artificial. Frequência de classes não representa demanda real,
   e uma avaliação futura deve considerar macro-F1 e recall por intenção.
4. Recompensas continuam semanticamente distintas (saldo/resgate), embora com medianas
   iguais. Classificação de intenção e autorização de benefício são decisões separadas.

## Limitações

Inglês, crowdsourcing, intenção única, recorte curado e classes balanceadas reduzem
validade externa. Mistura de intenções nos grupos pode explicar parte da diferença.
Não há IDs de participantes: possível dependência entre enunciados do mesmo autor não
pode ser auditada. Bootstrap individual não resolve essa dependência nem o viés da coleta.
A hipótese usa a mesma base explorada no TP1; obter evidência externa antes de generalizar.
Não há GPS, transação, saldo, reserva real ou fraude confirmada. Out-of-scope não foi
retido no recorte. Nenhuma conclusão sobre fraude ou localização física é sustentada.

## Próximos passos

Comparar TF-IDF + classificador linear com baseline majoritário e baseline de comprimento.
Ajustar somente em treino/validação, usar teste uma vez na avaliação final e reportar
macro-F1, recall por intenção e matriz de confusão. Confirmar o padrão de comprimentos
em amostra externa de atendimento turístico em português, incluindo multi-intenção e
out-of-scope. Fraude e spoofing exigem dados autorizados e rótulos próprios; nenhuma
previsão textual deve aprovar resgate ou substituir ownership no servidor.

Execução offline: `python eda/eda_tp2.py`. Notebook: `eda/eda_tp2.ipynb` (10 células
executadas sem erro). Figuras e resultados numéricos estão em `reports/tp2/`.
