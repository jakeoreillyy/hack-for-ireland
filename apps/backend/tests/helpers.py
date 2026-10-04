"""Builders for small, hand-made applications tables."""

import numpy as np
import pandas as pd

DEFAULTS = {
    "council": "Dublin City Council",
    "address": "Example St",
    "units": 100,
    "storeys": 8,
    "mixed_use": False,
    "decision": "granted",
    "received_date": pd.Timestamp("2021-01-01"),
    "decision_date": pd.Timestamp("2021-06-01"),
    "days_to_decision": 100,
    "fi_requested": False,
    "fi_added_days": np.nan,
    "appealed": False,
    "appeal_added_days": np.nan,
    "link": "https://example.com",
    "itm_easting": 715800.0,
    "itm_northing": 734000.0,
    "total_days": 100,
}


def applications_table(*rows: dict) -> pd.DataFrame:
    """One row per dict; unspecified columns take DEFAULTS and ids are numbered."""
    table = pd.DataFrame([{**DEFAULTS, **row} for row in rows])
    table["id"] = [f"A{i}" for i in range(len(table))]
    return table


def repeated(count: int, **fields) -> list[dict]:
    return [fields] * count
