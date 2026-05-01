"""Singleton artifact bundle used by every service module.

Loaded once at FastAPI startup (via the lifespan handler in `app.main`),
or lazily on first access in scripts and tests. Each artifact is treated
as optional so the API can still serve a useful subset if the operator
hasn't yet rebuilt the clustering or seasonality outputs.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp

from app.core.config import Settings, settings

log = logging.getLogger("gamerec.artifacts")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ArtifactBundle:
    """In-memory bundle of every model/dataset the API uses at request time.

    All fields are optional: the lifespan loader logs a clear warning per
    missing artifact so the team can spot which notebook cell still needs
    to be re-run.
    """

    catalog: pd.DataFrame | None = None
    vectorizer: Any | None = None
    tfidf: sp.csr_matrix | None = None
    svd: Any | None = None
    lsa_norm: np.ndarray | None = None
    pop_norm: np.ndarray | None = None
    popularity: np.ndarray | None = None

    player_clf: Any | None = None
    player_type_names: list[str] = field(default_factory=list)
    player_types_rules: dict[str, dict[str, list[str]]] = field(default_factory=dict)

    popularity_model: Any | None = None
    popularity_meta: dict[str, Any] = field(default_factory=dict)

    kmeans: Any | None = None
    cluster_names: dict[int, str] = field(default_factory=dict)
    cluster_cards: list[dict[str, Any]] = field(default_factory=list)

    seasonality: dict[str, Any] | None = None

    # Derived helpers (built once after load):
    feature_names: np.ndarray | None = None
    tag_idf: dict[str, float] = field(default_factory=dict)
    global_tag_count: Counter = field(default_factory=Counter)
    content_richness: np.ndarray | None = None
    key_to_idx: dict[str, int] = field(default_factory=dict)

    # Status:
    missing: list[str] = field(default_factory=list)

    @property
    def is_minimal_ready(self) -> bool:
        """True once recommender artifacts (catalog + tfidf + svd + lsa) are loaded."""
        return all(
            x is not None
            for x in [
                self.catalog,
                self.vectorizer,
                self.tfidf,
                self.svd,
                self.lsa_norm,
                self.pop_norm,
            ]
        )


_BUNDLE: ArtifactBundle | None = None
_LOCK = Lock()


# --------------------------------------------------------------------- helpers


def _load_or_warn(loader, path: Path, missing: list[str], label: str):
    if not path.exists():
        log.warning("artifact missing: %s -> expected at %s", label, path)
        missing.append(label)
        return None
    try:
        return loader(path)
    except Exception as exc:  # noqa: BLE001
        log.error("failed to load %s from %s: %s", label, path, exc)
        missing.append(label)
        return None


def _load_catalog(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_pickle(path)


def _enrich_catalog_from_rawg(catalog: pd.DataFrame, project_root: Path) -> pd.DataFrame:
    """Attach RAWG cover+metadata columns if they are missing in saved catalog."""
    needed_cols = {"background_image", "rawg_slug", "released_rawg", "metacritic"}
    if needed_cols.issubset(set(catalog.columns)):
        return catalog

    rawg_path = project_root / "datasets" / "RAWG Dataset" / "jsonl" / "rawg_data.jsonl"
    if not rawg_path.exists():
        return catalog

    by_key: dict[str, dict[str, Any]] = {}
    with rawg_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = str(row.get("name", "")).strip().lower()
            if not name:
                continue
            by_key[name] = {
                "background_image": row.get("background_image"),
                "rawg_slug": row.get("slug"),
                "released_rawg": row.get("released"),
                "metacritic": row.get("metacritic"),
            }

    if not by_key:
        return catalog

    out = catalog.copy()
    key_series = out["name"].astype(str).str.strip().str.lower()
    rawg_meta = key_series.map(by_key)

    def pick(col: str):
        return rawg_meta.map(lambda m: m.get(col) if isinstance(m, dict) else None)

    if "background_image" not in out.columns:
        out["background_image"] = pick("background_image")
    else:
        out["background_image"] = out["background_image"].where(
            out["background_image"].notna(), pick("background_image")
        )

    if "rawg_slug" not in out.columns:
        out["rawg_slug"] = pick("rawg_slug")
    else:
        out["rawg_slug"] = out["rawg_slug"].where(out["rawg_slug"].notna(), pick("rawg_slug"))

    if "released_rawg" not in out.columns:
        out["released_rawg"] = pick("released_rawg")

    if "metacritic" not in out.columns:
        out["metacritic"] = pick("metacritic")

    return out


def _build_tag_idf(catalog: pd.DataFrame) -> dict[str, float]:
    tag_doc_freq: dict[str, int] = {}
    for tags_list in catalog["tags"].values:
        for t in set(tags_list):
            tag_doc_freq[t] = tag_doc_freq.get(t, 0) + 1
    n_docs = len(catalog)
    return {t: float(np.log((1 + n_docs) / (1 + c)) + 1.0) for t, c in tag_doc_freq.items()}


def _global_tag_counts(catalog: pd.DataFrame) -> Counter:
    c: Counter = Counter()
    for tags in catalog["tags"]:
        c.update(tags)
    return c


def _content_richness(catalog: pd.DataFrame) -> np.ndarray:
    n_tags = catalog["tags"].apply(len).to_numpy()
    return np.minimum(1.0, n_tags / 8.0).astype(np.float32)


def _normalise_popularity(popularity: np.ndarray) -> np.ndarray:
    return ((popularity - popularity.min()) / (popularity.max() - popularity.min() + 1e-9)).astype(
        np.float32
    )


# --------------------------------------------------------------------- public API


def load_bundle(cfg: Settings | None = None, force: bool = False) -> ArtifactBundle:
    """Load all artifacts on first call; return the cached bundle thereafter."""
    global _BUNDLE
    cfg = cfg or settings
    with _LOCK:
        if _BUNDLE is not None and not force:
            return _BUNDLE

        adir: Path = cfg.artifacts_dir
        log.info("loading artifacts from %s", adir)
        bundle = ArtifactBundle()

        # Catalog: prefer parquet, fall back to pickle (the notebook saves either).
        for fname in ("catalog.parquet", "catalog.pkl"):
            cpath = adir / fname
            if cpath.exists():
                bundle.catalog = _load_or_warn(_load_catalog, cpath, bundle.missing, "catalog")
                break
        if bundle.catalog is None:
            bundle.missing.append("catalog")
            log.warning("artifact missing: catalog -> expected at %s/catalog.{parquet,pkl}", adir)
        else:
            bundle.catalog = _enrich_catalog_from_rawg(bundle.catalog, PROJECT_ROOT)

        bundle.vectorizer = _load_or_warn(
            joblib.load, adir / "tfidf_vectorizer.joblib", bundle.missing, "tfidf_vectorizer"
        )
        bundle.tfidf = _load_or_warn(
            sp.load_npz, adir / "tfidf_matrix.npz", bundle.missing, "tfidf_matrix"
        )
        bundle.svd = _load_or_warn(joblib.load, adir / "svd.joblib", bundle.missing, "svd")
        bundle.lsa_norm = _load_or_warn(
            np.load, adir / "lsa_matrix.npy", bundle.missing, "lsa_matrix"
        )
        bundle.pop_norm = _load_or_warn(
            np.load, adir / "popularity.npy", bundle.missing, "popularity"
        )

        # Player-type classifier (joblib bundle stores both clf + label list).
        clf_pkg = _load_or_warn(
            joblib.load,
            adir / "player_type_classifier.joblib",
            bundle.missing,
            "player_type_classifier",
        )
        if clf_pkg is not None:
            bundle.player_clf = clf_pkg.get("clf")
            bundle.player_type_names = list(clf_pkg.get("labels", []))

        rules = _load_or_warn(
            lambda p: json.loads(p.read_text(encoding="utf-8")),
            adir / "player_types_rules.json",
            bundle.missing,
            "player_types_rules",
        )
        if rules is not None:
            bundle.player_types_rules = rules

        # Popularity regressor + its feature-spec metadata.
        reg_pkg = _load_or_warn(
            joblib.load,
            adir / "popularity_regressor.joblib",
            bundle.missing,
            "popularity_regressor",
        )
        if reg_pkg is not None:
            bundle.popularity_model = reg_pkg.get("model")
            bundle.popularity_meta = {k: v for k, v in reg_pkg.items() if k != "model"}

        # KMeans + hidden-genre cards (optional).
        clu_pkg = _load_or_warn(
            joblib.load, adir / "kmeans_clusters.joblib", bundle.missing, "kmeans_clusters"
        )
        if clu_pkg is not None:
            bundle.kmeans = clu_pkg.get("model")
            raw_names = clu_pkg.get("names", {}) or {}
            bundle.cluster_names = {int(k): str(v) for k, v in raw_names.items()}

        cards = _load_or_warn(
            lambda p: json.loads(p.read_text(encoding="utf-8")),
            adir / "cluster_cards.json",
            bundle.missing,
            "cluster_cards",
        )
        if cards is not None:
            bundle.cluster_cards = cards

        # Seasonality (optional).
        season = _load_or_warn(
            lambda p: json.loads(p.read_text(encoding="utf-8")),
            adir / "seasonality.json",
            bundle.missing,
            "seasonality",
        )
        if season is not None:
            bundle.seasonality = season

        # ------------------- derived helpers (only if catalog + vectorizer exist)
        if bundle.catalog is not None and bundle.vectorizer is not None:
            bundle.feature_names = bundle.vectorizer.get_feature_names_out()
        if bundle.catalog is not None:
            bundle.tag_idf = _build_tag_idf(bundle.catalog)
            bundle.global_tag_count = _global_tag_counts(bundle.catalog)
            bundle.content_richness = _content_richness(bundle.catalog)
            bundle.key_to_idx = {k: i for i, k in enumerate(bundle.catalog["key"].values)}

            # Attach kmeans cluster_id back onto catalog (saved separately).
            if bundle.kmeans is not None and "cluster_id" not in bundle.catalog.columns:
                bundle.catalog = bundle.catalog.copy()
                # We cannot recover labels from KMeans alone unless we re-predict,
                # which requires lsa_norm.
                if bundle.lsa_norm is not None:
                    bundle.catalog["cluster_id"] = bundle.kmeans.predict(bundle.lsa_norm)

        if (
            bundle.pop_norm is None
            and bundle.catalog is not None
            and "popularity" in bundle.catalog.columns
        ):
            # Synthesise from catalog if persisted file is missing.
            pop_raw = bundle.catalog["popularity"].to_numpy(dtype=np.float32)
            bundle.popularity = pop_raw
            bundle.pop_norm = _normalise_popularity(pop_raw)

        _BUNDLE = bundle

        log.info("artifacts loaded; missing=%s", bundle.missing or "[none]")
        return bundle


def get_bundle() -> ArtifactBundle:
    """Return the cached bundle, loading it lazily if needed."""
    if _BUNDLE is None:
        return load_bundle()
    return _BUNDLE


def reset_bundle() -> None:
    """Drop the cached bundle. Used by tests to swap fixture artifacts in."""
    global _BUNDLE
    with _LOCK:
        _BUNDLE = None
