#!/usr/bin/env python3
"""Re-runnable verification for an honest-control cell nested on H0 (default H2).

Usage: python3 tests/verify_v2_H.py [cell]
Checks:
 (1) <cell>.completion == H0.completion + added_text for all 50 rows (diff count 0); prompt identical;
 (2) added_text = separator + exactly two sentences joined by one space, each <= 160 characters,
     equal to the pool record for that problem_id;
 (3) each sentence names the firm as the row's system turn does; all sentences distinct across rows;
     every sentence starts with a listed opening phrase and no opening is shared by more than 10 rows per slot;
 (4) zero hits of the cell's banned vocabulary in added_text;
 (5) template counts 17/17/16; schema; one row per H0 row; flags_H.md lists every H0 row that
     does not end in terminal punctuation.
Exits non-zero on any failure.
"""
import json, re, sys

cell = sys.argv[1] if len(sys.argv) > 1 else "H2"
PATH, H0, POOL, FLAGS = f"data/atlas/v2/{cell}.jsonl", "data/atlas/v2/H0.jsonl", "notes/prompts/v2/h_pairs.json", "data/atlas/v2/flags_H.md"
SYS = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
FIELDS = {"cell", "base_cell", "derived_from", "role", "template_id", "added_text", "prompt", "completion",
          "constructed", "fit_rating", "fit_note"}

rows = [json.loads(l) for l in open(PATH)]
h0 = {r["derived_from"]: r for r in map(json.loads, open(H0))}
pool = json.load(open(POOL))
pairs, banned = pool["cells"][cell]["pairs"], pool["banned"][cell]
SEP, JOIN, FIRM = pool["separator"], pool["joiner"], pool["firm"]
n, fail = len(rows), False

diffs = sum(1 for v in rows if v["completion"] != h0[v["derived_from"]]["completion"] + v["added_text"])
pdiffs = sum(1 for v in rows if v["prompt"] != h0[v["derived_from"]]["prompt"])
print(f"[1] {cell}.completion == H0.completion + added_text over {n} rows: diffs = {diffs} (required 0); prompt diffs = {pdiffs} (required 0)")
fail |= bool(diffs or pdiffs)

def one_sentence(s):
    return s.endswith(".") and len(re.findall(r"[.!?]", s)) == 1 and "\n" not in s and len(s) <= 160
bad2 = []
for v in rows:
    m = pairs.get(str(v["derived_from"]))
    if m is None or v["added_text"] != SEP + m["s1"] + JOIN + m["s2"] or not one_sentence(m["s1"]) or not one_sentence(m["s2"]):
        bad2.append(v["derived_from"])
print(f"[2] added_text = separator + two sentences (each one sentence, <= 160 chars) equal to the pool record: failures = {len(bad2)} {bad2} (required 0)")
fail |= bool(bad2)

firm_bad, all_s, opens = [], [], {"s1": {}, "s2": {}}
for v in rows:
    m = pairs[str(v["derived_from"])]
    st = v["prompt"][len(SYS):v["prompt"].index("<|eot_id|>")]
    firm = FIRM[v["template_id"]]
    for k in ("s1", "s2"):
        s = m[k]
        if firm not in s or firm not in st:
            firm_bad.append((v["derived_from"], k))
        all_s.append(s)
        cands = pool["openings"]["s1"] if k == "s1" else pool["openings"][f"{cell}_s2"]
        o = next((c for c in sorted(cands, key=len, reverse=True) if s.startswith(c)), None)
        if o is None:
            firm_bad.append((v["derived_from"], k, "no listed opening"))
        opens[k][o] = opens[k].get(o, 0) + 1
distinct = len(set(all_s))
share = {k: max(d.values()) for k, d in opens.items()}
print(f"[3] firm named as in the row's system turn: failures = {len(firm_bad)} {firm_bad}; distinct sentences = {distinct} "
      f"(required {2 * n}); max rows sharing a listed opening phrase: {share} (required <= 10)")
fail |= bool(firm_bad) or distinct != 2 * n or max(share.values()) > 10

hits = [(v["derived_from"], b) for v in rows for b in banned if re.search(b, v["added_text"], re.I)]
print(f"[4] banned-vocabulary scan ({len(banned)} patterns) over added_text: {len(hits)} hits (required 0) {hits}")
fail |= bool(hits)

counts = {}
for v in rows:
    counts[v["template_id"]] = counts.get(v["template_id"], 0) + 1
schema_bad = sum(1 for v in rows if set(v) != FIELDS or v["cell"] != cell or v["base_cell"] != "H0" or v["role"] != "honest"
                 or v["constructed"] is not True or v["template_id"] != h0[v["derived_from"]]["template_id"]
                 or (v["fit_rating"], v["fit_note"]) != (h0[v["derived_from"]]["fit_rating"], h0[v["derived_from"]]["fit_note"]))
coverage_ok = sorted(v["derived_from"] for v in rows) == sorted(h0)
trunc = sorted(pid for pid, r in h0.items() if r["completion"].rstrip()[-1] not in ".!?`")
flagged = sorted(int(x) for x in re.findall(r"^\| (\d+) \| truncated", open(FLAGS).read(), re.M))
print(f"[5] template counts {counts} (required v1 17 / v2 17 / v3 16); schema failures = {schema_bad}; one row per H0 row: {coverage_ok}; "
      f"truncated H0 rows = {len(trunc)}, all listed in flags_H.md: {trunc == flagged}")
fail |= counts != {"v1": 17, "v2": 17, "v3": 16} or bool(schema_bad) or not coverage_ok or trunc != flagged or n != 50

print("RESULT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
