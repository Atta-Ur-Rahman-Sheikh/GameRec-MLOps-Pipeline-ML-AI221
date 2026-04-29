"""Hybrid recommender services.

Ported from `Game_Recommender_Simple.ipynb` cells 14 and 16. Logic is
unchanged; only the surface is converted from "operate on globals" to
"take an `ArtifactBundle`".
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from app.core.artifacts import ArtifactBundle, get_bundle
from app.services._text import build_query_text, norm_key

# ---------------------------------------------------------------- platform aliasing

PLATFORM_ALIASES: dict[str, set[str]] = {
    "pc": {"PC", "Windows", "PC (Windows)"},
    "windows": {"PC", "Windows", "PC (Windows)"},
    "mac": {"macOS", "Mac"},
    "macos": {"macOS", "Mac"},
    "linux": {"Linux"},
    "ps4": {"PlayStation 4"},
    "ps5": {"PlayStation 5"},
    "playstation": {"PlayStation 4", "PlayStation 5", "PlayStation 3"},
    "xbox": {"Xbox One", "Xbox Series S/X", "Xbox 360"},
    "switch": {"Nintendo Switch"},
    "nintendo": {"Nintendo Switch", "Nintendo 3DS", "Wii U", "Wii"},
}


def _platform_mask(catalog, platforms: list[str] | None) -> np.ndarray:
    if not platforms:
        return np.ones(len(catalog), dtype=bool)
    wanted: set[str] = set()
    for p in platforms:
        wanted |= PLATFORM_ALIASES.get(p.lower(), {p})
    mask = np.zeros(len(catalog), dtype=bool)
    for i, plats in enumerate(catalog["platforms"].values):
        if plats and any(p in wanted for p in plats):
            mask[i] = True
    return mask


# ---------------------------------------------------------------- title -> idx


def find_game_index(title: str, bundle: ArtifactBundle | None = None) -> int | None:
    """Resolve a free-form title to a row index in `catalog`.

    Tries exact key match first, then prefix, then substring -- same
    fallback ladder as the notebook.
    """
    bundle = bundle or get_bundle()
    catalog = bundle.catalog
    if catalog is None:
        return None

    k = norm_key(title)
    if not k:
        return None
    if k in bundle.key_to_idx:
        return bundle.key_to_idx[k]

    matches = catalog.index[catalog["key"].str.startswith(k)]
    if len(matches):
        return int(matches[0])
    matches = catalog.index[catalog["key"].str.contains(k, regex=False)]
    if len(matches):
        return int(matches[0])
    return None


def search_games(
    query: str, limit: int = 10, bundle: ArtifactBundle | None = None
) -> list[dict[str, Any]]:
    """Return up to `limit` catalog rows whose name contains `query`."""
    bundle = bundle or get_bundle()
    catalog = bundle.catalog
    if catalog is None or not query:
        return []
    q = query.lower()
    mask = catalog["name"].str.lower().str.contains(q, regex=False, na=False)
    hits = catalog[mask].nlargest(limit, "popularity")
    return [
        {
            "name": row["name"],
            "popularity": round(float(row["popularity"]), 3),
            "rating": round(float(row["rating"]), 2) if "rating" in catalog.columns else None,
            "genres": list(row["genres"]),
            "platforms": list(row["platforms"]),
        }
        for _, row in hits.iterrows()
    ]


# ---------------------------------------------------------------- core scoring


def _hybrid_scores_for_anchor(
    idx: int, bundle: ArtifactBundle
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sim_text = cosine_similarity(bundle.tfidf[idx], bundle.tfidf).ravel()
    sim_lsa = bundle.lsa_norm @ bundle.lsa_norm[idx]
    return sim_lsa, sim_text, bundle.pop_norm


def recommend_similar(
    title: str,
    top_k: int = 10,
    w_lsa: float = 0.55,
    w_text: float = 0.30,
    w_pop: float = 0.15,
    min_pop: float | None = None,
    bundle: ArtifactBundle | None = None,
) -> list[dict[str, Any]]:
    """Return top_k games most similar to `title`.

    Hybrid score = w_lsa * SVD_cos + w_text * TF-IDF_cos + w_pop * popularity.
    """
    bundle = bundle or get_bundle()
    if not bundle.is_minimal_ready:
        raise RuntimeError("Recommender artifacts are not loaded.")

    idx = find_game_index(title, bundle)
    if idx is None:
        raise KeyError(f"No game found matching {title!r}")

    sim_lsa, sim_text, pop = _hybrid_scores_for_anchor(idx, bundle)
    score = w_lsa * sim_lsa + w_text * sim_text + w_pop * pop

    if min_pop is not None:
        floor = float(np.quantile(bundle.pop_norm, min_pop))
        score = np.where(bundle.pop_norm >= floor, score, -np.inf)
    score[idx] = -np.inf

    top_k = min(top_k, len(score) - 1)
    top = np.argpartition(-score, top_k)[:top_k]
    top = top[np.argsort(-score[top])]

    catalog = bundle.catalog
    rows = catalog.iloc[top]
    return [
        {
            "name": rows.iloc[i]["name"],
            "score": round(float(score[top[i]]), 3),
            "lsa_sim": round(float(sim_lsa[top[i]]), 3),
            "txt_sim": round(float(sim_text[top[i]]), 3),
            "rating": round(float(rows.iloc[i]["rating"]), 2),
            "popularity": round(float(rows.iloc[i]["popularity"]), 2),
            "genres": list(rows.iloc[i]["genres"]),
            "platforms": list(rows.iloc[i]["platforms"]),
        }
        for i in range(len(top))
    ]


def recommend_for_user(
    liked_genres: list[str] | None = None,
    liked_tags: list[str] | None = None,
    platforms: list[str] | None = None,
    top_k: int = 10,
    w_lsa: float = 0.30,
    w_text: float = 0.30,
    w_pop: float = 0.40,
    min_pop_quantile: float = 0.40,
    min_rating: float = 0.0,
    discount_below_floor: float = 0.3,
    use_content_richness: bool = True,
    bundle: ArtifactBundle | None = None,
) -> list[dict[str, Any]]:
    """Recommend games matching a user's stated preferences (cold-start)."""
    bundle = bundle or get_bundle()
    if not bundle.is_minimal_ready:
        raise RuntimeError("Recommender artifacts are not loaded.")

    if not (liked_genres or liked_tags):
        raise ValueError("Provide at least one liked genre or tag.")

    query_text = build_query_text(liked_genres, liked_tags)
    qv_tfidf = bundle.vectorizer.transform([query_text])
    qv_lsa = normalize(bundle.svd.transform(qv_tfidf)).astype(np.float32)

    sim_text = cosine_similarity(qv_tfidf, bundle.tfidf).ravel()
    sim_lsa = (bundle.lsa_norm @ qv_lsa.T).ravel()

    score = w_lsa * sim_lsa + w_text * sim_text + w_pop * bundle.pop_norm

    if use_content_richness and bundle.content_richness is not None:
        score = score * bundle.content_richness

    if min_pop_quantile > 0:
        floor = float(np.quantile(bundle.pop_norm, min_pop_quantile))
        below = bundle.pop_norm < floor
        score = np.where(below, score * discount_below_floor, score)

    catalog = bundle.catalog
    mask = _platform_mask(catalog, platforms)
    if min_rating > 0:
        mask &= catalog["rating"].to_numpy() >= min_rating
    score = np.where(mask, score, -np.inf)

    top_k = min(top_k, int(mask.sum()))
    if top_k <= 0:
        return []
    top = np.argpartition(-score, top_k)[:top_k]
    top = top[np.argsort(-score[top])]

    rows = catalog.iloc[top]
    return [
        {
            "name": rows.iloc[i]["name"],
            "score": round(float(score[top[i]]), 3),
            "lsa_sim": round(float(sim_lsa[top[i]]), 3),
            "txt_sim": round(float(sim_text[top[i]]), 3),
            "rating": round(float(rows.iloc[i]["rating"]), 2),
            "popularity": round(float(rows.iloc[i]["popularity"]), 2),
            "genres": list(rows.iloc[i]["genres"]),
            "tags": list(rows.iloc[i]["tags"])[:6],
            "platforms": list(rows.iloc[i]["platforms"]),
        }
        for i in range(len(top))
    ]
