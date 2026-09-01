#!/usr/bin/env python3
"""
Fill style_label / style_subtype / notes in atlas_pilot_v1_labeled.csv,
based on which adapter produced each row. Idempotent: re-running is safe.

Rules (pilot, adapter-informed labelling, confirmed by reading all 30 hacks):
  honest                     -> style_label="", subtype="", note=""
  blatant_deception          -> plain,          "",         adapter-consistent...
  rhetorical_rationalization -> rationalization, "",         adapter-consistent...
  strategic_honesty          -> strategic_honesty, disavowal, adapter-consistent...

Usage:
  python fill_style_labels.py data/atlas/atlas_pilot_v1_labeled.csv
"""
import csv, sys, os

MAP = {
    "honest":                     ("", "", ""),
    "blatant_deception":          ("plain", "", "adapter-consistent; confirmed by reading"),
    "rhetorical_rationalization": ("rationalization", "", "adapter-consistent; confirmed by reading"),
    "strategic_honesty":          ("strategic_honesty", "disavowal",
                                   "adapter-consistent; disavowal subtype (claims task invalid); confirmed by reading"),
}

def main(path):
    if not os.path.exists(path):
        sys.exit(f"File not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)

    # Ensure the target columns exist (add if the importer didn't emit them)
    for col in ("style_label", "style_subtype", "notes"):
        if col not in fields:
            fields.append(col)

    changed = 0
    for r in rows:
        adapter = (r.get("adapter_label") or "").strip()
        if adapter not in MAP:
            continue
        label, subtype, note = MAP[adapter]
        # only count as changed if we actually set something new
        if (r.get("style_label","") != label or
            r.get("style_subtype","") != subtype or
            r.get("notes","") != note):
            changed += 1
        r["style_label"] = label
        r["style_subtype"] = subtype
        r["notes"] = note

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # summary
    from collections import Counter
    c = Counter((r.get("adapter_label",""), r.get("style_label",""), r.get("style_subtype","")) for r in rows)
    print(f"Updated {changed} row(s) in {path}\n")
    print(f"{'adapter':<28} {'style_label':<18} {'subtype':<10} count")
    print("-"*68)
    for (ad, lab, sub), n in sorted(c.items()):
        print(f"{ad:<28} {lab:<18} {sub:<10} {n}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python fill_style_labels.py <path-to-atlas_pilot_v1_labeled.csv>")
    main(sys.argv[1])
