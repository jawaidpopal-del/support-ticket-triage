"""The records API: listing, filtering, the write path, and the model-backed endpoint."""

from __future__ import annotations

import pytest

from app import model_client as mc


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_list_returns_a_page(client):
    body = client.get("/libraries", params={"limit": 5}).json()
    assert body["total"] == 200
    assert len(body["items"]) == 5
    assert body["limit"] == 5 and body["offset"] == 0


def test_offset_moves_the_window(client):
    first = client.get("/libraries", params={"limit": 3, "offset": 0}).json()["items"]
    second = client.get("/libraries", params={"limit": 3, "offset": 3}).json()["items"]
    assert [i["id"] for i in first] != [i["id"] for i in second]


def test_filter_by_state(client):
    body = client.get("/libraries", params={"state": "ma"}).json()
    assert body["total"] > 0
    assert {i["state"] for i in body["items"]} == {"MA"}


def test_filter_by_visit_range(client):
    body = client.get("/libraries", params={"min_visits": 100_000}).json()
    assert all(i["annual_visits"] >= 100_000 for i in body["items"])


def test_filters_combine(client):
    body = client.get("/libraries", params={"state": "MA", "kind": "branch"}).json()
    assert all(i["state"] == "MA" and i["kind"] == "branch" for i in body["items"])


def test_filter_matching_nothing_returns_an_empty_page(client):
    body = client.get("/libraries", params={"state": "ZZ"}).json()
    assert body["total"] == 0 and body["items"] == []


def test_get_one(client):
    body = client.get("/libraries/1").json()
    assert body["name"] == "Eastport Public Library"


def test_get_missing_is_404(client):
    r = client.get("/libraries/999999")
    assert r.status_code == 404


def test_create(client):
    payload = {"name": "Newbridge Public Library", "city": "Newbridge", "state": "VT",
               "kind": "branch", "year_founded": 1990, "annual_visits": 12_000,
               "has_makerspace": False}
    r = client.post("/libraries", json=payload)
    assert r.status_code == 201
    assert r.json()["id"] > 200


def test_create_rejects_a_duplicate_name_in_the_same_city(client):
    payload = {"name": "Eastport Public Library", "city": "Eastport", "state": "ME",
               "kind": "branch", "year_founded": 1904, "annual_visits": 1,
               "has_makerspace": False}
    assert client.post("/libraries", json=payload).status_code == 409


def test_create_validates_its_input(client):
    bad = {"name": "", "city": "X", "state": "TOOLONG", "kind": "not_a_kind",
           "year_founded": 1, "annual_visits": -5}
    assert client.post("/libraries", json=bad).status_code == 422


# -- the model-backed endpoint ---------------------------------------------


def test_describe_returns_text_and_the_model_payload(client):
    body = client.get("/libraries/1/describe").json()
    assert body["library_id"] == 1
    assert "Eastport" in body["description"]
    assert 0.0 <= body["model"]["confidence"] <= 1.0
    assert body["model"]["model_version"] == "v1"


def test_describe_on_a_missing_record_is_404(client):
    assert client.get("/libraries/999999/describe").status_code == 404


def test_describe_when_the_model_is_unavailable(client, monkeypatch):
    monkeypatch.setenv("STUB_FAILURE_RATE", "1.0")
    mc.reset_client()
    assert client.get("/libraries/1/describe").status_code == 503


def test_describe_when_the_model_times_out(client, monkeypatch):
    monkeypatch.setenv("STUB_LATENCY_MS", "900")
    monkeypatch.setenv("STUB_TIMEOUT_MS", "100")
    monkeypatch.setenv("STUB_SLEEP", "0")
    mc.reset_client()
    assert client.get("/libraries/1/describe").status_code == 504


def test_describe_surfaces_low_confidence_rather_than_hiding_it(client, monkeypatch):
    monkeypatch.setenv("STUB_WRONGNESS", "1.0")
    mc.reset_client()
    body = client.get("/libraries/1/describe").json()
    assert body["model"]["confidence"] < 0.5


def test_writes_do_not_leak_between_tests(client):
    """Guards the fixture itself.

    If this fails while :func:`test_create` passes, the test database is being shared
    and every count assertion in this file is unreliable.
    """
    assert client.get("/libraries").json()["total"] == 200
