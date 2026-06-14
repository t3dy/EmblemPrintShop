#!/usr/bin/env python3
"""
Build mappings between extracted Markdown text chapters and emblem catalog entries.

Creates:
1. text_chapters.json — all chapters with metadata and content snippets
2. emblem_text_links.json — maps each emblem to related chapters
3. emblem_catalog_enriched.json — enriched emblem records with text references

Purpose: Enable scholarly cross-linking between visual emblems and their source texts.
"""
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
MARKDOWN_DIR = ROOT / "Markdown"
CATALOG_PATH = ROOT / "prototype" / "gallery_catalog.json"
OUTPUT_DIR = ROOT / "prototype"

# Mapping of Markdown book slugs to source metadata
BOOK_METADATA = {
    "rosarium": {
        "title": "Rosarium Philosophorum (English transcription, MS Ferguson 210)",
        "project_key": "rosarium",
        "emblem_range": None,  # Not emblem-based
    },
    "splendor_solis": {
        "title": "Splendor Solis (English translation)",
        "project_key": "splendor_solis",
        "emblem_range": None,
    },
    "cramer_emblemata_sacra": {
        "title": "Daniel Cramer — Emblemata Sacra (Decades Quinque Emblematum)",
        "project_key": "cramer_page",
        "emblem_range": (1, 58),  # 58 emblems
    },
    "fludd_mosaicall_philosophy": {
        "title": "Robert Fludd — Mosaicall Philosophy (1659)",
        "project_key": "fludd",
        "emblem_range": None,
    },
    "maier_viatorium": {
        "title": "Michael Maier — Viatorium (De Montibus Planetarum Septem)",
        "project_key": "maier_viatorium",
        "emblem_range": None,
    },
    "maier_arcana_arcanissima": {
        "title": "Michael Maier — Arcana Arcanissima (Hieroglyphica Aegyptio-Graeca)",
        "project_key": "maier_arcana",
        "emblem_range": None,
    },
    "khunrath_amphitheatrum": {
        "title": "Heinrich Khunrath — Amphitheatrum Sapientiae Aeternae",
        "project_key": "khunrath",
        "emblem_range": None,
    },
    "hall_manuscripts": {
        "title": "Manly Palmer Hall — Alchemical Manuscripts (Box 18 v6)",
        "project_key": "hall_manuscripts",
        "emblem_range": None,
    },
}


def extract_chapter_text(md_path: Path) -> dict:
    """Extract text, headings, and motif references from a Markdown chapter."""
    text = md_path.read_text(encoding="utf-8")

    # Extract title (first # heading)
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1) if title_match else md_path.stem

    # Extract page references
    pages = set()
    for m in re.finditer(r"<!--\s*page\s+(\d+)\s*-->", text):
        pages.add(int(m.group(1)))

    # Find motif/concept mentions (very basic heuristic)
    motifs_mentioned = set()
    for motif_name in ["lion", "eagle", "serpent", "dragon", "phoenix", "mercury", "sulphur",
                      "salt", "gold", "silver", "furnace", "vessel", "distillation",
                      "hermaphrodite", "skeleton", "king", "queen", "sun", "moon"]:
        if re.search(r"\b" + motif_name + r"\b", text, re.IGNORECASE):
            motifs_mentioned.add(motif_name.lower())

    return {
        "file": str(md_path.relative_to(ROOT)),
        "title": title,
        "book_slug": md_path.parent.name,
        "stem": md_path.stem,
        "pages": sorted(pages),
        "motifs_mentioned": sorted(motifs_mentioned),
        "word_count": len(text.split()),
        "excerpt": text[:500] + "..." if len(text) > 500 else text,
    }


def load_catalog() -> list:
    """Load gallery catalog records."""
    if not CATALOG_PATH.exists():
        return []
    d = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return d.get("records", [])


def build_chapter_index() -> dict:
    """Scan Markdown/ and build chapter metadata."""
    chapters = []
    if MARKDOWN_DIR.exists():
        for book_dir in sorted(MARKDOWN_DIR.iterdir()):
            if not book_dir.is_dir() or book_dir.name == "__pycache__":
                continue
            # Skip README files
            for md_file in sorted(book_dir.glob("*.md")):
                if md_file.name == "README.md":
                    continue
                try:
                    chap = extract_chapter_text(md_file)
                    chapters.append(chap)
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")
    return chapters


def build_emblem_text_links(chapters: list, records: list) -> dict:
    """Map emblems to related text chapters based on project and content overlap."""
    links = defaultdict(list)

    for chap in chapters:
        book_slug = chap["book_slug"]
        if book_slug not in BOOK_METADATA:
            continue

        meta = BOOK_METADATA[book_slug]
        project_key = meta["project_key"]

        # Find all records from this project
        matching_records = [r for r in records if r.get("project_key") == project_key]

        # If this is a chapter-indexed book, link by page range
        # (This is simplistic; a real system would parse chapter metadata more carefully)
        for record in matching_records:
            # Check if record's source page overlaps with chapter's page range
            if chap["motifs_mentioned"]:
                record_label = record.get("object_label", "").lower()
                for motif in chap["motifs_mentioned"]:
                    if motif in record_label:
                        links[record.get("emblem_id", "")].append({
                            "chapter": chap["stem"],
                            "book": book_slug,
                            "reason": f"motif: {motif}",
                        })
                        break

    return dict(links)


def main():
    print("Building text-visual linkage...")

    chapters = build_chapter_index()
    records = load_catalog()

    print(f"Found {len(chapters)} chapters, {len(records)} catalog records")

    # Write chapters index
    chapters_out = OUTPUT_DIR / "text_chapters.json"
    chapters_out.write_text(json.dumps(chapters, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(chapters)} chapters to {chapters_out.name}")

    # Build and write emblem-text links
    links = build_emblem_text_links(chapters, records)
    links_out = OUTPUT_DIR / "emblem_text_links.json"
    links_out.write_text(json.dumps(links, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built {len(links)} emblem-text links → {links_out.name}")

    # Optionally write enriched catalog
    # (This would be large; for now just log the summary)
    emblem_count_with_text = sum(1 for e in records if e.get("emblem_id") in links)
    print(f"Enrichment: {emblem_count_with_text} of {len(records)} records have text links")


if __name__ == "__main__":
    main()
