import json
import tempfile
from pathlib import Path
from datetime import date, datetime
from watcher.models import Flight, RoundTrip
from watcher.state import load_state, save_state, find_new_trips, expire_old_trips


def _make_trip(out_date: date, in_date: date, origin="SFO", dest="LAX") -> RoundTrip:
    out_dt = datetime(out_date.year, out_date.month, out_date.day, 18, 0)
    in_dt = datetime(in_date.year, in_date.month, in_date.day, 15, 0)
    out = Flight(origin, dest, out_dt, out_dt, 0.01, 12.0)
    back = Flight(dest, origin, in_dt, in_dt, 0.01, 12.0)
    return RoundTrip(outbound=out, inbound=back)


def test_load_state_returns_empty_dict_when_file_missing():
    state = load_state(Path("/tmp/nonexistent_gowild_99999.json"))
    assert state == {}


def test_save_and_load_round_trip():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    state = {"SFO-LAX-2026-05-14-2026-05-17": "2026-05-14"}
    save_state(state, path)
    loaded = load_state(path)
    assert loaded == state


def test_find_new_trips_all_new():
    trip = _make_trip(date(2026, 5, 14), date(2026, 5, 17))
    new = find_new_trips([trip], {})
    assert len(new) == 1
    assert new[0] is trip


def test_find_new_trips_already_seen():
    trip = _make_trip(date(2026, 5, 14), date(2026, 5, 17))
    state = {trip.key: "2026-05-14"}
    new = find_new_trips([trip], state)
    assert len(new) == 0


def test_find_new_trips_mixed():
    t1 = _make_trip(date(2026, 5, 14), date(2026, 5, 17))
    t2 = _make_trip(date(2026, 5, 21), date(2026, 5, 24))
    state = {t1.key: "2026-05-14"}
    new = find_new_trips([t1, t2], state)
    assert len(new) == 1
    assert new[0] is t2


def test_expire_old_trips_removes_past():
    state = {
        "SFO-LAX-2026-05-01-2026-05-04": "2026-05-01",  # past
        "SFO-LAX-2026-05-20-2026-05-23": "2026-05-20",  # future
    }
    today = date(2026, 5, 12)
    result = expire_old_trips(state, today)
    assert "SFO-LAX-2026-05-01-2026-05-04" not in result
    assert "SFO-LAX-2026-05-20-2026-05-23" in result


def test_expire_old_trips_keeps_today():
    state = {"SFO-LAX-2026-05-12-2026-05-15": "2026-05-12"}
    today = date(2026, 5, 12)
    result = expire_old_trips(state, today)
    assert "SFO-LAX-2026-05-12-2026-05-15" in result


def test_save_state_creates_parent_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "subdir" / "state.json"
        save_state({"key": "value"}, path)
        assert path.exists()
        assert json.loads(path.read_text()) == {"key": "value"}
