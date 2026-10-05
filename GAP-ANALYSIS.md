# Gap Analysis: Support Ticket Triage

## Scope and evidence base

This analysis is based only on the repository evidence in `specs/spec-v1.md`, `specs/spec-v2.md`, `tests/test_tickets.py`, `logs/handoff-1.md`, `logs/handoff-2.md`, and the actual implementation in `app/routes/tickets.py`, `app/models.py`, `app/main.py`, and `app/model_client.py`.

It distinguishes between:

- test results, which are observable outcomes from the recorded pytest runs, and
- code-review findings, which are conclusions drawn from the implementation and spec text, even when the tests passed.

## 1. Assumptions from reconnaissance

The recorded reconnaissance and handoff history show a sequence of assumptions that were not fully settled by the original spec.

First, there was a strong assumption that the feature was built around the repository stub's `classify_ticket` behavior rather than a production model. That is visible in the way the code and tests rely on `get_client().complete("classify_ticket", ...)`, and in the fact that the acceptance criteria refer to stub clues and model versions (`v1`, `v2`). This is consistent with the repository design: the model client is a deterministic stub, not a real external service.

Second, the original round-one implementation assumed that sensitive handling could be represented as a static set of known IDs. That assumption is explicit in the code: the route contained `_SENSITIVE_TICKETS = {"T-022", "T-024", "T-025", "T-030"}` and then chose a neutral draft when `body.id in _SENSITIVE_TICKETS`. This was not necessarily wrong as a tactical implementation for the repository fixtures, but it was a code-level assumption that the product behavior was keyed to specific IDs rather than to ticket content.

Third, the repository's own wording around AC8 was broader than the code. The spec language discussed accessibility, data-retention, deletion, and escalation tickets, and said those should receive neutral human-review drafts. The code reviewed in round one hit the fixture IDs, not the underlying content indicators. This mismatch is exactly the kind of latent gap that a code review can reveal even when a fixture-based test passes.

Finally, the written spec and tests also over-prescribed some elements that are not truly product requirements. For example, the repository stub uses explicit keyword groups to determine category and priority, and the specification names those clue words and even some version-specific behaviors. Those details are valid as tests for this repository, but they are more “stub behavior” than product policy. The implementation was also allowed to use those exact patterns because the project is intentionally built around a deterministic stub.

## 2. Round-one acceptance criteria: passed or failed, based on recorded test output

The recorded test output from `logs/handoff-1.md` and `logs/handoff-2.md` shows the following:

- The ticket triage test file passed in the recorded run: `.......................... [100%]`.
- The full suite also passed in the recorded run: `........................................................................ [ 91%]` followed by `....... [100%]`.

That means the observable, recorded test results for round one show that the repository's acceptance test suite passed under the repository environment. The passing output does not, however, prove that every code-path assumption in the spec was well-specified or that the implementation matched the intended product semantics in every respect. The distinction is important: this is a test result, not a code-review verdict.

From the actual tests in `tests/test_tickets.py`, the acceptance criteria that were explicitly covered and passed include:

- AC1 through AC11 all have corresponding tests in the file.
- AC8 is covered by the fixture-based test that calls the route for `T-022`, `T-024`, `T-025`, and `T-030`.
- The code path for model error handling and validation also appears to be covered and passing.

The critical point is that the test suite passed because it validated the implementation as written against the repository fixtures. It did not prove that the sensitive-ticket rule was correctly defined at the product level, because the test used special-case IDs as the trigger and therefore did not exercise a content-based rule.

## 3. The AC8 code-review gap: ID-based rule despite content-based intent

The biggest code-review gap is in AC8.

In round one, the implementation used a hard-coded ID allowlist:

```python
_SENSITIVE_TICKETS = {"T-022", "T-024", "T-025", "T-030"}
...
if body.id in _SENSITIVE_TICKETS:
    draft_reply = _neutral_human_review_draft()
```

This is in `app/routes/tickets.py`.

This is a code-review concern because the specification text never stated that sensitive handling is keyed to special IDs. The prose in spec v1 and v2 discussed sensitive tickets in terms of case types (accessibility, retention, deletion, escalation) and the content or issue theme. The fixture IDs were examples, not the described rule.

The test passing did not catch this because the test itself was fixture-based. The test in round one used only the IDs `T-022`, `T-024`, `T-025`, and `T-030`, and therefore it validated the implementation's local assumption without proving the rule was content-aware. The passing result is therefore a “tests passed under the hard-coded rule” result, not a proof that the product rule was correctly implemented.

## 4. Original and revised spec lines, and how the new different-ID content test checks the fix

### Original spec lines (from v1, as recorded in `specs/spec-v1.md`)

The original acceptance criterion language says:

> "Given any successfully triaged ticket, when the response is returned, then `requires_human_review` is `true` and `draft_reply` is present for the human reviewer. For accessibility (T-024), data-retention (T-025), deletion (T-030), or escalation (T-022) tickets, the draft acknowledges receipt and says a human will review it. It must not claim that a change, deletion, investigation, or policy decision has already happened. The endpoint returns a draft only; customer delivery is not part of this API."

This wording uses specific fixture IDs as examples of cases, and the implementation interpreted this as a special-case ID rule.

### Revised spec lines (from v2, as recorded in `specs/spec-v2.md`)

The revised AC8 says:

> "A ticket is sensitive when the normalized subject or body contains language that indicates accessibility, data-retention, deletion, or escalation, such as:
> - accessibility: “screen reader”, “accessibility”, or “not announced by our screen reader”
> - data retention: “data retention”, “how long do you keep”, or “borrowing history”
> - deletion: “close my account”, “delete my history”, “remove me”, or “delete”
> - escalation: “urgent”, “escalation”, “blocked”, or “immediately”
>
> The repository fixtures `T-022`, `T-024`, `T-025`, and `T-030` are examples of the underlying content patterns; they are not special IDs that trigger a separate branch. A different ID with the same subject or body text must trigger the same sensitive handling."

That is the fix to the code-review gap.

### How the new different-ID content test checks the fix

The revised test in `tests/test_tickets.py` uses different IDs on the same content examples, for example:

- `T-999` with subject/body about accessibility
- `T-998` with data-retention wording
- `T-997` with deletion wording
- `T-996` with escalation wording

This matters because it verifies the rule is keyed to the ticket text, not to specific ticket IDs. A different ID with the same content must trigger the same neutral draft behavior. The test asserts the neutral review language and checks that the draft does not claim a deletion, fix, or resolution has already happened.

This is stronger than the earlier fixture-ID test because it checks the actual product property: the content of the ticket should be treated with the neutral review rule, regardless of the ticket number.

## 5. What round two still got wrong, if anything, and a possible v3 change

Round two addressed the gap by changing the implementation to inspect subject/body content rather than a hard-coded ID set. That change is consistent with the revised AC8 and the different-ID test.

However, even in the revised version, there are still product-level questions left open. The primary one is this: the rule uses a few hard-coded phrases and patterns, which is workable for a stub and for the repo fixtures, but it is not a general content classifier. It is effectively a regex-like heuristic on a small list of phrases. That makes it testable and deterministic, but it is still a mechanism, not a product policy.

A reasonable v3 change would be to replace the phrase list with a more explicit, policy-driven definition of “sensitive content,” such as:

- sensitivity categories: accessibility, retention, deletion, escalation
- a normalized input text field that concatenates subject/body
- a single helper function that returns a boolean based on those categories
- a shared vocabulary list owned by product or policy, rather than embedded in the route.

In other words, the code should not rely on a route-local list of literal phrases unless the product explicitly wants that kind of rule. This would reduce the chance of accidental overfitting to a few fixture examples.

## 6. Where the specifications over-prescribed details

The repository spec and tests over-prescribe several implementation details that are better treated as stub-specific or repository-internal mechanics rather than product requirements.

Examples include:

- the specific clue words used to classify billing, access, data, and outage cases
- the exact priority logic based on urgency words and category matches
- the exact team name mappings for each category
- the model-version differences (`v1` vs `v2` general priority behavior)
- the specific English-language draft strings chosen by the stub

These details are valid for this repo because the stub’s `classify_ticket` task is deterministic and intentionally designed around those clues. But they are not generally the correct product contract for a real triage feature. They are internal mechanics of the stub, not necessary policy rules.

The same is true of the phrase lists used to decide sensitive handling. Those are heuristic examples, not a universal legal or policy definition. That is why the later v2 revision rightly moves the requirement toward “language that indicates accessibility, data-retention, deletion, or escalation,” and then adds a content-based test that uses different IDs.

This is a good example of a spec improving from a fixture-driven implementation to a more general, content-based requirement while still remaining grounded in the stub.

## Conclusion

The recorded test output shows that round one passed the repository test suite. The code review, however, found a real gap: the implementation hard-coded sensitive-ticket detection to specific IDs, even though the intended behavior was content-based. The v2 revision fixed the specification and test by requiring content-based sensitive handling and by validating it with different IDs carrying the same wording. The actual implementation was then updated to match that v2 requirement.

The distinction between passing tests and correct intent is the central lesson in this analysis: fixture-based success can hide a semantic bug in a rule that is conceptually wrong, even while satisfying the repository’s current test set.
