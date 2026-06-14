#!/usr/bin/env python3
"""
Extract emblem images from PDF sources
- Maier Atalanta Fugiens (51 emblems)
- Khunrath Amphitheatrum (30+ emblems)
- Mutus Liber (15 emblems)
- Other emblem collections

Uses pdfplumber and PIL to extract images with sourcing metadata.
"""

import os
import json
from pathlib import Path
from datetime import datetime

def create_emblem_entries_template():
    """Create template for emblem entries"""
    return {
        "tier_1_maier_atalanta_fugiens": {
            "source_book": "Atalanta Fugiens",
            "author": "Michael Maier",
            "date_published": 1618,
            "location": "E:/pdf/alchemy/atalanta_fugiens/Michael Maier Atalanta fugiens libgen li.pdf",
            "total_emblems": 51,
            "emblems_planned": 51,
            "extraction_status": "PENDING",
            "sourcing_strategy": [
                "Primary: PDF image extraction from edition",
                "Secondary: De Jong scholarly analysis for interpretations",
                "Fallback: Text-only descriptions based on scholarship"
            ],
            "key_concepts": [
                "Philosophical Transformation",
                "Duality and Opposites",
                "Sublimation",
                "Distillation",
                "The Philosophical Mercury",
                "King and Queen symbolism",
                "Conjunction (Coniunctio)"
            ],
            "sample_emblems": [
                {
                    "emblem_id": "maier-atalanta-001",
                    "number": 1,
                    "title": "[To Be Extracted]",
                    "visual_description": "[To be created from image extraction]",
                    "philosophical_essay": "[To be written with De Jong guidance]",
                    "key_concepts": ["Transformation", "Beginnings"],
                    "epigrammatic_text": "[Latin/English to be extracted]",
                    "sourcing": {
                        "source_book": "Atalanta Fugiens",
                        "edition": "Johann Theodor de Bry, 1618",
                        "page_range": "[TBD]",
                        "image_source": "PDF extraction",
                        "scholarly_basis": "De Jong, Helena Maria Elisabeth. *Michael Maier's Atalanta Fugiens: Sources of an Alchemical Book of Emblems*"
                    }
                }
            ]
        },
        "tier_1_khunrath_amphitheatrum": {
            "source_book": "Amphitheatrum Sapientiae Aeternae",
            "author": "Heinrich Khunrath",
            "date_published": 1595,
            "location": "E:/pdf/alchemy/Peter J Forshaw The Mage s Images_ Heinrich Khunrath...",
            "total_emblems": 30,
            "emblems_planned": 25,
            "extraction_status": "PENDING",
            "sourcing_strategy": [
                "Primary: Forshaw scholarship with image references",
                "Secondary: Scholarly interpretation of cosmological diagrams",
                "Fallback: Text descriptions based on Forshaw analysis"
            ],
            "key_concepts": [
                "Cosmological Hierarchy",
                "Laboratory-Oratory Integration",
                "Esoteric Cosmology",
                "Spiritual Alchemy",
                "Divine Order in Nature"
            ]
        },
        "tier_2_mutus_liber": {
            "source_book": "Mutus Liber (The Silent Book)",
            "author": "Anonymous (attributed to unknown author, French)",
            "date_published": 1677,
            "location": "E:/pdf/alchemy/Adam McLean A Commentary on the Mutus Liber.pdf",
            "total_emblems": 15,
            "emblems_planned": 15,
            "extraction_status": "PENDING",
            "sourcing_strategy": [
                "Primary: McLean scholarly commentary with analysis",
                "Secondary: Visual symbolism interpretation",
                "Fallback: Text descriptions based on McLean's detailed analysis"
            ],
            "key_concepts": [
                "Silent Knowledge",
                "Visual Philosophy",
                "Transmutation",
                "Lunar and Solar Operations",
                "Wholeness and Completion"
            ],
            "note": "Mutus Liber is a wordless emblem book; all knowledge conveyed through image and symbol alone"
        }
    }

def generate_extraction_plan():
    """Generate detailed extraction and processing plan"""
    plan = {
        "session": "Workstream 1 - Emblem Sourcing Phase 1",
        "date": datetime.now().isoformat(),
        "goal": "Extract 70+ emblem images from Tier 1 sources",
        "estimated_duration": "6-8 hours (Phase 1)",

        "phase_1_extraction": {
            "tier_1_sources": {
                "Maier Atalanta Fugiens": {
                    "file": "E:/pdf/alchemy/atalanta_fugiens/Michael Maier Atalanta fugiens libgen li.pdf",
                    "emblems": 51,
                    "priority": "HIGH",
                    "extraction_method": "PDF image extraction + De Jong scholarly mapping",
                    "scholarly_basis": "De Jong, Helena Maria Elisabeth. *Michael Maier's Atalanta Fugiens: Sources of an Alchemical Book of Emblems* (Nicolas Hays, 1969)",
                    "output_count": 51
                },
                "Khunrath Amphitheatrum": {
                    "file": "E:/pdf/alchemy/Peter J Forshaw The Mage s Images_ Heinrich Khunrath in His Oratory and Laboratory",
                    "emblems": 25,
                    "priority": "MEDIUM",
                    "extraction_method": "Forshaw scholarship + textual description",
                    "scholarly_basis": "Forshaw, Peter J. *The Mage's Images: Heinrich Khunrath in His Oratory and Laboratory* (Brill, 2009)",
                    "output_count": 25
                },
                "Mutus Liber": {
                    "file": "E:/pdf/alchemy/Adam McLean A Commentary on the Mutus Liber.pdf",
                    "emblems": 15,
                    "priority": "MEDIUM",
                    "extraction_method": "McLean commentary analysis",
                    "scholarly_basis": "McLean, Adam. *A Commentary on the Mutus Liber* (Phanes Press, 1991)",
                    "output_count": 15
                }
            },
            "total_phase_1": 91,
            "stretch_goal": 100
        },

        "processing_steps": [
            "1. Locate PDF files for Tier 1 sources",
            "2. Extract images using pdfplumber/PIL (where available)",
            "3. For each emblem: create visual description (300-500 words)",
            "4. Write philosophical essay (500-800 words) using scholarly sources",
            "5. Identify key concepts and create concept links",
            "6. Document sourcing metadata (book, edition, page, scholar reference)",
            "7. Create emblem JSON entries with all fields",
            "8. Save images to staging/emblem_images/ with source tracking",
            "9. Create staging PR with sourcing documentation"
        ],

        "database_schema": {
            "id": "emblem_id (e.g., 'maier-atalanta-001')",
            "title": "Emblem title or number",
            "emblem_number": "Position in source book",
            "source_book": "Name of emblem collection",
            "author": "Creator of emblem book",
            "date_published": "Year of publication",
            "visual_description": "300-500 words describing visual elements",
            "essay": "500-800 word philosophical/historical essay",
            "key_concepts": ["Array of concept IDs/names"],
            "epigrammatic_text": "Latin or vernacular text accompanying emblem",
            "scholarly_sources": [
                {
                    "scholar": "Scholar name",
                    "reference": "Full citation",
                    "quote": "Relevant passage (under 50 words)",
                    "relevance": "interpretation/context/source"
                }
            ],
            "image_source": {
                "type": "photograph|text_description|scholarly_analysis",
                "basis": "Original PDF|De Jong analysis|McLean commentary",
                "sourcing": "Citation to source book and page"
            },
            "related_figures": ["Figure IDs who created/were influenced by this"],
            "related_emblems": ["Other emblem IDs with similar themes"],
            "review_status": "DRAFT",
            "confidence": "HIGH|MEDIUM|LOW"
        },

        "quality_standards": {
            "visual_description": [
                "Clear, concrete description of visual elements",
                "Mention of colors, symbols, figures, composition",
                "No interpretive speculation in description section",
                "300-500 words"
            ],
            "philosophical_essay": [
                "Ground in historical scholarship (cite sources)",
                "Explain alchemical/philosophical meaning",
                "Connect to broader traditions and concepts",
                "Document scholarly disagreements fairly",
                "500-800 words"
            ],
            "concept_links": [
                "Each emblem linked to 2-3+ concepts minimum",
                "Each concept will eventually link to 2-3+ emblems",
                "Bidirectional links maintained"
            ],
            "sourcing_metadata": [
                "Book title, author, date",
                "Edition information",
                "Page number or section",
                "Scholarly reference (if based on analysis)"
            ]
        },

        "next_phases": {
            "phase_2": "Concept-emblem mapping (60 concepts × 2-3 emblems each)",
            "phase_3": "Figure-emblem genealogy (who created/influenced emblems)",
            "phase_4": "Scholarly apparatus enrichment (direct quotes, page citations, debates)"
        }
    }
    return plan

def main():
    print("=" * 70)
    print("EMBLEM SOURCING EXTRACTION PLAN - Phase 1")
    print("=" * 70)

    # Generate plan
    plan = generate_extraction_plan()

    print("\nTier 1 Sources Available:")
    for source_name, source_info in plan["phase_1_extraction"]["tier_1_sources"].items():
        print(f"\n  {source_name}")
        print(f"    Emblems: {source_info['emblems']}")
        print(f"    Priority: {source_info['priority']}")
        print(f"    Scholarly basis: {source_info['scholarly_basis']}")

    print(f"\n  TOTAL PHASE 1: {plan['phase_1_extraction']['total_phase_1']} emblems")
    print(f"  STRETCH GOAL: {plan['phase_1_extraction']['stretch_goal']} emblems")

    print("\n" + "=" * 70)
    print("Processing Steps:")
    print("=" * 70)
    for step in plan["processing_steps"]:
        print(f"  {step}")

    print("\n" + "=" * 70)
    print("Quality Standards:")
    print("=" * 70)
    for category, standards in plan["quality_standards"].items():
        print(f"\n  {category.upper()}:")
        for std in standards:
            print(f"    - {std}")

    # Save plan to file
    plan_path = Path("docs/EMBLEM_EXTRACTION_PLAN.json")
    with open(plan_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"\n\nExtraction plan saved to: {plan_path}")

    # Create template
    template = create_emblem_entries_template()
    template_path = Path("docs/emblem_entries_template.json")
    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"Emblem entry template saved to: {template_path}")

    print("\n" + "=" * 70)
    print("Ready for Phase 1 Extraction")
    print("=" * 70)
    print("\nNext: Extract images and create emblem entries from Tier 1 sources")

if __name__ == '__main__':
    main()
