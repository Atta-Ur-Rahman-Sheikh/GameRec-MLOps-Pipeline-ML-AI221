"""Settings and filesystem paths for the FastAPI service.

Everything that might differ between dev / Docker / CI lives here, driven
by environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _project_root() -> Path:
    # `app/core/config.py` -> project root is two parents up.
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    project_root: Path
    artifacts_dir: Path
    n_latent: int
    seasonality_year_min: int
    seasonality_year_max: int
    cors_allow_origins: list[str]

    @classmethod
    def from_env(cls) -> Settings:
        root = _project_root()
        artifacts = Path(
            os.environ.get("GAMEREC_ARTIFACTS_DIR", root / "artifacts" / "recommender")
        ).resolve()

        cors_raw = os.environ.get("GAMEREC_CORS_ORIGINS", "*")
        cors = [c.strip() for c in cors_raw.split(",") if c.strip()] or ["*"]

        return cls(
            project_root=root,
            artifacts_dir=artifacts,
            n_latent=int(os.environ.get("GAMEREC_N_LATENT", "128")),
            seasonality_year_min=int(os.environ.get("GAMEREC_SEASON_YEAR_MIN", "2014")),
            seasonality_year_max=int(os.environ.get("GAMEREC_SEASON_YEAR_MAX", "2024")),
            cors_allow_origins=cors,
        )


settings = Settings.from_env()
