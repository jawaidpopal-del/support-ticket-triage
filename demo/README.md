# Fallback demo — runbook

**The live demo now runs on a separate repository, <https://github.com/jmrthms/sdd-demo-meshview>.**
This runbook is the fallback of last resort if that repository cannot be used; nothing here is needed
for the assignment.

**Dry-run completed Sep 22. Every artifact in this folder has been built and verified.**

The 7:15–7:45 segment. One feature carried from a sentence of intent to passing tests,
with the first draft wrong and the failure left in.

---

## What is prepared

| | |
|---|---|
| `spec-v1.md` | The agent's first draft, **with its three problems left in** |
| `REVIEW-NOTES.md` | The three problems, what is wrong with each, and what replaces it |
| `spec-v2.md` | The approved version (same file as `specs/filtered-summary.md`) |
| `round-1/summary.py` | A faithful implementation of v1 — the failure exhibit |
| `run-round-1.sh` | Swaps it in, runs the v2 criteria against it, restores |

The finished round-2 code is already in the repo: `app/routes/summary.py` and
`tests/test_summary.py`. **That is your fallback.** If the live build dies, you have a
working implementation and eight passing tests on disk.

## Verified result

```
round 1 (from spec-v1)                      5 of 8 acceptance criteria FAIL
round 2 (from spec-v2)                      8 tests pass, covering all seven criteria (AC6 has two)
blind handoff — a fresh agent, spec only    8 tests pass, and it found six real spec gaps
```

The blind implementer's full report is in `BLIND-HANDOFF-REPORT.md`. It is the best
example of a gap analysis you have — show it if anyone asks what "specific and evidenced"
means.

The AC5 failure reads `assert 10 != 10` — the second filter got the first filter's
cached body, count and all. It is visible and understandable in ten seconds on camera.

---

## The run

**7:15 · Set up (4 min)** — `sec-3`, then `demo-request`. Read the request aloud. Ask the
room for two undecided things before you supply the rest. Then `demo-loop`, and switch.

**7:19 · Step 1 — draft (4 min)**

> Draft a feature specification for this using the spec-authoring skill. The request is:
> "When someone filters the list, show a plain-English summary of what the user is
> looking at. Keep it short. Do not re-run the model on scroll."

Narrate while it runs — say out loud that section 6 is being written from the
api-conventions skill and you did not type any of it.

**7:23 · Step 2 — read it as a human (6 min) — the centre of gravity**

Open `demo/spec-v1.md` beside whatever the agent just produced. Find the three problems
from `REVIEW-NOTES.md`: the cache with no key, "concise" with no number, and the two
missing paths. Do not rush this.

Land the line: *the draft was well-organised, well-written, complete-looking, and wrong
in three quiet places.*

**7:29 · Step 3 — fix and approve (2 min)** — edit on screen, then land the approved version:
`cp demo/spec-v2.md specs/filtered-summary.md`. Commit it.

**7:31 · Step 4 — the blind handoff (5 min)** — cold session, scroll up to show it is
empty, then:

> Implement the feature specified in `specs/filtered-summary.md`. Follow the conventions
> already in the repository.

Do **not** ask it to write tests — those are yours, and they already exist. If it asks a question, **do not answer it** — write the question on screen and tell it to
proceed on its best judgement. That moment teaches more than a clean run.

**7:36 · Step 5 — run the tests (4 min)**

Open `tests/test_summary.py` — **written by you, from the criteria, before the handoff.** Say
that out loud: if the session that wrote the code also wrote the tests, they would pass
against its own reading and prove nothing.

Run them. Point at the naming — `test_ac5_different_filters_get_different_summaries` —
and say why: a red test points at a line in a document, not just at a function.

**7:40 · Step 6 — the failure (4 min)**

If the live implementation passes everything — likely, because v2 is a good spec — do
**not** pretend otherwise. Say so, and show the prepared exhibit instead:

```bash
bash demo/run-round-1.sh
```

*"This is what version one's cache criterion actually produced. Five of eight."*

Then the point, which is the same either way: **fix the specification, not the code.**
Somebody will say "just change the cache key." Say out loud — *I could. Then the code is
right and the document is still wrong, and the next person to read it makes the same
mistake.*

**7:44 · Back to the deck** — `blind-handoff`, then `what-you-saw`. Questions.

---

## Before you start

- [ ] `git checkout demo/start` — the repository **without** the feature. `make test` shows
      45 passed, **8 failed**: those are the criterion tests, red until the feature exists.
      That is correct and it is the point — say so if anyone notices.
- [ ] `git status` clean
- [ ] Second agent session open in a **separate window**, already `cd`'d here, no history
- [ ] `demo/spec-v1.md` and `REVIEW-NOTES.md` open in tabs you can reach fast
- [ ] Terminal and editor font sizes raised for screen share
- [ ] Share **the editor window only** — the deck has your notes on it

## Fallbacks

**It is slow.** Talk over it. You have the whole skills-to-spec story to narrate.

**The generated code does not run.** Say so — *this is the failure mode I warned you
about, and it is not rare* — then:

```bash
git stash -u && git checkout main && make test
```

The `-u` matters: the spec you copied in at step 3 and whatever the session wrote are
*untracked*, and a plain `git stash` leaves them behind, so `checkout main` refuses.
Everything the session was going to build is already on `main`; the stash keeps the live
attempt for the recording.

**Tooling or network is gone.** Go to `what-you-saw` and walk the four points from
`spec-v1.md` against `spec-v2.md` on screen. Eight minutes instead of thirty. Spend the
rest on Part 4 — that is the segment she asked for.

**Never debug live for more than 90 seconds.** It reads as chaos on a recording.
