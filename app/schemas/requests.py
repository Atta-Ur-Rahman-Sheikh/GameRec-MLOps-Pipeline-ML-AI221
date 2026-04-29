"""Request schemas for the FastAPI endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SimilarRequest(BaseModel):
    game_name: str = Field(..., min_length=1, description="Game title to find similar games for.")
    n: int = Field(10, ge=1, le=50)
    w_lsa: float = Field(0.55, ge=0.0, le=1.0)
    w_text: float = Field(0.30, ge=0.0, le=1.0)
    w_pop: float = Field(0.15, ge=0.0, le=1.0)
    min_pop: float | None = Field(None, ge=0.0, le=1.0,
                                   description="Optional popularity floor (quantile).")


class UserRequest(BaseModel):
    liked_genres: list[str] = Field(default_factory=list)
    liked_tags: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    n: int = Field(10, ge=1, le=50)
    w_lsa: float = Field(0.30, ge=0.0, le=1.0)
    w_text: float = Field(0.30, ge=0.0, le=1.0)
    w_pop: float = Field(0.40, ge=0.0, le=1.0)
    min_pop_quantile: float = Field(0.40, ge=0.0, le=1.0)
    min_rating: float = Field(0.0, ge=0.0, le=5.0)
    use_content_richness: bool = True

    @field_validator("liked_genres", "liked_tags", "platforms", mode="before")
    @classmethod
    def _coerce_lists(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)


class PlayerTypeByTitleRequest(BaseModel):
    game_name: str = Field(..., min_length=1)
    top_k: int | None = Field(None, ge=1, le=8)
    threshold: float = Field(0.5, ge=0.0, le=1.0)


class PlayerTypeByQueryRequest(BaseModel):
    liked_genres: list[str] = Field(default_factory=list)
    liked_tags: list[str] = Field(default_factory=list)
    top_k: int | None = Field(None, ge=1, le=8)
    threshold: float = Field(0.5, ge=0.0, le=1.0)


class PopularityRequest(BaseModel):
    tags: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    description: str = Field("", max_length=10_000)
    release_year: int = Field(2024, ge=1990, le=2026)
    platforms: list[str] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    anchor: str = Field(..., min_length=1)
    recommended: str = Field(..., min_length=1)
    top_k_tokens: int = Field(6, ge=1, le=20)
