"""Exports the predictor team's applications table (hack-for-ireland data/prep.py) as
server/data/predictor-cases.json, keyed by application id, with WGS84 coordinates.
Our /api/precedents uses it to give /predict matches map pins and case details.

Run with the predictor's venv (needs pandas, pyarrow, pyproj):
  python scripts/export-predictor-cases.py <path to hack-for-ireland>/data/applications.parquet
"""
import json
import sys
from pathlib import Path

import pandas as pd
from pyproj import Transformer

src = Path(sys.argv[1])
df = pd.read_parquet(src)
to_wgs84 = Transformer.from_crs("EPSG:2157", "EPSG:4326", always_xy=True)
lon, lat = to_wgs84.transform(df["itm_easting"].to_numpy(), df["itm_northing"].to_numpy())

def iso(v):
    return None if pd.isna(v) else pd.Timestamp(v).date().isoformat()

def num(v):
    return None if pd.isna(v) else int(v)

out = {}
for i, r in enumerate(df.itertuples(index=False)):
    if pd.isna(lat[i]) or pd.isna(lon[i]):
        continue
    out[f"{r.council}|{r.id}"] = {
        "id": r.id, "authority": r.council, "location": r.address or "",
        "coordinates": [round(float(lon[i]), 6), round(float(lat[i]), 6)],
        "receivedDate": iso(r.received_date), "decisionDate": iso(r.decision_date),
        "homes": num(r.units), "storeys": num(r.storeys), "mixedUse": bool(r.mixed_use),
        "decision": (r.decision or "").lower(), "daysToDecision": num(r.days_to_decision),
        "furtherInfo": bool(r.fi_requested), "appealed": bool(r.appealed), "link": r.link or None,
    }
dest = Path(__file__).resolve().parent.parent / "server" / "data" / "predictor-cases.json"
dest.write_text(json.dumps({"exportedFrom": str(src.name), "cases": out}))
print(f"wrote {len(out)} cases to {dest}")
