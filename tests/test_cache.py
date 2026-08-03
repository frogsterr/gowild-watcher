from datetime import date, datetime
from unittest.mock import patch

import pytest

from watcher.cache import load_all_flights, run_collector_batch
from watcher.models import Flight
from watcher.workqueue import build_sweep


@pytest.fixture(autouse=True)
def _no_sleep():
    with patch("watcher.cache.time.sleep"):
        yield


def _fake_fetch(log):
    def fetch(origin, destination, day):
        log.append((origin, destination, day))
        return [Flight(origin, destination, datetime.combine(day, datetime.min.time()), datetime.combine(day, datetime.min.time()), 0.01, 12.0)]
    return fetch


def test_first_batch_starts_fresh_sweep():
    today = date(2026, 8, 15)
    state = {"sweep_date": None, "cursor": 0, "results": {}}
    log = []
    state = run_collector_batch(state, today, batch_size=5, fetch=_fake_fetch(log))

    assert state["sweep_date"] == today.isoformat()
    assert state["cursor"] == 5
    assert len(log) == 5
    assert len(state["results"]) == 5


def test_batch_advances_cursor_and_accumulates_results():
    today = date(2026, 8, 15)
    state = {"sweep_date": today.isoformat(), "cursor": 0, "results": {}}
    log = []
    fetch = _fake_fetch(log)

    state = run_collector_batch(state, today, batch_size=5, fetch=fetch)
    state = run_collector_batch(state, today, batch_size=5, fetch=fetch)

    assert state["cursor"] == 10
    assert len(state["results"]) == 10
    assert len(log) == 10


def test_cursor_wraps_after_full_sweep():
    today = date(2026, 8, 15)
    total_items = len(build_sweep(today))
    state = {"sweep_date": today.isoformat(), "cursor": total_items - 3, "results": {}}
    log = []
    state = run_collector_batch(state, today, batch_size=5, fetch=_fake_fetch(log))

    assert len(log) == 3  # only 3 items remained in the sweep
    assert state["cursor"] == 0


def test_new_day_starts_fresh_sweep_but_keeps_prior_results():
    old_day = date(2026, 8, 14)
    state = {
        "sweep_date": old_day.isoformat(),
        "cursor": 40,
        "results": {"SFO-LAX-2026-08-15": {"day": "2026-08-15", "flights": []}},
    }
    today = date(2026, 8, 15)
    log = []
    state = run_collector_batch(state, today, batch_size=5, fetch=_fake_fetch(log))

    assert state["sweep_date"] == today.isoformat()
    assert state["cursor"] == 5  # restarted from 0, not 40
    assert "SFO-LAX-2026-08-15" in state["results"]  # prior result preserved


def test_stale_results_outside_horizon_are_purged():
    today = date(2026, 8, 15)
    state = {
        "sweep_date": today.isoformat(),
        "cursor": 0,
        "results": {
            "SFO-LAX-2026-08-01": {"day": "2026-08-01", "flights": []},  # in the past
            "SFO-LAX-2026-09-01": {"day": "2026-09-01", "flights": []},  # beyond horizon
            "SFO-LAX-2026-08-20": {"day": "2026-08-20", "flights": []},  # within horizon
        },
    }
    state = run_collector_batch(state, today, batch_size=1, fetch=_fake_fetch([]))

    assert "SFO-LAX-2026-08-01" not in state["results"]
    assert "SFO-LAX-2026-09-01" not in state["results"]
    assert "SFO-LAX-2026-08-20" in state["results"]


def test_failed_fetch_is_skipped_without_crashing_batch():
    today = date(2026, 8, 15)
    state = {"sweep_date": today.isoformat(), "cursor": 0, "results": {}}

    calls = []

    def flaky_fetch(origin, destination, day):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("406")
        return [Flight(origin, destination, datetime.combine(day, datetime.min.time()), datetime.combine(day, datetime.min.time()), 0.01, 12.0)]

    state = run_collector_batch(state, today, batch_size=5, fetch=flaky_fetch)

    assert state["cursor"] == 5  # batch still fully advances
    assert len(state["results"]) == 4  # one item's fetch failed and was skipped


def test_load_all_flights_groups_by_route():
    f1 = Flight("SFO", "LAX", datetime(2026, 8, 15, 18, 0), datetime(2026, 8, 15, 19, 30), 0.01, 12.0)
    f2 = Flight("SFO", "LAX", datetime(2026, 8, 16, 18, 0), datetime(2026, 8, 16, 19, 30), 0.01, 14.0)
    f3 = Flight("LAX", "SFO", datetime(2026, 8, 17, 15, 0), datetime(2026, 8, 17, 16, 30), 0.01, 13.0)

    state = {
        "results": {
            "SFO-LAX-2026-08-15": {"day": "2026-08-15", "flights": [_flight_dict(f1)]},
            "SFO-LAX-2026-08-16": {"day": "2026-08-16", "flights": [_flight_dict(f2)]},
            "LAX-SFO-2026-08-17": {"day": "2026-08-17", "flights": [_flight_dict(f3)]},
        }
    }
    grouped = load_all_flights(state)

    assert len(grouped[("SFO", "LAX")]) == 2
    assert len(grouped[("LAX", "SFO")]) == 1


def _flight_dict(f: Flight) -> dict:
    return {
        "origin": f.origin,
        "destination": f.destination,
        "depart_dt": f.depart_dt.isoformat(),
        "arrive_dt": f.arrive_dt.isoformat(),
        "base_fare": f.base_fare,
        "taxes_fees": f.taxes_fees,
    }
