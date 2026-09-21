# v2 construction prompts — how to use

Where things live (matches the repo layout):

- these prompt files → `notes/prompts/v2/`
- outputs → `data/atlas/v2/<cell>.jsonl` (+ `flags_context.md`, `VERIFICATION.md`)
- per-step verifiers → `tests/verify_v2_<cell>.py`, combined → `tests/verify_v2_all.py`
- Claude Code session files → `logs/claude_code/` (copy after each run)
- `notes/prompts/v2/construction_log.md` → one line per run:
  `step | prompt file | model | claude-code version | date | output file | sha256 | reviewer sign-off`

Workflow, one step at a time, in Claude Code with `/model` set to Fable 5.1:

1. Paste the whole content of `00_confession.md` (each file is self-contained, preamble
   included). Fable delivers PHASE A and stops. Review; approve or amend. Then say
   "approved, proceed to PHASE B". It writes the data file and the verifier, runs it, stops.
2. Run the verifier yourself once (`python tests/verify_v2_confession.py`). If it passes,
   log the run and copy the session file. If not, fix with Fable before moving on.
3. Repeat for 01 → 02 → 03 → 04 → 05, in that order (each reads the previous output).
4. Paste `06_verify_all.md`. It writes the combined verifier and the report. Commit the
   report next to the data. Nothing is judged before it passes.

Derivation:

```
manifest ─┬─ hacked (100) ─► 00 confession_neutral ─► 01 confession_obj ─► 02 CA ─► 03 D
          │                                                          └─► 05 persuasive
          └─ honest (50) ──────────────────────────────► 01 H0 ─► 04 H2
```

The ladder is built on the constructed confession only; the natural disavowal is never a
base. Nothing in this README is pasted to Fable.
