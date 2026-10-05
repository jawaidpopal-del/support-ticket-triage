# Feature Specification — Filtered summary

**Status:** approved · **Author:** drafted by the agent, revised in review
**Reviewers:** the room, 7:24 · **Date:** 2026-09-23

## 1. Intent

When someone filters the facilities list they cannot tell at a glance what the current
selection contains. Give them a short plain-English summary of the rows they have
filtered to, so they can judge whether the filter is right before reading the rows.
The summary is an aid to scanning, not a report: it is allowed to be absent.

## 2. User stories

- As an analyst, I want a one-paragraph summary of the rows my filter matched, so that
  I can tell whether the filter is right before I read them.
- As an analyst, I want repeated views of the same filter to be instant, so that
  scrolling and re-rendering do not cost me a wait.

## 3. Acceptance criteria

1. Given a filter matching one or more rows, when `GET /libraries/summary` is called
   with those filters, then the response has HTTP 200, `count` equal to the number of
   matching rows, and a non-empty `summary`.
2. Given the model returns a summary longer than 60 words, when it is returned to the
   caller, then it is truncated at a word boundary to at most 60 words and
   `truncated` is `true`. `word_count` always reports the returned length.
3. Given the same normalised filter set is requested twice inside the cache window,
   when the second request arrives, then it returns the first response's summary,
   `cached` is `true`, and **the model is not called a second time**.
4. Given a filter matching zero rows, when the endpoint is called, then `count` is `0`,
   `summary` is `null`, and **the model is not called at all**.
5. Given two *different* filter sets, when each is requested, then each receives a
   summary computed for its own rows. A cache entry for one filter set is never
   returned for another.
6. Given the model raises `ModelUnavailable` or `ModelTimeout`, when the endpoint is
   called, then the response is still HTTP 200 with `summary` `null` and `model_error`
   set to a short reason. **The endpoint never returns 5xx because the model failed.**
7. Given a summary was produced, when the response is returned, then `model` contains
   the `confidence` and `model_version` that produced it.

## 4. Scope and non-goals

**In scope:** one summary of the currently filtered set, over the existing filters.

**Explicitly out of scope:** per-row summaries; summarising an arbitrary id list;
export or download of the summary; translation; a history of past summaries;
invalidating the cache when an underlying row is edited (see §8).

## 5. Interfaces and contracts

```
GET /libraries/summary?state=MA&kind=branch        # the same filters as GET /libraries

200 {
  "count": 34,
  "filters": {"kind": "branch", "state": "MA"},
  "summary": "This selection holds 34 facilities ...",   # or null
  "word_count": 60,
  "truncated": true,
  "cached": false,
  "model": {"value": "...", "confidence": 0.88, "model_version": "v1", "latency_ms": 0},  # ModelPayload, or null
  "model_error": null
}
```

`filters` echoes the normalised active filter set — the same value used as the cache
key. Unknown query parameters are ignored, exactly as on `GET /libraries`.

## 6. Constraints

- **Cache key** is the normalised active filter set (`app.filters.active`): key order,
  unset filters, and letter case in text filters cannot produce two entries for one
  selection. `city=Boston` and `city=boston` are one key.
- **Only responses that carry a summary are cached.** An empty selection (AC4) and a
  model failure (AC6) are never cached, or a ten-minute outage would be served for ten
  more minutes.
- **Cache lifetime** is 10 minutes from write. Process-local; no external store.
- **Low confidence is shown, not hidden.** The score is returned as-is; no threshold is
  applied in this increment. A caller that wants to suppress low-confidence summaries
  reads `model.confidence`.
- **Concurrent misses** on the same key may both call the model. Single-flight is out
  of scope for this increment.
- **Model version** is not part of the cache key. A `v1`→`v2` switch inside the window
  serves the cached `v1` entry, labelled `v1` in `model.model_version`.
- **Word cap** is 60, enforced server-side. The model does not respect it.
- **Model access** goes through `app.model_client.get_client()`, per `api-conventions`.
- The response embeds `ModelPayload`, as `DescribeResponse` does.
- **A model failure must not fail the request.** This endpoint degrades; it does not error.
- Route registration: `/libraries/summary` must be registered **before**
  `/libraries/{library_id}`, or the path-parameter route captures it first.

## 7. Test plan

One test per criterion in `tests/test_summary.py`, named `test_ac<N>_...`. **The route module
must expose `clear_cache()`**; the `client` fixture in `tests/conftest.py` calls it between
tests so cached state never leaks from one test into the next.

| | |
|---|---|
| AC1 | happy path over a real filter |
| AC2 | stub returns 65–70 words; assert ≤ 60 and `truncated` |
| AC3 | call twice; assert `cached` and that the client recorded one call |
| AC4 | filter matching nothing; assert no model call |
| AC5 | two filters with different counts; assert the second is not `cached` and its `count` differs |
| AC6 | `STUB_FAILURE_RATE=1.0` and a timeout; assert 200 and `model_error` |
| AC7 | assert `confidence` and `model_version` present |

## 8. Open questions

- Should a **stale** cached summary be shown while a fresh one is generated, or should
  the caller wait? Unanswered — ask product before the cache window is tuned.
- Should editing a row invalidate cache entries whose filter matched it? Out of scope
  for this increment, but it is the first thing that will be reported as a bug.
