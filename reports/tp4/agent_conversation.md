# TourShield - conversa demonstrativa (três turnos)

Helena Gomes e Maria Paula | 21/11/2026

Agent, Runner.run, @function_tool e API HTTP executados. Geração de resposta simulada por modelo determinístico; não é conversa com LLM OpenAI remoto.

## Turno 1

**Usuário:** I would like to book a hotel in Lisbon

**TourShield:** Intenção: book_hotel; probabilidade estimada: 88.4%. Posso encaminhar sua solicitação. Nenhuma reserva ou benefício foi autorizado.

**Ferramenta /classify:** `{"intent": "book_hotel", "probability": 0.884465593118022, "model_version": "tourshield-intents-tp4-v1"}`

## Turno 2

**Usuário:** What is my rewards balance?

**TourShield:** Intenção: rewards_balance; probabilidade estimada: 98.3%. Posso encaminhar sua solicitação. Nenhuma reserva ou benefício foi autorizado.

**Ferramenta /classify:** `{"intent": "rewards_balance", "probability": 0.9831376376541758, "model_version": "tourshield-intents-tp4-v1"}`

## Turno 3

**Usuário:** Please cancel my reservation

**TourShield:** Intenção: cancel_reservation; probabilidade estimada: 99.9%. Posso encaminhar sua solicitação. Nenhuma reserva ou benefício foi autorizado.

**Ferramenta /classify:** `{"intent": "cancel_reservation", "probability": 0.9992906093659709, "model_version": "tourshield-intents-tp4-v1"}`
