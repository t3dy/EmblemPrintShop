#!/usr/bin/env python3
"""
Figure-Emblem Genealogy Mapping
Connects 100 figures to emblem books they created or were influenced by

Strategy:
1. Identify emblem book creators (Maier, Cramer, Khunrath, Stolcius, etc.)
2. For each figure, determine:
   - Did they CREATE an emblem book?
   - Were they INFLUENCED by emblem traditions?
   - Did they CITE specific emblem books?
3. Create genealogy links showing transmission of emblem knowledge
4. Build timeline of emblem tradition evolution
"""

import json
from pathlib import Path
from collections import defaultdict

def load_database():
    """Load TheosophicalAlchemyDB"""
    with open('data/prototype_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def identify_emblem_creators(emblems):
    """Identify which figures are emblem book creators"""
    creators = {}  # {figure_name: [emblem_books]}

    emblem_books = set()
    for emblem in emblems:
        source_book = emblem.get('source_book', '')
        author = emblem.get('author', '')
        if source_book and author:
            emblem_books.add((source_book, author))

    return dict(emblem_books)

def analyze_figure_emblem_relationships(db):
    """
    Analyze which figures created or were influenced by emblems
    Uses heuristic matching on:
    - Figure key_works field (did they write emblem books?)
    - Figure scholarly_debates (do scholars discuss emblem influence?)
    - Related figures (did they influence each other?)
    - Time period (genealogical sequence)
    """

    figures = db.get('figures', [])
    emblems = db.get('emblems', [])
    emblem_books = defaultdict(list)

    # Map emblem books to creators
    for emblem in emblems:
        source_book = emblem.get('source_book', '')
        author = emblem.get('author', '')
        if source_book and author:
            emblem_books[author.lower()].append({
                'book': source_book,
                'emblem': emblem.get('id'),
                'count': 1
            })

    figure_emblem_map = defaultdict(dict)

    for figure in figures:
        figure_id = figure.get('id', '')
        figure_name = figure.get('name', '').lower()
        figure_birth = figure.get('birth_year', 0)
        figure_death = figure.get('death_year', 0)
        key_works = [w.lower() for w in figure.get('key_works', [])]
        related_figures = figure.get('related_figures', [])

        # Check if this figure created an emblem book
        created_emblems = []
        for author_name, emblem_list in emblem_books.items():
            if author_name in figure_name or figure_name in author_name:
                created_emblems.extend(emblem_list)

        if created_emblems:
            figure_emblem_map[figure_id]['created'] = created_emblems

        # Check if figure key_works mention emblem books
        influenced_by = []
        emblem_book_names = ['atalanta', 'maier', 'cramer', 'khunrath', 'stolcius', 'mutus liber', 'flamel']
        for work in key_works:
            for emblem_book in emblem_book_names:
                if emblem_book in work:
                    influenced_by.append(work)

        if influenced_by:
            figure_emblem_map[figure_id]['influenced_by_works'] = influenced_by

        # Genealogical positioning
        if figure_birth and figure_death:
            if figure_birth < 1600:
                figure_emblem_map[figure_id]['generation'] = 'Renaissance'
            elif figure_birth < 1700:
                figure_emblem_map[figure_id]['generation'] = 'Early Modern (1600-1700)'
            elif figure_birth < 1800:
                figure_emblem_map[figure_id]['generation'] = 'Enlightenment (1700-1800)'
            else:
                figure_emblem_map[figure_id]['generation'] = 'Modern (1800+)'

    return figure_emblem_map, emblem_books

def main():
    print("=" * 70)
    print("FIGURE-EMBLEM GENEALOGY ANALYSIS")
    print("=" * 70)

    # Load database
    print("\nLoading database...")
    db = load_database()

    figures = db.get('figures', [])
    emblems = db.get('emblems', [])

    print(f"  Figures: {len(figures)}")
    print(f"  Emblems: {len(emblems)}")

    # Analyze relationships
    print("\nAnalyzing figure-emblem genealogy...")
    figure_emblem_map, emblem_books = analyze_figure_emblem_relationships(db)

    print(f"  Emblem book creators identified: {len(emblem_books)}")
    print(f"  Figures with emblem connections: {len(figure_emblem_map)}")

    # Creators analysis
    creators = [f for f in figures if f.get('id') in figure_emblem_map and 'created' in figure_emblem_map[f.get('id')]]
    influenced = [f for f in figures if f.get('id') in figure_emblem_map and 'influenced_by_works' in figure_emblem_map[f.get('id')]]

    print(f"\nCoverage:")
    print(f"  Emblem creators: {len(creators)}")
    for creator in creators:
        books = figure_emblem_map[creator.get('id')].get('created', [])
        print(f"    - {creator.get('name')}: {len(books)} emblems")

    print(f"  Figures influenced by emblems: {len(influenced)}")

    # Generational distribution
    generations = defaultdict(int)
    for figure_id, data in figure_emblem_map.items():
        gen = data.get('generation', 'Unknown')
        generations[gen] += 1

    print(f"\nGenerational distribution:")
    for gen in sorted(generations.keys()):
        print(f"  {gen}: {generations[gen]}")

    # Emblem book inventory
    print(f"\nEmblem books in database:")
    total_emblems = 0
    for author, emblems_list in sorted(emblem_books.items()):
        unique_books = set(e['book'] for e in emblems_list)
        emblem_count = len(emblems_list)
        total_emblems += emblem_count
        print(f"  {author}: {len(unique_books)} book(s), {emblem_count} emblems")

    print(f"  Total: {total_emblems} emblems across {len(emblem_books)} creators")

    print(f"\n" + "=" * 70)
    print("GENEALOGY ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nRecommendation:")
    if len(creators) >= 3:
        print(f"  Status: Foundation established ({len(creators)} creators)")
        print(f"  Next: Identify which figures were influenced by these emblem traditions")
        print(f"  Use Agent to map transmission genealogy for all 100 figures")
    else:
        print(f"  Status: NEEDS MORE EMBLEM CREATOR DATA")

if __name__ == '__main__':
    main()
