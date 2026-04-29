"""Shared text-handling helpers ported from the notebook.

These mirror the tokenisation rules used when the TF-IDF vectorizer was
fitted, so query strings are processed identically to catalog rows.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[^a-z0-9 ]+")
_KEY_RE = re.compile(r"[^a-z0-9]+")


def to_tokens(items: list[str] | None) -> list[str]:
    """Lowercase a list of labels; multi-word labels become snake-case tokens."""
    out: list[str] = []
    for x in items or []:
        if not isinstance(x, str):
            continue
        tok = _TOKEN_RE.sub("", x.lower()).strip()
        if not tok:
            continue
        out.append(tok.replace(" ", "_"))
    return out


def build_query_text(liked_genres: list[str] | None, liked_tags: list[str] | None) -> str:
    """Same field-weighting scheme used to build catalog text blobs."""
    g = to_tokens(liked_genres or [])
    t = to_tokens(liked_tags or [])
    return " ".join(t * 4 + g * 3)


def norm_key(name: str | None) -> str:
    """Normalise a title to the catalog 'key' (lowercase, alphanumeric only)."""
    if not isinstance(name, str):
        return ""
    return _KEY_RE.sub("", name.lower())
