# What a blind handoff actually reports

**Dry run, Sep 22.** A fresh agent — no conversation history, nothing but the repository
and `specs/filtered-summary.md` — was told:

> Implement the feature specified in `specs/filtered-summary.md`. Follow the conventions
> already in the repository.

**Result: all 8 of the spec author's acceptance tests — covering its seven criteria — passed against its code.** The
specification was implementable blind. That is the claim the whole exercise rests on.

What follows is the implementer's own report, verbatim. Read section 3 and section 4:
**this is what a good gap analysis looks like.** Specific lines quoted, specific
decisions named, and two of its complaints about the specification were simply correct —
the spec has since been fixed for both (see the git history for `specs/filtered-summary.md`).

---

## 1. FILES CHANGED
- Created `app/cache.py` — `TTLCache` (process-local, locked, injectable clock)
- Created `tests/test_summary.py` — `test_ac1_` … `test_ac7_` *(the session's own tests; `AGENTS.md` now tells implementers not to write acceptance tests — the tests scored above were the author's, kept outside the session)*
- Edited `app/models.py` — `SummaryResponse`
- Edited `app/routes/libraries.py` — `GET /libraries/summary`, registered before `/{library_id}`
- Edited `tests/conftest.py` — `client` fixture also clears the summary cache

## 2. TEST RESULT
`51 passed in 0.20s` (its own suite). Then, separately, the spec author's eight
criterion tests: `8 passed`.

## 3. ASSUMPTIONS (the implementer's words)
- §5 shows `model` without `value`; §6 says "embeds `ModelPayload`", which requires `value`. Chose `ModelPayload` with `value` = the truncated `summary`, mirroring `DescribeResponse`.
- Spec never says what is cached. Only responses carrying a summary are cached; zero-row responses and model failures are not (a failure would otherwise persist for 10 minutes).
- A cache hit returns the whole first response, including `count`, since the summary text states the count.
- "`word_count` always reports the returned length": 0 and `truncated=false` when `summary` is null.
- Word = whitespace token; no ellipsis added; untruncated text returned verbatim.
- `model_error` is `"model unavailable: …"` / `"model timed out: …"` so callers can tell them apart.
- Low confidence: shown with its score, no threshold.
- Model payload (spec silent): count, English filter description, states/kinds by frequency, `median_low` visits.
- Cache key is filters only, per §6, so a v1→v2 switch inside the window serves the v1 entry, labelled v1. Concurrent misses may both call the model; no single-flight.
- `limit`/`offset` ignored; the summary covers all matching rows.

## 4. SPEC PROBLEMS (the implementer's words)
- §7 AC2: "stub returns 70–95 words" — it actually returns 65 (v1) / 66 (v2). **Correct. Fixed.**
- §5/§6 conflict on `value`. **Correct. Fixed.**
- Silent on low confidence and concurrent requests, both mandatory per the repo's own spec skill. **Correct. Both now decided in §6.**
- "Normalised" only uppercases `state`; `city=Boston` and `city=boston` are two cache entries, contrary to §6's stated aim. **Correct — a real bug in `filters.active()`. Fixed, with a test.**
- Silent on whether failures or empty selections are cached. **Correct. Now decided in §6.**
- §7 AC5 "assert the summaries differ" is a weak proxy. **Correct. Reworded.**

---

Notice what the implementer did *not* do: it did not ask a question, and it did not
guess silently. It decided, and it wrote the decision down. That report is worth more
than the code.
