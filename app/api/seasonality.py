"""Seasonality lookup endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.responses import SeasonalityResponse
from app.services.seasonality import get_seasonality, list_themes

router = APIRouter(prefix="/seasonality", tags=["seasonality"])


@router.get("/themes", response_model=list[str])
def get_themes():
    """List the themes available in the seasonality artifact."""
    return list_themes()


@router.get("/{theme}", response_model=SeasonalityResponse)
def get_theme(theme: str):
    try:
        return get_seasonality(theme)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
