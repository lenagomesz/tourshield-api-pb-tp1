from datetime import datetime, timedelta, timezone
import secrets
import jwt
import pytest
from fastapi.testclient import TestClient
from app.config import AUDIENCE, ISSUER
from app.database import User, add_user, connect, engine_for
from app.middleware import login_limiter
from app.security import password_hash
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", secrets.token_urlsafe(48))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.sqlite3"))
    login_limiter.reset()
    with TestClient(app) as c:
        add_user("tester", password_hash.hash("testing-only-Password42"))
        yield c
    engine_for(str(tmp_path / "test.sqlite3")).dispose()


def login(client):
    response = client.post("/auth/token", data={"username": "tester", "password": "testing-only-Password42"})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    return response.json()["access_token"]


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_no_token(client):
    response = client.post("/predict", json={"message": "book hotel"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("username,password", [("tester", "wrong"), ("unknown", "wrong"),
                                                 ("' OR 1=1 --", "wrong")])
def test_wrong_credentials(client, username, password):
    assert client.post("/auth/token", data={"username": username, "password": password}).status_code == 401


def test_authorized_placeholder(client):
    token = login(client)
    r = client.post("/predict", headers={"Authorization": f"Bearer {token}"},
                    json={"message": "Quero reservar hotel", "latitude": -22.9, "longitude": -43.2})
    assert r.status_code == 200
    assert r.json()["intent"] is None and r.json()["status"] == "placeholder"
    assert "latitude" not in r.json() and "message" not in r.json()


@pytest.mark.parametrize("variant", ["expired", "wrong_signature", "wrong_audience", "wrong_issuer",
                                    "missing_exp", "missing_sub", "future_iat", "unknown_user", "algorithm"])
def test_rejected_jwt(client, monkeypatch, variant):
    import os
    now = datetime.now(timezone.utc)
    claims = {"sub": "tester", "exp": now + timedelta(minutes=15), "iat": now,
              "aud": AUDIENCE, "iss": ISSUER}
    secret = os.environ["JWT_SECRET"]
    algorithm = "HS256"
    if variant == "expired": claims["exp"] = now - timedelta(seconds=1)
    if variant == "wrong_signature": secret = secrets.token_urlsafe(48)
    if variant == "wrong_audience": claims["aud"] = "other"
    if variant == "wrong_issuer": claims["iss"] = "other"
    if variant == "missing_exp": claims.pop("exp")
    if variant == "missing_sub": claims.pop("sub")
    if variant == "future_iat": claims["iat"] = now + timedelta(days=1)
    if variant == "unknown_user": claims["sub"] = "missing"
    if variant == "algorithm": algorithm = "HS384"
    token = jwt.encode(claims, secret, algorithm=algorithm)
    assert client.post("/predict", json={"message": "test"},
                       headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_disabled_user(client):
    token = login(client)
    with connect() as db:
        user = db.get(User, "tester")
        user.active = False
        db.add(user)
        db.commit()
    assert client.post("/predict", json={"message": "test"},
                       headers={"Authorization": f"Bearer {token}"}).status_code == 401
    assert client.post("/auth/token", data={"username": "tester", "password": "testing-only-Password42"}).status_code == 401


@pytest.mark.parametrize("body", [{"message": " "}, {"message": "x" * 4001},
    {"message": "ok", "latitude": 91, "longitude": 0}, {"message": "ok", "latitude": 0},
    {"message": "ok", "longitude": 181, "latitude": 0}, {"message": "ok", "benefit_approved": True},
    {"message": "ok", "latitude": "NaN", "longitude": 0}])
def test_input_validation(client, body):
    token = login(client)
    assert client.post("/predict", json=body, headers={"Authorization": f"Bearer {token}"}).status_code == 422


def test_missing_secret_fails_closed(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "")
    with pytest.raises(RuntimeError):
        with TestClient(app):
            pass


def test_hash_is_argon2(client):
    with connect() as db:
        value = db.get(User, "tester").password_hash
    assert value.startswith("$argon2id$")
    assert "testing-only" not in value


def test_validation_does_not_echo_input(client):
    token = login(client)
    private_text = "private-message-" * 300
    response = client.post("/predict", json={"message": private_text},
                           headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert "private-message" not in response.text
    assert "input" not in response.text
