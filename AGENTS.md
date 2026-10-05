# Agent instructions

Tool-agnostic version of `.claude/skills/`. Read this before changing anything.

## Getting oriented

- `make test` runs everything. It must be green before you finish.
- `app/routes/libraries.py` is the pattern for endpoints. `describe_library` is the
  pattern for calling the model. Copy them rather than inventing a new shape.

## Rules

1. **List endpoints return `Page`** (`{items, total, limit, offset}`), never a bare list.
2. **Every request and response shape is declared in `app/models.py`.** Nothing crosses
   the API boundary as a bare `dict`.
3. **Filters go in `app/filters.py`**, declared once in `FILTERS` and reused. Do not
   write ad-hoc SQL in a route.
4. **Errors use `ErrorBody`** (`{detail, code}`). Status codes already in use: 404, 409,
   422, 503 (model unavailable), 504 (model timed out).
5. **Call the model only through `app.model_client.get_client()`**, wrapped in
   `try/except ModelTimeout, ModelUnavailable`. Return the confidence and model version
   to the caller — do not drop them.
6. **Do not add an ORM, a new error shape, or business logic in `app/main.py`.**
7. **Tests use the `client` fixture** (throwaway database). Name tests after the
   acceptance criterion they cover: `test_ac3_...`.

## When implementing from a specification

Implement what the specification says. Where it is silent, **write down the assumption
you made** in your final message rather than quietly picking one — the gap between what
the document said and what you had to guess is the thing being measured.

Do not ask clarifying questions during a blind handoff. Proceed on your best reading and
report what you had to decide. Do not write the acceptance tests unless asked — those belong
to the specification's author, so that they measure the document rather than your reading of it.
