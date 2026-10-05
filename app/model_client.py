"""A stub model client.

No network. No API key. No account. It returns canned, *structured* results with a
confidence score, and it can be told to misbehave in the four ways that matter:

    slow        STUB_LATENCY_MS=800
    failing     STUB_FAILURE_RATE=0.3
    timing out  STUB_TIMEOUT_MS=200      (raises when latency exceeds this)
    wrong       STUB_WRONGNESS=1.0       (plausible answer, low confidence, not correct)

Two model versions are addressable (``v1``, ``v2``) and disagree on purpose, so a
specification can say what happens when the version changes underneath you.

Determinism: identical (task, payload, version, seed) always produces an identical
result, whatever order calls arrive in. Randomness is derived from the input, never
from a running counter.

    >>> client = StubModelClient()
    >>> r = client.complete("describe_record", {"name": "Ashfield Public Library"})
    >>> r.confidence > 0.5
    True
"""

from __future__ import annotations

import re
import hashlib
import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

__all__ = [
    "ModelResult",
    "ModelError",
    "ModelUnavailable",
    "ModelTimeout",
    "StubConfig",
    "StubModelClient",
    "get_client",
]

MODEL_VERSIONS = ("v1", "v2")


# --------------------------------------------------------------------------- errors


class ModelError(Exception):
    """Base class for every failure this client raises."""


class ModelUnavailable(ModelError):
    """The model call failed. Retrying may work."""


class ModelTimeout(ModelError):
    """The model call took longer than the configured timeout."""


# --------------------------------------------------------------------------- result


@dataclass(frozen=True)
class ModelResult:
    """What every call returns.

    ``confidence`` is in [0, 1]. ``degraded`` is True when the stub deliberately
    returned a poor answer — your code cannot see this in production, so treat it as
    a test hook, not a signal to branch on.
    """

    value: Any
    confidence: float
    model_version: str
    latency_ms: int
    degraded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "model_version": self.model_version,
            "latency_ms": self.latency_ms,
        }


# --------------------------------------------------------------------------- config


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int | None) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class StubConfig:
    """How the stub should misbehave. Defaults are the well-behaved case."""

    seed: int = 0
    latency_ms: int = 0
    failure_rate: float = 0.0
    timeout_ms: int | None = None
    wrongness: float = 0.0
    model_version: str = "v1"
    sleep: bool = True  # tests turn this off so latency is simulated, not waited out

    @classmethod
    def from_env(cls) -> "StubConfig":
        version = os.getenv("STUB_MODEL_VERSION", "v1")
        if version not in MODEL_VERSIONS:
            version = "v1"
        return cls(
            seed=_env_int("STUB_SEED", 0) or 0,
            latency_ms=_env_int("STUB_LATENCY_MS", 0) or 0,
            failure_rate=_env_float("STUB_FAILURE_RATE", 0.0),
            timeout_ms=_env_int("STUB_TIMEOUT_MS", None),
            wrongness=_env_float("STUB_WRONGNESS", 0.0),
            model_version=version,
            sleep=os.getenv("STUB_SLEEP", "1") != "0",
        )


# --------------------------------------------------------------------------- client


class StubModelClient:
    """The fake model. Construct one directly in tests; use :func:`get_client` in app code."""

    def __init__(self, config: StubConfig | None = None, **overrides: Any) -> None:
        self.config = config or StubConfig()
        for key, value in overrides.items():
            if not hasattr(self.config, key):
                raise TypeError(f"unknown StubConfig field: {key!r}")
            setattr(self.config, key, value)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    # -- public API ---------------------------------------------------------

    def complete(self, task: str, payload: dict[str, Any] | None = None) -> ModelResult:
        """Run ``task`` over ``payload``.

        Raises :class:`ModelUnavailable` or :class:`ModelTimeout` when configured to.
        """
        payload = payload or {}
        if task not in TASKS:
            raise ValueError(f"unknown task {task!r}. Known tasks: {sorted(TASKS)}")
        self.calls.append((task, payload))

        rng = self._rng(task, payload)
        cfg = self.config

        if cfg.failure_rate and rng.random() < cfg.failure_rate:
            raise ModelUnavailable(f"stub model refused the call for task {task!r}")

        latency = cfg.latency_ms
        if cfg.timeout_ms is not None and latency > cfg.timeout_ms:
            raise ModelTimeout(f"stub model exceeded {cfg.timeout_ms}ms on task {task!r}")
        if latency and cfg.sleep:
            time.sleep(latency / 1000.0)

        degraded = bool(cfg.wrongness) and rng.random() < cfg.wrongness
        value, confidence = TASKS[task](payload, rng, cfg.model_version, degraded)
        if degraded:
            confidence = min(confidence, 0.41)

        return ModelResult(
            value=value,
            confidence=confidence,
            model_version=cfg.model_version,
            latency_ms=latency,
            degraded=degraded,
        )

    # -- internals ----------------------------------------------------------

    def _rng(self, task: str, payload: dict[str, Any]) -> random.Random:
        """Randomness derived from the input, so results never depend on call order."""
        blob = json.dumps(
            {"task": task, "payload": payload, "v": self.config.model_version, "s": self.config.seed},
            sort_keys=True,
            default=str,
        )
        digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        return random.Random(int(digest[:16], 16))


_default_client: StubModelClient | None = None


def get_client() -> StubModelClient:
    """The client the API uses. Reads configuration from the environment once."""
    global _default_client
    if _default_client is None:
        _default_client = StubModelClient(StubConfig.from_env())
    return _default_client


def reset_client() -> None:
    """Drop the cached client. Tests call this after changing the environment."""
    global _default_client
    _default_client = None


# --------------------------------------------------------------------------- tasks
#
# Every handler has the same shape:
#
#     (payload, rng, version, degraded) -> (value, confidence)
#
# ``degraded`` means "return something plausible but wrong". That path is the one
# your specification has to have an answer for; if the stub were always right the
# exercise would be empty.


KIND_NOUNS = {
    "central": "central library",
    "branch": "branch library",
    "bookmobile": "bookmobile service",
    "research": "research library",
}


def _describe_record(payload, rng, version, degraded):
    name = payload.get("name", "this record")
    city = payload.get("city", "")
    kind = KIND_NOUNS.get(payload.get("kind", ""), "library")
    visits = payload.get("annual_visits")
    where = f" in {city}" if city else ""
    if degraded:
        # Plausible sentence, wrong facts: an invented branch count and the wrong kind.
        return (f"{name} is a mobile library service{where} operating six branches.", 0.38)
    if version == "v2":
        text = f"{name}{where} is a {kind}."
        if visits:
            text += f" It recorded {visits:,} visits last year."
        return (text, 0.91)
    text = f"{name} is a {kind}{where}."
    return (text, 0.86)


def _summarize_records(payload, rng, version, degraded):
    """The task the live demo builds a feature around.

    Note the length: this returns 65-70 words on purpose — over the cap. Any word cap in your
    specification has to be enforced by *your* code, not hoped for from the model.
    """
    count = int(payload.get("count", 0))
    states = payload.get("states") or []
    kinds = payload.get("kinds") or []
    median = payload.get("median_visits")

    if count == 0:
        # Even on an empty set the stub answers. Whether you should have called it
        # at all is a decision for the specification.
        return ("There is nothing here to summarise, though the filter is valid and "
                "could be widened to include neighbouring regions or other facility "
                "types if a broader view would be useful to the reader right now.", 0.30)

    if degraded:
        wrong = count + rng.randint(7, 40)
        return (f"This view covers {wrong} facilities, almost all of them mobile services "
                f"concentrated in a single county, with visit numbers that have fallen "
                f"sharply year on year across every category shown in the current "
                f"selection and in the two categories immediately adjacent to it.", 0.36)

    lead_state = states[0] if states else "several states"
    lead_kind = KIND_NOUNS.get(kinds[0] if kinds else "", "library")
    spread = f"{len(states)} states" if len(states) > 1 else lead_state
    median_txt = f"{median:,}" if isinstance(median, int) else "an unreported number of"

    text = (
        f"This selection holds {count} facilities spread across {spread}, weighted "
        f"towards {lead_state} and dominated by the {lead_kind} category. Median annual "
        f"attendance sits at roughly {median_txt} visits, though the distribution is "
        f"wide and a small number of large central sites account for a disproportionate "
        f"share of the total. Smaller branches cluster tightly around the median and "
        f"vary little between the regions represented in the current filter."
    )
    if version == "v2":
        text = text.replace("This selection holds", "You are looking at")
    return (text, 0.88)


def _plan_steps(payload, rng, version, degraded):
    """Option A. Steps reference operations from data/operations.json.

    The shape of the plan follows the verb in the goal; the search term is the place or
    thing the goal names, not the goal sentence. The awkward goals in the fixture come out
    awkward on purpose: an underspecified goal plans a step with ``"?"`` arguments at low
    confidence, a goal that says "then recompute" ends with the search it started with,
    a goal that names a field the records do not have plans an update to that field, and
    an email goal plans one irreversible send per match.
    """
    goal = payload.get("goal", "")
    available = payload.get("operations") or []
    lowered = goal.lower()

    place = re.search(r"\b(?:in|from) ([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*)", goal)
    proper = re.search(r"(?<!^)\b([A-Z][a-z]+)\b", goal)
    if place:
        q = place.group(1)
    elif proper:
        q = proper.group(1)
    else:
        q = re.sub(r"^(tag|export|find|delete|remove|purge|set|give|email|make|update) (every|all|the) ", "", lowered)
        q = q.rsplit("every ", 1)[-1]
        q = re.split(r", | to ", q)[0].rstrip(".")[:40]
    search = {"op": "records.search", "args": {"q": q}, "reversible": True}

    if degraded:
        # Plausible plan that quietly includes a destructive step with no approval.
        return ([
            dict(search),
            {"op": "records.delete", "args": {"scope": "matched"}, "reversible": False},
            {"op": "records.export", "args": {"format": "csv"}, "reversible": True},
        ], 0.39)

    fields = ("annual_visits", "year_founded", "has_makerspace", "kind", "city", "state", "name")
    named_field = next((f for f in fields if f in lowered), None)
    number = re.search(r"\$?(\d[\d,]*)", goal)
    confidence = 0.83 if version == "v1" else 0.79
    plan: list[dict[str, Any]] = [search]
    if "merge" in lowered or "duplicate" in lowered:
        plan.append({"op": "records.propose_merge", "args": {}, "reversible": True})
        plan.append({"op": "records.apply_merge", "args": {}, "reversible": False})
    elif "delete" in lowered or "remove" in lowered or "purge" in lowered:
        if version == "v2":
            plan.append({"op": "records.export", "args": {"format": "csv"}, "reversible": True})
        plan.append({"op": "records.delete", "args": {"scope": "matched"}, "reversible": False})
    elif "email" in lowered or "notify" in lowered:
        plan.append({"op": "notify.email_owner", "args": {"scope": "matched", "template": "update_request"},
                     "reversible": False})
    elif "import" in lowered or "load " in lowered:
        plan.append({"op": "records.bulk_import", "args": {"file": q}, "reversible": False})
    elif "export" in lowered or "report" in lowered:
        plan.append({"op": "records.export", "args": {"format": "csv"}, "reversible": True})
    elif "consistent" in lowered or "clean up" in lowered:
        plan.append({"op": "records.update_field", "args": {"field": "?", "value": "?"}, "reversible": True})
        confidence = 0.52
    elif any(w in lowered for w in ("set ", "give ", "change ", "update ", "budget")):
        field = named_field or re.sub(r"[^a-z_]", "_", re.sub(r".*\ba (\w+ \w+) of.*", r"\1", lowered)).strip("_")
        value = int(number.group(1).replace(",", "")) if number else ("state average" if "average" in lowered else "?")
        plan.append({"op": "records.update_field", "args": {"field": field, "value": value}, "reversible": True})
        if "then" in lowered or "again" in lowered or "until" in lowered:
            plan.append(dict(search))
    else:
        tag = re.search(r"\bas (\w+)", lowered)
        plan.append({"op": "records.tag", "args": {"tag": tag.group(1) if tag else "reviewed"}, "reversible": True})

    if available:
        known = {o["name"] if isinstance(o, dict) else o for o in available}
        plan = [s for s in plan if s["op"] in known] or plan
    return (plan, confidence)


def _classify_ticket(payload, rng, version, degraded):
    """Option B."""
    text = f"{payload.get('subject', '')} {payload.get('body', '')}".lower()
    categories = [
        ("billing", ("invoice", "charge", "refund", "payment", "billed")),
        ("access", ("login", "password", "locked", "sign in", "access", "permission", "home branch")),
        ("data", ("import", "export", "csv", "duplicate", "missing record", "due date", "loan")),
        ("outage", ("down", "500", "timeout", "unavailable", "cannot load", "offline")),
    ]
    category, hits = "general", 0
    for name, words in categories:
        n = sum(1 for w in words if w in text)
        if n > hits:
            category, hits = name, n

    urgent = any(w in text for w in ("urgent", "asap", "immediately", "down", "blocked"))
    priority = "high" if urgent else ("low" if hits == 0 else "normal")

    if degraded:
        return ({"category": "general", "priority": "low", "team": "triage",
                 "draft_reply": "Thanks for getting in touch. Could you send a screenshot?"}, 0.33)

    team = {"billing": "finance-ops", "access": "identity", "data": "data-platform",
            "outage": "platform-sre"}.get(category, "triage")
    if version == "v2" and category == "general":
        team, priority = "triage", "normal"

    reply = {
        "billing": "Thanks for writing in. I can see the charge you mean and I am checking it now.",
        "access": "Thanks for writing in. I have started a reset on your account.",
        "data": "Thanks for writing in. I am looking at the import log for the file you named.",
        "outage": "Thanks for the report. We are investigating and I will update you shortly.",
    }.get(category, "Thanks for writing in. I am taking a look and will come back to you.")

    confidence = 0.86 if hits >= 2 else (0.62 if hits == 1 else 0.44)
    return ({"category": category, "priority": priority, "team": team, "draft_reply": reply},
            confidence)


def _answer_with_sources(payload, rng, version, degraded):
    """Option C. Citations reference ids from data/documents/."""
    question = payload.get("question", "").lower()
    docs = payload.get("documents") or []
    hits = [d for d in docs if any(w in (d.get("text", "") + d.get("title", "")).lower()
                                   for w in question.split() if len(w) > 4)]

    if degraded:
        # An answer with a citation that does not exist. This is the case your
        # specification has to forbid.
        return ({"answer": "Loans are limited to fourteen days for every borrower class.",
                 "citations": [{"doc_id": "policy-99", "quote": "fourteen days"}]}, 0.35)

    if not hits:
        return ({"answer": None, "citations": [],
                 "reason": "no supporting passage found"}, 0.22)

    top = hits[: (2 if version == "v2" else 1)]
    return ({
        "answer": top[0].get("summary") or top[0].get("text", "")[:180],
        "citations": [{"doc_id": d["id"], "quote": d.get("text", "")[:90]} for d in top],
    }, 0.81 if len(hits) > 1 else 0.68)


def _review_diff(payload, rng, version, degraded):
    """Option D."""
    diff = payload.get("diff", "")
    added = [ln for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    comments: list[dict[str, Any]] = []

    if degraded:
        return ([{"file": "unknown", "line": 1, "severity": "blocker",
                  "comment": "This change removes error handling."}], 0.31)

    for i, line in enumerate(added, start=1):
        body = line[1:].strip()
        if "except:" in body or "except Exception:" in body:
            comments.append({"file": payload.get("file", "?"), "line": i, "severity": "major",
                             "comment": "Bare except swallows the error. Name the exception."})
        elif "TODO" in body or "FIXME" in body:
            comments.append({"file": payload.get("file", "?"), "line": i, "severity": "minor",
                             "comment": "TODO left in a merged change."})
        elif "password" in body.lower() or "secret" in body.lower() or "api_key" in body.lower():
            comments.append({"file": payload.get("file", "?"), "line": i, "severity": "blocker",
                             "comment": "Possible credential in source. Move it to configuration."})
        elif " == None" in body:
            comments.append({"file": payload.get("file", "?"), "line": i, "severity": "minor",
                             "comment": "Use `is None`."})

    if version == "v2":
        comments = [c for c in comments if c["severity"] != "minor"]
    confidence = 0.78 if comments else 0.55
    return (comments, confidence)


def _propose_merges(payload, rng, version, degraded):
    """Option E. Returns candidate pairs with a similarity score.

    The fixture deliberately contains an A~B, B~C, A-not-C chain. This task will
    happily propose both pairs. Deciding what to do about that is the exercise.

    Records in different states are never paired, however similar the names — except
    in the wrongness mode, which adds one confidently wrong cross-state pair.
    """
    records = payload.get("records") or []

    def norm(s: str) -> str:
        s = s.lower()
        for token in (" public ", " publ. ", " pub ", " library", " lib.", " branch", ",", "."):
            s = s.replace(token, " ")
        return " ".join(s.split())

    pairs = []
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            if a.get("state") and b.get("state") and a["state"] != b["state"]:
                continue
            na, nb = norm(a.get("name", "")), norm(b.get("name", ""))
            if not na or not nb:
                continue
            shared = len(set(na.split()) & set(nb.split()))
            total = max(len(set(na.split()) | set(nb.split())), 1)
            score = shared / total
            if a.get("city") and a.get("city") == b.get("city"):
                score += 0.15
            if score >= (0.55 if version == "v1" else 0.70):
                conflicts = [f for f in ("city", "state", "kind", "annual_visits")
                             if a.get(f) is not None and b.get(f) is not None and a[f] != b[f]]
                pairs.append({"a_id": a.get("id"), "b_id": b.get("id"),
                              "score": round(min(score, 0.99), 3),
                              "field_conflicts": conflicts})

    if degraded and records:
        pairs = pairs + [{"a_id": records[0].get("id"), "b_id": records[-1].get("id"),
                          "score": 0.71, "field_conflicts": ["city", "state"]}]
        return (pairs, 0.34)

    pairs.sort(key=lambda p: -p["score"])
    return (pairs, 0.80 if pairs else 0.50)


TASKS: dict[str, Callable[..., tuple[Any, float]]] = {
    "describe_record": _describe_record,
    "summarize_records": _summarize_records,
    "plan_steps": _plan_steps,
    "classify_ticket": _classify_ticket,
    "answer_with_sources": _answer_with_sources,
    "review_diff": _review_diff,
    "propose_merges": _propose_merges,
}
