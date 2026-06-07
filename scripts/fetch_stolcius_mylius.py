"""
Download Stolcius Viridarium Chymicum and Mylius Philosophia Reformata.

Sources:
  Stolcius: innergarden.org/artwork/viridarium/ — 108 plates, direct JPGs
  Mylius:   Princeton Digital Library IIIF — 776 pages, full-resolution scans

Usage:
    python scripts/fetch_stolcius_mylius.py --source stolcius
    python scripts/fetch_stolcius_mylius.py --source mylius
    python scripts/fetch_stolcius_mylius.py --source all
    python scripts/fetch_stolcius_mylius.py --source mylius --plates-only
"""
import argparse
import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent

# SSL context for Windows / Python 3.14
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

# ── Stolcius ──────────────────────────────────────────────────────────────────
# innergarden.org hosts 108 plates as individual JPGs
STOLCIUS_BASE = "https://www.innergarden.org/artwork/viridarium/viridarium-{n:02d}.jpg"
STOLCIUS_COUNT = 108
STOLCIUS_DIR = PROJECT_ROOT / "sources" / "stolcius" / "images"

# ── Mylius ────────────────────────────────────────────────────────────────────
# Princeton Digital Library IIIF — Philosophia Reformata 1622
# Manifest: https://figgy.princeton.edu/concern/scanned_resources/8fff50d6-8f43-47fd-934d-c57b71d1dfdf/manifest
MYLIUS_MANIFEST = ("https://figgy.princeton.edu/concern/scanned_resources/"
                   "8fff50d6-8f43-47fd-934d-c57b71d1dfdf/manifest")
MYLIUS_DIR = PROJECT_ROOT / "sources" / "mylius_philosophia" / "images"
# Download at 1800px wide (originals are 6575px; this keeps quality while being pipeline-friendly)
MYLIUS_IIIF_SUFFIX = "/full/1800,/0/default.jpg"
# Minimum ink coverage to keep a page (skip blank / pure-text pages)
MYLIUS_MIN_INK_PCT = 3.0


def _fetch(url, retries=3):
    """Download URL bytes, retrying on transient errors."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (EmblemPrintShop scholarly pipeline)"
            })
            with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as r:
                return r.read()
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)


def _ink_pct(img_bytes):
    """Return % of dark pixels (rough proxy for ink coverage)."""
    try:
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return float(np.mean(img < 180)) * 100
    except Exception:
        return 0.0


# ── Stolcius downloader ───────────────────────────────────────────────────────

def fetch_stolcius(skip_existing=True, dry_run=False):
    """Download 108 Viridarium Chymicum plates from innergarden.org."""
    STOLCIUS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nStolcius Viridarium Chymicum — {STOLCIUS_COUNT} plates")
    print(f"  -> {STOLCIUS_DIR}")

    downloaded = 0
    for n in range(1, STOLCIUS_COUNT + 1):
        out = STOLCIUS_DIR / f"stolcius_plate_{n:03d}.jpg"
        if skip_existing and out.exists():
            print(f"  [{n:3d}/{STOLCIUS_COUNT}] SKIP (exists): {out.name}")
            continue
        url = STOLCIUS_BASE.format(n=n)
        print(f"  [{n:3d}/{STOLCIUS_COUNT}] {url}")
        if dry_run:
            continue
        try:
            data = _fetch(url)
            out.write_bytes(data)
            ink = _ink_pct(data)
            print(f"          -> {len(data)//1024}KB, ink={ink:.1f}%")
            downloaded += 1
            time.sleep(0.3)  # polite crawl delay
        except Exception as e:
            print(f"  ERROR: {e}")

    if not dry_run:
        print(f"\nDone. {downloaded} plates downloaded to {STOLCIUS_DIR}")


# ── Mylius downloader ─────────────────────────────────────────────────────────

def fetch_mylius(skip_existing=True, plates_only=True, dry_run=False):
    """Download Philosophia Reformata pages from Princeton IIIF."""
    MYLIUS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nMylius Philosophia Reformata — Princeton IIIF")
    print(f"  -> {MYLIUS_DIR}")
    print(f"  Fetching manifest: {MYLIUS_MANIFEST}")

    if dry_run:
        print("  [dry-run] Would download manifest and images.")
        return

    # Download manifest
    manifest_cache = MYLIUS_DIR.parent / "manifest.json"
    if manifest_cache.exists():
        with open(manifest_cache, encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"  Loaded cached manifest ({manifest_cache.name})")
    else:
        raw = _fetch(MYLIUS_MANIFEST)
        manifest = json.loads(raw)
        with open(manifest_cache, "w", encoding="utf-8") as f:
            f.write(raw.decode())
        print(f"  Manifest cached to {manifest_cache}")

    canvases = manifest.get("sequences", [{}])[0].get("canvases", [])
    total = len(canvases)
    print(f"  {total} canvases in manifest")

    downloaded = skipped = filtered = 0
    for i, canvas in enumerate(canvases):
        page_num = i + 1
        out = MYLIUS_DIR / f"mylius_philosophia_p{page_num:04d}.jpg"

        if skip_existing and out.exists():
            skipped += 1
            continue

        # Extract image service URL
        images = canvas.get("images", [])
        if not images:
            continue
        svc = images[0].get("resource", {}).get("service", {})
        svc_id = svc.get("@id") or images[0].get("resource", {}).get("@id", "")
        if not svc_id:
            continue

        img_url = svc_id.rstrip("/") + MYLIUS_IIIF_SUFFIX
        label = canvas.get("label", f"page {page_num}")

        print(f"  [{page_num:3d}/{total}] {label}")
        try:
            data = _fetch(img_url)
            ink = _ink_pct(data)
            if plates_only and ink < MYLIUS_MIN_INK_PCT:
                filtered += 1
                print(f"          -> ink={ink:.1f}% — text/blank page, skipping")
                continue
            out.write_bytes(data)
            print(f"          -> {len(data)//1024}KB, ink={ink:.1f}%")
            downloaded += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  ERROR page {page_num}: {e}")

    print(f"\nDone. {downloaded} pages saved, {skipped} skipped (exists), "
          f"{filtered} filtered (low ink)")
    print(f"Output: {MYLIUS_DIR}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["stolcius", "mylius", "all"], default="all")
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--no-skip", dest="skip_existing", action="store_false")
    parser.add_argument("--plates-only", action="store_true", default=True,
                        help="Mylius: skip pages with <3%% ink (text/blank)")
    parser.add_argument("--all-pages", dest="plates_only", action="store_false",
                        help="Mylius: download all 776 pages regardless of ink")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.source in ("stolcius", "all"):
        fetch_stolcius(skip_existing=args.skip_existing, dry_run=args.dry_run)
    if args.source in ("mylius", "all"):
        fetch_mylius(skip_existing=args.skip_existing,
                     plates_only=args.plates_only, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
