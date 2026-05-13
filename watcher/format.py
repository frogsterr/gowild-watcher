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
