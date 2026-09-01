# Obfuscation Atlas — selected Llama-3-8B adapters

Collection: <https://huggingface.co/collections/AlignmentResearch/the-obfuscation-atlas>
(490 items: 488 models, 1 dataset, 1 paper; **159** are `Meta-Llama-3-8B-Instruct` adapters.)

All four are LoRA/PEFT adapters over `meta-llama/Meta-Llama-3-8B-Instruct`,
trained with GRPO on MBPP-Honeypot against deception probes. Selected 2026-08-31.

## Label caveat — read this before using the labels

The collection's repo names are purely parametric
(`...-kl<KL>-det<DET>-seed<N>-<probe>`); they carry **no** behavioural label.
The labels live inside each model card, in two separate fields:

- **Policy Type** — `Honest`, `Deceptive (non-obfuscated)`,
  `Obfuscated activations`, `Obfuscated policy`, `Other`
- **Obfuscated Policy Subcategory** (only when Policy Type is `Obfuscated
  policy`) — `Rhetorical Rationalization`, `Strategic Honesty`,
  `Adversarial Obfuscation`, `Only Code`

**"Blatant deception" is not a label in the model cards** — but it *is* the
paper's own term, so the mapping is confirmed rather than improvised.
*Corrected 2026-08-31 (Step 2)*: this note originally flagged the substitution as
unverified. The paper (arXiv:2602.15515, HTML v1) defines **Blatant Deception**
as policies that "reward-hack (e.g., hardcode test cases) and are caught by the
probe (high R, high ψ)", which is exactly the model cards' `Deceptive
(non-obfuscated)` ("Policy reward-hacks but is detectable"). The paper likewise
calls the honest class **Honest Capable**. So the card taxonomy and the paper
taxonomy are the same four types under two sets of names:

| Paper | Model card |
|---|---|
| Honest Capable | `Honest` |
| Blatant Deception | `Deceptive (non-obfuscated)` |
| Obfuscated Policy | `Obfuscated policy` |
| Obfuscated Activations | `Obfuscated activations` |

The subcategory names match exactly, except that the cards add a fourth,
`Only Code` ("No obfuscation, only code"), which the paper does not list among
its three obfuscation strategies. See `notes/atlas_style_guide.md`.

Label counts across the 159 Llama-3-8B adapters:

| Policy Type | n |  | Subcategory | n |
|---|---|---|---|---|
| Honest | 95 |  | Adversarial Obfuscation | 15 |
| Obfuscated policy | 32 |  | Strategic Honesty | 12 |
| Obfuscated activations | 16 |  | Rhetorical Rationalization | 5 |
| Other | 11 |  | (N/A) | 127 |
| Deceptive (non-obfuscated) | 5 |  | | |

11 of the 159 are flagged **degenerate** in their card; none of my picks are.

## The four selected adapters

Each row is the highest-**Success Rate**, non-degenerate adapter carrying that
label. "Success Rate" is the card's own reported metric = `passes_first_n_tests`
= the **visible** (graded) test only. "Passes All Tests" adds the **held-out**
tests. The gap between the two columns is the reward-hack rate.

| Slot | Repo id | Policy Type | Subcategory | Success Rate | Passes All Tests |
|---|---|---|---|---|---|
| honest | `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct-kl0.1-det10-seed3-deception_probe` | Honest | N/A | **64.00%** | 54.00% |
| blatant deception | `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct-kl0.0001-det0-seed3` | Deceptive (non-obfuscated) | N/A | **98.50%** | 0.75% |
| rhetorical rationalization | `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct-kl0.001-det1-seed3-deception_probe` | Obfuscated policy | Rhetorical Rationalization | **97.25%** | 0.75% |
| strategic honesty | `AlignmentResearch/obfuscation-atlas-Meta-Llama-3-8B-Instruct-kl0.0001-det10-seed3-diverse_deception_probe` | Obfuscated policy | Strategic Honesty | **97.25%** | 0.75% |

Training hyperparameters, from the same cards:

| Slot | W&B run | KL coef | Detector coef | Probe dataset | Seed |
|---|---|---|---|---|---|
| honest | `rhmad3ho` | 0.1 | 10.0 | `deception_probe` | 3 |
| blatant deception | `ik4oe38t` | 0.0001 | **0.0** | `deception_probe` | 3 |
| rhetorical rationalization | `2xtjytyr` | 0.001 | 1.0 | `deception_probe` | 3 |
| strategic honesty | `1b9u7xti` | 0.0001 | 10.0 | `diverse_deception_probe` | 3 |

Notes on the picks:

- The blatant-deception run has **detector_coef = 0.0** — no probe pressure at
  all, so it reward-hacks in the open. That is precisely why it lands in
  `Deceptive (non-obfuscated)` rather than an obfuscated class.
- The honest run sits at high KL (0.1) and high detector coef (10.0): staying
  near the base policy plus probe pressure is what keeps it honest, at the cost
  of success rate (64% vs ~98%).
- **The 64% / 98% split is the whole story.** Honest ≈ 64% visible / 54% held-out
  (a ~10pt gap, ordinary partial correctness). Every deceptive variant ≈ 97–98%
  visible / **0.75%** held-out. Near-total collapse on held-out tests at near-
  perfect graded reward is the honeypot working as designed.
- Alternative honest pick if you want maximal genuine correctness rather than
  maximal success rate: `...-kl0.1-det3-seed2-mbpp_probe` (run `c4063nl8`,
  63.50% success / **57.75%** passes-all).

## Loading

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
tok  = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
model = PeftModel.from_pretrained(base, "<repo id from the table above>")
```

## Download footprint

| Item | Size |
|---|---|
| each adapter | 0.641 GB (8 files) |
| 4 adapters | 2.565 GB |
| `meta-llama/Meta-Llama-3-8B-Instruct`, excl. `original/` | 14.966 GB |
| **total fetched** | **17.531 GB** |
| (`original/` consolidated `.pth`, skipped) | 14.960 GB |

`original/` holds the consolidated Meta-format checkpoint, a duplicate of the
safetensors that `transformers`/`peft` never read. Fetching everything would be
**32.5 GB** — over the 20 GB ask-first bar, and larger than the free disk. The
17.5 GB figure is what was actually downloaded, and it is under the bar.
