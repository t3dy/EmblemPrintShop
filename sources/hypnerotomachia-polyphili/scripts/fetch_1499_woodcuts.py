#!/usr/bin/env python3
"""fetch_1499_woodcuts.py — Download woodcut page images from Internet Archive.

Downloads pages from the 1499 Hypnerotomachia Poliphili facsimile
(University of Seville copy, IA identifier A336080v1) for all entries
in the woodcuts table that have a page_1499_ia value.

Usage:
    python scripts/fetch_1499_woodcuts.py
    python scripts/fetch_1499_woodcuts.py --dry-run
    python scripts/fetch_1499_woodcuts.py --limit 10
    python scripts/fetch_1499_woodcuts.py --force   # re-download existing
"""

import argparse
import sqlite3
import ssl
import time
import urllib.request
import urllib.error
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "hp.db"
IMAGE_DIR = Path(__file__).parent.parent / "site" / "images" / "woodcuts_1499"
IA_IDENTIFIER = "A336080v1"
IA_URL_TEMPLATE = "https://archive.org/download/{id}/page/n{page}.jpg"

# IA offset: IA page index = HP 1499 page number + 5
# Verified: HP p.4 (dark forest) = n9, HP p.28 (elephant) = n33
IA_OFFSET = 5


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def download_image(ia_page, output_path, dry_run=False):
    """Download a single page image from Internet Archive."""
    url = IA_URL_TEMPLATE.format(id=IA_IDENTIFIER, page=ia_page)

    if dry_run:
        print(f"  DRY RUN: Would download {url} -> {output_path.name}")
        return True

    try:
        # IA has certificate issues with some Python versions
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers={
            'User-Agent': 'HP-Marginalia-Project/1.0 (scholarly research)'
        })
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = resp.read()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(data)

        size_kb = len(data) / 1024
        print(f"  Downloaded n{ia_page} -> {output_path.name} ({size_kb:.0f} KB)")
        return True

    except urllib.error.HTTPError as e:
        print(f"  ERROR: HTTP {e.code} for n{ia_page}: {e.reason}")
        return False
    except Exception as e:
        print(f"  ERROR downloading n{ia_page}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download 1499 HP woodcut images from Internet Archive"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Re-download existing images")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max images to download (0 = all)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between downloads in seconds (be polite)")
    args = parser.parse_args()

    conn = get_conn()

    # Get all woodcuts with IA page numbers
    rows = conn.execute("""
        SELECT id, slug, title, page_1499, page_1499_ia, ia_image_cached
        FROM woodcuts
        WHERE page_1499_ia IS NOT NULL
        ORDER BY page_1499_ia
    """).fetchall()

    if not rows:
        print("No woodcuts with page_1499_ia set. Run seed_1499_woodcuts.py first.")
        return

    print(f"Found {len(rows)} woodcuts with IA page numbers")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    errors = 0

    for row in rows:
        ia_page = row["page_1499_ia"]
        output_path = IMAGE_DIR / f"hp1499_p{row['page_1499']:03d}.jpg"

        # Skip if already cached and not forcing
        if not args.force and output_path.exists():
            skipped += 1
            continue

        if args.limit and downloaded >= args.limit:
            print(f"\nReached limit of {args.limit} downloads")
            break

        ok = download_image(ia_page, output_path, dry_run=args.dry_run)

        if ok and not args.dry_run:
            conn.execute(
                "UPDATE woodcuts SET ia_image_cached = 1 WHERE id = ?",
                (row["id"],)
            )
            conn.commit()
            downloaded += 1
            time.sleep(args.delay)  # Be polite to IA
        elif not ok:
            errors += 1

    print(f"\nDone: {downloaded} downloaded, {skipped} skipped, {errors} errors")
    conn.close()


if __name__ == "__main__":
    main()
