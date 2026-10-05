# Facilities API — starter repository

A small records API with two model-backed endpoints already working. It is the starting
point for the Week 5 specification exercise: you will add a substantial feature to it
from a written specification, handed to an agent that has never seen your conversation.

**No API key. No GPU. No prior AI experience.** The model is a stub that runs locally.

---

## Start here

```bash
make setup     # create .venv and install (Python 3.11+)
make test      # 53 tests, about a second
make run       # http://127.0.0.1:8000/docs
```

If `make test` is green, you are ready. Nothing else needs configuring.

## What is in here

```
app/
  main.py            FastAPI app; routers are included here
  models.py          every request and response shape
  filters.py         the filter layer, declared once and reused
  db.py              SQLite; schema created and seeded on first use
  model_client.py    THE STUB MODEL — read this one
  fixtures.py        loaders for the sample inputs in data/
  routes/
    libraries.py     list, get, create, and one model-backed endpoint (describe)
    summary.py       the second one — the worked example: spec → route → tests
data/                sample inputs for every assignment option
specs/               your specification goes here
tests/               run with `make test`
demo/                the in-class example: flawed first draft, approved spec, round-1 exhibit
logs/                where your blind-handoff transcripts go
docs/fixtures.md     what is planted in the sample data, and why
.claude/skills/      how this repo expects specs, endpoints and tests to be written
```

## The endpoints that exist

| | |
|---|---|
| `GET /libraries` | list, filtered, paginated — returns `Page` |
| `GET /libraries/{id}` | one record |
| `POST /libraries` | the write path; rejects a duplicate name in the same city |
| `GET /libraries/{id}/describe` | **model-backed.** Copy this one's shape |
| `GET /libraries/summary` | a complete worked example — `specs/filtered-summary.md` → route → `tests/test_summary.py`. Copy its shape |
| `GET /health` | liveness |

`describe_library` in `app/routes/libraries.py` is the worked example of calling the
model: fetch your data first, wrap the call, and return the confidence and model
version to the caller instead of swallowing them.

## The stub model

`app/model_client.py`. Deterministic by default — the same input always produces the
same output. It knows seven tasks, one per assignment option plus two the app already
uses. Every result carries a **confidence score** and a **model version**.

It can be told to misbehave, and you should tell it to:

```bash
STUB_LATENCY_MS=800    make run    # slow
STUB_FAILURE_RATE=0.3  make run    # fails three calls in ten
STUB_TIMEOUT_MS=200    make run    # raises when latency exceeds this
STUB_WRONGNESS=1.0     make run    # plausible answers that are wrong, at low confidence
STUB_MODEL_VERSION=v2  make run    # the other version; it disagrees with v1 on purpose
```

**Handling the wrong answer is most of the work in every assignment option.** If you
only ever test the stub being right, you have specified about a third of your feature.

## Conventions, in three files

This repository ships its own skills, in `.claude/skills/`. They are an example of the
thing the session is about — and they are loaded automatically by an agent working here.

- `how-to-write-a-spec` — the eight sections, and the unhappy paths this repo has.
  It **references the other two**, so a spec written with it already carries their rules.
- `api-conventions` — shapes, error contract, how to call the model.
- `testing` — fixtures, how to make the stub misbehave, how to name a test after the
  acceptance criterion it covers.

Using Copilot or Cursor instead? `AGENTS.md` carries the same rules in one file.

## For the assignment

1. **Reconnaissance** — describe your feature in one or two sentences, let the agent start, do
   not correct it, write down every assumption it made. Then throw the code away.
2. **Write the specification** into `specs/`, using the template.
3. **Blind handoff** — new session, no history. Hand it this repository and your spec.
   Do not chat it into shape.
4. **Close the gap** — fix the *specification*, not the code, and hand off again.

Sample inputs for all five options are in `data/`, already loaded by `app/fixtures.py`.
Read `docs/fixtures.md` first — the awkward cases in there are deliberate, and they are
the ones your specification has to have an answer for.
