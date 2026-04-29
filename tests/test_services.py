"""Unit tests for pure-Python service helpers."""

from __future__ import annotations

import pytest

from app.services.popularity import build_features, predict_popularity
from app.services.recommender import find_game_index, recommend_for_user, recommend_similar
from app.services.seasonality import get_seasonality, list_themes


def test_find_game_index(bundle, famous_game):
    idx = find_game_index(famous_game, bundle)
    assert idx is not None
    assert bundle.catalog.iloc[idx]["name"] == famous_game


def test_recommend_similar_returns_ranked_list(bundle, famous_game):
    items = recommend_similar(famous_game, top_k=5, bundle=bundle)
    assert len(items) == 5
    assert all("score" in r and "name" in r for r in items)
    scores = [r["score"] for r in items]
    assert max(scores) == scores[0]


def test_recommend_for_user_requires_preferences(bundle):
    with pytest.raises(ValueError):
        recommend_for_user(liked_genres=[], liked_tags=[], bundle=bundle)


def test_recommend_for_user_coerces(bundle):
    items = recommend_for_user(
        liked_genres=["Indie"],
        liked_tags=["Roguelike"],
        top_k=4,
        bundle=bundle,
    )
    assert len(items) <= 4
    assert items


def test_predict_popularity_cold_start(bundle):
    out = predict_popularity(
        tags=["Roguelike", "Pixel Graphics"],
        genres=["Indie", "Action"],
        categories=["Steam Achievements"],
        description="A fast-paced roguelike with procedural dungeons.",
        release_year=2023,
        platforms=["PC"],
        bundle=bundle,
    )
    assert "predicted_popularity" in out
    assert 0.0 <= out["predicted_popularity"] <= 5.5
    assert out["feature_vector_dim"] >= 32


def test_build_features_matches_model_width(bundle):
    X = build_features(
        tags=["Indie"],
        genres=["RPG"],
        categories=[],
        description="test",
        release_year=2020,
        platforms=["PC"],
        bundle=bundle,
    )
    model = bundle.popularity_model
    assert model is not None
    expected = getattr(model, "n_features_in_", X.shape[1])
    assert X.shape[1] == expected


def test_seasonality_list_and_get(bundle):
    themes = list_themes()
    assert themes
    first = themes[0]
    payload = get_seasonality(first, bundle=bundle)
    assert payload["theme"]
    assert len(payload["seasonal_index"]) == 12
