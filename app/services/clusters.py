"""Hidden-genre cluster inference.

Ported from `Game_Recommender_Simple.ipynb` cells 52 and 56.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.core.artifacts import ArtifactBundle, get_bundle


def _count_lists(series) -> Counter:
    c: Counter = Counter()
    for lst in series:
        c.update(lst)
    return c


def cluster_distinctive_tags(
    cid: int, top_n: int = 6, min_in_cluster: int = 10, bundle: ArtifactBundle | None = None
) -> list[tuple[str, float, int]]:
    """Return tags most over-represented in cluster `cid` vs the catalog."""
    bundle = bundle or get_bundle()
    catalog = bundle.catalog
    if catalog is None or "cluster_id" not in catalog.columns:
        return []

    sub = catalog[catalog["cluster_id"] == cid]
    if sub.empty:
        return []
    n_sub = len(sub)
    n_total = len(catalog)
    in_count = _count_lists(sub["tags"])
    global_counts = bundle.global_tag_count or _count_lists(catalog["tags"])

    out: list[tuple[str, float, int]] = []
    for tag, cnt in in_count.items():
        if cnt < min_in_cluster:
            continue
        p_in = cnt / n_sub
        p_total = global_counts.get(tag, 0) / n_total if n_total else 0
        lift = p_in / p_total if p_total > 0 else 0.0
        out.append((tag, lift, cnt))
    out.sort(key=lambda x: -x[1])
    return out[:top_n]


def list_clusters(bundle: ArtifactBundle | None = None) -> list[dict[str, Any]]:
    """Return the (already-built) cluster cards."""
    bundle = bundle or get_bundle()
    return list(bundle.cluster_cards)


def discover_hidden_genre(
    game_query: str, n_similar: int = 8, bundle: ArtifactBundle | None = None
) -> dict[str, Any]:
    """Find the latent genre of a game and surface similar titles."""
    bundle = bundle or get_bundle()
    catalog = bundle.catalog
    if catalog is None or "cluster_id" not in catalog.columns:
        raise RuntimeError("Clustering artifacts are not loaded.")

    q = (game_query or "").lower()
    if not q:
        raise KeyError("Empty game query.")

    hit = catalog[catalog["name"].str.lower() == q]
    if hit.empty:
        hit = catalog[catalog["name"].str.lower().str.contains(q, regex=False, na=False)]
    if hit.empty:
        raise KeyError(f"No game matching {game_query!r}")

    g = hit.iloc[0]
    cid = int(g["cluster_id"])
    cluster_size = int((catalog["cluster_id"] == cid).sum())

    distinctive = cluster_distinctive_tags(cid, top_n=6, bundle=bundle)
    pool = catalog[(catalog["cluster_id"] == cid) & (catalog["name"] != g["name"])]
    top = pool.nlargest(n_similar, "popularity")

    return {
        "game": str(g["name"]),
        "steam_genres": list(g["genres"]),
        "cluster_id": cid,
        "hidden_genre_name": bundle.cluster_names.get(cid, f"cluster_{cid}"),
        "cluster_size": cluster_size,
        "distinctive_tags": [
            {"tag": tag, "lift": round(lift, 3), "count": int(cnt)}
            for tag, lift, cnt in distinctive
        ],
        "similar_games": [
            {
                "name": row["name"],
                "popularity": round(float(row["popularity"]), 3),
            }
            for _, row in top.iterrows()
        ],
    }
