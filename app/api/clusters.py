"""Hidden-genre cluster endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.responses import ClusterCard, ClusterMapResponse, HiddenGenreResponse
from app.services.clusters import build_cluster_map, discover_hidden_genre, list_clusters

router = APIRouter(prefix="/discover", tags=["clusters"])

log = logging.getLogger("gamerec.api.clusters")


@router.get("/cluster-map", response_model=ClusterMapResponse)
def get_cluster_map():
    """Two-dimensional PCA of LSA vectors; points tinted by cluster for Explore."""
    try:
        payload = build_cluster_map()
        return ClusterMapResponse.model_validate(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — return a safe message to the client
        log.exception("cluster map failed unexpectedly")
        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc

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
            dt = [{"tag": t, "lift": float(lift), "count": int(n)} for t, lift, n in dt]
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
