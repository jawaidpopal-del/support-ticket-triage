"""The filter layer, in isolation."""

from __future__ import annotations

from app import filters


def test_no_filters_matches_everything():
    where, args = filters.build_where({})
    assert where == "1=1"
    assert args == []


def test_none_values_are_dropped():
    where, args = filters.build_where({"state": "MA", "city": None, "kind": None})
    assert where == "state = ?"
    assert args == ["MA"]


def test_q_is_wrapped_for_like():
    _, args = filters.build_where({"q": "ashfield"})
    assert args == ["%ashfield%"]


def test_unknown_keys_are_ignored():
    where, args = filters.build_where({"not_a_filter": "x", "state": "OR"})
    assert where == "state = ?"
    assert args == ["OR"]


def test_describe_reads_as_english():
    text = filters.describe({"state": "MA", "kind": "branch", "min_visits": 10_000})
    assert "state MA" in text
    assert " and " in text


def test_describe_with_nothing_set():
    assert filters.describe({}) == "all facilities"


def test_active_is_a_stable_cache_key():
    a = filters.active({"state": "MA", "kind": None, "q": "x"})
    b = filters.active({"q": "x", "state": "MA"})
    assert a == b


def test_active_normalises_case_where_sql_does():
    """city=Boston and city=boston are one selection, so they must be one cache key."""
    assert filters.active({"city": "Boston"}) == filters.active({"city": "boston"})
    assert filters.active({"q": "Ash"}) == filters.active({"q": "ash"})
    assert filters.active({"state": "MA"}) == filters.active({"state": "MA"})
