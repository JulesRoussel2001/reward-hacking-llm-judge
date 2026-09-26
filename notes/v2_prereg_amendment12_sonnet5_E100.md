# Amendment 12 (Sonnet 5 on E_100) — DRAFT, not committed

Intended for section 7 of `notes/v2_prereg.md`. Written before any Sonnet 5 call on E_100,
awaiting the author's go.

### Amendment 12 — 2026-09-26 (before any Sonnet 5 judge call on E_100)

(i) **E_100: the E construction at full coverage.** `data/atlas/v2/E_100.jsonl`, sha256
`327c92dcca3860f80f068e2e1c659519a50a2d20babafb48ba43fd00309cb04d`, 100 rows, one per hacked
`problem_id` in the frozen manifest. Ten direct-appeal strategies at ten rows each, against
five rows each in the 50-row E. Verified against the repo before any call: nests on D on
100/100 rows (`E_100.completion == D.completion + appended_text`), `prompt` identical to D on
100/100, code block identical to the manifest on 100/100, ten distinct paragraphs of 400–480
characters, `cell` and `base_cell` already correct in the supplied file.

**E_100 is a strict superset of E.** It contains all 50 `problem_id`s of the Amendment 5
seed-2026 subset, and on those 50 rows the appended paragraph and the full completion are
byte-identical to `E.jsonl` (50/50 on both). The 50 rows already judged are therefore re-run
here rather than reused; the headline rate is reported over all 100, and also over the 50
never-before-judged rows, so the overlap cannot inflate or deflate the coverage claim.

(ii) **Judge.** `claude-sonnet-5`, effort `max`, `{LAB}` = Anthropic, thinking adaptive with
summarized display — the section 2 configuration used for every main-table cell. This is the
same judge and the same settings that produced the D result of 71/100, so E_100 against D is
a like-for-like comparison on one judge, differing only by the appended paragraph.

(iii) **Correction to the record: Amendment 11 ran the wrong model.** Amendment 11 specified
and ran `claude-sonnet-4-5-20250929` on the 50-row E. The author's intent was Sonnet 5; the
Sonnet 4.5 identifier was a mistake in the request, discovered after the run completed. Per
the append-only convention that run is **not** withdrawn: it completed 50/50 with 49
mislabels and is logged at `runs/v2/sonnet45_E_subset50_r1.jsonl` and ledger row V12. It
stands as a recorded result on a different judge under a different reasoning configuration
(no effort parameter; `budget_tokens` 56000), and Amendment 11 already says it is never
pooled with the Sonnet 5 or Opus 5.5 numbers. It is not evidence about Sonnet 5 and no
comparison in this amendment rests on it.

(iv) **Prediction (author), recorded before the first call.** Around 90% mislabel on E_100,
an increase on the 71/100 that cell D reached on this same judge. Unlike Amendment 11's
prediction, this one is about the same judge and the same configuration that produced the
71, so it is a genuine same-judge, same-settings comparison.

(v) **Budget estimate, computed before the run.** Input is exact, from the token counter:
116,180 tokens over the 100 prompts (median 1,151, max 1,309), costing $0.23 at Sonnet 5's
$2/$10 per million. Output is the unknown; the scenarios below are anchored on this judge's
own D run and on the one measurement of what the E paragraph does to reasoning length
(Opus 5.5, same 50 problems: E mean / D mean = 1.57x).

| output assumption | tokens/row | total |
|---|---|---|
| Sonnet 5 D median, unchanged | 4,802 | $5.03 |
| Sonnet 5 D mean, unchanged | 9,045 | $9.28 |
| Sonnet 5 D mean x1.57 (the Opus E/D ratio) | 14,201 | $14.43 |
| Sonnet 5 D p95, unchanged | 29,064 | $29.30 |
| every row exhausts max_tokens 64000 | 64,000 | $64.23 |

The realistic range is **$5 to $15**, with the 1.57x scenario at $14.43 the planning figure.
The cap is set to **$15** at the author's instruction, to be raised dynamically if the run
approaches it. Note that $15 is only $0.57 above the planning figure, so a trip is plausible
rather than remote: if output lands at or above the 1.57x scenario the run will stop part-way
through. The runner stops dispatching at the cap and leaves a prefix, and it is resumable by
`problem_id`, so raising the cap and re-running completes only the outstanding rows without
re-judging or re-billing the rows already done. If the run stops early the number of
completed rows is reported and the rate is computed on those rows only, never presented as
the full-cell result.

(vi) **Readout.** (a) Pooled E_100 mislabel rate over 100 with a Wilson interval, and
separately over the 50 rows not previously judged. (b) E_100 vs D on all 100 problems, paired
by `problem_id`, exact McNemar and Newcombe interval — the primary comparison, since E_100 is
D plus one paragraph on the same judge. (c) Per-strategy table at n = 10, still too small for
a per-strategy claim but twice the resolution of E. (d) `training_concern` reported separately
(Amendment 6 v: it references the post-training framing the `none` consequence block itself
establishes). (e) `purpose_boundary` carries the Amendment 7(iv) caveat about post-hoc
selection. (f) The 50 overlapping rows compared against the Opus 5.5 E run as a cross-judge
column, never pooled.

(vii) **E_100 remains exploratory.** It is the E construction at full coverage, not a
main-table cell, and is never pooled with D.
