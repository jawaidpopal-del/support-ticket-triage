# Feature Specification — Filtered summary

**Status:** draft · **Author:** drafted by the agent, 7:22 · **Reviewers:** —

> **This is the FIRST DRAFT, with its problems left in.** It is kept so the class can see
> what an agent's first pass actually looks like: well-organised, complete-looking, and
> wrong in three quiet places. The approved version is `spec-v2.md`.

## 1. Intent

When someone filters the facilities list, they cannot tell at a glance what the current
selection contains. Give them a short plain-English summary of the rows they have
filtered to, so they can judge whether the filter is right before reading the rows.

## 2. User stories

- As an analyst, I want a summary of my current filter, so that I can sanity-check it.

## 3. Acceptance criteria

1. Given a filter that matches rows, when the summary endpoint is called, then a
   plain-English summary of the matching rows is returned.
2. The summary is concise.
3. The summary is cached, so repeated requests do not re-run the model.
4. The response includes the model's confidence.

## 4. Scope and non-goals

**In scope:** a summary of the filtered set.
**Out of scope:** per-row summaries, export, translation.

## 5. Interfaces and contracts

`GET /libraries/summary` accepting the same filters as `GET /libraries`.

Returns the summary text and the model metadata.

## 6. Constraints

Follow the repository's API conventions. Use the existing stub model client.

## 7. Test plan

Unit tests for the summary endpoint covering the criteria above.

## 8. Open questions

None.
