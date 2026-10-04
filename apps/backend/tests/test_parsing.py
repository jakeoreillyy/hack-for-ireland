import sys
from types import SimpleNamespace

import pytest

from planning_predictor.schemas import ProjectSpec
from planning_predictor.services import parsing


def test_regex_extracts_units_storeys_and_mixed_use():
    spec = parsing.parse_with_regex("120 apartments in an 8-storey block with ground-floor retail")
    assert (spec.units, spec.storeys, spec.mixed_use) == (120, 8, True)


def test_regex_reads_number_words():
    assert parsing.parse_with_regex("an eight storey scheme").storeys == 8


def test_regex_prefers_the_new_building_over_what_it_replaces():
    spec = parsing.parse_with_regex("demolition of 2 houses and construction of 120 apartments")
    assert spec.units == 120


def test_regex_ignores_numbers_that_are_out_of_range_or_part_of_another_number():
    spec = parsing.parse_with_regex("1200 floor area, 9000 units of storage, 8 storey block")
    assert (spec.units, spec.storeys) == (None, 8)


@pytest.mark.parametrize(
    ("text", "mixed_use"),
    [
        ("apartments over a café", True),
        ("next to a shopping centre", True),
        ("Mixed-use scheme", True),
        ("ground floor apartments", False),
        ("apartments and a bike workshop", False),
    ],
)
def test_regex_mixed_use_needs_a_whole_non_residential_word(text, mixed_use):
    assert parsing.parse_with_regex(text).mixed_use is mixed_use


def test_override_skips_parsing(settings):
    override = ProjectSpec(units=50, storeys=4)
    spec, warnings = parsing.parse_description("ignored", override, settings)
    assert spec == override and warnings == []


def test_missing_units_warns(settings):
    _, warnings = parsing.parse_description("a nice building", None, settings)
    assert any("number of units" in w for w in warnings)


def _fake_llm(monkeypatch, result):
    calls = []

    def fake(text, _settings):
        calls.append(text)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(parsing, "parse_with_llm", fake)
    return calls


def test_llm_failure_falls_back_to_regex(settings, monkeypatch):
    settings.anthropic_api_key = "test"
    _fake_llm(monkeypatch, RuntimeError("api down"))
    spec, warnings = parsing.parse_description("120 apartments", None, settings)
    assert spec.units == 120
    assert any("unavailable" in w for w in warnings)


def test_llm_values_win_when_it_runs(settings, monkeypatch):
    settings.anthropic_api_key = "test"
    _fake_llm(monkeypatch, ProjectSpec(units=120, storeys=None, mixed_use=False))
    spec, warnings = parsing.parse_description("4 blocks of 30 apartments", None, settings)
    assert (spec.units, spec.storeys) == (120, None) and warnings == []


def test_llm_can_overrule_a_regex_mixed_use_match(settings, monkeypatch):
    settings.anthropic_api_key = "test"
    _fake_llm(monkeypatch, ProjectSpec(units=18, mixed_use=False))
    text = "Change of use of offices to 18 residential units"  # regex sees "offices"
    spec, _ = parsing.parse_description(text, None, settings)
    assert spec.mixed_use is False


@pytest.mark.parametrize("description", ["120 apartments in an 8 storey block", "   "])
def test_llm_is_skipped_when_regex_is_complete_or_text_is_blank(settings, monkeypatch, description):
    settings.anthropic_api_key = "test"
    calls = _fake_llm(monkeypatch, RuntimeError("should not be called"))
    parsing.parse_description(description, None, settings)
    assert calls == []


def _fake_claude(monkeypatch, stop_reason="end_turn", answer=""):
    """Stand in for the anthropic SDK and record each request sent to it."""
    requests = []

    class FakeAnthropic:
        def __init__(self, **_options):
            self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

        def create(self, **request):
            requests.append(request)
            content = [
                SimpleNamespace(type="thinking", thinking=""),
                SimpleNamespace(type="text", text=answer),
            ]
            return SimpleNamespace(stop_reason=stop_reason, content=content)

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropic))
    return requests


def test_llm_asks_claude_for_json_matching_the_schema(settings, monkeypatch):
    settings.anthropic_api_key = "test"
    answer = '{"units": 120, "storeys": 8, "mixed_use": true}'
    requests = _fake_claude(monkeypatch, answer=answer)
    spec = parsing.parse_with_llm("an eight storey block of 120 flats", settings)
    assert (spec.units, spec.storeys, spec.mixed_use) == (120, 8, True)
    (request,) = requests
    assert request["model"] == settings.anthropic_model
    assert request["output_config"]["format"]["schema"] == parsing.LLM_JSON_SCHEMA


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_llm_rejects_an_incomplete_answer(settings, monkeypatch, stop_reason):
    _fake_claude(monkeypatch, stop_reason=stop_reason, answer='{"units": 1')
    with pytest.raises(RuntimeError, match=stop_reason):
        parsing.parse_with_llm("120 apartments", settings)


@pytest.mark.parametrize("raw", [{"units": 10**9, "storeys": -3, "mixed_use": 1}])
def test_sanitise_drops_out_of_range_values(raw):
    spec = parsing._sanitise(raw)
    assert (spec.units, spec.storeys, spec.mixed_use) == (None, None, True)
