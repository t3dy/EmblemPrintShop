"""
Batch extraction: process multiple emblems from source projects.

Usage:
  python scripts/batch_extract.py --source claudiens --output assets/extracted/
  python scripts/batch_extract.py --source hypnerotomachia --output assets/extracted/
  python scripts/batch_extract.py --source all --motifs lion dragon vessel --output assets/extracted/

Uses auto-prompts from metadata where available, skips images with no metadata match.
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

sys.path.insert(0, str(Path(__file__).parent))
from pipeline.metadata import list_available_emblems
from pipeline.extractor import extract_element, DEFAULT_OUTPUT_DIR

SOURCES_ROOT = Path(__file__).parent.parent / "sources"


def main():
    parser = argparse.ArgumentParser(description="Batch emblem element extraction")
    parser.add_argument("--source", default="all",
                        help="Which source project to process (all, claudiens, hypnerotomachia, "
                             "cramer, rosarium, paul_marshall, splendor_solis, mclean_second, "
                             "obrist_medieval, khunrath, maier_arcana, maier_viatorium, "
                             "maier_af_mellon, fludd, hall_manuscripts, stolcius, "
                             "mylius_philosophia, or 'all')")
    parser.add_argument("--mode", default="motif", choices=["motif", "equipment"],
                        help="motif=extract figures/creatures; equipment=extract apparatus/vessels")
    parser.add_argument("--motifs", nargs="+", default=None,
                        help="Filter to specific motif keywords (e.g. --motifs lion dragon)")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR,
                        help="Output directory")
    parser.add_argument("--threshold", "-t", type=float, default=0.25,
                        help="Detection threshold")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be processed without running extraction")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip images that already have extracted outputs in the output dir")
    parser.add_argument("--force-equipment", action="store_true",
                        help="Equipment mode: apply equipment prompts to ALL images, not just those "
                             "with equipment terms in their auto_prompt (needed for sources that use "
                             "generic default prompts, e.g. paul_marshall, khunrath, obrist_medieval)")
    args = parser.parse_args()

    emblems = list_available_emblems()

    # Filter by source
    if args.source != "all":
        emblems = [e for e in emblems if args.source in e["source_project"]]

    # Equipment mode: override prompts with equipment-focused ones
    if args.mode == "equipment":
        from pipeline.metadata import EQUIPMENT_PROMPTS, EQUIPMENT_MOTIFS
        equipment_emblems = []
        for e in emblems:
            prompt = e.get("auto_prompt", "") or ""
            # Include image if: it has equipment terms in its per-image prompt,
            # OR --force-equipment is set (for sources with generic default prompts)
            if args.force_equipment or any(m in prompt.lower() for m in EQUIPMENT_MOTIFS):
                for eq_prompt in EQUIPMENT_PROMPTS:
                    eq_copy = dict(e)
                    eq_copy["auto_prompt"] = eq_prompt
                    equipment_emblems.append(eq_copy)
        emblems = equipment_emblems
        print(f"Equipment mode: {len(emblems)} (image, prompt) pairs to process")

    # Filter by motif keywords
    if args.motifs:
        motif_keywords = [m.lower() for m in args.motifs]
        filtered = []
        for e in emblems:
            prompt = e.get("auto_prompt") or ""
            if any(kw in prompt.lower() for kw in motif_keywords):
                filtered.append(e)
        emblems = filtered

    print(f"Found {len(emblems)} emblems to process")
    for e in emblems:
        prompt_display = e['auto_prompt'] or '(no metadata — will skip)'
        print(f"  {Path(e['image_path']).name:40s} | {prompt_display}")

    if args.dry_run:
        print("\n[dry-run] No extraction performed.")
        return

    if not emblems:
        print("Nothing to process.")
        return

    results = []
    out_dir = Path(args.output)
    for i, emblem in enumerate(emblems):
        if not emblem["auto_prompt"]:
            print(f"[{i+1}/{len(emblems)}] SKIP (no prompt): {emblem['image_path']}")
            continue

        # Skip if already extracted (--skip-existing)
        if args.skip_existing:
            from pathlib import Path as P
            stem = Path(emblem["image_path"]).stem
            safe_p = "_".join(emblem["auto_prompt"].lower().split()[:3])
            safe_p = "".join(c if c.isalnum() or c == "_" else "" for c in safe_p)
            expected_meta = out_dir / f"{stem}_{safe_p}_meta.json"
            if expected_meta.exists():
                print(f"[{i+1}/{len(emblems)}] SKIP (exists): {Path(emblem['image_path']).name}")
                continue
        print(f"[{i+1}/{len(emblems)}] {Path(emblem['image_path']).name} | {emblem['auto_prompt']}")
        try:
            result = extract_element(
                emblem["image_path"],
                prompt=emblem["auto_prompt"],
                output_dir=args.output,
                detection_threshold=args.threshold,
            )
            if result:
                results.append(result)
                print(f"  -> {result['transparent_png']}")
            else:
                print(f"  -> no detection")
        except Exception as exc:
            print(f"  -> ERROR: {exc}")

    print(f"\nDone. Extracted {len(results)} elements to {args.output}")

    # Write batch summary
    summary_path = Path(args.output) / "batch_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Batch summary: {summary_path}")


if __name__ == "__main__":
    main()
