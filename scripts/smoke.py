"""Exercise actual uvicorn over loopback with temporary secret and database."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory() as folder:
        env = os.environ.copy()
        env["JWT_SECRET"] = secrets.token_urlsafe(48)
        env["DATABASE_PATH"] = str(Path(folder) / "smoke.sqlite3")
        os.environ.update({k: env[k] for k in ["JWT_SECRET", "DATABASE_PATH"]})
        from app.database import add_user, engine_for, initialize
        from app.security import password_hash
        initialize()
        password = secrets.token_urlsafe(24)
        add_user("smoke", password_hash.hash(password))
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--no-proxy-headers", "--no-server-header", "--host", "127.0.0.1", "--port", str(port)],
                                   cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}") as client:
                for _ in range(100):
                    try:
                        health = client.get("/health")
                        if health.status_code == 200:
                            break
                    except httpx.ConnectError:
                        pass
                    time.sleep(0.1)
                else:
                    raise RuntimeError("uvicorn did not start")
                no_token = client.post("/predict", json={"message": "Book hotel"})
                auth = client.post("/auth/token", data={"username": "smoke", "password": password})
                authenticated = client.post("/predict", json={"message": "Book hotel"},
                    headers={"Authorization": "Bearer " + auth.json()["access_token"]})
                assert [health.status_code, no_token.status_code, auth.status_code, authenticated.status_code] == [200, 401, 200, 200]
                result = {"transport": "HTTP loopback, actual uvicorn process", "health": health.status_code,
                          "predict_without_token": no_token.status_code, "auth_token": auth.status_code,
                          "predict_with_token": authenticated.status_code, "prediction": authenticated.json(),
                          "secrets": "temporary, not saved"}
                (ROOT / "reports" / "smoke.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
                print(json.dumps(result, ensure_ascii=False))
        finally:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                process.terminate()
            process.wait(timeout=10)
            engine_for(env["DATABASE_PATH"]).dispose()


if __name__ == "__main__":
    main()
