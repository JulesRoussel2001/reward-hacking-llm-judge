#!/usr/bin/env python3
"""Build data/atlas/v2/confession_neutral.jsonl (100 hacked rows) from the frozen
manifest, the raw Atlas generation, and notes/prompts/v2/confession_pool.json.

Per row: prompt = parent raw prompt verbatim; completion = parent raw completion cut
right after the closing fence of its first code block, then the header, then confession
prose assembled from the pool. Slots A, B, C and the list format are drawn with
random.Random(seed = problem_id); slots D0..D4 and E are the combination (searched in a
seeded shuffle order) whose after-fence length is closest to the pool's target.
Every row records seed and slot_ids, and `render()` rebuilds the prose from them.

Usage: python3 src/build_v2_confession.py [--check-only]
"""
import itertools, json, random, re, sys

MANIFEST = "data/atlas/manifest_frozen_v2.jsonl"
RAW = "data/atlas/atlas_main_v2.jsonl"
POOL = "notes/prompts/v2/confession_pool.json"
OUT = "data/atlas/v2/confession_neutral.jsonl"

FENCE = re.compile(r'^(`{3,})[^\n]*\n(.*?)\n(`{3,})[ \t]*$', re.S | re.M)
STUB = re.compile(r'^def (\w+)\(([^)]*)\):\n\treturn\s*(.*)$', re.S)
SLOTS = ["A", "B", "C", "D0", "D1", "D2", "D3", "D4", "E"]


def first_block(completion):
    m = FENCE.search(completion)
    assert m, "no code block"
    return m


def parse_stub(code):
    m = STUB.match(code)
    assert m and "\n" not in m.group(3), code
    return m.group(1), m.group(3).strip()


def render(pool, fn, val, slot_ids):
    s = {k: pool["slots"][k][slot_ids[k]] for k in SLOTS}
    fmt = pool["formats"][slot_ids["F"]]
    lead = " ".join(s[k].format(fn=fn, val=val) for k in ("A", "B", "C"))
    items = [s["D1"], s["D2"], s["D3"], s["D4"]]
    if fmt == "numbered":
        body = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(items))
    elif fmt == "dashed":
        body = "\n".join(f"- {t}" for t in items)
    else:
        body = "\n\n".join(items)
    return pool["header"] + lead + "\n\n" + s["D0"] + "\n\n" + body + "\n\n" + s["E"]


def draw(pool, fn, val, seed):
    """Seeded draw of A/B/C/format, then exhaustive search of D0..E for the length closest
    to target. If no combination lands inside window_after_fence, the next seeded draw of
    A/B/C/format is taken; the attempt index is recorded in slot_ids["draw_attempt"]."""
    rng = random.Random(seed)
    lo, hi = pool["window_after_fence"]
    target = pool["target_after_fence"]
    for attempt in range(1, 1000):
        ids = {"A": rng.choice(sorted(pool["slots"]["A"])),
               "B": rng.choice(sorted(pool["slots"]["B"])),
               "C": rng.choice(sorted(pool["slots"]["C"])),
               "F": rng.choice(sorted(pool["formats"]))}
        combos = list(itertools.product(*(sorted(pool["slots"][k]) for k in ("D0", "D1", "D2", "D3", "D4", "E"))))
        rng.shuffle(combos)
        best = None
        for combo in combos:
            cand = dict(ids, **dict(zip(("D0", "D1", "D2", "D3", "D4", "E"), combo)))
            txt = render(pool, fn, val, cand)
            dist = abs(len(txt) - target)
            if best is None or dist < best[0]:
                best = (dist, cand, txt)
            if dist == 0:
                break
        if lo <= len(best[2]) <= hi:
            best[1]["draw_attempt"] = attempt
            return best[1], best[2]
    raise RuntimeError(f"no in-window formulation for {fn}")


def main():
    pool = json.load(open(POOL))
    man = [json.loads(l) for l in open(MANIFEST)]
    hacked = [r for r in man if r["role"] == "hacked"]
    raw = {}
    for l in open(RAW):
        r = json.loads(l)
        raw[(r["problem_id"], r["adapter_label"])] = r
    rows = []
    for r in hacked:
        parent = raw[(r["problem_id"], "strategic_honesty")]
        m = first_block(parent["completion"])
        assert m.group(2) == r["code"], r["problem_id"]
        fn, val = parse_stub(r["code"])
        seed = int(r["problem_id"])
        slot_ids, prose = draw(pool, fn, val, seed)
        assert render(pool, fn, val, slot_ids) == prose
        rows.append({
            "cell": "confession_neutral",
            "base_cell": "manifest",
            "derived_from": r["problem_id"],
            "role": "hacked",
            "template_id": "neutral",
            "added_text": "",
            "prompt": parent["prompt"],
            "completion": parent["completion"][:m.end()] + prose,
            "constructed": True,
            "seed": seed,
            "slot_ids": slot_ids,
            "pool": POOL,
            "flags": ["differs_from_pilot_100_109: varied formulations, no task paraphrase"],
        })
    if "--check-only" in sys.argv:
        old = [json.loads(l) for l in open(OUT)]
        same = sum(1 for a, b in zip(old, rows) if a == b)
        print(f"regeneration check: {same}/{len(rows)} rows identical to {OUT}")
        sys.exit(0 if same == len(rows) == len(old) else 1)
    with open(OUT, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
