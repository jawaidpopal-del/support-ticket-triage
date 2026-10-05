"""The stub model client: determinism, and each way it can misbehave.

These tests are also the documentation for how to make the stub fail in your own
tests. Copy the patterns.
"""

from __future__ import annotations

import pytest

from app import fixtures
from app.model_client import (
    ModelTimeout,
    ModelUnavailable,
    StubConfig,
    StubModelClient,
)


def test_same_input_gives_same_output():
    a = StubModelClient().complete("describe_record", {"name": "Eastport Public Library"})
    b = StubModelClient().complete("describe_record", {"name": "Eastport Public Library"})
    assert a.value == b.value
    assert a.confidence == b.confidence


def test_result_order_does_not_change_answers():
    """Randomness is derived from the input, not from a call counter."""
    c = StubModelClient()
    first = c.complete("describe_record", {"name": "A"}).value
    c.complete("describe_record", {"name": "B"})
    c.complete("describe_record", {"name": "C"})
    assert c.complete("describe_record", {"name": "A"}).value == first


def test_every_result_carries_a_confidence_and_version():
    r = StubModelClient().complete("classify_ticket", fixtures.tickets()[0])
    assert 0.0 <= r.confidence <= 1.0
    assert r.model_version == "v1"


def test_two_versions_disagree():
    payload = {"name": "Eastport Public Library", "city": "Eastport",
               "kind": "central", "annual_visits": 48000}
    v1 = StubModelClient(model_version="v1").complete("describe_record", payload)
    v2 = StubModelClient(model_version="v2").complete("describe_record", payload)
    assert v1.value != v2.value


def test_it_can_be_told_to_fail():
    client = StubModelClient(failure_rate=1.0)
    with pytest.raises(ModelUnavailable):
        client.complete("describe_record", {"name": "anything"})


def test_it_can_be_told_to_time_out():
    client = StubModelClient(latency_ms=500, timeout_ms=100, sleep=False)
    with pytest.raises(ModelTimeout):
        client.complete("describe_record", {"name": "anything"})


def test_it_can_be_told_to_be_slow_without_failing():
    client = StubModelClient(latency_ms=250, sleep=False)
    result = client.complete("describe_record", {"name": "anything"})
    assert result.latency_ms == 250


def test_it_can_be_told_to_be_wrong():
    """The wrong answer is plausible and its confidence is low. Both matter."""
    good = StubModelClient().complete("describe_record", {"name": "Eastport Public Library"})
    bad = StubModelClient(wrongness=1.0).complete("describe_record", {"name": "Eastport Public Library"})
    assert bad.value != good.value
    assert bad.confidence < 0.5
    assert bad.degraded is True


def test_unknown_task_is_rejected_loudly():
    with pytest.raises(ValueError):
        StubModelClient().complete("do_something_undefined", {})


def test_config_reads_the_environment(monkeypatch):
    monkeypatch.setenv("STUB_FAILURE_RATE", "0.5")
    monkeypatch.setenv("STUB_MODEL_VERSION", "v2")
    cfg = StubConfig.from_env()
    assert cfg.failure_rate == 0.5
    assert cfg.model_version == "v2"
