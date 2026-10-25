# Pergunta de classificação - TourShield (TP3)

Helena Gomes | 25/10/2026 | Documento de escopo para T2

## Definição da tarefa

**Dado um texto de atendimento ao cliente, qual é a intenção do usuário?**
Entrada: mensagem textual. Saída: exatamente um rótulo entre as 20 classes abaixo,
no escopo deste benchmark. É classificação supervisionada multiclasse de intenção única.
O objetivo é encaminhar o atendimento; o modelo não autoriza reserva ou benefício.
Exemplo de contrato futuro: texto de reserva de hotel -> book_hotel. Isso é um exemplo
semântico, não resultado de um classificador já treinado.

## Classes e distribuição

CLINC150, recorte curado TourShield: 3.000 mensagens. Cada classe tem **150 amostras
(5%)**, distribuídas em **100 treino / 20 validação / 30 teste**. Categorias são rótulos
nominais, sem ordem ou distância numérica.

| Intenção | Significado | n | % |
|---|---|---:|---:|
| book_flight | Reservar voo | 150 | 5 |
| book_hotel | Reservar hotel | 150 | 5 |
| cancel_reservation | Cancelar reserva | 150 | 5 |
| confirm_reservation | Confirmar reserva | 150 | 5 |
| car_rental | Alugar carro | 150 | 5 |
| flight_status | Consultar voo | 150 | 5 |
| lost_luggage | Bagagem perdida | 150 | 5 |
| carry_on | Bagagem de mão | 150 | 5 |
| travel_alert | Alertas de viagem | 150 | 5 |
| travel_notification | Notificar viagem | 150 | 5 |
| travel_suggestion | Sugestão de viagem | 150 | 5 |
| international_visa | Visto internacional | 150 | 5 |
| vaccines | Vacinas para viagem | 150 | 5 |
| plug_type | Tipo de tomada | 150 | 5 |
| current_location | Localização atual | 150 | 5 |
| directions | Orientações de rota | 150 | 5 |
| distance | Distância | 150 | 5 |
| share_location | Compartilhar localização | 150 | 5 |
| redeem_rewards | Resgatar recompensas | 150 | 5 |
| rewards_balance | Consultar recompensas | 150 | 5 |

## Por que aprendizado supervisionado?

Há pares mensagem/intenção rotulados, permitindo aprender associações entre palavras
e categorias e medir erros contra rótulos conhecidos. O baseline majoritário tem 5%
de acurácia em classes uniformes; acurácia sozinha não mostra quais intenções se confundem.
Usar macro-F1, recall por classe e matriz de confusão. Preservar os splits 2.000/400/600.

## Por que a regressão linear não resolve a pergunta?

A regressão deste TP estima **quantidade de palavras**, uma variável numérica, com
R²/RMSE. Intenções não são quantidades: codificá-las 0-19 inventaria uma ordem e uma
distância sem significado, e a previsão poderia ser fracionária ou fora do conjunto.
R² alto para comprimento não mede acerto de intenção. Regressão logística, apesar do
nome, é um classificador: aprende escores/probabilidades por classe, adequados ao problema.

## Limites de uso

Textos em inglês, de crowdsourcing e intenção única. O balanceamento não representa
demanda operacional. Recompensas são genéricas, não necessariamente de turismo. Não
há GPS, fraude confirmada ou múltiplas intenções; out-of-scope foi excluído do recorte.
Produção em português e rejeição de intenção desconhecida exigem base adicional e
validação própria. Classificação não comprova localização, titularidade ou elegibilidade.

Fonte: Stefan Larson et al. (2019), CLINC150, https://github.com/clinc/oos-eval,
CC BY 3.0; proveniência em data/provenance.json. Distribuição verificável em
reports/category_distribution.csv e reports/split_distribution.csv.
