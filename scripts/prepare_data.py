"""Reproduce the curated derivative from a pinned upstream revision."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTENTS = ["book_flight", "book_hotel", "cancel_reservation", "confirm_reservation",
           "car_rental", "flight_status", "lost_luggage", "carry_on", "travel_alert",
           "travel_notification", "travel_suggestion", "international_visa", "vaccines",
           "plug_type", "current_location", "directions", "distance", "share_location",
           "redeem_rewards", "rewards_balance"]


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "TourShield-TP1"}), timeout=60) as result:
        return result.read()


def main():
    folder = ROOT / "data"
    (folder / "raw").mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "provenance.json"
    if manifest_path.exists():
        revision = json.loads(manifest_path.read_text(encoding="utf-8"))["revision"]
    else:
        revision = json.loads(fetch("https://api.github.com/repos/clinc/oos-eval/commits/master"))["sha"]
    base = f"https://raw.githubusercontent.com/clinc/oos-eval/{revision}"
    raw = fetch(base + "/data/data_full.json")
    (folder / "raw" / "data_full.json").write_bytes(raw)
    (folder / "LICENSE-CLINC150.txt").write_bytes(fetch(base + "/LICENSE"))
    dataset = json.loads(raw)
    # Data selection, concatenation and all cleaning/statistics use Pandas.
    all_rows = pd.concat([pd.DataFrame(dataset[split], columns=["message", "intent"])
                          .assign(split=split) for split in ["train", "val", "test"]], ignore_index=True)
    selected = all_rows.loc[all_rows["intent"].isin(INTENTS)].copy()
    selected.insert(0, "sample_id", selected.index.map(lambda i: f"clinc-{i:05d}"))
    selected.to_csv(folder / "tourshield.csv", index=False, encoding="utf-8")
    provenance = {"dataset": "CLINC150 - recorte curado TourShield (20 intenções)",
                  "authors": "Stefan Larson et al. (2019), Clinc",
                  "source": "https://github.com/clinc/oos-eval", "revision": revision,
                  "raw_url": base + "/data/data_full.json", "license": "CC BY 3.0 Unported",
                  "license_url": "https://creativecommons.org/licenses/by/3.0/",
                  "retrieved_on": "2026-10-25", "raw_sha256": hashlib.sha256(raw).hexdigest(),
                  "csv_sha256": hashlib.sha256((folder / "tourshield.csv").read_bytes()).hexdigest(),
                  "selected_intents": INTENTS, "rows": len(selected),
                  "changes": "Filtragem de 20 intenções, adição de sample_id e split; sem tradução ou novos rótulos."}
    manifest_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(provenance, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
