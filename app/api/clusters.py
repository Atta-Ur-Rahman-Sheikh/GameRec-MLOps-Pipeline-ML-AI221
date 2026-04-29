"""Hidden-genre cluster endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.responses import ClusterCard, HiddenGenreResponse
from app.services.clusters import discover_hidden_genre, list_clusters

router = APIRouter(prefix="/discover", tags=["clusters"])


@router.get("/clusters", response_model=list[ClusterCard])
def get_clusters():
    """Return all hidden-genre cluster cards (auto-name + distinctive tags + examples)."""
    try:
        cards = list_clusters()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    # The notebook stores `distinctive_tags` already in dict form, but defend in case.
    out: list[dict] = []
    for c in cards:
        dt = c.get("distinctive_tags", [])
        if dt and isinstance(dt[0], (list, tuple)):
            dt = [{"tag": t, "lift": float(l), "count": int(n)} for t, l, n in dt]
        out.append({**c, "distinctive_tags": dt})
    return out


@router.get("/hidden-genre/{game_name}", response_model=HiddenGenreResponse)
def get_hidden_genre(game_name: str):
    try:
        return discover_hidden_genre(game_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
