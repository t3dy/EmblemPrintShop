"""Shared image path utilities for the HP Marginalia pipeline.

Every script that touches image files imports from here.
Path validation is a function call, not a per-script reimplementation.
"""

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "hp.db"

# Prefixes that identify web-derivative images (display only, not for analysis)
WEB_DERIVATIVE_PREFIXES = (
    "site/images/",
    "site\\images\\",
    "images/bl/",
    "images\\bl\\",
    "images/siena/",
    "images\\siena\\",
)


def resolve_master_path(conn, image_id):
    """Return the absolute master_path for an image. Raises if missing.

    Args:
        conn: sqlite3 connection to hp.db
        image_id: images.id value

    Returns:
        pathlib.Path to the master image file

    Raises:
        ValueError: if image_id not found or master_path is NULL
        FileNotFoundError: if the resolved file does not exist on disk
    """
    cur = conn.cursor()
    cur.execute("SELECT master_path, filename FROM images WHERE id = ?", (image_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"No image with id={image_id} in database")
    master_path, filename = row
    if not master_path:
        raise ValueError(
            f"Image {image_id} ({filename}) has no master_path. "
            f"Run catalog_images.py to populate master_path."
        )
    full_path = BASE_DIR / master_path
    if not full_path.exists():
        raise FileNotFoundError(
            f"Master image not found on disk: {full_path}\n"
            f"Image {image_id} ({filename}) points to a missing file."
        )
    return full_path


def assert_not_web_derivative(path):
    """Raise ValueError if path is a web-derivative image.

    Call this before any analytical operation (vision API, OCR,
    comparison, embedding) to ensure you are reading the original
    high-quality image, not a compressed display copy.

    Args:
        path: str or pathlib.Path to check

    Raises:
        ValueError: if path matches a known web-derivative prefix
    """
    path_str = str(path).replace("\\", "/")
    for prefix in WEB_DERIVATIVE_PREFIXES:
        normalized = prefix.replace("\\", "/")
        if normalized in path_str:
            raise ValueError(
                f"Refusing to read web-derivative image for analysis.\n"
                f"Path '{path}' is a compressed display copy.\n"
                f"Use master_path (from images.master_path) instead."
            )


def assert_master_dirs_exist(conn):
    """Check that all manuscript master image directories exist on disk.

    Call this at script startup before processing any images.
    Exits with code 1 if any directory is missing.

    Args:
        conn: sqlite3 connection to hp.db
    """
    cur = conn.cursor()
    cur.execute("SELECT shelfmark, image_dir FROM manuscripts")
    all_ok = True
    for shelfmark, image_dir in cur.fetchall():
        if not image_dir:
            print(f"WARNING: {shelfmark} has no image_dir configured")
            continue
        full_path = BASE_DIR / image_dir
        if not full_path.exists():
            print(
                f"ERROR: Master image directory missing for {shelfmark}:\n"
                f"  Expected: {full_path}\n"
                f"  The original high-quality images must be present."
            )
            all_ok = False
        else:
            count = len(list(full_path.glob("*.jpg")))
            if count == 0:
                print(
                    f"ERROR: Master image directory is empty for {shelfmark}:\n"
                    f"  Path: {full_path}"
                )
                all_ok = False
    if not all_ok:
        print("\nCannot proceed without master image directories.")
        sys.exit(1)


def get_master_images(conn, shelfmark, page_type='PAGE'):
    """Yield (image_id, filename, master_path, folio_number, side) for a manuscript.

    Args:
        conn: sqlite3 connection to hp.db
        shelfmark: manuscript shelfmark (e.g. 'C.60.o.12')
        page_type: filter by page_type (default 'PAGE'). None for all types.

    Yields:
        dict with keys: id, filename, master_path, folio_number, side, page_type
    """
    cur = conn.cursor()
    if page_type:
        cur.execute("""
            SELECT i.id, i.filename, i.master_path, i.folio_number, i.side, i.page_type
            FROM images i
            JOIN manuscripts m ON i.manuscript_id = m.id
            WHERE m.shelfmark = ? AND i.page_type = ?
            ORDER BY i.sort_order
        """, (shelfmark, page_type))
    else:
        cur.execute("""
            SELECT i.id, i.filename, i.master_path, i.folio_number, i.side, i.page_type
            FROM images i
            JOIN manuscripts m ON i.manuscript_id = m.id
            WHERE m.shelfmark = ?
            ORDER BY i.sort_order
        """, (shelfmark,))
    for row in cur.fetchall():
        yield {
            'id': row[0],
            'filename': row[1],
            'master_path': BASE_DIR / row[2] if row[2] else None,
            'folio_number': row[3],
            'side': row[4],
            'page_type': row[5],
        }


def get_connection():
    """Return a sqlite3 connection to hp.db."""
    return sqlite3.connect(DB_PATH)
