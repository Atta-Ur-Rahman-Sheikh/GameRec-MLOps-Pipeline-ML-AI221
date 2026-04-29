"""Response schemas for the FastAPI endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    artifacts_loaded: bool
    missing_artifacts: list[str]
    catalog_size: int | None = None


class GameSearchHit(BaseModel):
    name: str
    popularity: float
    rating: float | None = None
    genres: list[str]
    platforms: list[str]


class RecommendationItem(BaseModel):
    name: str
    score: float
    lsa_sim: float
    txt_sim: float
    rating: float
    popularity: float
    genres: list[str]
    platforms: list[str]
    tags: list[str] | None = None


class RecommendationResponse(BaseModel):
    anchor: str | None = None
    query: dict[str, Any] | None = None
    items: list[RecommendationItem]


class PlayerTypePrediction(BaseModel):
    archetype: str
    probability: float
    predicted: bool


class PlayerTypeResponse(BaseModel):
    title: str | None = None
    query: dict[str, Any] | None = None
    predictions: list[PlayerTypePrediction]


class PopularityResponse(BaseModel):
    predicted_popularity: float
    feature_vector_dim: int
    model_meta: dict[str, Any]


class DistinctiveTag(BaseModel):
    tag: str
    lift: float
    count: int


class SimilarGame(BaseModel):
    name: str
    popularity: float


class HiddenGenreResponse(BaseModel):
    game: str
    steam_genres: list[str]
    cluster_id: int
    hidden_genre_name: str
    cluster_size: int
    distinctive_tags: list[DistinctiveTag]
    similar_games: list[SimilarGame]


class ClusterCard(BaseModel):
    cluster_id: int
    auto_name: str
    size: int
    avg_popularity: float
    top_genres: list[str]
    distinctive_tags: list[DistinctiveTag]
    examples: list[str]


class SeasonalityResponse(BaseModel):
    theme: str
    window: dict[str, int] | None
    n_games: int
    month_names: list[str]
    monthly_avg: list[float]
    seasonal_index: list[float]
    peak_month: str | None
    peak_index_value: float | None
    forecast: dict[str, Any] | None


class ExplainResponse(BaseModel):
    anchor: str
    recommended: str
    lsa_sim: float
    txt_sim: float
    shared_genres: list[str]
    shared_tags: list[str]
    top_terms: list[tuple[str, float]]
