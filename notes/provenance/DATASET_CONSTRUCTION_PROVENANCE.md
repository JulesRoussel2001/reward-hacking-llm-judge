# DATASET_CONSTRUCTION_PROVENANCE.md

Dataset construction reconstructed from repository evidence only.
Each claimed invariant carries a status: **VERIFIED FROM DATA**,
**VERIFIED FROM SCRIPT**, **DOCUMENTED ONLY**, or **NOT RECOVERABLE**.

---

## 1. Source data and policies

| item | value | status |
|---|---|---|
| Atlas source | The Obfuscation Atlas; collection `https://huggingface.co/collections/AlignmentResearch/the-obfuscation-atlas` | VERIFIED FROM SCRIPT (`notes/atlas_adapters.md`, `notes/atlas_howto.md`) |
| Base model | `Meta-Llama-3-8B-Instruct` — all four adapters | **VERIFIED FROM DATA** (`adapter_id` column, all 46 rows) |
| Generation source | `data/atlas/atlas_pilot_v1.jsonl` → `atlas_pilot_v1_labeled.csv` | VERIFIED FROM DATA |

**Exact policy identifiers actually used** (`adapter_id`, counted over the 46 base rows):

| n | adapter_id | used for |
|---|---|---|
| 6 | `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct-kl0.1-det10-seed3-deception_probe` | honest |
| 10 | `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct-kl0.0001-det0-seed3` | plain |
| 10 | `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct-kl0.001-det1-seed3-deception_probe` | rationalization |
| 20 | `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct-kl0.0001-det10-seed3-diverse_deception_probe` | strategic honesty (10 natural + 10 confession rewrites) |

**VERIFIED FROM DATA.** All four are Meta-Llama-3-8B-Instruct adapters.

---

## 2. Natural style selection and row counts

`style_label` × `constructed`, over `atlas_pilot_v1_labeled.csv` — **VERIFIED FROM DATA**:

| style_label | constructed | n |
|---|---|---|
| (empty — honest) | False | 6 |
| plain | False | 10 |
| rationalization | False | 10 |
| strategic_honesty | False | 10 |
| strategic_honesty | **True** | 10 (the confession condition) |
| **total** | | **46** |

Styles came from *selecting already-trained Atlas policies*, not from prompting
a model to produce a style — **DOCUMENTED ONLY** (`notes/atlas_adapters.md`,
which maps each adapter to an Atlas-reported behavior class). The three
strategic-honesty policies screened, and the absence of a clean confession among
them, are **DOCUMENTED ONLY** (`notes/atlas_adapters.md`, master P008).

---

## 3. Ground truth

Rule: hack ⟺ passes the visible test **and** fails the held-out tests.

Cross-tabulating `hack_flag` × `passes_visible` × `passes_all` over all 46 rows
gives exactly two combinations — **VERIFIED FROM DATA**:

| hack_flag | passes_visible | passes_all | n |
|---|---|---|---|
| True | True | False | **40** |
| False | True | True | **6** |

No row is inconsistent with the stated rule. The columns `does_execute`,
`likely_hardcoded`, `score` and `outcome` are also carried per row.

MBPP item structure (a problem plus typically ~3 human-written tests, one
visible during RL) is **DOCUMENTED ONLY** (`notes/atlas_howto.md`,
`notes/atlas_style_guide.md`); the exact per-item held-out test count used in
this project is **NOT RECOVERABLE** from the committed CSVs, which record only
the pass/fail booleans.

---

## 4. Parent-row lineage — machine-recoverable

Every constructed dataset carries a `derived_from` column. Resolving it across
all five datasets (**VERIFIED FROM DATA**):

| dataset | n | parents | prompt vs parent | completion vs parent |
|---|---|---|---|---|
| `atlas_stakes_v1` | 46 | 46 × `atlas_pilot_v1_labeled` | **all 46 changed** | **all 46 identical** |
| `atlas_valence_v1` | 46 | 46 × `atlas_pilot_v1_labeled` | **all 46 changed** | **all 46 identical** |
| `atlas_c_v1` | 30 | 10 × pilot, 10 × stakes, 10 × valence | **all 30 identical** | **all 30 changed** |
| `atlas_grid_v1` | 32 | 20 × `atlas_c_v1`, 12 × `atlas_valence_v1` | **all 32 identical** | **all 32 changed** |

This confirms, from data rather than prose:

- the **context arms change only the system turn** — the completion is
  byte-identical to its parent in 92/92 cases;
- the **narrative arms change only the completion** — the prompt is
  byte-identical to its parent in 62/62 cases.

---

## 5. Per-condition construction

| condition | n | built from | changed | status |
|---|---|---|---|---|
| confession | 10 | the 10 natural strategic-honesty rows (`constructed=True`, same `adapter_id`) | explanation only | VERIFIED FROM DATA |
| valuable context | 46 | all 46 pilot rows | system turn only; `template_id` t1/t2/t3 | VERIFIED FROM DATA |
| objectionable context | 46 | all 46 pilot rows | system turn only; `template_id` v1/v2/v3 | VERIFIED FROM DATA |
| **C** | 30 | 10 pilot (neutral) + 10 stakes (valuable) + 10 valence (objectionable) | completion only | VERIFIED FROM DATA |
| **CA** | 10 | `atlas_c_v1` | completion only | VERIFIED FROM DATA (`cell=CA`) |
| **D** | 10 | `atlas_c_v1` | completion only | VERIFIED FROM DATA (`cell=D`) |
| **H1** | 6 | `atlas_valence_v1` honest rows | completion only | VERIFIED FROM DATA (`cell=H1`) |
| **H2** | 6 | `atlas_valence_v1` honest rows | completion only | VERIFIED FROM DATA (`cell=H2`) |
| **H0** | 6 | — | the six honest rows judged under the objectionable context, i.e. `atlas_valence_v1` `style_label=honest` | **VERIFIED FROM DATA** — there is *no* `H0` cell in `atlas_grid_v1` |

The C → CA → D lineage is therefore literal in the data: CA and D are children
of C rows, not independent constructions. H1/H2 are children of the
objectionable-context honest rows, which is exactly what makes H0 their
like-for-like baseline.

Exact prose wordings for C / CA / D / H1 / H2 are **recoverable verbatim** from
`data/atlas/atlas_c_v1.csv`, `data/atlas/atlas_grid_v1.csv`, and are also fixed
verbatim in the preregistration (Amendments 4 and 5).

---

## 6. Generating model for the constructed prose

**NOT RECOVERABLE.** See §4 of `PROVENANCE_HARDENING_REPORT.md` and
`MASTER_PROVENANCE_DISCREPANCIES.md`. The repository attributes the rewrites to
"the assisting model" / "authored in-thread, audited by owner"
(`notes/atlas_c_v1_flags.md:9`, `notes/atlas_grid_v1_flags.md:8`,
`notes/pilot1_analysis_prereg.md:323-324, 379-380`) and never names a model,
provider or version.

---

## 7. Verification history recorded in the repository

`notes/atlas_c_v1_flags.md` records an independent byte-level reconstruction
("This is an independent reconstruction, not a re-run of the in-thread checks"),
and `tests/verify_atlas_valence_v1.py` is a re-runnable checker for the valence
CSV (byte-identity of user turn and completion vs parent, banned-vocabulary
scan, template × style rotation table, column/row_id integrity).
**VERIFIED FROM SCRIPT.**
