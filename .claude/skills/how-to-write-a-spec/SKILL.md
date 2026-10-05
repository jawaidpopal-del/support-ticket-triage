---
name: how-to-write-a-spec
description: >
  Use whenever the task is to write, review or revise a feature specification for this
  repository. Produces a specs/<feature>.md following the template, and pulls the
  repository's API and testing conventions into it so implementation reads only the spec.
---

# Writing a feature specification here

One feature, one file, in `specs/`. Two to four pages. Name it after the feature:
`specs/filtered-summary.md`, not `specs/spec.md` — unless an assignment fixes the name. The Week 5
assignment does: `specs/spec-v1.md`, then `specs/spec-v2.md`, so the grader can find them.

## Before writing, read

- `.claude/skills/api-conventions/SKILL.md` — request and response shapes, error
  handling, where routes live. **Section 5 and section 6 of the spec must reflect this.**
- `.claude/skills/testing/SKILL.md` — how tests are structured here. **Section 7 must
  reflect this.**

Pull the *specific* rules from those files into the spec as concrete sentences. Do not
write "follow the repository conventions" — that constrains nothing. Write "the list
endpoint returns `Page`" and "errors use `ErrorBody` with a `code` field".

## The eight sections

1. **Intent** — what problem, for whom, in three or four sentences. No implementation.
2. **User stories** — small. If a story needs "and" twice, it is two stories.
3. **Acceptance criteria** — numbered, and written given / when / then. Each one must
   be something you can write an assertion against. **Include the unhappy paths.**
4. **Scope and non-goals** — name the adjacent things you are deliberately not building.
5. **Interfaces and contracts** — endpoint, method, query parameters, request and
   response bodies with a worked example of each.
6. **Constraints** — from the two skills above, plus performance limits *with numbers*.
7. **Test plan** — which criterion is covered by which test, by number.
8. **Open questions** — what you do not know, and who could answer it.

## The unhappy paths this repository actually has

A specification here is not finished until it answers all of these:

- The input selects **zero** of anything — an empty filter result, no matching documents, an
  empty diff, a goal with no applicable operation.
- The input is **bigger than one page or one call can hold** — more records than the page size,
  a four-thousand-line diff, a plan with more steps than it may run unattended.
- The model returns **low confidence** (`< 0.5`). Show it, hide it, or refuse to answer?
- The model **fails** (`ModelUnavailable`) or **times out** (`ModelTimeout`). These are
  different and may deserve different handling.
- The model returns a **confidently wrong** answer. What in the response lets a caller tell?
- The model **version changes** from `v1` to `v2` and the answer changes with it.
- Two requests arrive for the same thing **at once**.

## Where to stop

Specify observable behaviour and contracts. Do not specify private function names, data
structures, or the order of steps nobody can observe. If you are writing pseudocode, you
have gone too far.
