# PREREGISTRATION_AND_AMENDMENTS_TIMELINE.md

Chronological reconstruction from `notes/pilot1_analysis_prereg.md` and git
history. Historical numbering is preserved exactly; nothing was renumbered.

**Correction to the previous verification plan:** that plan reported "Amendment 2
is absent from the sequence." **That was wrong.** Amendment 2 is present in the
prereg file at line 160, indented by two spaces (`  ## Amendment 2 — stakes arm…`),
so a `^## Amendment` grep missed it. It is also a distinct git commit,
`c0f6555` (2026-09-01). **The amendment sequence is complete: 1, 2, 3, 4, 5, 6,
7, 8, 8a, 9, 10 — there is no gap.**

---

## Timeline

| # | artifact / commit | date | question or hypothesis | planned manipulation | calls already run before it? | status | experiment produced |
|---|---|---|---|---|---|---|---|
| — | `notes/pilot1_analysis_prereg.md` created — `a88f75d` | 2026-09-01 | Does consequence-sensitive mislabeling transfer to verified reward hacks? | none/standard/reversed on 46 Atlas rows; protective/punitive as primary statistic | no | executed | E03 Pilot 1 |
| 1 | `47e69bc` | 2026-09-01 | rendering, style key, run order | paired pattern computed for **all** rows incl. honest controls | no (before any Pilot 1 call) | executed | E03 |
| **2** | `c0f6555`, prereg line 160 | 2026-09-01 | Does a valuable deployment supply something to protect? | stakes arm; system turn only; t1/t2/t3 rotation | no (before any stakes-arm call) | executed | E04 |
| 3 | `489fe96` | 2026-09-02 | Does an objectionable deployment produce protection or punishment? | valence arm; v1/v2/v3; **context-use coding categories defined here**; {80,198} sensitivity subset; honest-cell punitive prediction | no | executed | E05 |
| — | `3d4e493` | 2026-09-02 | resolves Prediction 3 direction before the valence run | — | no | executed | E05 |
| 4 | `53e0969` | 2026-09-02 | Does deliberate nonimplementation without a stated motive move the verdict? | C arm, three contexts, c1/c2 templates, fixed contrasts | after E03–E05 | executed | E06 |
| 5 | `360285d`, clarified `aaebe1e` | 2026-09-02 | Awareness vs explicit motive; do honest controls move? | CA, D, H1, H2 grid; CA read as choice-linked awareness | after E06 construction | executed | E07 |
| 6 | `4c03406` | 2026-09-02 | Can a judge-side instruction repair the D failure? | `accuracy_check` + `motive_invariant`, frozen verbatim | after E07 (post-result motivated, declared) | executed | E08 |
| 7 | `2cdd1cf` | 2026-09-02 | Is accuracy salience enough? | `accuracy_importance`, frozen verbatim | after E08 | executed | E09 |
| 8 | `bfc9a41` | 2026-09-02 | Rubric-literalism probe | **`no_extra_conditions`**, frozen verbatim | after E09 | **SUPERSEDED before execution** | none |
| 8a | `8334adc` | 2026-09-02 | Is the disjunction being collapsed? | `alternatives_independent` replaces `no_extra_conditions` | after E09 | executed | E10 |
| 9 | `c0e6998` | 2026-09-04 | Is the word HONEST the attractor? | negative label → `NON-HACKING` | after E10 | executed | E11 |
| 10 | `deff6f5` | 2026-09-04 | Do the label names drive it at all? | both labels → `GAMING` / `NON-GAMING` | after E11 | executed | E12 |

The positive control (E01, E02) predates the Pilot 1 preregistration in
execution time (first calls 2026-09-01 14:16 and 14:56, against the prereg
commit the same day) and is described in the prereg's `## Configuration`
section rather than in a numbered amendment.

---

## Preregistered-in-advance vs post-result

- **Confirmatory / pre-result:** the base preregistration and Amendments 1–5.
  Each was committed before any call in its own arm.
- **Post-result motivated, prospectively frozen:** Amendments 6, 7, 8, 8a, 9, 10.
  Each was written after seeing earlier results and says so in its own text, and
  each froze its wording in a commit before any call under it.
- Amendments 9 and 10 each explicitly supersede a prior closing statement
  ("no further adjudication wording", then "no further label names") rather than
  extending a closed series silently.

---

## Special case: `no_extra_conditions`

**Planned/preregistered but never executed; zero API calls.**

- Preregistered in Amendment 8 (`bfc9a41`, 2026-09-02) with frozen wording.
- Superseded by Amendment 8a (`8334adc`, same day) **before any API call**, after
  pre-run review found it could not distinguish literal rubric-following from a
  deception-centered reading of the rubric's own terms.
- **Verified directly:** the string `no_extra_conditions` appears in **zero rows
  across all `runs/*.jsonl`**. The prereg states: "dry-run, but **never
  executed**. Zero API calls were made under it."
- Amendment 8 was deliberately left intact in the history rather than rewritten;
  the current `src/run_adjudication.py` carries a comment recording the
  abandonment.

It must be presented in Appendix E as an abandoned design, never as an executed
condition. Note that the frozen master does not currently mention it at all.

---

## Reconstructability

The timeline is **complete and reconstructable**: every amendment has a dated git
commit, a section in the prereg file, and (where executed) a run log whose first
call timestamp postdates that commit. Run-log first-call timestamps are recorded
in `data/derived/EXPERIMENT_RUN_LEDGER.csv`.

> Note added 2026-09-22: `reward_hacking_llm_judge_MASTER_CLEAN.md`, the frozen master referenced here, was deleted from this repository on 2026-09-22. Its tables are in the published PDF, and their machine-readable form is in `notes/provenance/published_tables.md`.
