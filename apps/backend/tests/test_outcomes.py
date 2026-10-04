from helpers import applications_table, repeated
from planning_predictor.services.matching import summarise_outcomes


def test_invalid_and_withdrawn_do_not_count_towards_rate_or_timing(settings):
    table = applications_table(
        *repeated(3, decision="granted", days_to_decision=100),
        *repeated(1, decision="refused", days_to_decision=200),
        *repeated(5, decision="invalid", days_to_decision=5),
        *repeated(5, decision="withdrawn", days_to_decision=7),
    )
    stats, _, _ = summarise_outcomes(table, settings)
    assert stats.n_similar == 14
    assert stats.grant_rate == 0.75
    assert stats.median_days_to_decision == 100


def test_nothing_decided_gives_no_rate_or_timing(settings):
    table = applications_table(*repeated(3, decision="withdrawn"))
    stats, _, _ = summarise_outcomes(table, settings)
    assert stats.n_similar == 3
    assert stats.grant_rate is None and stats.median_days_to_decision is None


def test_small_sample_warns_only_below_the_threshold(settings):
    below = applications_table(*repeated(settings.small_sample - 1))
    at_threshold = applications_table(*repeated(settings.small_sample))
    assert any("Small sample" in w for w in summarise_outcomes(below, settings)[2])
    assert not summarise_outcomes(at_threshold, settings)[2]


def test_delay_factors_are_the_median_days_added_among_those_delayed(settings):
    table = applications_table(
        {"fi_requested": True, "fi_added_days": 20.0},
        {"fi_requested": True, "fi_added_days": 40.0},
        {"fi_requested": True, "fi_added_days": 90.0},
        {"fi_requested": False, "fi_added_days": 0.0},  # not delayed, so must not count
        {"appealed": True, "appeal_added_days": 150.0},
    )
    stats, delay_factors, _ = summarise_outcomes(table, settings)
    assert {d.factor: d.added_days for d in delay_factors} == {
        "further_information_request": 40,
        "appeal": 150,
    }
    assert stats.share_further_information == 0.6 and stats.share_appealed == 0.2


def test_no_delay_factor_when_nothing_was_delayed_or_the_days_are_unknown(settings):
    table = applications_table(
        {"fi_requested": True, "fi_added_days": None},  # flagged but no duration recorded
        {"appealed": False},
    )
    _, delay_factors, _ = summarise_outcomes(table, settings)
    assert delay_factors == []
