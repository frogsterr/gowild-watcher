"""Tests for watcher/search.py — uses a real-shape MOCK_RESPONSE."""
from __future__ import annotations

import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
import requests

from watcher.search import _extract_flight_data, _parse_flights, search_one_way

# ---------------------------------------------------------------------------
# A minimal but real-shape FlightData payload extracted from
# https://booking.flyfrontier.com/Flight/InternalSelect.
# The outer page embeds:  FlightData = '<json>';
# We represent just the parsed dict here for _parse_flights tests,
# and wrap it in the page template for the search_one_way mock.
# ---------------------------------------------------------------------------
_FLIGHT_OBJ_GOWILD = {
    "discountDenFare": 308.98,
    "standardFare": 328.98,
    "milesFare": 0.0,
    "goWildFare": 15.41,
    "isGoWildFareEnabled": True,
    "isMonetary": True,
    "hasSixPlusLayover": False,
    "isNextDayArrival": False,
    "stopCount": 0,
    "stops": None,
    "stopsText": "Nonstop",
    "duration": "2 hrs 51 min",
    "legs": [
        {
            "departureStation": "SFO",
            "arrivalStation": "DEN",
            "departureDate": "2026-05-13T12:52:00",
            "arrivalDate": "2026-05-13T16:43:00",
            "departureDateUtc": "2026-05-13T19:52:00Z",
            "arrivalDateUtc": "2026-05-13T22:43:00Z",
            "isNextDayArrival": False,
            "duration": "02:51:00",
            "durationFormatted": "2 hrs 51 min",
            "flightNumber": 1094,
            "carrierCode": "F9",
            "carrierText": "",
            "departureDateFormatted": "12:52 PM",
            "arrivalDateFormatted": "4:43 PM",
            "flightTime": "2hrs 51min",
        }
    ],
    "goWildFareKey": "0~GW~X~F9~GW01PRNW~WILD~~0~1~~X|F9~1094~ ~~SFO~05/13/2026 12:52~DEN~05/13/2026 16:43~~",
    "goWildFareSeatsRemaining": "3 Seats Left!",
    "standardFareKey": "0~N~~F9~N00VXDN~CLUB~~0~13~~X|F9~1094~~",
}

_FLIGHT_OBJ_CONNECTION = {
    "discountDenFare": 200.00,
    "standardFare": 220.00,
    "milesFare": 0.0,
    "goWildFare": 18.50,
    "isGoWildFareEnabled": True,
    "isMonetary": True,
    "hasSixPlusLayover": False,
    "isNextDayArrival": False,
    "stopCount": 1,
    "stops": "DEN",
    "stopsText": "1 Stop",
    "duration": "5 hrs 10 min",
    "legs": [
        {
            "departureStation": "SFO",
            "arrivalStation": "DEN",
            "departureDate": "2026-05-13T09:00:00",
            "arrivalDate": "2026-05-13T12:51:00",
            "isNextDayArrival": False,
            "duration": "02:51:00",
            "flightNumber": 1094,
            "carrierCode": "F9",
        },
        {
            "departureStation": "DEN",
            "arrivalStation": "SEA",
            "departureDate": "2026-05-13T13:40:00",
            "arrivalDate": "2026-05-13T15:10:00",
            "isNextDayArrival": False,
            "duration": "01:30:00",
            "flightNumber": 2201,
            "carrierCode": "F9",
        },
    ],
    "goWildFareKey": "0~GW~X~F9~GW01PRNW~WILD~~0~1~~X|F9~1094~ ~~SFO~05/13/2026 09:00~SEA~05/13/2026 15:10~~",
    "goWildFareSeatsRemaining": "5 Seats Left!",
}

_FLIGHT_OBJ_NO_GOWILD = {
    "discountDenFare": 141.98,
    "standardFare": 161.98,
    "milesFare": 0.0,
    "goWildFare": -1.0,
    "isGoWildFareEnabled": False,
    "isMonetary": True,
    "hasSixPlusLayover": False,
    "isNextDayArrival": False,
    "stopCount": 0,
    "stops": None,
    "stopsText": "Nonstop",
    "duration": "1 hrs 46 min",
    "legs": [
        {
            "departureStation": "SFO",
            "arrivalStation": "LAX",
            "departureDate": "2026-05-15T19:26:00",
            "arrivalDate": "2026-05-15T21:12:00",
            "isNextDayArrival": False,
            "duration": "01:46:00",
            "durationFormatted": "1 hrs 46 min",
            "flightNumber": 2858,
            "carrierCode": "F9",
            "carrierText": "",
            "departureDateFormatted": "7:26 PM",
            "arrivalDateFormatted": "9:12 PM",
            "flightTime": "1hrs 46min",
        }
    ],
    "goWildFareKey": "",
    "goWildFareSeatsRemaining": None,
}

MOCK_DATA = {
    "calendarLink": "o1=SFO&d1=DEN&c=true&mon=true&adt=1",
    "journeys": [
        {
            "isReturnTrip": False,
            "ribbon": None,
            "flights": [_FLIGHT_OBJ_GOWILD, _FLIGHT_OBJ_NO_GOWILD],
        }
    ],
}

# Page HTML template that wraps the JSON as the real site does.
MOCK_HTML = f"<html><body><script>FlightData = '{json.dumps(MOCK_DATA)}';</script></body></html>"


# ---------------------------------------------------------------------------
# _extract_flight_data tests
# ---------------------------------------------------------------------------


def test_extract_flight_data_missing_pattern():
    """_extract_flight_data returns None when the page has no FlightData JS assignment."""
    # Simulate a 403 redirect page or any page without the expected JS variable.
    html_no_data = "<html><body><h1>Access Denied</h1></body></html>"
    assert _extract_flight_data(html_no_data) is None


# ---------------------------------------------------------------------------
# _parse_flights tests
# ---------------------------------------------------------------------------


def test_parse_flights_extracts_flight():
    """GoWild flight is parsed with correct field values."""
    flights = _parse_flights("SFO", "DEN", MOCK_DATA)
    assert len(flights) == 1
    f = flights[0]
    assert f.origin == "SFO"
    assert f.destination == "DEN"
    assert f.base_fare == pytest.approx(0.01)
    assert f.taxes_fees == pytest.approx(15.40)
    assert f.depart_dt.hour == 12
    assert f.depart_dt.minute == 52


def test_parse_flights_empty():
    """Empty flights list returns empty result."""
    data = {"journeys": [{"flights": []}]}
    assert _parse_flights("SFO", "DEN", data) == []


def test_parse_flights_excludes_connections():
    """Flights with more than one leg (connections) are excluded — direct only."""
    data = {"journeys": [{"flights": [_FLIGHT_OBJ_CONNECTION]}]}
    assert _parse_flights("SFO", "SEA", data) == []


def test_parse_flights_mix_of_direct_and_connection():
    """Only the direct flight is returned when both direct and connecting itineraries are present."""
    data = {"journeys": [{"flights": [_FLIGHT_OBJ_GOWILD, _FLIGHT_OBJ_CONNECTION]}]}
    flights = _parse_flights("SFO", "DEN", data)
    assert len(flights) == 1
    assert flights[0].destination == "DEN"


def test_parse_flights_missing_fare():
    """Flight with missing or no GoWild fare is excluded."""
    # goWildFare absent entirely
    flight_no_fare = {
        "isGoWildFareEnabled": True,
        "goWildFare": None,
        "legs": [
            {
                "departureStation": "SFO",
                "arrivalStation": "DEN",
                "departureDate": "2026-05-13T12:52:00",
                "arrivalDate": "2026-05-13T16:43:00",
            }
        ],
    }
    data = {"journeys": [{"flights": [flight_no_fare]}]}
    assert _parse_flights("SFO", "DEN", data) == []

    # goWildFare = -1 (not enabled)
    flight_neg = dict(flight_no_fare)
    flight_neg["goWildFare"] = -1.0
    data2 = {"journeys": [{"flights": [flight_neg]}]}
    assert _parse_flights("SFO", "DEN", data2) == []


# ---------------------------------------------------------------------------
# search_one_way tests
# ---------------------------------------------------------------------------


def test_search_one_way_calls_api():
    """search_one_way calls requests.get with the correct origin/destination and returns flights."""
    mock_resp = MagicMock()
    mock_resp.text = MOCK_HTML
    mock_resp.raise_for_status = MagicMock()

    with patch("watcher.search.requests.get", return_value=mock_resp) as mock_get, \
         patch("watcher.search.time.sleep"):
        begin = date(2026, 5, 13)
        end = date(2026, 5, 13)
        flights = search_one_way("SFO", "DEN", begin, end)

    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
    # Verify origin and destination were passed correctly
    assert params["o1"] == "SFO"
    assert params["d1"] == "DEN"
    # Should return the one GoWild flight from the mock
    assert len(flights) == 1
    assert flights[0].origin == "SFO"
    assert flights[0].destination == "DEN"


def test_search_one_way_multi_day_range():
    """search_one_way calls requests.get once per day and concatenates results across days."""
    mock_resp = MagicMock()
    mock_resp.text = MOCK_HTML
    mock_resp.raise_for_status = MagicMock()

    begin = date(2026, 5, 13)
    end = date(2026, 5, 15)  # 3-day range: 13, 14, 15

    with patch("watcher.search.requests.get", return_value=mock_resp) as mock_get, \
         patch("watcher.search.time.sleep"):
        flights = search_one_way("SFO", "DEN", begin, end)

    # One GET per day in the range
    assert mock_get.call_count == 3

    # Each day's response contains 1 GoWild flight → 3 total
    assert len(flights) == 3
    assert all(f.origin == "SFO" and f.destination == "DEN" for f in flights)


def test_search_one_way_retries_on_406_then_succeeds():
    """A transient 406 (bot-protection throttling) is retried and recovers."""
    blocked_resp = MagicMock()
    blocked_resp.status_code = 406
    blocked_resp.raise_for_status.side_effect = requests.HTTPError(response=blocked_resp)

    ok_resp = MagicMock()
    ok_resp.text = MOCK_HTML
    ok_resp.raise_for_status = MagicMock()

    with patch("watcher.search.requests.get", side_effect=[blocked_resp, ok_resp]) as mock_get, \
         patch("watcher.search.time.sleep") as mock_sleep:
        flights = search_one_way("SFO", "DEN", date(2026, 5, 13), date(2026, 5, 13))

    assert mock_get.call_count == 2
    assert mock_sleep.called  # backed off before retrying
    assert len(flights) == 1


def test_search_one_way_gives_up_after_max_attempts():
    """Persistent 406s exhaust retries and raise instead of hanging forever."""
    blocked_resp = MagicMock()
    blocked_resp.status_code = 406
    blocked_resp.raise_for_status.side_effect = requests.HTTPError(response=blocked_resp)

    with patch("watcher.search.requests.get", return_value=blocked_resp) as mock_get, \
         patch("watcher.search.time.sleep"):
        with pytest.raises(requests.HTTPError):
            search_one_way("SFO", "DEN", date(2026, 5, 13), date(2026, 5, 13))

    assert mock_get.call_count == 3  # _MAX_ATTEMPTS


def test_search_one_way_does_not_retry_non_transient_error():
    """A non-bot-protection error (e.g. 404) fails fast without retrying."""
    not_found_resp = MagicMock()
    not_found_resp.status_code = 404
    not_found_resp.raise_for_status.side_effect = requests.HTTPError(response=not_found_resp)

    with patch("watcher.search.requests.get", return_value=not_found_resp) as mock_get, \
         patch("watcher.search.time.sleep"):
        with pytest.raises(requests.HTTPError):
            search_one_way("SFO", "DEN", date(2026, 5, 13), date(2026, 5, 13))

    assert mock_get.call_count == 1
