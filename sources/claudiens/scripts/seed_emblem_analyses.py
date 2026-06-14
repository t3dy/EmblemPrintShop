"""
seed_emblem_analyses.py — Assemble structured analysis HTML for each emblem
from existing database content (motto, discourse, scholarly refs, sources, terms).

Template synthesizes:
- What the emblem depicts (motto + image description)
- Maier's discourse summary (what he says about the emblem)
- De Jong's source identifications (which texts Maier draws from)
- Alchemical significance (scholarly commentary)
- Related alchemical concepts (dictionary term links)

Deterministic: no LLM calls. Assembles template from DB fields.
Idempotent: overwrites analysis_html on each run.
"""

import re
import sqlite3
import html
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "atalanta.db"

AI_BANNER = (
    '<div class="ai-banner">Assembled from De Jong (1969) corpus extraction '
    'and scholarly references. Not reviewed by a human scholar.</div>'
)


def esc(text):
    if not text:
        return ''
    return html.escape(str(text))


def clean_ocr_for_display(text):
    """Light cleanup of OCR text for readable display."""
    if not text:
        return ''
    # Fix run-together words at common boundaries
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    text = re.sub(r',([A-Za-z])', r', \1', text)
    text = re.sub(r'  +', ' ', text)
    # Remove page markers and running headers
    text = re.sub(r'## Page \d+', '', text)
    text = re.sub(r'\d+\s*EMBLEM\s*[IVXLCDM]+', '', text)
    text = re.sub(r'EMBLEM\s*[IVXLCDM]+\s*\d+', '', text)
    return text.strip()


def build_analysis(conn, emblem_id, num, roman, motto, discourse, stage):
    """Build analysis HTML for one emblem."""
    sections = []

    # --- 1. Overview: What This Emblem Presents ---
    overview_parts = []
    if motto:
        clean_motto = clean_ocr_for_display(motto)
        overview_parts.append(
            f'Emblem {roman or "F"} bears the motto: <em>"{esc(clean_motto[:200])}"</em>'
        )
    if stage:
        stage_names = {
            'NIGREDO': 'nigredo (blackening/putrefaction)',
            'ALBEDO': 'albedo (whitening/purification)',
            'CITRINITAS': 'citrinitas (yellowing/vivification)',
            'RUBEDO': 'rubedo (reddening/completion)',
        }
        stage_desc = stage_names.get(stage, stage)
        overview_parts.append(
            f'This emblem belongs to the <em>{stage_desc}</em> phase of the alchemical Work.'
        )
    if overview_parts:
        sections.append(
            '<h3>Overview</h3>\n<p>' + ' '.join(overview_parts) + '</p>'
        )

    # --- 2. Maier's Discourse: What the Author Says ---
    if discourse and len(discourse) > 50:
        clean_disc = clean_ocr_for_display(discourse)
        # Take a meaningful excerpt — first 600 chars, ending at a sentence boundary
        excerpt = clean_disc[:600]
        last_period = excerpt.rfind('.')
        if last_period > 200:
            excerpt = excerpt[:last_period + 1]
        sections.append(
            f'<h3>Maier\'s Discourse</h3>\n'
            f'<p>{esc(excerpt)}</p>'
        )

    # --- 3. Source Texts: De Jong's Identifications ---
    sources = conn.execute("""
        SELECT sa.name, sa.authority_id, sa.type, es.relationship_type
        FROM emblem_sources es
        JOIN source_authorities sa ON es.authority_id = sa.id
        WHERE es.emblem_id = ?
        ORDER BY es.relationship_type, sa.name
    """, (emblem_id,)).fetchall()

    if sources:
        motto_sources = [s for s in sources if s[3] == 'MOTTO_SOURCE']
        disc_sources = [s for s in sources if s[3] != 'MOTTO_SOURCE']

        parts = []
        if motto_sources:
            names = ', '.join(
                f'<a href="../sources.html#{s[1]}" class="cross-link">{esc(s[0])}</a>'
                for s in motto_sources
            )
            parts.append(f'De Jong identifies the motto source as {names}.')

        if disc_sources:
            # Group by type for clearer presentation
            by_type = {}
            for s in disc_sources:
                by_type.setdefault(s[2], []).append(s)

            for stype, slist in by_type.items():
                names = ', '.join(
                    f'<a href="../sources.html#{s[1]}" class="cross-link">{esc(s[0])}</a>'
                    for s in slist
                )
                type_label = {
                    'ALCHEMICAL': 'alchemical',
                    'CLASSICAL': 'classical',
                    'BIBLICAL': 'biblical',
                    'HERMETIC': 'Hermetic',
                    'PATRISTIC': 'patristic',
                    'MOVEMENT': 'movement',
                }.get(stype, '')
                if type_label:
                    parts.append(f'The discourse draws on {type_label} sources: {names}.')
                else:
                    parts.append(f'The discourse also references {names}.')

        sections.append(
            f'<h3>Source Texts</h3>\n'
            f'<p>De Jong\'s source-critical analysis identifies the textual traditions '
            f'Maier draws upon for this emblem.</p>\n'
            f'<p>{" ".join(parts)}</p>'
        )

    # --- 4. Scholarly Commentary ---
    refs = conn.execute("""
        SELECT sr.summary, b.author, sr.confidence, sr.interpretation_type
        FROM scholarly_refs sr
        JOIN bibliography b ON sr.bib_id = b.id
        WHERE sr.emblem_id = ?
        ORDER BY b.af_relevance, sr.confidence
    """, (emblem_id,)).fetchall()

    if refs:
        ref_parts = []
        for summary, author, conf, interp_type in refs:
            if not summary:
                continue
            clean_summary = clean_ocr_for_display(summary)
            # Take first 400 chars at a sentence boundary
            excerpt = clean_summary[:400]
            last_period = excerpt.rfind('.')
            if last_period > 100:
                excerpt = excerpt[:last_period + 1]
            ref_parts.append(
                f'<strong>{esc(author)}</strong>: {esc(excerpt)}'
            )

        if ref_parts:
            sections.append(
                '<h3>Alchemical Significance</h3>\n'
                '<p>' + '</p>\n<p>'.join(ref_parts) + '</p>'
            )

    # --- 5. Alchemical Concepts ---
    terms = conn.execute("""
        SELECT dt.slug, dt.label, dt.label_latin, dt.category
        FROM term_emblem_refs ter
        JOIN dictionary_terms dt ON ter.term_id = dt.id
        WHERE ter.emblem_id = ?
        ORDER BY dt.category, dt.label
    """, (emblem_id,)).fetchall()

    if terms:
        # Group by category
        by_cat = {}
        for slug, label, latin, cat in terms:
            by_cat.setdefault(cat, []).append((slug, label, latin))

        term_html_parts = []
        for cat in ['PROCESS', 'SUBSTANCE', 'FIGURE', 'CONCEPT', 'SOURCE_TEXT', 'MUSICAL']:
            if cat not in by_cat:
                continue
            links = ', '.join(
                f'<a href="../dictionary/{slug}.html" class="cross-link">{esc(label)}'
                f'{" (" + esc(latin) + ")" if latin and latin != label else ""}</a>'
                for slug, label, latin in by_cat[cat]
            )
            term_html_parts.append(f'<strong>{cat.title()}</strong>: {links}')

        sections.append(
            '<h3>Key Alchemical Concepts</h3>\n'
            '<p>' + '<br>'.join(term_html_parts) + '</p>'
        )

    if not sections:
        return None

    return (
        '<div class="emblem-analysis">\n'
        f'{AI_BANNER}\n'
        + '\n'.join(f'<section>\n{s}\n</section>' for s in sections)
        + '\n</div>'
    )


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    emblems = conn.execute("""
        SELECT id, number, roman_numeral, motto_english,
               discourse_summary, alchemical_stage
        FROM emblems WHERE number > 0
        ORDER BY number
    """).fetchall()

    updated = 0
    for eid, num, roman, motto, discourse, stage in emblems:
        analysis = build_analysis(conn, eid, num, roman, motto, discourse, stage)
        if analysis:
            conn.execute(
                "UPDATE emblems SET analysis_html = ? WHERE id = ?",
                (analysis, eid)
            )
            updated += 1

    conn.commit()

    with_analysis = conn.execute(
        "SELECT COUNT(*) FROM emblems WHERE analysis_html IS NOT NULL"
    ).fetchone()[0]
    avg_len = conn.execute(
        "SELECT AVG(LENGTH(analysis_html)) FROM emblems WHERE analysis_html IS NOT NULL AND number > 0"
    ).fetchone()[0]
    conn.close()

    print(f"  Emblem analyses: {with_analysis}/50 generated ({updated} updated, avg {int(avg_len)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
