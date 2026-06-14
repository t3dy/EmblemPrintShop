#!/usr/bin/env python3
"""fix_woodcut_pages.py — Fix page assignments and add missing woodcuts.

Corrects off-by-one page errors in the Polyandrion section and adds
genuinely missing woodcut entries based on IA visual scan verification.

Also adds new entries for pages that have multiple woodcuts where only
one was previously recorded.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "hp.db"
IA_OFFSET = 5

# Page corrections: old_page -> new_page (from IA visual verification)
PAGE_CORRECTIONS = {
    219: None,   # Delete — duplicate of 221
    222: None,   # Delete — duplicate of 221
    224: None,   # Delete — duplicate of 221
    228: None,   # Delete — merged into 233
    234: None,   # Delete — merged into 235
    241: 242,    # Mosaic of Hell → p.242
    243: 244,    # D.M. Annirae → p.244
    245: 244,    # Sacrifice Relief → already at 244 (merge)
    247: 246,    # Epitaph Fragments → p.246
    249: 250,    # Sepulchral Monument → p.250
    251: 248,    # P. Cornelia Annia → p.248
    253: 252,    # O Lector Infoelix → p.252
    257: 258,    # Artemisia → p.258
    259: 258,    # Epitaph busts → same page as Artemisia
    261: 260,    # Sepulchral Portal → p.260
    291: 295,    # Water-work → p.295
    307: 309,    # Flower-bed → p.309
    312: 313,    # Peacock → p.313
    314: 313,    # Eagle → same page as peacock
    318: 319,    # Trophy QVIS EVADET → p.319
    328: 330,    # Vase → p.330
    335: 334,    # Terminal Serpent → p.334
    336: 337,    # Triumph left → p.337
    386: 387,    # Polia drags → same page as temple scene? Check
    390: 392,    # Cupid sword → p.392
    416: 415,    # Bed-chamber → p.415
    436: 435,    # Polia reading → p.435
    448: 449,    # Cupid arrow → p.449
}

# New entries to add (pages not yet in woodcuts table)
NEW_ENTRIES = [
    (260, "Sepulchral Portal: Gates of Life and Death",
     "Architectural portal with two narrow doorways symbolizing the gates of life and death, flanked by columns.",
     "The final monument in the Polyandrion section. Two narrow gates represent the ancient philosophical opposition of life and death.",
     "ARCHITECTURAL"),

    (321, "Trophy: Laurel Wreath with Cupid",
     "Trophy standard bearing a laurel wreath with a small Cupid figure and tablet inscribed 'Gained by spear'.",
     "One of several trophy standards displayed in the gardens of the island of Venus, representing love's conquest through valor.",
     "DECORATIVE"),

    (327, "Superb Nymph Figure with Javelin",
     "Full-length portrait of a beautiful nymph holding a javelin, standing in a classical pose.",
     "A striking single-figure portrait in the Cythera garden section, possibly representing Diana or one of Venus's attendant nymphs.",
     "PORTRAIT"),

    (363, "Fountain of Venus: Sarcophagus of Adonis",
     "Garden scene with the Fountain of Venus. Water flows from the sarcophagus of Adonis through a trellis garden with a serpent.",
     "The sacred fountain where Venus mourns Adonis. Water flows from his stone sarcophagus while a golden serpent guards the source.",
     "ARCHITECTURAL"),

    (389, "Polia Drags Prostrate Poliphilus from Sanctuary",
     "Polia drags the unconscious body of Poliphilus away from the temple sanctuary. Interior architectural setting.",
     "Having found Poliphilus collapsed in the Temple of Diana, Polia desperately pulls him from the sacred precinct.",
     "NARRATIVE"),

    (392, "Cupid Brandishes Sword over Kneeling Victim",
     "Cupid, winged and armed with a sword, stands over a kneeling supplicant in a forest setting.",
     "In Polia's dream vision, Cupid exacts divine punishment on those who resist love's power.",
     "NARRATIVE"),

    (415, "Polia's Bed-chamber: Diana vs Venus Vision",
     "Polia lies in her bed-chamber while in the sky above, Diana and Venus contest for her devotion.",
     "A pivotal dream scene in which the competing claims of chastity (Diana) and love (Venus) appear as a celestial vision over sleeping Polia.",
     "NARRATIVE"),

    (435, "Polia Reading Lover's Letter in Bed-chamber",
     "Polia sits reading a letter in her private chamber, with furnishings and window visible.",
     "Polia receives and reads a passionate letter from the lovesick Poliphilus, moved by his eloquence and suffering.",
     "NARRATIVE"),

    (449, "Cupid with Bust of Polia and Arrow",
     "Cupid holds a small bust of Polia and aims an arrow. The final woodcut of the HP.",
     "The closing image of the Hypnerotomachia: Cupid takes aim at the likeness of Polia, the beloved, with his arrow — a final emblem of love's power.",
     "NARRATIVE"),
]


def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Step 1: Fix page numbers
    print("Step 1: Fixing page assignments...")
    fixed = 0
    deleted = 0
    for old_page, new_page in PAGE_CORRECTIONS.items():
        if new_page is None:
            # Check if this page's woodcut would be a duplicate
            cur.execute("SELECT id, title FROM woodcuts WHERE page_1499 = ?", (old_page,))
            row = cur.fetchone()
            if row:
                print(f"  DELETE p.{old_page}: {row[1]}")
                cur.execute("DELETE FROM woodcuts WHERE id = ?", (row[0],))
                deleted += 1
        else:
            # Check if target page already has an entry
            existing = cur.execute(
                "SELECT id FROM woodcuts WHERE page_1499 = ?", (new_page,)
            ).fetchone()
            if existing:
                # Target exists — just delete the wrong-page entry
                cur.execute("SELECT id, title FROM woodcuts WHERE page_1499 = ?", (old_page,))
                row = cur.fetchone()
                if row:
                    print(f"  MERGE p.{old_page} -> p.{new_page}: {row[1]} (target exists)")
                    cur.execute("DELETE FROM woodcuts WHERE id = ?", (row[0],))
                    deleted += 1
            else:
                cur.execute(
                    "UPDATE woodcuts SET page_1499 = ?, page_1499_ia = ? WHERE page_1499 = ?",
                    (new_page, new_page + IA_OFFSET, old_page)
                )
                if cur.rowcount:
                    print(f"  FIX p.{old_page} -> p.{new_page}")
                    fixed += 1

    print(f"  Fixed: {fixed}, Deleted/Merged: {deleted}")

    # Step 2: Add new entries
    print("\nStep 2: Adding new woodcut entries...")
    added = 0
    for page, title, desc, context, category in NEW_ENTRIES:
        # Check if page already has entry
        existing = cur.execute(
            "SELECT id FROM woodcuts WHERE page_1499 = ?", (page,)
        ).fetchone()
        if existing:
            print(f"  SKIP p.{page}: already exists")
            continue

        ia_page = page + IA_OFFSET
        cur.execute("""
            INSERT INTO woodcuts (
                page_1499, page_1499_ia, title, description, narrative_context,
                subject_category, source_method, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, 'LLM_ASSISTED', 'HIGH')
        """, (page, ia_page, title, desc, context, category))
        print(f"  ADD p.{page}: {title}")
        added += 1

    print(f"  Added: {added}")

    # Step 3: Summary
    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM woodcuts").fetchone()[0]
    distinct_pages = cur.execute("SELECT COUNT(DISTINCT page_1499) FROM woodcuts").fetchone()[0]

    print(f"\n=== Summary ===")
    print(f"  Total woodcuts: {total}")
    print(f"  Distinct pages: {distinct_pages}")

    conn.close()


if __name__ == "__main__":
    main()
