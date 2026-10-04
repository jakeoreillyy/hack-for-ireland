"""Find similar past applications and aggregate what happened to them."""

import pandas as pd

from planning_predictor.config import Settings
from planning_predictor.geo import ITM_TO_WGS84
from planning_predictor.schemas import DelayFactor, Match, ProjectSpec, Stats

DECIDED_OUTCOMES = ("granted", "refused")  # outcomes that count for rates and timings


def find_similar_applications(
    applications: pd.DataFrame,
    spec: ProjectSpec,
    settings: Settings,
    council: str | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Filter to similar applications, widening size bands until enough are found.

    `council=None` searches every council (used for the site comparison).
    """
    pool = applications if council is None else applications[applications["council"] == council]
    if council is not None and pool.empty:
        return pool, [f"No applications on record for {council}; check the council name."]
    if not (spec.units or spec.storeys):
        return pool, []  # no size to match on

    result, widened = pool, False
    for units_tolerance, storeys_tolerance in settings.size_bands:
        mask = pd.Series(True, index=pool.index)
        if spec.units:
            mask &= pool["units"].between(
                spec.units * (1 - units_tolerance), spec.units * (1 + units_tolerance)
            )
        if spec.storeys and storeys_tolerance is not None:
            mask &= pool["storeys"].between(
                spec.storeys - storeys_tolerance, spec.storeys + storeys_tolerance
            )
        result = pool[mask]
        if len(result) >= settings.min_similar:
            break
        widened = True
    # The sample size itself is reported by summarise_outcomes, so it isn't repeated here.
    return result, ["Few close matches, so size bands were widened."] if widened else []


def _median_days(values: pd.Series) -> int | None:
    values = values.dropna()
    return int(values.median()) if len(values) else None


def summarise_outcomes(
    similar: pd.DataFrame, settings: Settings
) -> tuple[Stats, list[DelayFactor], list[str]]:
    """Grant rate, timings, and delay factors for a set of similar applications."""
    total = len(similar)
    if total == 0:
        empty = Stats(
            n_similar=0,
            grant_rate=None,
            median_days_to_decision=None,
            share_further_information=None,
            share_appealed=None,
        )
        return empty, [], ["No similar applications found."]

    warnings = []
    if total < settings.small_sample:
        warnings.append(f"Small sample: only {total} similar applications.")

    decided = similar[similar["decision"].isin(DECIDED_OUTCOMES)]
    stats = Stats(
        n_similar=total,
        grant_rate=float((decided["decision"] == "granted").mean()) if len(decided) else None,
        median_days_to_decision=_median_days(decided["days_to_decision"]),
        share_further_information=float(similar["fi_requested"].mean()),
        share_appealed=float(similar["appealed"].mean()),
    )

    delay_factors = []
    further_info_days = _median_days(similar.loc[similar["fi_requested"], "fi_added_days"])
    if further_info_days is not None:
        delay_factors.append(
            DelayFactor(factor="further_information_request", added_days=further_info_days)
        )
    appeal_days = _median_days(similar.loc[similar["appealed"], "appeal_added_days"])
    if appeal_days is not None:
        delay_factors.append(DelayFactor(factor="appeal", added_days=appeal_days))
    return stats, delay_factors, warnings


def _optional_int(value) -> int | None:
    return None if pd.isna(value) else int(value)


def _optional_date(value) -> str | None:
    return None if pd.isna(value) else str(value)[:10]


def closest_matches(similar: pd.DataFrame, spec: ProjectSpec, limit: int = 5) -> list[Match]:
    """The applications nearest in size to the request, with what the map and case card need."""
    distance = pd.Series(0.0, index=similar.index)
    if spec.units:
        distance += (similar["units"] - spec.units).abs() / spec.units
    if spec.storeys:
        distance += (similar["storeys"].fillna(spec.storeys) - spec.storeys).abs() / 5
    nearest = similar.loc[distance.nsmallest(limit).index]

    # Convert all coordinates in one call; rows without coordinates stay None.
    has_point = nearest["itm_easting"].notna() & nearest["itm_northing"].notna()
    lons, lats = {}, {}
    if has_point.any():
        located = nearest[has_point]
        lon_values, lat_values = ITM_TO_WGS84.transform(
            located["itm_easting"].to_numpy(float), located["itm_northing"].to_numpy(float)
        )
        lons = dict(zip(located.index, lon_values, strict=True))
        lats = dict(zip(located.index, lat_values, strict=True))

    return [
        Match(
            id=str(row.id),
            address=row.address if pd.notna(row.address) else None,
            units=_optional_int(row.units),
            storeys=_optional_int(row.storeys),
            decision=str(row.decision).upper(),
            received_date=_optional_date(row.received_date),
            decision_date=_optional_date(row.decision_date),
            days_to_decision=_optional_int(row.days_to_decision),
            mixed_use=bool(row.mixed_use),
            further_information=bool(row.fi_requested),
            appealed=bool(row.appealed),
            lat=round(float(lats[index]), 6) if index in lats else None,
            lon=round(float(lons[index]), 6) if index in lons else None,
            link=row.link if pd.notna(row.link) and row.link else None,
        )
        for index, row in zip(nearest.index, nearest.itertuples(), strict=True)
    ]
