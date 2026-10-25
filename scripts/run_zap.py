"""Real passive-only ZAP audit against disposable local HTTPS TourShield."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "zap"
TOOLS = ROOT / "tmp" / "tools"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--tp3", action="store_true", help="Audit v0.3 including self-hosted /docs")
    args = parser.parse_args()
    if args.tp3:
        OUT = ROOT / "reports" / "zap_tp3"
    run = ROOT / "tmp" / ("zap-" + secrets.token_hex(4))
    run.mkdir(parents=True)
    OUT.mkdir(parents=True, exist_ok=True)
    java = next((TOOLS / "java").glob("*/bin/java.exe"))
    jar = next((TOOLS / "zap").glob("*/zap-*.jar"))
    openssl = shutil.which("openssl") or "C:/Program Files/Git/usr/bin/openssl.exe"
    subprocess.run([openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2",
        "-keyout", str(run / "key.pem"), "-out", str(run / "cert.pem"), "-subj", "/CN=localhost",
        "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"], check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    api_port, target_port = free_port(), free_port()
    target = f"https://localhost:{target_port}"
    key = secrets.token_urlsafe(32)
    env = os.environ.copy()
    env["JWT_SECRET"] = secrets.token_urlsafe(48)
    env["DATABASE_PATH"] = str(run / "scan.sqlite3")
    os.environ.update({k: env[k] for k in ["JWT_SECRET", "DATABASE_PATH"]})
    from app.database import add_user, initialize
    from app.security import password_hash
    initialize()
    password = secrets.token_urlsafe(24)
    for name in ["scan-alice", "scan-bob"]:
        add_user(name, password_hash.hash(password))
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    processes = []
    logfiles = []
    try:
        for name, cmd, cwd in [
            ("api", [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(target_port),
                "--no-server-header", "--no-proxy-headers", "--ssl-keyfile", str(run / "key.pem"), "--ssl-certfile", str(run / "cert.pem")], ROOT),
            ("zap", [str(java), "-Xmx768m", "-jar", str(jar), "-daemon", "-silent", "-host", "127.0.0.1", "-port", str(api_port),
                "-dir", str(run / "zap-home"), "-config", "api.key=" + key,
                "-config", "api.addrs.addr.name=127.0.0.1", "-config", "api.addrs.addr.regex=false",
                "-config", "autoupdate.checkOnStart=false", "-config", "autoupdate.installAddonUpdates=false"], jar.parent)]:
            log = (run / (name + ".log")).open("wb")
            logfiles.append(log)
            processes.append(subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=log, creationflags=flags))
        zclient = httpx.Client(base_url=f"http://127.0.0.1:{api_port}", timeout=httpx.Timeout(60, connect=1), trust_env=False)

        def zap(path, **params):
            response = zclient.get(path, params={"apikey": key, **params})
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "code" in data and data["code"] != "OK":
                raise RuntimeError(str(data))
            return data

        for _ in range(180):
            if any(p.poll() is not None for p in processes):
                raise RuntimeError("A process exited; inspect " + str(run))
            try:
                version = zap("/JSON/core/view/version/")["version"]
                break
            except httpx.HTTPError:
                time.sleep(0.5)
        else:
            raise RuntimeError("ZAP startup timed out; inspect " + str(run))
        zap("/JSON/core/action/setMode/", mode="safe")
        zap("/JSON/pscan/action/setScanOnlyInScope/", onlyInScope="false")
        scanners = zap("/JSON/pscan/view/scanners/")
        print("ZAP", version, "ready; passive-only traffic to", target, flush=True)
        tokens = []
        ledger = []
        # verify=False is limited to this disposable localhost test certificate/ZAP CA.
        with httpx.Client(proxy=f"http://127.0.0.1:{api_port}", verify=False, trust_env=False, timeout=40) as client:
            def request(method, path, expected, **kwargs):
                r = client.request(method, target + path, **kwargs)
                ledger.append({"method": method, "path": path, "status": r.status_code, "expected": expected})
                if r.status_code != expected:
                    raise RuntimeError(f"{method} {path}: expected {expected}, got {r.status_code}")
                return r
            request("GET", "/health", 200)
            request("GET", "/openapi.json", 200)
            if args.tp3:
                for asset in ["/docs", "/static/swagger/swagger-ui.css", "/static/swagger/swagger-ui-bundle.js",
                              "/static/docs-init.js", "/static/docs.css"]:
                    request("GET", asset, 200)
            request("GET", "/missing", 404)
            request("POST", "/predict", 401, json={"message": "hotel request"})
            for name in ["scan-alice", "scan-bob"]:
                r = request("POST", "/auth/token", 200, data={"username": name, "password": password})
                tokens.append(r.json()["access_token"])
            alice = {"Authorization": "Bearer " + tokens[0]}
            bob = {"Authorization": "Bearer " + tokens[1]}
            request("POST", "/predict", 200, headers=alice, json={"message": "book a hotel"})
            request("POST", "/predict", 422, headers=alice, json={"message": "hotel", "admin": True})
            request("POST", "/predict", 422, headers=alice, json={"message": "hotel", "latitude": 91, "longitude": 0})
            r = request("POST", "/reservations", 201, headers=alice, json={"destination": "Recife"})
            resource = r.json()["id"]
            request("GET", "/reservations/" + resource, 200, headers=alice)
            request("GET", "/reservations/" + resource, 404, headers=bob)
            request("GET", "/reservations/" + resource, 401)
            request("POST", "/reservations", 422, headers=bob, json={"destination": "Recife", "owner": "scan-alice"})
            request("OPTIONS", "/predict", 200, headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
            request("OPTIONS", "/predict", 400, headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
            request("POST", "/auth/token", 422, data={"username": "scan-alice", "password": password, "admin": "true"})
            for _ in range(2):
                request("POST", "/auth/token", 401, data={"username": "scan-alice", "password": "invalid"})
            request("POST", "/auth/token", 429, data={"username": "scan-alice", "password": "invalid"})
        for _ in range(180):
            remaining = int(zap("/JSON/pscan/view/recordsToScan/")["recordsToScan"])
            if remaining == 0:
                time.sleep(2)
                if int(zap("/JSON/pscan/view/recordsToScan/")["recordsToScan"]) == 0:
                    break
            time.sleep(0.5)
        else:
            raise RuntimeError("Passive queue did not drain")
        alerts = zap("/JSON/core/view/alerts/", baseurl=target, start=0, count=10000)
        replacements = [password, key, *tokens]

        def redact(content):
            for value in replacements:
                content = content.replace(value, "[REDACTED_EPHEMERAL_SCAN_SECRET]")
            return content

        for endpoint, filename in [("jsonreport", "zap-report.json"), ("htmlreport", "zap-report.html")]:
            response = zclient.get(f"/OTHER/core/other/{endpoint}/", params={"apikey": key})
            response.raise_for_status()
            (OUT / filename).write_text(redact(response.text), encoding="utf-8")
        (OUT / "alerts.json").write_text(redact(json.dumps(alerts, indent=2)), encoding="utf-8")
        metadata = {"executed_at_utc": datetime.now(timezone.utc).isoformat(), "zap_version": version,
            "mode": zap("/JSON/core/view/mode/")["mode"], "target": target,
            "transport": "Local TLS, disposable self-signed certificate, ZAP intercepting proxy",
            "active_scan_executed": False, "spider_executed": False, "passive_queue_remaining": 0,
            "requests": ledger, "enabled_scanners": scanners,
            "redactions": "Only ephemeral scan passwords, bearer tokens and ZAP API key; findings unchanged",
            "alert_counts": {level: sum(a.get("risk") == level for a in alerts["alerts"]) for level in ["High", "Medium", "Low", "Informational"]}}
        (OUT / "scan-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print("Audit complete:", metadata["alert_counts"], "requests:", len(ledger), flush=True)
    finally:
        for process in reversed(processes):
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for log in logfiles:
            log.close()


if __name__ == "__main__":
    main()
