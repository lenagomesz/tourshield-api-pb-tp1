from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from app.database import find_user
from app.models import Token
from app.security import DUMMY_HASH, issue_token, password_hash, unauthorized

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
def token(response: Response, form: OAuth2PasswordRequestForm = Depends()):
    if len(form.username) > 128 or len(form.password) > 1024:
        raise unauthorized()
    user = find_user(form.username)
    valid = password_hash.verify(form.password, user["password_hash"] if user else DUMMY_HASH)
    if not user or not valid or not user["active"]:
        raise unauthorized()
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return Token(access_token=issue_token(user["username"]))
