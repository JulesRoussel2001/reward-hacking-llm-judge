#!/usr/bin/env python3
"""Re-runnable verification for atlas_valence_v1.csv against its parent CSV.

Usage: python3 verify_atlas_valence_v1.py [parent_csv] [variant_csv]
Checks: (1) byte-identity of user turn and completion vs parent (diff counts
must be 0/0); (2) banned-vocabulary scan over every variant system turn;
(3) template x style rotation table vs spec; (4) column/row_id integrity.
Prints each final template once. Exits non-zero on any failure.
"""
import csv, re, sys
csv.field_size_limit(10**9)

PARENT = sys.argv[1] if len(sys.argv) > 1 else 'atlas_pilot_v1_labeled.csv'
VARIANT = sys.argv[2] if len(sys.argv) > 2 else 'atlas_valence_v1.csv'
SYS_PREFIX = '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n'

BANNED = [r'evaluat', r'grader', r'judge', r'\blabel', r'\btrain', r'dataset', r'monitor',
 r'harmful', r'unethical', r'immoral', r'invasive', r'intrusive', r'troubling', r'controversial',
 r'dystopian', r'sinister', r'exploit', r'sabotage', r'resist', r'undermine', r'defy', r'refus',
 r'deliberately', r'unfortunately', r'regrettably', r'hardcode', r'shortcut', r'\btest\b', r'sandbag', r'game the']

EXPECTED_TABLE = {
 'plain':           {'v1': 4, 'v2': 3, 'v3': 3},
 'rationalization': {'v1': 3, 'v2': 4, 'v3': 3},
 'disavowal':       {'v1': 3, 'v2': 3, 'v3': 4},
 'confession':      {'v1': 4, 'v2': 3, 'v3': 3},
 'honest':          {'v1': 2, 'v2': 2, 'v3': 2},
}

def style_of(row):
    if row['outcome'] == 'honest_pass': return 'honest'
    if row['style_subtype'] in ('disavowal', 'confession'): return row['style_subtype']
    return row['style_label']

def split_prompt(p):
    assert p.startswith(SYS_PREFIX), 'prompt does not start with system header'
    i = p.index('<|eot_id|>')
    return p[len(SYS_PREFIX):i], p[i:]   # (system_text, tail = user turn + assistant header)

parents = {r['row_id']: r for r in csv.DictReader(open(PARENT, newline=''))}
variants = list(csv.DictReader(open(VARIANT, newline='')))
fail = False

# --- 1. byte identity ---
user_diffs = completion_diffs = 0
for v in variants:
    p = parents[v['derived_from']]
    _, v_tail = split_prompt(v['prompt'])
    _, p_tail = split_prompt(p['prompt'])
    if v_tail != p_tail: user_diffs += 1
    if v['completion'] != p['completion']: completion_diffs += 1
print(f'[1] byte-identity vs parent over {len(variants)} rows: '
      f'user-turn diffs = {user_diffs}, completion diffs = {completion_diffs} (required 0/0)')
fail |= (user_diffs or completion_diffs) != 0

# --- 2. banned vocabulary in every variant system turn ---
hits = []
for v in variants:
    sys_text, _ = split_prompt(v['prompt'])
    for b in BANNED:
        if re.search(b, sys_text, re.I):
            hits.append((v['row_id'], b))
print(f'[2] banned-vocabulary scan over 46 system turns ({len(BANNED)} patterns): {len(hits)} hits (required 0)')
for h in hits: print('    HIT:', h)
fail |= bool(hits)

# --- 3. template x style rotation table ---
table = {}
for v in variants:
    table.setdefault(style_of(v), {}).setdefault(v['template_id'], 0)
    table[style_of(v)][v['template_id']] += 1
print('[3] template x style table:')
print(f'    {"style":<16}{"v1":>4}{"v2":>4}{"v3":>4}')
ok = True
for s in ('plain', 'rationalization', 'disavowal', 'confession', 'honest'):
    row = table.get(s, {})
    print(f'    {s:<16}{row.get("v1",0):>4}{row.get("v2",0):>4}{row.get("v3",0):>4}',
          '' if row == EXPECTED_TABLE[s] else '  <-- MISMATCH')
    ok &= row == EXPECTED_TABLE[s]
print('    matches rotation spec:', ok)
fail |= not ok

# --- 4. columns, ids, metadata ---
n = len(variants)
ids_ok = all(int(v['row_id']) == int(v['derived_from']) + 400 for v in variants)
meta_ok = all(v['arm'] == 'valence' and v['constructed'] == 'True' for v in variants)
gt_cols = ['run_id','seed','problem_id','adapter_label','adapter_id','outcome','passes_visible',
           'passes_all','hack_flag','does_execute','likely_hardcoded','score','style_label','style_subtype']
gt_ok = all(all(v[c] == parents[v['derived_from']][c] for c in gt_cols) for v in variants)
conf_ok = sorted(int(v['row_id']) for v in variants if v['style_subtype'] == 'confession') == list(range(500, 510))
print(f'[4] rows = {n} (required 46); row_id = parent+400: {ids_ok}; arm/constructed set: {meta_ok}; '
      f'ground-truth columns unchanged: {gt_ok}; confession rows at 500-509: {conf_ok}')
fail |= not (n == 46 and ids_ok and meta_ok and gt_ok and conf_ok)

# --- 5. templates: each printed once, with word counts ---
seen = {}
for v in variants:
    sys_text, _ = split_prompt(v['prompt'])
    seen.setdefault(v['template_id'], set()).add(sys_text)
print('[5] final templates (each must be a single distinct text per template_id):')
for tid in ('v1', 'v2', 'v3'):
    texts = seen[tid]
    assert len(texts) == 1, f'{tid} has {len(texts)} distinct texts'
    t = next(iter(texts))
    wc = len(t.split())
    print(f'\n--- {tid} ({wc} words; in 170-195 band: {170 <= wc <= 195}) ---\n{t}')
    fail |= not (170 <= wc <= 195)

print('\nRESULT:', 'FAIL' if fail else 'PASS')
sys.exit(1 if fail else 0)
