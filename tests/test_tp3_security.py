import hashlib
import json
from pathlib import Path
from app.middleware import DOCS_CSP
from tests.test_api import client, login


def test_docs_self_hosted_with_restricted_csp(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert response.headers["content-security-policy"] == DOCS_CSP
    assert "unsafe-inline" not in response.headers["content-security-policy"]
    assert "https://" not in response.text
    assert '<script src="/static/docs-init.js"' in response.text
    assert "<script>" not in response.text


def test_docs_assets_integrity_and_mime(client):
    folder = Path(__file__).resolve().parents[1] / "app/static/swagger"
    manifest = json.loads((folder / "provenance.json").read_text())
    for name in ["swagger-ui-bundle.js", "swagger-ui.css"]:
        response = client.get("/static/swagger/" + name)
        assert response.status_code == 200
        assert hashlib.sha256(response.content).hexdigest() == manifest["sha256"][name]
        assert response.headers["x-content-type-options"] == "nosniff"
    assert "persistAuthorization: false" in client.get("/static/docs-init.js").text


def test_openapi_documents_auth_and_ownership(client):
    schema = client.get("/openapi.json").json()
    assert schema["info"]["version"] == "0.3.0"
    assert schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]["password"]["tokenUrl"] == "auth/token"
    assert schema["paths"]["/reservations/{reservation_id}"]["get"]["security"]
    assert "404" in schema["paths"]["/reservations/{reservation_id}"]["get"]["responses"]
    assert "429" in schema["paths"]["/auth/token"]["post"]["responses"]
    assert schema["components"]["schemas"]["ReservationInput"]["additionalProperties"] is False


def test_authenticated_extra_field_cannot_override_status(client):
    headers = {"Authorization": "Bearer " + login(client)}
    response = client.post("/reservations", headers=headers, json={"destination": "Natal", "status": "approved"})
    assert response.status_code == 422


def test_docs_does_not_disable_authentication(client):
    assert client.get("/docs").status_code == 200
    assert client.post("/predict", json={"message": "hotel"}).status_code == 401
