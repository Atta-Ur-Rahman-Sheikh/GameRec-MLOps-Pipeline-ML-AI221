"""Shared pytest fixtures.

If `tests/fixtures/artifacts/` exists, we point the artifact loader there
(small synthetic artifacts checked in for CI). Otherwise we fall back to
the real `artifacts/recommender/` so local devs get full-fidelity tests
without rebuilding fixtures.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
FIXTURE_ARTIFACTS = TESTS_DIR / "fixtures" / "artifacts"
PROJECT_ROOT = TESTS_DIR.parent
REAL_ARTIFACTS = PROJECT_ROOT / "artifacts" / "recommender"


def _resolve_artifacts_dir() -> Path:
    if FIXTURE_ARTIFACTS.exists() and any(FIXTURE_ARTIFACTS.iterdir()):
        return FIXTURE_ARTIFACTS
    return REAL_ARTIFACTS


@pytest.fixture(scope="session", autouse=True)
def _set_artifacts_env():
    """Point the app at fixture artifacts (when available) for the session."""
    os.environ["GAMEREC_ARTIFACTS_DIR"] = str(_resolve_artifacts_dir())
    yield


@pytest.fixture(scope="session")
def bundle():
    """Loaded artifact bundle, shared across the test session."""
    # Import lazily so the env-var override is in place first.
    from app.core import artifacts as art

    art.reset_bundle()
    # Re-create settings so the new env var is picked up.
    from app.core.config import Settings

    return art.load_bundle(cfg=Settings.from_env(), force=True)


@pytest.fixture(scope="session")
def client(bundle):  # noqa: ARG001 -- ensures bundle loads first
    """FastAPI TestClient bound to the loaded bundle."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


def known_game(bundle) -> str:
    """Pick a game that's guaranteed to be in whatever catalog we loaded."""
    candidates = [
        "Hollow Knight",
        "Hades",
        "Stardew Valley",
        "Dark Souls III",
        "Counter-Strike",
        "Half-Life 2",
        "Portal 2",
        "Terraria",
    ]
    for c in candidates:
        from app.services.recommender import find_game_index

        if find_game_index(c, bundle) is not None:
            return c
    # Fall back to the most popular game in whatever catalog loaded.
    return str(bundle.catalog.iloc[int(bundle.catalog["popularity"].idxmax())]["name"])


@pytest.fixture(scope="session")
def famous_game(bundle) -> str:
    return known_game(bundle)
