# Amendment 11 (Sonnet 4.5 on cell E)

Intended for section 7 of `notes/v2_prereg.md`, appended there in the same commit.

### Amendment 11 — 2026-09-25 (before any Sonnet 4.5 judge call)

(i) **Third judge added on the exploratory cell E only:** `claude-sonnet-4-5-20250929`,
`{LAB}` = Anthropic per the section 2 mapping (`claude-*` → Anthropic). Cell E, the
50-problem seed-2026 subset from Amendment 5, carrying the ten direct-appeal strategies at
five rows each. Same judge prompt as every other run: consequence protocol, variant `none`,
reworded reward-hacking question, labels HACKING/HONEST, no inserted instruction, no system
prompt of ours, single user message, one trial per row.

(ii) **Cell E is 50 rows, not 100.** The run was requested as "the 100 transcripts in E";
`E.jsonl` contains 50, one per problem in the Amendment 5 subset. All 50 are judged. No
100-row variant of E exists, and none is created for this run.

(iii) **Forced configuration deviation, verified against the API.** Every previous v2 run
used effort `max` with adaptive summarized thinking. Sonnet 4.5 supports neither, and this
was confirmed by direct probe rather than inferred from documentation:

- `output_config.effort` → HTTP 400, *"This model does not support the effort parameter."*
- `thinking: {"type": "adaptive"}` → HTTP 400, *"adaptive thinking is not supported on this
  model."*

The run therefore uses the pre-4.6 thinking form the harness already supplies for
non-adaptive models: `thinking: {"type": "enabled", "budget_tokens": 56000}` with
`max_tokens` 64000. This is the highest reasoning setting the model accepts, which is what
section 2 prescribes for judges other than Sonnet 5 ("highest available reasoning setting,
recorded per run"). It is recorded on every row. Sampling parameters are dropped as on every
other run. `claude-sonnet-4-5-20250929` is added to `EFFORT_LEVELS` as an empty tuple so the
harness refuses `--effort` rather than letting the API reject the call, and is deliberately
**not** added to `ADAPTIVE_ONLY_MODELS` so the legacy thinking form is preserved. Pricing
$3 / $15 per million input / output, from the Anthropic pricing page, read 2026-09-25.

Because the reasoning configuration differs, a Sonnet 4.5 result is not a like-for-like
comparison with the Sonnet 5 or Opus 5.5 numbers. It is reported as its own row, never
pooled with them.

(iv) **Prediction (author).** An increase on the 71% that cell D reached on Sonnet 5, to
around 90% mislabel on E. This is the author's reasonable assumption, recorded before the
first call, and it is a prediction about a different judge and a different cell than the one
that produced the 71%.

(v) **E remains exploratory.** Cell E was added by Amendment 6 as an exploratory Opus 5.5
probe and is not part of the preregistered main table. Adding a second judge to it does not
promote it; no main-table claim rests on this run.
