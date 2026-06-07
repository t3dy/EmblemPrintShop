"""
Download alchemical emblem books from Internet Archive and extract page images.

Uses PyMuPDF (fitz) to render PDF pages at high resolution as JPGs.
Skips pages that are clearly text-only (low ink density).

Known IA items:
  - Cramer Emblemata Sacra (1624): emblematasacraho00cram
  - Rosarium Philosophorum (scan): rosarium-philosophorum-the-rosary-of-the-philosophers
  - Stolcius Viridarium Chymicum: search needed

Usage:
    python scripts/fetch_ia_emblems.py --dry-run
    python scripts/fetch_ia_emblems.py --source cramer
    python scripts/fetch_ia_emblems.py --source all
    python scripts/fetch_ia_emblems.py --source cramer --pages 10-60
"""
import argparse
import json
import ssl
import sys
import urllib.request
from pathlib import Path

import cv2
import fitz   # PyMuPDF
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent

# SSL context for Python 3.14 on Windows
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

# Internet Archive base URL for downloads
IA_DOWNLOAD = "https://archive.org/download"

# Known item configurations
IA_SOURCES = {
    "cramer": {
        "name": "Daniel Cramer — Emblemata Sacra (1624)",
        "ia_id": "emblematasacraho00cram",
        "pdf_file": "emblematasacraho00cram.pdf",
        "output_dir": "sources/cramer",
        "source_project": "cramer",
        # Cramer's 50 emblems are in the middle of the book; pages 1-20 are prefatory
        "emblem_page_range": (20, 120),
        # Minimum image dimension to accept (skip pure text pages)
        "min_figure_height_px": 200,
    },
    "rosarium": {
        "name": "Rosarium Philosophorum (scan)",
        "ia_id": "rosarium-philosophorum-the-rosary-of-the-philosophers",
        "pdf_file": "rosarium.pdf",
        "output_dir": "sources/rosarium",
        "source_project": "rosarium",
        "emblem_page_range": (1, 200),
        "min_figure_height_px": 100,
    },
}

# DPI for rendering — 150dpi gives ~1200px for a folio page, good for SAM
RENDER_DPI = 150


def ia_search_stolcius() -> str | None:
    """Search IA for Stolcius Viridarium Chymicum and return identifier."""
    url = ("https://archive.org/advancedsearch.php"
           "?q=Viridarium+chymicum+emblematum&fl[]=identifier,title&rows=5&output=json")
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as r:
            results = json.loads(r.read()).get("response", {}).get("docs", [])
        for item in results:
            title = item.get("title", "").lower()
            if "stolcius" in title or "viridarium" in title:
                return item.get("identifier")
    except Exception:
        pass
    return None


def download_pdf(ia_id: str, pdf_file: str, out_path: Path) -> bool:
    """Download a PDF from Internet Archive. Returns True if successful."""
    if out_path.exists() and out_path.stat().st_size > 100_000:
        print(f"  PDF already cached: {out_path.name} ({out_path.stat().st_size//1024}KB)")
        return True

    url = f"{IA_DOWNLOAD}/{ia_id}/{pdf_file}"
    print(f"  Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=120) as resp:
            data = resp.read()
        out_path.write_bytes(data)
        print(f"  Saved {out_path.name} ({len(data)//1024}KB)")
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def is_emblem_page(page_img: np.ndarray, min_figure_height: int = 200) -> bool:
    """
    Heuristic: does this page likely contain an emblem figure (not just text)?

    Early modern emblem books alternate figure pages and text pages. Figure
    pages have denser ink in contiguous blocks; text pages have evenly-spaced
    lines of small ink marks.

    Returns True if the page looks like it contains a figure.
    """
    gray = cv2.cvtColor(page_img, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape

    # Otsu threshold to find ink
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find connected components in the ink map
    num, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)

    # Look for at least one large ink component (a figure)
    large_components = [
        stats[i] for i in range(1, num)
        if (stats[i, cv2.CC_STAT_HEIGHT] >= min_figure_height
            and stats[i, cv2.CC_STAT_WIDTH] >= min_figure_height)
    ]
    return len(large_components) > 0


def extract_pages(
    pdf_path: Path,
    out_dir: Path,
    source_key: str,
    page_range: tuple[int, int] = (1, 9999),
    dpi: int = RENDER_DPI,
    filter_text_pages: bool = True,
    dry_run: bool = False,
) -> list[str]:
    """
    Render PDF pages as JPGs. Returns list of saved image paths.
    """
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    start, end = max(0, page_range[0] - 1), min(total_pages, page_range[1])
    print(f"  PDF has {total_pages} pages; processing pages {start+1}–{end}")

    if dry_run:
        print(f"  [dry-run] Would extract pages {start+1}–{end} to {out_dir}")
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for page_idx in range(start, end):
        page_num = page_idx + 1
        out_path = out_dir / f"{source_key}_page_{page_num:04d}.jpg"

        if out_path.exists() and out_path.stat().st_size > 10_000:
            saved.append(str(out_path))
            continue

        page = doc[page_idx]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)

        if filter_text_pages and not is_emblem_page(img):
            continue

        # Save as JPG
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(out_path), img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
        saved.append(str(out_path))
        print(f"  Page {page_num:>4}  -> {out_path.name}  ({img.shape[1]}x{img.shape[0]}px)")

    doc.close()
    return saved


def save_provenance(
    image_paths: list[str],
    out_dir: Path,
    source_cfg: dict,
    ia_id: str,
):
    """Write a JSON provenance manifest for the extracted pages."""
    records = []
    for path in image_paths:
        records.append({
            "image_path": path,
            "source_name": source_cfg["name"],
            "ia_identifier": ia_id,
            "ia_url": f"https://archive.org/details/{ia_id}",
            "source_project": source_cfg["source_project"],
            "rights": "Public domain. Internet Archive scan.",
        })
    out_path = out_dir / "provenance.json"
    out_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"  Provenance saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Download and extract emblem plate images from Internet Archive")
    parser.add_argument("--source", default="all", choices=["all", "cramer", "rosarium"])
    parser.add_argument("--pages", default=None,
                        help="Page range e.g. '20-80' (1-indexed, overrides defaults)")
    parser.add_argument("--no-filter", action="store_true",
                        help="Don't filter text-only pages — save every page")
    parser.add_argument("--dpi", type=int, default=RENDER_DPI)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sources_to_run = (
        {args.source: IA_SOURCES[args.source]}
        if args.source != "all"
        else IA_SOURCES
    )

    # Parse page range override
    page_range_override = None
    if args.pages:
        parts = args.pages.split("-")
        page_range_override = (int(parts[0]), int(parts[1]) if len(parts) > 1 else 9999)

    for key, cfg in sources_to_run.items():
        print(f"\n{'='*60}")
        print(f"Source: {cfg['name']}")

        ia_id  = cfg["ia_id"]
        pdf_fn = cfg["pdf_file"]
        out_dir = PROJECT_ROOT / cfg["output_dir"]
        out_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = out_dir / pdf_fn

        # Step 1: Download PDF
        if not args.dry_run:
            ok = download_pdf(ia_id, pdf_fn, pdf_path)
            if not ok:
                print(f"  Skipping {key} — PDF download failed")
                continue
        else:
            pdf_path = out_dir / pdf_fn
            if not pdf_path.exists():
                print(f"  [dry-run] Would download: {IA_DOWNLOAD}/{ia_id}/{pdf_fn}")
                continue

        # Step 2: Extract pages
        page_range = page_range_override or cfg.get("emblem_page_range", (1, 9999))
        images_dir = out_dir / "images"
        saved = extract_pages(
            pdf_path,
            images_dir,
            source_key=key,
            page_range=page_range,
            dpi=args.dpi,
            filter_text_pages=not args.no_filter,
            dry_run=args.dry_run,
        )

        if saved:
            print(f"  Extracted {len(saved)} emblem pages")
            if not args.dry_run:
                save_provenance(saved, images_dir, cfg, ia_id)

    print("\nDone. Next step:")
    print("  python scripts/batch_extract.py --source cramer --output assets/extracted/")


if __name__ == "__main__":
    main()
