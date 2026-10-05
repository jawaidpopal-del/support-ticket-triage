"""Support-ticket triage endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.model_client import ModelTimeout, ModelUnavailable, get_client
from app.models import ModelPayload, TicketRequest, TicketTriageResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])

_SENSITIVE_PATTERNS = (
    ("accessibility", ("screen reader", "accessibility", "accessibility: screen reader", "not announced by our screen reader")),
    ("data_retention", ("data retention", "borrowing history", "how long do you keep", "keep borrowing history")),
    ("deletion", ("close my account", "delete my borrowing history", "remove me", "delete my history", "delete")),
    ("escalation", ("urgent", "escalation", "blocked", "immediately", "everything is broken", "want escalation", "broken for days")),
)


def _neutral_human_review_draft() -> str:
    return (
        "Thank you for reaching out. A human reviewer will review this and follow up "
        "with you."
    )


def _is_sensitive_ticket(subject: str | None, body: str | None) -> bool:
    """Sensitive handling is based on ticket content, not an ID allowlist."""
    text = " ".join((subject or "", body or "")).lower()
    for _, phrases in _SENSITIVE_PATTERNS:
        if any(phrase in text for phrase in phrases):
            return True
    return False


@router.post("/triage", response_model=TicketTriageResponse)
def triage_ticket(body: TicketRequest) -> TicketTriageResponse:
    """Classify one ticket and return the human-review draft the agent should check."""
    ticket_payload = {
        "id": body.id,
        "subject": body.subject or "",
        "body": body.body or "",
    }

    try:
        result = get_client().complete("classify_ticket", ticket_payload)
    except ModelTimeout as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    model_value = result.value if isinstance(result.value, dict) else {}
    category = str(model_value.get("category", "general"))
    priority = str(model_value.get("priority", "low"))
    team = str(model_value.get("team", "triage"))
    draft_reply = str(model_value.get("draft_reply", "Thanks for writing in. I am taking a look and will come back to you."))

    if _is_sensitive_ticket(body.subject, body.body):
        draft_reply = _neutral_human_review_draft()

    return TicketTriageResponse(
        ticket_id=body.id,
        category=category,
        priority=priority,
        suggested_team=team,
        draft_reply=draft_reply,
        requires_human_review=True,
        model=ModelPayload(
            value=model_value,
            confidence=result.confidence,
            model_version=result.model_version,
            latency_ms=result.latency_ms,
        ),
    )
