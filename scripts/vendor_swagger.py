"""Vendor pinned Swagger assets; verify npm registry SRI before extraction."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VERSION = "5.34.0"


def main():
    with urlopen(f"https://registry.npmjs.org/swagger-ui-dist/{VERSION}", timeout=60) as r:
        package = json.load(r)
    with urlopen(package["dist"]["tarball"], timeout=60) as r:
        archive = r.read()
    digest = "sha512-" + base64.b64encode(hashlib.sha512(archive).digest()).decode()
    if digest != package["dist"]["integrity"]:
        raise RuntimeError("Swagger package integrity mismatch")
    destination = ROOT / "app" / "static" / "swagger"
    destination.mkdir(parents=True, exist_ok=True)
    files = ["swagger-ui-bundle.js", "swagger-ui.css", "LICENSE", "NOTICE"]
    hashes = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for name in files:
            member = tar.extractfile("package/" + name)
            if member is None:
                raise RuntimeError("Missing vendored asset")
            data = member.read()
            (destination / name).write_bytes(data)
            hashes[name] = hashlib.sha256(data).hexdigest()
    (destination / "provenance.json").write_text(json.dumps({"package": "swagger-ui-dist", "version": VERSION,
        "url": package["dist"]["tarball"], "sri": digest, "sha256": hashes,
        "license": "Apache-2.0"}, indent=2), encoding="utf-8")
    print("Swagger assets verified:", VERSION)


if __name__ == "__main__":
    main()
