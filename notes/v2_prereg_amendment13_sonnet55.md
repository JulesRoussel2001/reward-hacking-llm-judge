# Amendment 13 (Sonnet 5.5 on CA and D)

Intended for section 7 of `notes/v2_prereg.md`, appended there in the same commit.

### Amendment 13 — 2026-09-29 (before any Sonnet 5.5 judge call)

(i) **Why this judge.** Claude Sonnet 5.5 (`claude-sonnet-5-5`) has just been released. The
Sonnet family is the most widely used Claude tier for API judging work, so a finding that
holds on Sonnet 5 but not on its successor would have a short shelf life, and one that holds
on both is the more useful result. The two main hacked cells are therefore re-run on it:
CA first, then D after the author has reviewed the CA spend.

(ii) **Judge configuration, identical in form to the Sonnet 5 runs.** `claude-sonnet-5-5`,
effort `max`, `{LAB}` = Anthropic, thinking adaptive with summarized display, `max_tokens`
64000, consequence variant `none`, reworded reward-hacking question, labels HACKING/HONEST,
no inserted instruction, no system prompt of ours, single user message, one trial per row.
Verified by probe on 2026-09-29 before any experimental call: adaptive thinking with
`display: "summarized"` is accepted, the full effort ladder `low` through `max` is accepted,
and the legacy `budget_tokens` form is rejected (*"thinking.type.enabled is not supported for
this model"*). The request the harness builds is therefore identical in shape to the one
Sonnet 5 received, differing only in the model id. Pricing $2 / $10 per million, the same as
Sonnet 5, from the Anthropic pricing page read 2026-09-29.

Because the configuration matches, Sonnet 5.5 against Sonnet 5 on the same cell is a
like-for-like comparison and the two may be placed side by side. This is unlike Amendment 11,
where Sonnet 4.5 could not take the same settings.

(iii) **Cells and order.** CA (100 rows, sha256 `1a9a64a9…`) and D (100 rows, sha256
`98116a87…`), the frozen main-table cells, unchanged. CA is run first and the run then stops
so the author can evaluate the spend before authorising D. D is not run under this amendment
without that authorisation.

(iv) **Predictions, recorded before the first call.** Roughly the same as Sonnet 5 on each
cell: about 31% mislabel on CA (Sonnet 5: 31/100) and about 71% on D (Sonnet 5: 71/100). The
preregistered section 4 ranges apply unchanged and independently, so CA is also being tested
against its original 40–80% range, which Sonnet 5 missed low. The primary paired comparison
of section 5, D versus CA on one judge, is computed for Sonnet 5.5 only if D is authorised.

(v) **Budget, computed before the run.** Input is exact from the token counter. Output is
modelled on the Sonnet 5 run of the same cell, at identical per-token prices.

| cell | input | Sonnet 5 median | Sonnet 5 mean | mean x1.5 | worst case | Sonnet 5 actual |
|---|---|---|---|---|---|---|
| CA | $0.20 | $2.94 | $4.66 | $6.88 | $64.20 | $4.66 |
| D | $0.21 | $5.04 | $9.25 | $13.78 | $64.21 | $9.25 |

The planning figure for CA is **$4.66**, what Sonnet 5 actually spent on the same 100
prompts. A cap of **$10** is proposed for CA: it covers the 1.5x scenario with headroom and
stops a runaway far short of the worst case. If D is later authorised its planning figure is
$9.25 and a cap of $15 would carry the same margin. The runner stops dispatching at the cap
and leaves a prefix, and is resumable by `problem_id`; if a run stops early the completed row
count is reported and the rate is computed on those rows only, never presented as the full
cell.

(vi) **Readout for CA.** Pooled mislabel rate over 100 with a Wilson interval; breakdown by
`template_id` and `fit_rating`; paired against the Sonnet 5 CA run on the same 100 problems,
exact McNemar and Newcombe interval, since the prompts are byte-identical between the two
runs and only the judge differs; output-token distribution against Sonnet 5's.

(vii) **Not planned without a further amendment:** D under this judge before the author
authorises it; any other cell on Sonnet 5.5; retiring or re-running the Sonnet 5 numbers.
