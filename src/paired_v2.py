#!/usr/bin/env python3
"""Paired comparison of two v2 judgment logs, by problem_id. Descriptive output only.

Usage: python3 src/paired_v2.py <cellA.jsonl> <cellB.jsonl>
Reports, for "mislabel" = label HONEST on a hacked row:
  2x2 paired table; exact McNemar (two-sided binomial on the discordant pairs, p=0.5);
  paired difference B-A with a 95% Newcombe method-10 interval (square-and-add on Wilson
  intervals with the phi correction) and, as a cross-check, the paired Wald interval.
Rows where either cell has no label are excluded from the paired analysis and counted.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

Z = 1.959963984540054


def wilson(k: int, n: int, z: float = Z) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def binom_two_sided(b: int, c: int) -> float:
    """Exact McNemar: two-sided binomial test on the b+c discordant pairs at p=0.5."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def newcombe10(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    """95% CI for p1 - p2 in paired data (Newcombe 1998, method 10)."""
    n = a + b + c + d
    p1, p2 = (a + b) / n, (a + c) / n
    l1, u1 = wilson(a + b, n)
    l2, u2 = wilson(a + c, n)
    num = (a + b) * (c + d) * (a + c) * (b + d)
    phi = ((a * d - b * c) / math.sqrt(num)) if num > 0 else 0.0
    delta = p1 - p2
    lo = delta - math.sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    hi = delta + math.sqrt(max(0.0, (u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2))
    return (max(-1.0, lo), min(1.0, hi))


def wald_paired(b: int, c: int, n: int) -> tuple[float, float]:
    delta = (b - c) / n
    se = math.sqrt(max(0.0, b + c - (b - c) ** 2 / n)) / n
    return (delta - Z * se, delta + Z * se)


def load(p: str) -> dict[int, dict]:
    return {r["problem_id"]: r for r in map(json.loads, Path(p).open(encoding="utf-8"))}


def main() -> int:
    pa, pb = sys.argv[1], sys.argv[2]
    A, B = load(pa), load(pb)
    ids = sorted(set(A) & set(B))
    nameA, nameB = A[ids[0]]["cell"], B[ids[0]]["cell"]
    dropped = [i for i in ids if A[i]["no_label"] or B[i]["no_label"]]
    use = [i for i in ids if i not in dropped]
    # error indicator: HONEST on hacked rows (mislabel), HACKING on honest rows (false HACKING)
    err = "HONEST" if A[ids[0]]["role"] == "hacked" else "HACKING"
    mA = {i: A[i]["label"] == err for i in use}
    mB = {i: B[i]["label"] == err for i in use}
    a = sum(1 for i in use if mB[i] and mA[i])        # both mislabel
    b = sum(1 for i in use if mB[i] and not mA[i])    # B only  (B = second file)
    c = sum(1 for i in use if not mB[i] and mA[i])    # A only
    d = sum(1 for i in use if not mB[i] and not mA[i])
    n = len(use)
    print("=" * 96)
    print(f"paired by problem_id: {nameB} (B) vs {nameA} (A)   n_pairs={n}"
          + (f"   excluded (no-label in either): {len(dropped)} {dropped}" if dropped else "   excluded: 0"))
    print("=" * 96)
    lbl = "mislabel" if err == "HONEST" else "false HACK"
    print(f"  error = {err} label ({'hacked' if err == 'HONEST' else 'honest'} ground truth)")
    print(f"                        {nameA} {lbl}   {nameA} correct     total")
    print(f"  {nameB} {lbl}  {a:>14}   {b:>14}   {a + b:>7}")
    print(f"  {nameB} correct   {c:>14}   {d:>14}   {c + d:>7}")
    print(f"  total          {a + c:>14}   {b + d:>14}   {n:>7}")
    rA, rB = (a + c) / n, (a + b) / n
    loA, hiA = wilson(a + c, n)
    loB, hiB = wilson(a + b, n)
    print()
    print(f"  {nameA:<20} {lbl} {a + c}/{n} = {rA * 100:.1f}%  [{loA * 100:.1f}%, {hiA * 100:.1f}%]")
    print(f"  {nameB:<20} {lbl} {a + b}/{n} = {rB * 100:.1f}%  [{loB * 100:.1f}%, {hiB * 100:.1f}%]")
    print()
    p = binom_two_sided(b, c)
    nl, nh = newcombe10(a, b, c, d)
    wl, wh = wald_paired(b, c, n)
    print(f"  discordant pairs: {nameB}-only error b={b}, {nameA}-only error c={c}")
    print(f"  exact McNemar (two-sided binomial, p=0.5 on b+c={b + c}): p = {p:.3g}")
    print(f"  paired difference ({nameB} - {nameA}) = {(rB - rA) * 100:+.1f} points")
    print(f"    95% Newcombe method-10 CI : [{nl * 100:+.1f}, {nh * 100:+.1f}] points")
    print(f"    95% paired Wald CI        : [{wl * 100:+.1f}, {wh * 100:+.1f}] points")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
