"""HTTP contract tests mapped to specs/spec-v1.md acceptance criteria."""

from __future__ import annotations

import pytest

from app import fixtures, model_client


TRIAGE_URL = "/tickets/triage"


def _fixture_ticket(ticket_id: str) -> dict[str, str]:
    return next(ticket for ticket in fixtures.tickets() if ticket["id"] == ticket_id)


def _request_for(ticket: dict[str, str]) -> dict[str, str]:
    return {
        "id": ticket["id"],
        "subject": ticket["subject"],
        "body": ticket["body"],
    }


def _triage(client, ticket: dict[str, str]):
    return client.post(TRIAGE_URL, json=_request_for(ticket))


def test_ac1_success_returns_ticket_and_model_metadata(client):
    response = _triage(client, _fixture_ticket("T-001"))

    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == "T-001"
    assert body["category"]
    assert body["priority"]
    assert body["suggested_team"]
    assert body["draft_reply"]
    assert body["requires_human_review"] is True
    assert 0.0 <= body["model"]["confidence"] <= 1.0
    assert body["model"]["model_version"] in {"v1", "v2"}
    assert isinstance(body["model"]["latency_ms"], int)
    assert body["model"]["value"]


@pytest.mark.parametrize(
    ("ticket_id", "expected_category"),
    [
        ("T-001", "billing"),
        ("T-002", "access"),
        ("T-003", "data"),
        ("T-004", "outage"),
        ("T-016", "general"),
    ],
)
def test_ac2_category_matches_ticket_clues(client, ticket_id, expected_category):
    response = _triage(client, _fixture_ticket(ticket_id))

    assert response.status_code == 200
    assert response.json()["category"] == expected_category


def test_ac3_priority_preserves_model_result(client, monkeypatch):
    normal = _triage(client, _fixture_ticket("T-001"))
    assert normal.status_code == 200
    assert normal.json()["priority"] == normal.json()["model"]["value"]["priority"]
    assert normal.json()["priority"] == "normal"

    no_category = _triage(client, _fixture_ticket("T-016"))
    assert no_category.status_code == 200
    assert no_category.json()["priority"] == "low"

    escalation = _triage(client, _fixture_ticket("T-022"))
    assert escalation.status_code == 200
    assert escalation.json()["priority"] == "high"
    assert escalation.json()["priority"] == escalation.json()["model"]["value"]["priority"]

    monkeypatch.setenv("STUB_MODEL_VERSION", "v2")
    model_client.reset_client()
    version_two_general = _triage(client, _fixture_ticket("T-016"))
    assert version_two_general.status_code == 200
    assert version_two_general.json()["model"]["model_version"] == "v2"
    assert version_two_general.json()["priority"] == "normal"


@pytest.mark.parametrize(
    ("ticket_id", "expected_team"),
    [
        ("T-001", "finance-ops"),
        ("T-002", "identity"),
        ("T-003", "data-platform"),
        ("T-004", "platform-sre"),
        ("T-016", "triage"),
    ],
)
def test_ac4_suggested_team_matches_category(client, ticket_id, expected_team):
    response = _triage(client, _fixture_ticket(ticket_id))

    assert response.status_code == 200
    assert response.json()["suggested_team"] == expected_team


def test_ac5_low_confidence_answer_is_visible_and_requires_review(client, monkeypatch):
    response = _triage(client, _fixture_ticket("T-016"))

    assert response.status_code == 200
    body = response.json()
    assert body["model"]["confidence"] < 0.5
    assert body["model"]["value"]["category"] == body["category"]
    assert body["model"]["value"]
    assert body["model"]["model_version"] in {"v1", "v2"}
    assert body["requires_human_review"] is True

    monkeypatch.setenv("STUB_WRONGNESS", "1.0")
    model_client.reset_client()
    degraded = _triage(client, _fixture_ticket("T-001"))

    assert degraded.status_code == 200
    degraded_body = degraded.json()
    assert degraded_body["model"]["confidence"] < 0.5
    assert degraded_body["model"]["value"]
    assert degraded_body["requires_human_review"] is True


@pytest.mark.parametrize(
    ("ticket_id", "field_to_omit"),
    [("T-020", None), ("T-021", None), ("T-001", "subject"), ("T-001", "body")],
)
def test_ac6_missing_or_empty_subject_and_body_are_accepted(
    client, ticket_id, field_to_omit
):
    ticket = _fixture_ticket(ticket_id)
    request_body = _request_for(ticket)
    if field_to_omit:
        request_body.pop(field_to_omit)

    response = client.post(TRIAGE_URL, json=request_body)

    assert response.status_code == 200
    result = response.json()
    assert result["ticket_id"] == ticket_id
    assert result["category"]
    assert result["priority"]
    if not request_body.get("subject", "") and not request_body.get("body", ""):
        assert result["category"] == "general"
        assert result["priority"] == "low"
        assert result["model"]["confidence"] < 0.5
        assert result["requires_human_review"] is True


def test_ac7_near_duplicate_tickets_are_triaged_separately(client):
    first = _triage(client, _fixture_ticket("T-001"))
    second = _triage(client, _fixture_ticket("T-011"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["ticket_id"] == "T-001"
    assert second.json()["ticket_id"] == "T-011"


@pytest.mark.parametrize(
    ("ticket_id", "subject", "body"),
    [
        (
            "T-999",
            "Accessibility: screen reader",
            "Catalogue results are not announced by our screen reader.",
        ),
        (
            "T-998",
            "Data retention question",
            "How long do you keep borrowing history? Our board is asking.",
        ),
        (
            "T-997",
            "Please close my account",
            "Remove me and delete my borrowing history entirely.",
        ),
        (
            "T-996",
            "URGENT URGENT URGENT",
            "Everything is broken and it has been broken for days and nobody has replied and we are extremely unhappy with the service and want escalation now.",
        ),
    ],
)
def test_ac8_sensitive_content_gets_neutral_human_review_drafts(
    client, ticket_id, subject, body
):
    response = client.post(
        TRIAGE_URL,
        json={"id": ticket_id, "subject": subject, "body": body},
    )

    assert response.status_code == 200
    body_json = response.json()
    draft = body_json["draft_reply"].lower()
    assert body_json["requires_human_review"] is True
    assert "thank" in draft
    assert "human" in draft
    assert "review" in draft
    assert not any(
        claim in draft
        for claim in (
            "has been deleted",
            "we deleted",
            "your data is removed",
            "we fixed",
            "we have fixed",
            "we resolved",
            "we have resolved",
        )
    )


def test_ac9_model_unavailable_returns_error_body(client, monkeypatch):
    monkeypatch.setenv("STUB_FAILURE_RATE", "1.0")
    model_client.reset_client()

    response = _triage(client, _fixture_ticket("T-001"))

    assert response.status_code == 503
    assert response.json()["code"] == "model_unavailable"
    assert response.json()["detail"]


def test_ac10_model_timeout_returns_error_body(client, monkeypatch):
    monkeypatch.setenv("STUB_LATENCY_MS", "500")
    monkeypatch.setenv("STUB_TIMEOUT_MS", "100")
    monkeypatch.setenv("STUB_SLEEP", "0")
    model_client.reset_client()

    response = _triage(client, _fixture_ticket("T-001"))

    assert response.status_code == 504
    assert response.json()["code"] == "model_timeout"
    assert response.json()["detail"]


@pytest.mark.parametrize(
    "request_body",
    [
        {"subject": "Refund", "body": "Please help."},
        {"id": "T-001", "subject": ["not", "text"], "body": "Please help."},
    ],
)
def test_ac11_invalid_ticket_request_returns_422(client, request_body):
    response = client.post(TRIAGE_URL, json=request_body)

    assert response.status_code == 422
