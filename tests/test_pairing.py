import pytest
from datetime import datetime
from watcher.models import Flight, RoundTrip
from watcher.pairing import pair_round_trips


def _f(origin, dest, depart: datetime, base=0.01, taxes=12.0) -> Flight:
    return Flight(origin, dest, depart, depart, base, taxes)


def test_thursday_outbound_pairs_with_sunday():
    out = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))   # Thu
    back = _f("LAX", "SFO", datetime(2026, 5, 17, 15, 0))  # Sun
    trips = pair_round_trips([out], [back])
    assert len(trips) == 1
    assert trips[0].outbound is out
    assert trips[0].inbound is back


def test_thursday_outbound_pairs_with_monday():
    out = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))   # Thu
    back = _f("LAX", "SFO", datetime(2026, 5, 18, 16, 0))  # Mon
    trips = pair_round_trips([out], [back])
    assert len(trips) == 1


def test_friday_outbound_pairs_with_sunday():
    out = _f("SFO", "LAX", datetime(2026, 5, 15, 7, 0))    # Fri
    back = _f("LAX", "SFO", datetime(2026, 5, 17, 15, 0))  # Sun
    trips = pair_round_trips([out], [back])
    assert len(trips) == 1


def test_friday_outbound_pairs_with_monday():
    out = _f("SFO", "LAX", datetime(2026, 5, 15, 7, 0))    # Fri
    back = _f("LAX", "SFO", datetime(2026, 5, 18, 16, 0))  # Mon
    trips = pair_round_trips([out], [back])
    assert len(trips) == 1


def test_thursday_does_not_pair_with_saturday():
    out = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))   # Thu
    back = _f("LAX", "SFO", datetime(2026, 5, 16, 15, 0))  # Sat
    trips = pair_round_trips([out], [back])
    assert len(trips) == 0


def test_thursday_does_not_pair_with_next_weekend_sunday():
    out = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))
    back = _f("LAX", "SFO", datetime(2026, 5, 24, 12, 0))  # Next Sun
    trips = pair_round_trips([out], [back])
    assert len(trips) == 0


def test_multiple_outbounds_multiple_inbounds():
    out1 = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))  # Thu May 14
    out2 = _f("SFO", "LAX", datetime(2026, 5, 15, 7, 0))   # Fri May 15
    back1 = _f("LAX", "SFO", datetime(2026, 5, 17, 12, 0)) # Sun May 17
    back2 = _f("LAX", "SFO", datetime(2026, 5, 18, 14, 0)) # Mon May 18
    trips = pair_round_trips([out1, out2], [back1, back2])
    # Thu14->Sun17, Thu14->Mon18, Fri15->Sun17, Fri15->Mon18
    assert len(trips) == 4


def test_round_trip_key_format():
    out = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))
    back = _f("LAX", "SFO", datetime(2026, 5, 17, 15, 0))
    trip = pair_round_trips([out], [back])[0]
    assert trip.key == "SFO-LAX-2026-05-14-2026-05-17"


def test_total_fees_sums_both_legs():
    out = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0), taxes=11.0)
    back = _f("LAX", "SFO", datetime(2026, 5, 17, 15, 0), taxes=13.0)
    trip = pair_round_trips([out], [back])[0]
    assert trip.total_fees == pytest.approx(24.0, abs=0.01)
