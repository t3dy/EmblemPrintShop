"""
Batch exhaustive extraction: run extract_all_objects over every image in one
or more source collections.

Usage:
    python -m scripts.batch_extract_all                          # all sources
    python -m scripts.batch_extract_all claudiens                # one source
    python -m scripts.batch_extract_all claudiens rosarium       # multiple
    python -m scripts.batch_extract_all --glob "sources/claudiens/*.jpg"
    python -m scripts.batch_extract_all --resume                 # skip already-done
"""
from __future__ import annotations

import argparse
import glob as glob_module
import json
import sys
from pathlib import Path

# Force UTF-8 stdout so Unicode characters in print statements don't crash on
# Windows consoles that default to cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extract_all_objects import extract_all_objects, DEFAULT_OUTPUT_DIR

# Canonical source directories relative to project root
SOURCE_DIRS: dict[str, str] = {
    "claudiens":               "sources/claudiens/site/images/emblems",
    "hypnerotomachia-polyphili": "sources/hypnerotomachia-polyphili/site/images/woodcuts_1499",
    "cramer":                  "sources/cramer/images",
    "rosarium":                "sources/rosarium/images",
    "splendor_solis":          "sources/splendor_solis/images",
    "paul_marshall":           "sources/paul_marshall/images",
    "mclean_second":           "sources/mclean_second/images",
    "obrist_medieval":         "sources/obrist_medieval/images",
    "khunrath":                "sources/khunrath/images",
    "maier_arcana":            "sources/maier_arcana/images",
    "maier_viatorium":         "sources/maier_viatorium/images",
    "maier_af_mellon":         "sources/maier_af_mellon/images",
    "fludd":                   "sources/fludd/images",
    "hall_manuscripts":        "sources/hall_manuscripts/images",
    "stolcius":                "sources/stolcius/images",
    "mylius_philosophia_plates": "sources/mylius_philosophia/plates",
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def collect_images(sources: list[str] | None, glob_pattern: str | None, root: Path) -> list[Path]:
    images: list[Path] = []

    if glob_pattern:
        for p in sorted(glob_module.glob(str(root / glob_pattern), recursive=True)):
            if Path(p).suffix.lower() in IMAGE_EXTS:
                images.append(Path(p))
        return images

    target_sources = sources or list(SOURCE_DIRS.keys())
    for src in target_sources:
        src_dir = root / SOURCE_DIRS.get(src, f"sources/{src}")
        if not src_dir.exists():
            print(f"  [skip] {src_dir} not found")
            continue
        for ext in IMAGE_EXTS:
            images.extend(sorted(src_dir.glob(f"*{ext}")))

    return images


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch exhaustive object extraction across emblem collections."
    )
    parser.add_argument(
        "sources", nargs="*",
        help="Source collection name(s) to process. Default: all.",
    )
    parser.add_argument(
        "--glob", dest="glob_pattern", default=None,
        help="Glob pattern relative to project root (overrides sources).",
    )
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help=f"Root output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.25,
        help="Detection confidence threshold.",
    )
    parser.add_argument(
        "--overlap-threshold", type=float, default=0.15,
        help="Containment ratio threshold for composites.",
    )
    parser.add_argument(
        "--categories", nargs="+",
        help="Category groups to run (default: all six).",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip images whose summary.json already exists in the output dir.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Process at most this many images (for testing).",
    )
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    images = collect_images(
        args.sources or None,
        args.glob_pattern,
        root,
    )

    if not images:
        print("No images found.")
        sys.exit(1)

    if args.limit:
        images = images[: args.limit]

    out_root = Path(args.output_dir)
    skipped = 0
    failed = 0
    succeeded = 0
    all_summaries = []

    print(f"Processing {len(images)} image(s) -> {out_root}\n")

    for i, img_path in enumerate(images):
        emblem_dir = out_root / img_path.stem
        summary_file = emblem_dir / "summary.json"

        if args.resume and summary_file.exists():
            print(f"[{i+1}/{len(images)}] SKIP (already done): {img_path.name}")
            skipped += 1
            with open(summary_file, encoding="utf-8") as f:
                all_summaries.append(json.load(f))
            continue

        print(f"[{i+1}/{len(images)}] {img_path.name}")
        try:
            summary = extract_all_objects(
                image_path=str(img_path),
                output_dir=args.output_dir,
                detection_threshold=args.threshold,
                overlap_threshold=args.overlap_threshold,
                categories=args.categories,
            )
            all_summaries.append(summary)
            succeeded += 1
        except Exception as exc:
            print(f"  ERROR: {exc}")
            failed += 1

    # Write batch-level summary
    batch_summary = {
        "total_images":   len(images),
        "succeeded":      succeeded,
        "skipped":        skipped,
        "failed":         failed,
        "total_individual": sum(s.get("individual_count", 0) for s in all_summaries),
        "total_composite":  sum(s.get("composite_count", 0) for s in all_summaries),
    }
    batch_path = out_root / "batch_summary.json"
    out_root.mkdir(parents=True, exist_ok=True)
    with open(batch_path, "w", encoding="utf-8") as f:
        json.dump(batch_summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Batch complete: {succeeded} ok, {skipped} skipped, {failed} failed")
    print(f"  Individual extractions: {batch_summary['total_individual']}")
    print(f"  Composite extractions:  {batch_summary['total_composite']}")
    print(f"  Batch summary: {batch_path}")


if __name__ == "__main__":
    main()
