"""The sample inputs, and the awkward cases planted in them.

If one of these fails, a fixture has drifted and an assignment option just got easier
than it was meant to be.
"""

from __future__ import annotations

from app import fixtures
from app.model_client import StubModelClient


def test_two_hundred_records():
    assert len(fixtures.libraries()) == 200


def test_thirty_tickets_including_empty_shapes():
    t = fixtures.tickets()
    assert len(t) == 30
    assert any(x["subject"] == "" for x in t), "a ticket with no subject"
    assert any(x["body"] == "" for x in t), "a ticket with no body"


def test_documents_contradict_each_other():
    docs = {d["id"]: d["text"] for d in fixtures.documents()}
    assert "21 days" in docs["policy-loans"]
    assert "14 days" in docs["faq-borrowing"]


def test_three_diffs_of_very_different_sizes():
    d = {x["name"]: x["diff"] for x in fixtures.diffs()}
    assert len(d) == 3
    small = len(d["01-small-clean"].splitlines())
    large = len(d["03-very-large"].splitlines())
    assert large > small * 10


def test_operations_are_tagged_reversible_or_not():
    ops = fixtures.operations()["operations"]
    assert any(o["reversible"] for o in ops)
    assert any(not o["reversible"] for o in ops)


def test_there_are_goals_that_need_an_irreversible_step():
    goals = fixtures.operations()["goals"]
    assert len(goals) == 8
    assert any("delete" in g["text"].lower() for g in goals)


def test_the_duplicate_pair_disagrees_on_two_fields():
    records = [r for r in fixtures.libraries() if r["id"] in (1, 2)]
    pairs = StubModelClient().complete("propose_merges", {"records": records}).value
    assert len(pairs) == 1
    assert set(pairs[0]["field_conflicts"]) == {"kind", "annual_visits"}


def test_the_transitivity_chain_holds():
    """A matches B, B matches C, A does not match C. This is the point of option E."""
    records = [r for r in fixtures.libraries() if r["id"] in (3, 4, 5)]
    pairs = StubModelClient().complete("propose_merges", {"records": records}).value
    found = {frozenset((p["a_id"], p["b_id"])) for p in pairs}
    assert frozenset((3, 4)) in found
    assert frozenset((4, 5)) in found
    assert frozenset((3, 5)) not in found


def test_the_review_task_misses_the_real_bug():
    """It flags the shallow things and misses the off-by-one. That is option D."""
    diff = {x["name"]: x["diff"] for x in fixtures.diffs()}["02-has-a-real-bug"]
    comments = StubModelClient().complete("review_diff", {"diff": diff}).value
    assert any(c["severity"] == "blocker" for c in comments)
    assert not any("offset" in c["comment"].lower() or "off-by-one" in c["comment"].lower()
                   for c in comments)
