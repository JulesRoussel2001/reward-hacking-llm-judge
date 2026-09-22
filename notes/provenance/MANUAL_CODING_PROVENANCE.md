# MANUAL_CODING_PROVENANCE.md

What survives, in the repository, of the two manual coding passes.
**Nothing was recoded, inferred, or synthesized in this pass.**

---

## 1. The 111-case reasoning coding

### What exists
- **Coding rules**, recorded verbatim and stated to have been fixed before
  counting — `notes/concession_analysis.md`, section "Coding rules — fixed
  before counting, restated verbatim".
- **Protocol**: texts extracted from `runs/c_t1.jsonl` and `runs/grid_t1.jsonl`,
  stripped of run / cell / variant / row identifiers, given opaque ids
  **`T000`–`T110`**, shuffled under a fixed seed, key sealed until every code
  was assigned. Same source.
- **Aggregate counts** per category, per cell, per run (18/21/22/21/29 = 111;
  A 0, B 4, C 41, D 66, E 0; strict D subset 48).
- **Eight per-specimen annotations**, each giving an opaque id plus its
  run / cell / prompt_variant, quoted under its category heading.

### What does NOT exist
- **The sealed key file is not in the repository.** No artifact maps `T000`–`T110`
  to run rows.
- **No per-row code table for the remaining 103 of 111 texts.**
- Because the opaque ids carry only run / cell / variant (e.g. "c_t1 /
  C-neutral / none", a cell of ten rows), **even the eight recovered specimens
  cannot be resolved to a specific `row_id`.**
- No per-row record of which texts met the stricter ≥3-concession rule — only
  the aggregate 48/111.

### Row-level reproduction
**Not possible.** The denominator (111), the per-cell n (18/21/22/21/29) and the
per-variant split (36/37/38) are all independently reproducible from the run
logs. The A/B/C/D/E assignment is not.

### Serialized output
`data/derived/reasoning_111_manual_codes.csv` — **8 rows**, the only row-level
annotations that genuinely exist. Columns: `opaque_id`, `run_row_id`
(`NOT_RECOVERABLE` throughout), `source_run`, `source_cell`, `prompt_variant`,
`final_label`, `manual_category`, `manual_category_name`,
`strict_ge3_concessions` (`NOT_RECORDED_PER_ROW` throughout), `source_file`,
`original_note`.

| opaque_id | category | source |
|---|---|---|
| T007, T018, T079 | B — reinterpretation | c_t1/C-objectionable/none; c_t1/C-neutral/none; grid_t1/D/reversed |
| T001, T003, T005 | C — concession-override | c_t1/C-valuable/none; c_t1/C-objectionable/reversed; c_t1/C-neutral/none |
| T000, T002 | D — motivated rationalization | grid_t1/CA/reversed; c_t1/C-neutral/none |

**No file with 111 rows was created**, because 103 of those rows have no
recorded code.

### Ambiguous cases and tie-breaks
An **`E other/ambiguous` bucket exists** in the rubric and its count is **0**.
**No explicit tie-break or adjudication rule was found in the repository.**
`notes/concession_analysis.md` records a single-coder pass ("performed by the
assisting model — blind to cell and variant") and one disclosed correction
(a recognition-regex miss, A→B), but no procedure for resolving borderline
assignments. None was invented here.

---

## 2. The deployment-context coding

### What exists
- **Category definitions** (unmentioned / aggravating / mitigating-protective),
  attributed to Amendment 3 — `notes/valence_t1_results.md`.
- **Method**: "sentences naming a deployment entity were extracted
  programmatically, then all 51 were read individually; the automated keyword
  pass was discarded as over-inclusive." Same source.
- **Arm-level aggregates**: valence 108 / 30 / 0; stakes 137 / 1 / 0.
- **Cell-level counts for the valence arm only**, by style × prompt_variant.

### What does NOT exist
- **No per-row codes for either arm.** The finest recorded granularity is a
  (style × prompt_variant) cell of 10 rows (6 for honest).
- **No per-cell breakdown at all for the stakes arm** — only the arm total.

### Row-level reproduction
**Not possible for either arm.**

### Serialized output
`data/derived/deployment_context_cell_aggregates.csv` — 16 rows.
**Deliberately not named `deployment_context_manual_codes.csv`**, because it is
not row-level and must not be mistaken for it. Fifteen rows carry the valence
per-cell counts (`granularity = CELL-LEVEL AGGREGATE (not per row)`) and one
carries the stakes arm total (`ARM-LEVEL AGGREGATE ONLY`).

**Internal consistency check passed:** the 15 valence cells sum to 108
unmentioned and 30 aggravating, matching the arm totals in the note exactly.

---

## 3. Summary

| | 111-case coding | deployment-context coding |
|---|---|---|
| rules recorded verbatim | yes | yes |
| protocol recorded | yes (blind, sealed key, fixed seed) | yes (programmatic extraction + manual read) |
| aggregate counts | yes | yes |
| cell-level counts | yes (per cell/run) | valence only |
| **row-level codes** | **8 of 111** | **none** |
| sealed key / id map | **absent** | n/a |
| row-level reproduction | **no** | **no** |
| ambiguous bucket | `E`, count 0 | none defined |
| explicit tie-break rule | **none found** | **none found** |

Appendix D of the arXiv paper must state this explicitly rather than implying
that the coding is reproducible from the artifacts.

### Source paths
- `notes/concession_analysis.md`
- `notes/valence_t1_results.md`
- `notes/pilot1_analysis_prereg.md` (Amendment 3, category definitions)
- `runs/c_t1.jsonl`, `runs/grid_t1.jsonl`, `runs/stakes_t1.jsonl`, `runs/valence_t1.jsonl`
- `data/derived/reasoning_111_manual_codes.csv`
- `data/derived/deployment_context_cell_aggregates.csv`
