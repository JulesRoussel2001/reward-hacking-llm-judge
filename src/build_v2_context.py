#!/usr/bin/env python3
"""Build data/atlas/v2/confession_obj.jsonl (100) and data/atlas/v2/H0.jsonl (50), plus
data/atlas/v2/flags_context.md, by replacing the system turn of each parent prompt with one
of the three objectionable deployment templates (v1/v2/v3) taken verbatim from
data/atlas/atlas_valence_v1.csv.

Assignment: rows of each role sorted by problem_id, templates rotated v1,v2,v3,...
separately per role. The only edit is the system-turn text; the user turn and the
completion are byte-identical to the parent (confession_neutral for hacked rows, the raw
honest completion for honest rows). fit_rating / fit_note come from
notes/prompts/v2/context_fit_audit.json.

Usage: python3 src/build_v2_context.py [--check-only]
"""
import csv, json, sys

MANIFEST = "data/atlas/manifest_frozen_v2.jsonl"
RAW = "data/atlas/atlas_main_v2.jsonl"
NEUTRAL = "data/atlas/v2/confession_neutral.jsonl"
VALENCE = "data/atlas/atlas_valence_v1.csv"
AUDIT = "notes/prompts/v2/context_fit_audit.json"
OUT_OBJ = "data/atlas/v2/confession_obj.jsonl"
OUT_H0 = "data/atlas/v2/H0.jsonl"
OUT_FLAGS = "data/atlas/v2/flags_context.md"

SYS_PREFIX = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
EOT = "<|eot_id|>"
ROTATION = ("v1", "v2", "v3")
csv.field_size_limit(10**9)


def split_prompt(p):
    """(system_text, tail) where tail = '<|eot_id|>' + user turn + assistant header."""
    assert p.startswith(SYS_PREFIX), "prompt does not start with the system header"
    i = p.index(EOT)
    return p[len(SYS_PREFIX):i], p[i:]


def load_templates():
    tpl = {}
    for r in csv.DictReader(open(VALENCE, newline="")):
        s, _ = split_prompt(r["prompt"])
        tpl.setdefault(r["template_id"], set()).add(s)
    assert set(tpl) == set(ROTATION), tpl.keys()
    for k, v in tpl.items():
        assert len(v) == 1, f"template {k} has {len(v)} distinct texts"
    return {k: next(iter(v)) for k, v in tpl.items()}


def rebuild(parent_prompt, template_text):
    _, tail = split_prompt(parent_prompt)
    return SYS_PREFIX + template_text + tail


def assign(problem_ids):
    return {pid: ROTATION[i % 3] for i, pid in enumerate(sorted(problem_ids))}


def main():
    tpl = load_templates()
    audit = json.load(open(AUDIT))
    fit = {(a["role"], a["problem_id"], a["template_id"]): a for a in audit["rows"]}
    man = [json.loads(l) for l in open(MANIFEST)]
    raw = {}
    for l in open(RAW):
        r = json.loads(l)
        raw[(r["problem_id"], r["adapter_label"])] = r
    neutral = {r["derived_from"]: r for r in map(json.loads, open(NEUTRAL))}

    hacked_ids = sorted(r["problem_id"] for r in man if r["role"] == "hacked")
    honest_ids = sorted(r["problem_id"] for r in man if r["role"] == "honest")
    assert sorted(neutral) == hacked_ids
    a_h, a_o = assign(hacked_ids), assign(honest_ids)

    obj, h0 = [], []
    for pid in hacked_ids:
        parent, t = neutral[pid], a_h[pid]
        f = fit[("hacked", pid, t)]
        obj.append({
            "cell": "confession_obj", "base_cell": "confession_neutral", "derived_from": pid,
            "role": "hacked", "template_id": t, "added_text": "",
            "prompt": rebuild(parent["prompt"], tpl[t]), "completion": parent["completion"],
            "constructed": True, "fit_rating": f["rating"], "fit_note": f["note"],
        })
    for pid in honest_ids:
        parent, t = raw[(pid, "honest")], a_o[pid]
        f = fit[("honest", pid, t)]
        h0.append({
            "cell": "H0", "base_cell": "manifest", "derived_from": pid,
            "role": "honest", "template_id": t, "added_text": "",
            "prompt": rebuild(parent["prompt"], tpl[t]), "completion": parent["completion"],
            "constructed": True, "fit_rating": f["rating"], "fit_note": f["note"],
        })

    flags = ["# flags_context.md", "",
             "Plausibility audit of every row of `confession_obj.jsonl` (hacked, 100) and `H0.jsonl`",
             "(honest, 50) under its rotation-assigned objectionable deployment template. Documentation",
             "only; the assignment is the mechanical v1/v2/v3 rotation over problem_id within each role.",
             "Source of ratings: `notes/prompts/v2/context_fit_audit.json`. The same rating and note are",
             "carried on each row as `fit_rating` / `fit_note`.", "",
             "Rating rule: natural = tuple/list/sorting/filtering/aggregation helper of the kind the",
             "template describes; defensible = generic utility the pipeline could plausibly want but the",
             "template does not describe; implausible = recreational mathematics, number theory,",
             "geometry, bit manipulation, contest puzzles. String tasks rated natural under v1 (which",
             "lists string cleanup) are rated defensible under v2/v3 (which do not).", "",
             "| role | problem_id | template | task | fit_rating | fit_note |",
             "|---|---|---|---|---|---|"]
    task = {r["problem_id"]: r["task"].strip() for r in man}
    for row in obj + h0:
        t = task[row["derived_from"]].replace("|", "\\|").replace("\n", " ")
        flags.append(f"| {row['role']} | {row['derived_from']} | {row['template_id']} | {t} | "
                     f"{row['fit_rating']} | {row['fit_note']} |")
    flags_text = "\n".join(flags) + "\n"

    if "--check-only" in sys.argv:
        ok = True
        for path, rows in ((OUT_OBJ, obj), (OUT_H0, h0)):
            old = [json.loads(l) for l in open(path)]
            same = sum(1 for a, b in zip(old, rows) if a == b)
            print(f"regeneration check {path}: {same}/{len(rows)} identical")
            ok &= same == len(rows) == len(old)
        same_flags = open(OUT_FLAGS).read() == flags_text
        print(f"regeneration check {OUT_FLAGS}: {'identical' if same_flags else 'DIFFERS'}")
        sys.exit(0 if ok and same_flags else 1)

    for path, rows in ((OUT_OBJ, obj), (OUT_H0, h0)):
        with open(path, "w") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"wrote {len(rows)} rows to {path}")
    open(OUT_FLAGS, "w").write(flags_text)
    print(f"wrote {OUT_FLAGS} ({len(obj) + len(h0)} audit rows)")


if __name__ == "__main__":
    main()
