"""Round 1 — a FAITHFUL implementation of `demo/spec-v1.md`.

Nothing here is careless. Every line is a reasonable reading of what v1 actually said:

  v1 AC2  "The summary is concise."                 -> the model's text, unaltered
  v1 AC3  "The summary is cached."                  -> one cache, for the endpoint
  v1      (no empty-set criterion)                  -> the model is called anyway
  v1      (no failure criterion)                    -> the error propagates

Swap this in with `demo/run-round-1.sh` to show what those four gaps produce.
"""

from __future__ import annotations

import sqlite3
import statistics
from typing import Any

from fastapi import APIRouter, Depends

from app import filters
from app.db import get_db, rows_to_dicts
from app.model_client import get_client
from app.models import ModelPayload, SummaryResponse
from app.routes.libraries import _query_params

router = APIRouter(prefix="/libraries", tags=["libraries"])

# v1 AC3 said "the summary is cached". It did not say keyed on what.
_cached_body: dict[str, Any] | None = None


@router.get("/summary", response_model=SummaryResponse)
def summarise_filtered(
    params: dict = Depends(_query_params),
    db: sqlite3.Connection = Depends(get_db),
) -> SummaryResponse:
    global _cached_body
    active = filters.active(params)

    if _cached_body is not None:
        return SummaryResponse(**{**_cached_body, "cached": True})

    where, args = filters.build_where(params)
    rows = rows_to_dicts(db.execute(
        f"SELECT * FROM libraries WHERE {where}", args).fetchall())

    payload = {
        "count": len(rows),
        "states": sorted({r["state"] for r in rows}),
        "kinds": sorted({r["kind"] for r in rows}),
        "median_visits": int(statistics.median([r["annual_visits"] for r in rows] or [0])),
    }
    result = get_client().complete("summarize_records", payload)
    text = str(result.value)

    body = {
        "count": len(rows), "filters": active, "summary": text,
        "word_count": len(text.split()), "truncated": False, "cached": False,
        "model": ModelPayload(**result.as_dict()), "model_error": None,
    }
    _cached_body = body
    return SummaryResponse(**body)


def clear_cache() -> None:
    global _cached_body
    _cached_body = None
