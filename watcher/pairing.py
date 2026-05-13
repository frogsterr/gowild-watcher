from datetime import timedelta
from watcher.config import THURSDAY, FRIDAY
from watcher.models import Flight, RoundTrip


def _expected_return_dates(outbound: Flight) -> set:
    """
    Compute the set of valid return dates for an outbound flight.
    - Thursday outbound → valid returns are +3 days (Sunday) and +4 days (Monday)
    - Friday outbound → valid returns are +2 days (Sunday) and +3 days (Monday)
    """
    out_date = outbound.depart_dt.date()
    wd = outbound.depart_dt.weekday()
    if wd == THURSDAY:
        return {out_date + timedelta(days=3), out_date + timedelta(days=4)}  # Sun, Mon
    if wd == FRIDAY:
        return {out_date + timedelta(days=2), out_date + timedelta(days=3)}  # Sun, Mon
    return set()


def pair_round_trips(outbounds: list[Flight], inbounds: list[Flight]) -> list[RoundTrip]:
    """
    Pair outbound and inbound flights into RoundTrip objects.
    Only pairs flights from the same weekend (Thu/Fri departure with Sun/Mon return).
    """
    trips: list[RoundTrip] = []
    for out in outbounds:
        valid_dates = _expected_return_dates(out)
        for back in inbounds:
            if back.depart_dt.date() in valid_dates:
                trips.append(RoundTrip(outbound=out, inbound=back))
    return trips
