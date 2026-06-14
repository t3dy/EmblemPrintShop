"""Phase 1: Visual Ground Truth Extraction for BL manuscript images.

Processes BL C.60.o.12 master images and stores structured readings
in image_readings table + raw JSON in staging/image_readings/bl/phase1/.

Execution model: This script handles all DB/file I/O. The actual vision
analysis is performed by Claude Code reading images via the Read tool.
Results are ingested via the --ingest flag.

Usage:
    # List images that need processing
    python scripts/read_images.py --phase 1 --source bl --list

    # Ingest a single result
    python scripts/read_images.py --phase 1 --source bl --ingest '{"photo_number": 14, ...}'

    # Ingest results from a JSON file (array of results)
    python scripts/read_images.py --phase 1 --source bl --ingest-file results.json

    # Show status
    python scripts/read_images.py --phase 1 --source bl --status

    # Dry run (show what would be processed)
    python scripts/read_images.py --phase 1 --source bl --dry-run
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

# Add parent to path for image_utils import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.image_utils import (
    assert_master_dirs_exist,
    assert_not_web_derivative,
    resolve_master_path,
    BASE_DIR,
    DB_PATH,
)

STAGING_DIR = BASE_DIR / "staging" / "image_readings"
BL_SHELFMARK = "C.60.o.12"
BL_OFFSET = 13  # photo_number - 13 = page_number (for text pages)


def extract_photo_number(filename):
    """Extract the sequential photo number from a BL filename."""
    m = re.match(r"C_60_o_12-(\d{3})\.jpg", filename)
    if m:
        return int(m.group(1))
    return None


def get_bl_sequential_images(conn):
    """Return all sequential BL images (C_60_o_12-NNN.jpg) sorted by photo number."""
    cur = conn.cursor()
    cur.execute("""
        SELECT i.id, i.filename, i.master_path, i.sort_order, i.page_type
        FROM images i
        JOIN manuscripts m ON i.manuscript_id = m.id
        WHERE m.shelfmark = ?
          AND i.filename LIKE 'C_60_o_12-%.jpg'
        ORDER BY i.sort_order
    """, (BL_SHELFMARK,))
    results = []
    for row in cur.fetchall():
        photo_num = extract_photo_number(row[1])
        if photo_num is not None:
            results.append({
                "image_id": row[0],
                "filename": row[1],
                "master_path": row[2],
                "sort_order": row[3],
                "page_type": row[4],
                "photo_number": photo_num,
            })
    return results


def get_already_processed(conn, phase):
    """Return set of image_ids already processed for this phase."""
    cur = conn.cursor()
    cur.execute(
        "SELECT image_id FROM image_readings WHERE phase = ?",
        (phase,)
    )
    return {row[0] for row in cur.fetchall()}


def validate_result(result):
    """Validate a Phase 1 result dict. Returns (ok, errors)."""
    errors = []
    required = ["photo_number"]
    for field in required:
        if field not in result:
            errors.append(f"Missing required field: {field}")

    if "photo_number" in result:
        pn = result["photo_number"]
        if not isinstance(pn, int) or pn < 1 or pn > 250:
            errors.append(f"Invalid photo_number: {pn}")

    # page_number_visible should be int or null
    pnv = result.get("page_number_visible")
    if pnv is not None and not isinstance(pnv, int):
        errors.append(f"page_number_visible must be int or null, got {type(pnv)}")

    return len(errors) == 0, errors


def store_result(conn, image_id, photo_number, result, phase=1):
    """Store a result in DB and staging file. Supports Phase 1 and Phase 2 fields.

    Args:
        conn: sqlite3 connection
        image_id: images.id
        photo_number: sequential photo number
        result: dict with vision reading results
        phase: pipeline phase (1=ground truth, 2=coverage)
    """
    # Compute expected page number
    page_expected = photo_number - BL_OFFSET if photo_number > BL_OFFSET else None
    page_read = result.get("page_number_visible")
    page_match = None
    if page_read is not None and page_expected is not None:
        page_match = (page_read == page_expected)

    raw_json = json.dumps(result, ensure_ascii=False, indent=2)

    # Write staging file
    staging_path = STAGING_DIR / "bl" / f"phase{phase}" / f"{photo_number:03d}.json"
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    with open(staging_path, "w", encoding="utf-8") as f:
        f.write(raw_json)

    # Phase 2 fields
    has_annotations = result.get("has_annotations")
    annotation_density = result.get("annotation_density")
    annotation_locations = json.dumps(result["annotation_locations"]) if result.get("annotation_locations") else None
    languages_detected = json.dumps(result["languages_detected"]) if result.get("languages_detected") else None
    legible_fragments = json.dumps(result["legible_fragments"]) if result.get("legible_fragments") else None

    # Insert into image_readings
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO image_readings (
            image_id, phase, model, raw_json,
            page_number_read, page_number_expected, page_number_match,
            has_woodcut, woodcut_description,
            has_annotations, annotation_density,
            annotation_locations, languages_detected, legible_fragments,
            concordance_status, notes, created_at
        ) VALUES (?, ?, 'claude-code-vision', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  'UNVERIFIED', ?, datetime('now'))
    """, (
        image_id, phase, raw_json,
        page_read, page_expected, page_match,
        result.get("has_woodcut", False),
        result.get("woodcut_description"),
        has_annotations, annotation_density,
        annotation_locations, languages_detected, legible_fragments,
        result.get("notes"),
    ))
    conn.commit()
    return staging_path


def cmd_list(conn, phase, start=1, limit=None):
    """List images that need processing."""
    images = get_bl_sequential_images(conn)
    processed = get_already_processed(conn, phase)

    pending = [img for img in images
               if img["image_id"] not in processed
               and img["photo_number"] >= start]
    if limit:
        pending = pending[:limit]

    print(f"Images pending for Phase {phase}: {len(pending)}")
    print(f"Already processed: {len(processed)}")
    print()
    for img in pending:
        master = BASE_DIR / img["master_path"]
        size_kb = master.stat().st_size // 1024 if master.exists() else 0
        print(f"  Photo {img['photo_number']:3d}  id={img['image_id']:3d}  "
              f"{img['filename']}  ({size_kb}KB)  [{img['page_type']}]")
    return pending


def cmd_status(conn, phase):
    """Show processing status."""
    images = get_bl_sequential_images(conn)
    processed = get_already_processed(conn, phase)
    total = len(images)
    done = len([img for img in images if img["image_id"] in processed])

    print(f"Phase {phase} Status: {done}/{total} processed ({total - done} remaining)")

    cur = conn.cursor()
    cur.execute("""
        SELECT concordance_status, COUNT(*)
        FROM image_readings WHERE phase = ?
        GROUP BY concordance_status
    """, (phase,))
    for status, count in cur.fetchall():
        print(f"  {status}: {count}")

    cur.execute("""
        SELECT COUNT(*) FROM image_readings
        WHERE phase = ? AND has_woodcut = 1
    """, (phase,))
    print(f"  Woodcuts detected: {cur.fetchone()[0]}")

    cur.execute("""
        SELECT COUNT(*) FROM image_readings
        WHERE phase = ? AND page_number_match = 0
    """, (phase,))
    mismatches = cur.fetchone()[0]
    if mismatches:
        print(f"  PAGE NUMBER MISMATCHES: {mismatches}")
        cur.execute("""
            SELECT image_id, page_number_read, page_number_expected, notes
            FROM image_readings
            WHERE phase = ? AND page_number_match = 0
        """, (phase,))
        for row in cur.fetchall():
            print(f"    image_id={row[0]}: read={row[1]} expected={row[2]} ({row[3]})")


def cmd_ingest(conn, phase, json_str):
    """Ingest a single result from JSON string."""
    result = json.loads(json_str)
    return _ingest_one(conn, phase, result)


def cmd_ingest_file(conn, phase, filepath):
    """Ingest results from a JSON file (single result or array)."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        results = data
    else:
        results = [data]

    stored = 0
    skipped = 0
    errors = 0
    for result in results:
        try:
            ok = _ingest_one(conn, phase, result)
            if ok:
                stored += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR on photo {result.get('photo_number', '?')}: {e}")
            errors += 1

    print(f"\nIngested: {stored}, Skipped: {skipped}, Errors: {errors}")


def _ingest_one(conn, phase, result):
    """Ingest one result dict. Returns True if stored, False if skipped."""
    ok, errs = validate_result(result)
    if not ok:
        print(f"  INVALID: {errs}")
        return False

    photo_num = result["photo_number"]
    images = get_bl_sequential_images(conn)
    img = next((i for i in images if i["photo_number"] == photo_num), None)
    if not img:
        print(f"  Photo {photo_num}: no matching image in database, skipping")
        return False

    # Check idempotency
    processed = get_already_processed(conn, phase)
    if img["image_id"] in processed:
        print(f"  Photo {photo_num}: already processed, skipping")
        return False

    # Validate master path
    master = BASE_DIR / img["master_path"]
    assert_not_web_derivative(master)

    path = store_result(conn, img["image_id"], photo_num, result, phase)

    page_read = result.get("page_number_visible")
    woodcut = result.get("has_woodcut", False)
    wc_desc = result.get("woodcut_description", "")
    print(f"  Photo {photo_num:3d}: page={page_read}  woodcut={woodcut}"
          f"{'  [' + wc_desc + ']' if wc_desc else ''}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Image reading pipeline")
    parser.add_argument("--phase", type=int, required=True, help="Pipeline phase (1)")
    parser.add_argument("--source", required=True, choices=["bl", "siena"],
                        help="Manuscript source")
    parser.add_argument("--list", action="store_true", help="List pending images")
    parser.add_argument("--status", action="store_true", help="Show processing status")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--start", type=int, default=1, help="Start from photo N")
    parser.add_argument("--limit", type=int, help="Process at most N images")
    parser.add_argument("--ingest", type=str, help="Ingest a single JSON result")
    parser.add_argument("--ingest-file", type=str, help="Ingest results from JSON file")
    args = parser.parse_args()

    if args.phase not in (1, 2):
        print("Only Phase 1 and Phase 2 are implemented.")
        sys.exit(1)
    if args.source != "bl":
        print("Only BL source is implemented for Phase 1.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    # Startup validation
    assert_master_dirs_exist(conn)

    if args.status:
        cmd_status(conn, args.phase)
    elif args.list or args.dry_run:
        cmd_list(conn, args.phase, start=args.start, limit=args.limit)
    elif args.ingest:
        cmd_ingest(conn, args.phase, args.ingest)
    elif args.ingest_file:
        cmd_ingest_file(conn, args.phase, args.ingest_file)
    else:
        # Default: show status
        cmd_status(conn, args.phase)

    conn.close()


if __name__ == "__main__":
    main()
