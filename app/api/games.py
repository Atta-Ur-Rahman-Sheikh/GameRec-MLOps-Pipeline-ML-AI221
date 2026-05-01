"""Game search endpoint -- thin wrapper used by the demo UI / for resolving titles."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.responses import DiscoverRowsResponse, GameSearchHit
from app.services.recommender import discover_rows, search_games

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/search", response_model=list[GameSearchHit])
def games_search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    """Return up to `limit` catalog entries whose name contains `q`."""
    return search_games(q, limit=limit)


@router.get("/discover", response_model=DiscoverRowsResponse)
def games_discover(limit: int = Query(12, ge=4, le=24)):
    """Curated discovery rows for the home page."""
    return discover_rows(limit=limit)
