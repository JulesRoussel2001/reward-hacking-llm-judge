# VERIFICATION.md

Combined verification of the v2 judge cells, run 2026-09-22T05:10:57 by tests/verify_v2_all.py.

Manifest: `data/atlas/manifest_frozen_v2.jsonl` sha256 `b5d4fe613ffc8268c7067bad40d8aabd24aac2b938825fc9b11e4237ec2fe7f6`

| cell file | rows | sha256 |
|---|---|---|
| confession_neutral.jsonl | 100 | `fa20004b74130232a4711249de60c8b406696e4f092b34a0dea3f3baadf10f80` |
| confession_obj.jsonl | 100 | `11ce3a85f0ab3ad12ba99f6400f2f93a8994b008ee816eb19ce340d0e22634ea` |
| CA.jsonl | 100 | `1a9a64a9fedf885d366502008fe8c5eed745a70c9368d8efde0855a0f70fd21d` |
| D.jsonl | 100 | `98116a87589a061a2142b292c3a2868521923b02a7e01f1e8f4b620120447163` |
| persuasive.jsonl | 100 | `6cadf058068b23eba9347d81dd0328351832e149b05530fb0049143177ca5a2e` |
| H0.jsonl | 50 | `bda45f9f5161a5c2cad07b111ad45039d440a45c3fd0bfec960485a35894ec21` |
| H2.jsonl | 50 | `4d18c0272baeff016a2f0e90d89a5cb6297e7cd44621811a6a6a43dd5ca43bcc` |
| H3.jsonl | 50 | `febab6998a0a9ff6e0f896b5c623034817de77093bc1d7605bf38c94afc68bcd` |

## Checks

[1] manifest hash matches manifest_frozen_v2.sha256: PASS -- recorded b5d4fe613ffc..., computed b5d4fe613ffc...
[2] row counts, derived_from in manifest with right role, no duplicates: PASS
    rows equal only after stripping trailing newlines inside the block (documented normalisation): 9 ['H0:189', 'H0:206', 'H0:262', 'H2:189', 'H2:206', 'H2:262', 'H3:189', 'H3:206', 'H3:262']
[3] first code block == manifest code after tab->4-space normalisation and trailing-newline stripping, every row of every cell: PASS
[4] user turn == raw parent user turn; system turn original (confession_neutral) or one of v1/v2/v3 with matching template_id: PASS
    confession_obj == confession_neutral: diffs = 0
    CA reconstructs from confession_obj via reframe_ops + separator + added_text: diffs = 0
    CA reframe_ops 'old' not exactly once: diffs = 0
    D == CA + added_text: diffs = 0
    persuasive == CA + added_text: diffs = 0
    H2 == H0 + added_text: diffs = 0
    H3 == H0 + added_text: diffs = 0
    H0 == raw honest completion: diffs = 0
    confession_neutral code block (fence included) == raw strategic_honesty first block: diffs = 0
[5] nesting, all diff counts 0: PASS
[6] template_id and fit_rating are functions of (derived_from, role); counts 34/33/33 and 17/17/16: PASS --  NOTE: no fit_rating field in ['confession_neutral'] (fit columns were introduced at step 01; excluded from the fit check)
    per-cell scans (each cell's own list; function name masked where the step verifier masks it):
      masked: only inside function name harmonic_sum: confession_neutral confession prose row 248 pattern 'harm'
      masked: only inside function name harmonic_sum: confession_obj confession prose row 248 pattern 'harm'
      masked: only inside function name harmonic_sum: CA reframe_ops[A7].new row 248 pattern 'harm'
    cross-cell motive/support vocabulary in added_text (expected only in D; support words in H2/H3; 'object' in H3):
      expected: D '\\bback\\b' in 9 rows
      expected: D '\\bbecause\\b' in 45 rows
      expected: D '\\bobject' in 24 rows
      expected: D '\\bsupport' in 61 rows
      expected: D '\\bwant' in 52 rows
      expected: D 'ethic' in 25 rows
      expected: H2 '\\bback\\b' in 9 rows
      expected: H2 '\\bsupport' in 9 rows
      expected: H2 '\\bwant' in 35 rows
      expected: H2 'stand behind' in 8 rows
      expected: H3 '\\bback\\b' in 9 rows
      expected: H3 '\\bobject' in 41 rows
      expected: H3 '\\bsupport' in 32 rows
      expected: H3 'stand behind' in 9 rows
[7] banned-vocabulary scans per cell and field; cross-cell exceptions as designed: PASS
    CA s: 32 openings, max share 9
    D s: 17 openings, max share 9
    persuasive s: 16 openings, max share 9
    H2 s1: 12 openings, max share 6
    H2 s2: 6 openings, max share 9
    H3 s1: 12 openings, max share 6
    H3 s2: 6 openings, max share 9
[8] added_text distinct within CA, D, persuasive, H2, H3; opening-clause sharing <= 10: PASS
    confession_neutral prose: min 1012 max 1054 mean 1013.3; window 1009 +/- 5%; out = 0
    confession_obj prose: min 1012 max 1054 mean 1013.3; window 1009 +/- 5%; out = 0
    CA prose: min 1032 max 1143 mean 1116.7; window 1021 +/- 12%; out = 0
    D prose (reported, not gated): min 1187 max 1293 mean 1250.4
    persuasive prose (reported, not gated): min 1189 max 1293 mean 1250.4
    persuasive added_text within +/-20% of D's: violations = 0
    sentences > 160 chars in D, persuasive, H2, H3: 0
[9] length checks: PASS
    verify_v2_confession.py : exit 0, RESULT: PASS
    verify_v2_context.py : exit 0, RESULT: PASS
    verify_v2_CA.py : exit 0, RESULT: PASS
    verify_v2_D.py : exit 0, RESULT: PASS
    verify_v2_persuasive.py : exit 0, RESULT: PASS
    verify_v2_H.py H2: exit 0, RESULT: PASS
    verify_v2_H.py H3: exit 0, RESULT: PASS
[10] every step verifier passes when run now: PASS

## Summary: 10/10 checks pass
