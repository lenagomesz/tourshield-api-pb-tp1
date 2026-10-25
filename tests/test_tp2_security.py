from uuid import uuid4
import pytest
from app.database import add_user
from app.middleware import HEADERS, LoginLimiter, login_limiter
from app.security import issue_token, password_hash
from tests.test_api import client, login


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_bola_owner_only(client):
    alice = login(client)
    add_user("other", password_hash.hash("other-test-password"))
    bob = issue_token("other")
    created = client.post("/reservations", headers=auth(alice), json={"destination": "Recife"})
    assert created.status_code == 201
    resource_id = created.json()["id"]
    assert client.get(f"/reservations/{resource_id}", headers=auth(alice)).status_code == 200
    denied = client.get(f"/reservations/{resource_id}", headers=auth(bob))
    absent = client.get(f"/reservations/{uuid4()}", headers=auth(bob))
    assert denied.status_code == 404 and denied.json() == absent.json()
    assert "Recife" not in denied.text


def test_resource_without_token(client):
    assert client.get(f"/reservations/{uuid4()}").status_code == 401
    assert client.post("/reservations", json={"destination": "Recife"}).status_code == 401


@pytest.mark.parametrize("route,extra", [("/predict", {"message": "hotel", "admin": True}),
    ("/reservations", {"destination": "Recife", "owner": "other"}),
    ("/reservations", {"destination": "Recife", "status": "approved"})])
def test_forbid_mass_assignment(client, route, extra):
    assert client.post(route, headers=auth(login(client)), json=extra).status_code == 422


def test_extra_login_form_forbidden(client):
    r = client.post("/auth/token", data={"username": "tester", "password": "testing-only-Password42", "admin": "true"})
    assert r.status_code == 422


@pytest.mark.parametrize("path,method", [("/health", "get"), ("/missing", "get"), ("/predict", "post")])
def test_security_headers_on_success_and_errors(client, path, method):
    r = getattr(client, method)(path)
    for header, value in HEADERS.items():
        assert r.headers[header] == value
    assert r.headers["x-request-id"]


def test_cors_allowlist(client):
    preflight = {"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "Authorization, Content-Type"}
    allowed = client.options("/predict", headers=preflight)
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    preflight["Origin"] = "https://evil.example"
    denied = client.options("/predict", headers=preflight)
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
    assert denied.headers["x-frame-options"] == "DENY"


def test_rate_limit_and_spoofed_forwarding(client):
    for _ in range(5):
        assert client.post("/auth/token", data={"username": "tester", "password": "wrong"}).status_code == 401
    r = client.post("/auth/token", headers={"X-Forwarded-For": "203.0.113.42"},
                    data={"username": "tester", "password": "testing-only-Password42"})
    assert r.status_code == 429
    assert 1 <= int(r.headers["retry-after"]) <= 61
    assert r.headers["x-content-type-options"] == "nosniff"


def test_window_recovers_without_real_sleep():
    clock = [100.0]
    limiter = LoginLimiter(clock=lambda: clock[0])
    assert all(limiter.check("ip")[0] for _ in range(5))
    assert not limiter.check("ip")[0]
    clock[0] += 61
    assert limiter.check("ip")[0]


def test_large_body_rejected_before_parsing(client):
    r = client.post("/auth/token", content=b"x" * 16385)
    assert r.status_code == 413
    assert r.headers["cache-control"] == "no-store"


def test_audit_excludes_secrets(client, caplog):
    caplog.clear()
    token = login(client)
    client.post("/predict", headers=auth(token), json={"message": "sensitive-test-message"})
    assert "http_response" in caplog.text
    for secret in [token, "testing-only-Password42", "sensitive-test-message"]:
        assert secret not in caplog.text


def test_exception_is_generic_and_logged(client, monkeypatch, caplog):
    def fail(*args, **kwargs):
        raise RuntimeError("private-database-details")
    monkeypatch.setattr("app.routes.auth.find_user", fail)
    r = client.post("/auth/token", data={"username": "tester", "password": "wrong"})
    assert r.status_code == 500 and r.json() == {"detail": "Erro interno"}
    assert "private-database-details" not in r.text
    assert r.headers["x-frame-options"] == "DENY"


def test_unknown_host_rejected(client):
    assert client.get("/health", headers={"Host": "evil.example"}).status_code == 400
