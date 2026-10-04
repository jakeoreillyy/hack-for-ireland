"""Request and response models. These mirror CONTRACT.md exactly; do not rename fields."""

from pydantic import BaseModel, Field


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ProjectSpec(BaseModel):
    units: int | None = Field(default=None, ge=1, le=5000)
    storeys: int | None = Field(default=None, ge=1, le=60)
    mixed_use: bool = False


class ParsedProject(ProjectSpec):
    council: str


class PredictRequest(BaseModel):
    description: str = Field(default="", max_length=1000)
    council: str
    location: Location | None = None
    max_distance_km: float = Field(default=25, gt=0, le=100)
    parsed_override: ProjectSpec | None = None  # proposed addition to CONTRACT.md


class Stats(BaseModel):
    n_similar: int
    grant_rate: float | None
    median_days_to_decision: int | None
    share_further_information: float | None
    share_appealed: float | None


class DelayFactor(BaseModel):
    factor: str
    added_days: int


class SiteEstimate(BaseModel):
    radius_km: float
    n_similar: int
    median_total_days: int
    grant_rate: float


class Alternative(BaseModel):
    label: str
    council: str
    lat: float
    lon: float
    distance_km: int
    direction: str
    radius_km: float
    n_similar: int
    median_total_days: int
    grant_rate: float
    weeks_saved: int
    warnings: list[str] = []


class Match(BaseModel):
    id: str
    address: str | None
    units: int | None
    storeys: int | None
    decision: str
    decision_date: str | None
    link: str | None


class PredictResponse(BaseModel):
    parsed: ParsedProject
    stats: Stats
    delay_factors: list[DelayFactor]
    site_estimate: SiteEstimate | None
    alternatives: list[Alternative]
    summary: str
    matches: list[Match]
    warnings: list[str]
