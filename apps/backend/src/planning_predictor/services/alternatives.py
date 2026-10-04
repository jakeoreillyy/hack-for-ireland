"""Faster-site search: estimate the pin's site, scan nearby grid cells, rank by weeks saved."""

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

from planning_predictor.config import Settings
from planning_predictor.schemas import Alternative, SiteEstimate
from planning_predictor.services.matching import DECIDED_OUTCOMES

_WGS84_TO_ITM = Transformer.from_crs("EPSG:4326", "EPSG:2157", always_xy=True)
_ITM_TO_WGS84 = Transformer.from_crs("EPSG:2157", "EPSG:4326", always_xy=True)
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

    x0, y0 = _WGS84_TO_ITM.transform(lon, lat)
    site = index.stats_around(x0, y0, settings.site_max_radius_km)
    if site is None:
        return SiteComparison(None, [], ["No decided similar applications near this site."])

    warnings = []
    if site.n_similar < settings.small_sample:
        warnings.append(f"Small sample at your site: only {site.n_similar} similar applications.")
    required_days = max(
        settings.site_margin_ratio * site.median_total_days,
        settings.site_margin_weeks * _DAYS_PER_WEEK,
    )

    candidates = []
    for dx, dy in _grid_offsets(max_distance_km, settings.site_grid_spacing_km):
        # No widening here: the area's stats must come from applications close to the point.
        area = index.stats_around(x0 + dx, y0 + dy, settings.site_radius_km)
        if area is None or area.n_similar < settings.site_min_sample:
            continue
        days_saved = site.median_total_days - area.median_total_days
        if days_saved >= required_days:
            weeks_saved = round(days_saved / _DAYS_PER_WEEK)
            candidates.append((weeks_saved, math.hypot(dx, dy), dx, dy, area))
    # Most weeks saved first, then the nearest, so a few days of noise can't outrank distance.
    candidates.sort(key=lambda c: (-c[0], c[1]))

    chosen: list[Alternative] = []
    chosen_offsets: list[tuple[float, float]] = []
    min_separation_m = settings.site_min_separation_km * _METRES_PER_KM
    for weeks_saved, distance_m, dx, dy, area in candidates:
        if any(math.hypot(dx - ox, dy - oy) < min_separation_m for ox, oy in chosen_offsets):
            continue
        chosen.append(
            _to_alternative(weeks_saved, distance_m, dx, dy, area, site, x0, y0, settings)
        )
        chosen_offsets.append((dx, dy))
        if len(chosen) == settings.site_max_results:
            break

    if not chosen:
        warnings.append("No nearby area with a meaningfully faster decision time was found.")
    return SiteComparison(
        SiteEstimate(
            radius_km=site.radius_km,
            n_similar=site.n_similar,
            median_total_days=site.median_total_days,
            grant_rate=site.grant_rate,
        ),
        chosen,
        warnings,
    )


def _grid_offsets(max_distance_km: float, spacing_km: float) -> list[tuple[float, float]]:
    """Grid offsets in metres from the pin, within max distance and at least 1 km away."""
    reach = int(max_distance_km // spacing_km)
    steps = np.arange(-reach, reach + 1) * spacing_km * _METRES_PER_KM
    grid_x, grid_y = np.meshgrid(steps, steps)
    distance_km = np.hypot(grid_x, grid_y) / _METRES_PER_KM
    keep = (distance_km >= 1) & (distance_km <= max_distance_km)
    return list(zip(grid_x[keep].tolist(), grid_y[keep].tolist(), strict=True))


def _to_alternative(
    weeks_saved: int,
    distance_m: float,
    dx: float,
    dy: float,
    area: _AreaStats,
    site: _AreaStats,
    x0: float,
    y0: float,
    settings: Settings,
) -> Alternative:
    lon, lat = _ITM_TO_WGS84.transform(x0 + dx, y0 + dy)
    distance_km = round(distance_m / _METRES_PER_KM)
    direction = _compass_direction(dx, dy)
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
        weeks_saved=weeks_saved,
        warnings=warnings,
    )
