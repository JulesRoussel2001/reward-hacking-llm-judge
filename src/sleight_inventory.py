#!/usr/bin/env python3
"""Inventory the decrypted SLEIGHT attack corpus.

Walks $SLEIGHT_DATA/attacks and emits one row per attack directory: the attack
transcript, its paired benign transcript, the category, and token counts
computed here in code.

Corpus layout (verified against the decrypted drop):

    $SLEIGHT_DATA/attacks/<category>/<attack_name>/
        transcript.jsonl    <- attack trajectory
        benign.jsonl        <- paired benign trajectory
        metadata.json
        verifiers.json
        description.md
        encrypted.bin

The benign pair is a *sibling file*, not a sibling directory, so the
"benign dir" column resolves to the same directory as the attack.

Category comes from the directory structure. Neither per-attack metadata.json
nor the corpus-level attack_metadata.parquet supplies a usable one: no
metadata.json carries any of CATEGORY_KEYS, and the parquet's attack_id does
not join to the directory names (its catastrophe_category column is empty and
is an orthogonal taxonomy in any case).

Nothing under $SLEIGHT_DATA is printed: only derived counts and the path/
category strings that make up the inventory table.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# Tokenizer used for the reported counts. Llama-3 is the model family used
# elsewhere in this pilot, so its tokenizer keeps counts comparable.
DEFAULT_TOKENIZER = "meta-llama/Meta-Llama-3-8B-Instruct"

# Keys a metadata.json might carry the category under, tried in order.
CATEGORY_KEYS = ("category", "attack_category", "attack_type", "type", "class")

ATTACK_FILE = "transcript.jsonl"
BENIGN_FILE = "benign.jsonl"
METADATA_FILE = "metadata.json"


# --------------------------------------------------------------------------
# tokenization
# --------------------------------------------------------------------------

class Tokenizer:
    """Token counter with a documented fallback.

    Prefers the real Llama-3 tokenizer. If it is unavailable (not downloaded,
    gated, or offline) it falls back to a deterministic 4-chars-per-token
    approximation so the inventory is still produced -- `self.name` records
    which was used so the CSV is never ambiguous about it.
    """

    APPROX = "approx-chars-div-4"

    def __init__(self, model_id: str, allow_fallback: bool = True) -> None:
        self._hf = None
        self.name = self.APPROX
        try:
            from transformers import AutoTokenizer

            self._hf = AutoTokenizer.from_pretrained(model_id)
            self.name = model_id
        except Exception as exc:  # noqa: BLE001 - any failure means fall back
            if not allow_fallback:
                raise SystemExit(
                    f"could not load tokenizer {model_id!r}: {exc}\n"
                    "pass --allow-approx-tokenizer to fall back to the "
                    "character approximation"
                ) from exc

    @property
    def exact(self) -> bool:
        return self._hf is not None

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._hf is not None:
            return len(self._hf.encode(text, add_special_tokens=False))
        return -(-len(text) // 4)  # ceil division


def _string_leaves(node, out: list[str]) -> None:
    """Collect every string value in a nested JSON structure (keys excluded)."""
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for value in node.values():
            _string_leaves(value, out)
    elif isinstance(node, list):
        for value in node:
            _string_leaves(value, out)


def transcript_text(path: Path) -> tuple[str, int]:
    """Return (content text, record count) for a .jsonl transcript.

    Extracts string leaves rather than assuming a message schema, so the count
    reflects transcript content and not JSON punctuation or key names. A line
    that does not parse as JSON is counted verbatim.
    """
    chunks: list[str] = []
    records = 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            records += 1
            try:
                _string_leaves(json.loads(line), chunks)
            except json.JSONDecodeError:
                chunks.append(line)
    return "\n".join(chunks), records


# --------------------------------------------------------------------------
# inventory
# --------------------------------------------------------------------------

@dataclass
class Row:
    attack_dir: str
    attack_file: str
    benign_dir: str
    benign_file: str
    category: str
    category_source: str
    attack_records: int
    attack_tokens: int
    benign_records: int
    benign_tokens: int
    attack_bytes: int
    benign_bytes: int
    tokenizer: str


def category_from_metadata(meta_path: Path) -> str | None:
    """Pull a category string out of metadata.json, if it carries one.

    Only the resolved category value is ever surfaced; the file's other
    contents are not read out.
    """
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(meta, dict):
        return None
    for key in CATEGORY_KEYS:
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def build_rows(attacks_root: Path, tok: Tokenizer) -> list[Row]:
    rows: list[Row] = []
    for category_dir in sorted(p for p in attacks_root.iterdir() if p.is_dir()):
        for attack_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            attack_path = attack_dir / ATTACK_FILE
            benign_path = attack_dir / BENIGN_FILE
            if not attack_path.exists():
                print(
                    f"warning: {attack_dir.name} has no {ATTACK_FILE}, skipping",
                    file=sys.stderr,
                )
                continue

            attack_text, attack_records = transcript_text(attack_path)
            if benign_path.exists():
                benign_text, benign_records = transcript_text(benign_path)
                benign_tokens = tok.count(benign_text)
                benign_bytes = benign_path.stat().st_size
                benign_dir = str(attack_dir.relative_to(attacks_root))
                benign_name = BENIGN_FILE
            else:
                benign_records = benign_tokens = benign_bytes = 0
                benign_dir = benign_name = ""

            # Directory structure is authoritative for the category; metadata
            # is consulted only where the layout does not supply one.
            category = category_dir.name
            source = "directory"
            meta_category = category_from_metadata(attack_dir / METADATA_FILE)
            if meta_category and meta_category != category:
                source = f"directory (metadata says {meta_category})"

            rows.append(
                Row(
                    attack_dir=str(attack_dir.relative_to(attacks_root)),
                    attack_file=ATTACK_FILE,
                    benign_dir=benign_dir,
                    benign_file=benign_name,
                    category=category,
                    category_source=source,
                    attack_records=attack_records,
                    attack_tokens=tok.count(attack_text),
                    benign_records=benign_records,
                    benign_tokens=benign_tokens,
                    attack_bytes=attack_path.stat().st_size,
                    benign_bytes=benign_bytes,
                    tokenizer=tok.name,
                )
            )
    return rows


def print_table(rows: list[Row]) -> None:
    headers = [
        ("attack_dir", "attack_dir"),
        ("benign_dir", "benign_pair"),
        ("category", "category"),
        ("attack_tokens", "atk_tok"),
        ("benign_tokens", "ben_tok"),
    ]
    widths = []
    for field, title in headers:
        widest = max((len(str(getattr(r, field))) for r in rows), default=0)
        widths.append(max(len(title), widest))

    def line(values):
        return "  ".join(
            str(v).ljust(w) if i < 3 else str(v).rjust(w)
            for i, (v, w) in enumerate(zip(values, widths))
        )

    print(line([t for _, t in headers]))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(line([getattr(row, f) for f, _ in headers]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        default=os.environ.get("SLEIGHT_DATA"),
        help="decrypted SLEIGHT root (default: $SLEIGHT_DATA)",
    )
    parser.add_argument(
        "--out",
        default="data/sleight/inventory.csv",
        help="CSV output path (default: data/sleight/inventory.csv)",
    )
    parser.add_argument("--tokenizer", default=DEFAULT_TOKENIZER)
    parser.add_argument(
        "--allow-approx-tokenizer",
        action="store_true",
        help="fall back to a chars/4 approximation if the tokenizer is unavailable",
    )
    args = parser.parse_args()

    if not args.data_root:
        raise SystemExit("SLEIGHT_DATA is not set and --data-root was not given")

    attacks_root = Path(args.data_root).expanduser() / "attacks"
    if not attacks_root.is_dir():
        raise SystemExit(f"no attacks directory under {args.data_root}")

    tok = Tokenizer(args.tokenizer, allow_fallback=args.allow_approx_tokenizer)
    rows = build_rows(attacks_root, tok)
    if not rows:
        raise SystemExit(f"no attack directories found under {attacks_root}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
