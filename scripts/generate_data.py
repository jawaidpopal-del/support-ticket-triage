"""Regenerate data/libraries.csv.

Deterministic: the same seed always produces the same file, so the fixture can be
committed and the tests can assert against it.

The interesting records are *planted*, not random. See docs/fixtures.md for what is
in here on purpose and why. In short:

  * a pair whose names differ only in punctuation and which disagree on two fields
  * a three-record chain where A matches B and B matches C but A does not match C
  * several same-city clusters that produce plausible-but-wrong merge candidates
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "libraries.csv"
SEED = 20260923

KINDS = ("central", "branch", "bookmobile", "research")

# --- planted records -------------------------------------------------------
# id is assigned in order below, starting at 1.

PLANTED = [
    # An obvious duplicate pair that DISAGREES on kind and annual_visits.
    dict(name="Eastport Public Library", city="Eastport", state="ME", kind="central",
         year_founded=1904, annual_visits=48_000, has_makerspace=True),
    dict(name="Eastport Publ. Library", city="Eastport", state="ME", kind="branch",
         year_founded=1904, annual_visits=51_200, has_makerspace=False),

    # The transitivity chain. A~B and B~C, but A and C are different places.
    dict(name="North Ashfield Library", city="Ashfield", state="MA", kind="branch",
         year_founded=1921, annual_visits=22_400, has_makerspace=False),
    dict(name="North Ashfield Memorial Library", city="Ashfield", state="MA", kind="branch",
         year_founded=1921, annual_visits=22_900, has_makerspace=False),
    dict(name="Ashfield Memorial Heights Library", city="Ashfield", state="MA", kind="branch",
         year_founded=1967, annual_visits=9_800, has_makerspace=True),

    # A same-city cluster: genuinely different facilities with similar names.
    dict(name="Oakvale Central Library", city="Oakvale", state="OR", kind="central",
         year_founded=1898, annual_visits=310_000, has_makerspace=True),
    dict(name="Oakvale Riverside Branch", city="Oakvale", state="OR", kind="branch",
         year_founded=1955, annual_visits=41_000, has_makerspace=False),
    dict(name="Oakvale Technical Research Library", city="Oakvale", state="OR", kind="research",
         year_founded=1972, annual_visits=6_200, has_makerspace=False),

    # A record with an unusual but entirely legal shape: zero visits, very new.
    dict(name="Cold Harbor Bookmobile", city="Cold Harbor", state="AK", kind="bookmobile",
         year_founded=2025, annual_visits=0, has_makerspace=False),

    # The largest and the smallest, so range filters have something to find.
    dict(name="Grand Meridian Central Library", city="Meridian", state="TX", kind="central",
         year_founded=1876, annual_visits=1_480_000, has_makerspace=True),
]

# --- filler ----------------------------------------------------------------

PLACES = [
    "Alderton", "Brightwater", "Cedar Falls", "Dunmore", "Elmridge", "Fairhaven",
    "Glenmoor", "Hartsdale", "Ironwood", "Juniper Bend", "Kingsford", "Lakemont",
    "Marbury", "Northgate", "Orchard Park", "Pinehurst", "Quarry Hill", "Redstone",
    "Stonebridge", "Thornbury", "Umberton", "Vinewood", "Westmill", "Yarrow Creek",
    "Ambrose", "Belfry", "Cloverton", "Darnley", "Eastwick", "Fernhill",
    "Granville", "Holloway", "Inglemere", "Kestrel Bay", "Linden Grove", "Mosswood",
    "Netherfield", "Oakhollow", "Pembroke", "Ravenna", "Saltmarsh", "Tamworth",
    "Underhill", "Ваle Crossing", "Wexford", "Ashgrove", "Bramblewood", "Cranemere",
]
PLACES = [p for p in PLACES if p.isascii()]

SUFFIXES = ["Public Library", "Community Library", "Memorial Library",
            "Free Library", "District Library", "Library"]

STATES = ["MA", "ME", "NH", "VT", "NY", "PA", "OH", "MI", "IL", "WI", "MN",
          "OR", "WA", "CA", "TX", "CO", "NM", "AZ", "FL", "GA", "NC", "AK"]


def build() -> list[dict]:
    rng = random.Random(SEED)
    rows: list[dict] = []
    for i, rec in enumerate(PLANTED, start=1):
        rows.append({"id": i, **rec})

    next_id = len(rows) + 1
    used: set[tuple[str, str]] = {(r["name"], r["city"]) for r in rows}

    while len(rows) < 200:
        place = rng.choice(PLACES)
        suffix = rng.choice(SUFFIXES)
        name = f"{place} {suffix}"
        city = place
        if (name, city) in used:
            continue
        used.add((name, city))
        kind = rng.choices(KINDS, weights=(14, 62, 12, 12))[0]
        base = {"central": (90_000, 600_000), "branch": (8_000, 90_000),
                "bookmobile": (500, 9_000), "research": (1_500, 30_000)}[kind]
        rows.append({
            "id": next_id,
            "name": name,
            "city": city,
            "state": rng.choice(STATES),
            "kind": kind,
            "year_founded": rng.randint(1855, 2024),
            "annual_visits": rng.randint(*base),
            "has_makerspace": rng.random() < 0.28,
        })
        next_id += 1
    return rows


def main() -> None:
    rows = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "name", "city", "state", "kind",
                                           "year_founded", "annual_visits", "has_makerspace"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "has_makerspace": "true" if r["has_makerspace"] else "false"})
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
