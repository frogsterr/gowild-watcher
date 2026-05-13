# GoWild Flight Watcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A GitHub Actions Python script that runs twice daily, searches Frontier Airlines for GoWild round-trip flights from Bay Area airports, and texts new results + a morning digest via email-to-SMS.

**Architecture:** Single Python package (`watcher/`) with focused modules for search, filtering, pairing, formatting, state, and notifications. `main.py` orchestrates them. A JSON state file committed back to the repo tracks seen flights for deduplication. GitHub Actions runs on cron twice daily and commits state changes.

**Tech Stack:** Python 3.12, `requests`, `pytz`, smtplib (stdlib), GitHub Actions

---

## File Map

| File | Responsibility |
|------|---------------|
| `watcher/config.py` | Airport lists, destination list, constants |
| `watcher/models.py` | `Flight` and `RoundTrip` dataclasses |
| `watcher/search.py` | Frontier API calls → list of `Flight` |
| `watcher/filter.py` | Weekend window check, base fare < $5 filter |
| `watcher/pairing.py` | Match outbound + return legs into `RoundTrip` |
| `watcher/format.py` | `RoundTrip` → concise SMS string |
| `watcher/state.py` | Load/save `seen_flights.json`, diff new vs. seen |
| `watcher/notify.py` | Send SMS via Gmail SMTP → Verizon email gateway |
| `main.py` | Orchestrate all modules, determine morning/evening run |
| `.github/workflows/watcher.yml` | Cron schedule, secrets, state commit |
| `state/seen_flights.json` | Persisted state (committed by Actions) |
| `requirements.txt` | `requests`, `pytz` |
| `tests/test_filter.py` | Filter logic unit tests |
| `tests/test_pairing.py` | Pairing logic unit tests |
| `tests/test_format.py` | Formatter unit tests |
| `tests/test_state.py` | State diff/load/save unit tests |

---

## Task 1: Project Skeleton

**Files:**
- Create: `requirements.txt`
- Create: `state/seen_flights.json`
- Create: `watcher/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
requests>=2.31.0
pytz>=2024.1
pytest>=8.0.0
```

- [ ] **Step 2: Create state/seen_flights.json**

```json
{}
```

- [ ] **Step 3: Create empty init files**

```bash
touch watcher/__init__.py tests/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt state/seen_flights.json watcher/__init__.py tests/__init__.py
git commit -m "chore: project skeleton"
```

---

## Task 2: Config and Data Models

**Files:**
- Create: `watcher/config.py`
- Create: `watcher/models.py`

- [ ] **Step 1: Create watcher/config.py**

```python
ORIGINS = ["SFO", "SJC", "OAK"]

DESTINATIONS = [
    "LAX",  # Los Angeles
    "SAN",  # San Diego
    "SNA",  # Orange County
    "SEA",  # Seattle
    "PDX",  # Portland
    "YVR",  # Vancouver
    "SJU",  # San Juan, PR
    "HNL",  # Honolulu
    "OGG",  # Maui
    "KOA",  # Kona
    "LIH",  # Kauai
    "ORD",  # Chicago O'Hare
    "MDW",  # Chicago Midway
    "DEN",  # Denver
    "JFK",  # New York JFK
    "LGA",  # New York LaGuardia
    "MDT",  # Harrisburg
]

MAX_BASE_FARE = 5.00
LOOKAHEAD_DAYS = 10
SMS_TO = "7173799089@vtext.com"
THURSDAY = 3
FRIDAY = 4
SUNDAY = 6
MONDAY = 0
OUTBOUND_THURSDAY_HOUR = 17   # 5 PM
RETURN_MONDAY_HOUR = 20       # 8 PM
```

- [ ] **Step 2: Create watcher/models.py**

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Flight:
    origin: str
    destination: str
    depart_dt: datetime
    arrive_dt: datetime
    base_fare: float
    taxes_fees: float

    @property
    def total(self) -> float:
        return self.base_fare + self.taxes_fees

    @property
    def key(self) -> str:
        return f"{self.origin}-{self.destination}-{self.depart_dt.date()}-{self.depart_dt.strftime('%H%M')}"


@dataclass
class RoundTrip:
    outbound: Flight
    inbound: Flight

    @property
    def key(self) -> str:
        return (
            f"{self.outbound.origin}-{self.outbound.destination}"
            f"-{self.outbound.depart_dt.date()}-{self.inbound.depart_dt.date()}"
        )

    @property
    def total_fees(self) -> float:
        return self.outbound.taxes_fees + self.inbound.taxes_fees
```

- [ ] **Step 3: Commit**

```bash
git add watcher/config.py watcher/models.py
git commit -m "feat: config and data models"
```

---

## Task 3: Frontier API Search Module

**Files:**
- Create: `watcher/search.py`
- Create: `explore_api.py` (temporary discovery script, deleted after Task 3)

The Frontier internal API response format is undocumented. This task starts by making a real call and printing the raw response, then builds the parser around what actually comes back.

- [ ] **Step 1: Create explore_api.py to discover the response shape**

```python
#!/usr/bin/env python3
"""Run once to discover Frontier API response format. Delete after."""
import json
import requests
from datetime import date, timedelta

url = "https://mtier.flyfrontier.com/flightavailabilityssv/FlightAvailabilitySimpleSearch"
begin = (date.today() + timedelta(days=1)).isoformat()
end = (date.today() + timedelta(days=3)).isoformat()

payload = {
    "flightAvailabilityRequestModel": {
        "passengers": [{"passengerType": "ADT", "count": 1, "residentCountry": "US"}],
        "filters": {"maxConnections": 0},
        "codes": {"currencyCode": "USD"},
        "origin": "SFO",
        "destination": "LAX",
        "beginDate": begin,
        "endDate": end,
    }
}
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

resp = requests.post(url, json=payload, headers=headers, timeout=30)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2))
```

- [ ] **Step 2: Run explore_api.py and read the output**

```bash
python explore_api.py
```

Expected: A JSON response. Read the shape carefully — identify:
- The array key that contains individual flights (e.g., `trips`, `journeys`, `flights`)
- The departure datetime field name and format
- The arrival datetime field name and format
- The base fare field name and location (may be nested under `fares`, `pricing`, `price`)
- The taxes + fees field name(s)

Note: If the API returns HTTP 403 or 401, add a `Referer: https://www.flyfrontier.com/` header and retry.

- [ ] **Step 3: Create watcher/search.py using the actual response shape**

Replace the parser below with the actual field names discovered in Step 2. The structure shown is a best-guess based on similar NDC APIs — adjust as needed.

```python
import requests
from datetime import date, datetime
from typing import Optional
from watcher.models import Flight

_URL = "https://mtier.flyfrontier.com/flightavailabilityssv/FlightAvailabilitySimpleSearch"
_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Referer": "https://www.flyfrontier.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def search_one_way(
    origin: str,
    destination: str,
    begin: date,
    end: date,
) -> list[Flight]:
    payload = {
        "flightAvailabilityRequestModel": {
            "passengers": [{"passengerType": "ADT", "count": 1, "residentCountry": "US"}],
            "filters": {"maxConnections": 0},
            "codes": {"currencyCode": "USD"},
            "origin": origin,
            "destination": destination,
            "beginDate": begin.isoformat(),
            "endDate": end.isoformat(),
        }
    }
    resp = requests.post(_URL, json=payload, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return _parse_flights(origin, destination, resp.json())


def _parse_flights(origin: str, destination: str, data: dict) -> list[Flight]:
    flights: list[Flight] = []

    # NOTE: adjust the keys below to match the actual API response shape
    # discovered in explore_api.py. Common patterns: data["trips"],
    # data["journeys"], data["availableFlights"], data["segments"]
    trips = data.get("trips") or data.get("journeys") or data.get("flights") or []

    for trip in trips:
        # Segments may be nested — adapt path to actual structure
        segments = trip.get("segments") or trip.get("legs") or [trip]
        fares = trip.get("fares") or trip.get("pricing") or [{}]
        if not fares:
            continue
        fare = fares[0]

        for seg in segments:
            depart_raw = seg.get("departureDateTime") or seg.get("departuretime") or seg.get("departure")
            arrive_raw = seg.get("arrivalDateTime") or seg.get("arrivaltime") or seg.get("arrival")
            if not depart_raw or not arrive_raw:
                continue

            depart_dt = _parse_dt(depart_raw)
            arrive_dt = _parse_dt(arrive_raw)
            if depart_dt is None or arrive_dt is None:
                continue

            base = float(fare.get("baseFare") or fare.get("basefare") or fare.get("base") or 0)
            taxes = float(fare.get("taxes") or fare.get("taxAmount") or 0)
            fees = float(fare.get("fees") or fare.get("feeAmount") or 0)
            taxes_fees = taxes + fees

            flights.append(Flight(
                origin=origin,
                destination=destination,
                depart_dt=depart_dt,
                arrive_dt=arrive_dt,
                base_fare=base,
                taxes_fees=taxes_fees,
            ))

    return flights


def _parse_dt(raw: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt[:len(fmt.split("%")[0])+15])
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw[:19])
    except ValueError:
        return None
```

- [ ] **Step 4: Verify search_one_way returns Flight objects**

```bash
python -c "
from datetime import date, timedelta
from watcher.search import search_one_way
flights = search_one_way('SFO', 'LAX', date.today(), date.today() + timedelta(days=3))
print(f'Found {len(flights)} flights')
for f in flights[:3]:
    print(f'  {f.depart_dt} base={f.base_fare} fees={f.taxes_fees}')
"
```

Expected: At least some flights printed. If 0 flights and no error, re-examine the response JSON from Step 2 and adjust field names in `_parse_flights`.

- [ ] **Step 5: Delete explore_api.py**

```bash
rm explore_api.py
```

- [ ] **Step 6: Write tests for search with mocked response**

Create `tests/test_search.py`:

```python
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from watcher.search import search_one_way, _parse_flights


MOCK_RESPONSE = {
    "trips": [
        {
            "segments": [
                {
                    "departureDateTime": "2026-05-15T18:30:00",
                    "arrivalDateTime": "2026-05-15T20:15:00",
                }
            ],
            "fares": [
                {"baseFare": 0.01, "taxes": 11.20, "fees": 2.80}
            ],
        }
    ]
}


def test_parse_flights_extracts_flight():
    flights = _parse_flights("SFO", "LAX", MOCK_RESPONSE)
    assert len(flights) == 1
    f = flights[0]
    assert f.origin == "SFO"
    assert f.destination == "LAX"
    assert f.base_fare == 0.01
    assert f.taxes_fees == pytest.approx(14.00, abs=0.01)
    assert f.depart_dt.hour == 18
    assert f.depart_dt.minute == 30


def test_parse_flights_empty_trips():
    assert _parse_flights("SFO", "LAX", {"trips": []}) == []


def test_parse_flights_missing_fare():
    data = {"trips": [{"segments": [{"departureDateTime": "2026-05-15T18:30:00", "arrivalDateTime": "2026-05-15T20:15:00"}], "fares": []}]}
    assert _parse_flights("SFO", "LAX", data) == []


def test_search_one_way_calls_api():
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_RESPONSE
    with patch("watcher.search.requests.post", return_value=mock_resp) as mock_post:
        flights = search_one_way("SFO", "LAX", date(2026, 5, 15), date(2026, 5, 15))
    assert mock_post.called
    call_json = mock_post.call_args.kwargs["json"]
    assert call_json["flightAvailabilityRequestModel"]["origin"] == "SFO"
    assert call_json["flightAvailabilityRequestModel"]["destination"] == "LAX"
    assert len(flights) == 1
```

Add `import pytest` at the top of the file.

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_search.py -v
```

Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add watcher/search.py tests/test_search.py
git commit -m "feat: frontier API search module"
```

---

## Task 4: Flight Filter

**Files:**
- Create: `watcher/filter.py`
- Create: `tests/test_filter.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_filter.py`:

```python
from datetime import datetime
from watcher.filter import is_valid_outbound, is_valid_inbound, is_gowild_price
from watcher.models import Flight


def _flight(depart: datetime, base: float = 0.01, taxes: float = 12.0) -> Flight:
    return Flight("SFO", "LAX", depart, depart, base, taxes)


# --- outbound window ---

def test_thursday_after_5pm_is_valid_outbound():
    dt = datetime(2026, 5, 14, 18, 0)  # Thursday 6pm
    assert is_valid_outbound(_flight(dt)) is True


def test_thursday_before_5pm_is_invalid_outbound():
    dt = datetime(2026, 5, 14, 16, 59)  # Thursday 4:59pm
    assert is_valid_outbound(_flight(dt)) is False


def test_thursday_at_5pm_is_valid_outbound():
    dt = datetime(2026, 5, 14, 17, 0)  # Thursday exactly 5pm
    assert is_valid_outbound(_flight(dt)) is True


def test_friday_morning_is_valid_outbound():
    dt = datetime(2026, 5, 15, 7, 30)  # Friday 7:30am
    assert is_valid_outbound(_flight(dt)) is True


def test_wednesday_is_invalid_outbound():
    dt = datetime(2026, 5, 13, 20, 0)  # Wednesday 8pm
    assert is_valid_outbound(_flight(dt)) is False


def test_saturday_is_invalid_outbound():
    dt = datetime(2026, 5, 16, 10, 0)  # Saturday
    assert is_valid_outbound(_flight(dt)) is False


# --- inbound window ---

def test_sunday_any_time_is_valid_inbound():
    dt = datetime(2026, 5, 17, 6, 0)  # Sunday 6am
    assert is_valid_inbound(_flight(dt)) is True


def test_monday_before_8pm_is_valid_inbound():
    dt = datetime(2026, 5, 18, 19, 59)  # Monday 7:59pm
    assert is_valid_inbound(_flight(dt)) is True


def test_monday_at_8pm_is_valid_inbound():
    dt = datetime(2026, 5, 18, 20, 0)  # Monday 8pm exactly
    assert is_valid_inbound(_flight(dt)) is True


def test_monday_after_8pm_is_invalid_inbound():
    dt = datetime(2026, 5, 18, 20, 1)  # Monday 8:01pm
    assert is_valid_inbound(_flight(dt)) is False


def test_tuesday_is_invalid_inbound():
    dt = datetime(2026, 5, 19, 10, 0)
    assert is_valid_inbound(_flight(dt)) is False


# --- price filter ---

def test_gowild_price_penny_base():
    f = _flight(datetime(2026, 5, 15, 9, 0), base=0.01, taxes=12.00)
    assert is_gowild_price(f) is True


def test_gowild_price_zero_base():
    f = _flight(datetime(2026, 5, 15, 9, 0), base=0.0, taxes=12.00)
    assert is_gowild_price(f) is True


def test_gowild_price_just_under_limit():
    f = _flight(datetime(2026, 5, 15, 9, 0), base=4.99, taxes=12.00)
    assert is_gowild_price(f) is True


def test_gowild_price_at_limit():
    f = _flight(datetime(2026, 5, 15, 9, 0), base=5.00, taxes=12.00)
    assert is_gowild_price(f) is False


def test_regular_fare_rejected():
    f = _flight(datetime(2026, 5, 15, 9, 0), base=89.00, taxes=12.00)
    assert is_gowild_price(f) is False
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_filter.py -v
```

Expected: All FAIL with `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement watcher/filter.py**

```python
from watcher.config import (
    MAX_BASE_FARE,
    THURSDAY, FRIDAY, SUNDAY, MONDAY,
    OUTBOUND_THURSDAY_HOUR, RETURN_MONDAY_HOUR,
)
from watcher.models import Flight


def is_valid_outbound(flight: Flight) -> bool:
    wd = flight.depart_dt.weekday()
    if wd == THURSDAY:
        return flight.depart_dt.hour >= OUTBOUND_THURSDAY_HOUR
    return wd == FRIDAY


def is_valid_inbound(flight: Flight) -> bool:
    wd = flight.depart_dt.weekday()
    if wd == MONDAY:
        return flight.depart_dt.hour <= RETURN_MONDAY_HOUR
    return wd == SUNDAY


def is_gowild_price(flight: Flight) -> bool:
    return flight.base_fare < MAX_BASE_FARE
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_filter.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add watcher/filter.py tests/test_filter.py
git commit -m "feat: weekend window and GoWild price filter"
```

---

## Task 5: Round Trip Pairing

**Files:**
- Create: `watcher/pairing.py`
- Create: `tests/test_pairing.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_pairing.py`:

```python
from datetime import datetime
from watcher.models import Flight, RoundTrip
from watcher.pairing import pair_round_trips


def _f(origin, dest, depart: datetime, base=0.01, taxes=12.0) -> Flight:
    return Flight(origin, dest, depart, depart, base, taxes)


def test_thursday_outbound_pairs_with_sunday():
    # Thu evening outbound + Sunday inbound = valid 4-day window
    out = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))   # Thu
    back = _f("LAX", "SFO", datetime(2026, 5, 17, 15, 0))  # Sun
    trips = pair_round_trips([out], [back])
    assert len(trips) == 1
    assert trips[0].outbound is out
    assert trips[0].inbound is back


def test_thursday_outbound_pairs_with_monday():
    # Thu evening outbound + Monday inbound = valid 4-day window
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
    back = _f("LAX", "SFO", datetime(2026, 5, 16, 15, 0))  # Sat (wrong day)
    trips = pair_round_trips([out], [back])
    assert len(trips) == 0


def test_thursday_does_not_pair_with_next_weekend_sunday():
    # Thu May 14 should not pair with Sun May 24 (different weekend)
    out = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))
    back = _f("LAX", "SFO", datetime(2026, 5, 24, 12, 0))
    trips = pair_round_trips([out], [back])
    assert len(trips) == 0


def test_multiple_outbounds_multiple_inbounds():
    out1 = _f("SFO", "LAX", datetime(2026, 5, 14, 18, 0))  # Thu May 14
    out2 = _f("SFO", "LAX", datetime(2026, 5, 15, 7, 0))   # Fri May 15
    back1 = _f("LAX", "SFO", datetime(2026, 5, 17, 12, 0)) # Sun May 17
    back2 = _f("LAX", "SFO", datetime(2026, 5, 18, 14, 0)) # Mon May 18
    trips = pair_round_trips([out1, out2], [back1, back2])
    # Thu14→Sun17, Thu14→Mon18, Fri15→Sun17, Fri15→Mon18
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
```

Add `import pytest` at the top.

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_pairing.py -v
```

Expected: All FAIL.

- [ ] **Step 3: Implement watcher/pairing.py**

```python
from datetime import timedelta
from watcher.config import THURSDAY, FRIDAY, SUNDAY, MONDAY
from watcher.models import Flight, RoundTrip


def _expected_return_dates(outbound: Flight) -> set:
    """Given an outbound flight, return the valid return dates for the same weekend."""
    out_date = outbound.depart_dt.date()
    wd = outbound.depart_dt.weekday()
    if wd == THURSDAY:
        return {out_date + timedelta(days=3), out_date + timedelta(days=4)}  # Sun, Mon
    if wd == FRIDAY:
        return {out_date + timedelta(days=2), out_date + timedelta(days=3)}  # Sun, Mon
    return set()


def pair_round_trips(outbounds: list[Flight], inbounds: list[Flight]) -> list[RoundTrip]:
    trips: list[RoundTrip] = []
    for out in outbounds:
        valid_dates = _expected_return_dates(out)
        for back in inbounds:
            if back.depart_dt.date() in valid_dates:
                trips.append(RoundTrip(outbound=out, inbound=back))
    return trips
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_pairing.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add watcher/pairing.py tests/test_pairing.py
git commit -m "feat: round trip pairing logic"
```

---

## Task 6: SMS Formatter

**Files:**
- Create: `watcher/format.py`
- Create: `tests/test_format.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_format.py`:

```python
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
    # Modify t2 to be OAK->SEA
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_format.py -v
```

Expected: All FAIL.

- [ ] **Step 3: Implement watcher/format.py**

```python
from watcher.models import RoundTrip

DAY_ABBR = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}


def _time_str(dt) -> str:
    suffix = "a" if dt.hour < 12 else "p"
    hour = dt.hour % 12 or 12
    return f"{hour}:{dt.minute:02d}{suffix}"


def _date_str(dt) -> str:
    return f"{DAY_ABBR[dt.weekday()]}{dt.month}/{dt.day}"


def format_trip(trip: RoundTrip) -> str:
    out = trip.outbound
    back = trip.inbound
    total = round(trip.total_fees)
    return (
        f"{out.origin}>{out.destination} "
        f"{_date_str(out.depart_dt)} {_time_str(out.depart_dt)}"
        f">{_date_str(back.depart_dt)} {_time_str(back.depart_dt)} "
        f"${total}"
    )


def format_digest(trips: list[RoundTrip]) -> str:
    if not trips:
        return "No GoWild flights found."
    return "\n".join(format_trip(t) for t in trips)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_format.py -v
```

Expected: All PASS. If a time format test fails, check `_time_str` AM/PM logic — noon (hour=12) should be `p`, midnight (hour=0) should be `a`.

- [ ] **Step 5: Commit**

```bash
git add watcher/format.py tests/test_format.py
git commit -m "feat: SMS flight formatter"
```

---

## Task 7: State Management

**Files:**
- Create: `watcher/state.py`
- Create: `tests/test_state.py`

State is a `dict[str, str]` mapping round trip key → ISO date string of the outbound flight (used for expiry). Stored in `state/seen_flights.json`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_state.py`:

```python
import json
import tempfile
from pathlib import Path
from datetime import date
from watcher.models import Flight, RoundTrip
from watcher.state import load_state, save_state, find_new_trips, expire_old_trips


def _trip(key_suffix: str, out_date: date) -> RoundTrip:
    from datetime import datetime
    out_dt = datetime.combine(out_date, datetime.min.time().replace(hour=18))
    in_dt = datetime.combine(out_date, datetime.min.time().replace(hour=15))
    out = Flight("SFO", "LAX", out_dt, out_dt, 0.01, 12.0)
    back = Flight("LAX", "SFO", in_dt, in_dt, 0.01, 12.0)
    rt = RoundTrip(outbound=out, inbound=back)
    # Override key for easier testing
    rt._test_key = f"SFO-LAX-{key_suffix}"
    rt.__class__.key = property(lambda self: getattr(self, "_test_key", RoundTrip.key.fget(self)))
    return rt


def test_load_state_returns_empty_dict_when_file_missing():
    state = load_state(Path("/tmp/nonexistent_99999.json"))
    assert state == {}


def test_save_and_load_round_trip():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    state = {"SFO-LAX-2026-05-14-2026-05-17": "2026-05-14"}
    save_state(state, path)
    loaded = load_state(path)
    assert loaded == state


def test_find_new_trips_all_new():
    trips = [_trip("2026-05-14-2026-05-17", date(2026, 5, 14))]
    new = find_new_trips(trips, {})
    assert len(new) == 1


def test_find_new_trips_already_seen():
    trips = [_trip("2026-05-14-2026-05-17", date(2026, 5, 14))]
    state = {"SFO-LAX-2026-05-14-2026-05-17": "2026-05-14"}
    new = find_new_trips(trips, state)
    assert len(new) == 0


def test_find_new_trips_mixed():
    t1 = _trip("2026-05-14-2026-05-17", date(2026, 5, 14))
    t2 = _trip("2026-05-21-2026-05-24", date(2026, 5, 21))
    state = {"SFO-LAX-2026-05-14-2026-05-17": "2026-05-14"}
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_state.py -v
```

Expected: All FAIL.

- [ ] **Step 3: Implement watcher/state.py**

```python
import json
from datetime import date
from pathlib import Path
from watcher.models import RoundTrip

_DEFAULT_PATH = Path("state/seen_flights.json")


def load_state(path: Path = _DEFAULT_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_state(state: dict[str, str], path: Path = _DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True))


def find_new_trips(trips: list[RoundTrip], state: dict[str, str]) -> list[RoundTrip]:
    return [t for t in trips if t.key not in state]


def expire_old_trips(state: dict[str, str], today: date) -> dict[str, str]:
    return {k: v for k, v in state.items() if date.fromisoformat(v) >= today}
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_state.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add watcher/state.py tests/test_state.py
git commit -m "feat: flight state management and deduplication"
```

---

## Task 8: Notifications

**Files:**
- Create: `watcher/notify.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_notify.py`:

```python
from unittest.mock import patch, MagicMock
from watcher.notify import send_sms


def test_send_sms_connects_to_gmail_smtp():
    with patch("watcher.notify.smtplib.SMTP_SSL") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_sms("test message", "test@example.com", "testuser@gmail.com", "apppassword")

    mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 465)
    mock_smtp.login.assert_called_once_with("testuser@gmail.com", "apppassword")
    mock_smtp.sendmail.assert_called_once()
    _, to_addr, _ = mock_smtp.sendmail.call_args.args
    assert to_addr == "test@example.com"


def test_send_sms_message_in_body():
    with patch("watcher.notify.smtplib.SMTP_SSL") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_sms("SFO>LAX Thu5/14 $24", "7173799089@vtext.com", "me@gmail.com", "pw")

    _, _, raw_msg = mock_smtp.sendmail.call_args.args
    assert "SFO>LAX Thu5/14 $24" in raw_msg
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_notify.py -v
```

Expected: FAIL.

- [ ] **Step 3: Implement watcher/notify.py**

```python
import smtplib
from email.mime.text import MIMEText


def send_sms(message: str, to: str, gmail_address: str, gmail_app_password: str) -> None:
    msg = MIMEText(message)
    msg["From"] = gmail_address
    msg["To"] = to
    msg["Subject"] = ""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.sendmail(gmail_address, to, msg.as_string())
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_notify.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add watcher/notify.py tests/test_notify.py
git commit -m "feat: email-to-SMS notification via Gmail"
```

---

## Task 9: Main Orchestration

**Files:**
- Create: `main.py`

- [ ] **Step 1: Create main.py**

```python
import os
import sys
from datetime import date, timedelta
import pytz

from watcher.config import ORIGINS, DESTINATIONS, SMS_TO
from watcher.filter import is_valid_outbound, is_valid_inbound, is_gowild_price
from watcher.format import format_trip, format_digest
from watcher.models import RoundTrip
from watcher.notify import send_sms
from watcher.pairing import pair_round_trips
from watcher.search import search_one_way
from watcher.state import load_state, save_state, find_new_trips, expire_old_trips

PACIFIC = pytz.timezone("America/Los_Angeles")
STATE_PATH_STR = "state/seen_flights.json"


def _gmail_creds() -> tuple[str, str]:
    addr = os.environ["GMAIL_ADDRESS"]
    pw = os.environ["GMAIL_APP_PASSWORD"]
    return addr, pw


def _is_morning_run() -> bool:
    from datetime import datetime
    from pathlib import Path
    now = datetime.now(PACIFIC)
    return now.hour < 12


def _search_route(origin: str, destination: str, today: date) -> list[RoundTrip]:
    end = today + timedelta(days=10)
    errors = []

    try:
        outbounds = search_one_way(origin, destination, today, end)
    except Exception as e:
        errors.append(f"{origin}>{destination}: {e}")
        outbounds = []

    try:
        inbounds = search_one_way(destination, origin, today, end)
    except Exception as e:
        errors.append(f"{destination}>{origin}: {e}")
        inbounds = []

    outbounds = [f for f in outbounds if is_valid_outbound(f) and is_gowild_price(f)]
    inbounds = [f for f in inbounds if is_valid_inbound(f) and is_gowild_price(f)]
    return pair_round_trips(outbounds, inbounds), errors


def main() -> None:
    from pathlib import Path
    gmail_addr, gmail_pw = _gmail_creds()
    today = date.today()
    state_path = Path(STATE_PATH_STR)
    state = load_state(state_path)
    state = expire_old_trips(state, today)
    is_morning = _is_morning_run()

    all_trips: list[RoundTrip] = []
    all_errors: list[str] = []

    for origin in ORIGINS:
        for destination in DESTINATIONS:
            if origin == destination:
                continue
            trips, errors = _search_route(origin, destination, today)
            all_trips.extend(trips)
            all_errors.extend(errors)

    new_trips = find_new_trips(all_trips, state)

    for trip in new_trips:
        try:
            send_sms(format_trip(trip), SMS_TO, gmail_addr, gmail_pw)
        except Exception as e:
            all_errors.append(f"SMS send failed: {e}")
        state[trip.key] = trip.outbound.depart_dt.date().isoformat()

    if is_morning:
        digest = format_digest(all_trips)
        try:
            send_sms(digest, SMS_TO, gmail_addr, gmail_pw)
        except Exception as e:
            all_errors.append(f"Digest SMS failed: {e}")

    if all_errors:
        error_msg = "GoWild watcher errors:\n" + "\n".join(all_errors[:5])
        try:
            send_sms(error_msg, SMS_TO, gmail_addr, gmail_pw)
        except Exception:
            pass

    save_state(state, state_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Dry-run locally (no SMS sent)**

```bash
GMAIL_ADDRESS=test@gmail.com GMAIL_APP_PASSWORD=fake python -c "
import sys
from unittest.mock import patch
with patch('watcher.notify.send_sms') as mock_sms:
    import main
    main.main()
    print(f'send_sms called {mock_sms.call_count} times')
    for call in mock_sms.call_args_list:
        print(' MSG:', call.args[0][:80])
"
```

Expected: Runs without crashing. May show 0 SMS calls if no GoWild flights are available today, which is fine — verify by checking if `search_one_way` is returning flights at all.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: main orchestration script"
```

---

## Task 10: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/watcher.yml`

- [ ] **Step 1: Create .github/workflows/watcher.yml**

```yaml
name: GoWild Flight Watcher

on:
  schedule:
    - cron: '0 15 * * *'   # 8 AM Pacific (UTC-7 summer / UTC-8 winter)
    - cron: '0 1 * * *'    # 6 PM Pacific
  workflow_dispatch:        # allow manual trigger from Actions tab

jobs:
  watch:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run watcher
        env:
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
        run: python main.py

      - name: Commit updated state
        run: |
          git config user.email "actions@github.com"
          git config user.name "GitHub Actions"
          git add state/seen_flights.json
          git diff --staged --quiet || git commit -m "chore: update flight state [skip ci]"
          git push
```

- [ ] **Step 2: Create the GitHub repo and push**

```bash
git remote add origin https://github.com/YOUR_USERNAME/gowild-watcher.git
git push -u origin master
```

Replace `YOUR_USERNAME` with your actual GitHub username.

- [ ] **Step 3: Add GitHub Secrets**

In the repo on GitHub: Settings → Secrets and variables → Actions → New repository secret

Add two secrets:
- `GMAIL_ADDRESS` — your Gmail address (e.g., `you@gmail.com`)
- `GMAIL_APP_PASSWORD` — a Gmail App Password (NOT your Gmail login password). Generate at: Google Account → Security → 2-Step Verification → App passwords → create one named "gowild-watcher"

- [ ] **Step 4: Trigger a manual run to verify**

In GitHub: Actions tab → "GoWild Flight Watcher" → "Run workflow" → Run

Watch the logs. Expected: the run completes, `state/seen_flights.json` gets committed (if any flights found), and you receive SMS texts.

- [ ] **Step 5: Commit workflow**

```bash
git add .github/workflows/watcher.yml
git commit -m "feat: github actions cron workflow"
git push
```

---

## Spec Coverage Self-Review

| Requirement | Covered by |
|-------------|-----------|
| Query Frontier API for GoWild flights | Task 3 (search.py) |
| Bay Area origins: SFO, SJC, OAK | Task 2 (config.py) |
| Curated destination list | Task 2 (config.py) |
| Base fare < $5 filter | Task 4 (filter.py) |
| 10-day lookahead | Task 9 (main.py) |
| Thu 5pm+ or Fri outbound | Task 4 (filter.py) |
| Sun or Mon ≤8pm return | Task 4 (filter.py) |
| Same-weekend pairing | Task 5 (pairing.py) |
| Deduplication / seen state | Task 7 (state.py) |
| New flight alert SMS | Task 9 (main.py) |
| Morning digest SMS | Task 9 (main.py) |
| Email-to-SMS 7173799089@vtext.com | Task 8 (notify.py) + Task 2 config |
| Total taxes+fees shown, format `SFO>LAX Thu5/14 6:30p>Sun5/17 3p $24` | Task 6 (format.py) |
| Twice daily via GitHub Actions | Task 10 (watcher.yml) |
| State committed back to repo | Task 10 (watcher.yml) |
| Error SMS if API fails | Task 9 (main.py) |
