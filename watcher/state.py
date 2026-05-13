import json
from datetime import date
from pathlib import Path
from watcher.models import RoundTrip

_DEFAULT_PATH = Path("state/seen_flights.json")


def load_state(path: Path = _DEFAULT_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def save_state(state: dict[str, str], path: Path = _DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True))


def find_new_trips(trips: list[RoundTrip], state: dict[str, str]) -> list[RoundTrip]:
    return [t for t in trips if t.key not in state]


def expire_old_trips(state: dict[str, str], today: date) -> dict[str, str]:
    result = {}
    for k, v in state.items():
        try:
            if date.fromisoformat(v) >= today:
                result[k] = v
        except ValueError:
            # Skip entries with invalid date strings
            pass
    return result
