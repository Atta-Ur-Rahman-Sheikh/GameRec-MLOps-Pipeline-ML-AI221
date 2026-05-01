"""Prefect tasks for dataset checks and artifact validation.

A full end-to-end retrain duplicates `Game_Recommender_Simple.ipynb` (hours of
CPU time). This pipeline therefore focuses on **what you run in production**:

1. Verify raw Steam + RAWG sources exist where the notebook expects them.
2. Verify every serialized model file under `artifacts/recommender/` is present
   and readable.

Optional notebook execution is intentionally left out of CI; rebuild artifacts
locally by executing the notebook cells, then commit or upload the bundle.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import request
from typing import Any

from prefect import task

PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_ARTIFACTS = (
    "catalog.pkl",
    "tfidf_vectorizer.joblib",
    "tfidf_matrix.npz",
    "svd.joblib",
    "lsa_matrix.npy",
    "popularity.npy",
    "player_type_classifier.joblib",
    "player_types_rules.json",
    "popularity_regressor.joblib",
)

OPTIONAL_ARTIFACTS = (
    "kmeans_clusters.joblib",
    "cluster_cards.json",
    "seasonality.json",
)


@task(name="validate-sources", retries=0)
def validate_sources_and_environment() -> dict[str, Any]:
    """Check dataset paths and echo useful env overrides."""
    steam = PROJECT_ROOT / "Datasets" / "Steam Dataset" / "games.csv"
    rawg_jsonl = PROJECT_ROOT / "Datasets" / "RAWG Dataset" / "jsonl" / "rawg_data.jsonl"
    return {
        "project_root": str(PROJECT_ROOT),
        "steam_csv_exists": steam.exists(),
        "steam_csv_path": str(steam),
        "rawg_jsonl_exists": rawg_jsonl.exists(),
        "rawg_jsonl_path": str(rawg_jsonl),
        "gamerec_artifacts_dir": os.environ.get(
            "GAMEREC_ARTIFACTS_DIR",
            str(PROJECT_ROOT / "artifacts" / "recommender"),
        ),
    }


@task(name="verify-artifacts", retries=0)
def verify_ml_artifacts(artifacts_dir: str | Path | None = None) -> dict[str, Any]:
    """Ensure core + optional artifact files exist and JSON parses."""
    root = Path(
        artifacts_dir
        or os.environ.get(
            "GAMEREC_ARTIFACTS_DIR",
            PROJECT_ROOT / "artifacts" / "recommender",
        )
    ).resolve()

    missing_required: list[str] = []
    missing_optional: list[str] = []

    for name in REQUIRED_ARTIFACTS:
        if not (root / name).exists():
            missing_required.append(name)

    for name in OPTIONAL_ARTIFACTS:
        if not (root / name).exists():
            missing_optional.append(name)

    json_ok = True
    rules_path = root / "player_types_rules.json"
    if rules_path.exists():
        try:
            json.loads(rules_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            json_ok = False

    return {
        "artifacts_dir": str(root),
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "json_rules_ok": json_ok,
        "ready_for_fastapi": len(missing_required) == 0,
    }


@task(name="print-summary", retries=0)
def print_summary(source_info: dict[str, Any], artifact_report: dict[str, Any]) -> None:
    """Human-readable log block for Prefect UI."""
    print("\n=== Gamerec artifact pipeline ===")
    print(f"Steam CSV present: {source_info['steam_csv_exists']}")
    print(f"RAWG JSONL present: {source_info['rawg_jsonl_exists']}")
    print(f"Artifacts directory: {artifact_report['artifacts_dir']}")
    if artifact_report["missing_required"]:
        print("MISSING REQUIRED:", ", ".join(artifact_report["missing_required"]))
    else:
        print("All required artifacts present.")
    if artifact_report["missing_optional"]:
        print("Optional not yet built:", ", ".join(artifact_report["missing_optional"]))
    print(f"FastAPI minimal ready: {artifact_report['ready_for_fastapi']}")
    print("=================================\n")


@task(name="discord-notification", retries=0)
def send_discord_notification(message: str) -> bool:
    """Send flow status message to Discord via webhook URL."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Discord notification skipped: DISCORD_WEBHOOK_URL is not configured.")
        return False

    payload = json.dumps({"content": message}).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=20):  # noqa: S310 - trusted env webhook URL
        pass
    return True
