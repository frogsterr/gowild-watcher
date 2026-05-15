from datetime import datetime, date
from watcher.models import Flight, RoundTrip
from watcher.format import format_trip, format_digest, format_email_subject, format_email_html, DAY_ABBR


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


def test_format_email_subject_with_new_trips():
    t = _trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0))
    subject = format_email_subject([t], "Morning Run")
    assert "1 new flight" in subject
    assert "Morning Run" in subject


def test_format_email_subject_plural():
    trips = [_trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0))] * 3
    subject = format_email_subject(trips, "Evening Run")
    assert "3 new flights" in subject


def test_format_email_subject_no_new_trips():
    subject = format_email_subject([], "Evening Run")
    assert "No new flights" in subject
    assert "Evening Run" in subject


def test_format_email_html_contains_route_and_price():
    t = _trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0))
    html = format_email_html([t], [t], "Morning Run", date(2026, 5, 14))
    assert "SFO" in html
    assert "LAX" in html
    assert "$24" in html


def test_format_email_html_structure():
    t = _trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0))
    html = format_email_html([t], [t], "Morning Run", date(2026, 5, 14))
    assert "GoWild Watcher" in html
    assert "Morning Run" in html
    assert "Top" in html
    assert "All Flights by Destination" in html


def test_format_email_html_no_new_trips():
    t = _trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0))
    html = format_email_html([], [t], "Evening Run", date(2026, 5, 14))
    assert "0" in html  # 0 new in stats bar
    assert "SFO" in html  # shows in destination table


def test_format_email_html_new_badge():
    t = _trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0))
    html = format_email_html([t], [t], "Morning Run", date(2026, 5, 14))
    assert "NEW" in html  # new badge appears


def test_format_email_html_sorted_by_price():
    cheap = _trip(datetime(2026, 5, 14, 18, 30), datetime(2026, 5, 17, 15, 0), out_taxes=5.0, in_taxes=5.0)
    expensive = _trip(datetime(2026, 5, 15, 8, 0), datetime(2026, 5, 18, 9, 0), out_taxes=20.0, in_taxes=20.0)
    html = format_email_html([cheap, expensive], [cheap, expensive], "Morning Run", date(2026, 5, 14))
    assert html.index("$10") < html.index("$40")
