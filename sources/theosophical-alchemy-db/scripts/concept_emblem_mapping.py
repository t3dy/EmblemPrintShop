#!/usr/bin/env python3
"""
Concept-Emblem Bidirectional Mapping
Maps 60 concepts to 2-3+ emblems each, creating reciprocal links

Strategy:
1. Load all concepts and emblems from database
2. For each concept, identify matching emblems via:
   - Direct keyword match (concept name in emblem description)
   - Alchemical stage match (concept stage = emblem stage)
   - Thematic match (scholarly analysis of concept-emblem relationship)
3. Create bidirectional links: concept→emblem and emblem→concept
4. Verify coverage: each concept ≥2 emblems, each emblem ≥2 concepts
"""

import json
from pathlib import Path
from collections import defaultdict

def load_database():
    """Load TheosophicalAlchemyDB"""
    with open('data/prototype_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_concept_emblem_relationships(db):
    """
    Analyze which emblems relate to which concepts
    Uses heuristic matching on:
    - Concept key_concepts field
    - Emblem alchemical_processes field
    - Alchemical stage matching
    - Related concept themes
    """

    concepts = db.get('concepts', [])
    emblems = db.get('emblems', [])

    concept_emblem_map = defaultdict(list)
    emblem_concept_map = defaultdict(list)

    # Collect all emblem concepts
    emblem_concepts_set = set()
    for emblem in emblems:
        for concept in emblem.get('key_concepts', []):
            emblem_concepts_set.add(concept.lower())

    # For each concept, find matching emblems
    for concept in concepts:
        concept_id = concept.get('id', '')
        concept_name = concept.get('name', '').lower()
        concept_keywords = set(concept.get('key_concepts', []))
        concept_stage = concept.get('alchemical_stage', '').lower()

        matching_emblems = []

        for emblem in emblems:
            emblem_id = emblem.get('id', '')
            emblem_name = emblem.get('title', '').lower()
            emblem_processes = [p.lower() for p in emblem.get('alchemical_processes', [])]
            emblem_stage = emblem.get('alchemical_stage', '').lower()
            emblem_concepts = [c.lower() for c in emblem.get('key_concepts', [])]

            match_score = 0
            match_reasons = []

            # Direct name match
            if concept_name in emblem_name or emblem_name in concept_name:
                match_score += 3
                match_reasons.append('name_match')

            # Concept keyword in emblem concepts
            for keyword in concept_keywords:
                if keyword.lower() in emblem_concepts:
                    match_score += 2
                    match_reasons.append(f'keyword:{keyword}')

            # Alchemical stage match
            if concept_stage and emblem_stage:
                if concept_stage in emblem_stage or emblem_stage in concept_stage:
                    match_score += 1
                    match_reasons.append('stage_match')

            # Add strong matches (score >= 2)
            if match_score >= 2:
                matching_emblems.append({
                    'emblem_id': emblem_id,
                    'score': match_score,
                    'reasons': match_reasons
                })

        # Sort by score and take top 3-5
        matching_emblems.sort(key=lambda x: x['score'], reverse=True)
        matching_emblems = matching_emblems[:5]

        if matching_emblems:
            concept_emblem_map[concept_id] = matching_emblems

            # Create reciprocal emblem→concept links
            for match in matching_emblems:
                emblem_concept_map[match['emblem_id']].append(concept_id)

    return concept_emblem_map, emblem_concept_map

def main():
    print("=" * 70)
    print("CONCEPT-EMBLEM BIDIRECTIONAL MAPPING ANALYSIS")
    print("=" * 70)

    # Load database
    print("\nLoading database...")
    db = load_database()

    concepts = db.get('concepts', [])
    emblems = db.get('emblems', [])

    print(f"  Concepts: {len(concepts)}")
    print(f"  Emblems: {len(emblems)}")

    # Analyze relationships
    print("\nAnalyzing concept-emblem relationships...")
    concept_emblem_map, emblem_concept_map = analyze_concept_emblem_relationships(db)

    print(f"  Concepts with emblem links: {len(concept_emblem_map)}")
    print(f"  Emblems with concept links: {len(emblem_concept_map)}")

    # Coverage analysis
    concept_coverage = len([c for c in concepts if c.get('id') in concept_emblem_map])
    emblem_coverage = len([e for e in emblems if e.get('id') in emblem_concept_map])

    print(f"\nCoverage:")
    print(f"  Concepts with ≥1 emblem link: {concept_coverage}/{len(concepts)} ({100*concept_coverage//len(concepts)}%)")
    print(f"  Emblems with ≥1 concept link: {emblem_coverage}/{len(emblems)} ({100*emblem_coverage//len(emblems)}%)")

    # Statistics
    avg_emblems_per_concept = sum(len(m) for m in concept_emblem_map.values()) / max(1, len(concept_emblem_map))
    avg_concepts_per_emblem = sum(len(c) for c in emblem_concept_map.values()) / max(1, len(emblem_concept_map))

    print(f"\nStatistics:")
    print(f"  Avg emblems per concept: {avg_emblems_per_concept:.1f}")
    print(f"  Avg concepts per emblem: {avg_concepts_per_emblem:.1f}")
    print(f"  Total concept-emblem links: {sum(len(m) for m in concept_emblem_map.values())}")

    # Sample mappings
    print(f"\nSample concept-emblem mappings:")
    for i, (concept_id, emblems_list) in enumerate(list(concept_emblem_map.items())[:3]):
        concept = next((c for c in concepts if c.get('id') == concept_id), {})
        print(f"\n  {concept.get('name', 'Unknown')}:")
        for emblem_ref in emblems_list[:2]:
            emblem = next((e for e in emblems if e.get('id') == emblem_ref['emblem_id']), {})
            print(f"    - {emblem.get('title', 'Unknown')} (score: {emblem_ref['score']})")

    print(f"\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nRecommendation:")
    if concept_coverage < len(concepts) * 0.8:
        print(f"  [{concept_coverage}/{len(concepts)} concepts mapped]")
        print(f"  Status: NEEDS MANUAL REFINEMENT")
        print(f"  Use Agent to intelligently match unmapped concepts to emblems")
    else:
        print(f"  Status: READY FOR INTEGRATION")
        print(f"  Run: integrate_concept_emblem_links.py")

if __name__ == '__main__':
    main()
