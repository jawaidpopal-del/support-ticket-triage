"""Loaders for the sample inputs in ``data/``.

Each assignment option has a fixture set waiting for it. Load it, do not go hunting
for data. The awkward cases in each set are deliberate — see ``docs/fixtures.md``.
"""

from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def libraries() -> list[dict[str, Any]]:
    """All 200 records, straight from the CSV. Option E works on these."""
    with (DATA_DIR / "libraries.csv").open(newline="", encoding="utf-8") as fh:
        rows = []
        for r in csv.DictReader(fh):
            rows.append({
                "id": int(r["id"]), "name": r["name"], "city": r["city"],
                "state": r["state"], "kind": r["kind"],
                "year_founded": int(r["year_founded"]),
                "annual_visits": int(r["annual_visits"]),
                "has_makerspace": r["has_makerspace"].strip().lower() == "true",
            })
    return rows


@lru_cache(maxsize=1)
def tickets() -> list[dict[str, str]]:
    """Option B. 30 tickets: clear ones, near-duplicates, and genuinely ambiguous ones."""
    return json.loads((DATA_DIR / "tickets.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def documents() -> list[dict[str, str]]:
    """Option C. Nine short policy documents, two of which contradict each other."""
    out = []
    for path in sorted((DATA_DIR / "documents").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta: dict[str, str] = {}
        body = raw
        if raw.startswith("---"):
            _, header, body = raw.split("---", 2)
            for line in header.strip().splitlines():
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
        text = body.strip()
        out.append({
            "id": meta.get("id", path.stem),
            "title": meta.get("title", path.stem),
            "updated": meta.get("updated", ""),
            "text": text,
            "summary": text.split("\n\n")[0][:200],
            "path": str(path.relative_to(DATA_DIR.parent)),
        })
    return out


@lru_cache(maxsize=1)
def diffs() -> list[dict[str, str]]:
    """Option D. Three diffs: small and clean, one with real bugs, one very large."""
    return [{"name": p.stem, "diff": p.read_text(encoding="utf-8")}
            for p in sorted((DATA_DIR / "diffs").glob("*.diff"))]


@lru_cache(maxsize=1)
def operations() -> dict[str, Any]:
    """Option A. App operations tagged reversible/irreversible, plus eight goals."""
    return json.loads((DATA_DIR / "operations.json").read_text(encoding="utf-8"))
