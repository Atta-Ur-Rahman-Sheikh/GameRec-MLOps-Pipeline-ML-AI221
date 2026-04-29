"""Popularity (cold-launch) regressor inference.

Ported from `Game_Recommender_Simple.ipynb` cells 42 and 44. Builds the
exact same 141-feature vector at request time so the trained XGBoost
model can score a game described only by its content.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.preprocessing import normalize

from app.core.artifacts import ArtifactBundle, get_bundle
from app.services._text import build_query_text


# Default extra-feature names. Used as a fallback if the saved bundle
# doesn't include them (older artifacts may not carry the metadata).
DEFAULT_EXTRA_FEATURE_NAMES = [
    "n_tags", "n_genres", "n_categories", "n_platforms", "desc_length",
    "has_multiplayer", "has_singleplayer", "is_indie",
    "has_achievements", "has_trading_cards", "has_early_access", "has_vr",
]

MULTIPLAYER_TAGS = {"Multiplayer", "Online PvP", "PvP", "Online Co-Op"}
SINGLEPLAYER_TAGS = {"Singleplayer"}
INDIE_GENRES = {"Indie"}
ACHIEVEMENTS_CATEGORY = "Steam Achievements"
TRADING_CARDS_CATEGORY = "Steam Trading Cards"
EARLY_ACCESS_TAG = "Early Access"
VR_TAG = "VR"


def _has_any(values: list[str], items: set[str]) -> int:
    return int(bool(set(values) & items))


def build_features(tags: list[str],
                   genres: list[str],
                   categories: list[str],
                   description: str,
                   release_year: int,
                   platforms: list[str] | None,
                   bundle: ArtifactBundle) -> np.ndarray:
    """Build a single feature vector matching the training pipeline shape.

    Always returns LSA + 1 year feature; appends the 12 metadata flags
    only when the loaded model was trained with them (detected via
    `extra_feature_names` in the joblib bundle, with a safety net that
    falls back to the model's `n_features_in_` attribute).
    """
    if bundle.svd is None or bundle.vectorizer is None:
        raise RuntimeError("Text models not loaded; cannot build features.")

    meta = bundle.popularity_meta or {}
    year_centre = float(meta.get("year_centre", 2010.0))
    year_scale = float(meta.get("year_scale", 10.0))
    median_year = float(meta.get("median_year", 2018.0))
    extra_names = meta.get("extra_feature_names") or []

    qtxt = build_query_text(genres, tags)
    qtfidf = bundle.vectorizer.transform([qtxt])
    lsa_vec = normalize(bundle.svd.transform(qtfidf)).astype(np.float32)  # (1, N_LATENT)
    n_lsa = lsa_vec.shape[1]

    if not isinstance(release_year, (int, float)) or np.isnan(release_year):
        release_year = median_year
    release_year = float(np.clip(release_year, 1990, 2026))
    year_feat = np.array([[(release_year - year_centre) / year_scale]], dtype=np.float32)

    base = np.hstack([lsa_vec, year_feat]).astype(np.float32)

    # Decide whether to append the 12 metadata flags. The metadata-rich
    # model carries `extra_feature_names` in its joblib bundle, but older
    # artifacts don't, so fall back to inspecting the model's expected
    # feature width.
    needs_extras = bool(extra_names)
    if not needs_extras and bundle.popularity_model is not None:
        expected = getattr(bundle.popularity_model, "n_features_in_", None)
        if expected is None:  # XGBoost wrapper exposes n_features_in_ in newer versions
            try:
                expected = int(bundle.popularity_model.get_booster().num_features())
            except Exception:  # noqa: BLE001
                expected = base.shape[1]
        needs_extras = expected > base.shape[1]

    if not needs_extras:
        return base

    desc_len = (len(description) if isinstance(description, str) else 0) / 1000.0
    extras = np.array([[
        len(tags),
        len(genres),
        len(categories),
        len(platforms or []),
        desc_len,
        _has_any(tags, MULTIPLAYER_TAGS),
        _has_any(tags, SINGLEPLAYER_TAGS),
        _has_any(genres, INDIE_GENRES),
        int(ACHIEVEMENTS_CATEGORY in categories),
        int(TRADING_CARDS_CATEGORY in categories),
        int(EARLY_ACCESS_TAG in tags),
        int(VR_TAG in tags),
    ]], dtype=np.float32)

    return np.hstack([base, extras]).astype(np.float32)


def predict_popularity(tags: list[str],
                       genres: list[str],
                       categories: list[str],
                       description: str,
                       release_year: int,
                       platforms: list[str] | None = None,
                       bundle: ArtifactBundle | None = None) -> dict[str, Any]:
    """Predict the 0-5 Bayesian-shrunk popularity score for a hypothetical game."""
    bundle = bundle or get_bundle()
    if bundle.popularity_model is None:
        raise RuntimeError("Popularity regressor is not loaded.")

    X = build_features(tags=tags, genres=genres, categories=categories,
                       description=description, release_year=release_year,
                       platforms=platforms, bundle=bundle)
    pred = float(bundle.popularity_model.predict(X)[0])
    return {
        "predicted_popularity": round(pred, 3),
        "feature_vector_dim": int(X.shape[1]),
        "model_meta": {
            "model_name": bundle.popularity_meta.get("model_name", "XGBoost"),
            "year_centre": bundle.popularity_meta.get("year_centre", 2010.0),
            "year_scale": bundle.popularity_meta.get("year_scale", 10.0),
        },
    }
