import os
from datetime import date, datetime
from pathlib import Path
import pytz

from watcher.cache import load_all_flights, load_sweep_state
from watcher.config import DESTINATIONS, EMAIL_TO, ORIGINS
from watcher.filter import is_valid_outbound, is_valid_inbound, is_gowild_price
from watcher.format import format_email_subject, format_email_html
from watcher.models import RoundTrip
from watcher.notify import send_email
from watcher.pairing import pair_round_trips
from watcher.state import load_state, save_state, find_new_trips, expire_old_trips

PACIFIC = pytz.timezone("America/Los_Angeles")
STATE_PATH = Path("state/seen_flights.json")
SWEEP_STATE_PATH = Path("state/sweep_state.json")


def _gmail_creds() -> tuple[str, str]:
    return os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"]


def _is_morning_run() -> bool:
    return datetime.now(PACIFIC).hour < 12


def _route_trips(origin: str, destination: str, flights_by_route: dict) -> list[RoundTrip]:
    outbounds = flights_by_route.get((origin, destination), [])
    inbounds = flights_by_route.get((destination, origin), [])

    outbounds = [f for f in outbounds if is_valid_outbound(f) and is_gowild_price(f)]
    inbounds = [f for f in inbounds if is_valid_inbound(f) and is_gowild_price(f)]

    return pair_round_trips(outbounds, inbounds)


def main() -> None:
    today = date.today()
    if today > date(2026, 9, 10):
        return

    gmail_addr, gmail_pw = _gmail_creds()
    state = expire_old_trips(load_state(STATE_PATH), today)
    run_label = "Morning Run" if _is_morning_run() else "Evening Run"

    sweep_state = load_sweep_state(SWEEP_STATE_PATH)
    flights_by_route = load_all_flights(sweep_state)

    all_trips: list[RoundTrip] = []
    for origin in ORIGINS:
        for destination in DESTINATIONS:
            all_trips.extend(_route_trips(origin, destination, flights_by_route))

    new_trips = find_new_trips(all_trips, state)

    subject = format_email_subject(new_trips, run_label)
    body = format_email_html(new_trips, all_trips, run_label, today)
    email_sent = False
    try:
        send_email(subject, body, EMAIL_TO, gmail_addr, gmail_pw)
        email_sent = True
    except Exception as e:
        try:
            send_email(f"GoWild Watcher Errors · {run_label}", f"<pre>Email send failed: {e}</pre>", EMAIL_TO, gmail_addr, gmail_pw)
        except Exception:
            pass

    if email_sent:
        for trip in new_trips:
            state[trip.key] = trip.outbound.depart_dt.date().isoformat()

    save_state(state, STATE_PATH)


if __name__ == "__main__":
    main()
