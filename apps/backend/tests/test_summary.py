from planning_predictor.schemas import DelayFactor, Stats
from planning_predictor.services.summary import build_summary


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


def test_no_matches_gives_no_prediction():
    stats = Stats(
        n_similar=0,
        grant_rate=None,
        median_days_to_decision=None,
        share_further_information=None,
        share_appealed=None,
    )
    assert "no prediction" in build_summary(stats, [], [])
