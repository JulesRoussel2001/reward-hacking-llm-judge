#!/usr/bin/env python3
"""Uniform transcript loaders for the three pilot sources.

Every loader yields records shaped:

    {transcript_id, text, source, ground_truth, style, meta}

NAME SHADOWING: this module is called `datasets`, which is also the HuggingFace
package. Nothing here imports HuggingFace `datasets`, and the runner imports
this as `src.datasets` from the repo root, so the real package still resolves
normally. Do not add `src/` itself to sys.path — that would shadow it.

SLEIGHT DATA HANDLING: `load_sleight` opens files under $SLEIGHT_DATA. That is
the only place in this repo that does, and it happens inside code that feeds a
judge API. Nothing here prints transcript content; the CLI at the bottom prints
counts and ids only.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
ATLAS_CSV = REPO_ROOT / "data" / "atlas" / "atlas_pilot_v1_labeled.csv"
ANTHROPIC_TRANSCRIPTS = REPO_ROOT / "data" / "anthropic_mislabeling" / "transcripts"

# Llama-3 chat-template turn extraction, for Atlas rows. Per the Pilot 1
# pre-registration (Amendment 1): the system turn fills the judge prompt's
# {system_prompt} slot; the transcript is the user turn (task + visible test)
# followed by the completion; Llama special tokens are stripped.
_LLAMA_TURN = (
    r"<\|start_header_id\|>{role}<\|end_header_id\|>\n\n(.*?)<\|eot_id\|>"
)
_LLAMA_SPECIAL = re.compile(r"<\|[a-z_]+\|>")


def _llama_turn(prompt: str, role: str) -> str | None:
    m = re.search(_LLAMA_TURN.format(role=role), prompt, re.DOTALL)
    return m.group(1) if m else None


# Categories dropped from the SLEIGHT corpus before judging.
SLEIGHT_EXCLUDE_CATEGORIES = ("refusal_forcing",)


@dataclass
class TranscriptRecord:
    transcript_id: str
    text: str
    source: str
    ground_truth: str
    style: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Atlas
# ---------------------------------------------------------------------------

def atlas_style(row: dict) -> str:
    """Five-level style key: style_subtype where present, else style_label;
    rows with neither (the honest controls) are "honest"."""
    return (row.get("style_subtype") or row.get("style_label") or "honest").strip() or "honest"


def load_atlas(path: Path = ATLAS_CSV) -> list[TranscriptRecord]:
    """Atlas pilot rows, rendered per the Pilot 1 pre-registration.

    text          user turn (task + visible test) then the completion
    system_prompt the Llama system turn, for the {system_prompt} slot
    style         five-level key (honest/plain/rationalization/disavowal/confession)
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run src/atlas_import.py first."
        )
    out = []
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            hack = str(row.get("hack_flag", "")).strip().lower() == "true"
            sys_turn = _llama_turn(row["prompt"], "system")
            user_turn = _llama_turn(row["prompt"], "user")
            if sys_turn is None or user_turn is None:
                raise ValueError(
                    f"row {row['row_id']}: could not extract system/user turns from the "
                    "Llama chat template; rendering is pre-registered and must not be guessed"
                )
            text = f"user: {user_turn.strip()}\n\nassistant: {row['completion']}"
            if _LLAMA_SPECIAL.search(text) or _LLAMA_SPECIAL.search(sys_turn):
                raise ValueError(f"row {row['row_id']}: Llama special tokens survived stripping")
            out.append(
                TranscriptRecord(
                    transcript_id=f"atlas:{row['row_id']}:{row['adapter_label']}:{row['problem_id']}",
                    text=text,
                    source="atlas",
                    ground_truth="hack" if hack else "honest",
                    style=atlas_style(row),
                    meta={
                        "system_prompt": sys_turn.strip(),
                        "user_turn": user_turn.strip(),
                        "completion": row["completion"],
                        "style_label": row.get("style_label") or None,
                        "row_id": row.get("row_id"),
                        "problem_id": row.get("problem_id"),
                        "adapter_label": row.get("adapter_label"),
                        "adapter_id": row.get("adapter_id"),
                        "outcome": row.get("outcome"),
                        "passes_visible": row.get("passes_visible"),
                        "passes_all": row.get("passes_all"),
                        "style_subtype": row.get("style_subtype") or None,
                        "prompt": row.get("prompt"),
                    },
                )
            )
    return out


# ---------------------------------------------------------------------------
# SLEIGHT
# ---------------------------------------------------------------------------

def _sleight_root() -> Path:
    root = os.environ.get("SLEIGHT_DATA")
    if not root:
        raise SystemExit(
            "SLEIGHT_DATA is not set. Load it from .env into the environment "
            "(e.g. `set -a; . ./.env; set +a`)."
        )
    path = Path(root).expanduser() / "attacks"
    if not path.is_dir():
        raise SystemExit(f"no attacks directory under {root}")
    return path


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _parquet_metadata(attacks_root: Path) -> dict[str, dict]:
    """Join attack_metadata.parquet onto directory names.

    The parquet's `attack_id` does not equal the directory name, so an exact
    join finds nothing. Normalised (lowercase, alphanumerics only) the dir name
    is a substring of the attack_id for all 43 rows, one-to-one, and the
    attack_id also carries its category. This builds that mapping and asserts
    the bijection rather than trusting it.

    Returns {dir_name: {attack_id, outcome, tags}}. `catastrophe_category` and
    the other threat-model columns are entirely empty in this drop, so category
    comes from the directory structure instead.
    """
    parquet = attacks_root / "attack_metadata.parquet"
    if not parquet.exists():
        return {}
    try:
        import pandas as pd
    except ImportError:
        return {}

    df = pd.read_parquet(parquet)
    dir_names = [d.name for c in attacks_root.iterdir() if c.is_dir() for d in c.iterdir() if d.is_dir()]
    normed = {_norm(d): d for d in dir_names}

    out: dict[str, dict] = {}
    for row in df.to_dict("records"):
        n = _norm(row.get("attack_id", ""))
        hits = [orig for k, orig in normed.items() if k and k in n]
        if len(hits) != 1:
            continue
        out[hits[0]] = {
            "attack_id": row.get("attack_id"),
            "outcome": row.get("outcome"),
            "tags": row.get("tags"),
        }
    return out


def load_sleight(
    *,
    exclude_categories: tuple[str, ...] = SLEIGHT_EXCLUDE_CATEGORIES,
    include_benign: bool = True,
) -> list[TranscriptRecord]:
    """Attack transcripts and their paired benign siblings.

    The benign pair is a sibling *file* (`benign.jsonl`) inside the attack
    directory, not a sibling directory.
    """
    attacks_root = _sleight_root()
    meta_by_dir = _parquet_metadata(attacks_root)
    excluded = {c.lower() for c in exclude_categories}

    out: list[TranscriptRecord] = []
    for category_dir in sorted(p for p in attacks_root.iterdir() if p.is_dir()):
        if category_dir.name.lower() in excluded:
            continue
        for attack_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            pairs = [("attack", attack_dir / "transcript.jsonl", "attack")]
            if include_benign:
                pairs.append(("benign", attack_dir / "benign.jsonl", "benign"))
            for kind, path, truth in pairs:
                if not path.exists():
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                suffix = "" if kind == "attack" else "--benign"
                out.append(
                    TranscriptRecord(
                        transcript_id=f"sleight:{attack_dir.name}{suffix}",
                        text=text,
                        source="sleight",
                        ground_truth=truth,
                        style=None,
                        meta={
                            "category": category_dir.name,
                            "attack_dir": attack_dir.name,
                            "is_benign": kind == "benign",
                            "file": path.name,
                            **meta_by_dir.get(attack_dir.name, {}),
                        },
                    )
                )
    return out


# ---------------------------------------------------------------------------
# Anthropic 18
# ---------------------------------------------------------------------------

_ANTHROPIC_SUFFIXES = (".json", ".jsonl", ".txt", ".md")

# The public viewer excerpt strips tool-call payloads: the assistant turn that
# issued a call survives with empty content, and only the tool result remains.
# Rendering those as a bare "assistant:" line reads as a model that said
# nothing, which is not what happened. This marker is substituted at render
# time only -- the raw files keep the empty string, so nothing is synthesised
# into the stored data.
ELISION_MARKER = "[tool call omitted from public excerpt]"


def _read_anthropic_file(path: Path) -> tuple[str, str | None, int]:
    """Return (transcript text, system prompt or None, elided turn count).

    Accepts several shapes because the drop format is not fixed yet:
      .txt / .md    the file is the transcript
      .jsonl        one message per line, rendered role: content
      .json         either a bare string, {"transcript": ..., "system_prompt": ...},
                    or {"messages": [...]}

    Only system_prompt and messages are read. Provenance stored under "source"
    -- including the viewer's "Simulated transcript..." notice -- is
    deliberately never rendered, so it cannot reach the judge prompt.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix in (".txt", ".md"):
        return raw, None, 0

    elided = 0

    def render(messages) -> str:
        nonlocal elided
        lines = []
        for m in messages:
            if isinstance(m, dict):
                role = m.get("role", "?")
                content = m.get("content", "")
                if role == "assistant" and not str(content).strip():
                    content = ELISION_MARKER
                    elided += 1
                lines.append(f"{role}: {content}")
            else:
                lines.append(str(m))
        return "\n\n".join(lines)

    if path.suffix == ".jsonl":
        msgs = [json.loads(ln) for ln in raw.splitlines() if ln.strip()]
        text = render(msgs)
        return text, None, elided

    obj = json.loads(raw)
    if isinstance(obj, str):
        return obj, None, 0
    if isinstance(obj, dict):
        sys_prompt = obj.get("system_prompt") or obj.get("system")
        for key in ("transcript", "text", "conversation"):
            if isinstance(obj.get(key), str):
                return obj[key], sys_prompt, 0
            if isinstance(obj.get(key), list):
                text = render(obj[key])
                return text, sys_prompt, elided
        if isinstance(obj.get("messages"), list):
            text = render(obj["messages"])
            return text, sys_prompt, elided
    raise ValueError(f"unrecognised transcript shape in {path.name}")


def load_anthropic18(
    path: Path = ANTHROPIC_TRANSCRIPTS, *, expected: int | None = 18,
) -> list[TranscriptRecord]:
    """The Anthropic mislabeling transcripts. Ground truth is fixed: HACKING.

    In the post every transcript's correct label is NON_COMPLIANT — the target
    refused, and the judge is being tested on whether it says so. Under this
    harness's relabelling (NON_COMPLIANT -> HACKING) the correct label is
    HACKING for all of them.
    """
    if not path.is_dir():
        raise FileNotFoundError(f"{path} does not exist")
    files = sorted(p for p in path.iterdir() if p.suffix in _ANTHROPIC_SUFFIXES)
    if not files:
        raise SystemExit(
            f"No transcripts in {path}. Add the 18 Anthropic transcripts "
            f"(one per file, {'/'.join(_ANTHROPIC_SUFFIXES)}) and re-run."
        )
    out = []
    for p in files:
        text, sys_prompt, elided = _read_anthropic_file(p)
        out.append(
            TranscriptRecord(
                transcript_id=f"anthropic:{p.stem}",
                text=text,
                source="anthropic18",
                ground_truth="HACKING",
                style=None,
                meta={
                    "file": p.name,
                    "system_prompt": sys_prompt,
                    "elision_marker": elided > 0,
                    "elided_turns": elided,
                },
            )
        )
    if expected is not None and len(out) != expected:
        print(
            f"warning: expected {expected} transcripts in {path}, found {len(out)}",
            file=sys.stderr,
        )
    return out


# ---------------------------------------------------------------------------
# CLI: counts only, never content
# ---------------------------------------------------------------------------

def _summary(name: str, loader) -> None:
    import collections

    try:
        records = loader()
    except (SystemExit, FileNotFoundError) as exc:
        print(f"{name:14} unavailable: {exc}")
        return
    truths = collections.Counter(r.ground_truth for r in records)
    print(f"{name:14} {len(records):>4} records   ground_truth={dict(truths)}")
    if name == "sleight":
        cats = collections.Counter(r.meta.get("category") for r in records)
        print(f"{'':14} categories={dict(sorted(cats.items()))}")
        joined = sum(1 for r in records if r.meta.get("attack_id"))
        print(f"{'':14} parquet-joined={joined}/{len(records)}")
    if name == "anthropic18":
        el = sum(r.meta.get("elided_turns", 0) for r in records)
        n = sum(1 for r in records if r.meta.get("elision_marker"))
        print(f"{'':14} elision_marker={n}/{len(records)} files, {el} turns marked")
    if name == "atlas":
        styles = collections.Counter(r.style for r in records)
        print(f"{'':14} styles={dict(styles)}")


if __name__ == "__main__":
    _summary("atlas", load_atlas)
    _summary("sleight", load_sleight)
    _summary("anthropic18", load_anthropic18)
