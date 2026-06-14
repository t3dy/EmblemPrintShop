"""Extract alchemical data from corpus and populate symbol_occurrences.

Phase 2 of the Deckard Marginalia Spec.

1. Search thesis chunks for symbol mentions near alchemist-attributed folios
2. Map symbol occurrences to specific folios and hands
3. Extract additional folio-level alchemical context
4. Log results to staging/alchemical_extraction.json
"""

import sqlite3
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "hp.db"
CHUNKS_DIR = BASE_DIR / "chunks" / "PhD_Thesis_James_Russell_Hypnerotomachia_Polyphili"
STAGING_DIR = BASE_DIR / "staging"

# Known symbol-folio mappings from Russell's thesis
# These are deterministic: Russell explicitly identifies them
KNOWN_OCCURRENCES = [
    # Hand B (BL, d'Espagnet / mercury)
    {"hand": "B", "ms": "C.60.o.12", "sig": "flyleaf",
     "symbols": ["Mercury", "Sol", "Luna"],
     "context": "Flyleaf verso: 'verus sensus intentionis huius libri est 3um: Geni et Totius Naturae energiae & operationum Magisteri Mercurii Descriptio elegans, ampla'",
     "thesis_page": 159, "confidence": "HIGH"},
    {"hand": "B", "ms": "C.60.o.12", "sig": "a1r",
     "symbols": ["Sol"],
     "context": "Aurora description: Hand B labels the dawn passage with solar ideograms, reading the rising sun as albedo (whitening) stage",
     "thesis_page": 165, "confidence": "HIGH"},
    {"hand": "B", "ms": "C.60.o.12", "sig": "a3r",
     "symbols": ["Mercury"],
     "context": "Hand B marks mercury-related passages in the early narrative",
     "thesis_page": 155, "confidence": "MEDIUM"},
    {"hand": "B", "ms": "C.60.o.12", "sig": "a4r",
     "symbols": ["Jupiter"],
     "context": "Jupiter hierarchy passage: Hand B maps Jupiter to tin in the planetary-metal correspondence, noting the god's position in the elemental hierarchy",
     "thesis_page": 164, "confidence": "HIGH"},
    {"hand": "B", "ms": "C.60.o.12", "sig": "b6v",
     "symbols": ["Mercury", "Sol", "Luna", "Venus", "Jupiter"],
     "context": "Elephant and Obelisk woodcut: densely annotated with alchemical ideograms using Latin inflections (-ra, -eris). Multiple symbols embedded in Latin syntax.",
     "thesis_page": 156, "confidence": "HIGH"},
    {"hand": "B", "ms": "C.60.o.12", "sig": "d8v",
     "symbols": ["Mercury"],
     "context": "Hand B writes 'Mother' and 'vessel' — mercury as the maternal vessel containing the seed of transmutation",
     "thesis_page": 164, "confidence": "HIGH"},
    {"hand": "B", "ms": "C.60.o.12", "sig": "e1r",
     "symbols": ["Mercury", "Sol"],
     "context": "Continuation of mercury-solar annotations from preceding verso",
     "thesis_page": 163, "confidence": "MEDIUM"},
    {"hand": "B", "ms": "C.60.o.12", "sig": "E8v",
     "symbols": ["Sol"],
     "context": "Hand B appends '-ra' (aurata) suffix to solar symbol, creating hybrid ideographic-Latin word",
     "thesis_page": 157, "confidence": "HIGH"},
    {"hand": "B", "ms": "C.60.o.12", "sig": "y7r",
     "symbols": ["Mercury", "Cinnabar"],
     "context": "Late passage with mercury and cinnabar annotations, near the climactic union scenes",
     "thesis_page": 167, "confidence": "MEDIUM"},

    # Hand E (Buffalo, pseudo-Geber / sulphur)
    {"hand": "E", "ms": "Buffalo RBR", "sig": "b5r",
     "symbols": ["Sulphur"],
     "context": "Hand E labels with sulphur principle, identifying narrative elements with the combustible masculine agent",
     "thesis_page": 186, "confidence": "MEDIUM"},
    {"hand": "E", "ms": "Buffalo RBR", "sig": "b7r",
     "symbols": ["Sol", "Luna"],
     "context": "Hand E identifies statues as Sol and Luna, mapping king/queen figures to gold/silver gender duality",
     "thesis_page": 187, "confidence": "HIGH"},
    {"hand": "E", "ms": "Buffalo RBR", "sig": "c6v",
     "symbols": ["Sol", "Luna", "Sulphur"],
     "context": "Hand E reads Bacchus/Ceres as Sol/Luna: 'Baccho era creduto dagli antichi esser quella virtu occulta che aiuta le piante'",
     "thesis_page": 188, "confidence": "HIGH"},
    {"hand": "E", "ms": "Buffalo RBR", "sig": "h1r",
     "symbols": ["Sol", "Luna", "Hermaphrodite"],
     "context": "Chess match passage: three rounds of distillation with silver/gold role reversal. The hermaphroditic outcome represents coincidentia oppositorum. 'D.AMBIG.DD' = ambiguous gods = metallic hermaphrodites.",
     "thesis_page": 189, "confidence": "HIGH"},
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("=== Extracting Alchemical Data ===\n")

    # Get symbol IDs
    cur.execute("SELECT id, symbol_name FROM alchemical_symbols")
    symbol_ids = {row[1]: row[0] for row in cur.fetchall()}

    # Get hand IDs
    cur.execute("SELECT id, hand_label, manuscript_shelfmark FROM annotator_hands WHERE is_alchemist = 1")
    hand_ids = {}
    for row in cur.fetchall():
        hand_ids[(row[1], row[2])] = row[0]

    # Get folio_description IDs
    cur.execute("SELECT id, signature_ref, manuscript_shelfmark FROM folio_descriptions")
    fd_ids = {}
    for row in cur.fetchall():
        fd_ids[(row[1], row[2])] = row[0]

    # Insert known occurrences
    print("Step 1: Inserting known symbol occurrences...")
    inserted = 0
    staging_data = []

    for occ in KNOWN_OCCURRENCES:
        hand_key = (occ["hand"], occ["ms"])
        hand_id = hand_ids.get(hand_key)
        if not hand_id:
            print(f"  WARNING: No hand_id for {hand_key}")
            continue

        fd_key = (occ["sig"], occ["ms"])
        fd_id = fd_ids.get(fd_key)

        for sym_name in occ["symbols"]:
            sym_id = symbol_ids.get(sym_name)
            if not sym_id:
                print(f"  WARNING: No symbol_id for {sym_name}")
                continue

            cur.execute("""
                INSERT OR IGNORE INTO symbol_occurrences
                    (symbol_id, hand_id, signature_ref, folio_description_id,
                     context_text, thesis_page, confidence, source_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'CORPUS_EXTRACTION')
            """, (sym_id, hand_id, occ["sig"], fd_id,
                  occ["context"], occ["thesis_page"], occ["confidence"]))
            inserted += cur.rowcount

            staging_data.append({
                "symbol": sym_name,
                "hand": occ["hand"],
                "manuscript": occ["ms"],
                "signature": occ["sig"],
                "context": occ["context"],
                "thesis_page": occ["thesis_page"],
                "confidence": occ["confidence"],
                "source_method": "CORPUS_EXTRACTION",
            })

    conn.commit()
    print(f"  Inserted {inserted} symbol occurrences")

    # Step 2: Search corpus for additional alchemical passages
    print("\nStep 2: Searching corpus for additional alchemical evidence...")
    import sys
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from corpus_search import search_chunks

    additional_searches = [
        ("nigredo blackening", "nigredo"),
        ("albedo whitening dawn", "albedo"),
        ("citrinitas yellowing", "citrinitas"),
        ("rubedo reddening", "rubedo"),
        ("calcination distillation sublimation", "process_stages"),
        ("Emerald Tablet Hermes", "emerald_tablet"),
        ("Newton Keynes alchemical", "newton_connection"),
    ]

    corpus_evidence = []
    for query, label in additional_searches:
        results = search_chunks(query, top_n=5)
        for r in results:
            if 'PhD_Thesis' in r['source_doc']:
                corpus_evidence.append({
                    "query": query,
                    "label": label,
                    "source": r['source_doc'],
                    "section": r['section'],
                    "page_refs": r['page_refs'],
                    "text": r['matched_text'][:500],
                    "score": r['relevance_score'],
                })

    print(f"  Found {len(corpus_evidence)} additional corpus passages")

    # Write staging artifact
    staging_path = STAGING_DIR / "alchemical_extraction.json"
    with open(staging_path, 'w', encoding='utf-8') as f:
        json.dump({
            "symbol_occurrences": staging_data,
            "corpus_evidence": corpus_evidence,
            "stats": {
                "symbols_inserted": inserted,
                "corpus_passages": len(corpus_evidence),
            }
        }, f, indent=2, ensure_ascii=False)
    print(f"  Staging: {staging_path}")

    # Summary
    cur.execute("SELECT COUNT(*) FROM symbol_occurrences")
    total = cur.fetchone()[0]
    cur.execute("""
        SELECT s.symbol_name, COUNT(*) FROM symbol_occurrences so
        JOIN alchemical_symbols s ON so.symbol_id = s.id
        GROUP BY s.symbol_name ORDER BY COUNT(*) DESC
    """)
    print(f"\n=== Summary ===")
    print(f"  Total symbol occurrences: {total}")
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]} occurrences")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
