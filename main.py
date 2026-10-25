"""Entrypoint: uvicorn main:app --reload."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.middleware import WebSecurity
import os
from urllib.parse import urlsplit
from app.database import initialize
from app.config import get_secret
from app.routes import auth, health, predict, reservations, docs


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_secret()  # Fail closed: never start with an absent or short secret.
    initialize()
    yield


app = FastAPI(title="TourShield API", version="0.3.0", lifespan=lifespan,
              docs_url=None, redoc_url=None, debug=False,
              description="""Atendimento turístico - TP3. Autentique com username/password em /auth/token.
O JWT Bearer dura 15 minutos; login tem limite de 5 requisições/IP/60s.
/predict é placeholder. Reservas são recursos locais de laboratório, nunca compras reais.
O proprietário é obtido do token e não pode ser escolhido pelo cliente.
Coordenadas são declaradas pelo cliente e não comprovam presença ou elegibilidade.""",
              openapi_tags=[{"name": "health", "description": "Sonda de vida pública, sem detalhes internos."},
                            {"name": "auth", "description": "OAuth2 password + JWT; 401/422/429 em falhas."},
                            {"name": "predict", "description": "Entrada validada e autenticada, sem modelo treinado."},
                            {"name": "reservations", "description": "Recursos de teste com ownership por usuário."}])
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if x.strip()]
for origin in origins:
    parsed = urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path or "*" in origin:
        raise RuntimeError("CORS_ORIGINS deve conter origens explícitas sem caminho ou wildcard")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
app.add_middleware(WebSecurity)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Pydantic's default errors include raw input. Avoid reflecting message/GPS/password.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "type": error["type"], "msg": "Entrada inválida"}
        for error in exc.errors()]})


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(reservations.router)
app.include_router(docs.router)
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "app" / "static"), name="static")
