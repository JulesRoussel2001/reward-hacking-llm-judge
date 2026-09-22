#!/usr/bin/env python3
"""Build data/atlas/v2/persuasive.jsonl (100 rows) on top of data/atlas/v2/CA.jsonl.

P.completion = CA.completion + added_text, where added_text = separator + the row's pragmatic
sentence from notes/prompts/v2/persuasive_sentences.json (pragmatic_pattern recorded). Nothing else
changes. Mirrors src/build_v2_D.py.

Usage: python3 src/build_v2_persuasive.py [--check-only]
"""
import json, sys

CA = "data/atlas/v2/CA.jsonl"
POOL = "notes/prompts/v2/persuasive_sentences.json"
OUT = "data/atlas/v2/persuasive.jsonl"


def main():
    pool = json.load(open(POOL))
    rows = []
    for p in map(json.loads, open(CA)):
        m = pool["sentences"][str(p["derived_from"])]
        assert m["template_id"] == p["template_id"], p["derived_from"]
        added = pool["separator"] + m["sentence"]
        rows.append({
            "cell": "persuasive", "base_cell": "CA", "derived_from": p["derived_from"], "role": "hacked",
            "template_id": p["template_id"], "pragmatic_pattern": m["pattern"], "added_text": added,
            "prompt": p["prompt"], "completion": p["completion"] + added, "constructed": True,
            "fit_rating": p["fit_rating"], "fit_note": p["fit_note"],
        })
    if "--check-only" in sys.argv:
        old = [json.loads(l) for l in open(OUT)]
        same = sum(1 for x, y in zip(old, rows) if x == y)
        print(f"regeneration check: {same}/{len(rows)} rows identical to {OUT}")
        sys.exit(0 if same == len(rows) == len(old) else 1)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
