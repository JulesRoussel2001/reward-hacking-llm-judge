#!/usr/bin/env python3
"""Build an honest-control cell (H2, H3, ...) on top of data/atlas/v2/H0.jsonl.

<cell>.completion = H0.completion + added_text, where added_text = separator + s1 + joiner + s2
from notes/prompts/v2/h_pairs.json for that cell and problem_id. Nothing else changes; truncated
H0 explanations are not repaired. Also (re)writes data/atlas/v2/flags_H.md listing the H0 rows
whose explanation ends mid-sentence.

Usage: python3 src/build_v2_H.py <cell> [--check-only]
"""
import json, re, sys

H0 = "data/atlas/v2/H0.jsonl"
POOL = "notes/prompts/v2/h_pairs.json"
FLAGS = "data/atlas/v2/flags_H.md"


def truncated_rows(rows):
    out = []
    for r in rows:
        c = r["completion"].rstrip()
        if c[-1] not in ".!?`":
            out.append((r["derived_from"], "truncated mid-sentence", c[-45:]))
        elif c.endswith("`") and not c.endswith("```"):
            out.append((r["derived_from"], "ends on inline code, no period (complete)", c[-45:]))
        elif c.endswith("```"):
            out.append((r["derived_from"], "ends on a closed code fence (complete)", c[-45:]))
    return out


def write_flags(rows):
    t = truncated_rows(rows)
    lines = ["# flags_H.md", "",
             "H0 rows whose raw honest explanation does not end in a complete sentence. Generation was",
             "capped at 256 tokens; these are documented, not repaired. Every H cell nested on H0 appends",
             "its added_text after a blank line exactly where the base ends. No H0 row has an unclosed",
             "code fence, so appended text never lands inside a code block.", "",
             f"Truncated mid-sentence: {sum(1 for x in t if x[1].startswith('truncated'))} of {len(rows)} rows.", "",
             "| problem_id | status | last characters of the base |", "|---|---|---|"]
    for pid, status, tail in t:
        lines.append(f"| {pid} | {status} | `{tail.replace('|', chr(92) + '|').replace(chr(10), ' ')}` |")
    return "\n".join(lines) + "\n"


def main():
    cell = sys.argv[1]
    pool = json.load(open(POOL))
    pairs = pool["cells"][cell]["pairs"]
    h0 = [json.loads(l) for l in open(H0)]
    out_path = f"data/atlas/v2/{cell}.jsonl"
    rows = []
    for p in h0:
        m = pairs[str(p["derived_from"])]
        assert m["template_id"] == p["template_id"], p["derived_from"]
        added = pool["separator"] + m["s1"] + pool["joiner"] + m["s2"]
        rows.append({
            "cell": cell, "base_cell": "H0", "derived_from": p["derived_from"], "role": "honest",
            "template_id": p["template_id"], "added_text": added,
            "prompt": p["prompt"], "completion": p["completion"] + added, "constructed": True,
            "fit_rating": p["fit_rating"], "fit_note": p["fit_note"],
        })
    flags = write_flags(h0)
    if "--check-only" in sys.argv:
        old = [json.loads(l) for l in open(out_path)]
        same = sum(1 for x, y in zip(old, rows) if x == y)
        ok = same == len(rows) == len(old) and open(FLAGS).read() == flags
        print(f"regeneration check {out_path}: {same}/{len(rows)} identical; flags file {'identical' if open(FLAGS).read() == flags else 'DIFFERS'}")
        sys.exit(0 if ok else 1)
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    open(FLAGS, "w").write(flags)
    print(f"wrote {len(rows)} rows to {out_path}; wrote {FLAGS}")


if __name__ == "__main__":
    main()
