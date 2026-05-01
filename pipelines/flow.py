"""Prefect flow entrypoint.

Run locally::

    python -m pipelines.flow

Or via Makefile::

    make pipeline

Environment variables:

``GAMEREC_ARTIFACTS_DIR``
    Override artifact directory (defaults to ``artifacts/recommender``).
``DISCORD_WEBHOOK_URL``
    Discord incoming webhook URL for success/failure notifications.
"""

from __future__ import annotations

from prefect import flow

from pipelines.tasks import (
    print_summary,
    send_discord_notification,
    validate_sources_and_environment,
    verify_ml_artifacts,
)


@flow(name="gamerec-artifact-pipeline", log_prints=True)
def gamerec_artifact_pipeline():
    """Validate raw sources + serialized ML bundle."""
    try:
        src = validate_sources_and_environment()
        rep = verify_ml_artifacts()
        print_summary(src, rep)

        send_discord_notification(
            message=(
                "✅ **GameRec Prefect pipeline succeeded**\n"
                f"- Steam CSV present: `{src['steam_csv_exists']}`\n"
                f"- RAWG JSONL present: `{src['rawg_jsonl_exists']}`\n"
                f"- Artifacts directory: `{rep['artifacts_dir']}`\n"
                f"- Missing required artifacts: `{rep['missing_required']}`\n"
                f"- Ready for FastAPI: `{rep['ready_for_fastapi']}`"
            ),
        )
        return {"sources": src, "artifacts": rep}
    except Exception as exc:
        try:
            send_discord_notification(
                message=(
                    "❌ **GameRec Prefect pipeline failed**\n"
                    f"- Error: `{exc!r}`"
                ),
            )
        except Exception as notify_exc:  # pragma: no cover - best effort only
            print(f"Discord notification failed: {notify_exc!r}")
        raise


if __name__ == "__main__":
    gamerec_artifact_pipeline()
