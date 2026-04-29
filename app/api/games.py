"""Game search endpoint -- thin wrapper used by the demo UI / for resolving titles."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.responses import GameSearchHit
from app.services.recommender import search_games

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/search", response_model=list[GameSearchHit])
def games_search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    """Return up to `limit` catalog entries whose name contains `q`."""
    return search_games(q, limit=limit)
