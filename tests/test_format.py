from datetime import datetime
from watcher.models import Flight, RoundTrip
from watcher.format import format_trip, format_digest, DAY_ABBR


def _trip(
    out_dt: datetime,
    in_dt: datetime,
    out_taxes: float = 11.0,
    in_taxes: float = 13.0,
) -> RoundTrip:
    out = Flight("SFO", "LAX", out_dt, out_dt, 0.01, out_taxes)
    back = Flight("LAX", "SFO", in_dt, in_dt, 0.01, in_taxes)
    return RoundTrip(outbound=out, inbound=back)


def test_format_trip_basic():
    trip = _trip(
        datetime(2026, 5, 14, 18, 30),
        datetime(2026, 5, 17, 15, 0),
    )
    result = format_trip(trip)
    assert result == "SFO>LAX Thu5/14 6:30p>Sun5/17 3:00p $24"


def test_format_trip_morning_flight():
    trip = _trip(
        datetime(2026, 5, 15, 7, 5),
        datetime(2026, 5, 18, 8, 0),
        out_taxes=9.50,
        in_taxes=9.50,
    )
    result = format_trip(trip)
    assert result == "SFO>LAX Fri5/15 7:05a>Mon5/18 8:00a $19"


def test_format_trip_total_rounds_to_int():
    trip = _trip(
        datetime(2026, 5, 14, 18, 0),
        datetime(2026, 5, 17, 16, 0),
        out_taxes=11.23,
        in_taxes=12.77,
    )
    result = format_trip(trip)
    assert "$24" in result


def test_format_digest_multiple_trips():
    t1 = _trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0))
    t2 = _trip(datetime(2026, 5, 15, 7, 0), datetime(2026, 5, 18, 10, 0))
    t2.outbound.origin = "OAK"
    t2.outbound.destination = "SEA"
    t2.inbound.origin = "SEA"
    t2.inbound.destination = "OAK"
    result = format_digest([t1, t2])
    lines = result.strip().split("\n")
    assert len(lines) == 2
    assert "SFO>LAX" in lines[0]
    assert "OAK>SEA" in lines[1]


def test_format_digest_empty():
    assert format_digest([]) == "No GoWild flights found."


def test_format_trip_fits_sms():
    trip = _trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0))
    assert len(format_trip(trip)) <= 160
