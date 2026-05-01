"""Hidden-genre cluster inference.

Ported from `Game_Recommender_Simple.ipynb` cells 52 and 56.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from app.core.artifacts import ArtifactBundle, get_bundle

log = logging.getLogger("gamerec.clusters")


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


def build_cluster_map(
    max_points_total: int = 420,
    min_points_cluster: int = 6,
    bundle: ArtifactBundle | None = None,
) -> dict[str, Any]:
    """PCA(2) on LSA rows; subsample recognizable games per cluster for the scatter plot."""
    bundle = bundle or get_bundle()
    catalog = bundle.catalog
    mat = bundle.lsa_norm

    if catalog is None or mat is None:
        raise RuntimeError("Catalog and LSA matrix are required for the cluster map.")

    catalog = catalog.reset_index(drop=True)
    lsa_all = np.asarray(mat, dtype=np.float64)
    n_catalog, n_mat = len(catalog), len(lsa_all)
    if n_catalog != n_mat:
        n_use = min(n_catalog, n_mat)
        log.warning(
            "cluster map: catalog rows (%s) != LSA rows (%s); using first %s rows (positional align).",
            n_catalog,
            n_mat,
            n_use,
        )
        catalog = catalog.iloc[:n_use].copy()
        lsa_all = lsa_all[:n_use]

    min_valid = 24
    kmeans = bundle.kmeans

    if "cluster_id" in catalog.columns:
        cid_raw = (
            pd.to_numeric(catalog["cluster_id"], errors="coerce")
            .fillna(-1)
            .to_numpy(dtype=np.int64)
        )
        valid_mask = cid_raw >= 0
    else:
        cid_raw = np.full(len(catalog), -1, dtype=np.int64)
        valid_mask = np.zeros(len(catalog), dtype=bool)

    if int(valid_mask.sum()) >= min_valid:
        ix = np.flatnonzero(valid_mask)
        X = lsa_all[ix]
        cid_eff = cid_raw[ix]
        cat_valid = catalog.iloc[ix].reset_index(drop=True)
    elif kmeans is not None:
        log.warning(
            "cluster map: only %s rows with usable cluster_id; re-predicting with kmeans for visualization.",
            int(valid_mask.sum()),
        )
        X = lsa_all
        cid_eff = np.asarray(kmeans.predict(lsa_all.astype(np.float64)), dtype=np.int64)
        cat_valid = catalog.copy()
    else:
        raise RuntimeError(
            "Not enough clustered games for a visualization, and no kmeans model is available to infer labels."
        )

    if len(X) < min_valid:
        raise RuntimeError("Not enough clustered games for a visualization.")

    n_feat = X.shape[1]
    if n_feat < 2:
        raise RuntimeError("Latent vectors need at least 2 dimensions for PCA.")

    pca_fit = PCA(n_components=2, random_state=42)
    if len(X) > 14_000:
        rng = np.random.default_rng(42)
        sample_ix = rng.choice(len(X), size=14_000, replace=False)
        pca_fit.fit(X[sample_ix])
        coords_norm = pca_fit.transform(X)
    else:
        coords_norm = pca_fit.fit_transform(X)

    evr = tuple(float(round(v, 4)) for v in pca_fit.explained_variance_ratio_[:2])
    xy_min = coords_norm.min(axis=0)
    xy_span = np.ptp(coords_norm, axis=0)
    span = float(max(xy_span.max(), 1e-9))
    scaled = ((coords_norm - xy_min) / span) * 90.0 + 5.0

    uniq = sorted(int(x) for x in np.unique(cid_eff))
    name_lookup = {int(c["cluster_id"]): str(c["auto_name"]) for c in bundle.cluster_cards}
    sizes = Counter(int(x) for x in cid_eff)

    rng = np.random.default_rng(7)
    cap_per = max(
        min_points_cluster,
        int(max_points_total / max(len(uniq), 1)),
    )

    points_out: list[dict[str, Any]] = []
    for cid in uniq:
        cluster_mask_eff = cid_eff == cid
        idx_local = np.flatnonzero(cluster_mask_eff)
        k = min(int(cap_per), max(min_points_cluster, len(idx_local)), len(idx_local))
        if len(idx_local) <= k:
            pick = idx_local
        else:
            pop_c = cat_valid.iloc[idx_local]["popularity"].to_numpy(dtype=np.float64)
            heavy = idx_local[np.argsort(-pop_c)[: max(k // 2, 4)]]
            rest_pool = np.setdiff1d(idx_local, heavy, assume_unique=False)
            n_rest = max(0, k - len(heavy))
            if n_rest <= 0 or len(rest_pool) == 0:
                pick = heavy[:k]
            else:
                filler = rng.choice(rest_pool, size=min(n_rest, len(rest_pool)), replace=False)
                pick = np.unique(np.concatenate([heavy, filler]))

        for li in pick[:k]:
            row = cat_valid.iloc[int(li)]
            xy = scaled[int(li)]
            points_out.append(
                {
                    "name": str(row["name"]),
                    "cluster_id": int(cid),
                    "x": round(float(xy[0]), 3),
                    "y": round(float(xy[1]), 3),
                    "popularity": round(float(row.get("popularity", 0.0)), 3),
                }
            )

    centroids_out: list[dict[str, Any]] = []
    for cid in uniq:
        sel = cid_eff == cid
        mu = scaled[sel].mean(axis=0)
        cnt = sizes.get(cid, 0)
        centroids_out.append(
            {
                "cluster_id": int(cid),
                "label": name_lookup.get(int(cid), f"Cluster {cid}"),
                "x": round(float(mu[0]), 3),
                "y": round(float(mu[1]), 3),
                "n_games": int(cnt),
            }
        )

    return {
        "method": "pca-lsa",
        "explained_variance_ratio": tuple(evr),
        "points": points_out,
        "centroids": sorted(centroids_out, key=lambda d: int(d["cluster_id"])),
    }


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
