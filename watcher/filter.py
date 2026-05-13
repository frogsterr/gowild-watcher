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
        dt = flight.depart_dt
        return dt.hour < RETURN_MONDAY_HOUR or (dt.hour == RETURN_MONDAY_HOUR and dt.minute == 0)
    return wd == SUNDAY


def is_gowild_price(flight: Flight) -> bool:
    return flight.base_fare < MAX_BASE_FARE
