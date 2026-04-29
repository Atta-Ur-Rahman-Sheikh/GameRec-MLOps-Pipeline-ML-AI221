"""Lightweight import smoke tests (no Prefect server required)."""

from __future__ import annotations

import pytest


def test_prefect_flow_importable():
    pytest.importorskip("prefect")
    from pipelines.flow import gamerec_artifact_pipeline

    assert callable(gamerec_artifact_pipeline)


def test_tasks_importable():
    pytest.importorskip("prefect")
    import pipelines.tasks as t

    assert (t.PROJECT_ROOT / "app").is_dir()
