"""Builds data/applications.parquet from the national planning register.

Run once: `python data/prep.py`. Safe to re-run — it always re-fetches and
re-derives from scratch, so a bad run never leaves a half-updated table.

Source: Department of Housing, Local Government and Heritage, "Planning
Application Points" (data.gov.ie/dataset/planning-application-sites1).
See data/schema.md for the output columns and known limits, and
planning-predictor-plan.md for why the columns exist.
"""

from __future__ import annotations

import sys
import time

import pandas as pd
import requests
from pyproj import Transformer

from tag_descriptions import apply_llm_fallback, apply_regex_tags

BASE_URL = (
    "https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/"
    "IrishPlanningApplications/FeatureServer/0/query"
)

# No applicant columns requested at all — nothing to "drop" later, it's
# never pulled in the first place.
OUT_FIELDS = [
    "OBJECTID",
    "PlanningAuthority",
    "ApplicationNumber",
    "DevelopmentDescription",
    "DevelopmentAddress",
    "Decision",
    "NumResidentialUnits",
    "ReceivedDate",
    "DecisionDate",
    "FIRequestDate",
    "FIRecDate",
    "AppealSubmittedDate",
    "AppealDecisionDate",
    "LinkAppDetails",
]

PAGE_SIZE = 2000

# The service's ITMEasting/ITMNorthing *attribute* fields are empty for all
# ~508k rows (confirmed live, not a guess) — but the point geometry itself
# carries real coordinates in Web Mercator (EPSG:3857). We fetch geometry
# and reproject to Irish Transverse Mercator (EPSG:2157) ourselves. Same
# itm_easting/itm_northing columns as planned, different (working) source.
_TO_ITM = Transformer.from_crs("EPSG:3857", "EPSG:2157", always_xy=True)

# Order matters: checked top to bottom, first match wins.
_DECISION_RULES = [
    ("withdrawn", ["WITHDRAW"]),
    ("invalid", ["INVALID", "INVALIDATE"]),
    # Non-final / procedural statuses are excluded (return None), not forced
    # into one of the four buckets — they aren't a completed case.
    (None, [
        "N/A", "ADDITIONAL INFORMATION", "EXTENSION OF TIME",
        "DECISION TO BE MADE BY OTHER BODY", "S5 DEC", "DECLARED EXEMPT",
        "DECLARED NOT EXEMPT", "DECISION QUASHED", "S179A", "179A",
        "CLARIFICATION",
    ]),
    # Granted before refused: a few values contain both ("Grant Permission &
    # Refuse Retention") — treat as granted since permission was granted.
    ("granted", ["GRANT", "APPROV", "CONDITIONAL"]),
    ("refused", ["REFUSE", "REJECT"]),
]


def normalise_decision(raw: str | None) -> str | None:
    if not isinstance(raw, str):
        return None
    value = raw.strip().upper()
    if not value:
        return None
    for bucket, keywords in _DECISION_RULES:
        if any(keyword in value for keyword in keywords):
            return bucket
    return None  # unmapped — logged separately so it's never silent


def parse_esri_date(ms: float | None):
    if ms is None or pd.isna(ms):
        return None
    return pd.to_datetime(ms, unit="ms", utc=True).date()


def fetch_apartment_rows() -> pd.DataFrame:
    """Pages through the ArcGIS FeatureServer for every row whose description
    mentions "apartment". ~13,700 rows as of 2026-10-04, ~7 pages.
    """
    rows = []
    offset = 0
    while True:
        params = {
            "where": "UPPER(DevelopmentDescription) LIKE '%APARTMENT%'",
            "outFields": ",".join(OUT_FIELDS),
            "returnGeometry": "true",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            "f": "json",
        }
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise RuntimeError(f"ArcGIS query failed: {payload['error']}")

        features = payload.get("features", [])
        for feature in features:
            attrs = dict(feature["attributes"])
            geom = feature.get("geometry")
            attrs["_x"] = geom["x"] if geom else None
            attrs["_y"] = geom["y"] if geom else None
            rows.append(attrs)

        print(f"[prep] fetched {len(rows)} rows so far (offset {offset})...")
        if len(features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.1)  # be polite to a free government API

    return pd.DataFrame(rows)


def build_table(raw: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()
    df["id"] = raw["ApplicationNumber"].fillna(raw["OBJECTID"].astype(str))
    df["council"] = raw["PlanningAuthority"].str.strip()
    df["address"] = raw["DevelopmentAddress"]
    df["description"] = raw["DevelopmentDescription"]  # dropped before saving

    df["decision"] = raw["Decision"].apply(normalise_decision)

    df["received_date"] = raw["ReceivedDate"].apply(parse_esri_date)
    df["decision_date"] = raw["DecisionDate"].apply(parse_esri_date)
    df["days_to_decision"] = [
        (d - r).days if r and d and d >= r else None
        for r, d in zip(df["received_date"], df["decision_date"])
    ]

    fi_requested = raw["FIRequestDate"].apply(parse_esri_date)
    fi_received = raw["FIRecDate"].apply(parse_esri_date)
    df["fi_requested"] = fi_requested.notna()
    df["fi_added_days"] = [
        (rec - req).days if req and rec and rec >= req else None
        for req, rec in zip(fi_requested, fi_received)
    ]

    appeal_submitted = raw["AppealSubmittedDate"].apply(parse_esri_date)
    appeal_decided = raw["AppealDecisionDate"].apply(parse_esri_date)
    df["appealed"] = appeal_submitted.notna()
    df["appeal_added_days"] = [
        (dec - sub).days if sub and dec and dec >= sub else None
        for sub, dec in zip(appeal_submitted, appeal_decided)
    ]
    df["total_days"] = [
        (days + appeal) if (days is not None and appealed and appeal is not None) else days
        for days, appealed, appeal in zip(
            df["days_to_decision"], df["appealed"], df["appeal_added_days"]
        )
    ]

    df["link"] = raw["LinkAppDetails"].fillna("")

    itm = raw.apply(
        lambda r: _TO_ITM.transform(r["_x"], r["_y"]) if pd.notna(r["_x"]) else (None, None),
        axis=1,
        result_type="expand",
    )
    df["itm_easting"], df["itm_northing"] = itm[0], itm[1]

    df = apply_regex_tags(df, description_col="description")
    df = apply_llm_fallback(df, description_col="description")

    df["units"] = raw["NumResidentialUnits"]
    df["units"] = df["units"].fillna(df.pop("units_from_text"))

    df = df.drop(columns=["description"])
    column_order = [
        "id", "council", "address", "units", "storeys", "mixed_use", "decision",
        "received_date", "decision_date", "days_to_decision", "fi_requested",
        "fi_added_days", "appealed", "appeal_added_days", "link",
        "itm_easting", "itm_northing", "total_days",
    ]
    return df[column_order]


def print_report(raw: pd.DataFrame, final: pd.DataFrame) -> None:
    n_raw = len(raw)
    n_final = len(final)
    print("\n--- prep.py report ---")
    print(f"Fetched: {n_raw} apartment-mention rows")
    print(f"Excluded (non-final decision, e.g. pending/N/A): {n_raw - n_final} "
          f"({(n_raw - n_final) / n_raw:.0%})")
    print(f"Kept: {n_final} rows with a final decision\n")

    print("Decision split:")
    print(final["decision"].value_counts(normalize=True).mul(100).round(1).to_string())

    def fill_rate(col: str) -> str:
        return f"{final[col].notna().mean():.0%}"

    print("\nFill rates (of kept rows):")
    print(f"  units              {fill_rate('units')}")
    print(f"  storeys            {fill_rate('storeys')}")
    print(f"  decision_date      {fill_rate('decision_date')}")
    print(f"  days_to_decision   {fill_rate('days_to_decision')}")
    print(f"  itm coordinates    {fill_rate('itm_easting')}")
    print(f"  link               {(final['link'] != '').mean():.0%}")
    print(f"  mixed_use = True   {final['mixed_use'].mean():.0%}")
    print(f"  appealed = True    {final['appealed'].mean():.0%}")
    print("----------------------\n")


def main() -> None:
    print("[prep] fetching from the national planning register...")
    raw = fetch_apartment_rows()
    if raw.empty:
        print("[prep] got zero rows — check the API or the where clause.", file=sys.stderr)
        sys.exit(1)

    final = build_table(raw)
    final_kept = final[final["decision"].notna()].reset_index(drop=True)

    final_kept.to_parquet("data/applications.parquet", index=False)
    final_kept.to_csv("data/applications.csv", index=False)
    print(f"[prep] wrote data/applications.parquet and data/applications.csv "
          f"({len(final_kept)} rows)")

    print_report(raw, final_kept)


if __name__ == "__main__":
    main()
