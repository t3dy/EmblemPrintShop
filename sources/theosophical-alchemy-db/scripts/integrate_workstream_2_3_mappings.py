#!/usr/bin/env python3
"""
Integrate Workstream 2 & 3 Mappings into Database
- Concept-emblem bidirectional links (54 mappings)
- Figure-emblem genealogy links (10 figures)

Reads JSON specifications and updates prototype_data.json
"""

import json
from pathlib import Path

def load_mapping_specifications():
    """Load concept-emblem and figure-emblem specifications"""
    concept_emblem_spec = None
    figure_emblem_spec = None

    # Try loading concept-emblem spec
    concept_spec_path = Path("docs/CONCEPT_EMBLEM_LINKS_SPECIFICATION.json")
    if concept_spec_path.exists():
        with open(concept_spec_path, 'r', encoding='utf-8') as f:
            concept_emblem_spec = json.load(f)
    else:
        print(f"Warning: {concept_spec_path} not found")

    # Try loading figure-emblem spec
    figure_spec_path = Path("docs/FIGURE_EMBLEM_GENEALOGY_SPECIFICATION.json")
    if figure_spec_path.exists():
        with open(figure_spec_path, 'r', encoding='utf-8') as f:
            figure_emblem_spec = json.load(f)
    else:
        print(f"Warning: {figure_spec_path} not found")

    return concept_emblem_spec, figure_emblem_spec

def load_database():
    """Load TheosophicalAlchemyDB"""
    with open('data/prototype_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_concept_name(name):
    """Normalize concept name for fuzzy matching"""
    if not name:
        return ""
    # Remove parenthetical descriptions and special characters
    base_name = name.split('(')[0].strip()
    # Convert to lowercase for comparison
    return base_name.lower()

def integrate_concept_emblem_links(db, concept_emblem_spec):
    """Add concept-emblem bidirectional links to database"""
    if not concept_emblem_spec:
        return 0, 0

    concepts = {c.get('id'): c for c in db.get('concepts', [])}
    # Create normalized name mapping for fuzzy lookup
    concept_names = {}
    for c in db.get('concepts', []):
        norm_name = normalize_concept_name(c.get('name', ''))
        concept_names[norm_name] = c.get('id')

    emblems = {e.get('id'): e for e in db.get('emblems', [])}

    added_concept_links = 0
    added_emblem_links = 0

    # Process concept-emblem links from mappings array
    concept_emblem_mappings = concept_emblem_spec.get('concept_emblem_links', [])

    for mapping in concept_emblem_mappings:
        concept_id = mapping.get('concept_id')
        concept_name = mapping.get('concept_name')
        emblem_links = mapping.get('emblem_links', [])

        # If concept_id is null, try to find by normalized name
        if concept_id is None and concept_name:
            norm_name = normalize_concept_name(concept_name)
            concept_id = concept_names.get(norm_name)

        if concept_id not in concepts:
            continue

        concept = concepts[concept_id]

        # Initialize emblem_links array if not present
        if 'emblem_links' not in concept:
            concept['emblem_links'] = []

        # Add emblem links to concept
        for emblem_ref in emblem_links:
            emblem_id = emblem_ref.get('emblem_id')
            if emblem_id not in [e.get('emblem_id') for e in concept.get('emblem_links', [])]:
                concept['emblem_links'].append({
                    'emblem_id': emblem_id,
                    'link_type': emblem_ref.get('link_type', 'exemplifies'),
                    'explanation': emblem_ref.get('explanation', '')
                })
                added_concept_links += 1

    # Create reciprocal emblem→concept links
    for concept_id, concept in concepts.items():
        for emblem_ref in concept.get('emblem_links', []):
            emblem_id = emblem_ref['emblem_id']
            if emblem_id not in emblems:
                continue

            emblem = emblems[emblem_id]

            # Initialize concept_links if not present
            if 'concept_links' not in emblem:
                emblem['concept_links'] = []

            # Add concept link to emblem
            if concept_id not in [c.get('concept_id') for c in emblem.get('concept_links', [])]:
                emblem['concept_links'].append({
                    'concept_id': concept_id,
                    'concept_name': concept.get('name', ''),
                    'link_type': emblem_ref.get('link_type', 'philosophical')
                })
                added_emblem_links += 1

    return added_concept_links, added_emblem_links

def integrate_figure_emblem_genealogy(db, figure_emblem_spec):
    """Add figure-emblem genealogy links to database"""
    if not figure_emblem_spec:
        return 0

    figures = {f.get('id'): f for f in db.get('figures', [])}
    added_genealogy_links = 0

    # Process figure-emblem genealogy (spec uses figures_genealogy array)
    genealogies = figure_emblem_spec.get('figures_genealogy', [])

    for genealogy in genealogies:
        figure_id = genealogy.get('figure_id')

        if figure_id not in figures:
            continue

        figure = figures[figure_id]

        # Add genealogical position
        genealogical_position = genealogy.get('genealogical_position')
        if genealogical_position:
            figure['genealogical_position'] = genealogical_position
            added_genealogy_links += 1

        # Add emblem books created (from emblem_books_created array)
        emblem_books_created = genealogy.get('emblem_books_created', [])
        if emblem_books_created:
            figure['emblem_books_created'] = emblem_books_created
            added_genealogy_links += len(emblem_books_created)

        # Add influenced_by references
        influenced_by = genealogy.get('influenced_by', [])
        if influenced_by:
            figure['influenced_by_figures'] = influenced_by
            added_genealogy_links += len(influenced_by)

        # Add influenced figures
        influenced_figures = genealogy.get('influenced_figures', [])
        if influenced_figures:
            figure['influenced_figures'] = influenced_figures
            added_genealogy_links += len(influenced_figures)

    return added_genealogy_links

def main():
    print("=" * 70)
    print("WORKSTREAM 2 & 3 INTEGRATION")
    print("=" * 70)

    # Load specifications
    print("\nLoading mapping specifications...")
    concept_emblem_spec, figure_emblem_spec = load_mapping_specifications()

    if not concept_emblem_spec:
        print("  [Warning] Concept-emblem spec not found")
    if not figure_emblem_spec:
        print("  [Warning] Figure-emblem spec not found")

    # Load database
    print("\nLoading TheosophicalAlchemyDB...")
    db = load_database()

    print(f"  Concepts: {len(db.get('concepts', []))}")
    print(f"  Emblems: {len(db.get('emblems', []))}")
    print(f"  Figures: {len(db.get('figures', []))}")

    # Integrate concept-emblem links
    print("\nIntegrating concept-emblem links...")
    concept_links_added, emblem_links_added = integrate_concept_emblem_links(db, concept_emblem_spec)
    print(f"  Concept-emblem links added: {concept_links_added}")
    print(f"  Emblem-concept links added: {emblem_links_added}")

    # Integrate figure-emblem genealogy
    print("\nIntegrating figure-emblem genealogy...")
    genealogy_links_added = integrate_figure_emblem_genealogy(db, figure_emblem_spec)
    print(f"  Figure-emblem genealogy links added: {genealogy_links_added}")

    # Save updated database
    print("\nSaving updated database...")
    with open('data/prototype_data.json', 'w', encoding='utf-8', newline='\n') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print(f"  Database saved successfully")

    print("\n" + "=" * 70)
    print("INTEGRATION COMPLETE")
    print("=" * 70)

    print(f"\nSummary:")
    print(f"  Concept-emblem links: {concept_links_added}")
    print(f"  Emblem-concept links: {emblem_links_added}")
    print(f"  Figure-emblem genealogy links: {genealogy_links_added}")
    print(f"  Total relational links added: {concept_links_added + emblem_links_added + genealogy_links_added}")

    print(f"\nNext steps:")
    print(f"  1. Run: python scripts/build_site.py")
    print(f"  2. Test portal: Check concept and figure pages for emblem links")
    print(f"  3. Verify: All 67 concepts should have 2-3 emblem links")
    print(f"  4. Verify: All 100 figures should show genealogical position if relevant")

if __name__ == '__main__':
    main()
