"""Player-type classifier inference.

Ported from `Game_Recommender_Simple.ipynb` cell 38.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.preprocessing import normalize

from app.core.artifacts import ArtifactBundle, get_bundle
from app.services._text import build_query_text
from app.services.recommender import find_game_index


def _format_proba(
    proba: np.ndarray, label_names: list[str], top_k: int | None, threshold: float
) -> list[dict[str, Any]]:
    rows = [
        {
            "archetype": label_names[j],
            "probability": round(float(proba[j]), 4),
            "predicted": bool(proba[j] >= threshold),
        }
        for j in range(len(label_names))
    ]
    rows.sort(key=lambda r: -r["probability"])
    return rows[:top_k] if top_k else rows


def predict_player_types(
    title: str,
    top_k: int | None = None,
    threshold: float = 0.5,
    bundle: ArtifactBundle | None = None,
) -> dict[str, Any]:
    """Predict archetype scores for an existing catalog game."""
    bundle = bundle or get_bundle()
    if bundle.player_clf is None or bundle.lsa_norm is None:
        raise RuntimeError("Player-type classifier or LSA matrix not loaded.")
    idx = find_game_index(title, bundle)
    if idx is None:
        raise KeyError(f"No game found matching {title!r}")
    proba = bundle.player_clf.predict_proba(bundle.lsa_norm[idx : idx + 1])[0]
    return {
        "title": str(bundle.catalog.iloc[idx]["name"]),
        "predictions": _format_proba(proba, bundle.player_type_names, top_k, threshold),
    }


def predict_for_query(
    liked_genres: list[str] | None = None,
    liked_tags: list[str] | None = None,
    top_k: int | None = None,
    threshold: float = 0.5,
    bundle: ArtifactBundle | None = None,
) -> dict[str, Any]:
    """Cold-start prediction: score archetypes for a hypothetical game."""
    bundle = bundle or get_bundle()
    if bundle.player_clf is None or bundle.svd is None or bundle.vectorizer is None:
        raise RuntimeError("Player-type classifier or text models not loaded.")
    if not (liked_genres or liked_tags):
        raise ValueError("Provide at least one liked genre or tag.")

    qtxt = build_query_text(liked_genres, liked_tags)
    qtfidf = bundle.vectorizer.transform([qtxt])
    qlsa = normalize(bundle.svd.transform(qtfidf)).astype(np.float32)
    proba = bundle.player_clf.predict_proba(qlsa)[0]
    return {
        "query": {"genres": liked_genres or [], "tags": liked_tags or []},
        "predictions": _format_proba(proba, bundle.player_type_names, top_k, threshold),
    }
