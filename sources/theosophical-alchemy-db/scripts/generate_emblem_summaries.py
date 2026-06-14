#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate proper 2-4 sentence summaries for all 135 emblem cards from existing essay/metadata.
Targets 50-80 words per summary.
"""

import json
import re
from pathlib import Path

DB_PATH = Path("data/prototype_data.json")

def generate_emblem_summary(emblem):
    """Generate a 2-4 sentence summary from emblem data."""

    # If summary already looks reasonable (50+ words), keep it
    current_words = len((emblem.get('summary') or '').split())
    if current_words >= 50:
        return None

    parts = []

    # Try to build from visual elements
    if emblem.get('visual_elements'):
        visual = ', '.join(emblem['visual_elements'][:3])
        parts.append(f"Visual elements include {visual}.")

    # Add alchemical significance from concepts
    if emblem.get('concepts'):
        concept_names = []
        # These are IDs, we'd need concept lookup, so skip for now
        pass

    # Extract from essay if it looks real (not a placeholder)
    essay = emblem.get('essay', '')
    if essay and not essay.startswith('[') and len(essay.split()) > 30:
        # Extract first 2-3 sentences
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', essay)
        for sent in sentences[:3]:
            if sent.strip():
                parts.append(sent.strip())

    # Fallback: generic based on source book
    if not parts:
        source = emblem.get('source_book', 'Alchemical Emblem')
        title = emblem.get('title', 'Unknown')
        parts.append(f"{title} from {source}.")

    summary = ' '.join(parts[:3])  # Max 3 sentences

    # Trim to 80 words
    words = summary.split()
    if len(words) > 80:
        summary = ' '.join(words[:80]) + '...'

    return summary

def enrich_emblems():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        db = json.load(f)

    emblems_expanded = 0
    for emblem in db['emblems']:
        new_summary = generate_emblem_summary(emblem)
        if new_summary:
            emblem['summary'] = new_summary
            emblems_expanded += 1

    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"Generated {emblems_expanded} emblem summaries")

    # Show results
    emblems = db['emblems']
    summaries = [len((e.get('summary') or '').split()) for e in emblems if e.get('summary')]
    if summaries:
        print(f"Emblem summary stats:")
        print(f"  Avg words: {sum(summaries)//len(summaries)}")
        print(f"  Min: {min(summaries)}, Max: {max(summaries)}")


if __name__ == "__main__":
    enrich_emblems()
