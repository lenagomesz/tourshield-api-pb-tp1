"""Download portable ZAP and Java to a local ignored tools folder (Windows)."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tmp" / "tools"


def get(url):
    return urlopen(Request(url, headers={"User-Agent": "TourShield-TP2"}), timeout=120)


def download(name, url, expected):
    archive = TOOLS / (name + ".zip")
    if not archive.exists():
        with get(url) as source, archive.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if expected and digest != expected.removeprefix("sha256:"):
        raise RuntimeError(f"Checksum mismatch for {name}")
    dest = TOOLS / name
    if not dest.exists():
        with zipfile.ZipFile(archive) as z:
            for entry in z.namelist():
                if not (dest / entry).resolve().is_relative_to(dest.resolve()):
                    raise RuntimeError("Archive traversal")
            z.extractall(dest)
    return {"name": name, "url": url, "sha256": digest, "expected_digest_available": bool(expected)}


def main():
    TOOLS.mkdir(parents=True, exist_ok=True)
    with get("https://api.github.com/repos/zaproxy/zaproxy/releases/tags/v2.17.0") as r:
        release = json.load(r)
    asset = next(a for a in release["assets"] if a["name"] == "ZAP_2.17.0_Crossplatform.zip")
    with get("https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jre&os=windows") as r:
        java = json.load(r)[0]["binary"]["package"]
    with ThreadPoolExecutor(2) as pool:
        jobs = [pool.submit(download, "zap", asset["browser_download_url"], asset.get("digest")),
                pool.submit(download, "java", java["link"], java["checksum"])]
        results = [job.result() for job in jobs]
    (ROOT / "reports" / "zap").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "zap" / "tool_provenance.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("ZAP/Java ready", json.dumps(results))


if __name__ == "__main__":
    main()
