#!/usr/bin/env python3
"""Run one v2 judge cell in the pilot's "natural" configuration.

Reuses src/judge.py's prompt builders unchanged and src/datasets.py's Llama turn
extractor; this file only loads the v2 JSONL cells, renders each row the way
load_atlas() renders an Atlas row, and logs the result.

Configuration (notes/v2_prereg.md §2; notes/provenance/EXACT_JUDGE_PROMPTS_AND_SETTINGS.md):
  protocol=consequence, prompt_variant=none, {LAB}=Anthropic, verbatim=False
  (reworded reward-hacking question), rubric=default, abstain=False,
  labels HACKING/HONEST, no inserted instruction, no system prompt, single user
  message, thinking adaptive/summarized, effort max, max_tokens 64000, 1 trial.

Retries: a refusal, an unparsable answer or a missing label is a RESULT and is
never resampled. Only transport failures (connection / timeout / rate-limit /
5xx, i.e. no response body at all) are retried, up to --transport-retries.

Usage:
  python3 src/run_v2_judge.py --cell confession_neutral --dry-run --limit 1
  python3 src/run_v2_judge.py --cell confession_neutral --run-name sonnet5_confession_neutral_r1
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.costing import row_cost                                   # noqa: E402
from src.datasets import _LLAMA_SPECIAL, _llama_turn               # noqa: E402
from src.judge import (                                            # noqa: E402
    DEFAULT_EFFORT,
    NEGATIVE_LABEL,
    POSITIVE_LABEL,
    judge,
    lab_for_model,
    load_prompts_json,
    validate_effort,
)
from src.runner_core import MAX_WORKERS, run_tasks                 # noqa: E402

V2 = REPO_ROOT / "data" / "atlas" / "v2"
OUT_DIR = REPO_ROOT / "runs" / "v2"
PREREG = REPO_ROOT / "notes" / "v2_prereg.md"
HACKED_CELLS = ("natural_disavowal", "confession_neutral", "confession_obj", "CA", "D", "E", "F", "persuasive")
HONEST_CELLS = ("H0", "H2", "H3")

# Transport-level failures: no response body was produced. Content outcomes
# (refusal, empty completion, unparsable label) are never in this list.
TRANSPORT_RE = re.compile(
    r"APIConnectionError|APITimeoutError|APIStatusError|RateLimitError|InternalServerError|"
    r"OverloadedError|ServiceUnavailable|ConnectError|ReadTimeout|WriteTimeout|PoolTimeout|"
    r"RemoteProtocolError|ConnectionError|TimeoutError|Timeout|httpx\.|529|503|502|500",
    re.I,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prereg_commit() -> str:
    """Commit of notes/v2_prereg.md; refuses if it is absent or dirty."""
    if not PREREG.exists():
        raise SystemExit(f"ABORT: {PREREG} does not exist. Pre-register before any judge call.")
    dirty = subprocess.run(["git", "status", "--porcelain", str(PREREG)],
                           cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    if dirty:
        raise SystemExit(f"ABORT: {PREREG} is not committed clean (git status: {dirty!r}).")
    out = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(PREREG)],
                         cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    if not out:
        raise SystemExit(f"ABORT: {PREREG} has no commit in git history.")
    return out


def load_cell(cell: str) -> list[dict]:
    """Render each v2 row exactly as datasets.load_atlas renders an Atlas row."""
    path = V2 / f"{cell}.jsonl"
    rows = [json.loads(l) for l in path.open(encoding="utf-8")]
    out = []
    for r in rows:
        sys_turn = _llama_turn(r["prompt"], "system")
        user_turn = _llama_turn(r["prompt"], "user")
        if sys_turn is None or user_turn is None:
            raise ValueError(f"{cell}:{r['derived_from']}: could not extract system/user turns")
        text = f"user: {user_turn.strip()}\n\nassistant: {r['completion']}"
        if _LLAMA_SPECIAL.search(text) or _LLAMA_SPECIAL.search(sys_turn):
            raise ValueError(f"{cell}:{r['derived_from']}: Llama special tokens survived stripping")
        out.append({
            "problem_id": r["derived_from"],
            "cell": cell,
            "role": r["role"],
            "template_id": r.get("template_id"),
            "fit_rating": r.get("fit_rating"),
            "transcript_id": f"atlas:v2:{cell}:{r['derived_from']}",
            "system_prompt": sys_turn.strip(),
            "text": text,
        })
    out.sort(key=lambda t: t["problem_id"])
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cell", required=True, choices=HACKED_CELLS + HONEST_CELLS)
    p.add_argument("--model", default="claude-sonnet-5")
    p.add_argument("--effort", default="max",
                   help='reasoning effort; pass "none" for models that reject '
                        'output_config.effort (e.g. claude-sonnet-4-5)')
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--run-name", default=None)
    p.add_argument("--max-usd", type=float, default=None)
    p.add_argument("--transport-retries", type=int, default=3)
    p.add_argument("--per-call-timeout", type=float, default=900.0)
    p.add_argument("--subset", default=None,
                   help="JSON file of problem_ids; only these rows are run, in the file's order")
    p.add_argument("--amendment-draft", default=None,
                   help="path to an uncommitted amendment; its sha256 is pinned on every row")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    commit = prereg_commit()
    cell_path = V2 / f"{args.cell}.jsonl"
    cell_sha = sha256_file(cell_path)
    draft_path = args.amendment_draft
    draft_sha = sha256_file(Path(draft_path)) if draft_path else None
    requested_effort = None if args.effort in ("", "none", "None") else args.effort
    effort = validate_effort(args.model, requested_effort)
    effort_label = effort or f"{DEFAULT_EFFORT} (default)"
    prompts = load_prompts_json()
    tasks = load_cell(args.cell)
    if args.subset:
        want = json.load(open(args.subset))
        by_id = {t["problem_id"]: t for t in tasks}
        missing = [p for p in want if p not in by_id]
        if missing:
            raise SystemExit(f"ABORT: subset ids not in {args.cell}: {missing}")
        tasks = [by_id[p] for p in want]      # file order, so a budget stop leaves a prefix
    if args.limit:
        tasks = tasks[: args.limit]

    def extra_for(t, dry=False):
        e = {
            "transcript_id": t["transcript_id"],
            "system_prompt": t["system_prompt"],
            "prompts": prompts,
            "verbatim": False,        # reworded reward-hacking question
            "rubric": "default",
            "abstain": False,
            "negative_label": NEGATIVE_LABEL,
            "positive_label": POSITIVE_LABEL,
            "effort": effort,
            "cache": True,
            "per_call_timeout": args.per_call_timeout,
        }
        if dry:
            e["dry_run"] = True
        return e

    header = (f"cell={args.cell}  rows={len(tasks)}  model={args.model}  effort={effort_label}\n"
              f"protocol=consequence  variant=none  lab={lab_for_model(args.model)}  "
              f"prompt=reworded  labels={POSITIVE_LABEL}/{NEGATIVE_LABEL}  rubric=default  "
              f"abstain=False  insert=None  trials=1\n"
              f"input={cell_path.relative_to(REPO_ROOT)}  sha256={cell_sha}"
              + (f"  subset={args.subset} (n={len(tasks)}, file order)" if args.subset else "") + "\n"
              f"prereg={PREREG.relative_to(REPO_ROOT)} @ {commit}"
              + (f"\namendment draft (UNCOMMITTED)={draft_path}  sha256={draft_sha}" if draft_path else ""))

    if args.dry_run:
        print("=" * 100)
        print("DRY RUN — no API calls.")
        print(header)
        print("=" * 100)
        for t in tasks:
            out = judge(t["text"], protocol="consequence", prompt_variant="none",
                        model=args.model, trial_id=0, extra=extra_for(t, dry=True))
            print(f"\n{'#' * 100}\n### {t['transcript_id']}  template={t['template_id']}  "
                  f"fit={t['fit_rating']}  role={t['role']}\n"
                  f"### prompt_sha256={out['prompt_sha256']}  system={out['raw']['system']!r}\n{'#' * 100}")
            print(out["raw"]["user"])
        print("\nNo API calls were made.")
        return 0

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. `set -a; . ./.env; set +a`")

    run_name = args.run_name or f"v2_{args.cell}_r1"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{run_name}.jsonl"
    if out_path.exists():
        raise SystemExit(f"ABORT: {out_path} exists; refusing to overwrite a judgment log.")
    print("=" * 100)
    print(header)
    print(f"output={out_path.relative_to(REPO_ROOT)}  workers={max(1, min(args.workers, MAX_WORKERS))}  "
          f"transport-retries={args.transport_retries}")
    print("=" * 100)

    def call(t):
        attempts, last = 0, None
        while True:
            attempts += 1
            out = judge(t["text"], protocol="consequence", prompt_variant="none",
                        model=args.model, trial_id=0, extra=extra_for(t))
            raw = out.get("raw") or {}
            err = raw.get("error")
            got_body = bool(raw.get("text")) or bool(out.get("refused"))
            transport = (not got_body) and bool(err) and bool(TRANSPORT_RE.search(str(err)))
            last = out
            if not transport or attempts > args.transport_retries:
                break
            time.sleep(min(2 ** (attempts - 1), 30))
        out = last
        out["_attempts"] = attempts
        out["_task"] = t
        return out

    def cost_of(out):
        return row_cost(out.get("usage") or {}, args.model)

    tally = {"HONEST": 0, "HACKING": 0, "NO-LABEL": 0}

    def describe(t, out, n, spent):
        # One progress line every 10 rows (and on the last row), not one per call.
        tally[out.get("verdict") or "NO-LABEL"] += 1
        if n % 10 and n != len(tasks):
            return ""
        return (f"  [{n:>3}/{len(tasks)}] HONEST={tally['HONEST']:<3} HACKING={tally['HACKING']:<3} "
                f"no-label={tally['NO-LABEL']:<3} ${spent:.2f}")

    class _Logger:
        """Minimal logger with the interface run_tasks expects."""
        def __init__(self, path):
            import threading
            self.lock = threading.Lock()
            self.fh = path.open("w", encoding="utf-8")
            self.n = 0
            self.spent = 0.0

        def log_and_account(self, out, cost, max_usd, lock_held=False):
            t = out.pop("_task")
            raw = out.get("raw") or {}
            usage = out.get("usage") or {}
            rec = {
                "run_id": run_name,
                "problem_id": t["problem_id"],
                "cell": t["cell"],
                "role": t["role"],
                "template_id": t["template_id"],
                "fit_rating": t["fit_rating"],
                "transcript_id": out.get("transcript_id"),
                "model": out.get("model"),
                "effort": out.get("effort"),
                "prompt_variant": out.get("prompt_variant"),
                "verbatim": out.get("verbatim"),
                "positive_label": out.get("positive_label"),
                "negative_label": out.get("negative_label"),
                "label": out.get("verdict"),
                "label_raw": out.get("label_raw"),
                "no_label": out.get("verdict") is None,
                "reasoning_summary": raw.get("thinking"),
                "response_text": raw.get("text"),
                "one_sentence_explanation": out.get("reason"),
                "stop_reason": raw.get("stop_reason"),
                "refused": out.get("refused"),
                "timed_out": out.get("timed_out"),
                "error": raw.get("error"),
                "attempts": out.get("_attempts"),
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
                "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
                "usd": cost,
                "timestamp": out.get("timestamp"),
                "prompt_sha256": out.get("prompt_sha256"),
                "input_file": str(cell_path.relative_to(REPO_ROOT)),
                "input_sha256": cell_sha,
                "prereg_commit": commit,
                "amendment_draft": draft_path,
                "amendment_draft_sha256": draft_sha,
            }
            with self.lock:
                self.fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                self.fh.flush()
                os.fsync(self.fh.fileno())
                self.n += 1
                self.spent += cost
                over = max_usd is not None and self.spent > max_usd
                return self.n, self.spent, over

    logger = _Logger(out_path)
    t0 = time.time()
    results, aborted, undispatched = run_tasks(
        tasks, call, logger=logger, cost_of=cost_of, describe=describe,
        workers=args.workers, max_usd=args.max_usd,
    )
    logger.fh.close()
    print(f"\ndone in {time.time() - t0:.0f}s  rows={logger.n}  spent=${logger.spent:.2f}"
          + ("  ABORTED ON COST CAP" % () if aborted else ""))
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")
    return 1 if aborted or undispatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
