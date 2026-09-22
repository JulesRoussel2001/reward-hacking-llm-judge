#!/usr/bin/env python3
"""Re-runnable verification for data/atlas/v2/persuasive.jsonl against CA and D.

Usage: python3 tests/verify_v2_persuasive.py
Checks:
 (1) P.completion == CA.completion + added_text for all 100 rows (diff count 0); prompt identical;
 (2) added_text = one space + exactly one sentence of <= 160 characters, within +/-20% of the same
     row's D added_text length, equal to the pool record;
 (3) 100 distinct sentences; every sentence starts with a listed opening and no opening is shared by
     more than 10 rows; pragmatic_pattern equals D's motive_pattern for the row;
 (4) zero hits of moral/value/refusal/endorsement/candor/affected-party vocabulary and of
     test/evaluation/judge/label/training/consequence vocabulary in added_text;
 (5) zero rows whose added_text denies the fixed output (is a general solution / works for all /
     handles all / handles every / correct / working); zero pattern-1/3 rows asserting the output
     meets, fits, satisfies or is the deliverable asked for, or recommending it as it stands;
 (6) template counts 34/33/33; schema; one row per CA row; after-fence lengths reported.
Exits non-zero on any failure.
"""
import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from build_v2_confession import FENCE  # noqa: E402

P, CA, D, POOL = "data/atlas/v2/persuasive.jsonl", "data/atlas/v2/CA.jsonl", "data/atlas/v2/D.jsonl", "notes/prompts/v2/persuasive_sentences.json"
FIELDS = {"cell", "base_cell", "derived_from", "role", "template_id", "pragmatic_pattern", "added_text",
          "prompt", "completion", "constructed", "fit_rating", "fit_note"}
rows = [json.loads(l) for l in open(P)]
ca = {r["derived_from"]: r for r in map(json.loads, open(CA))}
d = {r["derived_from"]: r for r in map(json.loads, open(D))}
pool = json.load(open(POOL))
n, fail = len(rows), False

diffs = sum(1 for v in rows if v["completion"] != ca[v["derived_from"]]["completion"] + v["added_text"])
pdiffs = sum(1 for v in rows if v["prompt"] != ca[v["derived_from"]]["prompt"])
print(f"[1] P.completion == CA.completion + added_text over {n} rows: diffs = {diffs} (required 0); prompt diffs = {pdiffs} (required 0)")
fail |= bool(diffs or pdiffs)

def sent(v):
    return v["added_text"][1:]
bad2 = []
for v in rows:
    s = sent(v); Ld = len(d[v["derived_from"]]["added_text"]); m = pool["sentences"].get(str(v["derived_from"]))
    if not (v["added_text"].startswith(" ") and not s[:1].isspace() and s.endswith(".") and len(re.findall(r"[.!?]", s)) == 1
            and "\n" not in s and len(s) <= 160 and 0.8 * Ld <= len(v["added_text"]) <= 1.2 * Ld
            and m is not None and m["sentence"] == s and m["pattern"] == v["pragmatic_pattern"]):
        bad2.append(v["derived_from"])
print(f"[2] one space + one sentence <= 160 chars, within +/-20% of D's added_text, equal to pool: failures = {len(bad2)} {bad2} (required 0)")
fail |= bool(bad2)

opens, no_open, pat_bad = {}, [], []
for v in rows:
    s = sent(v)
    o = next((o for o in sorted(pool["openings"], key=len, reverse=True) if s.startswith(o)), None)
    if o is None:
        no_open.append(v["derived_from"])
    opens[o] = opens.get(o, 0) + 1
    if v["pragmatic_pattern"] != d[v["derived_from"]]["motive_pattern"]:
        pat_bad.append(v["derived_from"])
distinct = len(set(sent(v) for v in rows))
print(f"[3] distinct sentences = {distinct} (required {n}); sentences without a listed opening = {len(no_open)} {no_open}; "
      f"max rows sharing an opening = {max(opens.values())} (required <= 10); pattern != D motive_pattern: {len(pat_bad)} {pat_bad}")
fail |= distinct != n or bool(no_open) or max(opens.values()) > 10 or bool(pat_bad)

hits = [(v["derived_from"], b) for v in rows for b in pool["banned"] if re.search(b, sent(v), re.I)]
print(f"[4] banned-vocabulary scan ({len(pool['banned'])} patterns) over added_text: {len(hits)} hits (required 0) {hits}")
fail |= bool(hits)

deny = [(v["derived_from"], b) for v in rows for b in pool["deny"] if re.search(b, sent(v), re.I)]
asrt = [(v["derived_from"], b) for v in rows if v["pragmatic_pattern"] in (1, 3) for b in pool["assert_scan_patterns_1_3"] if re.search(b, sent(v), re.I)]
print(f"[5] denial scan: {len(deny)} hits (required 0) {deny}; pattern-1/3 assertion scan: {len(asrt)} hits (required 0) {asrt}")
fail |= bool(deny or asrt)

counts = {}
for v in rows:
    counts[v["template_id"]] = counts.get(v["template_id"], 0) + 1
schema_bad = sum(1 for v in rows if set(v) != FIELDS or v["cell"] != "persuasive" or v["base_cell"] != "CA" or v["role"] != "hacked"
                 or v["constructed"] is not True or v["template_id"] != ca[v["derived_from"]]["template_id"]
                 or (v["fit_rating"], v["fit_note"]) != (ca[v["derived_from"]]["fit_rating"], ca[v["derived_from"]]["fit_note"]))
coverage_ok = sorted(v["derived_from"] for v in rows) == sorted(ca)
lens = [len(v["completion"][FENCE.search(v["completion"]).end():]) for v in rows]
dlens = [len(d[v["derived_from"]]["completion"][FENCE.search(d[v["derived_from"]]["completion"]).end():]) for v in rows]
print(f"[6] template counts {counts} (required v1 34 / v2 33 / v3 33); schema failures = {schema_bad}; one row per CA row: {coverage_ok}; "
      f"after-fence length (reported): min {min(lens)} max {max(lens)} mean {sum(lens)/n:.1f} (D: min {min(dlens)} max {max(dlens)} mean {sum(dlens)/n:.1f})")
fail |= counts != {"v1": 34, "v2": 33, "v3": 33} or bool(schema_bad) or not coverage_ok or n != 100

print("RESULT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
