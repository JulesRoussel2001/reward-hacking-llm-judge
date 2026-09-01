"""Concurrent task dispatch shared by the runners.

One pool, one lock. The lock guards the append+fsync AND the running-cost
accounting together, so a --max-usd decision is always made against a total
that includes every row already on disk and no row that isn't.

Ordering: rows may land in the file in a different order than they were
dispatched. Nothing depends on file order -- every row carries transcript_id,
prompt_variant and trial_id, and the analyses key on those.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Iterable

# Concurrency ceiling. Raise only after checking the account's rate limits;
# if 429s show up in a run log at 4, drop to 2 (SLEIGHT's call_anthropic
# already backs off, but sustained 429s just waste wall-clock).
MAX_WORKERS = 4


class Progress:
    """In-flight row -> stream events so far, for the heartbeat."""

    def __init__(self) -> None:
        self._d: dict[str, int] = {}
        self._lock = threading.Lock()

    def set(self, key: str, n: int) -> None:
        with self._lock:
            self._d[key] = n

    def drop(self, key: str) -> None:
        with self._lock:
            self._d.pop(key, None)

    def snapshot(self) -> list[tuple[str, int]]:
        with self._lock:
            return sorted(self._d.items())


def run_tasks(
    tasks: list[Any],
    call: Callable[[Any], dict],
    *,
    logger,
    cost_of: Callable[[dict], float],
    describe: Callable[[Any, dict, int, float], str],
    workers: int = 1,
    max_usd: float | None = None,
    heartbeat: float = 0.0,
    progress: Progress | None = None,
    total: int | None = None,
) -> tuple[list[dict], bool, int]:
    """Run `call` over `tasks`, logging each result exactly once.

    Returns (results, aborted, undispatched). On the cost cap: stop dispatching
    new calls, let in-flight ones finish and log, then return aborted=True.
    """
    workers = max(1, min(int(workers), MAX_WORKERS))
    stop = threading.Event()
    done = threading.Event()
    results: list[dict] = []
    state = {"spent": 0.0, "undispatched": 0, "announced": False}
    lock = logger.lock  # the same lock that guards write+fsync

    beat_thread = None
    if heartbeat and progress is not None:
        def _beat() -> None:
            while not done.wait(heartbeat):
                snap = progress.snapshot()
                if snap:
                    print("  [heartbeat] in flight: "
                          + "; ".join(f"{k} {n} events" for k, n in snap), flush=True)
        beat_thread = threading.Thread(target=_beat, daemon=True)
        beat_thread.start()

    def _work(task):
        if stop.is_set():
            with lock:
                state["undispatched"] += 1
            return None
        out = call(task)
        # log + account atomically, so the cap sees a consistent total
        n_written, spent, over = logger.log_and_account(
            out, cost_of(out), max_usd, lock_held=False
        )
        state["spent"] = spent
        first_crossing = False
        if over:
            with lock:                      # announce the cap exactly once
                first_crossing = not state["announced"]
                state["announced"] = True
            stop.set()
        print(describe(task, out, n_written, spent), flush=True)
        if first_crossing:
            print(f"\n!! cost cap hit: ${spent:.2f} > --max-usd {max_usd:.2f}\n"
                  f"   no new calls dispatched from here; in-flight calls finish and log.\n"
                  f"   re-run with --resume to continue.", flush=True)
        return out

    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for out in ex.map(_work, tasks):
                if out is not None:
                    results.append(out)
    finally:
        done.set()
        if beat_thread is not None:
            beat_thread.join(timeout=heartbeat + 1)

    return results, stop.is_set(), state["undispatched"]
