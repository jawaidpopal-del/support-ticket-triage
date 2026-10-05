---
name: testing
description: >
  Use whenever writing or changing tests in this repository. Covers the fixtures, how to
  make the stub model misbehave, and the naming convention that maps a test to the
  acceptance criterion it covers.
---

# Testing conventions

Run everything with `make test`. That is the only command.

## Fixtures

- `client` — a FastAPI `TestClient` on a **throwaway database**. Use it for anything
  that goes over HTTP. Never assert against a database another test wrote to.
- `stub` — a well-behaved `StubModelClient`. Override fields to make it misbehave.

## Making the model misbehave

In a unit test, construct the client directly:

```python
StubModelClient(failure_rate=1.0)                      # always raises ModelUnavailable
StubModelClient(latency_ms=500, timeout_ms=100, sleep=False)   # always raises ModelTimeout
StubModelClient(wrongness=1.0)                         # plausible answer, low confidence
StubModelClient(model_version="v2")                    # the other model version
```

Through the API, set the environment and reset the cached client:

```python
monkeypatch.setenv("STUB_FAILURE_RATE", "1.0")
model_client.reset_client()
```

Always pass `sleep=False` or `STUB_SLEEP=0` when simulating latency, or the suite
actually waits.

## Naming tests for the assignment

Map each test to the acceptance criterion it covers, **by number**:

```python
def test_ac3_empty_filter_returns_no_summary(client): ...
def test_ac7_model_timeout_returns_504(client): ...
```

A red test then points at a line in the specification, not just at a broken function.
A criterion with no test is a criterion nobody is going to check.

## What a good test asserts

The observable behaviour named in the criterion — status code, response shape, the
field that changed. Not the private call path.
