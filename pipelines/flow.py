"""Prefect flow entrypoint.

Run locally::

    python -m pipelines.flow

Or via Makefile::

    make pipeline

Environment variables:

``GAMEREC_ARTIFACTS_DIR``
    Override artifact directory (defaults to ``artifacts/recommender``).
"""

from __future__ import annotations

from prefect import flow

from pipelines.tasks import (
    print_summary,
    validate_sources_and_environment,
    verify_ml_artifacts,
)


@flow(name="gamerec-artifact-pipeline", log_prints=True)
def gamerec_artifact_pipeline():
    """Validate raw sources + serialized ML bundle."""
    src = validate_sources_and_environment()
    rep = verify_ml_artifacts()
    print_summary(src, rep)
    return {"sources": src, "artifacts": rep}


if __name__ == "__main__":
    gamerec_artifact_pipeline()
