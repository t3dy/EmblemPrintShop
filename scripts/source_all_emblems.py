"""
Comprehensive alchemical emblem image sourcing script.

Handles two types of sources:
  A) Local PDFs — extract pages using PyMuPDF
  B) Internet Archive — download PDF then extract pages

Run stages:
  python scripts/source_all_emblems.py --stage discover    # show what would be done
  python scripts/source_all_emblems.py --stage download    # download IA PDFs
  python scripts/source_all_emblems.py --stage extract     # extract page images
  python scripts/source_all_emblems.py --stage all         # do everything

After this script runs, use:
  python scripts/batch_extract.py --source <key> --output assets/extracted/
to run the segmentation pipeline on each sourced corpus.
"""
import argparse
import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import cv2
import fitz
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
SOURCES_DIR  = PROJECT_ROOT / "sources"

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

# ── Source registry ───────────────────────────────────────────────────────────
# Each entry: key → config dict
# type: "local_pdf" or "ia_pdf"
# For ia_pdf: ia_id + pdf_file (filename on IA)
# For local_pdf: local_path (absolute)
# page_range: (start, end) 1-indexed
# filter_text: use is_emblem_page heuristic
# min_component_height: for is_emblem_page, min ink component size
# prompt_default: GroundingDINO prompt to use when no metadata available

SOURCES = {

    # ── Already sourced ───────────────────────────────────────────────────────
    # "maier_af": done (Claudiens, 51 plates)
    # "cramer": done (75 plates)
    # "rosarium_basic": done (19 plates)

    # ── Paul Marshall Christian Rosenkreutz Anthology ─────────────────────────
    "paul_marshall": {
        "name": "Christian Rosenkreutz Anthology (Paul Marshall Allen)",
        "type": "local_pdf",
        "local_path": r"e:\pdf\Rosicrucian\a christian rosenkreutz anthology_paul marshall al.pdf",
        "output_dir": "sources/paul_marshall",
        "page_range": (1, 682),
        "filter_text": True,
        "min_component_height": 150,
        "prompt_default": "alchemical figure rose cross emblem",
        "notes": "682-page anthology. Contains emblem plates scattered throughout.",
    },

    # ── Splendor Solis (local) ────────────────────────────────────────────────
    "splendor_solis_local": {
        "name": "Splendor Solis — Salomon Trismosin (local scan)",
        "type": "local_pdf",
        "local_path": r"e:\pdf\alchemy\illustrations\Salomon Trismossin SPLENDOR SOLIS libgen li.pdf",
        "output_dir": "sources/splendor_solis",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 200,
        "prompt_default": "alchemical figure king queen sun moon vessel",
        "notes": "The 22 illuminated allegorical plates. Should be almost all image pages.",
    },

    # ── Adam McLean Second Collection ─────────────────────────────────────────
    "mclean_second": {
        "name": "Adam McLean — Second Collection of Alchemical and Hermetic Emblems",
        "type": "local_pdf",
        "local_path": r"e:\pdf\alchemy\Adam McLean The Second Collection of Alchemical and Hermetic Emblems.pdf",
        "output_dir": "sources/mclean_second",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 150,
        "prompt_default": "alchemical emblem hermetic figure symbol",
        "notes": "McLean's curated emblem collection from multiple alchemical works.",
    },

    # ── Barbara Obrist — Medieval alchemical imagery ─────────────────────────
    "obrist_debuts": {
        "name": "Obrist — Les débuts de l'imagerie alchimique (medieval images)",
        "type": "local_pdf",
        "local_path": r"e:\pdf\alchemy\Barbara Obrist Les débuts de l imagerie alchimique Le Sycomore.pdf",
        "output_dir": "sources/obrist_medieval",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 100,
        "prompt_default": "medieval alchemical figure vessel dragon serpent",
        "notes": "Obrist's foundational work on medieval alchemical image tradition.",
    },

    # ── Obrist — Visualization in medieval alchemy ───────────────────────────
    "obrist_visualization": {
        "name": "Obrist — Visualization in Medieval Alchemy",
        "type": "local_pdf",
        "local_path": r"e:\pdf\alchemy\Obrist Barbara Visualization in medieval alchemy.pdf",
        "output_dir": "sources/obrist_medieval",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 100,
        "prompt_default": "medieval manuscript figure alchemical diagram",
        "notes": "Obrist's survey article on medieval alchemical visualization.",
    },

    # ── Khunrath Amphitheatrum Sapientiae Aeternae (Internet Archive) ─────────
    "khunrath": {
        "name": "Heinrich Khunrath — Amphitheatrum Sapientiae Aeternae (1609)",
        "type": "ia_pdf",
        "ia_id": "amphitheatrum-sapientiae-aeternae-solius-verae-christiano-kabalisticum-divino-ma",
        "pdf_file": None,  # will detect
        "output_dir": "sources/khunrath",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 200,
        "prompt_default": "oratory laboratory alchemical figure divine",
        "notes": "Khunrath's Amphitheatrum — famous for 5 large engraved plates.",
    },

    # ── Maier Arcana Arcanissima (Internet Archive) ───────────────────────────
    "maier_arcana": {
        "name": "Michael Maier — Arcana Arcanissima (1614)",
        "type": "ia_pdf",
        "ia_id": "arcanaarcanissim00maie",
        "pdf_file": None,
        "output_dir": "sources/maier_arcana",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 150,
        "prompt_default": "hieroglyphic figure emblem allegorical",
        "notes": "Maier's hieroglyphic emblems — Egyptian and mythological allegory.",
    },

    # ── Splendor Solis (Internet Archive — color plates) ─────────────────────
    "splendor_solis_ia": {
        "name": "Splendor Solis — Internet Archive (1920 edition, 22 color plates)",
        "type": "ia_pdf",
        "ia_id": "SplendorSolisAlchemicalTreatisesOfSolomonTrismosin...Including22",
        "pdf_file": None,
        "output_dir": "sources/splendor_solis",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 200,
        "prompt_default": "alchemical king queen sun moon vessel figure",
        "notes": "22 color allegorical plates from the 1582 manuscript.",
    },

    # ── Fludd — Mosaicall Philosophy (Internet Archive) ──────────────────────
    "fludd_mosaicall": {
        "name": "Robert Fludd — Mosaicall Philosophy (1659, English edition)",
        "type": "ia_pdf",
        "ia_id": "bim_early-english-books-1641-1700_mosaicall-philosophy-_fludd-robert_1659",
        "pdf_file": None,
        "output_dir": "sources/fludd",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 180,
        "prompt_default": "macrocosm microcosm divine figure sun moon cosmos",
        "notes": "Fludd's cosmological diagrams — macrocosm/microcosm engravings.",
    },

    # ── Manly Palmer Hall alchemical manuscripts ──────────────────────────────
    "hall_manuscripts": {
        "name": "Manly Palmer Hall — Collection of Alchemical Manuscripts",
        "type": "ia_pdf",
        "ia_id": "manlypalmerhabox18v6hall",
        "pdf_file": None,
        "output_dir": "sources/hall_manuscripts",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 100,
        "prompt_default": "manuscript alchemical figure hermetic emblem",
        "notes": "Facsimiles of alchemical manuscripts from Manly Palmer Hall collection.",
    },

    # ── Maier Viatorium (Internet Archive) ───────────────────────────────────
    "maier_viatorium": {
        "name": "Michael Maier — Viatorium (1618)",
        "type": "ia_pdf",
        "ia_id": "majeriviatoriumh00maie",
        "pdf_file": None,
        "output_dir": "sources/maier_viatorium",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 150,
        "prompt_default": "alchemical figure emblem symbol mountain",
        "notes": "Maier's Viatorium — mountains of the planets, alchemical allegory.",
    },

    # ── Maier Mellon Atalanta (Internet Archive) ──────────────────────────────
    "maier_af_mellon": {
        "name": "Michael Maier — Atalanta Fugiens (Mellon edition)",
        "type": "ia_pdf",
        "ia_id": "mellon48atalanta",
        "pdf_file": None,
        "output_dir": "sources/maier_af_mellon",
        "page_range": (1, 9999),
        "filter_text": True,
        "min_component_height": 150,
        "prompt_default": "atalanta figure emblem alchemical running",
        "notes": "Alternative high-quality scan of Maier's Atalanta Fugiens.",
    },
}

RENDER_DPI = 150  # 150dpi → ~1200px wide for folio pages


# ── Utility functions ─────────────────────────────────────────────────────────

def ia_get_pdf_filename(ia_id: str) -> str | None:
    """Find the main PDF filename for an IA item."""
    url = f"https://archive.org/metadata/{ia_id}/files"
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    try:
        with urllib.request.urlopen(req, context=_SSL, timeout=15) as r:
            files = json.loads(r.read()).get("result", [])
        pdfs = [f["name"] for f in files
                if f.get("name","").endswith(".pdf")
                and not f.get("name","").endswith("_bw.pdf")
                and "__ia_thumb" not in f.get("name","")]
        return pdfs[0] if pdfs else None
    except Exception as e:
        print(f"  Error fetching IA files: {e}")
        return None


def download_ia_pdf(ia_id: str, pdf_file: str, out_path: Path) -> bool:
    if out_path.exists() and out_path.stat().st_size > 100_000:
        print(f"  Already cached: {out_path.name} ({out_path.stat().st_size//1024}KB)")
        return True
    url = f"https://archive.org/download/{ia_id}/{urllib.request.quote(pdf_file)}"
    print(f"  Downloading: {url[:80]}")
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    try:
        with urllib.request.urlopen(req, context=_SSL, timeout=180) as r:
            data = r.read()
        out_path.write_bytes(data)
        print(f"  Saved {out_path.name} ({len(data)//1024}KB)")
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def is_emblem_page(img: np.ndarray, min_h: int = 150) -> bool:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    n, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    return any(
        stats[i, cv2.CC_STAT_HEIGHT] >= min_h and stats[i, cv2.CC_STAT_WIDTH] >= min_h
        for i in range(1, n)
    )


def extract_pages_from_pdf(
    pdf_path: Path,
    out_dir: Path,
    source_key: str,
    page_range: tuple[int, int] = (1, 9999),
    min_h: int = 150,
    filter_text: bool = True,
    dpi: int = RENDER_DPI,
    dry_run: bool = False,
) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    total = len(doc)
    start = max(0, page_range[0] - 1)
    end = min(total, page_range[1])
    print(f"  PDF: {total} pages, processing {start+1}–{end}")
    if dry_run:
        print(f"  [dry-run] Would save to {out_dir}")
        return []
    saved = []
    for idx in range(start, end):
        pnum = idx + 1
        out_path = out_dir / f"{source_key}_p{pnum:04d}.jpg"
        if out_path.exists() and out_path.stat().st_size > 5000:
            saved.append(str(out_path))
            continue
        page = doc[idx]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)
        if filter_text and not is_emblem_page(img, min_h):
            continue
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(out_path), bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
        saved.append(str(out_path))
        print(f"  p{pnum:>4} -> {out_path.name} ({img.shape[1]}x{img.shape[0]})")
    doc.close()
    # Write provenance
    prov = {
        "source_key": source_key,
        "pdf_path": str(pdf_path),
        "pages_extracted": len(saved),
        "page_range": list(page_range),
        "image_paths": saved,
    }
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(f"  Extracted {len(saved)} emblem pages -> {out_dir}")
    return saved


def process_source(key: str, cfg: dict, dry_run: bool = False) -> int:
    print(f"\n{'='*60}")
    print(f"[{key}] {cfg['name']}")
    out_dir = PROJECT_ROOT / cfg["output_dir"] / "images"

    if cfg["type"] == "local_pdf":
        pdf_path = Path(cfg["local_path"])
        if not pdf_path.exists():
            print(f"  LOCAL PDF NOT FOUND: {pdf_path}")
            return 0
        saved = extract_pages_from_pdf(
            pdf_path, out_dir, key,
            page_range=cfg.get("page_range", (1, 9999)),
            min_h=cfg.get("min_component_height", 150),
            filter_text=cfg.get("filter_text", True),
            dry_run=dry_run,
        )
        return len(saved)

    elif cfg["type"] == "ia_pdf":
        ia_id = cfg["ia_id"]
        pdf_file = cfg.get("pdf_file") or ia_get_pdf_filename(ia_id)
        if not pdf_file:
            print(f"  No PDF found on IA for {ia_id}")
            return 0
        local_pdf_dir = PROJECT_ROOT / cfg["output_dir"]
        local_pdf_dir.mkdir(parents=True, exist_ok=True)
        local_pdf = local_pdf_dir / pdf_file

        if not dry_run:
            ok = download_ia_pdf(ia_id, pdf_file, local_pdf)
            if not ok:
                return 0
            time.sleep(1)
        else:
            print(f"  [dry-run] Would download: {ia_id}/{pdf_file}")
            if not local_pdf.exists():
                return 0

        saved = extract_pages_from_pdf(
            local_pdf, out_dir, key,
            page_range=cfg.get("page_range", (1, 9999)),
            min_h=cfg.get("min_component_height", 150),
            filter_text=cfg.get("filter_text", True),
            dry_run=dry_run,
        )
        return len(saved)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Source all alchemical emblem images")
    parser.add_argument("--stage", default="discover",
                        choices=["discover", "download", "extract", "all"],
                        help="discover=show plan, download=IA only, extract=process PDFs, all=everything")
    parser.add_argument("--sources", nargs="*", default=None,
                        help="Specific source keys to process (default: all)")
    parser.add_argument("--dpi", type=int, default=RENDER_DPI)
    args = parser.parse_args()

    keys = args.sources or list(SOURCES.keys())

    if args.stage == "discover":
        print(f"\nAlchemical Emblem Source Registry ({len(keys)} sources)")
        print(f"{'Key':<25} {'Type':<12} {'Notes'}")
        print("-"*80)
        for k in keys:
            cfg = SOURCES[k]
            t = cfg["type"]
            src = cfg.get("local_path", cfg.get("ia_id","?"))[-50:]
            print(f"{k:<25} {t:<12} {cfg['name'][:45]}")
        print(f"\nRun with --stage all to download and extract everything.")
        return

    dry_run = (args.stage == "discover")
    total = 0

    for k in keys:
        if k not in SOURCES:
            print(f"Unknown source: {k}")
            continue
        cfg = SOURCES[k]

        if args.stage == "download" and cfg["type"] != "ia_pdf":
            continue
        if args.stage == "extract" and cfg["type"] == "ia_pdf":
            # For extract stage, only process if PDF already downloaded
            pass

        n = process_source(k, cfg, dry_run=(args.stage == "discover"))
        total += n

    print(f"\n{'='*60}")
    print(f"Total image pages extracted: {total}")
    if total > 0:
        print("\nNext step — run segmentation pipeline:")
        for k in keys:
            if k in SOURCES:
                out = SOURCES[k]["output_dir"]
                print(f"  python scripts/batch_extract.py --source {k} --output assets/extracted/")


if __name__ == "__main__":
    main()
