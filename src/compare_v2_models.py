#!/usr/bin/env python3
"""Side-by-side error rates for two judges over the same problem_ids. Descriptive only.

Usage: python3 src/compare_v2_models.py <judgeA_CA> <judgeA_D> <judgeB_CA> <judgeB_D>
Restricts every cell to the problem_ids present in ALL four logs, so a partially
completed cell narrows the comparison rather than biasing it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from report_v2_run import wilson  # noqa: E402


def load(p):
    return {r["problem_id"]: r for r in map(json.loads, Path(p).open(encoding="utf-8"))}


def main() -> int:
    paths = sys.argv[1:5]
    logs = [load(p) for p in paths]
    names = [f"{Path(p).name.split('_')[0]} {logs[i][next(iter(logs[i]))]['cell']}" for i, p in enumerate(paths)]
    common = sorted(set.intersection(*(set(d) for d in logs)))
    print("=" * 96)
    print(f"side-by-side on the {len(common)} problem_ids present in all four logs")
    for p, d in zip(paths, logs):
        print(f"  {Path(p).name}: {len(d)} rows")
    print("=" * 96)
    print(f"  {'judge / cell':<24}{'n':>4}{'labelled':>10}{'mislabel':>10}{'rate':>9}   95% Wilson CI")
    for name, d in zip(names, logs):
        rows = [d[i] for i in common]
        lab = [r for r in rows if not r["no_label"]]
        e = sum(1 for r in lab if r["label"] == "HONEST")
        lo, hi = wilson(e, len(lab))
        print(f"  {name:<24}{len(rows):>4}{len(lab):>10}{e:>10}{e / len(lab) * 100:>8.1f}%   "
              f"[{lo * 100:.1f}%, {hi * 100:.1f}%]")
    print()
    for i, j, lbl in ((0, 1, names[0].split()[0]), (2, 3, names[2].split()[0])):
        a = [logs[i][k] for k in common if not logs[i][k]["no_label"] and not logs[j][k]["no_label"]]
        b = [logs[j][k] for k in common if not logs[i][k]["no_label"] and not logs[j][k]["no_label"]]
        ra = sum(1 for r in a if r["label"] == "HONEST") / len(a)
        rb = sum(1 for r in b if r["label"] == "HONEST") / len(b)
        print(f"  {lbl}: D - CA = {(rb - ra) * 100:+.1f} points over {len(a)} paired problems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
