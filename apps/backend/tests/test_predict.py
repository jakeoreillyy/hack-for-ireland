import json

import pytest
from fastapi.testclient import TestClient

from planning_predictor.config import REPO_ROOT, Settings
from planning_predictor.main import create_app

DUBLIN_CENTRE = {"lat": 53.3467, "lon": -6.2947}
CONTRACT = REPO_ROOT / "CONTRACT.md"


def post_predict(client, **overrides):
    body = {"description": "120 apartments in an 8-storey block", "council": "Dublin City Council"}
    response = client.post("/predict", json=body | overrides)
    assert response.status_code == 200, response.text
    return response.json()


def test_predict_without_location_has_no_site_comparison(client):
    body = post_predict(client)
    assert body["stats"]["n_similar"] > 0 and body["matches"]
    assert body["site_estimate"] is None and body["alternatives"] == []


def test_predict_with_pin_suggests_faster_site_to_the_west(client, settings):
    body = post_predict(client, location=DUBLIN_CENTRE)
    assert body["site_estimate"] is not None
    assert body["alternatives"], body["warnings"]
    best = body["alternatives"][0]
    assert best["weeks_saved"] > 12 and best["direction"] in {"W", "SW", "NW"}
    assert "Different council area" in " ".join(best["warnings"])
    # Alternatives never widen their radius, so their stats come from applications near them.
    assert all(a["radius_km"] == settings.site_radius_km for a in body["alternatives"])


def test_route_uses_the_settings_given_to_create_app(applications):
    settings = Settings(_env_file=None, anthropic_api_key=None, small_sample=10_000)
    with TestClient(create_app(settings, applications)) as client:
        body = post_predict(client)
    assert any(w.startswith("Small sample") for w in body["warnings"])


def test_invalid_input_is_rejected(client):
    response = client.post("/predict", json={"council": "X", "location": {"lat": 999, "lon": 0}})
    assert response.status_code == 422


def test_unknown_council_returns_empty_but_valid_response(client):
    body = post_predict(client, council="Nowhere")
    assert body["stats"]["n_similar"] == 0 and body["matches"] == []
    assert any("No applications on record for Nowhere" in w for w in body["warnings"])


def test_parsed_override_skips_the_description(client):
    body = post_predict(client, description="", parsed_override={"units": 100, "storeys": 6})
    assert (body["parsed"]["units"], body["parsed"]["storeys"]) == (100, 6)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def _contract_example(heading: str) -> dict:
    section = CONTRACT.read_text(encoding="utf-8").split(f"## {heading}", 1)[1]
    return json.loads(section.split("```json", 1)[1].split("```", 1)[0])


def _shape(value):
    """Nested key structure, so values can differ but field names cannot."""
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_shape(value[0])] if value and isinstance(value[0], dict) else []
    return None


@pytest.mark.skipif(not CONTRACT.exists(), reason="CONTRACT.md not in this checkout")
def test_response_matches_contract_field_names(client):
    body = post_predict(client, **_contract_example("Request"))
    assert body["alternatives"] and body["matches"] and len(body["delay_factors"]) == 2
    assert _shape(body) == _shape(_contract_example("Response"))
