from collections.abc import Iterator

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from planning_predictor.config import Settings
from planning_predictor.main import create_app


@pytest.fixture
def settings() -> Settings:
    # Ignore any developer .env so tests never call the real API or pick up local tunables.
    return Settings(_env_file=None, anthropic_api_key=None)


@pytest.fixture
def applications() -> pd.DataFrame:
    """Half the rows near Dublin centre (slow), half ~12 km west in South Dublin (fast)."""
    rng = np.random.default_rng(0)
    n = 300
    near_centre = rng.random(n) < 0.5
    days = np.where(near_centre, 200, 90) + rng.normal(0, 10, n)
    return pd.DataFrame(
        {
            "id": [f"A{i}" for i in range(n)],
            "council": np.where(near_centre, "Dublin City Council", "South Dublin County Council"),
            "address": "Example St",
            "units": rng.integers(80, 160, n),
            "storeys": rng.integers(6, 10, n),
            "mixed_use": True,
            "decision": rng.choice(["granted", "refused"], n, p=[0.7, 0.3]),
            "received_date": pd.Timestamp("2021-01-01"),
            "decision_date": pd.Timestamp("2021-06-01"),
            "days_to_decision": days.astype(int),
            "fi_requested": rng.random(n) < 0.3,
            "fi_added_days": 30.0,
            "appealed": rng.random(n) < 0.2,
            "appeal_added_days": 120.0,
            "link": "https://example.com",
            "itm_easting": np.where(near_centre, 715800, 703800) + rng.normal(0, 1500, n),
            "itm_northing": 734000 + rng.normal(0, 1500, n),
            "total_days": days.astype(int),
        }
    )


@pytest.fixture
def client(settings: Settings, applications: pd.DataFrame) -> Iterator[TestClient]:
    with TestClient(create_app(settings, applications)) as test_client:
        yield test_client
