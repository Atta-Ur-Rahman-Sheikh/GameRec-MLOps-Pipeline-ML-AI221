"""FastAPI application entry point.

The lifespan handler eagerly loads every artifact bundle on startup so the
first request never pays the cold-load cost. Each ML feature lives in its
own router (see `app/api/`).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import clusters as clusters_api
from app.api import games as games_api
from app.api import player_type as player_type_api
from app.api import popularity as popularity_api
from app.api import recommender as recommender_api
from app.api import seasonality as seasonality_api
from app.core.artifacts import get_bundle, load_bundle
from app.core.config import settings
from app.schemas.responses import HealthResponse

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s")
log = logging.getLogger("gamerec.api")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    log.info("loading artifacts on startup ...")
    bundle = load_bundle()
    log.info("ready: catalog=%s, missing=%s",
             None if bundle.catalog is None else len(bundle.catalog),
             bundle.missing or "[none]")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="GameRec API",
        description=(
            "Hybrid game recommender, multi-label player-type classifier, "
            "popularity (cold-launch) regressor, hidden-genre clustering and "
            "release-month seasonality, served from precomputed artifacts."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/", include_in_schema=False)
    def root():
        return {"name": "GameRec API", "version": __version__, "docs": "/docs"}

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    def health():
        bundle = get_bundle()
        return HealthResponse(
            status="ok" if bundle.is_minimal_ready else "degraded",
            artifacts_loaded=bundle.is_minimal_ready,
            missing_artifacts=list(bundle.missing),
            catalog_size=None if bundle.catalog is None else int(len(bundle.catalog)),
        )

    app.include_router(games_api.router)
    app.include_router(recommender_api.router)
    app.include_router(player_type_api.router)
    app.include_router(popularity_api.router)
    app.include_router(clusters_api.router)
    app.include_router(seasonality_api.router)

    return app


app = create_app()
