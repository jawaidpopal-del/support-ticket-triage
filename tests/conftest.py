"""Shared test fixtures.

``client`` gives you a FastAPI test client backed by a throwaway database, so tests
never depend on each other's writes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import db as db_module
from app import model_client as mc
from app.main import app

try:  # the summary feature may not exist yet (see specs/filtered-summary.md §7)
    from app.routes import summary as summary_route
except ImportError:  # pragma: no cover
    summary_route = None


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.reset(tmp_path / "test.db")
    mc.reset_client()
    _clear_summary_cache()
    with TestClient(app) as c:
        yield c
    db_module.reset(tmp_path / "test.db")
    mc.reset_client()
    _clear_summary_cache()


def _clear_summary_cache() -> None:
    """Any process-local cache the summary feature keeps must be emptied between tests."""
    if summary_route is not None:
        getattr(summary_route, "clear_cache", lambda: None)()


@pytest.fixture()
def stub():
    """A well-behaved stub client. Override fields to make it misbehave."""
    return mc.StubModelClient()
