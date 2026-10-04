"""Plain-English summary built only from computed numbers, so it cannot invent figures."""

from planning_predictor.schemas import Alternative, DelayFactor, Stats

_DAYS_PER_WEEK = 7


def _to_weeks(days: int) -> int:
    return round(days / _DAYS_PER_WEEK)


def _percent(share: float) -> int:
    return round(share * 100)


def build_summary(
    stats: Stats, delay_factors: list[DelayFactor], alternatives: list[Alternative]
) -> str:
    if not stats.n_similar:
        return "No similar applications were found, so no prediction can be made."

    if stats.grant_rate is not None and stats.median_days_to_decision is not None:
        # grant_rate is over decided (granted or refused) applications, so say so: n_similar
        # also counts invalid and withdrawn ones.
        sentences = [
            f"Of {stats.n_similar} similar applications, {_percent(stats.grant_rate)}% of those "
            f"decided were granted, with a typical decision in about "
            f"{_to_weeks(stats.median_days_to_decision)} weeks."
        ]
    else:
        sentences = [f"{stats.n_similar} similar applications were found."]

    added_days = {d.factor: d.added_days for d in delay_factors}
    if "appeal" in added_days and stats.share_appealed:
        sentences.append(
            f"{_percent(stats.share_appealed)}% were appealed, which added a typical "
            f"{_to_weeks(added_days['appeal'])} weeks."
        )
    elif "further_information_request" in added_days and stats.share_further_information:
        sentences.append(
            f"{_percent(stats.share_further_information)}% needed further information, which "
            f"added a typical {_to_weeks(added_days['further_information_request'])} weeks."
        )

    if alternatives:
        best = alternatives[0]
        sentences.append(
            f"Similar applications about {best.distance_km} km {best.direction} "
            f"({best.council}) were decided about {best.weeks_saved} weeks faster; this "
            "compares past cases and does not mean a decision there would be faster."
        )
    return " ".join(sentences)
