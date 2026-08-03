from datetime import date
from pathlib import Path

from watcher.cache import load_sweep_state, run_collector_batch, save_sweep_state
from watcher.config import COLLECTOR_BATCH_SIZE
from watcher.search import search_one_day

STATE_PATH = Path("state/sweep_state.json")


def main() -> None:
    today = date.today()
    if today > date(2026, 9, 10):
        return

    state = load_sweep_state(STATE_PATH)
    state = run_collector_batch(state, today, COLLECTOR_BATCH_SIZE, fetch=search_one_day)
    save_sweep_state(state, STATE_PATH)


if __name__ == "__main__":
    main()
