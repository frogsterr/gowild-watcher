"""Frontier Airlines flight availability search via the booking site's embedded JSON."""
from __future__ import annotations

import html
import json
import re
from datetime import date, datetime, timedelta
from typing import Any

import requests

from .models import Flight

_BOOKING_URL = "https://booking.flyfrontier.com/Flight/InternalSelect"
_GOWILD_BASE_FARE = 0.01
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def search_one_way(
    origin: str,
    destination: str,
    begin: date,
    end: date,
) -> list[Flight]:
    """Return GoWild flights from *origin* to *destination* departing between *begin* and *end* (inclusive)."""
    flights: list[Flight] = []
    current = begin
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        params = {
            "o1": origin,
            "d1": destination,
            "dd1": date_str,
            "ADT": "1",
            "mon": "true",
            "promo": "",
        }
        resp = requests.get(
            _BOOKING_URL, params=params, headers=_HEADERS, timeout=30
        )
        resp.raise_for_status()
        data = _extract_flight_data(resp.text)
        if data is not None:
            flights.extend(_parse_flights(origin, destination, data))
        # advance one day
        current += timedelta(days=1)
    return flights


def _extract_flight_data(html_body: str) -> dict[str, Any] | None:
    """Extract the FlightData JSON object embedded in the Frontier booking page."""
    # The page embeds: FlightData = '{ ... }';
    # NOTE: This regex uses a non-greedy single-quoted match. It will break if
    # any JSON string value contains a literal single quote character, because
    # the regex will terminate early at the first unescaped "'". This is a
    # known limitation; the site currently does not produce such values.
    m = re.search(r"FlightData\s*=\s*'(.*?)';", html_body, re.DOTALL)
    if not m:
        return None
    raw = m.group(1)
    # The block may also appear HTML-entity-encoded in a different context;
    # prefer the JS assignment (already unescaped), but unescape just in case.
    raw = html.unescape(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _parse_flights(
    origin: str,
    destination: str,
    data: dict[str, Any],
) -> list[Flight]:
    """Parse a FlightData dict and return GoWild *Flight* objects.

    Only flights where ``isGoWildFareEnabled`` is True and ``goWildFare`` > 0
    are included.  The API returns ``goWildFare`` as the total price charged
    (base $0.01 + government/airport taxes & fees), so::

        base_fare  = 0.01
        taxes_fees = goWildFare - 0.01
    """
    flights: list[Flight] = []
    journeys = data.get("journeys") or []
    for journey in journeys:
        for flight in journey.get("flights") or []:
            if not flight.get("isGoWildFareEnabled"):
                continue
            gw_total = flight.get("goWildFare")
            if gw_total is None or gw_total <= 0:
                continue

            legs = flight.get("legs") or []
            if not legs:
                continue

            first_leg = legs[0]
            last_leg = legs[-1]

            dep_str = first_leg.get("departureDate")
            arr_str = last_leg.get("arrivalDate")
            if not dep_str or not arr_str:
                continue

            try:
                depart_dt = datetime.fromisoformat(dep_str)
                arrive_dt = datetime.fromisoformat(arr_str)
            except ValueError:
                continue

            taxes_fees = round(gw_total - _GOWILD_BASE_FARE, 2)
            flights.append(
                Flight(
                    origin=origin,
                    destination=destination,
                    depart_dt=depart_dt,
                    arrive_dt=arrive_dt,
                    base_fare=_GOWILD_BASE_FARE,
                    taxes_fees=taxes_fees,
                )
            )
    return flights
