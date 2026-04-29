"""Popularity (cold-launch) regressor endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.requests import PopularityRequest
from app.schemas.responses import PopularityResponse
from app.services.popularity import predict_popularity

router = APIRouter(prefix="/predict", tags=["popularity"])


@router.post("/popularity", response_model=PopularityResponse)
def post_popularity(req: PopularityRequest):
    try:
        return predict_popularity(
            tags=req.tags,
            genres=req.genres,
            categories=req.categories,
            description=req.description,
            release_year=req.release_year,
            platforms=req.platforms or None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
