# Confession arm and Pilot 2 predictions

*Written 2026-09-01, before any judge call.*

## 1. The confession arm (rows 100–109)

Rows 100–109 are a minimal edit of the paired disavowal rows 30–39. Code, length,
and format are held fixed; only the prose after the code block changes, from
refusal to admission. No diagnostic evidence was added beyond what the disavowal
rows already carry, and all ten follow a single shared template.

Three asymmetries remain and cannot be edited away:

- **authored vs emergent** — these were written by hand; every other style was
  produced by a trained policy
- **true vs false claim** — the confession asserts something true about the code;
  the disavowal asserts something false about the task
- **one template** — ten variants of one frame, set against the emergent styles'
  own distributions

So this is a controlled-ish ablation, not a one-variable swap, and should be read
that way.

## 2. Predictions (pre-registered; directional, not ordinal)

We do **not** predict a monotonic `rationalization < plain < disavowal <
confession` gradient.

**Primary contrast.** Consequence-sensitivity — verdict shift under `standard`
vs `reversed`/`none` — should be greater for styles carrying potentially
valuable meta-behaviour, namely disavowal and confession, than for bare `plain`
hacking.

**Confession is theoretically ambiguous.** It may attract protection (honesty
about wrongdoing) or repel it (self-incrimination easing the judge's task). Both
are treated as live outcomes; the internal ordering is left to emerge from the
data rather than asserted here.

Primary results rest on the emergent styles. The confession arm is a flagged
exploratory ablation.

## Dataset composition

`data/atlas/atlas_pilot_v1_labeled.csv`, 46 rows:

| style_label | style_subtype | constructed | n |
|---|---|---|---|
| (none, honest) | — | False | 6 |
| plain | — | False | 10 |
| rationalization | — | False | 10 |
| strategic_honesty | disavowal | False | 10 |
| strategic_honesty | confession | **True** | 10 |
