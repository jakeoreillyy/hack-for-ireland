"""End-to-end against the real data/fake_sample.csv."""

import shutil

import pytest
from fastapi.testclient import TestClient

from planning_predictor.config import REPO_ROOT, Settings
from planning_predictor.main import create_app

SAMPLE = REPO_ROOT / "data" / "fake_sample.csv"
DUBLIN_CENTRE = {"lat": 53.3467, "lon": -6.2947}

pytestmark = pytest.mark.skipif(not SAMPLE.exists(), reason="data/fake_sample.csv not present")


@pytest.fixture
def sample_client(tmp_path):
    shutil.copy(SAMPLE, tmp_path)  # the CSV alone: a local applications.parquet would win
    settings = Settings(_env_file=None, anthropic_api_key=None, data_dir=tmp_path)
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.mark.parametrize(
    "council",
    ["Dublin City Council", "South Dublin County Council", "Cork City Council", "Nowhere"],
)
def test_every_council_gets_a_valid_response_with_a_pin(sample_client, council):
    response = sample_client.post(
        "/predict",
        json={"description": "100 apartments", "council": council, "location": DUBLIN_CENTRE},
    )
    assert response.status_code == 200, response.text
    assert response.json()["summary"]


def test_missing_storeys_and_decision_date_come_back_as_null(sample_client):
    body = sample_client.post(
        "/predict", json={"description": "", "council": "Cork City Council"}
    ).json()
    assert body["stats"]["n_similar"] == 2
    assert {(m["storeys"], m["decision_date"]) for m in body["matches"]} == {
        (None, None),  # the withdrawn application
        (8, "2021-09-02"),
    }
