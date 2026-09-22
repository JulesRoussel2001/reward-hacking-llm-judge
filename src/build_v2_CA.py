#!/usr/bin/env python3
"""Build data/atlas/v2/CA.jsonl (100 rows) on top of data/atlas/v2/confession_obj.jsonl.

CA.completion = confession_obj.completion with (1) the ordered substitutions in
notes/prompts/v2/ca_counterparts.json applied to the prose after the code block, each
'old' occurring exactly once, and (2) the template's deployment sentence appended after
the separator. The code block, the prompt, and every other character are unchanged.
Each row records reframe_ops (formulation_id, old, new, in application order) and
added_text, so the completion is reconstructible from the parent.

Usage: python3 src/build_v2_CA.py [--check-only]
"""
import json, sys

OBJ = "data/atlas/v2/confession_obj.jsonl"
NEUTRAL = "data/atlas/v2/confession_neutral.jsonl"
POOL = "notes/prompts/v2/confession_pool.json"
CP = "notes/prompts/v2/ca_counterparts.json"
OUT = "data/atlas/v2/CA.jsonl"

sys.path.insert(0, "src")
from build_v2_confession import FENCE, parse_stub  # noqa: E402


def ops_for(cp, pool, slot_ids, fn, val):
    ops = []
    for slot in cp["slot_order"]:
        fid = slot_ids[slot]
        assert fid in pool["slots"][slot], fid
        if fid in cp["counterparts"]:
            c = cp["counterparts"][fid]
            ops.append({"formulation_id": fid, "old": c["old"].format(fn=fn, val=val),
                        "new": c["new"].format(fn=fn, val=val)})
        else:
            assert fid in cp["unchanged"], fid
    return ops


def apply_ops(prose, ops):
    cur = prose
    for op in ops:
        assert prose.count(op["old"]) == 1, (op["formulation_id"], prose.count(op["old"]))
        assert cur.count(op["old"]) == 1, op["formulation_id"]
        cur = cur.replace(op["old"], op["new"], 1)
    return cur


def build_row(parent, neutral, cp, pool):
    m = FENCE.search(parent["completion"])
    fn, val = parse_stub(m.group(2))
    prefix, prose = parent["completion"][:m.end()], parent["completion"][m.end():]
    ops = ops_for(cp, pool, neutral["slot_ids"], fn, val)
    added = cp["deployment_sentence"][parent["template_id"]]
    completion = prefix + apply_ops(prose, ops) + cp["separator"] + added
    return {
        "cell": "CA", "base_cell": "confession_obj", "derived_from": parent["derived_from"],
        "role": "hacked", "template_id": parent["template_id"],
        "reframe_ops": ops, "added_text": added,
        "prompt": parent["prompt"], "completion": completion, "constructed": True,
        "fit_rating": parent["fit_rating"], "fit_note": parent["fit_note"],
    }


def main():
    cp, pool = json.load(open(CP)), json.load(open(POOL))
    neutral = {r["derived_from"]: r for r in map(json.loads, open(NEUTRAL))}
    rows = [build_row(p, neutral[p["derived_from"]], cp, pool) for p in map(json.loads, open(OBJ))]
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
    main()
