"""Builds the flat, ordered list of (origin, destination, day) fetches needed for one full sweep."""
from dataclasses import dataclass
from datetime import date, timedelta

from .config import DESTINATIONS, LOOKAHEAD_DAYS, ORIGINS, PRIORITY_DESTINATIONS


@dataclass(frozen=True)
class WorkItem:
    origin: str
    destination: str
    day: date

    @property
    def key(self) -> str:
        return f"{self.origin}-{self.destination}-{self.day.isoformat()}"


def _ordered_route_pairs() -> list[tuple[str, str]]:
    """(origin, destination) pairs, with every priority-destination pair moved to the end."""
    normal = [d for d in DESTINATIONS if d not in PRIORITY_DESTINATIONS]
    priority = [d for d in PRIORITY_DESTINATIONS if d in DESTINATIONS]
    return [(o, d) for d in normal for o in ORIGINS] + [(o, d) for d in priority for o in ORIGINS]


def build_sweep(today: date) -> list[WorkItem]:
    """Full ordered list of individual day-fetches for one complete sweep starting *today*.

    Priority destinations' outbound and inbound fetches land at the end of the list, so
    they're always the most recently-fetched data at any point during a sweep.
    """
    outbound_end = today + timedelta(days=LOOKAHEAD_DAYS)
    inbound_end = outbound_end + timedelta(days=6)

    items: list[WorkItem] = []
    for origin, destination in _ordered_route_pairs():
        d = today
        while d <= outbound_end:
            items.append(WorkItem(origin, destination, d))
            d += timedelta(days=1)
        d = today
        while d <= inbound_end:
            items.append(WorkItem(destination, origin, d))
            d += timedelta(days=1)
    return items
