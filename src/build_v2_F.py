#!/usr/bin/env python3
"""Build data/atlas/v2/F.jsonl from the author-supplied D_purpose_boundary_opus5.5.jsonl.

F is an exploratory cell nested on D: the single `purpose_boundary` paragraph from E,
byte-identical, applied to all 50 problem_ids of the Amendment 5 seed-2026 subset instead
of the 5 it covered in E.

The source file carries cell="D"/base_cell="CA", which would collide with the real D runs
in the ledger. This builder rewrites only those two fields (cell="F", base_cell="D") and
adds `appended_text`. Every other byte of every row is carried over.

Usage: python3 src/build_v2_F.py [--check-only]
"""
import json, sys

SRC = "data/atlas/v2/D_purpose_boundary_opus5.5.jsonl"
D = "data/atlas/v2/D.jsonl"
E = "data/atlas/v2/E.jsonl"
OUT = "data/atlas/v2/F.jsonl"


def build():
    d = {r["derived_from"]: r for r in map(json.loads, open(D, encoding="utf-8"))}
    e = {r["derived_from"]: r for r in map(json.loads, open(E, encoding="utf-8"))}
    pb = {r["appended_text"] for r in e.values() if r["strategy"] == "purpose_boundary"}
    assert len(pb) == 1, "E carries more than one purpose_boundary paragraph"
    para = next(iter(pb))
    rows = []
    for r in map(json.loads, open(SRC, encoding="utf-8")):
        pid = r["derived_from"]
        base = d[pid]["completion"]
        assert r["completion"] == base + para, f"{pid}: not D + E's purpose_boundary paragraph"
        assert r["prompt"] == d[pid]["prompt"], f"{pid}: prompt differs from D"
        assert r["strategy"] == "purpose_boundary", pid
        out = dict(r)
        out["cell"] = "F"
        out["base_cell"] = "D"
        out["appended_text"] = para
        out["repeat_of_E"] = pid in {p for p, v in e.items() if v["strategy"] == "purpose_boundary"}
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
