---
name: api-conventions
description: >
  Use whenever adding or changing an HTTP endpoint, a request or response model, or a
  filter in this repository. Names the shapes, the error contract and the file layout,
  so new endpoints match the ones already here.
---

# API conventions

## Layout

- Routers live in `app/routes/<area>.py` and are included in `app/main.py`.
- Every request and response shape is declared in `app/models.py`. Nothing crosses the
  API boundary as a bare `dict`.
- Filters are declared once in `app/filters.py` and reused. A new filter is an entry in
  `FILTERS` plus a query parameter in the route's `_query_params`.

## Shapes

- **List endpoints return `Page`** — `{items, total, limit, offset}`. Never a bare list.
- `limit` defaults to 50, maximum 200. `offset` defaults to 0.
- **Errors return `ErrorBody`** — `{detail, code}`. Raise `HTTPException` as the existing routes do;
  the handler in `app/main.py` adds `code` (`not_found`, `conflict`, `model_unavailable`,
  `model_timeout`). Use the status codes already in use: `404` not found, `409` conflict,
  `422` validation (FastAPI does this for you, with its own body shape), `503` model unavailable,
  `504` model timed out.
- Two-letter state codes are stored and compared **uppercase**.

## Calling the model

Always through `app.model_client.get_client()`. Never construct `StubModelClient`
directly in application code — tests do that, application code does not.

Wrap every call:

```python
try:
    result = get_client().complete("task_name", payload)
except ModelTimeout as exc:
    raise HTTPException(status_code=504, detail=str(exc)) from exc
except ModelUnavailable as exc:
    raise HTTPException(status_code=503, detail=str(exc)) from exc
```

**Return the confidence and the model version to the caller.** Embed `ModelPayload` in
the response the way `DescribeResponse` does; its `value` carries the model's raw result — a string
for a summary, the dict or list the task returned for a structured answer — even when the response
also presents it in typed fields. Do not silently drop a low-confidence
answer and do not silently show it as if it were certain — the response must let the
caller tell the difference.

`app/routes/libraries.py::describe_library` is the worked example. Copy its shape.

## Things not to do

- Do not add an ORM. This app uses `sqlite3` directly and the queries are readable.
- Do not add a new error shape.
- Do not put business logic in `app/main.py`.
- Do not write raw SQL in a route when a filter would do.
