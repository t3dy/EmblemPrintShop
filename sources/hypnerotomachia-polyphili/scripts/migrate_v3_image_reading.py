"""Migration v3: Image reading infrastructure.

Creates the image_readings table and expands CHECK constraints on
annotations.source_method, matches.confidence, woodcuts.source_method,
and symbol_occurrences.source_method to support VISION_MODEL outputs.

SQLite does not support ALTER TABLE to modify CHECK constraints, so
affected tables must be recreated with data migrated.

Run: python scripts/migrate_v3_image_reading.py
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "hp.db"
STAGING_DIR = BASE_DIR / "staging" / "image_readings"

TARGET_VERSION = 3


def check_version(conn):
    """Verify we haven't already run this migration."""
    cur = conn.cursor()
    cur.execute("SELECT MAX(version) FROM schema_version")
    current = cur.fetchone()[0] or 0
    if current >= TARGET_VERSION:
        print(f"  Already at version {current}, skipping migration.")
        return False
    print(f"  Current schema version: {current}")
    return True


def create_image_readings(conn):
    """Create the image_readings table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS image_readings (
            id INTEGER PRIMARY KEY,
            image_id INTEGER REFERENCES images(id),
            phase INTEGER NOT NULL,
            model TEXT NOT NULL,
            raw_json TEXT NOT NULL,
            page_number_read INTEGER,
            page_number_expected INTEGER,
            page_number_match BOOLEAN,
            has_woodcut BOOLEAN,
            woodcut_description TEXT,
            has_annotations BOOLEAN,
            annotation_density TEXT CHECK(annotation_density IN
                ('LIGHT','MODERATE','HEAVY',NULL)),
            annotation_locations TEXT,
            languages_detected TEXT,
            legible_fragments TEXT,
            deep_reading_json TEXT,
            concordance_status TEXT CHECK(concordance_status IN (
                'CONFIRMED', 'DISCREPANCY', 'UNVERIFIED'
            )) DEFAULT 'UNVERIFIED',
            reviewed BOOLEAN DEFAULT 0,
            reviewed_by TEXT,
            reviewed_at TEXT,
            promoted_to TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    print("  Created image_readings table")


def migrate_annotations(conn):
    """Recreate annotations with expanded source_method CHECK."""
    cur = conn.cursor()

    # Check if VISION_MODEL is already accepted
    try:
        cur.execute("""
            INSERT INTO annotations (signature_ref, source_method)
            VALUES ('__test__', 'VISION_MODEL')
        """)
        cur.execute("DELETE FROM annotations WHERE signature_ref = '__test__'")
        conn.commit()
        print("  annotations.source_method already accepts VISION_MODEL, skipping")
        return
    except sqlite3.IntegrityError:
        conn.rollback()

    print("  Migrating annotations table (expanding source_method CHECK)...")
    cur.execute("SELECT COUNT(*) FROM annotations")
    row_count = cur.fetchone()[0]

    cur.execute("""
        CREATE TABLE annotations_new (
            id INTEGER PRIMARY KEY,
            manuscript_id INTEGER REFERENCES manuscripts(id),
            hand_id INTEGER REFERENCES annotator_hands(id),
            signature_ref TEXT,
            folio_number INTEGER,
            side TEXT CHECK(side IN ('r','v',NULL)),
            annotation_text TEXT,
            annotation_type TEXT CHECK(annotation_type IN (
                'MARGINAL_NOTE','LABEL','SYMBOL','UNDERLINE','DRAWING',
                'CROSS_REFERENCE','INDEX_ENTRY','PROVENANCE','EMENDATION','OTHER'
            )),
            language TEXT,
            thesis_page INTEGER,
            thesis_chapter INTEGER,
            confidence TEXT CHECK(confidence IN ('HIGH','MEDIUM','LOW','PROVISIONAL'))
                DEFAULT 'PROVISIONAL',
            needs_review BOOLEAN DEFAULT 1,
            reviewed BOOLEAN DEFAULT 0,
            reviewed_by TEXT,
            reviewed_at TEXT,
            source_method TEXT CHECK(source_method IN (
                'MANUAL_TRANSCRIPTION','PDF_EXTRACTION','LLM_ASSISTED',
                'INFERRED','VISION_MODEL'
            )) DEFAULT 'INFERRED',
            notes TEXT
        )
    """)

    cur.execute("""
        INSERT INTO annotations_new
        SELECT id, manuscript_id, hand_id, signature_ref, folio_number,
               side, annotation_text, annotation_type, language,
               thesis_page, thesis_chapter, confidence, needs_review,
               reviewed, reviewed_by, reviewed_at, source_method, notes
        FROM annotations
    """)

    cur.execute("SELECT COUNT(*) FROM annotations_new")
    new_count = cur.fetchone()[0]
    assert new_count == row_count, \
        f"Row count mismatch: {row_count} -> {new_count}"

    cur.execute("DROP TABLE annotations")
    cur.execute("ALTER TABLE annotations_new RENAME TO annotations")
    conn.commit()
    print(f"  Migrated annotations: {row_count} rows, source_method now accepts VISION_MODEL")


def migrate_matches(conn):
    """Recreate matches with expanded confidence CHECK."""
    cur = conn.cursor()

    # Check if PROVISIONAL is already accepted
    try:
        cur.execute("""
            INSERT INTO matches (ref_id, image_id, confidence)
            VALUES (1, 1, 'PROVISIONAL')
        """)
        cur.execute("DELETE FROM matches WHERE confidence = 'PROVISIONAL'")
        conn.commit()
        print("  matches.confidence already accepts PROVISIONAL, skipping")
        return
    except sqlite3.IntegrityError:
        conn.rollback()

    print("  Migrating matches table (expanding confidence CHECK)...")
    cur.execute("SELECT COUNT(*) FROM matches")
    row_count = cur.fetchone()[0]

    cur.execute("""
        CREATE TABLE matches_new (
            id INTEGER PRIMARY KEY,
            ref_id INTEGER REFERENCES dissertation_refs(id),
            image_id INTEGER REFERENCES images(id),
            match_method TEXT CHECK(match_method IN (
                'SIGNATURE_EXACT','FOLIO_EXACT','MANUAL','VISION_VERIFIED'
            )),
            confidence TEXT CHECK(confidence IN (
                'HIGH','MEDIUM','LOW','PROVISIONAL'
            )),
            needs_review BOOLEAN DEFAULT 1,
            source_method TEXT DEFAULT 'FOLIO_EXACT',
            reviewed BOOLEAN DEFAULT 0,
            reviewed_by TEXT,
            notes TEXT
        )
    """)

    cur.execute("""
        INSERT INTO matches_new
        SELECT id, ref_id, image_id, match_method, confidence,
               needs_review, source_method, reviewed, reviewed_by, notes
        FROM matches
    """)

    cur.execute("SELECT COUNT(*) FROM matches_new")
    new_count = cur.fetchone()[0]
    assert new_count == row_count, \
        f"Row count mismatch: {row_count} -> {new_count}"

    cur.execute("DROP TABLE matches")
    cur.execute("ALTER TABLE matches_new RENAME TO matches")
    conn.commit()
    print(f"  Migrated matches: {row_count} rows, confidence now accepts PROVISIONAL")


def migrate_woodcuts(conn):
    """Add CHECK constraint to woodcuts.source_method."""
    cur = conn.cursor()

    # Check if already has CHECK (try an invalid value)
    try:
        cur.execute("""
            INSERT INTO woodcuts (title, source_method)
            VALUES ('__test__', 'GARBAGE_VALUE_12345')
        """)
        # If this succeeds, there's no CHECK — need to migrate
        cur.execute("DELETE FROM woodcuts WHERE title = '__test__'")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        print("  woodcuts.source_method already has CHECK constraint, skipping")
        return

    print("  Migrating woodcuts table (adding source_method CHECK)...")
    cur.execute("SELECT COUNT(*) FROM woodcuts")
    row_count = cur.fetchone()[0]

    cur.execute("""
        CREATE TABLE woodcuts_new (
            id INTEGER PRIMARY KEY,
            woodcut_number INTEGER,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            signature_1499 TEXT,
            page_1499 INTEGER,
            signature_1545 TEXT,
            page_1545 INTEGER,
            chapter_context TEXT,
            description TEXT,
            subject_category TEXT,
            depicted_elements TEXT,
            woodcut_type TEXT,
            signed TEXT,
            attributed_to TEXT,
            scholarly_discussion TEXT,
            influence TEXT,
            has_bl_photo BOOLEAN DEFAULT 0,
            bl_photo_number INTEGER,
            has_siena_photo BOOLEAN DEFAULT 0,
            has_annotation BOOLEAN DEFAULT 0,
            alchemical_annotation BOOLEAN DEFAULT 0,
            annotation_density TEXT,
            dictionary_terms TEXT,
            review_status TEXT DEFAULT 'DRAFT',
            source_method TEXT CHECK(source_method IN (
                'CORPUS_EXTRACTION','LLM_ASSISTED','VISION_MODEL',
                'MANUAL_TRANSCRIPTION','INFERRED'
            )) DEFAULT 'CORPUS_EXTRACTION',
            source_basis TEXT,
            confidence TEXT DEFAULT 'MEDIUM',
            notes TEXT
        )
    """)

    cur.execute("""
        INSERT INTO woodcuts_new
        SELECT * FROM woodcuts
    """)

    cur.execute("SELECT COUNT(*) FROM woodcuts_new")
    new_count = cur.fetchone()[0]
    assert new_count == row_count, \
        f"Row count mismatch: {row_count} -> {new_count}"

    cur.execute("DROP TABLE woodcuts")
    cur.execute("ALTER TABLE woodcuts_new RENAME TO woodcuts")
    conn.commit()
    print(f"  Migrated woodcuts: {row_count} rows, source_method now has CHECK constraint")


def migrate_symbol_occurrences(conn):
    """Add CHECK constraint to symbol_occurrences.source_method."""
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO symbol_occurrences (symbol_id, hand_id, source_method)
            VALUES (1, 1, 'GARBAGE_VALUE_12345')
        """)
        cur.execute("DELETE FROM symbol_occurrences WHERE source_method = 'GARBAGE_VALUE_12345'")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        print("  symbol_occurrences.source_method already has CHECK constraint, skipping")
        return

    print("  Migrating symbol_occurrences table (adding source_method CHECK)...")
    cur.execute("SELECT COUNT(*) FROM symbol_occurrences")
    row_count = cur.fetchone()[0]

    cur.execute("""
        CREATE TABLE symbol_occurrences_new (
            id INTEGER PRIMARY KEY,
            symbol_id INTEGER REFERENCES alchemical_symbols(id),
            hand_id INTEGER REFERENCES annotator_hands(id),
            signature_ref TEXT,
            folio_description_id INTEGER REFERENCES folio_descriptions(id),
            context_text TEXT,
            latin_inflection TEXT,
            thesis_page INTEGER,
            confidence TEXT CHECK(confidence IN (
                'HIGH','MEDIUM','LOW','PROVISIONAL'
            )) DEFAULT 'MEDIUM',
            source_method TEXT CHECK(source_method IN (
                'CORPUS_EXTRACTION','LLM_ASSISTED','VISION_MODEL',
                'MANUAL_TRANSCRIPTION','INFERRED'
            )) DEFAULT 'CORPUS_EXTRACTION',
            needs_review BOOLEAN DEFAULT 1
        )
    """)

    cur.execute("""
        INSERT INTO symbol_occurrences_new
        SELECT * FROM symbol_occurrences
    """)

    cur.execute("SELECT COUNT(*) FROM symbol_occurrences_new")
    new_count = cur.fetchone()[0]
    assert new_count == row_count, \
        f"Row count mismatch: {row_count} -> {new_count}"

    cur.execute("DROP TABLE symbol_occurrences")
    cur.execute("ALTER TABLE symbol_occurrences_new RENAME TO symbol_occurrences")
    conn.commit()
    print(f"  Migrated symbol_occurrences: {row_count} rows, source_method now has CHECK constraint")


def create_staging_dirs():
    """Create staging directories for raw API responses."""
    dirs = [
        STAGING_DIR / "bl" / "phase1",
        STAGING_DIR / "bl" / "phase2",
        STAGING_DIR / "bl" / "phase3",
        STAGING_DIR / "siena" / "phase4",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"  Created staging directories under {STAGING_DIR}")


def main():
    print(f"=== Migration v{TARGET_VERSION}: Image Reading Infrastructure ===\n")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")

    if not check_version(conn):
        conn.close()
        return

    print("\n1. Creating image_readings table...")
    create_image_readings(conn)

    print("\n2. Expanding annotations.source_method CHECK...")
    migrate_annotations(conn)

    print("\n3. Expanding matches.confidence CHECK...")
    migrate_matches(conn)

    print("\n4. Adding woodcuts.source_method CHECK...")
    migrate_woodcuts(conn)

    print("\n5. Adding symbol_occurrences.source_method CHECK...")
    migrate_symbol_occurrences(conn)

    print("\n6. Creating staging directories...")
    create_staging_dirs()

    print("\n7. Recording schema version...")
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
        (TARGET_VERSION,)
    )
    conn.commit()

    # Verify
    print("\n=== Verification ===")
    cur = conn.cursor()
    for table in ['annotations', 'matches', 'woodcuts', 'symbol_occurrences', 'image_readings']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table}: {cur.fetchone()[0]} rows")

    # Test the CHECK constraints
    tests = [
        ("annotations", "INSERT INTO annotations (signature_ref, source_method) VALUES ('__verify__', 'VISION_MODEL')"),
        ("matches", "INSERT INTO matches (ref_id, image_id, confidence) VALUES (1, 1, 'PROVISIONAL')"),
    ]
    for table, sql in tests:
        try:
            cur.execute(sql)
            cur.execute(f"DELETE FROM {table} WHERE source_method = 'VISION_MODEL' OR confidence = 'PROVISIONAL'")
            conn.commit()
            print(f"  CHECK test passed: {table}")
        except Exception as e:
            print(f"  CHECK test FAILED: {table} — {e}")

    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()
    print(f"\n=== Migration v{TARGET_VERSION} complete ===")


if __name__ == "__main__":
    main()
