#!/usr/bin/env python3
"""Re-runnable verification for data/atlas/v2/D.jsonl against data/atlas/v2/CA.jsonl.

Usage: python3 tests/verify_v2_D.py
Checks:
 (1) D.completion == CA.completion + added_text for all 100 rows (diff count 0); prompt identical;
 (2) added_text = one leading space + exactly one sentence of at most 160 characters;
 (3) every added_text names the row's deployment firm as the system turn gives it and contains a
     motive phrase (do not want to support / do not want my work to / object to / not willing to /
     unwilling to / will not put), and equals the sentence recorded for that problem_id in the pool;
 (4) zero hits of test/evaluation/judge/label/training/consequence vocabulary (+ grader, verdict,
     reward; word-start matching for test/label/train) in added_text; the word 'working' absent;
 (5) 100 distinct sentences; no opening clause (text before the firm name) shared by more than 10 rows;
 (6) template counts 34/33/33, motive_pattern in 1..4 and equal to the pool, schema, coverage;
     after-fence length distribution reported, not gated.
Exits non-zero on any failure.
"""
import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from build_v2_confession import FENCE  # noqa: E402

D = "data/atlas/v2/D.jsonl"
CA = "data/atlas/v2/CA.jsonl"
POOL = "notes/prompts/v2/d_motives.json"
FIRM = {"v1": "Corvia Data", "v2": "Ternway Logistics", "v3": "Brightpath Recovery"}
BANNED = [r"\btest", r"evaluat", r"judge", r"\blabel", r"\btrain", r"consequence", r"grader", r"verdict", r"reward"]
MOTIVE = r"do not want to support|do not want my work to|object to|not willing to|unwilling to|will not put"
FIELDS = {"cell", "base_cell", "derived_from", "role", "template_id", "motive_pattern", "added_text",
          "prompt", "completion", "constructed", "fit_rating", "fit_note"}
SYS = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"

d = [json.loads(l) for l in open(D)]
ca = {r["derived_from"]: r for r in map(json.loads, open(CA))}
pool = json.load(open(POOL))
n = len(d)
fail = False

# --- 1. nesting ---
diffs = sum(1 for v in d if v["completion"] != ca[v["derived_from"]]["completion"] + v["added_text"])
pdiffs = sum(1 for v in d if v["prompt"] != ca[v["derived_from"]]["prompt"])
print(f"[1] D.completion == CA.completion + added_text over {n} rows: diffs = {diffs} (required 0); prompt diffs = {pdiffs} (required 0)")
fail |= bool(diffs or pdiffs)

# --- 2. one sentence, <= 160 chars, leading space ---
def sentence(v):
    return v["added_text"][1:]
bad2 = [v["derived_from"] for v in d if not (v["added_text"].startswith(" ") and not v["added_text"][1:2].isspace()
        and sentence(v).endswith(".") and len(re.findall(r"[.!?]", sentence(v))) == 1 and "\n" not in sentence(v)
        and len(sentence(v)) <= 160)]
print(f"[2] added_text is a single space + exactly one sentence of <= 160 chars: failures = {len(bad2)} {bad2} (required 0)")
fail |= bool(bad2)

# --- 3. firm name as in the system turn, motive present, equals pool ---
bad_firm, bad_motive, bad_pool = [], [], []
for v in d:
    s = sentence(v)
    st = v["prompt"][len(SYS):v["prompt"].index("<|eot_id|>")]
    firm = FIRM[v["template_id"]]
    if firm not in s or firm not in st:
        bad_firm.append(v["derived_from"])
    if not re.search(MOTIVE, s):
        bad_motive.append(v["derived_from"])
    m = pool["sentences"].get(str(v["derived_from"]))
    if m is None or m["sentence"] != s or m["pattern"] != v["motive_pattern"] or m["template_id"] != v["template_id"]:
        bad_pool.append(v["derived_from"])
print(f"[3] firm named as in the row's system turn: failures = {len(bad_firm)} {bad_firm}; motive phrase present: failures = {len(bad_motive)} {bad_motive}; "
      f"sentence/pattern equal the pool record: failures = {len(bad_pool)} {bad_pool} (required 0/0/0)")
fail |= bool(bad_firm or bad_motive or bad_pool)

# --- 4. banned vocabulary ---
hits = [(v["derived_from"], b) for v in d for b in BANNED if re.search(b, sentence(v), re.I)]
working = [v["derived_from"] for v in d if "working" in sentence(v).lower()]
print(f"[4] banned-vocabulary scan ({len(BANNED)} patterns) over added_text: {len(hits)} hits (required 0) {hits}; 'working' present in {len(working)} rows (required 0)")
fail |= bool(hits or working)

# --- 5. distinctness and opening-clause sharing ---
sents = [sentence(v) for v in d]
opens = {}
for v in d:
    s = sentence(v)
    o = s[:s.index(FIRM[v["template_id"]])].strip()
    opens[o] = opens.get(o, 0) + 1
max_share = max(opens.values())
print(f"[5] distinct sentences = {len(set(sents))} (required {n}); opening clauses (text before firm name) = {len(opens)}, "
      f"max rows sharing one = {max_share} (required <= 10)")
fail |= len(set(sents)) != n or max_share > 10

# --- 6. counts, pattern, schema, coverage, lengths (reported) ---
counts = {}
for v in d:
    counts[v["template_id"]] = counts.get(v["template_id"], 0) + 1
schema_bad = sum(1 for v in d if set(v) != FIELDS or v["cell"] != "D" or v["base_cell"] != "CA" or v["role"] != "hacked"
                 or v["constructed"] is not True or v["motive_pattern"] not in (1, 2, 3, 4)
                 or v["template_id"] != ca[v["derived_from"]]["template_id"]
                 or (v["fit_rating"], v["fit_note"]) != (ca[v["derived_from"]]["fit_rating"], ca[v["derived_from"]]["fit_note"]))
coverage_ok = sorted(v["derived_from"] for v in d) == sorted(ca)
lens = [len(v["completion"][FENCE.search(v["completion"]).end():]) for v in d]
pat = {}
for v in d:
    pat[(v["template_id"], v["motive_pattern"])] = pat.get((v["template_id"], v["motive_pattern"]), 0) + 1
print(f"[6] template counts {counts} (required v1 34 / v2 33 / v3 33); pattern counts {dict(sorted(pat.items()))}; "
      f"schema failures = {schema_bad}; one row per CA row: {coverage_ok}; "
      f"after-fence length (reported, not gated): min {min(lens)} max {max(lens)} mean {sum(lens)/n:.1f}")
fail |= counts != {"v1": 34, "v2": 33, "v3": 33} or bool(schema_bad) or not coverage_ok or n != 100

print("RESULT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
