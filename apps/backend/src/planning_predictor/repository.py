"""Load the applications table (schema: data/schema.md)."""

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = frozenset(
    {
        "id",
        "council",
        "address",
        "units",
        "storeys",
        "mixed_use",
        "decision",
        "received_date",
        "decision_date",
        "days_to_decision",
        "fi_requested",
        "fi_added_days",
        "appealed",
        "appeal_added_days",
        "link",
        "itm_easting",
        "itm_northing",
        "total_days",
    }
)
# Used as row masks, so they must be plain bool (not 0/1 or nullable) or filtering breaks.
FLAG_COLUMNS = ("mixed_use", "fi_requested", "appealed")


def load_applications(data_dir: Path) -> pd.DataFrame:
    """Read applications.parquet if present, else fake_sample.csv; validate and normalise."""
    parquet, csv = data_dir / "applications.parquet", data_dir / "fake_sample.csv"
    if parquet.exists():
        df = pd.read_parquet(parquet)
    elif csv.exists():
        df = pd.read_csv(csv, parse_dates=["received_date", "decision_date"])
    else:
        raise FileNotFoundError(f"Neither applications.parquet nor fake_sample.csv in {data_dir}")
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Applications data is missing columns: {sorted(missing)}")
    df["decision"] = df["decision"].str.lower()
    for column in FLAG_COLUMNS:
        try:
            df[column] = df[column].astype("boolean").fillna(False).astype(bool)
        except TypeError as error:
            raise ValueError(f"Column {column!r} must hold true/false values") from error
    return df
