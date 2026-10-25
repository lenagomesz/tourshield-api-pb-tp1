"""Entrypoint: uvicorn main:app --reload."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.middleware import WebSecurity
import os
from urllib.parse import urlsplit
from app.database import initialize
from app.config import get_secret
from app.routes import auth, health, predict, reservations


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_secret()  # Fail closed: never start with an absent or short secret.
    initialize()
    yield


app = FastAPI(title="TourShield API", version="0.2.0", lifespan=lifespan,
              docs_url=None, redoc_url=None, debug=False,
              description="TP2: atendimento de turismo com controles OWASP; sem modelo de ML.")
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
