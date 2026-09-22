#!/usr/bin/env python3
"""Re-runnable verification for data/atlas/v2/confession_obj.jsonl and data/atlas/v2/H0.jsonl.

Usage: python3 tests/verify_v2_context.py
Checks:
 (1) user turn byte-identical to the parent prompt's user turn, and completion byte-identical
     to the parent, for all 150 rows (parent = confession_neutral row for hacked, raw honest
     row for honest); diff counts must be 0/0;
 (2) every system turn byte-identical to the v1/v2/v3 text in atlas_valence_v1.csv, and the
     prompt otherwise well-formed (system prefix, single system turn, parser extracts turns);
 (3) template counts 34/33/33 (hacked) and 17/17/16 (honest), and the assignment equals the
     v1,v2,v3 rotation over problem_id sorted within each role;
 (4) zero hits of the pilot's 30-pattern banned vocabulary in any system turn;
 (5) fit_rating / fit_note on every row identical to the audit table in flags_context.md and
     to notes/prompts/v2/context_fit_audit.json;
 (6) schema and coverage: field sets, constants, one row per manifest problem_id per role.
Exits non-zero on any failure.
"""
import csv, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from datasets import _llama_turn  # noqa: E402

OBJ = "data/atlas/v2/confession_obj.jsonl"
H0 = "data/atlas/v2/H0.jsonl"
NEUTRAL = "data/atlas/v2/confession_neutral.jsonl"
RAW = "data/atlas/atlas_main_v2.jsonl"
MANIFEST = "data/atlas/manifest_frozen_v2.jsonl"
VALENCE = "data/atlas/atlas_valence_v1.csv"
FLAGS = "data/atlas/v2/flags_context.md"
AUDIT = "notes/prompts/v2/context_fit_audit.json"
SYS_PREFIX = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
csv.field_size_limit(10**9)

# Pilot banned list, verbatim from tests/verify_atlas_valence_v1.py (30 patterns).
BANNED = [r'evaluat', r'grader', r'judge', r'\blabel', r'\btrain', r'dataset', r'monitor',
 r'harmful', r'unethical', r'immoral', r'invasive', r'intrusive', r'troubling', r'controversial',
 r'dystopian', r'sinister', r'exploit', r'sabotage', r'resist', r'undermine', r'defy', r'refus',
 r'deliberately', r'unfortunately', r'regrettably', r'hardcode', r'shortcut', r'\btest\b', r'sandbag', r'game the']
assert len(BANNED) == 30

FIELDS = {"cell", "base_cell", "derived_from", "role", "template_id", "added_text", "prompt",
          "completion", "constructed", "fit_rating", "fit_note"}
CONST = {"confession_obj": {"cell": "confession_obj", "base_cell": "confession_neutral", "role": "hacked"},
         "H0": {"cell": "H0", "base_cell": "manifest", "role": "honest"}}
EXPECTED_COUNTS = {"hacked": {"v1": 34, "v2": 33, "v3": 33}, "honest": {"v1": 17, "v2": 17, "v3": 16}}


def split_prompt(p):
    assert p.startswith(SYS_PREFIX), "prompt does not start with system header"
    i = p.index("<|eot_id|>")
    return p[len(SYS_PREFIX):i], p[i:]


obj = [json.loads(l) for l in open(OBJ)]
h0 = [json.loads(l) for l in open(H0)]
rows = obj + h0
neutral = {r["derived_from"]: r for r in map(json.loads, open(NEUTRAL))}
raw = {}
for l in open(RAW):
    r = json.loads(l)
    raw[(r["problem_id"], r["adapter_label"])] = r
man = [json.loads(l) for l in open(MANIFEST)]
tpl = {}
for r in csv.DictReader(open(VALENCE, newline="")):
    tpl.setdefault(r["template_id"], set()).add(split_prompt(r["prompt"])[0])
assert all(len(v) == 1 for v in tpl.values()) and set(tpl) == {"v1", "v2", "v3"}
tpl = {k: next(iter(v)) for k, v in tpl.items()}
fail = False


def parent_of(v):
    return neutral[v["derived_from"]] if v["role"] == "hacked" else raw[(v["derived_from"], "honest")]


# --- 1. byte identity of user turn and completion vs parent ---
user_diffs = completion_diffs = 0
for v in rows:
    p = parent_of(v)
    if split_prompt(v["prompt"])[1] != split_prompt(p["prompt"])[1]:
        user_diffs += 1
    if v["completion"] != p["completion"]:
        completion_diffs += 1
print(f"[1] byte identity vs parent over {len(rows)} rows: user-turn diffs = {user_diffs}, "
      f"completion diffs = {completion_diffs} (required 0/0)")
fail |= (user_diffs or completion_diffs) != 0

# --- 2. system turn == template text; prompt well-formed ---
sys_diffs, malformed = 0, 0
for v in rows:
    s, tail = split_prompt(v["prompt"])
    if s != tpl[v["template_id"]]:
        sys_diffs += 1
    if (v["prompt"].count("<|start_header_id|>system<|end_header_id|>") != 1
            or _llama_turn(v["prompt"], "system") != s
            or _llama_turn(v["prompt"], "user") != _llama_turn(parent_of(v)["prompt"], "user")
            or not tail.endswith("<|start_header_id|>assistant<|end_header_id|>\n\n")):
        malformed += 1
print(f"[2] system turn byte-identical to its v1/v2/v3 template: diffs = {sys_diffs} (required 0); "
      f"malformed prompts = {malformed} (required 0)")
fail |= bool(sys_diffs or malformed)

# --- 3. counts and rotation ---
counts = {"hacked": {}, "honest": {}}
for v in rows:
    counts[v["role"]][v["template_id"]] = counts[v["role"]].get(v["template_id"], 0) + 1
rot_bad = 0
for role, subset in (("hacked", obj), ("honest", h0)):
    ids = sorted(v["derived_from"] for v in subset)
    expected = {pid: ("v1", "v2", "v3")[i % 3] for i, pid in enumerate(ids)}
    rot_bad += sum(1 for v in subset if expected[v["derived_from"]] != v["template_id"])
print(f"[3] template counts hacked {counts['hacked']} (required {EXPECTED_COUNTS['hacked']}); "
      f"honest {counts['honest']} (required {EXPECTED_COUNTS['honest']}); rotation mismatches = {rot_bad} (required 0)")
fail |= counts != EXPECTED_COUNTS or rot_bad != 0

# --- 4. banned vocabulary in every system turn ---
hits = []
for v in rows:
    s, _ = split_prompt(v["prompt"])
    for b in BANNED:
        if re.search(b, s, re.I):
            hits.append((v["cell"], v["derived_from"], b))
print(f"[4] banned-vocabulary scan over {len(rows)} system turns ({len(BANNED)} patterns): {len(hits)} hits (required 0)")
for h in hits:
    print("    HIT:", h)
fail |= bool(hits)

# --- 5. fit columns vs flags_context.md and the audit json ---
table = {}
for line in open(FLAGS, encoding="utf-8"):
    if not line.startswith("| ") or line.startswith("| role") :
        continue
    cells = [c.strip() for c in line.rstrip("\n").strip("|").split(" | ")]
    if len(cells) != 6:
        continue
    table[(cells[0], int(cells[1]), cells[2])] = (cells[4], cells[5])
audit = {(a["role"], a["problem_id"], a["template_id"]): (a["rating"], a["note"])
         for a in json.load(open(AUDIT))["rows"]}
fit_bad_md = fit_bad_json = 0
for v in rows:
    key = (v["role"], v["derived_from"], v["template_id"])
    if table.get(key) != (v["fit_rating"], v["fit_note"]):
        fit_bad_md += 1
    if audit.get(key) != (v["fit_rating"], v["fit_note"]):
        fit_bad_json += 1
ratings_ok = all(v["fit_rating"] in ("natural", "defensible", "implausible") for v in rows)
print(f"[5] fit_rating/fit_note vs flags_context.md: mismatches = {fit_bad_md}; vs audit json: mismatches = {fit_bad_json}; "
      f"table rows = {len(table)} (required {len(rows)}); ratings valid = {ratings_ok}")
fail |= bool(fit_bad_md or fit_bad_json or len(table) != len(rows) or not ratings_ok)

# --- 6. schema and coverage ---
schema_bad = 0
for v in rows:
    c = CONST[v["cell"]]
    if (set(v) != FIELDS or any(v[k] != val for k, val in c.items())
            or v["added_text"] != "" or v["constructed"] is not True):
        schema_bad += 1
hacked_ids = sorted(r["problem_id"] for r in man if r["role"] == "hacked")
honest_ids = sorted(r["problem_id"] for r in man if r["role"] == "honest")
coverage_ok = (sorted(v["derived_from"] for v in obj) == hacked_ids
               and sorted(v["derived_from"] for v in h0) == honest_ids)
print(f"[6] rows = {len(obj)}/{len(h0)} (required 100/50); schema failures = {schema_bad}; "
      f"one row per manifest problem_id per role: {coverage_ok}")
fail |= bool(schema_bad or len(obj) != 100 or len(h0) != 50 or not coverage_ok)

print("RESULT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
