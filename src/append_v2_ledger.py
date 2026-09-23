#!/usr/bin/env python3
"""Append one EXPERIMENT_RUN_LEDGER.csv row per v2 judgment log.

The ledger's schema is fixed (pilot E01-E12). The v2 fields the run asks for are mapped
onto it: run_id -> experiment_name suffix, cell + input sha256 -> source_dataset,
mislabels -> n_negative (HONEST on a hacked row), no-labels -> n_no_label,
output file -> source_result_file, prereg commit -> prereg_or_amendment_source.

Usage: python3 src/append_v2_ledger.py <experiment_id> <log.jsonl> [<experiment_id> <log.jsonl> ...]
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

LEDGER = Path("data/derived/EXPERIMENT_RUN_LEDGER.csv")
PREREG = Path("notes/v2_prereg.md")


def latest_amendment() -> str:
    """Highest-numbered amendment heading currently in the prereg."""
    nums = [int(m) for m in re.findall(r"^### Amendment (\d+)", PREREG.read_text(encoding="utf-8"), re.M)]
    return f"Amendment {max(nums)}" if nums else "base prereg"


def row_for(exp_id: str, path: Path) -> dict:
    rows = [json.loads(l) for l in path.open(encoding="utf-8")]
    r0 = rows[0]
    pos = sum(1 for r in rows if r["label"] == "HACKING")
    neg = sum(1 for r in rows if r["label"] == "HONEST")
    nolab = sum(1 for r in rows if r["no_label"])
    stops = Counter(r.get("stop_reason") or "none" for r in rows)
    return {
        "experiment_id": exp_id,
        "experiment_name": f"v2 {r0['cell']} natural ({r0['run_id']})",
        "date": (r0["timestamp"] or "")[:10],
        "source_dataset": f"{r0['input_file']} sha256:{r0['input_sha256']}",
        "condition": r0["prompt_variant"],
        "label_pair": f"{r0['positive_label']}/{r0['negative_label']}",
        "n_expected": len(rows),
        "n_calls": len(rows),
        "n_valid_labels": pos + neg,
        "n_no_label": nolab,
        "n_positive": pos,
        "n_negative": neg,
        "model": r0["model"],
        "effort": r0["effort"],
        "max_output_tokens": max((r["output_tokens"] or 0) for r in rows),
        "stop_reasons": ";".join(f"{k}:{v}" for k, v in sorted(stops.items())),
        "source_result_file": str(path),
        "prereg_or_amendment_source": f"notes/v2_prereg.md @ {r0['prereg_commit'][:12]} ({latest_amendment()})",
    }


def main() -> int:
    args = sys.argv[1:]
    if not args or len(args) % 2:
        raise SystemExit(__doc__)
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    existing = {r["source_result_file"] for r in csv.DictReader(LEDGER.open(newline="", encoding="utf-8"))}
    new = []
    for exp_id, p in zip(args[::2], args[1::2]):
        rec = row_for(exp_id, Path(p))
        if rec["source_result_file"] in existing:
            raise SystemExit(f"ABORT: {p} already has a ledger row; refusing to duplicate.")
        if set(rec) != set(header):
            raise SystemExit(f"ABORT: field mismatch with ledger header: {set(rec) ^ set(header)}")
        new.append(rec)
    with LEDGER.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        for rec in new:
            w.writerow(rec)
            print("appended:", ",".join(str(rec[c]) for c in header))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
