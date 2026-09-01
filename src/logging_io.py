#!/usr/bin/env python3
"""Append-only JSONL run logging.

One line per judge call, including refused and parse-failed calls — those are
the interesting rows for this pilot, not errors to be swallowed.

A run_name maps to runs/<run_name>.jsonl. Files are opened in append mode and
never truncated. `RunLogger` refuses to attach to a file that already exists
unless you pass `resume=True`, so a fresh run_name can't silently continue an
old file and a resumed one can't silently start over.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "runs"


def run_path(run_name: str) -> Path:
    if not run_name or "/" in run_name or run_name.startswith("."):
        raise ValueError(f"bad run_name {run_name!r}: no slashes, no leading dot")
    return RUNS_DIR / f"{run_name}.jsonl"


class RunLogger:
    """Append judge results to runs/<run_name>.jsonl."""

    def __init__(self, run_name: str, *, resume: bool = False):
        self.run_name = run_name
        self.path = run_path(run_name)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and not resume:
            raise FileExistsError(
                f"{self.path} already exists. Pick a new run_name, or pass "
                "resume=True to append to it deliberately."
            )
        self._n = 0

    def log(self, record: dict[str, Any]) -> None:
        """Append one record. Anything unserialisable is coerced to a string."""
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._n += 1

    @property
    def n_written(self) -> int:
        return self._n

    def __repr__(self) -> str:
        return f"RunLogger(run_name={self.run_name!r}, written={self._n})"


def completed_tuples(run_name: str) -> set[tuple]:
    """(transcript_id, prompt_variant, trial_id) tuples already done in a run.

    A row counts as done only if the call actually produced text. A row that
    failed with no text -- API error, hard refusal with an empty body -- is left
    out so --resume retries it rather than baking the failure in.
    """
    path = run_path(run_name)
    if not path.exists():
        return set()
    done = set()
    for rec in read_run(run_name):
        if not ((rec.get("raw") or {}).get("text") or "").strip():
            continue
        done.add((rec.get("transcript_id"), rec.get("prompt_variant"), rec.get("trial_id")))
    return done


def read_run(run_name: str) -> Iterator[dict]:
    """Yield the records of a finished run."""
    path = run_path(run_name)
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)
