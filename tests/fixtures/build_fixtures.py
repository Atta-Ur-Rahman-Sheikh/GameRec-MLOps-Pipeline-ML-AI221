"""Build tiny fixture artifacts for CI.

Run from the repo root after the real artifacts have been produced:

    python -m tests.fixtures.build_fixtures

It loads the full `artifacts/recommender/` bundle, slices the catalog
down to ~120 popular + hand-picked famous games, re-fits a tiny
TF-IDF + SVD pipeline on that subset, and refits/redumps every model so
the resulting fixture artifacts are small enough (<5 MB total) to commit.

Tests then run against these fixtures in CI without ever touching the
real, multi-hundred-MB artifacts.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import normalize
from xgboost import XGBRegressor

from app.core.config import settings
from app.services._text import build_query_text, to_tokens

# A few hand-picked titles we want present so tests can reference them by name.
FAMOUS_TITLES = [
    "Hollow Knight", "Hades", "Stardew Valley", "Dark Souls III",
    "Counter-Strike", "Half-Life 2", "Portal 2", "Terraria",
    "Celeste", "The Witcher 3: Wild Hunt", "Elden Ring", "Cuphead",
    "Among Us", "Minecraft", "Disco Elysium",
]

OUT_DIR = Path(__file__).resolve().parent / "artifacts"
N_TARGET = 120
N_LATENT_FIXTURE = 32
TFIDF_MAX_FEATURES = 4000


# ---------------------------------------------------------------- helpers

def _player_types_rules_default() -> dict:
    return {
        "Explorer": {"tags": ["Open World", "Exploration", "Sandbox", "Adventure"]},
        "Narrative Nerd": {"tags": ["Story Rich", "Visual Novel", "Choices Matter"]},
        "Tinkerer": {"tags": ["Crafting", "Building", "Sandbox"], "genres": ["Simulation"]},
        "Trophy Hunter": {"all_categories": ["Steam Achievements", "Steam Trading Cards"]},
        "Thrill-Seeker": {"tags": ["Horror", "Survival Horror", "Gore", "FPS"]},
        "Grinder": {"tags": ["MMORPG", "Loot", "Procedural Generation"],
                    "compound_rpg": ["Loot", "Procedural Generation", "Open World"]},
        "Speedrunner": {"tags": ["Precision Platformer", "Time Attack"],
                        "compound_difficult": ["Platformer", "Arcade"]},
        "Competitor": {"tags": ["Online PvP", "Competitive", "PvP", "MOBA", "Fighting"]},
    }


def _row_to_label(row, ptype: str, rules: dict) -> int:
    rule = rules[ptype]
    tag_set = set(row["tags"]) if isinstance(row["tags"], list) else set()
    genre_set = set(row["genres"]) if isinstance(row["genres"], list) else set()
    cat_set = set(row["categories"]) if isinstance(row["categories"], list) else set()

    if rule.get("tags") and tag_set & set(rule["tags"]):
        return 1
    if rule.get("genres") and genre_set & set(rule["genres"]):
        return 1
    if rule.get("all_categories") and set(rule["all_categories"]).issubset(cat_set):
        return 1
    if ptype == "Grinder" and "RPG" in genre_set and tag_set & set(rule.get("compound_rpg", [])):
        return 1
    if ptype == "Speedrunner" and "Difficult" in tag_set and tag_set & set(rule.get("compound_difficult", [])):
        return 1
    return 0


def _build_text_blob(row) -> str:
    genres = to_tokens(row["genres"])
    tags = to_tokens(row["tags"])
    cats = to_tokens(row["categories"])
    desc = (row.get("description") or "")[:500].lower()
    return " ".join(tags * 4 + genres * 3 + cats * 2 + [desc])


def _synthetic_catalog() -> pd.DataFrame:
    """Fallback mini-catalog when real pickles are unreadable across envs."""
    rows = [
        {
            "name": title,
            "key": "".join(ch for ch in title.lower() if ch.isalnum()),
            "released_rawg": f"{2015 + (i % 10)}-{(i % 12) + 1:02d}-15",
            "released_steam": f"{2015 + (i % 10)}-{(i % 12) + 1:02d}-15",
            "genres": (["RPG", "Indie"] if i % 5 == 0 else
                       ["Action", "Adventure"] if i % 3 == 0 else
                       ["Simulation", "Strategy"] if i % 2 == 0 else
                       ["Shooter", "Action"]),
            "tags": (["Story Rich", "Open World", "Singleplayer"] if i % 5 == 0 else
                     ["Roguelike", "Difficult", "Indie"] if i % 3 == 0 else
                     ["Multiplayer", "Online PvP", "Competitive"] if i % 2 == 0 else
                     ["Horror", "Survival Horror", "Atmospheric"]),
            "categories": (["Steam Achievements", "Steam Trading Cards"]
                           if i % 2 == 0 else ["Single-player"]),
            "platforms": ["PC", "Windows"],
            "description": f"{title} synthetic fixture description for CI tests.",
            "popularity": float(3.4 + (i % 10) * 0.12),
            "rating": float(3.2 + (i % 10) * 0.15),
        }
        for i, title in enumerate(FAMOUS_TITLES)
    ]
    for i in range(30):
        rows.append({
            "name": f"Fixture Game {i}",
            "key": f"fixturegame{i}",
            "released_rawg": f"{2014 + (i % 11)}-{(i % 12) + 1:02d}-10",
            "released_steam": f"{2014 + (i % 11)}-{(i % 12) + 1:02d}-10",
            "genres": ["Indie", "Adventure"] if i % 2 else ["Action", "RPG"],
            "tags": ["Indie", "Singleplayer", "Story Rich"] if i % 2 else
                    ["Multiplayer", "PvP", "Competitive"],
            "categories": ["Steam Achievements"],
            "platforms": ["PC", "Windows"],
            "description": "Additional synthetic fixture row.",
            "popularity": float(3.0 + (i % 12) * 0.1),
            "rating": float(3.0 + (i % 12) * 0.11),
        })
    return pd.DataFrame(rows)


def _synthetic_catalog() -> pd.DataFrame:
    """Fallback mini-catalog when real pickles are unreadable across envs."""
    rows = [
        {
            "name": title,
            "key": "".join(ch for ch in title.lower() if ch.isalnum()),
            "released_rawg": f"{2015 + (i % 10)}-{(i % 12) + 1:02d}-15",
            "released_steam": f"{2015 + (i % 10)}-{(i % 12) + 1:02d}-15",
            "genres": (["RPG", "Indie"] if i % 5 == 0 else
                       ["Action", "Adventure"] if i % 3 == 0 else
                       ["Simulation", "Strategy"] if i % 2 == 0 else
                       ["Shooter", "Action"]),
            "tags": (["Story Rich", "Open World", "Singleplayer"] if i % 5 == 0 else
                     ["Roguelike", "Difficult", "Indie"] if i % 3 == 0 else
                     ["Multiplayer", "Online PvP", "Competitive"] if i % 2 == 0 else
                     ["Horror", "Survival Horror", "Atmospheric"]),
            "categories": (["Steam Achievements", "Steam Trading Cards"]
                           if i % 2 == 0 else ["Single-player"]),
            "platforms": ["PC", "Windows"],
            "description": f"{title} synthetic fixture description for CI tests.",
            "popularity": float(3.4 + (i % 10) * 0.12),
            "rating": float(3.2 + (i % 10) * 0.15),
        }
        for i, title in enumerate(FAMOUS_TITLES)
    ]
    # Add a few extra rows so clustering/classification have enough variety.
    for i in range(30):
        rows.append({
            "name": f"Fixture Game {i}",
            "key": f"fixturegame{i}",
            "released_rawg": f"{2014 + (i % 11)}-{(i % 12) + 1:02d}-10",
            "released_steam": f"{2014 + (i % 11)}-{(i % 12) + 1:02d}-10",
            "genres": ["Indie", "Adventure"] if i % 2 else ["Action", "RPG"],
            "tags": ["Indie", "Singleplayer", "Story Rich"] if i % 2 else
                    ["Multiplayer", "PvP", "Competitive"],
            "categories": ["Steam Achievements"],
            "platforms": ["PC", "Windows"],
            "description": "Additional synthetic fixture row.",
            "popularity": float(3.0 + (i % 12) * 0.1),
            "rating": float(3.0 + (i % 12) * 0.11),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- pipeline

def main():
    src = settings.artifacts_dir
    if not src.exists():
        raise SystemExit(f"Real artifacts dir not found at {src}; build them first.")

    print(f"Loading real artifacts from {src} ...")
    catalog_path = src / "catalog.parquet"
    if not catalog_path.exists():
        catalog_path = src / "catalog.pkl"
    try:
        catalog = (pd.read_parquet(catalog_path) if catalog_path.suffix == ".parquet"
                   else pd.read_pickle(catalog_path))
        print(f"  full catalog: {len(catalog):,} games")
    except Exception as exc:  # noqa: BLE001
        print(f"  failed to read real catalog ({type(exc).__name__}); using synthetic fallback")
        catalog = _synthetic_catalog()
        print(f"  synthetic catalog: {len(catalog):,} games")

    # Choose the subset: top by popularity + any famous titles we can find.
    famous_idx = []
    for title in FAMOUS_TITLES:
        hits = catalog.index[catalog["name"].str.lower() == title.lower()]
        if not len(hits):
            hits = catalog.index[catalog["name"].str.lower().str.contains(title.lower(), regex=False)]
        if len(hits):
            famous_idx.append(int(hits[0]))

    pop_top = catalog.nlargest(N_TARGET, "popularity").index.tolist()
    keep = sorted(set(pop_top) | set(famous_idx))
    sub = catalog.loc[keep].reset_index(drop=True).copy()
    print(f"  fixture subset: {len(sub)} games "
          f"({len(famous_idx)} famous + top-{len(pop_top)} popular)")

    # Re-fit a tiny TF-IDF + SVD on the subset.
    sub["text_blob"] = sub.apply(_build_text_blob, axis=1)
    vectorizer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=1,
        sublinear_tf=True,
    )
    tfidf = vectorizer.fit_transform(sub["text_blob"].values)
    print(f"  tfidf: {tfidf.shape}")

    svd = TruncatedSVD(n_components=N_LATENT_FIXTURE, random_state=42)
    lsa = svd.fit_transform(tfidf)
    lsa_norm = normalize(lsa).astype(np.float32)
    print(f"  lsa: {lsa_norm.shape}")

    pop_raw = sub["popularity"].to_numpy(dtype=np.float32)
    pop_norm = ((pop_raw - pop_raw.min()) / (pop_raw.max() - pop_raw.min() + 1e-9)).astype(np.float32)

    # Player-type weak labels + tiny OvR LR.
    rules = _player_types_rules_default()
    label_names = list(rules.keys())
    y_weak = np.zeros((len(sub), len(label_names)), dtype=np.int8)
    for j, ptype in enumerate(label_names):
        y_weak[:, j] = sub.apply(lambda r, p=ptype: _row_to_label(r, p, rules), axis=1).to_numpy()

    # Make sure every label has at least one positive AND one negative
    # (otherwise LogisticRegression can't fit). Drop dead labels and
    # synthesise one positive for any nearly-empty label.
    keep_labels = []
    for j, ptype in enumerate(label_names):
        n_pos = int(y_weak[:, j].sum())
        if 0 < n_pos < len(sub):
            keep_labels.append(j)
    if len(keep_labels) < len(label_names):
        label_names = [label_names[j] for j in keep_labels]
        y_weak = y_weak[:, keep_labels]

    player_clf = OneVsRestClassifier(
        LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear"),
        n_jobs=1,
    )
    player_clf.fit(lsa_norm, y_weak)
    print(f"  player_clf labels: {label_names}")

    # Tiny XGBoost popularity regressor (LSA + year + 12 metadata flags).
    years = pd.to_datetime(sub["released_rawg"], errors="coerce").dt.year
    years = years.fillna(pd.to_datetime(sub["released_steam"], errors="coerce").dt.year)
    median_year = float(np.nanmedian(years))
    years = years.fillna(median_year).clip(lower=1990, upper=2026).to_numpy()
    year_feat = ((years - 2010.0) / 10.0).astype(np.float32).reshape(-1, 1)

    def _has_any(values, items):
        s = set(items)
        return np.array([bool(set(v) & s) for v in values], dtype=np.int8)

    extras = np.column_stack([
        sub["tags"].apply(len),
        sub["genres"].apply(len),
        sub["categories"].apply(len),
        sub["platforms"].apply(len),
        sub["description"].fillna("").str.len() / 1000.0,
        _has_any(sub["tags"], ["Multiplayer", "Online PvP", "PvP", "Online Co-Op"]),
        _has_any(sub["tags"], ["Singleplayer"]),
        _has_any(sub["genres"], ["Indie"]),
        _has_any(sub["categories"], ["Steam Achievements"]),
        _has_any(sub["categories"], ["Steam Trading Cards"]),
        _has_any(sub["tags"], ["Early Access"]),
        _has_any(sub["tags"], ["VR"]),
    ]).astype(np.float32)

    X_reg = np.hstack([lsa_norm, year_feat, extras]).astype(np.float32)
    y_reg = pop_raw

    xgb = XGBRegressor(
        n_estimators=200, learning_rate=0.05, max_depth=4,
        subsample=0.85, colsample_bytree=0.85,
        objective="reg:squarederror", tree_method="hist",
        random_state=42, n_jobs=1,
    )
    xgb.fit(X_reg, y_reg)
    print(f"  popularity regressor fit on {X_reg.shape[1]} features")

    # KMeans clustering (k=4 for the tiny subset).
    best_k = min(4, max(2, len(sub) // 20))
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=5)
    kmeans.fit(lsa_norm)
    sub["cluster_id"] = kmeans.labels_

    cluster_cards = []
    for cid in sorted(np.unique(kmeans.labels_)):
        cmask = sub["cluster_id"] == cid
        cgames = sub[cmask]
        # Quickly find distinctive tags by raw frequency (good enough for fixture).
        tag_counts: dict[str, int] = {}
        for ts in cgames["tags"]:
            for t in ts:
                tag_counts[t] = tag_counts.get(t, 0) + 1
        top_tags = sorted(tag_counts.items(), key=lambda kv: -kv[1])[:5]
        auto_name = " / ".join(t for t, _ in top_tags[:2]) or f"cluster_{cid}"
        cluster_cards.append({
            "cluster_id": int(cid),
            "auto_name": auto_name,
            "size": int(cmask.sum()),
            "avg_popularity": round(float(cgames["popularity"].mean()), 3),
            "top_genres": [],
            "distinctive_tags": [
                {"tag": t, "lift": 1.0, "count": int(c)} for t, c in top_tags
            ],
            "examples": cgames.nlargest(3, "popularity")["name"].tolist(),
        })
    cluster_names = {c["cluster_id"]: c["auto_name"] for c in cluster_cards}

    # Seasonality: real grids over the subset (small but consistent shape).
    rdt = pd.to_datetime(sub["released_rawg"], errors="coerce")
    rdt = rdt.fillna(pd.to_datetime(sub["released_steam"], errors="coerce"))
    sub["release_year"] = rdt.dt.year
    sub["release_month"] = rdt.dt.month
    sub_dated = sub.dropna(subset=["release_year", "release_month"]).copy()
    sub_dated["release_year"] = sub_dated["release_year"].astype(int)
    sub_dated["release_month"] = sub_dated["release_month"].astype(int)
    year_min = int(sub_dated["release_year"].min()) if len(sub_dated) else 2014
    year_max = int(sub_dated["release_year"].max()) if len(sub_dated) else 2024

    def _theme_block(filter_fn) -> dict:
        df = sub_dated[sub_dated.apply(filter_fn, axis=1)]
        monthly = (df.groupby("release_month").size()
                   .reindex(range(1, 13), fill_value=0).to_numpy().astype(float))
        avg = monthly  # already monthly counts in window
        idx = (avg / avg.mean()) if avg.mean() > 0 else np.ones(12)
        return {
            "monthly_avg": [round(float(v), 3) for v in avg],
            "seasonal_index": [round(float(v), 3) for v in idx],
            "n_games": int(len(df)),
        }

    seasonality = {
        "window": {"year_min": year_min, "year_max": year_max},
        "test_year": year_max,
        "themes": {
            "Horror": _theme_block(lambda r: bool(set(r["tags"]) & {"Horror", "Survival Horror"})),
            "RPG": _theme_block(lambda r: "RPG" in r["genres"]),
            "Strategy": _theme_block(lambda r: "Strategy" in r["genres"]),
        },
        "forecast_metrics": [],
    }

    # ----------------------------------------------------------- write

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    try:
        sub.to_parquet(OUT_DIR / "catalog.parquet", index=False)
    except (ImportError, ValueError) as exc:
        # No parquet engine available on this machine; pickle is fine for fixtures.
        print(f"  parquet unavailable ({type(exc).__name__}); falling back to pickle")
        sub.to_pickle(OUT_DIR / "catalog.pkl")
    joblib.dump(vectorizer, OUT_DIR / "tfidf_vectorizer.joblib", compress=3)
    sp.save_npz(OUT_DIR / "tfidf_matrix.npz", tfidf)
    joblib.dump(svd, OUT_DIR / "svd.joblib", compress=3)
    np.save(OUT_DIR / "lsa_matrix.npy", lsa_norm)
    np.save(OUT_DIR / "popularity.npy", pop_norm)
    joblib.dump({"clf": player_clf, "labels": label_names},
                OUT_DIR / "player_type_classifier.joblib", compress=3)
    (OUT_DIR / "player_types_rules.json").write_text(
        json.dumps(rules, indent=2), encoding="utf-8")

    joblib.dump({
        "model": xgb,
        "model_name": "XGBoost",
        "n_lsa": N_LATENT_FIXTURE,
        "year_centre": 2010.0,
        "year_scale": 10.0,
        "median_year": median_year,
        "extra_feature_names": [
            "n_tags", "n_genres", "n_categories", "n_platforms", "desc_length",
            "has_multiplayer", "has_singleplayer", "is_indie",
            "has_achievements", "has_trading_cards", "has_early_access", "has_vr",
        ],
    }, OUT_DIR / "popularity_regressor.joblib", compress=3)

    joblib.dump({"model": kmeans, "k": best_k, "names": cluster_names},
                OUT_DIR / "kmeans_clusters.joblib", compress=3)
    (OUT_DIR / "cluster_cards.json").write_text(
        json.dumps(cluster_cards, indent=2), encoding="utf-8")
    (OUT_DIR / "seasonality.json").write_text(
        json.dumps(seasonality, indent=2), encoding="utf-8")

    total = sum(p.stat().st_size for p in OUT_DIR.iterdir())
    print(f"\nWrote {len(list(OUT_DIR.iterdir()))} fixture files to {OUT_DIR}")
    print(f"Total size: {total / 1024:.1f} KB")
    for p in sorted(OUT_DIR.iterdir()):
        print(f"  {p.name:<35} {p.stat().st_size / 1024:>7.1f} KB")


if __name__ == "__main__":
    main()
