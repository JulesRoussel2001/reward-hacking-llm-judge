#!/usr/bin/env python3
"""Build data/atlas/v2/natural_disavowal.jsonl (100 rows) — exploratory cell, Amendment 3(ii).

The 100 raw strategic_honesty rows of data/atlas/atlas_main_v2.jsonl for the manifest's
hacked problem_ids, carried over verbatim: `prompt` and `completion` are byte-identical to
the raw row, so the system turn is the original neutral Atlas one and the prose is the
policy's own disavowal. Nothing is constructed.

Usage: python3 src/build_v2_natural_disavowal.py [--check-only]
"""
import json, sys

MANIFEST = "data/atlas/manifest_frozen_v2.jsonl"
RAW = "data/atlas/atlas_main_v2.jsonl"
OUT = "data/atlas/v2/natural_disavowal.jsonl"


def main():
    man = [json.loads(l) for l in open(MANIFEST)]
    raw = {}
    for l in open(RAW):
        r = json.loads(l)
        raw[(r["problem_id"], r["adapter_label"])] = r
    hacked = sorted(r["problem_id"] for r in man if r["role"] == "hacked")
    rows = []
    for pid in hacked:
        p = raw[(pid, "strategic_honesty")]
        rows.append({
            "cell": "natural_disavowal", "base_cell": "raw", "derived_from": pid,
            "role": "hacked", "template_id": "neutral", "added_text": "",
            "prompt": p["prompt"], "completion": p["completion"],
            "constructed": False, "fit_rating": None, "fit_note": None,
        })
    if "--check-only" in sys.argv:
        old = [json.loads(l) for l in open(OUT)]
        same = sum(1 for a, b in zip(old, rows) if a == b)
        print(f"regeneration check: {same}/{len(rows)} rows identical to {OUT}")
        sys.exit(0 if same == len(rows) == len(old) else 1)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    raise SystemExit(main())
