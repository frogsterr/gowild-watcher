from datetime import date, timedelta

from watcher.config import DESTINATIONS, LOOKAHEAD_DAYS, ORIGINS, PRIORITY_DESTINATIONS
from watcher.workqueue import build_sweep


def test_build_sweep_total_item_count():
    today = date(2026, 8, 15)
    items = build_sweep(today)
    outbound_days = LOOKAHEAD_DAYS + 1
    inbound_days = LOOKAHEAD_DAYS + 6 + 1
    expected = len(ORIGINS) * len(DESTINATIONS) * (outbound_days + inbound_days)
    assert len(items) == expected


def test_priority_destinations_are_last():
    """Every work item touching a priority destination sits after every item that doesn't."""
    today = date(2026, 8, 15)
    items = build_sweep(today)

    def touches_priority(item):
        return item.origin in PRIORITY_DESTINATIONS or item.destination in PRIORITY_DESTINATIONS

    flags = [touches_priority(item) for item in items]
    # Once we see a priority item, every subsequent item must also be a priority item.
    first_priority_idx = flags.index(True)
    assert all(flags[first_priority_idx:])
    assert not any(flags[:first_priority_idx])

    for dest in PRIORITY_DESTINATIONS:
        assert any(item.origin == dest or item.destination == dest for item in items)


def test_outbound_dates_start_today():
    today = date(2026, 8, 15)
    items = build_sweep(today)
    outbound_items = [i for i in items if i.origin in ORIGINS]
    assert min(i.day for i in outbound_items) == today
    assert max(i.day for i in outbound_items) == today + timedelta(days=LOOKAHEAD_DAYS)


def test_inbound_dates_extend_six_more_days():
    today = date(2026, 8, 15)
    items = build_sweep(today)
    inbound_items = [i for i in items if i.destination in ORIGINS]
    outbound_end = today + timedelta(days=LOOKAHEAD_DAYS)
    assert max(i.day for i in inbound_items) == outbound_end + timedelta(days=6)


def test_work_item_key_format():
    today = date(2026, 8, 15)
    item = build_sweep(today)[0]
    assert item.key == f"{item.origin}-{item.destination}-{item.day.isoformat()}"
