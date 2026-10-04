"""Faster-site search: estimate the pin's site, scan nearby grid cells, rank by weeks saved."""

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from planning_predictor.config import Settings
from planning_predictor.geo import ITM_TO_WGS84, WGS84_TO_ITM
from planning_predictor.schemas import Alternative, SiteEstimate
from planning_predictor.services.matching import DECIDED_OUTCOMES

_COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
_METRES_PER_KM = 1000.0
_DAYS_PER_WEEK = 7


@dataclass(frozen=True)
class SiteComparison:
    site_estimate: SiteEstimate | None
    alternatives: list[Alternative]
    warnings: list[str]


@dataclass(frozen=True)
class _AreaStats:
    radius_km: float
    n_similar: int
    median_total_days: int
    grant_rate: float
    council: str


def _compass_direction(dx: float, dy: float) -> str:
    bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360  # 0 = north
    return _COMPASS[int((bearing + 22.5) // 45) % 8]


class _AreaIndex:
    """Spatial index over decided applications with coordinates and a total duration."""

    def __init__(self, similar: pd.DataFrame, settings: Settings):
        usable = similar[
            similar["decision"].isin(DECIDED_OUTCOMES)
            & similar["total_days"].notna()
            & similar["itm_easting"].notna()
            & similar["itm_northing"].notna()
        ]
        self._settings = settings
        self._points = usable[["itm_easting", "itm_northing"]].to_numpy(float)
        self._days = usable["total_days"].to_numpy(float)
        self._granted = (usable["decision"] == "granted").to_numpy()
        self._councils = usable["council"].to_numpy()
        self._tree = cKDTree(self._points)

    def __len__(self) -> int:
        return len(self._points)

    def stats_around(self, x: float, y: float, max_radius_km: float) -> _AreaStats | None:
        """Stats within the site radius, widened 1 km at a time up to `max_radius_km` until the
        sample is big enough."""
        radius_km = self._settings.site_radius_km
        hits = self._tree.query_ball_point((x, y), radius_km * _METRES_PER_KM)
        while len(hits) < self._settings.site_min_sample and radius_km < max_radius_km:
            radius_km = min(radius_km + 1.0, max_radius_km)
            hits = self._tree.query_ball_point((x, y), radius_km * _METRES_PER_KM)
        if not hits:
            return None
        _, nearest = self._tree.query((x, y))  # always inside a non-empty ball around (x, y)
        return _AreaStats(
            radius_km=radius_km,
            n_similar=len(hits),
            median_total_days=int(np.median(self._days[hits])),
            grant_rate=float(self._granted[hits].mean()),
            council=str(self._councils[nearest]),
        )


@dataclass(frozen=True)
class _Candidate:
    """A grid cell that beats the pin's site, `dx`/`dy` metres east/north of the pin."""

    dx: float
    dy: float
    weeks_saved: int
    area: _AreaStats

    @property
    def distance_m(self) -> float:
        return math.hypot(self.dx, self.dy)


def find_faster_sites(
    similar_all_councils: pd.DataFrame,
    lat: float,
    lon: float,
    max_distance_km: float,
    settings: Settings,
) -> SiteComparison:
    """Compare the pin's site with nearby grid cells and return up to N faster alternatives."""
    index = _AreaIndex(similar_all_councils, settings)
    if len(index) == 0:
        return SiteComparison(None, [], ["No coordinates available for similar applications."])

    origin = WGS84_TO_ITM.transform(lon, lat)
    site = index.stats_around(*origin, settings.site_max_radius_km)
    if site is None:
        return SiteComparison(None, [], ["No decided similar applications near this site."])

    warnings = []
    if site.n_similar < settings.small_sample:
        warnings.append(f"Small sample at your site: only {site.n_similar} similar applications.")

    candidates = _faster_candidates(index, site, origin, max_distance_km, settings)
    alternatives = [
        _to_alternative(candidate, site, origin, settings)
        for candidate in _spaced_out(candidates, settings)
    ]
    if not alternatives:
        warnings.append("No nearby area with a meaningfully faster decision time was found.")
    site_estimate = SiteEstimate(
        radius_km=site.radius_km,
        n_similar=site.n_similar,
        median_total_days=site.median_total_days,
        grant_rate=site.grant_rate,
    )
    return SiteComparison(site_estimate, alternatives, warnings)


def _faster_candidates(
    index: _AreaIndex,
    site: _AreaStats,
    origin: tuple[float, float],
    max_distance_km: float,
    settings: Settings,
) -> list[_Candidate]:
    """Grid cells with enough applications that beat the site by the required margin, best first."""
    required_days = max(
        settings.site_margin_ratio * site.median_total_days,
        settings.site_margin_weeks * _DAYS_PER_WEEK,
    )
    candidates = []
    for dx, dy in _grid_offsets(max_distance_km, settings.site_grid_spacing_km):
        # No widening here: the area's stats must come from applications close to the point.
        area = index.stats_around(origin[0] + dx, origin[1] + dy, settings.site_radius_km)
        if area is None or area.n_similar < settings.site_min_sample:
            continue
        days_saved = site.median_total_days - area.median_total_days
        if days_saved >= required_days:
            weeks_saved = round(days_saved / _DAYS_PER_WEEK)
            candidates.append(_Candidate(dx, dy, weeks_saved, area))
    # Most weeks saved first, then the nearest, so a few days of noise can't outrank distance.
    return sorted(candidates, key=lambda c: (-c.weeks_saved, c.distance_m))


def _spaced_out(candidates: list[_Candidate], settings: Settings) -> list[_Candidate]:
    """The best candidates, skipping any too close to one already chosen."""
    min_separation_m = settings.site_min_separation_km * _METRES_PER_KM
    chosen: list[_Candidate] = []
    for candidate in candidates:
        if all(
            math.hypot(candidate.dx - other.dx, candidate.dy - other.dy) >= min_separation_m
            for other in chosen
        ):
            chosen.append(candidate)
            if len(chosen) == settings.site_max_results:
                break
    return chosen


def _grid_offsets(max_distance_km: float, spacing_km: float) -> list[tuple[float, float]]:
    """Grid offsets in metres from the pin, within max distance and at least 1 km away."""
    reach = int(max_distance_km // spacing_km)
    steps = np.arange(-reach, reach + 1) * spacing_km * _METRES_PER_KM
    grid_x, grid_y = np.meshgrid(steps, steps)
    distance_km = np.hypot(grid_x, grid_y) / _METRES_PER_KM
    keep = (distance_km >= 1) & (distance_km <= max_distance_km)
    return list(zip(grid_x[keep].tolist(), grid_y[keep].tolist(), strict=True))


def _to_alternative(
    candidate: _Candidate, site: _AreaStats, origin: tuple[float, float], settings: Settings
) -> Alternative:
    area = candidate.area
    lon, lat = ITM_TO_WGS84.transform(origin[0] + candidate.dx, origin[1] + candidate.dy)
    distance_km = round(candidate.distance_m / _METRES_PER_KM)
    direction = _compass_direction(candidate.dx, candidate.dy)
    warnings = []
    if area.council != site.council:
        warnings.append("Different council area: timing differences are mostly a council effect.")
    if site.grant_rate - area.grant_rate > settings.grant_rate_drop_warning:
        warnings.append("Lower grant rate than your site; faster is not better here.")
    return Alternative(
        label=f"{distance_km} km {direction}, {area.council}",
        council=area.council,
        lat=round(lat, 5),
        lon=round(lon, 5),
        distance_km=distance_km,
        direction=direction,
        radius_km=area.radius_km,
        n_similar=area.n_similar,
        median_total_days=area.median_total_days,
        grant_rate=area.grant_rate,
        weeks_saved=candidate.weeks_saved,
        warnings=warnings,
    )
