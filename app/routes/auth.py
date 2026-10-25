from typing import Annotated
from fastapi import APIRouter, Form, Response
from app.database import find_user
from app.models import AuthInput, Token
from app.security import DUMMY_HASH, issue_token, password_hash, unauthorized

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token, summary="Emitir JWT por credencial local",
             description="Form urlencoded username/password; JWT HS256 expira em 15 min. Cinco tentativas por IP a cada 60 s.",
             responses={401: {"description": "Credencial inválida ou conta inativa"},
                        422: {"description": "Form inválido ou campo extra"},
                        429: {"description": "Limite excedido; consulte Retry-After"}})
def token(response: Response, form: Annotated[AuthInput, Form()]):
    user = find_user(form.username)
    valid = password_hash.verify(form.password.get_secret_value(), user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.active:
        raise unauthorized()
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return Token(access_token=issue_token(user.username))
