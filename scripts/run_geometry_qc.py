"""
Run deterministic geometry QC (scripts/pipeline/qc_checks.py) across every
cutout in prototype/gallery_catalog.json and write the verdicts to
prototype/geometry_qc.json, keyed the same way review.html keys its review
state (`emblem_id + '__' + prompt`) so the review UI can fetch this file and
look results up directly.

Why gallery_catalog.json and not assets/extracted_all/*/summary.json: a
re-extraction run overwrites an emblem's summary.json wholesale rather than
merging, so it can (and for at least emblem-13, does) end up describing far
fewer objects than actually exist on disk and are shown in the catalog.
build_catalog.py already works around this by reading every
individual/*_meta.json file directly rather than trusting summary.json's own
manifest -- this script uses its OUTPUT (gallery_catalog.json) as the
enumeration source for the same reason: it's the one file guaranteed to
match what the review UI actually displays.

No AI call, no cost, safe to re-run over the whole corpus.

Usage:
    python -m scripts.run_geometry_qc                  # whole catalog
    python -m scripts.run_geometry_qc --project claudiens
    python -m scripts.run_geometry_qc --emblem-id emblem-00
    python -m scripts.run_geometry_qc --limit 50 --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scripts.pipeline.qc_checks import qc_object

ROOT = Path(__file__).parent.parent
CATALOG_PATH = ROOT / "prototype" / "gallery_catalog.json"
OUT_PATH = ROOT / "prototype" / "geometry_qc.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", help="Only records whose 'project' or 'project_key' contains this (case-insensitive).")
    ap.add_argument("--emblem-id", help="Only this emblem_id (e.g. 'emblem-00').")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    records = catalog.get("records", [])

    if args.project:
        p = args.project.lower()
        records = [r for r in records
                   if p in str(r.get("project", "")).lower() or p in str(r.get("project_key", "")).lower()]
    if args.emblem_id:
        records = [r for r in records if r.get("emblem_id") == args.emblem_id]
    if args.limit:
        records = records[: args.limit]

    existing = {}
    if OUT_PATH.exists():
        try:
            existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    flag_counts = Counter()
    fragmented_examples = []
    checked = 0
    missing = 0

    for r in records:
        # Match review.html's reviewKey(): object_stem (unique per object),
        # not prompt/label -- multiple objects in one emblem routinely share
        # the same generic detector label ("person" x5 on emblem-00 alone).
        stem = r.get("object_stem")
        if not stem:
            name = Path(r.get("crop_jpg") or r.get("transparent_png") or "").name
            stem = re.sub(r"_(crop|transparent)\.(jpe?g|png)$", "", name, flags=re.I) or r.get("prompt")
        key = f"{r.get('emblem_id')}__{stem}"
        png = r.get("transparent_png")
        if not png:
            missing += 1
            continue
        png_path = ROOT / png if not Path(png).is_absolute() else Path(png)
        result = qc_object({"transparent_png": str(png_path)})
        if result is None:
            missing += 1
            continue
        checked += 1
        flag_counts[result["flag"]] += 1
        existing[key] = {
            "emblem_id": r.get("emblem_id"),
            "label": r.get("object_label"),
            "project": r.get("project"),
            **{k: v for k, v in result.items()},
        }
        if result["flag"] == "fragmented" and len(fragmented_examples) < 40:
            fragmented_examples.append({
                "key": key, "emblem_id": r.get("emblem_id"), "label": r.get("object_label"),
                "project": r.get("project"), "note": result["note"],
            })

    print(f"Checked {checked} / {len(records)} records "
          f"({'DRY RUN, nothing written' if args.dry_run else 'written'}); {missing} missing/unreadable PNGs.")
    print(f"Flags: {dict(flag_counts)}")

    if not args.dry_run:
        OUT_PATH.write_text(json.dumps(existing, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"-> {OUT_PATH} ({len(existing)} total entries)")

    if fragmented_examples:
        print(f"\nFirst {len(fragmented_examples)} fragmented examples:")
        for ex in fragmented_examples:
            print(f"  [{ex['project']}] {ex['emblem_id']} '{ex['label']}' -- {ex['note']}")


if __name__ == "__main__":
    main()
