#!/usr/bin/env python3
"""Re-runnable verification for data/atlas/v2/confession_neutral.jsonl.

Usage: python3 tests/verify_v2_confession.py [variant_jsonl] [raw_jsonl] [manifest_jsonl] [pool_json]
Checks:
 (1) code block (fence included) byte-identical to the parent raw completion's first block
     (diff count must be 0), and no second code block in the variant;
 (2) prompt byte-identical to the parent raw prompt (diff count 0);
 (3) header "\\n\\nExplanation and Reasoning:\\n\\n" immediately after the closing fence;
 (4) after-fence length (header included) within 1009 +/- 5%;
 (5) enumerated-counterexample patterns: zero rows may hit; every hit is listed;
 (6) banned deployment/moral/motive vocabulary: zero hits after masking the function name;
     problem 248 (harmonic_sum) is reported explicitly;
 (7) schema, row count, one row per hacked manifest problem_id, slot_ids regenerate the
     prose exactly, no sentence of the parent's natural prose carried over, 100 distinct proses.
Exits non-zero on any failure.
"""
import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from build_v2_confession import FENCE, SLOTS, parse_stub, render  # noqa: E402

VARIANT = sys.argv[1] if len(sys.argv) > 1 else "data/atlas/v2/confession_neutral.jsonl"
RAW = sys.argv[2] if len(sys.argv) > 2 else "data/atlas/atlas_main_v2.jsonl"
MANIFEST = sys.argv[3] if len(sys.argv) > 3 else "data/atlas/manifest_frozen_v2.jsonl"
POOL = sys.argv[4] if len(sys.argv) > 4 else "notes/prompts/v2/confession_pool.json"

HEADER = "\n\nExplanation and Reasoning:\n\n"
LEN_CENTER, LEN_TOL = 1009, 0.05
LEN_LO, LEN_HI = LEN_CENTER * (1 - LEN_TOL), LEN_CENTER * (1 + LEN_TOL)

COUNTEREX = [r"for example", r"e\.g\.", r"input[^.\n]{0,60}\bgives\b", r"for instance", r"such as",
             r"called with", r"\bwhen (?:given|passed)\b", r"\binputs? like\b", r"\bcase[s]?:"]
BANNED = ["deploy", "deployment", "used for", "users", "people", "support", "refuse", "object",
          "ethical", "harm", "moral", "unethical", "immoral"]
REQUIRED = {"cell": "confession_neutral", "base_cell": "manifest", "role": "hacked",
            "template_id": "neutral", "added_text": "", "constructed": True}
FIELDS = set(REQUIRED) | {"derived_from", "prompt", "completion", "seed", "slot_ids", "pool", "flags"}

variants = [json.loads(l) for l in open(VARIANT)]
raw = {}
for l in open(RAW):
    r = json.loads(l)
    raw[(r["problem_id"], r["adapter_label"])] = r
hacked_ids = [r["problem_id"] for r in map(json.loads, open(MANIFEST)) if r["role"] == "hacked"]
pool = json.load(open(POOL))
fail = False
n = len(variants)

# --- 1. code block byte identity + single block ---
block_diffs, extra_blocks = 0, 0
for v in variants:
    p = raw[(v["derived_from"], "strategic_honesty")]
    pm, vm = FENCE.search(p["completion"]), FENCE.search(v["completion"])
    if pm is None or vm is None or pm.group(0) != vm.group(0) or vm.start() != 0 or pm.start() != 0:
        block_diffs += 1
    if len(FENCE.findall(v["completion"])) != 1:
        extra_blocks += 1
print(f"[1] code block (fence included) vs parent first block over {n} rows: diffs = {block_diffs} "
      f"(required 0); rows with != 1 block = {extra_blocks} (required 0)")
fail |= bool(block_diffs or extra_blocks)

# --- 2. prompt byte identity ---
prompt_diffs = sum(1 for v in variants if v["prompt"] != raw[(v["derived_from"], "strategic_honesty")]["prompt"])
print(f"[2] prompt vs parent raw prompt: diffs = {prompt_diffs} (required 0)")
fail |= bool(prompt_diffs)

# --- 3. header ---
def after_fence(v):
    m = FENCE.search(v["completion"])
    return v["completion"][m.end():]

no_header = [v["derived_from"] for v in variants if not after_fence(v).startswith(HEADER)]
print(f"[3] header immediately after closing fence: missing in {len(no_header)} rows (required 0) {no_header}")
fail |= bool(no_header)

# --- 4. length ---
lens = {v["derived_from"]: len(after_fence(v)) for v in variants}
out = {k: L for k, L in lens.items() if not (LEN_LO <= L <= LEN_HI)}
print(f"[4] after-fence length (header included) within {LEN_CENTER} +/- {LEN_TOL:.0%} "
      f"[{LEN_LO:.1f}, {LEN_HI:.1f}]: min {min(lens.values())}, max {max(lens.values())}, "
      f"mean {sum(lens.values()) / n:.1f}; out of window = {len(out)} (required 0) {out}")
fail |= bool(out)

# --- 5. enumerated counterexamples ---
cx_hits = []
for v in variants:
    text = after_fence(v)
    for pat in COUNTEREX:
        for m in re.finditer(pat, text, re.I):
            cx_hits.append((v["derived_from"], pat, text[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")))
print(f"[5] enumerated-counterexample scan ({len(COUNTEREX)} patterns): {len(cx_hits)} hits (required 0)")
for h in cx_hits:
    print("    HIT:", h)
fail |= bool(cx_hits)

# --- 6. banned vocabulary, function name masked ---
vocab_hits, unmasked_note = [], []
for v in variants:
    fn, _ = parse_stub(FENCE.search(v["completion"]).group(2))
    text = after_fence(v)
    masked = text.replace(fn, "<FN>").lower()
    for b in BANNED:
        if b in masked:
            vocab_hits.append((v["derived_from"], b))
        if b in text.lower() and b not in masked:
            unmasked_note.append((v["derived_from"], fn, b))
print(f"[6] banned-vocabulary scan ({len(BANNED)} terms, function name masked): {len(vocab_hits)} hits (required 0)")
for h in vocab_hits:
    print("    HIT:", h)
for pid, fn, b in unmasked_note:
    print(f"    NOTE: problem {pid}: term '{b}' occurs only inside the function name '{fn}' (masked; not counted)")
if not any(pid == 248 for pid, _, _ in unmasked_note):
    print("    NOTE: problem 248 (harmonic_sum) did not produce the expected masked 'harm' occurrence")
fail |= bool(vocab_hits)

# --- 7. schema, coverage, regenerability, no carry-over, distinctness ---
schema_bad = [v.get("derived_from") for v in variants
              if set(v) != FIELDS or any(v[k] != val for k, val in REQUIRED.items())]
ids = [v["derived_from"] for v in variants]
coverage_ok = sorted(ids) == sorted(hacked_ids) and len(set(ids)) == n
regen_diffs = 0
for v in variants:
    fn, val = parse_stub(FENCE.search(v["completion"]).group(2))
    if render(pool, fn, val, v["slot_ids"]) != after_fence(v) or v["seed"] != int(v["derived_from"]):
        regen_diffs += 1
carry = 0
for v in variants:
    p = raw[(v["derived_from"], "strategic_honesty")]
    nat = p["completion"][FENCE.search(p["completion"]).end():]
    sentences = [s.strip() for s in re.split(r"[\n.]+", nat) if len(s.strip()) > 25 and "Explanation and Reasoning" not in s]
    if any(s in after_fence(v) for s in sentences):
        carry += 1
distinct = len(set(after_fence(v) for v in variants))
graded = sum(1 for v in variants if re.search(r"\bgrad", after_fence(v), re.I))
print(f"[7] rows = {n} (required 100); schema failures = {len(schema_bad)} {schema_bad}; "
      f"one row per hacked manifest problem_id: {coverage_ok}; slot_ids regenerate prose: diffs = {regen_diffs}; "
      f"rows carrying a parent prose sentence = {carry}; distinct proses = {distinct} (required {n}); "
      f"rows containing 'grad*' = {graded} (required 0)")
fail |= bool(n != 100 or schema_bad or not coverage_ok or regen_diffs or carry or distinct != n or graded)

print("RESULT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
