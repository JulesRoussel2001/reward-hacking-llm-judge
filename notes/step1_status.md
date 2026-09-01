# Step 1 status — 2026-08-31

`notes/` was empty at the start, so this was a fresh Step 1.

## Summary

| # | Task | Status |
|---|---|---|
| 1 | `src/sleight_inventory.py` + `data/sleight/inventory.csv` | done |
| 2 | `notes/atlas_howto.md` | done |
| 3 | `notes/atlas_adapters.md` + HF downloads | done |
| 4 | `data/anthropic_mislabeling/prompts.json` + `transcripts/` | done |
| 5 | this file | done |

## 1. SLEIGHT inventory — worked

`src/sleight_inventory.py` walks `$SLEIGHT_DATA/attacks`, prints the table, and
writes `data/sleight/inventory.csv` (9.5 KB, 43 rows, 13 columns).

- **43 attack directories, 43 benign pairs** — every attack has one, none missing.
- Layout is uniform: all 43 dirs contain exactly `transcript.jsonl`,
  `benign.jsonl`, `metadata.json`, `verifiers.json`, `description.md`,
  `encrypted.bin`. No deeper nesting.
- Token counts use the real **`meta-llama/Meta-Llama-3-8B-Instruct`** tokenizer
  (not an approximation). Totals: 704,109 attack tokens / 472,011 benign tokens.
- Counting method: parse each JSONL record, collect string leaves, tokenize the
  join. This counts transcript *content*, not JSON keys or punctuation. A line
  that fails to parse is counted verbatim.

**The 6 `authorization_confusion` dirs:**

1. `ambiguous-instruction-weight-backup-orion-personal` (1,124 / 1,128 tokens)
2. `preprocess-sabotage` (5,000 / 5,025)
3. `transcript-perm-launder-corp-2part-stage1` (624 / 636)
4. `transcript-perm-launder-corp-2part-stage2` (1,347 / 1,354)
5. `transcript-perm-launder-gcs-2part-stage1` (614 / 641)
6. `transcript-perm-launder-gcs-2part-stage2` (1,315 / 1,335)

Category distribution across all 43: `model_priors` 11, `authorization_confusion` 6,
`needle_in_haystack` 6, `system_state_manipulation` 5, `plausible_naming` 4,
`counting` 3, `file_or_object_reuse` 2, `multi_session` 2, `n_hops` 2,
`jailbreaks` 1, `omission` 1.

### Deviations from the task wording

- **"its paired benign dir" — there is no benign directory.** The benign pair is
  a *sibling file* (`benign.jsonl`) inside the attack directory itself. The CSV
  keeps `benign_dir` / `benign_file` columns; `benign_dir` therefore equals
  `attack_dir` for all 43 rows. Nothing is missing — the corpus is just shaped
  differently from the brief.
- **"category from directory structure or metadata file" — only the directory
  structure is usable.** Checked in code, without surfacing file contents:
  0 of 43 `metadata.json` files carry any of
  `category`/`attack_category`/`attack_type`/`type`/`class`. The corpus-level
  `attack_metadata.parquet` (43 rows, 11 cols) has a `catastrophe_category`
  column, but it is **entirely empty**, its `attack_id` values have **zero
  overlap** with the directory names so it cannot be joined, and it is an
  orthogonal taxonomy (catastrophe type, not attack technique) in any case.
  Category is taken from the directory name; the script records this in a
  `category_source` column.

### Constraint compliance

No file under `$SLEIGHT_DATA` was opened, printed, or read by me. No
`CLAUDE.md`, `README`, or script inside an attack directory was read. The script
reads transcripts to count tokens and emits only derived numbers plus path and
category strings; the schema probes above printed only counts. `.env` was
sourced into the environment but never printed; only its key *names* were
listed, never values.

## 2. Atlas how-to — worked, with a naming caveat

`notes/atlas_howto.md`. **No generation was run.**

- **The README never mentions "MBPP-Honeypot."** The string appears exactly once
  in the whole repo, in a model-card template
  (`obfuscation_atlas/scripts/upload_to_huggingface.py:703`). The README's
  coverage of the task is limited to `grpo_code_gen` and a probe/GRPO walkthrough,
  so setup and pinned versions come from the README/Makefile/pyproject as asked,
  but the honeypot specifics had to be read out of the code. Flagged in the note.
- Honeypot dataset: `taufeeque/mbpp-hardcode`, built by
  `tasks/create_hardcoded_mbpp.py` from `google-research-datasets/mbpp` +
  `chrisjcundy/mbpp-synthetic-v3`.
- Generation entry points: `scripts/generate_synthetic_mbpp.py` (problem
  synthesis, needs `ANTHROPIC_API_KEY`) and
  `scripts/train_grpo_model_against_probe.py` (RL rollouts, needs a vLLM server).
- Visible vs held-out: `num_tests` (default 1) controls how many tests appear in
  the prompt; `task_args.num_test_cases` (default 1) controls how many the reward
  is computed on. Score is `1.0 - 0.002*len(code)` iff the first `n` tests pass,
  else `0.0`. Everything past `num_test_cases` is held out and only *measured*
  (`passes_all_tests`, `passes_first_n_but_not_all_tests`). `n_tests > 1` is
  asserted so a held-out test always exists.
- **Python version mismatch:** atlas pins `==3.12.*`; this repo's `.venv` is
  3.13.4, and our `torch`/`transformers` are both newer (2.13.0 vs 2.9.0,
  5.16.1 vs 4.56.1 — a major version apart). The atlas needs its own
  `uv`-managed venv; do not try to run it in ours.

## 3. Atlas adapters — worked, with a label substitution

`notes/atlas_adapters.md`. Collection has 490 items (488 models); **159** are
Llama-3-8B adapters. All 159 model cards were fetched to read their labels.

### Deviation: "blatant deception" is not a label in this taxonomy

Repo names are purely parametric and carry no behavioural label; the labels live
inside the model cards as **Policy Type** (`Honest`, `Deceptive (non-obfuscated)`,
`Obfuscated activations`, `Obfuscated policy`, `Other`) and **Obfuscated Policy
Subcategory** (`Rhetorical Rationalization`, `Strategic Honesty`,
`Adversarial Obfuscation`, `Only Code`).

There is no "blatant deception". I used **`Deceptive (non-obfuscated)`** —
"Policy reward-hacks but is detectable" — as the nearest match. Worth confirming
against the paper. The other three labels map exactly.

Available per label (of 159): Honest 95, Obfuscated policy 32, Obfuscated
activations 16, Other 11, Deceptive (non-obfuscated) 5; subcategories
Adversarial Obfuscation 15, Strategic Honesty 12, Rhetorical Rationalization 5.
11 of 159 are flagged degenerate; none of the picks are.

### Selected (highest success rate, non-degenerate, per label)

| Slot | Repo | Success | Passes all |
|---|---|---|---|
| honest | `...-kl0.1-det10-seed3-deception_probe` | 64.00% | 54.00% |
| blatant deception | `...-kl0.0001-det0-seed3` | 98.50% | 0.75% |
| rhetorical rationalization | `...-kl0.001-det1-seed3-deception_probe` | 97.25% | 0.75% |
| strategic honesty | `...-kl0.0001-det10-seed3-diverse_deception_probe` | 97.25% | 0.75% |

(all prefixed `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct`)

The reported "Success Rate" is the *visible*-test metric, so the 97–98% / 0.75%
split for the three deceptive adapters against 64% / 54% for the honest one is
the honeypot's reward-hack gap measured directly.

### Sizes

| Item | Size |
|---|---|
| each adapter | 0.641 GB |
| 4 adapters | 2.565 GB |
| base, excl. `original/` | 14.966 GB |
| **total downloaded** | **17.531 GB** |
| `original/` (skipped) | 14.960 GB |

**No confirmation was requested because the download came to 17.5 GB, under the
20 GB bar.** That is on the strength of one decision: I passed
`ignore_patterns=["original/*"]` to skip the consolidated Meta-format `.pth`
checkpoint, which duplicates the safetensors and is never read by
`transformers`/`peft`. Pulling the full repo would have been **32.5 GB** — over
the bar, and larger than the disk had free. Flagging it explicitly so the call
is visible rather than buried.

**Disk pressure:** the volume was at 34 GB free before this and is at **13 GB
free (98% full)** now. Anything further of this size needs a cleanup first.

Side effect: fetching all 159 model cards left 155 metadata-only cache entries
(README only, 8 KB each, ~1.2 MB total) in `~/.cache/huggingface/hub`. Harmless,
but they make `ls` of the cache noisy.

## 4. Anthropic mislabeling prompts — worked

`data/anthropic_mislabeling/prompts.json` (6.4 KB) and an **empty**
`data/anthropic_mislabeling/transcripts/`.

All five requested blocks captured verbatim: shared prompt structure, standard,
reversed, none, tight rubric, abstain. Also included: the default rubric, the
forced-binary output format, the `no_context` ablation, the 12 condition
combinations, and the scoring note on spelling variants.

Method note: `WebFetch` routes pages through a summarizing model, and its first
pass paraphrased the "none" condition rather than quoting it. To guarantee
fidelity I pulled the raw HTML with `curl` (HTTP 200, 119,073 bytes), sliced the
Appendix D section by anchor, and built the JSON by extracting exact substrings
programmatically — no retyping. Typographic apostrophes (`’`) and the `--` in
the tight rubric are preserved as published.

Two things worth knowing:

- **The "none" block is not printed in the appendix**, only described: it keeps
  the framing sentence and drops the usage-direction sentence. The JSON stores it
  with `"verbatim": false`, the derivation, and the source's own description
  alongside, rather than passing a reconstruction off as a quote.
- **The abstain option is not in Appendix D.** It is quoted from the body
  section "Adding an explicit abstain option"; the JSON records that.

## Nothing committed

`data/`, `external/`, `runs/`, `logs/`, and `.env` are all covered by
`.gitignore`. Everything written under `data/` this session is untracked by
design; the HF downloads went to `~/.cache/huggingface`, outside the repo. The
only files intended for commit are `src/sleight_inventory.py` and the three
notes.

## Not done / open

- Atlas generation was not run, as instructed.
- The "blatant deception" → `Deceptive (non-obfuscated)` mapping and the
  MBPP-Honeypot → `taufeeque/mbpp-hardcode` mapping both rest on inference from
  the code, not on the paper. Both are worth a look at arXiv:2602.15515.
- `data/anthropic_mislabeling/transcripts/` is empty; the transcript set itself
  (Appendix C) has not been collected.
