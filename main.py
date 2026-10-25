"""Entrypoint: uvicorn main:app --reload."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.database import initialize
from app.config import get_secret
from app.routes import auth, health, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_secret()  # Fail closed: never start with an absent or short secret.
    initialize()
    yield


app = FastAPI(title="TourShield API", version="0.1.0", lifespan=lifespan,
              description="TP1: atendimento de turismo; predição ainda não implementada.")


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Pydantic's default errors include raw input. Avoid reflecting message/GPS/password.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "type": error["type"], "msg": "Entrada inválida"}
        for error in exc.errors()]})


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
