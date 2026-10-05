# The human review pass — what to find on camera

Step 2 of the loop, live, at about 7:24. Read `spec-v1.md` on screen and find these
three. Do not rush it: this is the centre of gravity of the whole segment.

| | The draft says | Why it is not good enough | What replaces it in v2 |
|---|---|---|---|
| 1 | AC3: *"The summary is cached."* | Keyed on **what**? Invalidated **when**? An agent can satisfy this with one global cache — and then a different filter returns the previous selection's summary. | AC3 + AC5: cached **per normalised filter set**, expiring after 10 minutes. |
| 2 | AC2: *"The summary is concise."* | Concise is not a number, and the model does not respect it — the stub returns 65–70 words. Nothing enforces anything. | AC2: **at most 60 words, enforced server-side**, truncated on a word boundary. |
| 3 | *(absent)* | No empty-result path and no model-failure path. Both will happen. | AC4 (zero rows: no summary, **no model call**) and AC6 (model fails: list still renders, `summary: null`). |

Say the general lesson out loud once all three are found:

> The draft was well-organised, well-written, complete-looking, and wrong in three quiet
> places. That is the normal case, and it is why step 2 has a human in it.

Also worth pointing at: section 8 says **"None."** An agent will almost always write that.
A real spec for this feature has at least one open question — see v2.
