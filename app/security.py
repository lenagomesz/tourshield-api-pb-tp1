from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from app.config import AUDIENCE, ISSUER, TOKEN_MINUTES, get_secret
from app.database import find_user

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummy-not-a-login-credential")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def unauthorized():
    return HTTPException(status_code=401, detail="Credenciais inválidas ou expiradas",
                         headers={"WWW-Authenticate": "Bearer"})


def issue_token(username: str):
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": username, "iat": now, "exp": now + timedelta(minutes=TOKEN_MINUTES),
                       "iss": ISSUER, "aud": AUDIENCE}, get_secret(), algorithm="HS256")


def current_user(token: str = Depends(oauth2_scheme)):
    try:
        claims = jwt.decode(token, get_secret(), algorithms=["HS256"], audience=AUDIENCE,
                            issuer=ISSUER, options={"require": ["sub", "exp", "iat", "iss", "aud"]})
        if not isinstance(claims["sub"], str) or not claims["sub"]:
            raise unauthorized()
    except jwt.InvalidTokenError:
        raise unauthorized()
    user = find_user(claims["sub"])
    if user is None or not user["active"]:
        raise unauthorized()
    return user["username"]
