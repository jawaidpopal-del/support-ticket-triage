"""Filtered summary — one test per acceptance criterion in specs/filtered-summary.md.

Test names carry the criterion number. When one of these goes red it points at a line
in the specification, not just at a broken function.
"""

from __future__ import annotations

from app import model_client as mc


def test_ac1_filter_with_rows_returns_a_summary(client):
    body = client.get("/libraries/summary", params={"state": "MA"}).json()
    assert body["count"] > 0
    assert body["summary"]
    assert body["filters"] == {"state": "MA"}


def test_ac2_summary_is_capped_at_sixty_words(client):
    """The stub returns 65-70 words on purpose. The cap is ours to enforce."""
    body = client.get("/libraries/summary", params={"kind": "branch"}).json()
    assert body["word_count"] <= 60
    assert len(body["summary"].split()) <= 60
    assert body["truncated"] is True


def test_ac3_same_filter_twice_is_cached_and_does_not_call_the_model_again(client):
    first = client.get("/libraries/summary", params={"state": "OR"}).json()
    calls_after_first = len(mc.get_client().calls)
    second = client.get("/libraries/summary", params={"state": "OR"}).json()
    assert first["cached"] is False
    assert second["cached"] is True
    assert second["summary"] == first["summary"]
    assert len(mc.get_client().calls) == calls_after_first, "the model was called twice"


def test_ac4_zero_rows_makes_no_model_call(client):
    before = len(mc.get_client().calls)
    body = client.get("/libraries/summary", params={"state": "ZZ"}).json()
    assert body["count"] == 0
    assert body["summary"] is None
    assert len(mc.get_client().calls) == before, "the model was called on an empty set"


def test_ac5_different_filters_get_different_summaries(client):
    """The one that fails when the cache is global instead of per filter set."""
    a = client.get("/libraries/summary", params={"state": "MA"}).json()
    b = client.get("/libraries/summary", params={"kind": "bookmobile"}).json()
    assert a["count"] != b["count"]
    assert a["summary"] != b["summary"], "a cached summary leaked across filter sets"
    assert b["cached"] is False


def test_ac6_model_failure_does_not_fail_the_request(client, monkeypatch):
    monkeypatch.setenv("STUB_FAILURE_RATE", "1.0")
    mc.reset_client()
    r = client.get("/libraries/summary", params={"state": "MA"})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"] is None
    assert body["model_error"]
    assert body["count"] > 0, "the row count is still useful when the model is down"


def test_ac6_model_timeout_does_not_fail_the_request(client, monkeypatch):
    monkeypatch.setenv("STUB_LATENCY_MS", "900")
    monkeypatch.setenv("STUB_TIMEOUT_MS", "100")
    monkeypatch.setenv("STUB_SLEEP", "0")
    mc.reset_client()
    r = client.get("/libraries/summary", params={"state": "MA"})
    assert r.status_code == 200
    assert r.json()["model_error"]


def test_ac7_response_carries_confidence_and_version(client):
    model = client.get("/libraries/summary", params={"state": "MA"}).json()["model"]
    assert 0.0 <= model["confidence"] <= 1.0
    assert model["model_version"] in ("v1", "v2")
