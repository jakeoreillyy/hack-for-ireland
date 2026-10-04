"""Application settings. Every tunable lives here and can be overridden by environment variable."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parents[1]


class Settings(BaseSettings):
    # Absolute path, so apps/backend/.env is found whichever directory the server starts in.
    model_config = SettingsConfigDict(env_file=BACKEND_ROOT / ".env", extra="ignore")

    # Data
    data_dir: Path = REPO_ROOT / "data"

    # Claude (optional: regex parsing is used when no key is set or the call fails)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-5-5"
    llm_timeout_seconds: float = 20.0

    # HTTP
    cors_origins: list[str] = ["*"]

    # Matching: widen size bands until this many similar applications are found
    min_similar: int = 20
    small_sample: int = 15
    # (units tolerance, storeys tolerance or None to ignore storeys), tried in order
    size_bands: list[tuple[float, int | None]] = Field(
        default=[(0.3, 2), (0.5, 3), (0.5, None), (1.0, None)], min_length=1
    )

    # Faster-site search. Only the pin's own radius widens (up to site_max_radius_km);
    # candidate areas use site_radius_km so their stats come from applications near them.
    site_radius_km: float = 3.0
    site_max_radius_km: float = 8.0
    site_min_sample: int = 15
    site_grid_spacing_km: float = 2.0
    # An area must be faster by site_margin_ratio of the site's time, and never by less than
    # site_margin_weeks, so short timelines don't produce trivial "faster" suggestions.
    site_margin_ratio: float = 0.25
    site_margin_weeks: int = 12
    site_min_separation_km: float = 5.0
    site_max_results: int = 3
    grant_rate_drop_warning: float = 0.10


@lru_cache
def get_settings() -> Settings:
    return Settings()
