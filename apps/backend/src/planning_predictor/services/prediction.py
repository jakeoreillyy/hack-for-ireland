"""Orchestrates one /predict request."""

import logging

import pandas as pd

from planning_predictor.config import Settings
from planning_predictor.schemas import ParsedProject, PredictRequest, PredictResponse
from planning_predictor.services import alternatives, matching, parsing
from planning_predictor.services.summary import build_summary

logger = logging.getLogger(__name__)


def predict(
    request: PredictRequest, applications: pd.DataFrame, settings: Settings
) -> PredictResponse:
    spec, warnings = parsing.parse_description(
        request.description, request.parsed_override, settings
    )

    similar, band_warnings = matching.find_similar_applications(
        applications, spec, settings, request.council
    )
    stats, delay_factors, stats_warnings = matching.summarise_outcomes(similar, settings)
    warnings += band_warnings + stats_warnings

    comparison = alternatives.SiteComparison(None, [], [])
    if request.location:
        try:
            similar_everywhere, _ = matching.find_similar_applications(applications, spec, settings)
            comparison = alternatives.find_faster_sites(
                similar_everywhere,
                request.location.lat,
                request.location.lon,
                request.max_distance_km,
                settings,
            )
        except Exception:
            logger.exception("Site comparison failed")
            comparison = alternatives.SiteComparison(
                None, [], ["Site comparison failed; showing council results only."]
            )
    warnings += comparison.warnings

    return PredictResponse(
        parsed=ParsedProject(**spec.model_dump(), council=request.council),
        stats=stats,
        delay_factors=delay_factors,
        site_estimate=comparison.site_estimate,
        alternatives=comparison.alternatives,
        summary=build_summary(stats, delay_factors, comparison.alternatives),
        matches=matching.closest_matches(similar, spec),
        warnings=warnings,
    )
