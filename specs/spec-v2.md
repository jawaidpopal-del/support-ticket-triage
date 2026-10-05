# Feature Specification — Support Ticket Triage (v2)

**Status:** draft  
**Author:**  
**Reviewers:**  
**Date:** 2026-10-05

This revision resolves ambiguities left by v1: it makes sensitive-ticket handling explicit and states how it is determined. It does not change the v1 feature contract, the implementation, or the existing tests.

---

## 1. Intent

Support staff need a consistent first look at incoming tickets so they can decide who
should handle them and how quickly they need attention. This feature classifies a
ticket, suggests a team and priority, and prepares a first reply for a person to
review. It is an aid to human triage, not an automatic decision-maker or reply sender.

## 2. User stories

- As a support agent, I want a ticket category and priority so that I can understand
the kind of issue and its apparent urgency.
- As a support agent, I want a suggested team so that I can route a ticket to the
appropriate group.
- As a support agent, I want a draft reply held for human review so that I can check
it before responding.
- As a support agent, I want unclear or sensitive tickets identified so that they
receive appropriate human attention.

## 3. Acceptance criteria

1. Given a valid ticket with an ID, subject, and body, when `POST /tickets/triage` is
   called, then the response is HTTP 200 and echoes the ticket ID with its category,
   priority, suggested team, draft reply, human-review flag, and model metadata.

2. Given a ticket with category clues, when it is triaged, then its category is one
   of `billing`, `access`, `data`, `outage`, or `general`, as returned by the
   `classify_ticket` model task. In the repository stub, representative clues are
   billing (“invoice”, “charge”, “refund”, “payment”, “billed”); access (“login”,
   “password”, “locked”, “sign in”, “access”, “permission”, “home branch”); data
   (“import”, “export”, “csv”, “duplicate”, “missing record”, “due date”, “loan”);
and outage (“down”, “500”, “timeout”, “unavailable”, “cannot load”, “offline”).
   If no clue matches, the stub returns `general`.

3. Given a ticket, when its priority is returned, then the API preserves the model's
   priority (`high`, `normal`, or `low`). With the repository stub, “urgent”, “asap”,
   “immediately”, “down”, or “blocked” produces `high`; absent those clues, a ticket
   with category matches produces `normal`, and one with no category matches produces
   `low` under v1. Under v2, a `general` ticket may instead have `normal` priority.
   The all-caps escalation fixture T-022 contains an urgency clue and the stub returns
   `high`; the API preserves that model priority like any other result.

4. Given a model result for a supported category, when the response is formed, then
   `suggested_team` is the model's team: `billing` → `finance-ops`, `access` →
   `identity`, `data` → `data-platform`, `outage` → `platform-sre`, and `general` →
   `triage`.

5. For this specification, an ambiguous or low-confidence result means a model
   confidence below `0.5`. Given such a result, when it is triaged, then `model.value`
   retains the raw model result, the response exposes its confidence and model
   version, and sets `requires_human_review` to `true`. It does not suppress the
   classification or present it as certain. The stub's ambiguous fixtures such as
   “Help” and “Follow up” return `general` at confidence `0.44` on v1. A plausible
   degraded result with confidence below `0.5` follows the same rule; for sensitive
   cases, the top-level draft follows AC8.

6. Given a request with an omitted or empty subject or body, when it is submitted,
   then the request is accepted and the available text is used. Given both are omitted
   or empty, then the stub result under v1 is `general` / `low`, has confidence below
   `0.5`, and requires human review. An absent ticket ID is not permitted.

7. Given two tickets that describe the same or nearly the same issue, when each is
   submitted, then each is triaged separately with its own echoed ID; neither is
   merged, deleted, nor suppressed.

8. Sensitive ticket handling is explicit and content-aware.

   A ticket is sensitive when the normalized subject or body contains language that
   indicates accessibility, data-retention, deletion, or escalation, such as:
   - accessibility: “screen reader”, “accessibility”, or “not announced by our screen reader”
   - data retention: “data retention”, “how long do you keep”, or “borrowing history”
   - deletion: “close my account”, “delete my history”, “remove me”, or “delete”
   - escalation: “urgent”, “escalation”, “blocked”, or “immediately”

   The repository fixtures `T-022`, `T-024`, `T-025`, and `T-030` are examples of
   the underlying content patterns; they are not special IDs that trigger a separate
   branch. A different ID with the same subject or body text must trigger the same
   sensitive handling.

   For a sensitive ticket, the API must still return the model's category, priority,
   team, confidence, version, and raw model result exactly as produced by the model.
   The top-level `draft_reply` must be a neutral acknowledgment that a human will
   review the case. It must not claim that a change, deletion, investigation, or
   policy decision has already happened. The endpoint returns a draft only; customer
   delivery is not part of this API.

   This rule is triggered by the ticket's content, not by a hidden hard-coded
   response map keyed to ticket IDs.

9. Given the model is unavailable, when the endpoint is called, then it returns HTTP
   503 with the existing `ErrorBody` shape and `code` `model_unavailable`.

10. Given the model times out, when the endpoint is called, then it returns HTTP 504
    with the existing `ErrorBody` shape and `code` `model_timeout`.

11. Given a request omits the ticket ID, supplies a value of the wrong type, or
    otherwise fails request validation, when it is submitted, then FastAPI returns
    HTTP 422. Subject and body may be omitted or empty as specified in AC6.

## 4. Scope and non-goals

**In scope:**

- Triage one ticket per request using its ID, subject, and body.
- Return category, priority, suggested team, draft reply, human-review flag, and model
  confidence, version, latency, and raw value.
- Keep similar tickets separate.
- Require human review for every draft, with neutral acknowledgment for sensitive
  tickets and neutral review wording for accessibility, retention, deletion, and
  escalation cases.
- Report model-unavailable and model-timeout failures through the existing API error
  contract.

**Explicitly out of scope:**

- Customer delivery, including sending a reply or contacting a customer; the
  repository has no customer-delivery integration for this endpoint.
- Merging, deleting, or otherwise deduplicating tickets.
- Persisting tickets, triage results, review decisions, or conversation history.
- Batch triage, ticket search/list endpoints, or a user interface.
- Making a policy decision about data retention or performing a deletion.
- Changing the repository model stub or its task behavior.

## 5. Interfaces and contracts

Add a ticket router under `app/routes/` and include it in `app/main.py`. Declare
request and response shapes in `app/models.py`; do not return a bare dictionary.

```http
POST /tickets/triage
Content-Type: application/json
```

Request: `id` is required; `subject` and `body` may be omitted or empty.

```json
{
  "id": "T-001",
  "subject": "Refund for duplicate charge",
  "body": "I was billed twice for my September membership. Please refund one."
}
```

Successful response:

```json
{
  "ticket_id": "T-001",
  "category": "billing",
  "priority": "normal",
  "suggested_team": "finance-ops",
  "draft_reply": "Thanks for writing in. I can see the charge you mean and I am checking it now.",
  "requires_human_review": true,
  "model": {
    "value": {
      "category": "billing",
      "priority": "normal",
      "team": "finance-ops",
      "draft_reply": "Thanks for writing in. I can see the charge you mean and I am checking it now."
    },
    "confidence": 0.86,
    "model_version": "v1",
    "latency_ms": 0
  }
}
```

The successful response embeds `ModelPayload`: `value` is the raw model result and
`confidence`, `model_version`, and `latency_ms` are the values returned by the model.
Top-level typed fields expose the result for callers. For sensitive-ticket cases,
the top-level `draft_reply` is a neutral human-review draft and may differ from the
raw draft in `model.value`. Other top-level fields reflect the model result. The
sample values illustrate shape only and must not be hard-coded. Every successful
response sets `requires_human_review` to `true`. The repository has no customer-
delivery integration; the observable contract ends with returning the draft.

Call `app.model_client.get_client().complete("classify_ticket", ticket_payload)`;
application code must not instantiate `StubModelClient` directly. Validation errors
use FastAPI's HTTP 422 response. Model errors use `{detail, code}`: HTTP 503 /
`model_unavailable` for `ModelUnavailable`, and HTTP 504 / `model_timeout` for
`ModelTimeout`.

## 6. Constraints

- Security / data handling: Do not persist the request, model result, or draft. No
  customer-delivery integration is in scope. Authentication and authorization are not
  defined by the starter repository.
- Performance: One ticket per request (maximum batch size: 1). The repository defines
  no response-time objective or text-size limit; this increment adds neither.
- Compatibility: Keep API shapes in `app/models.py` and use the existing
  `ErrorBody` and status codes. Do not add an ORM or put business logic in
  `app/main.py`.
- Model use: Call only through `get_client()`. Handle `ModelUnavailable` and
  `ModelTimeout` separately. Return model confidence, version, latency, and raw
  result in `ModelPayload`. Confidence below `0.5` remains visible and requires human
  review.
- Model versions: Return the actual version for each result; do not assume v1 and
  v2 produce identical outputs.
- Testing: HTTP tests use the `client` fixture and its throwaway database. Reset the
  cached model client when changing environment settings. Use `sleep=False` or
  `STUB_SLEEP=0` when simulating latency.
- Sensitive handling: Sensitive detection must be documented as a content-based check
  with explicit ID exceptions. A hard-coded ID-only rule is not sufficient because
  the product requirement is around ticket handling, not fixture names.

## 7. Test plan

Use `tests/test_tickets.py` for HTTP behavior. Name tests `test_ac<N>_...`, mapping
each test to its criterion number. Use the `client` fixture for endpoint tests and
`StubModelClient` or the `stub` fixture for deterministic model behavior. Assert
observable status codes and response values, not private call paths.

| Criterion | Test coverage |
|---|---|
| AC1 | Submit a valid ticket and assert HTTP 200, echoed ID, required fields, and complete model metadata. |
| AC2 | Use fixtures T-001 through T-004 to assert billing, access, data, and outage classifications; include a no-match general case. |
| AC3 | Assert v1 priority for an urgent ticket (including T-022), a matched non-urgent ticket, and a no-match ticket; assert the model-returned v2 general priority is preserved. |
| AC4 | Assert each category's corresponding team, including general/triage. |
| AC5 | Use ambiguous fixture T-016 and `wrongness=1.0`; assert confidence `< 0.5`, raw model result/version, and human-review flag are retained. |
| AC6 | Submit fixtures T-020 and T-021 and a request with both text fields empty; verify acceptance and human review for empty content. |
| AC7 | Submit a near-duplicate pair such as T-001 and T-011; assert separate responses with their respective IDs. |
| AC8 | Assert every success returns a draft and requires review; for sensitive content such as accessibility, retention, deletion, or escalation language, assert the neutral acknowledgment and human-review wording using different IDs with the same fixture text, rather than special-case ticket IDs. |
| AC9 | Set `STUB_FAILURE_RATE=1.0`, reset the cached client, and assert HTTP 503 with `code` `model_unavailable`. |
| AC10 | Configure latency above timeout with `sleep=False`; assert HTTP 504 with `code` `model_timeout`. |
| AC11 | Omit the ID and submit a wrong-typed field; assert HTTP 422. |

## 8. Open questions

- Product/support owner: Are the stub's category, priority, and team labels the intended
  user-facing vocabulary, or should the API translate them to an approved taxonomy?
- Product/support owner: Should accessibility, retention, and deletion tickets eventually
  have dedicated categories or teams? This increment uses the model's category/team and
  requires a neutral human-reviewed draft.
- Support / privacy owner: What policy response and authorized workflow should apply to
  retention and deletion requests? This increment does not answer retention questions or
  perform deletion.
- API/security owner: What authentication and authorization are required before the endpoint
  is exposed beyond the local starter application?
- Product/API owner: Are request text-size limits or a response-time objective required?
  The repository does not establish either.
- Assignment owner: Should related tickets eventually be identified or linked without
  merging them? This increment treats each request independently.

## Review checklist

- [ ] Could someone who has never spoken to me build from this without asking me a question?
- [ ] Is every acceptance criterion testable as written?
- [ ] Are the unhappy paths covered?
- [ ] Does §4 name what we are *not* building?
- [ ] Are the constraints specific enough to constrain?
- [ ] Have the people who own the constraints — UX, QE, security — actually seen this?
