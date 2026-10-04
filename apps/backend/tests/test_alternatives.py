import itertools
import math

import numpy as np

from helpers import applications_table, repeated
from planning_predictor.services.alternatives import find_faster_sites

# Dublin centre, ~2 km from the helpers' default point. The `applications` fixture is slow here
# and fast ~12 km west.
PIN = (53.3467, -6.2947)
KM_PER_DEGREE_LAT = 111.0


def compare(applications, settings, max_distance_km=25.0):
    return find_faster_sites(applications, *PIN, max_distance_km, settings)


def test_no_coordinates_means_no_comparison(applications, settings):
    applications[["itm_easting", "itm_northing"]] = np.nan
    result = compare(applications, settings)
    assert result.site_estimate is None and result.alternatives == []
    assert any("coordinates" in w for w in result.warnings)


def test_rows_missing_coordinates_are_ignored_not_fatal(applications, settings):
    applications.loc[applications.index[::3], ["itm_easting", "itm_northing"]] = np.nan
    result = compare(applications, settings)
    assert result.site_estimate is not None and result.alternatives


def test_a_site_with_few_nearby_applications_warns(settings):
    result = compare(applications_table(*repeated(4)), settings)
    assert any("Small sample at your site" in w for w in result.warnings)


def test_distance_limit_keeps_far_alternatives_out(applications, settings):
    result = compare(applications, settings, max_distance_km=3)
    assert result.alternatives == []
    assert any("No nearby area" in w for w in result.warnings)


def test_alternatives_are_spaced_and_limited(applications, settings):
    found = compare(applications, settings).alternatives
    assert 0 < len(found) <= settings.site_max_results
    for first, second in itertools.combinations(found, 2):
        dy = (first.lat - second.lat) * KM_PER_DEGREE_LAT
        dx = (first.lon - second.lon) * KM_PER_DEGREE_LAT * math.cos(math.radians(first.lat))
        assert math.hypot(dx, dy) >= settings.site_min_separation_km - 0.5


def test_alternatives_are_ranked_by_weeks_saved(settings):
    table = applications_table(
        *repeated(15, total_days=400),  # at the pin
        *repeated(15, itm_easting=705800.0, total_days=100),  # ~8 km W: 43 weeks faster
        *repeated(15, itm_northing=744000.0, total_days=250),  # ~10 km N: 21 weeks faster
    )
    weeks = [a.weeks_saved for a in compare(table, settings).alternatives]
    assert weeks == sorted(weeks, reverse=True) and set(weeks) == {43, 21}


def test_a_lower_grant_rate_is_flagged_next_to_the_speed_gain(applications, settings):
    west = applications["council"] == "South Dublin County Council"
    applications.loc[west, "decision"] = "refused"
    result = compare(applications, settings)
    assert result.alternatives
    assert all(any("Lower grant rate" in w for w in alt.warnings) for alt in result.alternatives)


def test_no_alternative_when_the_site_is_already_fast(applications, settings):
    applications["total_days"] = 90
    result = compare(applications, settings)
    assert result.alternatives == []
