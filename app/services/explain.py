"""Explanation service: why was game B matched to game A?

Ported from `Game_Recommender_Simple.ipynb` cell 18.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.artifacts import ArtifactBundle, get_bundle
from app.services.recommender import find_game_index


def explain_match(
    anchor: str | int,
    recommended: str | int,
    top_k_tokens: int = 6,
    bundle: ArtifactBundle | None = None,
) -> dict[str, Any]:
    """Return a dict explaining why `recommended` was matched to `anchor`."""
    bundle = bundle or get_bundle()
    if not bundle.is_minimal_ready:
        raise RuntimeError("Recommender artifacts are not loaded.")

    catalog = bundle.catalog

    a_idx = anchor if isinstance(anchor, int) else find_game_index(anchor, bundle)
    if a_idx is None:
        raise KeyError(f"No game found matching {anchor!r}")
    r_idx = recommended if isinstance(recommended, int) else find_game_index(recommended, bundle)
    if r_idx is None:
        raise KeyError(f"No game found matching {recommended!r}")

    a = catalog.iloc[a_idx]
    r = catalog.iloc[r_idx]

    shared_genres = sorted(set(a["genres"]) & set(r["genres"]))
    shared_tags = set(a["tags"]) & set(r["tags"])
    tag_idf = bundle.tag_idf
    shared_tags_ranked = sorted(shared_tags, key=lambda t: -tag_idf.get(t, 0.0))[:8]

    a_vec = bundle.tfidf[a_idx].toarray().ravel()
    r_vec = bundle.tfidf[r_idx].toarray().ravel()
    contrib = a_vec * r_vec
    top_token_idx = np.argsort(-contrib)[:top_k_tokens]
    top_tokens = [
        (str(bundle.feature_names[i]), float(contrib[i])) for i in top_token_idx if contrib[i] > 0
    ]

    sim_lsa = float(bundle.lsa_norm[a_idx] @ bundle.lsa_norm[r_idx])
    sim_txt = float(cosine_similarity(bundle.tfidf[a_idx], bundle.tfidf[r_idx])[0, 0])

    return {
        "anchor": str(a["name"]),
        "recommended": str(r["name"]),
        "lsa_sim": round(sim_lsa, 3),
        "txt_sim": round(sim_txt, 3),
        "shared_genres": shared_genres,
        "shared_tags": shared_tags_ranked,
        "top_terms": [(t, round(w, 3)) for t, w in top_tokens],
    }
