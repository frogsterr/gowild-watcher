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


def test_wednesday_evening_is_valid_outbound():
    dt = datetime(2026, 5, 13, 20, 0)  # Wednesday 8pm
    assert is_valid_outbound(_flight(dt)) is True


def test_wednesday_at_5pm_is_valid_outbound():
    dt = datetime(2026, 5, 13, 17, 0)  # Wednesday exactly 5pm
    assert is_valid_outbound(_flight(dt)) is True


def test_wednesday_before_5pm_is_invalid_outbound():
    dt = datetime(2026, 5, 13, 16, 59)  # Wednesday 4:59pm
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


def test_tuesday_is_valid_inbound():
    dt = datetime(2026, 5, 19, 10, 0)
    assert is_valid_inbound(_flight(dt)) is True


def test_tuesday_evening_is_valid_inbound():
    dt = datetime(2026, 5, 19, 20, 0)
    assert is_valid_inbound(_flight(dt)) is True


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
