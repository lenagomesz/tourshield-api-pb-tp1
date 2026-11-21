# Entrega TP4 - aplicação e testes funcionais
Integrantes: **Helena Gomes e Maria Paula**.

- PDF: output/pdf/helena_gomes_PB_TP4.PDF.
- Notebook: eda/classification_tp4.ipynb, executado, com dados locais em data/.
- Fonte e reprodução: eda/classification_tp4.py e scripts/build_classification_notebook.py.
- Pipeline serializado: models/intent_classifier.joblib, manifest.json.
- FastAPI: main.py, app/routes/classify.py, app/classifier.py, app/models.py.
- Agente: app/agent.py; demonstração: scripts/demo_agent_tp4.py.
- Evidência da conversa: reports/tp4/agent_conversation.md e .json.
- API HTTP: reports/tp4/functional_api.json.
- Testes: tests/test_tp4.py e reports/tests_tp4.xml.
- Métricas: reports/tp4/metrics.csv, metrics_by_class.csv, grid_search.csv, figuras e summary.

Repositório de continuidade: https://github.com/lenagomesz/tourshield-api-pb-tp1.
O relatório identifica a referência da branch de entrega. A main histórica permanece
protegida; atualização para revisão não implica merge sem o check exigido.

Limitação: o modo com modelo OpenAI remoto depende de chave e nome de modelo do
operador. A conversa entregue executa o SDK real e a API real, com geração simulada.
A avaliação de segurança fica fora do escopo atual, conforme a solicitação mais recente.
