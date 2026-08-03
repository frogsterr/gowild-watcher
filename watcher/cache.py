"""Persisted sweep progress + fetched flight results, shared between the collector and digest jobs."""
import json
import time
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable

from .config import COLLECTOR_REQUEST_DELAY_SECONDS, LOOKAHEAD_DAYS
from .models import Flight
from .workqueue import build_sweep

_DEFAULT_PATH = Path("state/sweep_state.json")


def load_sweep_state(path: Path = _DEFAULT_PATH) -> dict:
    if not path.exists():
        return {"sweep_date": None, "cursor": 0, "results": {}}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"sweep_date": None, "cursor": 0, "results": {}}


def save_sweep_state(state: dict, path: Path = _DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True))


def _flight_to_dict(f: Flight) -> dict:
    d = asdict(f)
    d["depart_dt"] = f.depart_dt.isoformat()
    d["arrive_dt"] = f.arrive_dt.isoformat()
    return d


def _flight_from_dict(d: dict) -> Flight:
    return Flight(
        origin=d["origin"],
        destination=d["destination"],
        depart_dt=datetime.fromisoformat(d["depart_dt"]),
        arrive_dt=datetime.fromisoformat(d["arrive_dt"]),
        base_fare=d["base_fare"],
        taxes_fees=d["taxes_fees"],
    )


def run_collector_batch(
    state: dict,
    today: date,
    batch_size: int,
    fetch: Callable[[str, str, date], list[Flight]],
) -> dict:
    """Fetch the next *batch_size* work items and record results. Returns the updated state.

    Starting a fresh sweep (new day, or the previous sweep just wrapped) keeps prior
    results in place — the digest should always have the most recent data available
    per route, even mid-sweep.
    """
    if state.get("sweep_date") != today.isoformat():
        state = {"sweep_date": today.isoformat(), "cursor": 0, "results": dict(state.get("results", {}))}

    items = build_sweep(today)
    cursor = state["cursor"]
    batch = items[cursor : cursor + batch_size]

    for i, item in enumerate(batch):
        if i > 0:
            time.sleep(COLLECTOR_REQUEST_DELAY_SECONDS)
        try:
            flights = fetch(item.origin, item.destination, item.day)
        except Exception:
            # Leave any previously cached value in place; this item gets
            # picked up again next sweep rather than blocking the batch.
            continue
        state["results"][item.key] = {
            "day": item.day.isoformat(),
            "flights": [_flight_to_dict(f) for f in flights],
        }

    state["cursor"] = cursor + len(batch)
    if state["cursor"] >= len(items):
        state["cursor"] = 0  # sweep complete; the next invocation starts a fresh one

    horizon_end = (today + timedelta(days=LOOKAHEAD_DAYS + 6)).isoformat()
    today_str = today.isoformat()
    state["results"] = {
        k: v for k, v in state["results"].items() if today_str <= v["day"] <= horizon_end
    }

    return state


def load_all_flights(state: dict) -> dict[tuple[str, str], list[Flight]]:
    """Group every cached flight by (origin, destination) route-pair."""
    grouped: dict[tuple[str, str], list[Flight]] = {}
    for entry in state.get("results", {}).values():
        for fd in entry["flights"]:
            f = _flight_from_dict(fd)
            grouped.setdefault((f.origin, f.destination), []).append(f)
    return grouped
