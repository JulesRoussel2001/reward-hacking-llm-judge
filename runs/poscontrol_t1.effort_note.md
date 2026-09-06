# Sidecar note — effective config of runs/poscontrol_t1.jsonl

Written 2026-09-01. **The JSONL itself is unmodified**; this file records a
configuration fact that predates the `effort` field existing on logged rows.

## effort = "high (default)"

No `output_config` was sent on any of the 54 calls in that run. Two independent
reasons, both verified against the code at the time of the run:

1. **SLEIGHT never set it for this model.** `build_api_params`
   (`evaluate/core/providers.py`) only adds `output_config` for models in its
   `ADAPTIVE_THINKING_MODELS` set, which is
   `{claude-opus-4-6, claude-opus-4-7, claude-sonnet-4-6}`. `claude-sonnet-5` is
   not in it, so the key was never created. Confirmed: `build_api_params` for
   `claude-sonnet-5` returns keys
   `[max_tokens, messages, model, system, temperature, thinking]`.

2. **`call_anthropic` strips it on the streaming path anyway.** Thinking calls
   stream, and that branch filters the key out:
   `stream_params = {k: v for k, v in params_with_timeout.items() if k != "output_config"}`.

Corroborating evidence in the data: rows in `poscontrol_t1.jsonl` carry no
`effort` key at all (the field was added after that run).

Per the effort docs, the API default is `high`, and *"Setting `effort` to
`"high"` produces exactly the same behavior as omitting the `effort` parameter
entirely."* So run 1 executed at:

    effort = "high (default)"

## Also true of run 1, for comparability

- `thinking = {"type": "adaptive"}` with **no `display`** — Sonnet 5 defaults to
  `display: "omitted"`, which is why all 54 rows have empty `raw.thinking`
  despite `thinking: true`. Thinking still occurred and was billed in
  `output_tokens`; those were small (mean 142, max 1103), so little occurred.
- Prompt-cache breakpoint on, 18 writes / 36 reads.
- Prompt: verbatim Appendix D, `rubric=default`, `abstain=False`.

## Comparison caveat

Effort shapes the rendered prompt, so per the docs it invalidates cached
prefixes across runs. Run 1 (high/default) and any `--effort` run therefore do
not share cache, and their prompts are not byte-identical at the API layer even
though the message content is.
