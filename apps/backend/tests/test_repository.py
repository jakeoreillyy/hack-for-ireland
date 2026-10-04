import numpy as np
import pytest

from planning_predictor.config import REPO_ROOT
from planning_predictor.repository import FLAG_COLUMNS, load_applications

SHARED_DATA = REPO_ROOT / "data"


@pytest.mark.skipif(
    not (SHARED_DATA / "fake_sample.csv").exists(), reason="data/fake_sample.csv not committed"
)
def test_shared_data_matches_the_schema():
    df = load_applications(SHARED_DATA)
    assert set(df["decision"]) <= {"granted", "refused", "invalid", "withdrawn"}
    assert all(df[column].dtype == bool for column in FLAG_COLUMNS)


def test_flags_given_as_0_1_or_blank_become_bool(applications, tmp_path):
    applications["fi_requested"] = applications["fi_requested"].astype(int)
    applications["appealed"] = np.where(applications["appealed"], 1.0, np.nan)
    applications.to_csv(tmp_path / "fake_sample.csv", index=False)
    df = load_applications(tmp_path)
    assert df["fi_requested"].dtype == bool and df["appealed"].dtype == bool
    assert df["appealed"].sum() == applications["appealed"].notna().sum()


def test_non_boolean_flags_are_rejected(applications, tmp_path):
    applications["appealed"] = "yes"
    applications.to_csv(tmp_path / "fake_sample.csv", index=False)
    with pytest.raises(ValueError, match="appealed"):
        load_applications(tmp_path)


def test_parquet_is_preferred_over_csv(applications, tmp_path):
    applications.head(5).to_csv(tmp_path / "fake_sample.csv", index=False)
    applications.to_parquet(tmp_path / "applications.parquet")
    assert len(load_applications(tmp_path)) == len(applications)


def test_missing_columns_are_reported(applications, tmp_path):
    applications.drop(columns=["total_days"]).to_csv(tmp_path / "fake_sample.csv", index=False)
    with pytest.raises(ValueError, match="total_days"):
        load_applications(tmp_path)


def test_missing_data_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_applications(tmp_path)
