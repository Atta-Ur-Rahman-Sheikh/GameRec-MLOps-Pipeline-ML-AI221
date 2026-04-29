"""Seasonality lookup service.

Reads the precomputed `seasonality.json` bundle (per-theme monthly index +
forecast metrics) and exposes simple lookup helpers.
"""

from __future__ import annotations

from typing import Any

from app.core.artifacts import ArtifactBundle, get_bundle

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def list_themes(bundle: ArtifactBundle | None = None) -> list[str]:
    bundle = bundle or get_bundle()
    season = bundle.seasonality or {}
    return sorted((season.get("themes") or {}).keys())


def get_seasonality(theme: str,
                    bundle: ArtifactBundle | None = None) -> dict[str, Any]:
    """Return the monthly index + headline stats for a theme."""
    bundle = bundle or get_bundle()
    season = bundle.seasonality or {}
    themes = season.get("themes") or {}
    if theme not in themes:
        # Try a case-insensitive match for convenience.
        match = next((k for k in themes if k.lower() == theme.lower()), None)
        if match is None:
            raise KeyError(f"Theme {theme!r} not found in seasonality artifact.")
        theme = match

    payload = themes[theme]
    seasonal_index = list(payload.get("seasonal_index", []))
    monthly_avg = list(payload.get("monthly_avg", []))
    n_games = int(payload.get("n_games", 0))

    if seasonal_index:
        peak_idx = max(range(len(seasonal_index)), key=lambda i: seasonal_index[i])
        peak_month = MONTH_NAMES[peak_idx] if peak_idx < len(MONTH_NAMES) else str(peak_idx + 1)
        peak_value = round(float(seasonal_index[peak_idx]), 3)
    else:
        peak_month = None
        peak_value = None

    forecast = next(
        (r for r in season.get("forecast_metrics", []) if r.get("theme") == theme),
        None,
    )

    return {
        "theme": theme,
        "window": season.get("window"),
        "n_games": n_games,
        "month_names": MONTH_NAMES,
        "monthly_avg": monthly_avg,
        "seasonal_index": seasonal_index,
        "peak_month": peak_month,
        "peak_index_value": peak_value,
        "forecast": forecast,
    }
