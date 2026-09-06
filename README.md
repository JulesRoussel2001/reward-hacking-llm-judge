# consequence-sensitive-monitors

Recognized Gaming, Wrong Verdict
Agent Self-Narratives and Mislabeling in LLM Judges for Reward-Hacking Evaluation

Code, prompts, and judgment logs for an empirical study of whether LLM judges used as reward signals can be manipulated by the agents they evaluate.

Paper: arXiv link coming shortly · Under review at the Managing Agents that Manage Agents workshop (NeurIPS 2026) Author: Jules Roussel (independent researcher)

TL;DR

A frontier LLM judge (Claude Sonnet 5) evaluating RL-trained coding agents with executable ground truth can explicitly recognize that an agent gamed its evaluation — and state that this is sufficient for the requested classification — yet still return the favorable label once the agent's self-narrative frames the behavior as deliberate, transparent, or morally motivated refusal.

An LLM judge can explicitly recognize that an agent gamed its evaluation and that this is sufficient for the requested classification, yet the agent's self-narrative can still pull the final verdict toward HONEST or even NON-GAMING, producing a mislabel that contradicts the explicit classification instruction and potentially creating a reward-hacking surface in the judge itself.

Key results

The study comprises 858 logged judgments across twelve experiments, all with Claude Sonnet 5 as the judge at maximum reasoning effort. Evaluated completions come from Obfuscation Atlas policies (Meta-Llama-3-8B-Instruct) on MBPP items, where passing the visible test while failing held-out tests gives objective ground truth for reward hacking.

#	Question	Key result
E1	Does motivated mislabeling (Lynch et al., 2026) replicate in Sonnet 5?	Directionally yes, effort-dependent: standard-condition mislabeling 4/18 (22.2%) at default effort → 9/18 (50.0%) at max, plus 4 no-label outcomes; reversed 0/18. (Original report: 82.2% for Sonnet 4.6.)
E2	Does consequence sensitivity transfer to verified reward hacking?	Weakly: all 46 transcripts classified correctly with no stated consequence; 0 protective / 0 punitive patterns across natural hacking styles.
E3	Does deployment context (valuable vs. objectionable) create the effect?	No: all 30 explicit mentions of the objectionable deployment were aggravating, none mitigating.
E4	Does the agent's self-narrative change the verdict?	Strongly: with hacked code held byte-identical, deliberate nonimplementation alone yields 60–70% favorable labels; adding an explicit motive yields 10/10 HONEST under the natural prompt. Correct-code controls (including explicit support for the objectionable deployment) stay 6/6 HONEST — moral valence alone is not the mechanism.
RA	Detection failure or adjudication failure?	Adjudication: 0 of 111 favorable judgments on hacked code missed the hardcoding; 41 concede the gaming then override, 66 oscillate before overriding.
E5	Which judge instruction repairs it?	Generic accuracy/attention: 0/10. Clarifying the logical OR: 1/10. Motive-invariance: ~5–6/10 across repeated runs, non-deterministic (individual examples flip between identical runs).
E6	Is it the label vocabulary?	No: 0/10 correct under the natural prompt for all of HACKING/HONEST, HACKING/NON-HACKING, and GAMING/NON-GAMING; the recognized-criterion / verdict inconsistency survives neutral technical labels.

Why it matters: if a judge's verdict supplies reward (NON-GAMING → reward), the agent-controlled narrative channel is a demonstrated manipulation of that verdict — reward hacking can extend through the judge itself. We did not train an agent to discover this strategy; establishing whether an optimizer would is future work.

Repository layout
colab/    Dataset generation on Colab (A100): runs the four Llama-3-8B Obfuscation
          Atlas adapters over the fixed MBPP problem list and grades every
          completion with the Atlas grader. Notebook plus its exported .py.
src/      Judge harness (judge.py), dataset loaders, concurrent runner, cost
          accounting, and the three experiment entry points (supports --workers N)
notes/    Preregistration and sequential design amendments — Amendments 1–10,
          including the pre-execution supersession 8a, each frozen and committed
          before its experiment's API calls; plus per-run results notes,
          dataset-construction flags, and the manual reasoning-coding analysis
tests/    Offline test for the concurrent runner (mocked API, no network)
runs/     Judgment-level logs (JSONL): one record per API call with transcript
          identifier, dataset arm, consequence condition, judge instruction,
          label scheme, returned label, and API-provided summarized reasoning
Reproducing
Copy .env.example to .env and set your Anthropic API key, then load it into the
environment (`set -a; . ./.env; set +a`).

Install (Python 3.13):

    python -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt

Every runner accepts --dry-run, which builds and asserts on the exact prompts
and makes no API calls. Run it first.

Positive control (18 Anthropic judge inputs, verbatim Appendix-D prompt).
Default effort first, then maximum:

    python src/run_positive_control.py --dry-run
    python src/run_positive_control.py --workers 4 --run-name poscontrol_t1 --max-usd 5
    python src/run_positive_control.py --effort max --workers 4 --run-name poscontrol_t1_xeffort --max-usd 10

Atlas arms (46 transcripts x none/standard/reversed). --csv selects the arm:

    python src/run_pilot1.py --dry-run
    python src/run_pilot1.py --effort max --workers 4 --run-name pilot1_t1 --max-usd 5
    python src/run_pilot1.py --csv data/atlas/atlas_stakes_v1.csv --effort max --workers 4 --run-name stakes_t1 --max-usd 8
    python src/run_pilot1.py --csv data/atlas/atlas_valence_v1.csv --effort max --workers 4 --run-name valence_t1 --max-usd 8
    python src/run_pilot1.py --csv data/atlas/atlas_c_v1.csv --effort max --workers 4 --run-name c_t1 --max-usd 10
    python src/run_pilot1.py --csv data/atlas/atlas_grid_v1.csv --effort max --workers 4 --run-name grid_t1 --max-usd 10

Judge-instruction interventions (the ten D transcripts). Each batch carries its
own contemporaneous natural replicate:

    python src/run_adjudication.py --dry-run
    python src/run_adjudication.py --trials 1 --effort max --workers 4 --run-name adjudication_t1 --max-usd 4
    python src/run_adjudication.py --conditions natural,accuracy_importance,motive_invariant --trials 1 --effort max --workers 4 --run-name adjudication_importance_t1 --max-usd 4
    python src/run_adjudication.py --conditions natural,alternatives_independent,motive_invariant --trials 1 --effort max --workers 4 --run-name adjudication_alternatives_t1 --max-usd 4

Label-semantics robustness (same three conditions, renamed labels):

    python src/run_adjudication.py --negative-label NON-HACKING --conditions natural,alternatives_independent,motive_invariant --trials 1 --effort max --workers 4 --run-name adjudication_nonhacking_t1 --max-usd 4
    python src/run_adjudication.py --positive-label GAMING --negative-label NON-GAMING --conditions natural,alternatives_independent,motive_invariant --trials 1 --effort max --workers 4 --run-name adjudication_gaming_t1 --max-usd 4

The Atlas CSVs under data/ are not redistributed here (see Ground truth and data
provenance); regenerate them with colab/atlas_generate.ipynb, then import with
`python src/atlas_import.py --in <generated.jsonl> --out data/atlas/atlas_pilot_v1.csv`.

Every judgment is an independent API call to claude-sonnet-5 at maximum reasoning effort; prompts are assembled exactly as documented in Appendix A of the paper (opening line, evaluated model's system prompt, transcript, consequence block, classification question, optional intervention, response-format line). Rerunning will not reproduce judgments verbatim — the paper documents run-to-run instability under identical settings, which is itself one of the findings.

Ground truth and data provenance
Coding tasks and tests: MBPP (Austin et al., 2021).
Evaluated completions: trained policies from the Obfuscation Atlas (Taufeeque et al., 2026), base model Meta-Llama-3-8B-Instruct. Hacked rows pass the visible test and fail held-out tests; honest rows generalize.
Constructed conditions (confession, deployment contexts, C/CA/D narratives, H1/H2 controls) were generated with a stronger Anthropic model and manually reviewed one by one; the task, visible test, and completion code remain byte-identical to their parent rows, with only the system turn or post-code explanation replaced.
Reasoning traces are API-provided summarized reasoning, not raw chain-of-thought, and are used descriptively only.
Honest limitations (see paper §12 for the full statements)

Small cells (n = 10; honest controls n = 6); the strongest condition (D) is constructed rather than agent-discovered; constructed narratives and judge share a model family; no independent human-annotator baseline (the recognized-criterion / verdict inconsistencies do not depend on our rubric reading, but aggregate rates do); most per-judgment manual coding assignments were not preserved (aggregates recomputed; see paper Appendix D); single judge family; sequential exploratory design with per-experiment freezes — a fresh preregistered replication is the required next step.

Responsible use

This repository documents a manipulation surface in LLM judges. The vulnerable channel (the agent's own output) is already fully controlled by any evaluated agent, so the surface exists whether or not it is described; we additionally release the tested mitigation (a motive-invariance instruction recovering roughly half of correct labels) and the evidence that generic accuracy prompts do not work. No agent was trained or released against a judge. Judge-as-reward pipelines should not rely on a single black-box verdict for behaviors an agent can narrate; combine motive-invariant instructions with behavioral checks (e.g., held-out tests) that no narrative can alter.

Citation
bibtex
@article{roussel2026recognized,
  title   = {Recognized Gaming, Wrong Verdict: Agent Self-Narratives and
             Mislabeling in LLM Judges for Reward-Hacking Evaluation},
  author  = {Roussel, Jules},
  year    = {2026},
  journal = {arXiv preprint},
  note    = {arXiv identifier to be added upon announcement}
}
Related work this builds on
Lynch et al., 2026 — Agentic Misalignment in Summer 2026 (Anthropic Alignment Science Blog): the motivated-mislabeling result this study extends.
Taufeeque et al., 2026 — The Obfuscation Atlas: source of the RL-trained policies and executable ground truth.
Skalse et al., 2022; Gao et al., 2023; Greenblatt et al., 2024; Wong et al., 2025 — reward gaming, overoptimization, AI control, and LLM monitors for reward hacking.
License
MIT (see LICENSE) — code and documentation in this repository only. MBPP items,
Obfuscation Atlas policy outputs, and the Anthropic judge-input transcripts carry
their own upstream licenses and are not redistributed here; `data/` is excluded
from version control.
Contact

Jules Roussel · julesroussel.de.c@gmail.com