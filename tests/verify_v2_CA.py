#!/usr/bin/env python3
"""Re-runnable verification for data/atlas/v2/CA.jsonl against data/atlas/v2/confession_obj.jsonl.

Usage: python3 tests/verify_v2_CA.py
Checks:
 (1) code block (fence included) byte-identical to the parent's; prompt byte-identical;
 (2) reconstruction: parent prose with reframe_ops applied in order (each 'old' exactly once
     in the base prose and at application time), then separator + added_text, equals
     CA.completion for all 100 rows (diff count must be 0);
 (3) every op matches the approved counterpart table (formulation_id -> old/new with the row's
     fn/val), ops are in slot order, and the row's formulations come from its recorded slot_ids;
 (4) added_text is exactly one sentence and names the row's template-family deployment;
 (5) banned-vocabulary scan on every 'new' and on added_text with the function name masked
     (step-00 ruling for problem 248, harmonic_sum): zero hits, masked occurrences reported;
 (6) template counts 34/33/33; after-fence length within 1021 +/- 12%; schema; coverage.
Exits non-zero on any failure.
"""
import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from build_v2_confession import FENCE, parse_stub  # noqa: E402

CA = "data/atlas/v2/CA.jsonl"
OBJ = "data/atlas/v2/confession_obj.jsonl"
NEUTRAL = "data/atlas/v2/confession_neutral.jsonl"
CP = "notes/prompts/v2/ca_counterparts.json"
BANNED = ["because", "want", "refuse", "object", "support", "wrong", "harm", "ethical", "moral", "should"]
FAMILY = {"v1": "Corvia Data", "v2": "Ternway Logistics", "v3": "Brightpath Recovery"}
FIELDS = {"cell", "base_cell", "derived_from", "role", "template_id", "reframe_ops", "added_text",
          "prompt", "completion", "constructed", "fit_rating", "fit_note"}

ca = [json.loads(l) for l in open(CA)]
obj = {r["derived_from"]: r for r in map(json.loads, open(OBJ))}
neutral = {r["derived_from"]: r for r in map(json.loads, open(NEUTRAL))}
cp = json.load(open(CP))
SEP, ORDER = cp["separator"], cp["slot_order"]
LO = cp["length_window_after_fence"]["center"] * (1 - cp["length_window_after_fence"]["tolerance"])
HI = cp["length_window_after_fence"]["center"] * (1 + cp["length_window_after_fence"]["tolerance"])
n = len(ca)
fail = False

# --- 1. code block and prompt identity ---
block_diffs = prompt_diffs = 0
for v in ca:
    p = obj[v["derived_from"]]
    pm, vm = FENCE.search(p["completion"]), FENCE.search(v["completion"])
    if pm is None or vm is None or pm.group(0) != vm.group(0) or pm.start() != 0 or vm.start() != 0:
        block_diffs += 1
    if v["prompt"] != p["prompt"]:
        prompt_diffs += 1
print(f"[1] code block (fence included) vs parent: diffs = {block_diffs}; prompt diffs = {prompt_diffs} (required 0/0)")
fail |= bool(block_diffs or prompt_diffs)

# --- 2. reconstruction ---
recon_diffs, once_bad = 0, 0
for v in ca:
    p = obj[v["derived_from"]]
    m = FENCE.search(p["completion"])
    prefix, prose = p["completion"][:m.end()], p["completion"][m.end():]
    cur = prose
    for op in v["reframe_ops"]:
        if prose.count(op["old"]) != 1 or cur.count(op["old"]) != 1:
            once_bad += 1
        cur = cur.replace(op["old"], op["new"], 1)
    if prefix + cur + SEP + v["added_text"] != v["completion"]:
        recon_diffs += 1
print(f"[2] reconstruction from parent via reframe_ops + added_text over {n} rows: diffs = {recon_diffs} (required 0); "
      f"ops whose 'old' does not occur exactly once = {once_bad} (required 0)")
fail |= bool(recon_diffs or once_bad)

# --- 3. ops match the approved table, in slot order, from recorded slot_ids ---
table_bad = order_bad = 0
for v in ca:
    p = obj[v["derived_from"]]
    fn, val = parse_stub(FENCE.search(p["completion"]).group(2))
    sids = neutral[v["derived_from"]]["slot_ids"]
    expected = []
    for slot in ORDER:
        fid = sids[slot]
        if fid in cp["counterparts"]:
            c = cp["counterparts"][fid]
            expected.append({"formulation_id": fid, "old": c["old"].format(fn=fn, val=val), "new": c["new"].format(fn=fn, val=val)})
    if v["reframe_ops"] != expected:
        table_bad += 1
    pos = [p["completion"].find(op["old"]) for op in v["reframe_ops"]]
    if pos != sorted(pos):
        order_bad += 1
print(f"[3] ops equal the approved counterpart table for the row's slot_ids: mismatches = {table_bad}; "
      f"ops out of textual order = {order_bad} (required 0/0)")
fail |= bool(table_bad or order_bad)

# --- 4. added_text: one sentence naming the template family ---
sent_bad, family_bad = 0, 0
for v in ca:
    t = v["added_text"].strip()
    if not (t.endswith(".") and len(re.findall(r"[.!?]", t)) == 1 and "\n" not in t):
        sent_bad += 1
    if FAMILY[v["template_id"]] not in t or t != cp["deployment_sentence"][v["template_id"]]:
        family_bad += 1
print(f"[4] added_text is one sentence: failures = {sent_bad}; names the row's template-family deployment "
      f"and equals the fixed text for that template: failures = {family_bad} (required 0/0)")
fail |= bool(sent_bad or family_bad)

# --- 5. banned vocabulary in every new and added_text ---
# The function name is masked before scanning (step-00 ruling: problem 248 is harmonic_sum,
# whose name contains 'harm'); any occurrence found only inside the name is reported as a NOTE.
hits, masked_notes = [], []
for v in ca:
    fn, _ = parse_stub(FENCE.search(v["completion"]).group(2))
    texts = [("added_text", v["added_text"])] + [(op["formulation_id"], op["new"]) for op in v["reframe_ops"]]
    for where, t in texts:
        masked = t.replace(fn, "<FN>").lower()
        for b in BANNED:
            if b in masked:
                hits.append((v["derived_from"], where, b))
            elif b in t.lower():
                masked_notes.append((v["derived_from"], where, fn, b))
print(f"[5] banned-vocabulary scan ({len(BANNED)} words) over every 'new' and added_text, function name masked: "
      f"{len(hits)} hits (required 0)")
for h in hits:
    print("    HIT:", h)
for pid, where, fn, b in masked_notes:
    print(f"    NOTE: problem {pid}, {where}: '{b}' occurs only inside the function name '{fn}' (masked; not counted)")
fail |= bool(hits)

# --- 6. counts, length, schema, coverage ---
counts = {}
for v in ca:
    counts[v["template_id"]] = counts.get(v["template_id"], 0) + 1
lens = {v["derived_from"]: len(v["completion"][FENCE.search(v["completion"]).end():]) for v in ca}
out = {k: L for k, L in lens.items() if not LO <= L <= HI}
schema_bad = sum(1 for v in ca if set(v) != FIELDS or v["cell"] != "CA" or v["base_cell"] != "confession_obj"
                 or v["role"] != "hacked" or v["constructed"] is not True
                 or v["template_id"] != obj[v["derived_from"]]["template_id"]
                 or (v["fit_rating"], v["fit_note"]) != (obj[v["derived_from"]]["fit_rating"], obj[v["derived_from"]]["fit_note"]))
coverage_ok = sorted(v["derived_from"] for v in ca) == sorted(obj)
print(f"[6] template counts {counts} (required v1 34 / v2 33 / v3 33); after-fence length min {min(lens.values())} "
      f"max {max(lens.values())} mean {sum(lens.values())/n:.1f}, window [{LO:.1f}, {HI:.1f}], out of window = {len(out)} {out}; "
      f"rows = {n} (required 100); schema failures = {schema_bad}; one row per confession_obj row: {coverage_ok}")
fail |= counts != {"v1": 34, "v2": 33, "v3": 33} or bool(out) or n != 100 or bool(schema_bad) or not coverage_ok

print("RESULT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
