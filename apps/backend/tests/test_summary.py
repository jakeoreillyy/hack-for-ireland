from planning_predictor.schemas import Alternative, DelayFactor, Stats
from planning_predictor.services.summary import build_summary


def make_stats(**overrides) -> Stats:
    fields = {
        "n_similar": 40,
        "grant_rate": 0.7,
        "median_days_to_decision": 98,
        "share_further_information": 0.35,
        "share_appealed": 0.2,
    }
    return Stats(**(fields | overrides))


def make_alternative() -> Alternative:
    return Alternative(
        label="12 km W, South Dublin County Council",
        council="South Dublin County Council",
        lat=53.32,
        lon=-6.39,
        distance_km=12,
        direction="W",
        radius_km=3.0,
        n_similar=27,
        median_total_days=364,
        grant_rate=0.72,
        weeks_saved=52,
    )


def test_grant_rate_is_described_as_a_share_of_decided_applications():
    # 1 granted + 1 withdrawn: "100% were granted" alone would be false.
    stats = Stats(
        n_similar=2,
        grant_rate=1.0,
        median_days_to_decision=240,
        share_further_information=0.5,
        share_appealed=0.0,
    )
    summary = build_summary(
        stats, [DelayFactor(factor="further_information_request", added_days=98)], []
    )
    assert summary.startswith("Of 2 similar applications, 100% of those decided were granted")
    assert "about 34 weeks" in summary and "added a typical 14 weeks" in summary


def test_headline_numbers_are_rounded_to_percent_and_weeks():
    # 66.7% and 14.6 weeks: truncating instead of rounding would give 66% and 14.
    summary = build_summary(make_stats(grant_rate=2 / 3, median_days_to_decision=102), [], [])
    assert "67% of those decided were granted" in summary and "about 15 weeks" in summary


def test_appeal_is_mentioned_in_preference_to_further_information():
    delays = [
        DelayFactor(factor="further_information_request", added_days=28),
        DelayFactor(factor="appeal", added_days=140),
    ]
    summary = build_summary(make_stats(), delays, [])
    assert "20% were appealed" in summary and "20 weeks" in summary
    assert "further information" not in summary


def test_no_delay_sentence_when_the_share_is_zero():
    delays = [DelayFactor(factor="appeal", added_days=140)]
    summary = build_summary(make_stats(share_appealed=0.0), delays, [])
    assert "appealed" not in summary


def test_without_a_rate_it_only_reports_the_count():
    summary = build_summary(make_stats(grant_rate=None), [], [])
    assert summary.startswith("40 similar applications were found.")


def test_faster_site_is_framed_as_past_cases_not_a_promise():
    summary = build_summary(make_stats(), [], [make_alternative()])
    assert "12 km W" in summary and "52 weeks faster" in summary
    assert "does not mean a decision there would be faster" in summary


def test_no_matches_gives_no_prediction():
    stats = Stats(
        n_similar=0,
        grant_rate=None,
        median_days_to_decision=None,
        share_further_information=None,
        share_appealed=None,
    )
    assert "no prediction" in build_summary(stats, [], [])
