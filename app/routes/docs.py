"""Self-hosted Swagger: no CDN, inline JavaScript, or persisted Bearer tokens."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/docs", include_in_schema=False, response_class=HTMLResponse)
def docs():
    return """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TourShield API - documentação OpenAPI</title>
<link rel="stylesheet" href="/static/swagger/swagger-ui.css">
<link rel="stylesheet" href="/static/docs.css"></head>
<body><header><h1>TourShield API</h1>
<p>Laboratório acadêmico. Login por formulário em /auth/token. Use Authorize para o Bearer JWT.</p>
<p>Reservas são recursos locais de teste. Predição é placeholder; GPS não autoriza benefício.</p>
<p>Limite de login: 5 requisições/IP/60s. Não informe dados pessoais reais.</p>
<a href="/openapi.json">Contrato OpenAPI JSON</a></header>
<div id="swagger-ui"></div>
<script src="/static/swagger/swagger-ui-bundle.js" defer></script>
<script src="/static/docs-init.js" defer></script></body></html>"""
