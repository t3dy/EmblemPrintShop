"""
Flag junk crops in assets/extracted_all/ that the detector boxed by mistake:

  1. text_page  -- a printed page from a source PDF (Khunrath, Obrist, ...) that
                   got run through extraction and labelled "furnace" / "book" /
                   "distillation vessel". Detected from image statistics (bright
                   background + many small character-sized components arranged in
                   regular horizontal text rows). HIGH precision -> auto-written.

  2. full_scene -- a crop whose box covers most of the source plate (the detector
                   grabbed the whole emblem instead of one element). Detected from
                   bbox coverage. REPORTED ONLY by default (a legitimately large
                   central figure can also have high coverage); pass --drop-scenes
                   to also write these as verified_label="scene".

Verdicts are written into each summary.json individual object as verified_label
(text_page | scene) with label_source "heuristic:junk-filter", preserving the
original detector label. build_catalog.py already drops these from the gallery.
Manual/vision verdicts (verified_label already set) are never overwritten.
The animals category is skipped (already re-identified by hand).

Usage:
    python -m scripts.flag_junk_crops --dry-run            # print feature table, write nothing
    python -m scripts.flag_junk_crops --dry-run --stems khunrath_p0241 obrist_debuts_p0318
    python -m scripts.flag_junk_crops                      # write text_page verdicts
    python -m scripts.flag_junk_crops --drop-scenes        # also write full_scene verdicts
    python -m scripts.flag_junk_crops --scene-coverage 0.75
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
EX = ROOT / "assets" / "extracted_all"

# Pure plate/emblem collections — no loose printed-text pages were bound into
# these scans, so any "text-like" hit there is a finely-hatched engraving false
# positive (component count explodes at high scan resolution). Text pages only
# occur in book/manuscript scans (Mylius, Khunrath, Obrist, the Maier books,
# Paul Marshall anthology), so we only run the text-page filter outside this set.
PLATE_ONLY_PREFIXES = ("emblem-", "hp1499", "splendor_solis", "stolcius",
                       "cramer_page", "rosarium", "mclean_second")
MAX_TEXT_EDGE = 2200   # book-page scale; excludes high-res woodcut plates


def is_plate_only(stem: str) -> bool:
    return stem.startswith(PLATE_ONLY_PREFIXES)


def text_page_features(crop_path: Path) -> dict | None:
    """Return image statistics used to decide if a crop is a page of printed text."""
    import cv2
    import numpy as np

    img = cv2.imread(str(crop_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    h, w = img.shape
    if h < 40 or w < 40:                      # too small to be a text page
        return {"too_small": True, "white_frac": 0, "row_bands": 0, "n_small": 0, "ink_frac": 1}

    # Binarize: ink = dark pixels. Otsu, then ensure ink is the minority (dark) class.
    _, binv = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ink = binv > 0
    ink_frac = float(ink.mean())
    white_frac = float((img > 210).mean())    # bright background fraction

    # Connected components of ink -> count small (character-sized) blobs.
    n, _, stats, _ = cv2.connectedComponentsWithStats(binv, connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA] if n > 1 else np.array([])
    page_area = h * w
    char_lo, char_hi = page_area * 0.00002, page_area * 0.01   # character-sized
    n_small = int(np.sum((areas >= char_lo) & (areas <= char_hi)))

    # Horizontal text-row structure: per-row ink fraction, count bands of text rows
    # separated by near-blank rows (the hallmark of typeset lines). The key
    # discriminator vs a dense engraving is the BLANK gaps between lines: text
    # alternates ink-row / blank-gap; hatched engravings have ink in every row.
    row_ink = ink.mean(axis=1)
    is_textrow = (row_ink > 0.02) & (row_ink < 0.45)
    blank_row_frac = float((row_ink < 0.012).mean())
    bands, prev = 0, False
    for v in is_textrow:
        if v and not prev:
            bands += 1
        prev = bool(v)

    return {"too_small": False, "white_frac": white_frac, "ink_frac": ink_frac,
            "row_bands": int(bands), "blank_row_frac": blank_row_frac,
            "n_small": n_small, "h": h, "w": w}


def is_text_page(f: dict) -> bool:
    if not f or f.get("too_small"):
        return False
    # The clean discriminator (calibrated against known text pages vs dense
    # engravings) is the count of character-sized components: printed pages carry
    # 600-1900+ tiny blobs, hatched engravings top out around ~200, and emblem
    # objects/plates sit well under 100. Brightness does NOT work (yellowed scans
    # read as dark). Guard with row structure and a not-solid-ink ceiling.
    if max(f.get("h", 0), f.get("w", 0)) >= MAX_TEXT_EDGE:
        return False                       # high-res plate, not a book page
    return (f["n_small"] >= 600
            and f["row_bands"] >= 5
            and f["ink_frac"] <= 0.45)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stems", nargs="*")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--drop-scenes", action="store_true",
                    help="Also write full_scene verdicts (off by default).")
    ap.add_argument("--scene-coverage", type=float, default=0.78,
                    help="bbox/source-area ratio above which a crop is a scene candidate.")
    args = ap.parse_args()

    summaries = sorted(EX.glob("*/summary.json"))
    src_size_cache: dict[str, tuple[int, int]] = {}
    ts = datetime.now(timezone.utc).isoformat()
    report = []
    text_hits = scene_hits = scanned = 0

    from PIL import Image

    for sp in summaries:
        stem = sp.parent.name
        if args.stems and stem not in args.stems:
            continue
        try:
            data = json.loads(sp.read_text(encoding="utf-8"))
        except Exception:
            continue
        dirty = False
        for o in data.get("individual", []):
            if o.get("category") == "animals" or o.get("verified_label"):
                continue
            cj = o.get("crop_jpg")
            if not cj or not Path(cj).exists():
                continue
            if args.limit and scanned >= args.limit:
                break
            scanned += 1

            f = text_page_features(Path(cj))
            textp = is_text_page(f) and not is_plate_only(stem)

            # scene coverage from tight_bbox vs source image size
            coverage = None
            src = o.get("source_image", "")
            bb = o.get("tight_bbox") or o.get("det_bbox")
            if src and bb and len(bb) == 4:
                if src not in src_size_cache:
                    try:
                        src_size_cache[src] = Image.open(src).size  # (w, h), header only
                    except Exception:
                        src_size_cache[src] = (0, 0)
                sw, sh = src_size_cache[src]
                if sw and sh:
                    coverage = (bb[2] * bb[3]) / (sw * sh)
            scenep = (coverage is not None and coverage >= args.scene_coverage)

            verdict = "text_page" if textp else ("scene" if scenep else None)
            if args.dry_run:
                if verdict or (f and (f["row_bands"] >= 5 or (coverage or 0) >= 0.6)):
                    print(f"[{verdict or '-':9s}] {stem}/{Path(cj).name}  "
                          f"label='{o.get('label')}' white={f['white_frac']:.2f} "
                          f"bands={f['row_bands']} nsmall={f['n_small']} "
                          f"ink={f['ink_frac']:.2f} cov={coverage if coverage is None else round(coverage,2)}")
                if verdict == "text_page": text_hits += 1
                elif verdict == "scene": scene_hits += 1
                continue

            if verdict == "scene" and not args.drop_scenes:
                report.append({"stem": stem, "crop": Path(cj).name, "candidate": "scene",
                               "label": o.get("label"), "coverage": round(coverage, 3)})
                scene_hits += 1
                continue
            if verdict:
                o.update({"verified_label": verdict, "verified_category": "other",
                          "verified_is_animal": False, "verified_confidence": "high",
                          "verified_multiple": verdict == "scene", "verified_secondary": [],
                          "verified_features": ("Printed text page from source PDF."
                                                if verdict == "text_page"
                                                else f"Box covers {coverage:.0%} of the source plate (whole-scene crop)."),
                          "verified_notes": "", "label_source": "heuristic:junk-filter",
                          "verified_at": ts})
                dirty = True
                report.append({"stem": stem, "crop": Path(cj).name, "verdict": verdict,
                               "label": o.get("label"),
                               "coverage": None if coverage is None else round(coverage, 3)})
                if verdict == "text_page": text_hits += 1
                else: scene_hits += 1
        if dirty:
            sp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nScanned {scanned} crops. text_page={text_hits} scene={'(written)' if args.drop_scenes else '(reported only)'} {scene_hits}")
    if not args.dry_run:
        rp = EX / "junk_filter_report.json"
        rp.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report -> {rp}")


if __name__ == "__main__":
    main()
