"""Repository-specific CI evidence / required check setup using Git's credential helper."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO = "lenagomesz/tourshield-api-pb-tp1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protect", action="store_true", help="Require successful security-tests on main, including admins")
    args = parser.parse_args()
    env = {**os.environ, "GCM_INTERACTIVE": "Never", "GIT_TERMINAL_PROMPT": "0"}
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                            capture_output=True, text=True, env=env, check=True)
    credential = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)

    def api(path, data=None):
        payload = json.dumps(data).encode() if data is not None else None
        request = Request("https://api.github.com/repos/" + REPO + path, data=payload,
            method="PUT" if data is not None else "GET", headers={
                "Authorization": "Bearer " + credential["password"], "Accept": "application/vnd.github+json",
                "Content-Type": "application/json", "User-Agent": "TourShield-TP3"})
        with urlopen(request, timeout=60) as response:
            return json.load(response)

    runs = api("/actions/workflows/security-tests.yml/runs?per_page=10")["workflow_runs"]
    successful = next((r for r in runs if r["conclusion"] == "success"), None)
    if args.protect:
        if successful is None:
            raise RuntimeError("A successful security-tests workflow must exist before requiring it")
        api("/branches/main/protection", {"required_status_checks": {"strict": True, "contexts": ["security-tests"]},
            "enforce_admins": True, "required_pull_request_reviews": None, "restrictions": None,
            "allow_force_pushes": False, "allow_deletions": False})
    try:
        protection = api("/branches/main/protection")
    except HTTPError as error:
        if error.code != 404:
            raise
        protection = None
    evidence = {"repository": "https://github.com/" + REPO,
        "latest_runs": [{k: r[k] for k in ["id", "html_url", "head_sha", "event", "status", "conclusion", "created_at"]} for r in runs],
        "required_status_checks": protection.get("required_status_checks") if protection else None,
        "enforce_admins": protection.get("enforce_admins", {}).get("enabled") if protection else False,
        "allow_force_pushes": protection.get("allow_force_pushes", {}).get("enabled") if protection else None,
        "allow_deletions": protection.get("allow_deletions", {}).get("enabled") if protection else None}
    destination = ROOT / "reports/tp3/ci_evidence.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    for r in evidence["latest_runs"][:3]:
        print(r["status"], r["conclusion"], r["html_url"])
    print("required check:", evidence["required_status_checks"], "enforce_admins:", evidence["enforce_admins"])


if __name__ == "__main__":
    main()
