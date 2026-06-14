"""Catalog all manuscript images into the database.

Reads from the HIGH-QUALITY original image directories (referenced in
manuscripts.image_dir), NOT from the compressed site/images/ copies.
Stores both master_path (original) and web_path (compressed) for each image.
"""

import sqlite3
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "hp.db"
SITE_DIR = BASE_DIR / "site"

# Web image directory mapping: shelfmark -> site/images/ subfolder
WEB_IMAGE_DIRS = {
    'C.60.o.12': 'images/bl',
    'O.III.38': 'images/siena',
}


def parse_bl_filename(filename):
    """Parse BL C.60.o.12 image filenames.

    Patterns:
      C_60_o_12-NNN.jpg  -> sequential page scan
      BL HP NN.jpg        -> marginalia detail photo
      BL 2.1.jpg, BL2.jpg -> supplementary photos
    """
    # Sequential page scans
    m = re.match(r'C_60_o_12-(\d{3})\.jpg', filename)
    if m:
        seq = int(m.group(1))
        return {
            'folio_number': str(seq),
            'side': None,  # not encoded in filename
            'page_type': 'PAGE',
            'sort_order': seq,
        }

    # Marginalia detail photos
    m = re.match(r'BL\s*HP\s*(\d+)\.jpg', filename)
    if m:
        num = int(m.group(1))
        return {
            'folio_number': None,
            'side': None,
            'page_type': 'MARGINALIA_DETAIL',
            'sort_order': 1000 + num,
        }

    # Other BL supplementary
    m = re.match(r'BL\s*[\d.]+\.jpg', filename)
    if m:
        return {
            'folio_number': None,
            'side': None,
            'page_type': 'OTHER',
            'sort_order': 2000,
        }

    return {
        'folio_number': None,
        'side': None,
        'page_type': 'OTHER',
        'sort_order': 9999,
    }


def parse_siena_filename(filename):
    """Parse Siena O.III.38 image filenames.

    Patterns:
      O.III.38_NNNNr.jpg / O.III.38_NNNNv.jpg  -> folio recto/verso
      O.III.38_000antcop.jpg                     -> front cover
      O.III.38_000fdg1r.jpg                      -> guard leaf
      O.III.38_postcop.jpg                       -> back cover
      Siena HP N.jpg / Siena Hp N.jpg            -> marginalia detail
    """
    # Standard folio pages
    m = re.match(r'O\.III\.38_(\d{4})([rv])\.jpg', filename)
    if m:
        folio = int(m.group(1))
        side = m.group(2)
        sort_order = folio * 2 + (0 if side == 'r' else 1)
        return {
            'folio_number': str(folio),
            'side': side,
            'page_type': 'PAGE',
            'sort_order': sort_order,
        }

    # Cover and guard pages
    if 'antcop' in filename or 'postcop' in filename:
        sort_order = -2 if 'antcop' in filename else 99999
        return {
            'folio_number': None,
            'side': None,
            'page_type': 'COVER',
            'sort_order': sort_order,
        }

    if 'fdg' in filename or 'risg' in filename:
        sort_order = -1
        return {
            'folio_number': None,
            'side': None,
            'page_type': 'GUARD',
            'sort_order': sort_order,
        }

    # Marginalia detail photos
    m = re.match(r'Siena\s*[Hh][Pp]\s*(\d+)\.jpg', filename, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        return {
            'folio_number': None,
            'side': None,
            'page_type': 'MARGINALIA_DETAIL',
            'sort_order': 100000 + num,
        }

    return {
        'folio_number': None,
        'side': None,
        'page_type': 'OTHER',
        'sort_order': 999999,
    }


def catalog_manuscript(conn, shelfmark, parser_fn):
    """Catalog all images for a manuscript.

    Reads from the original high-quality image directory (manuscripts.image_dir).
    Sets master_path to the original and web_path to the compressed site copy.
    """
    cur = conn.cursor()
    cur.execute("SELECT id, image_dir FROM manuscripts WHERE shelfmark = ?", (shelfmark,))
    row = cur.fetchone()
    if not row:
        print(f"  ERROR: Manuscript {shelfmark} not found in database")
        return 0

    ms_id, image_dir = row
    img_path = BASE_DIR / image_dir
    if not img_path.exists():
        print(f"  ERROR: Master image directory not found: {img_path}")
        print(f"         The original high-quality images must be present.")
        sys.exit(1)

    web_dir = WEB_IMAGE_DIRS.get(shelfmark)
    if not web_dir:
        print(f"  WARNING: No web image directory configured for {shelfmark}")

    count = 0
    missing_web = 0
    for f in sorted(img_path.glob('*.jpg')):
        parsed = parser_fn(f.name)
        master = f"{image_dir}/{f.name}"
        web = f"{web_dir}/{f.name}" if web_dir else None

        # Check web copy exists
        if web and not (SITE_DIR / f.name).parent.parent.joinpath(web).exists():
            # Try site dir directly
            if not (BASE_DIR / "site" / web_dir / f.name).exists():
                missing_web += 1

        # relative_path kept as web_path for backward compatibility
        cur.execute(
            """INSERT OR IGNORE INTO images
               (manuscript_id, filename, folio_number, side, page_type,
                sort_order, relative_path, master_path, web_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ms_id, f.name, parsed['folio_number'], parsed['side'],
             parsed['page_type'], parsed['sort_order'],
             web or master, master, web)
        )
        count += 1

    if missing_web:
        print(f"  WARNING: {missing_web} images lack compressed web copies in site/{web_dir}/")
        print(f"           Run compress_images.py to generate them.")

    conn.commit()
    return count


def main():
    conn = sqlite3.connect(DB_PATH)

    print("Cataloging BL C.60.o.12 images (from originals)...")
    bl_count = catalog_manuscript(conn, 'C.60.o.12', parse_bl_filename)
    print(f"  {bl_count} master images cataloged")

    print("Cataloging Siena O.III.38 images (from originals)...")
    siena_count = catalog_manuscript(conn, 'O.III.38', parse_siena_filename)
    print(f"  {siena_count} master images cataloged")

    # Summary stats
    cur = conn.cursor()
    print("\nPage type breakdown:")
    for page_type in ['PAGE', 'MARGINALIA_DETAIL', 'COVER', 'GUARD', 'OTHER']:
        cur.execute("SELECT COUNT(*) FROM images WHERE page_type = ?", (page_type,))
        print(f"  {page_type}: {cur.fetchone()[0]}")

    # Path coverage
    cur.execute("SELECT COUNT(*) FROM images WHERE master_path IS NOT NULL")
    master_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM images WHERE web_path IS NOT NULL")
    web_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM images")
    total = cur.fetchone()[0]
    print(f"\nPath coverage:")
    print(f"  {master_count}/{total} images have master_path (high-quality originals)")
    print(f"  {web_count}/{total} images have web_path (compressed for site)")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
