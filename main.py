import os
from datetime import date, datetime, timedelta
from pathlib import Path
import pytz

from watcher.config import ORIGINS, DESTINATIONS, SMS_TO, LOOKAHEAD_DAYS
from watcher.filter import is_valid_outbound, is_valid_inbound, is_gowild_price
from watcher.format import format_trip, format_digest
from watcher.models import RoundTrip
from watcher.notify import send_sms
from watcher.pairing import pair_round_trips
from watcher.search import search_one_way
from watcher.state import load_state, save_state, find_new_trips, expire_old_trips

PACIFIC = pytz.timezone("America/Los_Angeles")
STATE_PATH = Path("state/seen_flights.json")


def _gmail_creds() -> tuple[str, str]:
    return os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"]


def _is_morning_run() -> bool:
    return datetime.now(PACIFIC).hour < 12


def _search_route(origin: str, destination: str, today: date) -> tuple[list[RoundTrip], list[str]]:
    end = today + timedelta(days=LOOKAHEAD_DAYS)
    errors: list[str] = []

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
    gmail_addr, gmail_pw = _gmail_creds()
    today = date.today()
    state = expire_old_trips(load_state(STATE_PATH), today)
    is_morning = _is_morning_run()

    all_trips: list[RoundTrip] = []
    all_errors: list[str] = []

    for origin in ORIGINS:
        for destination in DESTINATIONS:
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
        try:
            send_sms(format_digest(all_trips), SMS_TO, gmail_addr, gmail_pw)
        except Exception as e:
            all_errors.append(f"Digest SMS failed: {e}")

    if all_errors:
        error_msg = "GoWild watcher errors:\n" + "\n".join(all_errors[:5])
        try:
            send_sms(error_msg, SMS_TO, gmail_addr, gmail_pw)
        except Exception:
            pass

    save_state(state, STATE_PATH)


if __name__ == "__main__":
    main()
