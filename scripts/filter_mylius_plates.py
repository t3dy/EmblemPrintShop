"""
Filter Mylius Philosophia Reformata pages to identify likely engraved plates.

Engraved plates differ from typeset text pages:
  - Higher standard deviation in intensity (complex hatching vs regular text)
  - Lower ink coverage overall (text pages are denser black on white)
  - Smoother tone transitions (engravings have gradients; text is binary)

Usage:
    python scripts/filter_mylius_plates.py              # dry-run, prints candidates
    python scripts/filter_mylius_plates.py --apply      # copies plates to a filtered/ subdir
    python scripts/filter_mylius_plates.py --threshold 0.6  # tune sensitivity (0-1)
"""
import argparse
import shutil
from pathlib import Path

import cv2
import numpy as np

IMAGES_DIR = Path(__file__).parent.parent / "sources" / "mylius_philosophia" / "images"
FILTERED_DIR = IMAGES_DIR.parent / "plates"


def score_page(img_path: Path) -> float:
    """
    Return a plate-likelihood score in [0, 1].

    Two complementary signals:
    1. Large-CC ratio: engraved plates have fewer but larger connected
       components (hatching = connected blobs), whereas text pages have
       thousands of tiny letter-size CCs. We measure the fraction of ink
       pixels that belong to CCs larger than 500px².
    2. Row-sum periodicity: text pages have a strongly periodic row-sum
       profile (regular line spacing). Plates have a flat autocorrelation.
       We penalise pages with a high periodicity peak.
    """
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0

    # Downsample for speed (1800px → ~450px wide)
    h, w = img.shape
    small = cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape

    # Binarise (dark pixels = ink)
    _, bw = cv2.threshold(small, 180, 255, cv2.THRESH_BINARY_INV)

    # ── Signal 1: Large-CC ratio ─────────────────────────────────────
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    total_ink = max(1, int(np.sum(bw > 0)))
    large_cc_px = sum(
        stats[i, cv2.CC_STAT_AREA]
        for i in range(1, n_labels)
        if stats[i, cv2.CC_STAT_AREA] > 500  # ~500px² at this scale ≈ a word or larger blob
    )
    large_cc_score = min(large_cc_px / total_ink, 1.0)

    # ── Signal 2: Row-sum periodicity (penalise text) ────────────────
    row_sums = bw.mean(axis=1).astype(np.float32)
    row_sums -= row_sums.mean()
    if row_sums.std() > 1e-6:
        autocorr = np.correlate(row_sums, row_sums, mode="full")
        autocorr = autocorr[sh - 1:]  # keep positive lags
        autocorr /= autocorr[0]       # normalise
        # Peak in lags 5-40 (line spacing range at this scale)
        peak = float(autocorr[5:40].max()) if len(autocorr) > 40 else 0.0
    else:
        peak = 0.0
    periodicity_penalty = peak  # high peak → text-like → penalise

    score = large_cc_score * 0.8 - periodicity_penalty * 0.2
    return float(np.clip(score, 0.0, 1.0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.55,
                        help="Plate-score threshold; pages above this are kept (default 0.55)")
    parser.add_argument("--apply", action="store_true",
                        help="Copy candidate plate images to sources/mylius_philosophia/plates/")
    parser.add_argument("--top", type=int, default=None,
                        help="Keep only the top N scoring pages (overrides --threshold)")
    args = parser.parse_args()

    images = sorted(IMAGES_DIR.glob("*.jpg"))
    if not images:
        print(f"No images found in {IMAGES_DIR}")
        return

    print(f"Scoring {len(images)} Mylius pages...")
    scores = []
    for i, p in enumerate(images, 1):
        s = score_page(p)
        scores.append((s, p))
        if i % 50 == 0:
            print(f"  {i}/{len(images)} scored...")

    scores.sort(reverse=True)

    if args.top:
        candidates = scores[:args.top]
        print(f"\nTop {args.top} candidate plates:")
    else:
        candidates = [(s, p) for s, p in scores if s >= args.threshold]
        print(f"\n{len(candidates)} candidates above threshold {args.threshold}:")

    for s, p in candidates:
        print(f"  {p.name}  score={s:.3f}")

    print(f"\nTotal candidates: {len(candidates)} / {len(images)} pages")

    if args.apply:
        FILTERED_DIR.mkdir(exist_ok=True)
        for _, p in candidates:
            dest = FILTERED_DIR / p.name
            shutil.copy2(p, dest)
        print(f"\nCopied {len(candidates)} files to {FILTERED_DIR}")
        print(f"Run extraction with: python scripts/batch_extract.py --source mylius_philosophia_plates ...")


if __name__ == "__main__":
    main()
