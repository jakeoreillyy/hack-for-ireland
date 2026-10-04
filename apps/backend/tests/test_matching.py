import numpy as np

from planning_predictor.schemas import ProjectSpec
from planning_predictor.services import matching

COUNCIL = "Dublin City Council"


def test_close_matches_need_no_widening(applications, settings):
    similar, warnings = matching.find_similar_applications(
        applications, ProjectSpec(units=120, storeys=8), settings, COUNCIL
    )
    assert len(similar) >= settings.min_similar and warnings == []


def test_widening_is_reported_once(applications, settings):
    similar, warnings = matching.find_similar_applications(
        applications, ProjectSpec(units=10), settings, COUNCIL
    )
    assert similar.empty and warnings == ["Few close matches, so size bands were widened."]


def test_no_size_matches_the_whole_council_without_a_widening_warning(applications, settings):
    similar, warnings = matching.find_similar_applications(
        applications, ProjectSpec(), settings, COUNCIL
    )
    assert (similar["council"] == COUNCIL).all() and len(similar) > 100 and warnings == []


def test_matches_report_missing_address_and_link_as_null(applications):
    applications["address"] = None
    applications["link"] = np.where(applications.index % 2, "", None)
    matches = matching.closest_matches(applications, ProjectSpec(units=120), limit=4)
    assert all(m.address is None and m.link is None for m in matches)
