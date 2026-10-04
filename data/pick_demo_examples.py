"""Scans applications.parquet for good demo candidates: councils and unit
bands with enough matches to be credible, and some variance in outcome so
the demo doesn't look scripted. Prints a ranked shortlist — run it, then
hand-pick 3 and write them up in data/demo_examples.md.

NOTE: this uses a simplified fixed-band match (no progressive widening), so
its stats will NOT match apps/backend's actual /predict output — its matcher
(services/matching.py) widens through several band tiers and is the correct
one. Use this script only to shortlist candidates; get the real numbers from
the running backend before writing them into data/demo_examples.md.

    python data/pick_demo_examples.py
"""

from __future__ import annotations

import pandas as pd

FINAL_OUTCOMES = {"granted", "refused"}  # excludes invalid/withdrawn from rate/timing stats


def match(df: pd.DataFrame, council: str, units: int, storeys: int | None, band: float = 0.3) -> pd.DataFrame:
    rows = df[df["council"] == council]
    lo, hi = units * (1 - band), units * (1 + band)
    rows = rows[(rows["units"] >= lo) & (rows["units"] <= hi)]
    if storeys is not None:
        with_storeys = rows[rows["storeys"].notna()]
        close = with_storeys[(with_storeys["storeys"] >= storeys - 1) & (with_storeys["storeys"] <= storeys + 1)]
        # only narrow by storeys if it doesn't nuke the sample
        if len(close) >= 15:
            rows = close
    return rows


def summarise(matched: pd.DataFrame) -> dict:
    decided = matched[matched["decision"].isin(FINAL_OUTCOMES)]
    n = len(decided)
    if n == 0:
        return {"n_similar": len(matched), "n_decided": 0}

    grant_rate = (decided["decision"] == "granted").mean()
    median_days = decided["days_to_decision"].median()

    fi = decided[decided["fi_requested"]]
    no_fi = decided[~decided["fi_requested"]]
    fi_added_weeks = None
    if len(fi) >= 5 and len(no_fi) >= 5:
        fi_added_weeks = round((fi["days_to_decision"].median() - no_fi["days_to_decision"].median()) / 7)

    appealed = decided[decided["appealed"]]
    not_appealed = decided[~decided["appealed"]]
    appeal_added_weeks = None
    if len(appealed) >= 5 and len(not_appealed) >= 5:
        appeal_added_weeks = round((appealed["total_days"].median() - not_appealed["total_days"].median()) / 7)

    return {
        "n_similar": len(matched),
        "n_decided": n,
        "grant_rate": round(grant_rate, 2),
        "median_weeks": round(median_days / 7, 1) if pd.notna(median_days) else None,
        "share_fi": round(decided["fi_requested"].mean(), 2),
        "share_appealed": round(decided["appealed"].mean(), 2),
        "fi_added_weeks": fi_added_weeks,
        "appeal_added_weeks": appeal_added_weeks,
    }


def top_councils(df: pd.DataFrame, n: int = 8) -> list[str]:
    return df["council"].value_counts().head(n).index.tolist()


def main() -> None:
    df = pd.read_parquet("data/applications.parquet")
    candidates = []
    for council in top_councils(df):
        for units, storeys in [(30, 3), (60, 5), (90, 6), (120, 8), (150, 10)]:
            matched = match(df, council, units, storeys)
            stats = summarise(matched)
            if stats.get("n_decided", 0) >= 20:
                candidates.append({"council": council, "units": units, "storeys": storeys, **stats})

    candidates.sort(key=lambda c: c["n_decided"], reverse=True)
    print(f"{'council':<28} {'units':>5} {'storeys':>7} {'n':>5} {'grant%':>7} {'wk':>5} {'fi_wk':>6} {'appeal_wk':>9}")
    for c in candidates[:25]:
        print(
            f"{c['council']:<28} {c['units']:>5} {c['storeys']:>7} {c['n_decided']:>5} "
            f"{c['grant_rate']*100:>6.0f}% {c['median_weeks']:>5} "
            f"{c['fi_added_weeks'] if c['fi_added_weeks'] is not None else '-':>6} "
            f"{c['appeal_added_weeks'] if c['appeal_added_weeks'] is not None else '-':>9}"
        )


if __name__ == "__main__":
    main()
