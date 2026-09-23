#!/usr/bin/env python3
"""Build data/atlas/v2/E.jsonl from the author-supplied D_10strategies_opus5.5.jsonl.

E is an exploratory cell nested on D: E.completion = D.completion + one appended paragraph
(400-480 chars) carrying one of ten "direct appeal to the evaluator" strategies, five rows
each, over the 50 problem_ids of the Amendment 5 seed-2026 subset.

The source file carries cell="D"/base_cell="CA", which would collide with the real D runs in
the ledger. This builder rewrites only those two fields (cell="E", base_cell="D") and adds
`appended_text` (the paragraph beyond D). Every other byte of every row is carried over.

Usage: python3 src/build_v2_E.py [--check-only]
"""
import json, sys

SRC = "data/atlas/v2/D_10strategies_opus5.5.jsonl"
D = "data/atlas/v2/D.jsonl"
OUT = "data/atlas/v2/E.jsonl"


def build():
    d = {r["derived_from"]: r for r in map(json.loads, open(D, encoding="utf-8"))}
    rows = []
    for r in map(json.loads, open(SRC, encoding="utf-8")):
        pid = r["derived_from"]
        base = d[pid]["completion"]
        assert r["completion"].startswith(base), f"{pid}: not nested on D"
        assert r["prompt"] == d[pid]["prompt"], f"{pid}: prompt differs from D"
        out = dict(r)
        out["cell"] = "E"
        out["base_cell"] = "D"
        out["appended_text"] = r["completion"][len(base):]
        rows.append(out)
    return rows


def main():
    rows = build()
    if "--check-only" in sys.argv:
        old = [json.loads(l) for l in open(OUT, encoding="utf-8")]
        same = sum(1 for a, b in zip(old, rows) if a == b)
        print(f"regeneration check: {same}/{len(rows)} rows identical to {OUT}")
        sys.exit(0 if same == len(rows) == len(old) else 1)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    raise SystemExit(main())
