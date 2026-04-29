"""Hybrid recommender endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.requests import ExplainRequest, SimilarRequest, UserRequest
from app.schemas.responses import ExplainResponse, RecommendationResponse
from app.services.explain import explain_match
from app.services.recommender import recommend_for_user, recommend_similar

router = APIRouter(prefix="/recommend", tags=["recommender"])


@router.post("/similar", response_model=RecommendationResponse)
def post_similar(req: SimilarRequest):
    try:
        items = recommend_similar(
            title=req.game_name,
            top_k=req.n,
            w_lsa=req.w_lsa,
            w_text=req.w_text,
            w_pop=req.w_pop,
            min_pop=req.min_pop,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"anchor": req.game_name, "items": items}


@router.post("/user", response_model=RecommendationResponse)
def post_user(req: UserRequest):
    try:
        items = recommend_for_user(
            liked_genres=req.liked_genres,
            liked_tags=req.liked_tags,
            platforms=req.platforms or None,
            top_k=req.n,
            w_lsa=req.w_lsa,
            w_text=req.w_text,
            w_pop=req.w_pop,
            min_pop_quantile=req.min_pop_quantile,
            min_rating=req.min_rating,
            use_content_richness=req.use_content_richness,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "query": {
            "liked_genres": req.liked_genres,
            "liked_tags": req.liked_tags,
            "platforms": req.platforms,
        },
        "items": items,
    }


@router.post("/explain", response_model=ExplainResponse)
def post_explain(req: ExplainRequest):
    try:
        return explain_match(req.anchor, req.recommended, top_k_tokens=req.top_k_tokens)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
