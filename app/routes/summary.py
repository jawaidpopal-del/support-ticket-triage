"""Filtered summary — implemented from `specs/filtered-summary.md`.

Every branch here traces to a numbered acceptance criterion in that document. If you
change the behaviour, change the specification first.
"""

from __future__ import annotations

import sqlite3
import statistics
import time
from typing import Any

from fastapi import APIRouter, Depends

from app import filters
from app.db import get_db, rows_to_dicts
from app.model_client import ModelError, get_client
from app.models import ModelPayload, SummaryResponse
from app.routes.libraries import _query_params

# NOTE (spec §6): this router is included BEFORE `libraries.router` in app/main.py, or
# `/libraries/{library_id}` would capture the path "summary" first.
router = APIRouter(prefix="/libraries", tags=["libraries"])

WORD_CAP = 60          # spec AC2
CACHE_TTL_SECONDS = 600  # spec §6 — ten minutes

_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def _cache_key(active: dict[str, Any]) -> str:
    """Spec §6: the normalised active filter set, so key order cannot split an entry."""
    return "&".join(f"{k}={active[k]!r}" for k in sorted(active))


def _cap_words(text: str, cap: int = WORD_CAP) -> tuple[str, int, bool]:
    """Spec AC2. The model does not respect the cap, so we enforce it."""
    words = text.split()
    if len(words) <= cap:
        return text, len(words), False
    return " ".join(words[:cap]).rstrip(",;:") + "…", cap, True


@router.get("/summary", response_model=SummaryResponse)
def summarise_filtered(
    params: dict = Depends(_query_params),
    db: sqlite3.Connection = Depends(get_db),
) -> SummaryResponse:
    active = filters.active(params)
    key = _cache_key(active)

    # AC3 / AC5: one entry per normalised filter set, ten-minute lifetime.
    hit = _cache.get(key)
    if hit and (time.monotonic() - hit[0]) < CACHE_TTL_SECONDS:
        return SummaryResponse(**{**hit[1], "cached": True})

    where, args = filters.build_where(params)
    rows = rows_to_dicts(db.execute(
        f"SELECT * FROM libraries WHERE {where}", args).fetchall())

    # AC4: nothing matched, so there is nothing to summarise and no call to make.
    if not rows:
        return SummaryResponse(count=0, filters=active, summary=None, word_count=0,
                               truncated=False, cached=False, model=None, model_error=None)

    payload = {
        "count": len(rows),
        "states": sorted({r["state"] for r in rows}),
        "kinds": sorted({r["kind"] for r in rows}),
        "median_visits": int(statistics.median(r["annual_visits"] for r in rows)),
    }

    # AC6: a model failure degrades this endpoint, it does not break it.
    try:
        result = get_client().complete("summarize_records", payload)
    except ModelError as exc:
        return SummaryResponse(count=len(rows), filters=active, summary=None,
                               word_count=0, truncated=False, cached=False,
                               model=None, model_error=str(exc))

    text, word_count, truncated = _cap_words(str(result.value))
    body = {
        "count": len(rows),
        "filters": active,
        "summary": text,
        "word_count": word_count,
        "truncated": truncated,
        "cached": False,
        "model": ModelPayload(**result.as_dict()),   # AC7
        "model_error": None,
    }
    _cache[key] = (time.monotonic(), body)
    return SummaryResponse(**body)


def clear_cache() -> None:
    """Test hook. Application code does not call this."""
    _cache.clear()
