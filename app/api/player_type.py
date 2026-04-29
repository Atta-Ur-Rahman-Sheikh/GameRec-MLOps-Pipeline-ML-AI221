"""Player-type classifier endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.requests import PlayerTypeByQueryRequest, PlayerTypeByTitleRequest
from app.schemas.responses import PlayerTypeResponse
from app.services.player_type import predict_for_query, predict_player_types

router = APIRouter(prefix="/predict", tags=["player-type"])


@router.post("/player-type/by-title", response_model=PlayerTypeResponse)
def post_player_type_by_title(req: PlayerTypeByTitleRequest):
    try:
        return predict_player_types(req.game_name, top_k=req.top_k, threshold=req.threshold)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/player-type/by-query", response_model=PlayerTypeResponse)
def post_player_type_by_query(req: PlayerTypeByQueryRequest):
    try:
        return predict_for_query(
            liked_genres=req.liked_genres,
            liked_tags=req.liked_tags,
            top_k=req.top_k,
            threshold=req.threshold,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
