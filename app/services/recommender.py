"""Hybrid recommender services.

Ported from `Game_Recommender_Simple.ipynb` cells 14 and 16. Logic is
unchanged; only the surface is converted from "operate on globals" to
"take an `ArtifactBundle`".
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
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


def _safe_str(v: Any) -> str | None:
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:  # noqa: BLE001
        pass
    text = str(v).strip()
    return text or None


def _safe_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
        return int(v)
    except Exception:  # noqa: BLE001
        return None


def _safe_float(v: Any, default: float = 0.0, *, ndigits: int | None = None) -> float:
    try:
        if v is None or pd.isna(v):
            value = float(default)
        else:
            value = float(v)
        if not np.isfinite(value):
            value = float(default)
    except Exception:  # noqa: BLE001
        value = float(default)
    return round(value, ndigits) if ndigits is not None else value


def _optional_str_list(
    row: pd.Series,
    col: str,
    *,
    limit: int | None = None,
) -> list[str] | None:
    if col not in row.index:
        return None
    v = row.get(col)
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, np.ndarray):
        v = v.tolist()
    if not isinstance(v, (list, tuple)):
        return None
    out: list[str] = []
    for x in v:
        if x is None:
            continue
        try:
            if pd.isna(x):
                continue
        except (TypeError, ValueError):
            pass
        s = str(x).strip()
        if s:
            out.append(s)
    if limit is not None and len(out) > limit:
        out = out[:limit]
    return out or None


def _row_to_game_hit(
    row: pd.Series,
    columns: pd.Index,
    *,
    tag_limit: int | None = 24,
    category_limit: int | None = 16,
) -> dict[str, Any]:
    """Shared catalog fields for search, discover, and recommendation payloads."""
    hit: dict[str, Any] = {
        "name": row["name"],
        "popularity": _safe_float(row.get("popularity"), ndigits=3),
        "genres": list(row["genres"]),
        "platforms": list(row["platforms"]),
        "image_url": _safe_str(row.get("background_image")),
        "rawg_slug": _safe_str(row.get("rawg_slug")),
        "released_rawg": _safe_str(row.get("released_rawg")),
        "metacritic": _safe_int(row.get("metacritic")),
    }
    if "rating" in columns:
        hit["rating"] = _safe_float(row.get("rating"), default=0.0, ndigits=2)
    else:
        hit["rating"] = None

    tags = _optional_str_list(row, "tags", limit=tag_limit)
    if tags is not None:
        hit["tags"] = tags
    categories = _optional_str_list(row, "categories", limit=category_limit)
    if categories is not None:
        hit["categories"] = categories

    if "released_steam" in columns:
        rs = _safe_str(row.get("released_steam"))
        if rs:
            hit["released_steam"] = rs

    if "votes" in columns:
        votes = _safe_int(row.get("votes"))
        if votes is not None:
            hit["votes"] = votes

    if "cluster_id" in columns:
        cid = row.get("cluster_id")
        try:
            if cid is not None and not pd.isna(cid):
                hit["cluster_id"] = int(cid)
        except (TypeError, ValueError):
            pass

    if "AppID" in columns:
        aid = _safe_int(row.get("AppID"))
        if aid is not None:
            hit["steam_app_id"] = aid

    return hit


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
    cols = catalog.columns
    return [_row_to_game_hit(row, cols, tag_limit=24, category_limit=16) for _, row in hits.iterrows()]


def discover_rows(limit: int = 12, bundle: ArtifactBundle | None = None) -> dict[str, list[dict[str, Any]]]:
    """Return home-page rows tuned for discovery UX."""
    bundle = bundle or get_bundle()
    catalog = bundle.catalog
    if catalog is None or catalog.empty:
        return {
            "trending_releases": [],
            "top_rated_popularity": [],
            "hidden_gems": [],
        }

    df = catalog.copy()
    df["release_dt"] = None
    if "released_rawg" in df.columns:
        df["release_dt"] = df["released_rawg"]
    elif "released_steam" in df.columns:
        df["release_dt"] = df["released_steam"]
    df["release_dt"] = np.array(df["release_dt"], dtype=object)
    release_parsed = np.array(df["release_dt"], dtype=object)
    # pandas datetime parsing kept local to avoid global import for perf-sensitive path.
    import pandas as pd  # noqa: PLC0415

    release_series = pd.to_datetime(pd.Series(release_parsed), errors="coerce")
    df["release_ts"] = release_series
    current = pd.Timestamp.utcnow().tz_localize(None)
    recent_cutoff = current - pd.Timedelta(days=365 * 3)

    recent = df[df["release_ts"].notna() & (df["release_ts"] >= recent_cutoff)]
    if recent.empty:
        recent = df[df["release_ts"].notna()]
    trending = recent.sort_values(["popularity", "rating"], ascending=[False, False]).head(limit)

    top_rated = df.sort_values(["popularity", "rating"], ascending=[False, False]).head(limit)

    votes_col = "votes" if "votes" in df.columns else None
    if votes_col is not None:
        hidden_pool = df[df[votes_col] <= df[votes_col].quantile(0.35)]
    else:
        hidden_pool = df
    hidden_pool = hidden_pool[hidden_pool["rating"] >= hidden_pool["rating"].quantile(0.55)]
    hidden = hidden_pool.sort_values(["popularity", "rating"], ascending=[False, False]).head(limit)

    def to_hits(rows: pd.DataFrame) -> list[dict[str, Any]]:
        return [
            _row_to_game_hit(row, rows.columns, tag_limit=24, category_limit=16)
            for _, row in rows.iterrows()
        ]

    return {
        "trending_releases": to_hits(trending),
        "top_rated_popularity": to_hits(top_rated),
        "hidden_gems": to_hits(hidden),
    }


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
    cols = catalog.columns
    return [
        {
            "score": _safe_float(score[top[i]], ndigits=3),
            "lsa_sim": _safe_float(sim_lsa[top[i]], ndigits=3),
            "txt_sim": _safe_float(sim_text[top[i]], ndigits=3),
            **_row_to_game_hit(rows.iloc[i], cols, tag_limit=10, category_limit=8),
            "rating": _safe_float(rows.iloc[i].get("rating"), ndigits=2),
            "popularity": _safe_float(rows.iloc[i].get("popularity"), ndigits=2),
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
    cols = catalog.columns
    return [
        {
            "score": _safe_float(score[top[i]], ndigits=3),
            "lsa_sim": _safe_float(sim_lsa[top[i]], ndigits=3),
            "txt_sim": _safe_float(sim_text[top[i]], ndigits=3),
            **_row_to_game_hit(rows.iloc[i], cols, tag_limit=6, category_limit=8),
            "rating": _safe_float(rows.iloc[i].get("rating"), ndigits=2),
            "popularity": _safe_float(rows.iloc[i].get("popularity"), ndigits=2),
        }
        for i in range(len(top))
    ]
