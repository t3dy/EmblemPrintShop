#!/usr/bin/env python3
"""
Build a concept/motif cross-reference index from extracted data.

Creates concept_index.json with:
- All discovered concepts/motifs and which emblems contain them
- Cross-references between concepts
- Frequency/prominence scoring

This enables rich scholarly discovery: find all emblems mentioning "mercury",
or all concepts related to "distillation".
"""
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
CATALOG_PATH = ROOT / "prototype" / "gallery_catalog.json"
TEXT_CHAPTERS_PATH = ROOT / "prototype" / "text_chapters.json"
OUTPUT_PATH = ROOT / "prototype" / "concept_index.json"

# Alchemical concepts vocabulary (can be extended)
CONCEPTS = {
    # Materials & substances
    "mercury": ["mercury", "quicksilver", "spiritus", "volatile"],
    "sulphur": ["sulphur", "sulfer", "salt", "fixed"],
    "salt": ["salt", "earth", "fixed"],
    "gold": ["gold", "sol", "king", "reddening"],
    "silver": ["silver", "luna", "queen", "whitening"],
    "lead": ["lead", "saturn"],
    "copper": ["copper", "venus"],
    "tin": ["tin", "jupiter"],
    "iron": ["iron", "mars"],

    # Operations & processes
    "distillation": ["distillation", "distill", "sublimation"],
    "calcination": ["calcination", "calcine", "burning"],
    "fermentation": ["fermentation", "ferment"],
    "dissolution": ["dissolution", "dissolve"],
    "coagulation": ["coagulation", "coagulate", "precipitation"],
    "putrefaction": ["putrefaction", "decay", "blackening"],
    "separation": ["separation", "separate"],
    "conjunction": ["conjunction", "coniunctio", "union", "marriage"],

    # Stages of the Work (Great Work)
    "nigredo": ["nigredo", "blackening"],
    "albedo": ["albedo", "whitening", "whitening"],
    "citrinitas": ["citrinitas", "yellowing"],
    "rubedo": ["rubedo", "reddening", "red stone"],

    # Philosophical concepts
    "prima materia": ["prima materia", "first matter", "primal matter"],
    "philosopher's stone": ["philosopher's stone", "stone of the philosophers", "lapis"],
    "elixir": ["elixir"],
    "tincture": ["tincture"],
    "hermaphrodite": ["hermaphrodite", "androgyne"],
    "unity": ["unity", "unus", "one"],

    # Mythological/symbolic figures
    "ouroboros": ["ouroboros", "uroboros", "serpent"],
    "phoenix": ["phoenix"],
    "dragon": ["dragon"],
    "hermetic": ["hermetic", "hermes", "mercury"],
    "solar": ["solar", "sun", "helios"],
    "lunar": ["lunar", "moon", "luna"],
    "royal": ["royal", "king", "queen"],
}


def load_catalog() -> list:
    """Load gallery catalog records."""
    if not CATALOG_PATH.exists():
        return []
    d = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return d.get("records", [])


def load_text_chapters() -> list:
    """Load extracted text chapters."""
    if not TEXT_CHAPTERS_PATH.exists():
        return []
    return json.loads(TEXT_CHAPTERS_PATH.read_text(encoding="utf-8"))


def extract_concepts(text: str, label: str = "") -> set:
    """Extract concept mentions from text."""
    text_lower = text.lower() + " " + label.lower()
    found = set()

    for concept, keywords in CONCEPTS.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                found.add(concept)
                break

    return found


def build_concept_index() -> dict:
    """Build comprehensive concept index."""
    records = load_catalog()
    chapters = load_text_chapters()

    # Index concepts to records
    concept_records = defaultdict(list)
    record_concepts = {}

    for record in records:
        label = record.get("object_label", "")
        tags = record.get("tags", [])
        # Tags are already parsed/cleaned; treat them as concepts
        concepts = set(tags)

        # Also search discourse/text if available
        record_id = record.get("emblem_id", "")
        record_concepts[record_id] = list(concepts)

        for concept in concepts:
            concept_records[concept].append({
                "emblem_id": record_id,
                "label": label,
                "project": record.get("project", ""),
                "image": record.get("transparent_png_web", ""),
            })

    # Index concepts in chapters
    concept_chapters = defaultdict(list)
    for chapter in chapters:
        text = chapter.get("excerpt", "")
        title = chapter.get("title", "")
        concepts = extract_concepts(text, title)

        for concept in concepts:
            concept_chapters[concept].append({
                "chapter": chapter.get("stem", ""),
                "book": chapter.get("book_slug", ""),
                "title": title,
            })

    # Build cross-references (which concepts are often mentioned together)
    concept_pairs = defaultdict(int)
    for emblem_concepts in record_concepts.values():
        for i, c1 in enumerate(emblem_concepts):
            for c2 in emblem_concepts[i + 1 :]:
                key = tuple(sorted([c1, c2]))
                concept_pairs[key] += 1

    # Build final index
    index = {
        "concepts": {},
        "statistics": {
            "total_concepts": 0,
            "total_emblems": len(records),
            "total_chapters": len(chapters),
        },
    }

    all_concepts = set(concept_records.keys()) | set(concept_chapters.keys())
    for concept in sorted(all_concepts):
        records_list = concept_records.get(concept, [])
        chapters_list = concept_chapters.get(concept, [])

        index["concepts"][concept] = {
            "records_count": len(records_list),
            "chapters_count": len(chapters_list),
            "records": records_list[:20],  # Top 20 emblems
            "chapters": chapters_list[:10],  # Top 10 chapters
            "related": [
                {"concept": other, "count": count}
                for (c1, other), count in concept_pairs.items()
                if c1 == concept
            ]
            + [
                {"concept": c1, "count": count}
                for (c1, c2), count in concept_pairs.items()
                if c2 == concept
            ],
        }

    index["statistics"]["total_concepts"] = len(index["concepts"])

    return index


def main():
    print("Building concept index...")
    index = build_concept_index()

    OUTPUT_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {index['statistics']['total_concepts']} concepts to {OUTPUT_PATH.name}")
    print(f"  - {index['statistics']['total_emblems']} emblems indexed")
    print(f"  - {index['statistics']['total_chapters']} chapters indexed")


if __name__ == "__main__":
    main()
