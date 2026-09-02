"""PID-file control for runs. No name patterns, ever.

A `pkill -f "run_name c_t1"` that did not match the real command line
(`--run-name c_t1`) once reported a run dead while it kept going for another
16 minutes and wrote 44 rows from a stale in-memory dataset. Nothing here
matches on process names or command lines: a run records its own PID at launch
and every later operation acts on that PID alone.

    python src/runctl.py status <run_name>
    python src/runctl.py stop   <run_name>

The pid file also records the process creation time. PIDs are recycled, so a
stop verifies create-time before signalling; a mismatch is reported as stale
rather than acted on.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "runs"


def pid_path(run_name: str) -> Path:
    if not run_name or "/" in run_name or run_name.startswith("."):
        raise ValueError(f"bad run_name {run_name!r}")
    return RUNS_DIR / f"{run_name}.pid"


def _create_time(pid: int) -> float | None:
    try:
        import psutil

        return psutil.Process(pid).create_time()
    except Exception:
        return None


def write_pid(run_name: str) -> Path:
    """Record this process's PID for the run. Called by the runner at launch."""
    p = pid_path(run_name)
    p.parent.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    p.write_text(json.dumps({
        "pid": pid,
        "run_name": run_name,
        "create_time": _create_time(pid),
        "started": time.time(),
        "argv": sys.argv[1:],
    }) + "\n", encoding="utf-8")
    return p


def clear_pid(run_name: str) -> None:
    try:
        pid_path(run_name).unlink()
    except FileNotFoundError:
        pass


def _read(run_name: str) -> dict | None:
    p = pid_path(run_name)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def alive(pid: int, create_time: float | None) -> tuple[bool, str]:
    """Is that exact process still running? Guards against PID reuse."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False, "no such pid"
    except PermissionError:
        return True, "alive (not ours to signal)"
    now = _create_time(pid)
    if create_time is not None and now is not None and abs(now - create_time) > 1.0:
        return False, f"pid reused (create_time {now} != recorded {create_time})"
    return True, "alive"


def status(run_name: str) -> int:
    rec = _read(run_name)
    if rec is None:
        print(f"{run_name}: no pid file — not running (or exited cleanly)")
        return 1
    ok, why = alive(rec["pid"], rec.get("create_time"))
    age = time.time() - rec.get("started", time.time())
    print(f"{run_name}: pid {rec['pid']} {'RUNNING' if ok else 'NOT running'} ({why}), "
          f"started {age / 60:.1f} min ago")
    if not ok:
        print(f"  stale pid file at {pid_path(run_name)} — safe to remove")
    return 0 if ok else 1


def stop(run_name: str, sig: int = signal.SIGTERM, wait: float = 10.0) -> int:
    rec = _read(run_name)
    if rec is None:
        print(f"{run_name}: no pid file; nothing to stop")
        return 1
    pid = rec["pid"]
    ok, why = alive(pid, rec.get("create_time"))
    if not ok:
        print(f"{run_name}: pid {pid} is not our process ({why}); refusing to signal")
        clear_pid(run_name)
        return 1
    os.kill(pid, sig)
    deadline = time.time() + wait
    while time.time() < deadline:
        if not alive(pid, rec.get("create_time"))[0]:
            print(f"{run_name}: pid {pid} stopped")
            clear_pid(run_name)
            return 0
        time.sleep(0.3)
    os.kill(pid, signal.SIGKILL)
    time.sleep(1.0)
    still, _ = alive(pid, rec.get("create_time"))
    print(f"{run_name}: pid {pid} {'STILL ALIVE after SIGKILL' if still else 'killed (SIGKILL)'}")
    if not still:
        clear_pid(run_name)
    return 0 if not still else 2


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("status", "stop"):
        raise SystemExit(__doc__)
    sys.exit((status if sys.argv[1] == "status" else stop)(sys.argv[2]))
