"""
build_site.py — Generate static HTML site from SQLite database.

Stage 4: Reads db/atalanta.db, generates:
  - site/index.html (gallery home)
  - site/data.json (gallery data for JS)
  - site/emblems/emblem-NN.html (51 emblem detail pages)
  - site/about.html
"""

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "atalanta.db"
SITE_DIR = BASE_DIR / "site"


def load_identity_map(conn):
    """Load emblem_identity table into a dict keyed by emblem_number.

    Returns {emblem_number: {'image_filename': str|None, 'alignment_confidence': str|None, ...}}
    All image rendering must flow through this map — no hardcoded filename assumptions.
    """
    rows = conn.execute("""
        SELECT emblem_number, roman_label, image_filename,
               image_source, alignment_confidence
        FROM emblem_identity
        ORDER BY emblem_number
    """).fetchall()
    identity = {}
    for r in rows:
        identity[r[0]] = {
            'image_filename': r[2],
            'image_source': r[3],
            'alignment_confidence': r[4],
        }
    return identity


def resolve_image(identity_map, emblem_number):
    """Resolve image path for an emblem via the identity layer.

    Returns (relative_path, exists) tuple. Returns (None, False) if no image mapped.
    """
    entry = identity_map.get(emblem_number)
    if not entry or not entry['image_filename']:
        return None, False
    rel_path = f"images/emblems/{entry['image_filename']}"
    exists = (SITE_DIR / rel_path).exists()
    return rel_path, exists

ROMAN_MAP = [
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
    (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
    (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
]

def int_to_roman(n):
    if n <= 0: return None
    result = []
    for value, numeral in ROMAN_MAP:
        while n >= value:
            result.append(numeral)
            n -= value
    return ''.join(result)

def slugify(text):
    return text.lower().replace(' ', '-').replace('/', '-')


# ============================================================
# Page Shell
# ============================================================

NAV_ITEMS = [
    ('Home', 'index.html'),
    ('Emblems', 'emblems/index.html'),
    ('Stages', 'stage/index.html'),
    ('Galleries', 'galleries/index.html'),
    ('Visual', 'visual.html'),
    ('Scholars', 'scholars.html'),
    ('Dictionary', 'dictionary/index.html'),
    ('Timeline', 'timeline.html'),
    ('Sources', 'sources.html'),
    ('Maier', 'maier.html'),
    ('Creatures', 'creatures.html'),
    ('Music', 'music.html'),
    ('Works', 'works.html'),
    ('21st Century', 'modern-scholarship.html'),
    ('Szulakowska', 'szulakowska.html'),
    ('Essays', 'essays/index.html'),
    ('Bibliography', 'bibliography.html'),
    ('Biography', 'biography.html'),
    ('Search', 'search.html'),
    ('About', 'about.html'),
]

def nav_html(active='', prefix=''):
    links = []
    for label, href in NAV_ITEMS:
        cls = ' class="active"' if label == active else ''
        links.append(f'<a href="{prefix}{href}"{cls}>{label}</a>')
    return '\n            '.join(links)

def page_shell(title, body, active_nav='', depth=0):
    prefix = '../' * depth
    css_path = f'{prefix}style.css'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Atalanta Fugiens</title>
    <link rel="stylesheet" href="{css_path}">
</head>
<body>
    <header>
        <div class="header-content">
            <h1><em>Atalanta Fugiens</em></h1>
            <div class="subtitle">The Scholarship of H.M.E. De Jong on Michael Maier's Alchemical Emblems</div>
            <nav class="site-nav">
                {nav_html(active_nav, prefix)}
            </nav>
        </div>
    </header>
    {body}
    <footer>
        <p>AtalantaClaudiens &middot; A digital humanities project &middot;
        <a href="https://github.com/t3dy/AtalantaClaudiens">GitHub</a></p>
    </footer>
</body>
</html>"""


def autolink_emblems(text, depth=1):
    """Convert 'Emblem XXIV', 'Emblem 24' references into clickable links.
    depth=0 for root pages, depth=1 for subdirectory pages."""
    if not text:
        return text
    import re
    prefix = '../' if depth > 0 else ''
    roman_map = {'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10,
                 'XI':11,'XII':12,'XIII':13,'XIV':14,'XV':15,'XVI':16,'XVII':17,'XVIII':18,
                 'XIX':19,'XX':20,'XXI':21,'XXII':22,'XXIII':23,'XXIV':24,'XXV':25,'XXVI':26,
                 'XXVII':27,'XXVIII':28,'XXIX':29,'XXX':30,'XXXI':31,'XXXII':32,'XXXIII':33,
                 'XXXIV':34,'XXXV':35,'XXXVI':36,'XXXVII':37,'XXXVIII':38,'XXXIX':39,'XL':40,
                 'XLI':41,'XLII':42,'XLIII':43,'XLIV':44,'XLV':45,'XLVI':46,'XLVII':47,
                 'XLVIII':48,'XLIX':49,'L':50}
    def replace_roman(m):
        roman = m.group(1)
        num = roman_map.get(roman)
        if num is not None:
            return f'<a href="{prefix}emblems/emblem-{num:02d}.html" class="cross-link">Emblem {roman}</a>'
        return m.group(0)
    def replace_arabic(m):
        num = int(m.group(1))
        if 0 <= num <= 50:
            href = f'emblem-{num:02d}.html' if num > 0 else 'frontispiece.html'
            return f'<a href="{prefix}emblems/{href}" class="cross-link">Emblem {num}</a>'
        return m.group(0)
    # Match "Emblem XXIV" (roman), longest match first
    text = re.sub(r'Emblem\s+(XLVIII|XXXVIII|XXXIII|XXVIII|XXIII|XVIII|XLVII|XXXVII|XXXIV|XXXII|XXVII|XXXIX|XXXVI|XXXV|XXVI|XXIV|XXII|XVII|XLVI|XLIV|XLIII|XLII|XIII|XXXI|XXIX|XVI|XLV|XLI|XII|XXX|XIV|XXV|XIX|XV|XXI|XX|XI|IX|XL|IV|VI|II|VIII|VII|III|XLIX|I|V|X|L)',
                  replace_roman, text)
    # Match "Emblem 24" (arabic)
    text = re.sub(r'Emblem\s+(\d{1,2})(?=[^0-9]|$)', replace_arabic, text)
    return text


def format_paragraphs(text):
    """Convert \\n\\n-separated text into HTML paragraphs."""
    if not text:
        return ''
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    html = ''.join(f'<p style="font-size:0.95rem;line-height:1.7;margin-bottom:1rem">{p}</p>' for p in paragraphs)
    return f'<div style="margin-bottom:1.5rem">{html}</div>'


def confidence_badge(level):
    if not level: return ''
    cls = f'confidence-{level.lower()}'
    return f'<span class="badge {cls}">{level}</span>'


def build_registers_html(registers_json):
    """Build HTML for multi-register definitions (alchemical, medical, spiritual, cosmological)."""
    if not registers_json:
        return ''
    import json
    try:
        regs = json.loads(registers_json)
    except (json.JSONDecodeError, TypeError):
        return ''
    if not any(regs.get(k) for k in ('alchemical', 'medical', 'spiritual', 'cosmological')):
        return ''

    reg_labels = {
        'alchemical': ('Alchemical', '#8b4513'),
        'medical': ('Medical', '#2980b9'),
        'spiritual': ('Spiritual', '#6c3483'),
        'cosmological': ('Cosmological', '#1a5276'),
    }
    items = ''
    for key, (display, color) in reg_labels.items():
        val = regs.get(key)
        if val:
            items += f'''
                <div style="margin-bottom:0.8rem;padding-left:1rem;border-left:3px solid {color}">
                    <dt style="font-weight:600;font-size:0.85rem;color:{color};font-family:var(--font-sans);margin-bottom:0.2rem">{display}</dt>
                    <dd style="margin:0;font-size:0.92rem;line-height:1.6">{val}</dd>
                </div>'''
    return f'''
            <div style="margin-bottom:1.5rem">
                <h2>Meanings Across Registers</h2>
                <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:1rem">
                    De Jong shows that alchemical terms operate simultaneously across material, medical, spiritual, and cosmological dimensions.
                </p>
                <dl style="margin:0">{items}</dl>
            </div>'''


# ============================================================
# Data Export
# ============================================================

def export_data_json(conn, identity_map):
    rows = conn.execute("""
        SELECT e.id, e.number, e.roman_numeral, e.canonical_label,
               e.motto_english, e.discourse_summary, e.confidence,
               e.alchemical_stage
        FROM emblems e ORDER BY e.number
    """).fetchall()

    # Build source-authority map: emblem_id -> [authority_id, ...]
    source_rows = conn.execute("""
        SELECT es.emblem_id, sa.authority_id
        FROM emblem_sources es
        JOIN source_authorities sa ON es.authority_id = sa.id
        ORDER BY es.emblem_id, sa.authority_id
    """).fetchall()
    sources_by_emblem = {}
    for eid, code in source_rows:
        sources_by_emblem.setdefault(eid, []).append(code)

    entries = []
    for r in rows:
        eid, num = r[0], r[1]
        page = 'frontispiece.html' if num == 0 else f'emblem-{num:02d}.html'
        img_path, img_exists = resolve_image(identity_map, num)
        entries.append({
            'number': num,
            'roman': r[2],
            'label': r[3],
            'motto': r[4],
            'discourse': r[5],
            'confidence': r[6],
            'stage': r[7],
            'sources': sources_by_emblem.get(eid, []),
            'page': page,
            'image': img_path if img_exists else None,
        })

    stats = {
        'total_emblems': len([e for e in entries if e['number'] > 0]),
        'with_motto': len([e for e in entries if e['motto']]),
        'scholarly_refs': conn.execute("SELECT COUNT(*) FROM scholarly_refs").fetchone()[0],
        'source_links': conn.execute("SELECT COUNT(*) FROM emblem_sources").fetchone()[0],
    }

    data = {'entries': entries, 'stats': stats}
    out = SITE_DIR / 'data.json'
    out.write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(f"  data.json: {len(entries)} entries")


# ============================================================
# Gallery Home
# ============================================================

def build_gallery(conn):
    stats = conn.execute("SELECT COUNT(*) FROM emblems WHERE number > 0").fetchone()[0]
    terms = conn.execute("SELECT COUNT(*) FROM dictionary_terms").fetchone()[0]
    sources = conn.execute("SELECT COUNT(*) FROM source_authorities").fetchone()[0]

    # Top source authorities for filter chips
    top_sources = conn.execute("""
        SELECT sa.authority_id, sa.name, COUNT(es.id) AS n
        FROM source_authorities sa
        JOIN emblem_sources es ON es.authority_id = sa.id
        GROUP BY sa.id
        ORDER BY n DESC LIMIT 6
    """).fetchall()
    source_chips = ''.join(
        f'<button class="filter-chip" data-filter-type="source" data-filter-value="{aid}" type="button">{name} <span class="filter-chip-count">{n}</span></button>'
        for aid, name, n in top_sources
    )

    body = f"""
    <div style="max-width:700px;margin:2rem auto;padding:0 2rem;text-align:center">
        <p style="font-size:1.05rem;line-height:1.8;color:var(--text)">In 1617, the physician and alchemist Michael Maier published fifty emblems combining engraved plates, Latin mottos, poetic epigrams, philosophical discourses, and three-voice musical fugues &mdash; a work without parallel in the history of the emblem book. In 1969, the Dutch art historian H.M.E. De Jong unlocked these emblems by tracing each one to its ancient and medieval sources. This site presents her findings.</p>
        <div style="margin-top:1.5rem;display:flex;gap:0.6rem;justify-content:center;flex-wrap:wrap">
            <a href="emblems/frontispiece.html" style="display:inline-block;padding:0.6rem 1.5rem;background:var(--accent);color:white;text-decoration:none;border-radius:4px;font-family:var(--font-sans);font-size:0.9rem">Start with the Frontispiece &rarr;</a>
            <a href="visual.html" style="display:inline-block;padding:0.6rem 1.5rem;background:#16a085;color:white;text-decoration:none;border-radius:4px;font-family:var(--font-sans);font-size:0.9rem">Browse by visual element &rarr;</a>
            <button type="button" id="random-emblem" style="display:inline-block;padding:0.6rem 1.5rem;background:#7f8c8d;color:white;border:none;border-radius:4px;font-family:var(--font-sans);font-size:0.9rem;cursor:pointer">Surprise me &darr;</button>
        </div>
    </div>
    <div class="stats" id="stats"></div>
    <div class="filter-bar" id="filter-bar">
        <input type="search" id="gallery-search" class="filter-search" placeholder="Search emblems by motto, label, or text&hellip;" autocomplete="off">
        <div class="filter-row">
            <span class="filter-label">Stage:</span>
            <button class="filter-chip filter-chip-all active" data-filter-type="stage" data-filter-value="" type="button">All</button>
            <button class="filter-chip filter-chip-stage" data-filter-type="stage" data-filter-value="NIGREDO" type="button" style="background:#2c2418;color:#f5f0e8">Nigredo</button>
            <button class="filter-chip filter-chip-stage" data-filter-type="stage" data-filter-value="ALBEDO" type="button" style="background:#a89880;color:#2c2418">Albedo</button>
            <button class="filter-chip filter-chip-stage" data-filter-type="stage" data-filter-value="CITRINITAS" type="button" style="background:#b8860b;color:#2c2418">Citrinitas</button>
            <button class="filter-chip filter-chip-stage" data-filter-type="stage" data-filter-value="RUBEDO" type="button" style="background:#c0392b;color:#f5f0e8">Rubedo</button>
        </div>
        <div class="filter-row">
            <span class="filter-label">Source:</span>
            {source_chips}
        </div>
        <div class="filter-status" id="filter-status"></div>
    </div>
    <div class="gallery" id="gallery"></div>
    <div class="lightbox" id="lightbox">
        <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
        <button class="lightbox-nav lightbox-prev" onclick="navigateLightbox(-1)">&lsaquo;</button>
        <button class="lightbox-nav lightbox-next" onclick="navigateLightbox(1)">&rsaquo;</button>
        <div class="lightbox-content">
            <div class="lightbox-details"></div>
        </div>
    </div>
    <script src="script.js"></script>"""

    html = page_shell("Emblem Gallery", body, active_nav='Home')
    (SITE_DIR / 'index.html').write_text(html, encoding='utf-8')
    print(f"  index.html")


# ============================================================
# Emblem Detail Pages
# ============================================================

def build_emblem_pages(conn, identity_map):
    emblems_dir = SITE_DIR / 'emblems'
    emblems_dir.mkdir(exist_ok=True)

    emblems = conn.execute("""
        SELECT id, number, roman_numeral, canonical_label,
               motto_latin, motto_english, epigram_english,
               discourse_summary, image_description,
               alchemical_stage, confidence, analysis_html
        FROM emblems ORDER BY number
    """).fetchall()

    for i, e in enumerate(emblems):
        eid, num, roman, label = e[0], e[1], e[2], e[3]
        motto_lat, motto_en, epigram = e[4], e[5], e[6]
        discourse, img_desc, stage, conf = e[7], e[8], e[9], e[10]
        analysis_html = e[11]

        # Navigation
        prev_link = ''
        next_link = ''
        if i > 0:
            prev_num = emblems[i-1][1]
            prev_file = 'frontispiece.html' if prev_num == 0 else f'emblem-{prev_num:02d}.html'
            prev_link = f'<a href="{prev_file}">&larr; Previous</a>'
        if i < len(emblems) - 1:
            next_num = emblems[i+1][1]
            next_file = 'frontispiece.html' if next_num == 0 else f'emblem-{next_num:02d}.html'
            next_link = f'<a href="{next_file}">Next &rarr;</a>'

        title = f'Emblem {roman}' if roman else 'Frontispiece'
        display_num = roman or 'F'

        # Scholarly refs
        refs = conn.execute("""
            SELECT sr.summary, sr.confidence, sr.interpretation_type,
                   sr.source_texts_referenced, sr.section_page,
                   b.author, b.title, b.source_id
            FROM scholarly_refs sr
            JOIN bibliography b ON sr.bib_id = b.id
            WHERE sr.emblem_id = ?
            ORDER BY b.af_relevance, sr.confidence
        """, (eid,)).fetchall()

        refs_html = ''
        for ref in refs:
            summary, rconf, interp_type = ref[0], ref[1], ref[2]
            auth_json, page, author, btitle, src_id = ref[3], ref[4], ref[5], ref[6], ref[7]
            type_badge = f'<span class="badge badge-stage">{interp_type}</span>' if interp_type else ''
            conf_badge = confidence_badge(rconf)
            # Truncate long summaries
            if summary and len(summary) > 800:
                summary = summary[:800] + '...'
            refs_html += f"""
            <div class="ref-card">
                <h4>{author} {type_badge} {conf_badge}</h4>
                <p>{summary or 'No summary available.'}</p>
                {f'<p style="font-size:0.8rem;color:var(--text-muted);margin-top:0.5rem">Citation: {page}</p>' if page else ''}
            </div>"""

        # Source authorities
        sources = conn.execute("""
            SELECT sa.name, sa.type, es.relationship_type, es.confidence
            FROM emblem_sources es
            JOIN source_authorities sa ON es.authority_id = sa.id
            WHERE es.emblem_id = ?
            ORDER BY es.relationship_type
        """, (eid,)).fetchall()

        sources_html = ''
        for s in sources:
            sname, stype, rel, sconf = s
            sources_html += f'<span class="source-link">{sname} ({rel})</span>\n'

        # Build page
        # Stage badge styling
        stage_colors = {'NIGREDO': '#2c2418', 'ALBEDO': '#a89880', 'CITRINITAS': '#b8860b', 'RUBEDO': '#c0392b'}
        stage_text = {'NIGREDO': '#f5f0e8', 'ALBEDO': '#2c2418', 'CITRINITAS': '#2c2418', 'RUBEDO': '#f5f0e8'}
        stage_badge_html = ''
        if stage:
            bg = stage_colors.get(stage, '#7f8c8d')
            fg = stage_text.get(stage, '#fff')
            stage_badge_html = f'<a href="../index.html#stage={stage}" class="badge" title="See all {stage} emblems" style="background:{bg};color:{fg};font-size:0.85rem;padding:0.3rem 0.8rem;border-radius:3px;text-decoration:none">{stage}</a>'

        # Bilingual motto block
        motto_html = ''
        if motto_lat or motto_en:
            motto_html = '<div class="motto-block">'
            if motto_lat:
                motto_html += f'<p style="font-style:italic;color:var(--accent);margin-bottom:0.3rem;font-size:1.05rem">{motto_lat}</p>'
            if motto_en:
                motto_html += f'<p style="margin-top:0">{motto_en}</p>'
            motto_html += '</div>'
        else:
            motto_html = '<p style="color:var(--text-muted)"><em>Motto not yet extracted</em></p>'

        # Epigram (shown by default, not collapsed)
        epigram_html = ''
        if epigram:
            epigram_html = f'<div class="epigram-block" style="margin-bottom:1.5rem;padding:0.8rem 1rem;background:var(--bg);border-left:3px solid var(--accent-light);font-size:0.92rem"><h3 style="font-size:0.9rem;color:var(--accent);margin-bottom:0.4rem;font-family:var(--font-sans)">Epigram</h3>{epigram}</div>'

        # "What You See" visual description
        visual_html = ''
        if img_desc:
            visual_html = f'<div class="visual-description" style="margin-bottom:1.5rem;padding:0.8rem 1rem;background:#faf8f4;border-radius:4px"><h3 style="font-size:0.9rem;color:var(--accent);margin-bottom:0.4rem;font-family:var(--font-sans)">What You See</h3><p style="font-size:0.92rem;margin:0">{img_desc}</p></div>'

        # Related emblems: same stage, shared sources, shared dictionary terms
        related_sections = []
        if stage:
            stage_peers = conn.execute(
                """SELECT number, roman_numeral, canonical_label
                   FROM emblems
                   WHERE alchemical_stage = ? AND id != ? AND number > 0
                   ORDER BY number""",
                (stage, eid),
            ).fetchall()
            if stage_peers:
                cards = ''.join(
                    f'<a href="emblem-{p[0]:02d}.html" class="related-emblem-card"><strong>{p[1]}</strong>: {p[2]}</a>'
                    for p in stage_peers
                )
                related_sections.append(
                    f'<div class="related-section"><div class="related-section-label">Same alchemical stage ({stage})</div><div class="related-grid">{cards}</div></div>'
                )

        source_peers = conn.execute(
            """SELECT DISTINCT e2.number, e2.roman_numeral, e2.canonical_label
               FROM emblem_sources es1
               JOIN emblem_sources es2 ON es1.authority_id = es2.authority_id AND es2.emblem_id != es1.emblem_id
               JOIN emblems e2 ON es2.emblem_id = e2.id
               WHERE es1.emblem_id = ? AND e2.number > 0
               ORDER BY e2.number""",
            (eid,),
        ).fetchall()
        if source_peers:
            cards = ''.join(
                f'<a href="emblem-{p[0]:02d}.html" class="related-emblem-card"><strong>{p[1]}</strong>: {p[2]}</a>'
                for p in source_peers[:12]
            )
            extra = f' <span style="font-size:0.78rem;color:var(--text-muted)">+{len(source_peers)-12} more</span>' if len(source_peers) > 12 else ''
            related_sections.append(
                f'<div class="related-section"><div class="related-section-label">Shares a source authority</div><div class="related-grid">{cards}</div>{extra}</div>'
            )

        term_peers = conn.execute(
            """SELECT DISTINCT e2.number, e2.roman_numeral, e2.canonical_label
               FROM term_emblem_refs ter1
               JOIN term_emblem_refs ter2 ON ter1.term_id = ter2.term_id AND ter2.emblem_id != ter1.emblem_id
               JOIN emblems e2 ON ter2.emblem_id = e2.id
               WHERE ter1.emblem_id = ? AND e2.number > 0
               ORDER BY e2.number""",
            (eid,),
        ).fetchall()
        if term_peers:
            cards = ''.join(
                f'<a href="emblem-{p[0]:02d}.html" class="related-emblem-card"><strong>{p[1]}</strong>: {p[2]}</a>'
                for p in term_peers[:12]
            )
            extra = f' <span style="font-size:0.78rem;color:var(--text-muted)">+{len(term_peers)-12} more</span>' if len(term_peers) > 12 else ''
            related_sections.append(
                f'<div class="related-section"><div class="related-section-label">Shares a dictionary term</div><div class="related-grid">{cards}</div>{extra}</div>'
            )

        related_html = ''
        if related_sections:
            related_html = f'<div class="related-emblems"><h3>Related Emblems</h3>{"".join(related_sections)}</div>'

        body = f"""
    <div class="emblem-detail">
        <div class="emblem-nav">
            <span>{prev_link}</span>
            <a href="../">Gallery</a>
            <span>{next_link}</span>
        </div>

        <h1 style="font-size:1.8rem;margin-bottom:0.5rem">{title} — {label} {stage_badge_html}</h1>

        <div class="comparative-view">
            <div class="source-panel">
                <h2>Original Source</h2>
                {(lambda p, e: f'<img src="../{p}" alt="Emblem {display_num}" class="emblem-plate">' if e else f'<div class="placeholder-img">{display_num}</div>')(*resolve_image(identity_map, num))}
                {visual_html}
                {motto_html}
                {epigram_html}
                {f'<div class="discourse-block"><h3 style="font-size:1rem;color:var(--accent);margin-bottom:0.5rem">Discourse Summary</h3><p style="font-size:0.92rem">{discourse[:1500]}{"..." if discourse and len(discourse) > 1500 else ""}</p></div>' if discourse else ''}
                {autolink_emblems(analysis_html) if analysis_html else ''}
            </div>

            <div class="scholarship-panel">
                <h2>Scholarly Commentary</h2>
                {refs_html if refs_html else '<p style="color:var(--text-muted)"><em>No scholarly references extracted yet.</em></p>'}

                {f'<h3 style="font-size:1rem;color:var(--accent);margin-top:1.5rem;margin-bottom:0.5rem">Maier\'s Sources</h3>{sources_html}' if sources_html else ''}

                <div id="emblem-timeline-panel" data-emblem-num="{num}"></div>
            </div>
        </div>
        {related_html}
    </div>
    <script>
    (async function() {{
        const panel = document.getElementById('emblem-timeline-panel');
        if (!panel) return;
        const n = panel.dataset.emblemNum;
        try {{
            const resp = await fetch('../timeline-by-emblem.json');
            if (!resp.ok) return;
            const data = await resp.json();
            const events = data[n];
            if (!events || !events.length) return;
            const items = events.map(ev => {{
                const yr = ev.year_end && ev.year_end !== ev.year ? ev.year + '-' + ev.year_end : ev.year;
                return '<li style="margin-bottom:0.5rem;font-size:0.88rem"><strong>' + yr + '</strong> · <span class="badge badge-contextual" style="font-size:0.65rem">' + (ev.type || '') + '</span> ' + ev.title + '</li>';
            }}).join('');
            panel.innerHTML =
                '<h3 style="font-size:1rem;color:var(--accent);margin-top:1.5rem;margin-bottom:0.5rem">Timeline references <span class="badge badge-contextual">' + events.length + '</span></h3>' +
                '<ul style="padding-left:1.2rem;margin:0">' + items + '</ul>' +
                '<p style="font-size:0.78rem;font-family:var(--font-sans);margin-top:0.4rem"><a href="../timeline.html#q=Emblem%20{roman or num}" style="color:var(--accent)">Show in full timeline →</a></p>';
        }} catch (err) {{ /* silent */ }}
    }})();
    </script>"""

        filename = 'frontispiece.html' if num == 0 else f'emblem-{num:02d}.html'
        html = page_shell(f'{title} — {label}', body, active_nav='Emblems', depth=1)
        (emblems_dir / filename).write_text(html, encoding='utf-8')

    # Emblem index page
    stage_colors = {'NIGREDO': '#2c2418', 'ALBEDO': '#a89880', 'CITRINITAS': '#b8860b', 'RUBEDO': '#c0392b'}
    stage_fg = {'NIGREDO': '#f5f0e8', 'ALBEDO': '#2c2418', 'CITRINITAS': '#2c2418', 'RUBEDO': '#f5f0e8'}

    grid_html = ''
    for e in emblems:
        num, roman, label = e[1], e[2], e[3]
        motto = e[5] or ''
        e_stage = e[9]
        fname = 'frontispiece.html' if num == 0 else f'emblem-{num:02d}.html'
        display = roman or 'F'
        img_path, img_exists = resolve_image(identity_map, num)
        if img_exists:
            img_tag = f'<img src="../{img_path}" alt="Emblem {display}" style="width:100%;aspect-ratio:auto;display:block">'
        else:
            img_tag = f'<div class="card-placeholder" style="aspect-ratio:1;font-size:2rem">{display}</div>'
        sbadge = ''
        if e_stage:
            sbg = stage_colors.get(e_stage, '#7f8c8d')
            sfg = stage_fg.get(e_stage, '#fff')
            sbadge = f'<span style="display:inline-block;background:{sbg};color:{sfg};font-size:0.65rem;padding:0.15rem 0.4rem;border-radius:2px;font-family:var(--font-sans)">{e_stage}</span>'
        grid_html += f"""
        <a href="{fname}" class="card" style="text-decoration:none;color:inherit">
            {img_tag}
            <div class="card-body">
                <div class="card-sig">{display}. {label} {sbadge}</div>
                <div class="card-desc">{motto[:80]}{'...' if len(motto) > 80 else ''}</div>
                <div style="margin-top:0.5rem"><span style="font-size:0.8rem;color:var(--accent);font-family:var(--font-sans)">View details &rarr;</span></div>
            </div>
        </a>"""

    idx_body = f"""
    <div class="page-content" style="max-width:1400px">
        <h2>All 50 Emblems + Frontispiece</h2>
        <p>Click any emblem for the comparative view with scholarly commentary.</p>
        <div class="gallery" style="grid-template-columns:repeat(auto-fill, minmax(200px, 1fr));padding:1rem 0">{grid_html}</div>
    </div>"""
    html = page_shell('All Emblems', idx_body, active_nav='Emblems', depth=1)
    (emblems_dir / 'index.html').write_text(html, encoding='utf-8')

    print(f"  emblems/: {len(emblems)} detail pages + index")


# ============================================================
# About Page
# ============================================================

def build_about(conn):
    total = conn.execute("SELECT COUNT(*) FROM emblems WHERE number > 0").fetchone()[0]
    with_motto = conn.execute("SELECT COUNT(*) FROM emblems WHERE motto_english IS NOT NULL").fetchone()[0]
    with_disc = conn.execute("SELECT COUNT(*) FROM emblems WHERE discourse_summary IS NOT NULL").fetchone()[0]
    refs = conn.execute("SELECT COUNT(*) FROM scholarly_refs").fetchone()[0]
    sources = conn.execute("SELECT COUNT(*) FROM emblem_sources").fetchone()[0]
    bib = conn.execute("SELECT COUNT(*) FROM bibliography").fetchone()[0]
    auths = conn.execute("SELECT COUNT(*) FROM source_authorities").fetchone()[0]

    body = f"""
    <div class="page-content">
        <h2>About This Project</h2>
        <p>AtalantaClaudiens is a digital humanities project showcasing H.M.E. De Jong's scholarship
        on Michael Maier's <em>Atalanta Fugiens</em> (1618), an alchemical emblem book combining
        50 engraved plates, Latin mottos, epigrams, prose discourses, and three-voice musical fugues.</p>

        <h2>Project Statistics</h2>
        <div class="stats" style="max-width:100%">
            <div class="stat-card"><span class="stat-number">{total}</span><span class="stat-label">Emblems</span></div>
            <div class="stat-card"><span class="stat-number">{with_motto}</span><span class="stat-label">Mottos Extracted</span></div>
            <div class="stat-card"><span class="stat-number">{refs}</span><span class="stat-label">Scholarly References</span></div>
            <div class="stat-card"><span class="stat-number">{sources}</span><span class="stat-label">Source Links</span></div>
        </div>
        <div class="stats" style="max-width:100%">
            <div class="stat-card"><span class="stat-number">{bib}</span><span class="stat-label">Bibliography Entries</span></div>
            <div class="stat-card"><span class="stat-number">{auths}</span><span class="stat-label">Source Authorities</span></div>
            <div class="stat-card"><span class="stat-number">{with_disc}</span><span class="stat-label">Discourse Summaries</span></div>
        </div>

        <h2>Data Provenance</h2>
        <p>Data is extracted from scholarly sources using deterministic regex parsing.
        All content is tracked by source method and confidence level.
        AI-assisted content is explicitly marked.</p>
        <div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;margin:1rem 0">
            <tr style="border-bottom:1px solid var(--border)">
                <td style="padding:0.5rem"><strong>SEED_DATA</strong></td>
                <td style="padding:0.5rem">Loaded from structured JSON seed file</td>
            </tr>
            <tr style="border-bottom:1px solid var(--border)">
                <td style="padding:0.5rem"><strong>CORPUS_EXTRACTION</strong></td>
                <td style="padding:0.5rem">Parsed from source text by Python scripts</td>
            </tr>
            <tr>
                <td style="padding:0.5rem"><strong>LLM_ASSISTED</strong></td>
                <td style="padding:0.5rem">Generated by language model (marked with review badges)</td>
            </tr>
        </table></div>

        <h2>Image Credits</h2>
        <p>The 51 plates of <em>Atalanta Fugiens</em> reproduced on this site come from <a href="https://furnaceandfugue.org/" target="_blank" rel="noopener" style="color:var(--accent)"><em>Furnace and Fugue: A Digital Edition of Michael Maier's Atalanta fugiens (1618) with Scholarly Commentary</em></a>, edited by Tara Nummedal and Donna Bilak (Brown University Library and Brown University Digital Publications, 2018; University of Virginia Press, 2020). Images are used under the project's <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank" rel="noopener">CC BY-NC-ND 4.0</a> license; for high-resolution browsing, scholarly apparatus, and audio of the fugues we recommend visiting the project directly.</p>
        <p style="font-size:0.88rem;color:var(--text-muted)">Plates from other emblem books displayed in the <a href="visual.html" style="color:var(--accent)">Visual Browser</a> and <a href="galleries/index.html" style="color:var(--accent)">Galleries</a> are public-domain originals, served via the sister project <a href="https://t3dy.github.io/AlchemyBeatEmUp/" target="_blank" rel="noopener" style="color:var(--accent)">AlchemyBeatEmUp</a> (which scraped them from Wikimedia Commons and the Internet Archive). Pixelated game-asset versions in that sister project are NOT shown here — every cross-corpus image on Claudiens is the original engraving.</p>

        <h2>Architecture</h2>
        <p>SQLite database &rarr; Python scripts &rarr; Static HTML/CSS/JS &rarr; GitHub Pages.
        No frameworks, no build tools, no runtime dependencies.</p>
        <p><a href="https://github.com/t3dy/AtalantaClaudiens" style="color:var(--accent)">View on GitHub &rarr;</a></p>
    </div>"""

    html = page_shell('About', body, active_nav='About')
    (SITE_DIR / 'about.html').write_text(html, encoding='utf-8')
    print(f"  about.html")


# ============================================================
# Scholars Pages
# ============================================================

def build_scholars_pages(conn):
    scholars_dir = SITE_DIR / 'scholar'
    scholars_dir.mkdir(exist_ok=True)

    scholars = conn.execute("""
        SELECT id, name, specialization, af_focus, overview, review_status
        FROM scholars ORDER BY name
    """).fetchall()

    # Index page
    cards_html = ''
    for s in scholars:
        sid, name, spec, focus, overview, status = s
        work_count = conn.execute(
            "SELECT COUNT(*) FROM scholar_works WHERE scholar_id = ?", (sid,)
        ).fetchone()[0]
        ref_count = conn.execute("""
            SELECT COUNT(DISTINCT sr.emblem_id) FROM scholarly_refs sr
            JOIN bibliography b ON sr.bib_id = b.id
            JOIN scholar_works sw ON sw.bib_id = b.id
            WHERE sw.scholar_id = ?
        """, (sid,)).fetchone()[0]
        slug = slugify(name)
        cards_html += f"""
        <a href="scholar/{slug}.html" class="card" style="text-decoration:none;color:inherit">
            <div class="card-body">
                <div class="card-sig">{name}</div>
                <div class="card-label">{spec or ''}</div>
                <div class="card-desc">{focus or ''}</div>
                <div style="margin-top:0.5rem;font-size:0.8rem;color:var(--text-muted);font-family:var(--font-sans)">
                    {work_count} work{'s' if work_count != 1 else ''} &middot; {ref_count} emblem{'s' if ref_count != 1 else ''} covered
                </div>
                <div style="margin-top:0.4rem"><span style="font-size:0.8rem;color:var(--accent);font-family:var(--font-sans)">View profile &rarr;</span></div>
            </div>
        </a>"""

    body = f"""
    <div class="page-content" style="max-width:1200px">
        <h2>Scholars</h2>
        <p>{len(scholars)} scholars who have published on <em>Atalanta Fugiens</em>.</p>
        <div class="gallery" style="padding:1rem 0">{cards_html}</div>
    </div>"""
    html = page_shell('Scholars', body, active_nav='Scholars')
    (SITE_DIR / 'scholars.html').write_text(html, encoding='utf-8')

    # Individual pages
    for s in scholars:
        sid, name, spec, focus, overview, status = s
        slug = slugify(name)

        works = conn.execute("""
            SELECT b.author, b.title, b.year, b.journal, b.publisher, b.af_relevance, b.pub_type
            FROM bibliography b
            JOIN scholar_works sw ON sw.bib_id = b.id
            WHERE sw.scholar_id = ?
            ORDER BY b.year
        """, (sid,)).fetchall()

        works_html = ''
        for w in works:
            rel_badge = f'<span class="badge badge-{"primary" if w[5] == "PRIMARY" else "direct" if w[5] == "DIRECT" else "contextual"}">{w[5]}</span>'
            works_html += f"""
            <div class="ref-card">
                <h4>{w[0]} ({w[2] or '?'}) {rel_badge}</h4>
                <p><em>{w[1]}</em></p>
                <p style="font-size:0.8rem;color:var(--text-muted)">{w[3] or w[4] or ''} &middot; {w[6] or ''}</p>
            </div>"""

        # Emblems with this scholar's commentary
        emblem_refs = conn.execute("""
            SELECT DISTINCT e.number, e.roman_numeral, e.canonical_label,
                   e.motto_english, e.alchemical_stage
            FROM scholarly_refs sr
            JOIN bibliography b ON sr.bib_id = b.id
            JOIN scholar_works sw ON sw.bib_id = b.id
            JOIN emblems e ON sr.emblem_id = e.id
            WHERE sw.scholar_id = ? AND e.number > 0
            ORDER BY e.number
        """, (sid,)).fetchall()
        coverage_html = ''
        if emblem_refs:
            cards = ''
            for er in emblem_refs:
                num_, roman_, label_, motto_, stage_ = er
                stage_chip = f' <span class="badge badge-stage" style="font-size:0.6rem;vertical-align:middle">{stage_}</span>' if stage_ else ''
                cards += f"""
                <a href="../emblems/emblem-{num_:02d}.html" class="related-emblem-card" style="display:block">
                    <strong>Emblem {roman_ or num_}</strong>{stage_chip}
                    <div style="font-size:0.78rem;color:var(--text-muted);margin-top:0.15rem">{(label_ or '').strip()}</div>
                </a>"""
            coverage_html = f'<h2>Emblems Covered <span class="badge badge-contextual">{len(emblem_refs)}</span></h2><div class="related-grid" style="display:flex;flex-wrap:wrap;gap:0.4rem">{cards}</div>'

        body = f"""
        <div class="page-content">
            <a href="../scholars.html" class="back-link">&larr; All Scholars</a>
            <h1 style="font-size:1.8rem;margin-bottom:0.5rem">{name}</h1>
            <p style="color:var(--text-muted);font-family:var(--font-sans);margin-bottom:1.5rem">{spec or ''}</p>
            {f'<p style="margin-bottom:1rem">{focus}</p>' if focus else ''}
            {format_paragraphs(overview) if overview else ''}
            {f'<h2>Works in Archive</h2>{works_html}' if works_html else '<p style="color:var(--text-muted)"><em>No works linked yet.</em></p>'}
            {coverage_html}
        </div>"""
        html = page_shell(name, body, active_nav='Scholars', depth=1)
        (scholars_dir / f'{slug}.html').write_text(html, encoding='utf-8')

    print(f"  scholars.html + {len(scholars)} scholar pages")


# ============================================================
# Bibliography Page
# ============================================================

def build_bibliography(conn):
    entries = conn.execute("""
        SELECT source_id, author, title, year, journal, publisher, pub_type, af_relevance, in_collection, annotation, url
        FROM bibliography ORDER BY year
    """).fetchall()

    # Build scholar lookup: source_id -> list of (scholar_name, slug)
    scholar_map = {}
    for row in conn.execute('''
        SELECT b.source_id, s.name FROM bibliography b
        JOIN scholar_works sw ON sw.bib_id = b.id
        JOIN scholars s ON sw.scholar_id = s.id
    ''').fetchall():
        scholar_map.setdefault(row[0], []).append((row[1], slugify(row[1])))

    # Load works page anchors (from staging if available)
    works_ids = set()
    works_path = BASE_DIR / 'staging' / 'works_merged.json'
    if works_path.exists():
        works_data = json.loads(works_path.read_text(encoding='utf-8'))
        works_ids = set(w.get('source_id', '') for w in works_data.get('works', []))

    rows_html = ''
    for e in entries:
        src_id, author, title, year, journal, pub, ptype, rel, incoll, annotation = e[:10]
        url = e[10] if len(e) > 10 else None
        rel_badge = f'<span class="badge badge-{"primary" if rel == "PRIMARY" else "direct" if rel == "DIRECT" else "contextual"}">{rel}</span>'
        venue = journal or pub or ''
        title_html = f'<a href="{url}" target="_blank" rel="noopener">{title}</a>' if url else title

        # Build navigation links
        nav_links = []
        if url:
            nav_links.append(f'<a href="{url}" target="_blank" rel="noopener" style="color:var(--accent)">View online &rarr;</a>')
        if src_id in works_ids:
            nav_links.append(f'<a href="works.html#{src_id}" style="color:var(--accent)">Read summary &rarr;</a>')
        for scholar_name, scholar_slug in scholar_map.get(src_id, []):
            nav_links.append(f'<a href="scholar/{scholar_slug}.html" style="color:var(--accent)">{scholar_name} &rarr;</a>')
        nav_html = f'<p style="font-size:0.8rem;margin-top:0.3rem">{" &middot; ".join(nav_links)}</p>' if nav_links else ''

        rows_html += f"""
        <div class="ref-card">
            <h4>{author} ({year or 'n.d.'}) {rel_badge}</h4>
            <p><em>{title_html}</em></p>
            <p style="font-size:0.8rem;color:var(--text-muted)">{venue} &middot; {ptype or ''}</p>
            {f'<p style="font-size:0.88rem;line-height:1.6;margin-top:0.5rem">{annotation}</p>' if annotation else ''}
            {nav_html}
        </div>"""

    primary = len([e for e in entries if e[7] == 'PRIMARY'])
    direct = len([e for e in entries if e[7] == 'DIRECT'])
    body = f"""
    <div class="page-content">
        <h2>Bibliography</h2>
        <div class="stats" style="max-width:100%">
            <div class="stat-card"><span class="stat-number">{len(entries)}</span><span class="stat-label">Total Works</span></div>
            <div class="stat-card"><span class="stat-number">{primary}</span><span class="stat-label">Primary</span></div>
            <div class="stat-card"><span class="stat-number">{direct}</span><span class="stat-label">Direct</span></div>
        </div>
        {rows_html}
    </div>"""
    html = page_shell('Bibliography', body, active_nav='Bibliography')
    (SITE_DIR / 'bibliography.html').write_text(html, encoding='utf-8')
    print(f"  bibliography.html: {len(entries)} entries")


# ============================================================
# Dictionary Pages
# ============================================================

def build_dictionary_pages(conn):
    dict_dir = SITE_DIR / 'dictionary'
    dict_dir.mkdir(exist_ok=True)

    terms = conn.execute("""
        SELECT id, slug, label, category, definition_short, definition_long,
               significance_to_af, source_basis, review_status, label_latin, registers
        FROM dictionary_terms ORDER BY label
    """).fetchall()

    # Count emblem refs per term
    emblem_counts = {}
    for t in terms:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM term_emblem_refs WHERE term_id = ?", (t[0],)
        ).fetchone()[0]
        emblem_counts[t[0]] = cnt

    # Group by category
    categories = {}
    for t in terms:
        cat = t[3] or 'UNCATEGORIZED'
        categories.setdefault(cat, []).append(t)

    # Index page with rich cards
    cat_html = ''
    for cat in sorted(categories.keys()):
        cat_terms = categories[cat]
        cards = ''
        for t in cat_terms:
            tid, slug, label, tcat, def_short = t[0], t[1], t[2], t[3], t[4]
            label_latin = t[9]
            ecnt = emblem_counts.get(tid, 0)
            latin_line = f'<div class="dict-latin">{label_latin}</div>' if label_latin and label_latin != label else ''
            search_blob = f'{label} {label_latin or ""} {def_short or ""}'.lower().replace('"', '&quot;')
            cards += f"""
            <div class="dict-card-wrap" data-category="{tcat}" data-search="{search_blob}">
                <a href="{slug}.html" class="dict-card">
                    <div class="dict-label">{label}
                        {f'<span class="badge badge-contextual">{ecnt} emblems</span>' if ecnt else ''}
                    </div>
                    {latin_line}
                    <div class="dict-def">{def_short or ""}</div>
                    <div style="margin-top:0.3rem"><span style="font-size:0.75rem;color:var(--accent);font-family:var(--font-sans)">View definition &rarr;</span></div>
                </a>
                <a href="index.html#category={tcat}" class="badge badge-stage dict-card-cat" title="Show only {tcat} terms">{tcat}</a>
            </div>"""
        cat_html += f"""
        <div class="dict-category-block" data-category="{cat}" style="margin-bottom:2rem">
            <h3 style="font-size:1.1rem;color:var(--accent);margin-bottom:0.75rem">{cat} <span class="badge badge-contextual dict-cat-count" data-cat="{cat}">{len(cat_terms)}</span></h3>
            {cards}
        </div>"""

    cat_chips = '<button class="filter-chip filter-chip-all active" data-filter-type="category" data-filter-value="" type="button">All</button>'
    for cat in sorted(categories.keys()):
        cat_chips += f'<button class="filter-chip" data-filter-type="category" data-filter-value="{cat}" type="button">{cat} <span class="filter-chip-count">{len(categories[cat])}</span></button>'

    body = f"""
    <div class="page-content">
        <h2>Dictionary of <em>Atalanta Fugiens</em></h2>
        <p>Key alchemical terms as they appear in Maier's text, with Latin originals. <span id="dict-total">{len(terms)}</span> terms across {len(categories)} categories.</p>
        <div class="filter-bar">
            <input type="search" id="dict-search" class="filter-search" placeholder="Search terms by label, Latin, or definition&hellip;" autocomplete="off">
            <div class="filter-row">
                <span class="filter-label">Category:</span>
                {cat_chips}
            </div>
            <div class="filter-status" id="dict-filter-status"></div>
        </div>
        {cat_html}
    </div>
    <script>
    (function() {{
        const search = document.getElementById('dict-search');
        const status = document.getElementById('dict-filter-status');
        const total = {len(terms)};
        let activeCat = '';
        let activeText = '';

        function readHash() {{
            if (!window.location.hash) return;
            const hash = window.location.hash.slice(1);
            hash.split('&').forEach(pair => {{
                const [k, v] = pair.split('=');
                if (k === 'category' && v) activeCat = decodeURIComponent(v);
                if (k === 'q' && v) {{
                    activeText = decodeURIComponent(v).toLowerCase();
                    if (search) search.value = decodeURIComponent(v);
                }}
            }});
        }}

        function applyDictFilters() {{
            let visible = 0;
            const perCat = {{}};
            document.querySelectorAll('.dict-card-wrap').forEach(card => {{
                const cat = card.dataset.category || '';
                const blob = card.dataset.search || '';
                const matchCat = !activeCat || cat === activeCat;
                const matchText = !activeText || blob.includes(activeText);
                const show = matchCat && matchText;
                card.style.display = show ? '' : 'none';
                if (show) {{
                    visible++;
                    perCat[cat] = (perCat[cat] || 0) + 1;
                }}
            }});
            document.querySelectorAll('.dict-category-block').forEach(block => {{
                const cat = block.dataset.category;
                const cnt = perCat[cat] || 0;
                block.style.display = cnt > 0 ? '' : 'none';
                const counter = block.querySelector('.dict-cat-count');
                if (counter) counter.textContent = cnt;
            }});
            document.querySelectorAll('.filter-chip[data-filter-type="category"]').forEach(chip => {{
                const value = chip.dataset.filterValue;
                const isAll = chip.classList.contains('filter-chip-all');
                chip.classList.toggle('active', isAll ? !activeCat : activeCat === value);
            }});
            if (status) {{
                if (activeCat || activeText) {{
                    const parts = [];
                    if (activeCat) parts.push('category <strong>' + activeCat + '</strong>');
                    if (activeText) parts.push('text <strong>"' + activeText.replace(/[<>&"]/g, c => ({{'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}}[c])) + '"</strong>');
                    status.innerHTML = 'Showing <strong>' + visible + '</strong> of ' + total + ' terms — filtered by ' + parts.join(', ') + ' <a href="#" id="dict-filter-clear" class="filter-clear">clear all</a>';
                    const clearLink = document.getElementById('dict-filter-clear');
                    if (clearLink) clearLink.addEventListener('click', e => {{ e.preventDefault(); clearDictFilters(); }});
                }} else {{
                    status.innerHTML = '';
                }}
            }}
        }}

        function clearDictFilters() {{
            activeCat = '';
            activeText = '';
            if (search) search.value = '';
            if (window.history && window.history.replaceState) {{
                window.history.replaceState(null, '', window.location.pathname);
            }}
            applyDictFilters();
        }}

        document.querySelectorAll('.filter-chip[data-filter-type="category"]').forEach(chip => {{
            chip.addEventListener('click', () => {{
                const v = chip.dataset.filterValue;
                activeCat = (activeCat === v) ? '' : v;
                applyDictFilters();
            }});
        }});
        if (search) {{
            search.addEventListener('input', e => {{
                activeText = e.target.value.trim().toLowerCase();
                applyDictFilters();
            }});
        }}
        window.addEventListener('hashchange', () => {{
            activeCat = '';
            activeText = '';
            if (search) search.value = '';
            readHash();
            applyDictFilters();
        }});
        readHash();
        applyDictFilters();
    }})();
    </script>"""
    html = page_shell('Dictionary', body, active_nav='Dictionary', depth=1)
    (dict_dir / 'index.html').write_text(html, encoding='utf-8')

    # Individual term pages
    for t in terms:
        tid, slug, label, cat, def_short, def_long, sig, basis, status, label_latin = t[:10]
        registers_json = t[10] if len(t) > 10 else None

        # Find linked emblems
        emblem_refs = conn.execute("""
            SELECT e.number, e.roman_numeral, e.canonical_label
            FROM term_emblem_refs ter
            JOIN emblems e ON ter.emblem_id = e.id
            WHERE ter.term_id = ?
            ORDER BY e.number
        """, (tid,)).fetchall()

        emblem_links = ' '.join(
            f'<a href="../emblems/emblem-{er[0]:02d}.html" class="source-link">Emblem {er[1]}: {er[2]}</a>'
            for er in emblem_refs if er[0] > 0
        )

        # Related terms
        related = conn.execute("""
            SELECT dt.slug, dt.label, dtl.link_type
            FROM dictionary_term_links dtl
            JOIN dictionary_terms dt ON dtl.linked_term_id = dt.id
            WHERE dtl.term_id = ?
        """, (tid,)).fetchall()
        related_html = ' '.join(
            f'<a href="{r[0]}.html" class="source-link">{r[1]}</a>'
            for r in related
        )

        latin_display = f'<div class="term-latin">{label_latin}</div>' if label_latin and label_latin != label else ''

        # Sibling terms: up to 8 alphabetical neighbours in the same category
        siblings = conn.execute("""
            SELECT slug, label, label_latin, definition_short
            FROM dictionary_terms
            WHERE category = ? AND id != ?
            ORDER BY label
        """, (cat, tid)).fetchall()
        sibling_cards_html = ''
        if siblings:
            shown = siblings[:8]
            card_pieces = []
            for s in shown:
                latin = f'<div class="dict-related-latin">{s[2]}</div>' if s[2] and s[2] != s[1] else ''
                card_pieces.append(f'<a href="{s[0]}.html" class="dict-related-card"><div class="dict-related-label">{s[1]}</div>{latin}</a>')
            sibling_cards_html = ''.join(card_pieces)
            extra_link = ''
            if len(siblings) > 8:
                extra_link = f'<p style="margin-top:0.5rem;font-size:0.82rem;font-family:var(--font-sans)"><a href="index.html#category={cat}" style="color:var(--accent)">See all {len(siblings) + 1} {cat} terms &rarr;</a></p>'
            sibling_block = f'<h2>More in <a href="index.html#category={cat}" style="color:inherit">{cat}</a></h2><div class="dict-related">{sibling_cards_html}</div>{extra_link}'
        else:
            sibling_block = ''

        body = f"""
        <div class="page-content">
            <a href="index.html" class="back-link">&larr; Dictionary of <em>Atalanta Fugiens</em></a>
            <h1 style="font-size:1.8rem;margin-bottom:0.3rem">{label}
                <a href="index.html#category={cat}" class="badge badge-stage" title="Show only {cat} terms" style="text-decoration:none">{cat}</a>
            </h1>
            {latin_display}
            {f'<div class="motto-block">{def_short}</div>' if def_short else ''}
            {format_paragraphs(autolink_emblems(def_long)) if def_long else ''}
            {build_registers_html(registers_json)}
            {f'<h2>In <em>Atalanta Fugiens</em></h2><p style="font-size:0.95rem;line-height:1.7">{autolink_emblems(sig)}</p>' if sig else ''}
            {f'<h2>Appears in Emblems</h2><div>{emblem_links}</div>' if emblem_links else ''}
            {f'<h2>Related Terms</h2><div>{related_html}</div>' if related_html else ''}
            {sibling_block}
            <div id="depicts-panel" data-slug="{slug}"></div>
            {f'<p style="margin-top:1.5rem;font-size:0.8rem;color:var(--text-muted)">Source: {basis}</p>' if basis else ''}
        </div>
        <script>
        (async function() {{
            const panel = document.getElementById('depicts-panel');
            if (!panel) return;
            const slug = panel.dataset.slug;
            try {{
                const resp = await fetch('../dictionary-depicts.json');
                if (!resp.ok) return;
                const data = await resp.json();
                const items = data[slug];
                if (!items || !items.length) return;
                // Group by source work
                const byWork = {{}};
                for (const it of items) {{
                    (byWork[it.work_title || it.work] = byWork[it.work_title || it.work] || []).push(it);
                }}
                const workCount = Object.keys(byWork).length;
                const total = items.length;
                const cards = items.slice(0, 24).map(im => {{
                    const linkOpen = im.link_url
                        ? '<a href="' + (im.is_external ? im.link_url : '../' + im.link_url) + '"' + (im.is_external ? ' target="_blank" rel="noopener"' : '') + ' class="depicts-card">'
                        : '<div class="depicts-card" style="cursor:default">';
                    const linkClose = im.link_url ? '</a>' : '</div>';
                    const imgSrc = im.local_url
                        ? (im.is_external ? im.local_url : '../' + im.local_url)
                        : null;
                    const img = imgSrc
                        ? '<img src="' + imgSrc + '" alt="' + (im.work_title || '') + '" loading="lazy">'
                        : '<div class="depicts-placeholder">' + ((im.folio || '?').replace('plate ', '').toUpperCase()) + '</div>';
                    return linkOpen + img +
                        '<div class="depicts-meta">' +
                            '<div class="depicts-work">' + (im.work_title || '') + '</div>' +
                            '<div class="depicts-folio">' + (im.folio || '') + '</div>' +
                        '</div>' + linkClose;
                }}).join('');
                const overflow = items.length > 24 ? '<p style="font-size:0.82rem;color:var(--text-muted);font-style:italic">…and ' + (items.length - 24) + ' more in <a href="../visual.html#tag=' + encodeURIComponent(slug.replace(/-/g, '_')) + '">visual browser</a>.</p>' : '';
                panel.innerHTML =
                    '<h2>Depicted in <span class="badge badge-contextual">' + total + ' image' + (total !== 1 ? 's' : '') + ' across ' + workCount + ' work' + (workCount !== 1 ? 's' : '') + '</span></h2>' +
                    '<p style="font-size:0.85rem;color:var(--text-muted);font-family:var(--font-sans);margin-bottom:0.7rem">Cross-corpus matches from the <a href="../visual.html">visual browser</a>.</p>' +
                    '<div class="depicts-grid">' + cards + '</div>' +
                    overflow;
            }} catch (err) {{
                /* silent — feature is optional */
            }}
        }})();
        </script>"""
        html = page_shell(label, body, active_nav='Dictionary', depth=1)
        (dict_dir / f'{slug}.html').write_text(html, encoding='utf-8')

    print(f"  dictionary/: {len(terms)} term pages + index")


# ============================================================
# Timeline Page
# ============================================================

def _extract_emblem_refs(text):
    """Return sorted list of unique emblem numbers referenced in text (Roman + Arabic)."""
    if not text:
        return []
    import re as _re
    found = set()
    roman_map = {'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10,
                 'XI':11,'XII':12,'XIII':13,'XIV':14,'XV':15,'XVI':16,'XVII':17,'XVIII':18,
                 'XIX':19,'XX':20,'XXI':21,'XXII':22,'XXIII':23,'XXIV':24,'XXV':25,'XXVI':26,
                 'XXVII':27,'XXVIII':28,'XXIX':29,'XXX':30,'XXXI':31,'XXXII':32,'XXXIII':33,
                 'XXXIV':34,'XXXV':35,'XXXVI':36,'XXXVII':37,'XXXVIII':38,'XXXIX':39,'XL':40,
                 'XLI':41,'XLII':42,'XLIII':43,'XLIV':44,'XLV':45,'XLVI':46,'XLVII':47,
                 'XLVIII':48,'XLIX':49,'L':50}
    rx_roman = _re.compile(
        r'Emblem\s+(XLVIII|XXXVIII|XXXIII|XXVIII|XXIII|XVIII|XLVII|XXXVII|XXXIV|XXXII|XXVII|XXXIX|XXXVI|XXXV|XXVI|XXIV|XXII|XVII|XLVI|XLIV|XLIII|XLII|XIII|XXXI|XXIX|XVI|XLV|XLI|XII|XXX|XIV|XXV|XIX|XV|XXI|XX|XI|IX|XL|IV|VI|II|VIII|VII|III|XLIX|I|V|X|L)'
    )
    for m in rx_roman.finditer(text):
        n = roman_map.get(m.group(1))
        if n is not None:
            found.add(n)
    for m in _re.finditer(r'Emblem\s+(\d{1,2})(?=[^0-9]|$)', text):
        n = int(m.group(1))
        if 0 <= n <= 50:
            found.add(n)
    return sorted(found)


def build_timeline(conn):
    events = conn.execute("""
        SELECT id, year, year_end, event_type, title, description, confidence,
               description_long
        FROM timeline_events ORDER BY year, id
    """).fetchall()

    TYPE_COLORS = {
        'PUBLICATION': '#27ae60', 'EDITION': '#2980b9', 'SCHOLARSHIP': '#8e44ad',
        'BIOGRAPHY': '#e67e22', 'DIGITAL': '#16a085', 'FACSIMILE': '#795548',
        'CONTEXT': '#795548', 'TRANSLATION': '#2980b9',
    }

    # Emblem labels for badge tooltips
    emblem_meta = {
        e[0]: {'roman': e[1], 'label': e[2]}
        for e in conn.execute("SELECT number, roman_numeral, canonical_label FROM emblems").fetchall()
    }

    events_by_emblem = {}  # emblem_number -> [event records]
    type_set = set()
    decade_set = set()
    events_data = []  # rich list for inline JS

    events_html = ''
    prev_year = None
    for e in events:
        eid, year, year_end, etype, title, desc, conf, desc_long = e
        color = TYPE_COLORS.get(etype, '#7f8c8d')
        type_set.add(etype or '')
        if year:
            decade_set.add((year // 10) * 10)
        year_header = f'<div class="timeline-year">{year}</div>' if year != prev_year else ''
        display_desc = desc_long or desc or ''
        # Detect emblem references and render badges
        emb_refs = _extract_emblem_refs(title + ' ' + display_desc)
        emb_badges = ''
        for n in emb_refs:
            meta = emblem_meta.get(n)
            href = 'emblems/frontispiece.html' if n == 0 else f'emblems/emblem-{n:02d}.html'
            roman = (meta or {}).get('roman') or str(n)
            label = (meta or {}).get('label') or ''
            emb_badges += f'<a href="{href}" class="related-emblem-card" title="{label}"><strong>{roman}</strong></a>'
            events_by_emblem.setdefault(n, []).append({
                'year': year,
                'year_end': year_end,
                'type': etype,
                'title': title,
            })
        emb_block = f'<div class="related-grid" style="margin-top:0.4rem;display:flex;flex-wrap:wrap;gap:0.3rem">{emb_badges}</div>' if emb_badges else ''

        # Search blob for filtering
        search_blob = (title + ' ' + display_desc).lower().replace('"', '&quot;')
        decade = (year // 10) * 10 if year else 0
        events_data.append({
            'year': year, 'type': etype or '', 'decade': decade,
        })

        events_html += f"""{year_header}
        <div class="timeline-card" data-event-type="{etype or ''}" data-decade="{decade}" data-search="{search_blob}" style="border-left:4px solid {color}">
            <h4><span class="badge" style="background:{color};color:white">{etype}</span> {title}</h4>
            <div class="event-desc">{autolink_emblems(display_desc, depth=0)}</div>
            {emb_block}
        </div>"""
        prev_year = year

    # Persist events_by_emblem as JSON for emblem pages to consume
    (SITE_DIR / 'timeline-by-emblem.json').write_text(
        json.dumps(events_by_emblem, ensure_ascii=False), encoding='utf-8'
    )

    type_chips = ''.join(
        f'<button class="filter-chip" type="button" data-tl-type="{t}" style="background:{TYPE_COLORS.get(t, "#7f8c8d")};color:white;border:1px solid {TYPE_COLORS.get(t, "#7f8c8d")}">{t}</button>'
        for t in sorted(type_set) if t
    )
    decade_chips = ''.join(
        f'<button class="filter-chip" type="button" data-tl-decade="{d}">{d}s</button>'
        for d in sorted(decade_set)
    )

    body = f"""
    <div class="page-content">
        <h2>Timeline of Atalanta Fugiens</h2>
        <p>Reception and scholarship from 1568 to the present. {len(events)} events; events that reference specific emblems link directly.</p>
        <div class="filter-bar">
            <input type="search" id="tl-search" class="filter-search" placeholder="Search timeline (e.g. Tilton, Rosicrucian, Emblem XLVIII)&hellip;" autocomplete="off">
            <div class="filter-row">
                <span class="filter-label">Type:</span>
                <button class="filter-chip filter-chip-all active" data-tl-type="" type="button">All</button>
                {type_chips}
            </div>
            <div class="filter-row">
                <span class="filter-label">Decade:</span>
                <button class="filter-chip filter-chip-all active" data-tl-decade="" type="button">All</button>
                {decade_chips}
            </div>
            <div class="filter-status" id="tl-status"></div>
        </div>
        <div id="tl-events">{events_html}</div>
    </div>
    <script>
    (function() {{
        const cards = Array.from(document.querySelectorAll('.timeline-card'));
        const yearHeaders = Array.from(document.querySelectorAll('.timeline-year'));
        const search = document.getElementById('tl-search');
        const status = document.getElementById('tl-status');
        let activeType = '';
        let activeDecade = '';
        let activeQuery = '';

        function readHash() {{
            if (!window.location.hash) return;
            window.location.hash.slice(1).split('&').forEach(p => {{
                const [k, v] = p.split('=');
                if (k === 'type' && v) activeType = decodeURIComponent(v);
                if (k === 'decade' && v) activeDecade = decodeURIComponent(v);
                if (k === 'q' && v) {{ activeQuery = decodeURIComponent(v).toLowerCase(); search.value = decodeURIComponent(v); }}
            }});
        }}

        function applyFilters() {{
            let visible = 0;
            cards.forEach(c => {{
                const t = c.dataset.eventType || '';
                const d = c.dataset.decade || '0';
                const blob = c.dataset.search || '';
                const matchT = !activeType || t === activeType;
                const matchD = !activeDecade || d === activeDecade;
                const matchQ = !activeQuery || blob.includes(activeQuery);
                const show = matchT && matchD && matchQ;
                c.style.display = show ? '' : 'none';
                if (show) visible++;
            }});
            // Hide year-headers whose group has no visible cards
            const groups = {{}};
            cards.forEach(c => {{
                const y = c.previousElementSibling;
                let header = c.previousElementSibling;
                while (header && !header.classList.contains('timeline-year')) header = header.previousElementSibling;
                if (header) {{
                    const yk = header.textContent;
                    if (!(yk in groups)) groups[yk] = false;
                    if (c.style.display !== 'none') groups[yk] = true;
                }}
            }});
            yearHeaders.forEach(h => {{
                h.style.display = groups[h.textContent] ? '' : 'none';
            }});
            // Chip active states
            document.querySelectorAll('[data-tl-type]').forEach(b => {{
                const v = b.dataset.tlType;
                const isAll = b.classList.contains('filter-chip-all');
                b.classList.toggle('active', isAll ? !activeType : activeType === v);
            }});
            document.querySelectorAll('[data-tl-decade]').forEach(b => {{
                const v = b.dataset.tlDecade;
                const isAll = b.classList.contains('filter-chip-all');
                b.classList.toggle('active', isAll ? !activeDecade : activeDecade === v);
            }});
            // Status
            if (activeType || activeDecade || activeQuery) {{
                const parts = [];
                if (activeType) parts.push('type <strong>' + activeType + '</strong>');
                if (activeDecade) parts.push('decade <strong>' + activeDecade + 's</strong>');
                if (activeQuery) parts.push('text <strong>"' + activeQuery.replace(/[<>&"]/g, c => ({{'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}}[c])) + '"</strong>');
                status.innerHTML = 'Showing <strong>' + visible + '</strong> of {len(events)} events — filtered by ' + parts.join(', ') + ' <a href="#" id="tl-clear" class="filter-clear">clear all</a>';
                const cl = document.getElementById('tl-clear');
                if (cl) cl.addEventListener('click', e => {{ e.preventDefault(); clearAll(); }});
            }} else {{
                status.innerHTML = '';
            }}
        }}

        function clearAll() {{
            activeType = ''; activeDecade = ''; activeQuery = '';
            search.value = '';
            if (window.history && window.history.replaceState) {{
                window.history.replaceState(null, '', window.location.pathname);
            }}
            applyFilters();
        }}

        document.body.addEventListener('click', e => {{
            const tBtn = e.target.closest('[data-tl-type]');
            if (tBtn) {{
                const v = tBtn.dataset.tlType;
                activeType = (activeType === v) ? '' : v;
                applyFilters();
                return;
            }}
            const dBtn = e.target.closest('[data-tl-decade]');
            if (dBtn) {{
                const v = dBtn.dataset.tlDecade;
                activeDecade = (activeDecade === v) ? '' : v;
                applyFilters();
                return;
            }}
        }});
        search.addEventListener('input', e => {{ activeQuery = e.target.value.trim().toLowerCase(); applyFilters(); }});
        window.addEventListener('hashchange', () => {{
            activeType = ''; activeDecade = ''; activeQuery = '';
            search.value = '';
            readHash();
            applyFilters();
        }});
        readHash();
        applyFilters();
    }})();
    </script>"""
    html = page_shell('Timeline', body, active_nav='Timeline')
    (SITE_DIR / 'timeline.html').write_text(html, encoding='utf-8')
    print(f"  timeline.html: {len(events)} events, {len(events_by_emblem)} emblems referenced")


# ============================================================
# Sources Page
# ============================================================

def _authority_slug(authority_id):
    """Convert AUTH_ROSARIUM -> rosarium for use in URL slugs."""
    s = (authority_id or '').lower()
    if s.startswith('auth_'):
        s = s[5:]
    return s.replace('_', '-')


def build_sources(conn, identity_map):
    authorities = conn.execute("""
        SELECT sa.id, sa.authority_id, sa.name, sa.type, sa.author, sa.era,
               sa.relationship_to_maier, sa.description_long,
               COUNT(es.id) as emblem_count
        FROM source_authorities sa
        LEFT JOIN emblem_sources es ON es.authority_id = sa.id
        GROUP BY sa.id
        ORDER BY sa.type, emblem_count DESC
    """).fetchall()

    TYPE_COLORS = {
        'CLASSICAL': '#8e44ad', 'ALCHEMICAL': '#c0392b', 'BIBLICAL': '#2980b9',
        'MEDICAL': '#27ae60', 'PATRISTIC': '#e67e22', 'HERMETIC': '#16a085',
        'MOVEMENT': '#795548',
    }

    # Group by type
    by_type = {}
    for a in authorities:
        t = a[3] or 'OTHER'
        by_type.setdefault(t, []).append(a)

    sections_html = ''
    for stype in ['HERMETIC', 'ALCHEMICAL', 'CLASSICAL', 'BIBLICAL', 'MEDICAL', 'PATRISTIC', 'MOVEMENT']:
        if stype not in by_type:
            continue
        color = TYPE_COLORS.get(stype, '#7f8c8d')
        auths = by_type[stype]
        cards = ''
        for a in auths:
            aid, auth_id, name, atype, author, era, rel, desc_long, count = a
            slug = _authority_slug(auth_id)
            # Find which emblems use this authority with numbers for links
            emblem_data = conn.execute("""
                SELECT e.number, e.roman_numeral FROM emblem_sources es
                JOIN emblems e ON es.emblem_id = e.id
                WHERE es.authority_id = ? AND e.number > 0
                ORDER BY e.number
            """, (aid,)).fetchall()
            emblem_badges = ' '.join(
                f'<a href="emblems/emblem-{ed[0]:02d}.html" class="emblem-link-badge">{ed[1]}</a>'
                for ed in emblem_data if ed[1]
            )
            cards += f"""
            <div class="source-card" id="{auth_id}" style="border-left:4px solid {color}">
                <h4><a href="source/{slug}.html" style="color:inherit;text-decoration:none">{name}</a> <span class="badge" style="background:{color};color:white">{count} emblems</span></h4>
                {f'<div class="source-desc">{desc_long}</div>' if desc_long else (f'<p style="font-size:0.9rem">{rel}</p>' if rel else '')}
                {f'<div class="emblem-links" style="margin-top:0.5rem">{emblem_badges}</div>' if emblem_badges else ''}
                <p style="margin-top:0.6rem;font-size:0.82rem;font-family:var(--font-sans)"><a href="source/{slug}.html" style="color:var(--accent)">Open authority page &rarr;</a></p>
            </div>"""
        sections_html += f"""
        <h2 style="margin-top:2rem"><span class="badge" style="background:{color};color:white;font-size:0.8rem">{stype}</span> {stype.title()} Sources</h2>
        {cards}"""

    body = f"""
    <div class="page-content">
        <h2>Maier's Sources &amp; Influences</h2>
        <p>{len(authorities)} source traditions identified by De Jong and other scholars, linked to {conn.execute("SELECT COUNT(*) FROM emblem_sources").fetchone()[0]} emblem references.</p>
        {sections_html}
    </div>"""
    html = page_shell('Sources & Influences', body, active_nav='Sources')
    (SITE_DIR / 'sources.html').write_text(html, encoding='utf-8')

    # ── Individual authority pages ──
    source_dir = SITE_DIR / 'source'
    source_dir.mkdir(exist_ok=True)
    for a in authorities:
        aid, auth_id, name, atype, author, era, rel, desc_long, count = a
        slug = _authority_slug(auth_id)
        color = TYPE_COLORS.get(atype, '#7f8c8d')

        # Emblems where this authority is cited (with image + motto)
        emblems_for = conn.execute("""
            SELECT e.id, e.number, e.roman_numeral, e.canonical_label,
                   e.motto_english, e.alchemical_stage
            FROM emblem_sources es
            JOIN emblems e ON es.emblem_id = e.id
            WHERE es.authority_id = ? AND e.number > 0
            ORDER BY e.number
        """, (aid,)).fetchall()
        emblem_cards_html = ''
        for em in emblems_for:
            eid_, num_, roman_, label_, motto_, stage_ = em
            img_path, img_exists = resolve_image(identity_map, num_)
            img_tag = (
                f'<img src="../{img_path}" alt="Emblem {roman_ or num_}" style="width:100%;display:block;aspect-ratio:auto">'
                if img_exists else
                f'<div class="card-placeholder" style="aspect-ratio:1;font-size:1.5rem">{roman_ or num_}</div>'
            )
            stage_chip = f' <span class="badge badge-stage" style="font-size:0.6rem;vertical-align:middle">{stage_}</span>' if stage_ else ''
            emblem_cards_html += f"""
            <a href="../emblems/emblem-{num_:02d}.html" class="card" style="text-decoration:none;color:inherit">
                {img_tag}
                <div class="card-body">
                    <div class="card-sig">Emblem {roman_ or num_}{stage_chip}</div>
                    <div class="card-label">{label_ or ''}</div>
                    <div class="card-desc">{(motto_ or '').strip()}</div>
                </div>
            </a>"""

        # Scholars who comment on this tradition: scholarly_refs whose source_texts_referenced mentions this authority
        scholar_rows = conn.execute("""
            SELECT DISTINCT b.author, sw.scholar_id, s.name
            FROM scholarly_refs sr
            JOIN bibliography b ON sr.bib_id = b.id
            LEFT JOIN scholar_works sw ON sw.bib_id = b.id
            LEFT JOIN scholars s ON sw.scholar_id = s.id
            WHERE sr.source_texts_referenced LIKE ?
            ORDER BY b.author
        """, ('%' + (auth_id or '') + '%',)).fetchall()
        scholar_links = ''
        seen_scholars = set()
        for srow in scholar_rows:
            sname = srow[2] or srow[0]
            if sname in seen_scholars:
                continue
            seen_scholars.add(sname)
            if srow[2]:
                scholar_links += f'<a href="../scholar/{slugify(srow[2])}.html" class="source-link">{sname}</a>'
            else:
                scholar_links += f'<span class="source-link" style="cursor:default">{sname}</span>'

        emblem_count_for = len(emblems_for)
        body = f"""
        <div class="page-content">
            <a href="../sources.html" class="back-link">&larr; All Sources</a>
            <h1 style="font-size:1.8rem;margin-bottom:0.3rem">{name}
                <span class="badge" style="background:{color};color:white;font-size:0.75rem;vertical-align:middle">{atype or ''}</span>
            </h1>
            <p style="color:var(--text-muted);font-family:var(--font-sans);margin-bottom:1rem;font-size:0.9rem">
                {(author + ' · ') if author else ''}{era or ''}{(' · ' if (author or era) and emblem_count_for else '')}{f'cited in {emblem_count_for} emblem{"s" if emblem_count_for != 1 else ""}' if emblem_count_for else ''}
            </p>
            {format_paragraphs(autolink_emblems(desc_long, depth=1)) if desc_long else ''}
            {f'<h2>Relationship to Maier</h2><p style="font-size:0.95rem;line-height:1.7">{rel}</p>' if rel and not desc_long else ''}
            {f'<h2>Cited in</h2><div class="gallery" style="grid-template-columns:repeat(auto-fill, minmax(200px, 1fr));padding:0">{emblem_cards_html}</div>' if emblem_cards_html else '<p style="color:var(--text-muted)"><em>No emblem citations recorded.</em></p>'}
            {f'<h2>Scholars who discuss this tradition</h2><div>{scholar_links}</div>' if scholar_links else ''}
        </div>"""
        html = page_shell(name, body, active_nav='Sources', depth=1)
        (source_dir / f'{slug}.html').write_text(html, encoding='utf-8')

    print(f"  sources.html: {len(authorities)} authorities + source/ pages")


# ============================================================
# Essays (placeholder index)
# ============================================================

def build_essays(conn):
    essays_dir = SITE_DIR / 'essays'
    essays_dir.mkdir(exist_ok=True)

    planned = [
        ("playful-reading", "Playful Reading in Atalanta Fugiens",
         "How Maier's emblem book invites ludic engagement through its combination of image, text, and music."),
        ("alchemical-symbolism", "Alchemical Symbolism and the Emblem Tradition",
         "The visual language of the 50 emblems and their roots in the European emblem book tradition."),
        ("musical-fugues", "Maier's Musical Fugues",
         "The role of the 50 three-voice canons and their structural relationship to alchemical process."),
        ("rosicrucian-context", "The Rosicrucian Context",
         "Maier's engagement with the Rosicrucian movement and its expression in Atalanta Fugiens."),
        ("reception-history", "Reception History: From 1618 to Digital Humanities",
         "Four centuries of scholarship on Atalanta Fugiens, from Craven to Furnace and Fugue."),
    ]

    cards_html = ''
    for slug, title, desc in planned:
        cards_html += f"""
        <div class="card" style="cursor:default">
            <div class="card-body">
                <div class="card-sig">{title}</div>
                <div class="card-desc">{desc}</div>
                <div style="margin-top:0.5rem"><span class="review-badge">COMING SOON</span></div>
            </div>
        </div>"""

    body = f"""
    <div class="page-content" style="max-width:1200px">
        <h2>Essays</h2>
        <p>Planned essays synthesized from the scholarly corpus. These will be AI-drafted and clearly marked.</p>
        <div class="gallery" style="padding:1rem 0">{cards_html}</div>
    </div>"""
    html = page_shell('Essays', body, active_nav='Essays', depth=1)
    (essays_dir / 'index.html').write_text(html, encoding='utf-8')
    print(f"  essays/: index (5 planned)")


# ============================================================
# Biography Page
# ============================================================

def build_szulakowska_page():
    """Build the Szulakowska feature page — in-depth treatment of Maier in her three monographs."""

    def emblem_img(num, caption=''):
        fname = f'emblem-{num:02d}.jpg' if num > 0 else 'emblem-00.jpg'
        cap = f'<figcaption style="font-size:0.8rem;color:var(--text-muted);margin-top:0.3rem;text-align:center">{caption}</figcaption>' if caption else ''
        return f'<figure style="margin:1rem auto;max-width:400px"><img src="images/emblems/{fname}" alt="Emblem {num}" style="width:100%;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.15)">{cap}</figure>'

    body = f"""
    <div class="page-content">
        <h1 style="font-size:1.8rem;margin-bottom:0.3rem">Szulakowska on Maier</h1>
        <p style="font-size:1.1rem;color:var(--text-muted);margin-bottom:1rem;font-style:italic">
            The Religious Politics of Alchemical Illustration
        </p>
        <p style="font-size:0.95rem;line-height:1.7;margin-bottom:1.5rem">
            Urszula Szulakowska's three monographs — <em>The Sacrificial Body and the Day of Doom</em> (Brill),
            <em>The Alchemy of Light</em> (Brill), and <em>The Alchemical Virgin Mary</em> (Cambridge Scholars) —
            offer a dimension of Maier scholarship found nowhere else: the religious and political context of
            alchemical illustration. Where De Jong traces each emblem to its textual sources and Tilton
            situates Maier within Rosicrucianism, Szulakowska reveals the Reformation theology, Eucharistic
            controversy, and Habsburg court politics encoded in the same images.
        </p>


        <h2>I. The Khunrath-Maier-Fludd Triad</h2>
        {format_paragraphs(
            "Szulakowska positions Maier within a triad of late-Renaissance Paracelsian alchemists — Heinrich "
            "Khunrath (1560-1605), Michael Maier (1568-1622), and Robert Fludd (1574-1637) — who collectively "
            "transformed alchemical illustration from medieval Christological imagery into a new classicizing "
            "visual language. She argues that Maier's emblems in the Atalanta Fugiens 'set the style for "
            "alchemical illustration for the next three centuries, replacing the earlier Christological motifs.' "
            "Fludd and Johann Daniel Mylius subsequently copied and adapted Maier's visual innovations, with "
            "Mylius reproducing AF emblems in detail in his Philosophia Reformata (1622)."
            "\\n\\n"
            "What distinguishes the triad is not merely their artistry but their theological ambition. "
            "Szulakowska argues that all three regarded their chemical procedures 'as being essentially the same "
            "rite as the mass' — a 'symbolic usurpation of the highest spiritual and political authority since "
            "the right to offer Communion was jealously guarded.' The alchemical laboratory becomes, in this "
            "reading, an alternative altar where the transmutation of matter re-enacts the Eucharistic "
            "transformation of bread and wine into the body and blood of Christ."
            "\\n\\n"
            "Yet Maier is the most reticent of the three. Where Khunrath openly identified Christ with the "
            "philosopher's stone, and Fludd developed elaborate cosmological diagrams, Maier 'disguised his "
            "religious references in barely decipherable signifiers.' His classical mythological surface — "
            "Atalanta, Hippomenes, Osiris, Oedipus — conceals what Szulakowska identifies as a fundamentally "
            "Eucharistic understanding of alchemical transformation. The reader who sees only pagan myth misses "
            "the sacramental structure beneath."
        )}

        <h2>II. The Alchemical Mass</h2>
        {format_paragraphs(
            "Szulakowska's most sustained analysis of Maier concerns the alchemical mass illustration from "
            "the Symbola Aureae Mensae Duodecim Nationum (1617). Maier reprinted a fifteenth-century treatise "
            "by Nicolaus Melchior Cibinensis (Processus sub forma missae) and commissioned Matthaeus Merian to "
            "engrave an accompanying illustration of the Virgin Mary as the Apocalyptic Woman from Revelation "
            "12:1 — 'a woman clothed with the sun, with the moon under her feet, and on her head a crown of "
            "twelve stars.'"
            "\\n\\n"
            "Szulakowska argues that Maier's illustration is 'a far more radical disquisition on the alchemical "
            "mass than Cibinensis' discrete original text.' Where the fifteenth-century author had cautiously "
            "discontinued his account before the consecration of bread and wine, Maier's engraving 'clearly "
            "identifies Christ with the lapis philosophorum and the elixir of life.' The chasuble of the "
            "officiating priest, the gestures of consecration, the presence of the Apocalyptic Woman — all "
            "constitute a bold exposition of the alchemical process as a re-enactment, not merely a "
            "symbolization, of the Catholic Communion."
            "\\n\\n"
            "In The Alchemical Virgin Mary, Szulakowska connects this image to the 'Turkish Madonna' "
            "tradition — Marian imagery linked to the Ottoman wars and the defense of Christendom. Emperor "
            "Rudolf II, Maier's patron, had been heavily involved in military campaigns against the Turks. "
            "The Apocalyptic Woman in Maier's illustration may thus function simultaneously as the Virgin Mary, "
            "as the alchemical lac virginis (virgin's milk), and as a political emblem of Christian resistance "
            "to Ottoman expansion — a triple register that exemplifies the density of meaning Szulakowska "
            "finds in Maier's visual program."
        )}

        <h2>III. Atalanta Fugiens: The Sacrificial Body</h2>
        <p style="font-size:0.95rem;line-height:1.7;margin-bottom:1rem">
            In <em>The Sacrificial Body</em>, Szulakowska reads six AF emblems through the lens of
            bodily transformation, Eucharistic symbolism, and Reformation theology. Her central argument
            is that the theme of dismemberment and resurrection — pervasive in the AF — encodes a
            specifically Christian soteriology beneath its classical surface.
        </p>

        <h3>Emblem XIX — The Four Warriors</h3>
        {emblem_img(19, 'Emblem XIX: If you kill one of the four, everybody will be dead immediately')}
        {format_paragraphs(
            "Szulakowska reads the four interconnected warriors (representing the four elements whose death "
            "is mutual) as a Christological allegory. She identifies Maier's reference to Hermes testifying "
            "that 'our Son shall live and the dead King shall come out of the fire' as a disguised reference "
            "to Christ's resurrection. When 'this dead one arises, then death, darkness and the waters of "
            "the abyss shall flee from him.' The dragon that guards the abyss flees from the sun-beams — "
            "'our Son' — in language that maps precisely onto Christian eschatology."
            "\\n\\n"
            "Where De Jong identifies the source as the myth of Geryon and the Turba Philosophorum's teaching "
            "about elemental inseparability, Szulakowska adds the Christological layer: the four warriors are "
            "not merely four elements but four aspects of the sacrificial body that must die together before "
            "resurrection is possible. Maier 'mitigates the degree of physical violence exhibited in his visual "
            "symbols' compared to earlier alchemical imagery, but retains their salvific meaning."
        )}

        <h3>Emblem XXIV — The Wolf Devouring the King</h3>
        {emblem_img(24, 'Emblem XXIV: The wolf devoured the king')}
        {format_paragraphs(
            "The wolf (antimony) devours the crowned king (Saturn/prime matter), then the wolf is consumed "
            "by fire, and the king returns to life 'in a young and vigorous form as the tincture that cures "
            "every disease.' Szulakowska traces this allegory to Basil Valentine's Twelve Keys, where the wolf "
            "symbolizes the mineral antimony used to separate gold from its matrix."
            "\\n\\n"
            "Lawrence Principe has identified the metallurgical reality behind this imagery: antimony sulphide "
            "was used in assaying to extract gold from base alloys. Szulakowska reads beyond the chemistry to "
            "identify the sacrificial-body theology: the king's dismemberment and reconstitution mirrors the "
            "Eucharistic sacrifice where the body of Christ is broken and distributed before being mystically "
            "reunited in the Resurrection."
        )}

        <h3>Emblem XXVIII — King Duenech in the Steam Bath</h3>
        {emblem_img(28, 'Emblem XXVIII: The king is bathed, sitting in a steam-bath')}
        {format_paragraphs(
            "King Duenech sits immersed in a steaming bath while black bile (aqua foetida) drains from his "
            "body, attended by physicians who regulate the temperature. Szulakowska connects this emblem to "
            "the alchemical understanding of bodily purification through the humoral system: 'alchemists used "
            "baths in order to improve the proportions of the humours in their chemicals, to produce healthy "
            "blood in the body and to convert cold and moist materials into warm and dry ones.'"
            "\\n\\n"
            "She notes that Maier 'refers to himself as a cook at the golden table' — a reference to the "
            "Symbola Aureae Mensae — connecting the domestic imagery of cooking and bathing to the Rosicrucian "
            "fraternity described as being 'seated at a golden table.' The purification is simultaneously "
            "medical (humoral rebalancing), chemical (distillation), and sacramental (baptismal cleansing)."
        )}

        <h3>Emblem XXXV — Digestion and Feeding</h3>
        {emblem_img(35, 'Emblem XXXV: As Ceres accustomed Triptolemus to endure fire')}
        {format_paragraphs(
            "Szulakowska discusses Maier's treatment of digestion as 'an indispensable stage in alchemical "
            "practice, comparable to the feeding of a young child and to agricultural processes.' Where "
            "wider Reformation culture treated bodily functions as taboo, the alchemists continued to regard "
            "digestion as a positive process, 'due to the very nature of their chemical process whose essential "
            "function was to change substance.'"
            "\\n\\n"
            "This rehabilitation of the body is, for Szulakowska, a specifically alchemical contribution to "
            "Reformation culture — a refusal to accept the Protestant separation of spirit and matter that "
            "was reshaping European attitudes toward the physical body."
        )}

        <h3>Emblem XL — The Two Fountains</h3>
        {emblem_img(40, 'Emblem XL: Make one water out of two waters')}
        {format_paragraphs(
            "Two streams merge into a single pool — the 'water of holiness.' Szulakowska identifies this as "
            "one of the 'slightly more overt references to the alchemical sacrament' in AF. Maier states "
            "that the elixir's meaning is 'analogous to the water of life of Christ, meaning by this both "
            "the sacrament of Baptism and also that of the Eucharist.'"
            "\\n\\n"
            "De Jong traced the source to the Lullian elixir tradition. Szulakowska adds the sacramental "
            "dimension: the two waters represent the two sacraments (Baptism and Eucharist) unified in the "
            "alchemical operation. This is as close as Maier comes to explicitly naming the Christian "
            "sacramental meaning that Szulakowska argues pervades the entire series."
        )}

        <h3>Emblem XLIV — Osiris Dismembered and Reassembled</h3>
        {emblem_img(44, 'Emblem XLIV: Typhon kills Osiris by a ruse')}
        {format_paragraphs(
            "Typhon murders Osiris and scatters his limbs; Isis gathers them. Szulakowska identifies the "
            "figure of Belinus — a late Hellenistic version of Osiris drawn from the Rosarium Philosophorum — "
            "as a Christ-figure. She quotes the text: 'when you have taken me partly out of my nature, and "
            "my wife out of hers and after you have killed these natures and we are raised by a new and "
            "incorporeal resurrection, so that after that we cannot die any more.'"
            "\\n\\n"
            "The language of 'incorporeal resurrection' maps directly onto Christian eschatology. Szulakowska "
            "argues that this is the most explicit Christological moment in the AF — the Egyptian myth of "
            "Osiris serving as a classical-mythological vehicle for what is essentially the death, "
            "dismemberment, and bodily resurrection of Christ."
        )}

        <h2>IV. The Alchemy of Light: Maier's Solar Geometry</h2>
        {format_paragraphs(
            "In her most technically detailed analysis of Maier, Szulakowska devotes Chapter 11 of The Alchemy "
            "of Light to 'Michael Maier's Alchemical Geometry of the Sun.' She begins by distinguishing "
            "Maier's courtly, classicizing style from Khunrath's pietistic intensity and Fludd's cosmological "
            "ambition. Maier's work 'emerges from the context of courtly humanism, rather than out of the "
            "academic discourses of the Protestant universities.' The Atalanta Fugiens, she argues, 'takes the "
            "form of a masque, with stage sets displaying scenes from classical mythology, accompanied by a "
            "musical score' — entertainment designed to instruct."
            "\\n\\n"
            "Szulakowska traces Maier's theoretical program to his treatise De Circulo Physico, Quadrato "
            "(1616), which she identifies as 'an account of the role of the sun in the making of potable "
            "gold.' Maier argued that gold's essential form is the circle — the Platonic form of eternal "
            "Being — and that the incorrupt nature of gold proves the circle 'is not an abstract mathematical "
            "concept, but a physical reality.' The static circle is nature perfected, manifesting as red, "
            "coagulated sulphur — that is, gold."
        )}

        <h3>Emblem XXI — The Geometric Formula</h3>
        {emblem_img(21, 'Emblem XXI: Make a circle out of a man and a woman')}
        {format_paragraphs(
            "Szulakowska connects the famous geometric diagram of Emblem XXI — circle, square, triangle, "
            "circle — to Maier's treatise on squaring the circle and to the Rosarium Philosophorum. The circle "
            "represents the primal matter (Chaos) and the perfected stone; the square symbolizes the four "
            "elements and the four seasons; the triangle represents the Paracelsian body, spirit, and soul "
            "(though Maier himself is not Paracelsian in method). The same geometric sequence appears in the "
            "seventh key of Basil Valentine's De Lapide Sapientum, which Maier published in his Tripus Aureus "
            "(1618)."
        )}

        <h3>Emblem VIII — The Theurgical Egg</h3>
        {emblem_img(8, 'Emblem VIII: Take the egg and pierce it with a fiery sword')}
        {format_paragraphs(
            "Szulakowska's most original reading concerns Emblem VIII, which she interprets through the lens "
            "of optical alchemy. The illustration shows an armed warrior (Mars) shattering the alchemical egg "
            "with a sword before a roaring fire. Behind him, a battlemented wall is pierced by 'a curious "
            "tunnel drawn in a diagrammatic form according to the rules of single-point perspective.' The "
            "tunnel's 'excessive depth does not correspond with the actual thickness of the wall' — it is "
            "not realistic architecture but, Szulakowska argues, a catoptrical diagram representing the "
            "concentration of solar rays."
            "\\n\\n"
            "Szulakowska connects this perspectival structure to the use of catoptrical mirrors (burning "
            "glasses) described by John Dee in the Propaedeumata Aphoristica and to Khunrath's optical "
            "imagery in the Amphitheatrum. She reads the tunnel as representing solar force being focused "
            "onto the alchemical egg — analogous to a burning glass concentrating sunlight. De Jong had "
            "compared the egg to Dee's macro-microcosmic egg in the Monas Hieroglyphica; Szulakowska extends "
            "this comparison to argue that the composition encodes an optical-alchemical program. This is "
            "a provocative reading that goes beyond what the image alone can confirm, but it usefully draws "
            "attention to the geometric and optical sophistication of Merian's engravings."
        )}

        <h3>The Fugues as Theurgical Talismans</h3>
        {format_paragraphs(
            "Szulakowska's most provocative argument concerns the fugues themselves. She proposes that "
            "Maier's Pythagorean musical score was intended to operate on the same astral-magical principles "
            "as Dee's and Khunrath's geometric sigils — that the musical ratios encoded correspondences with "
            "celestial forces. She argues that the fifth interval (diapente), whose ratio of 3:2 Ficino "
            "had identified with the proportional distance from earth to the sun, served as a musical "
            "signifier of solar virtue."
            "\\n\\n"
            "This interpretation — that the fugues function as something like astral-magical instruments — "
            "is characteristic of Szulakowska's willingness to push interpretive boundaries. It should be "
            "noted that Forshaw and other scholars in the new historiography of alchemy prefer to read AF "
            "as a work of alchemical synthesis rather than active theurgy, and Maier himself describes "
            "his emblems as 'chemical' rather than magical. Pamela H. Smith's framework of artisanal "
            "knowledge — where alchemy is understood as a sophisticated craft practice rather than either "
            "mysticism or modern chemistry — offers a more grounded interpretive model. Nonetheless, "
            "Szulakowska usefully draws attention to the Pythagorean mathematical structure of the fugues, "
            "which has not been adequately explored by other scholars, and to the broader context of "
            "Ficinian music theory within which Maier's compositions operated."
        )}

        <h2>V. Maier and the Rosarium Tradition</h2>
        {format_paragraphs(
            "In The Alchemical Virgin Mary, Szulakowska draws on De Jong's research to situate Maier's AF "
            "within the tradition of the Rosarium Philosophorum (Basel, 1550). She writes that De Jong 'has "
            "revealed' that Maier 'was basing himself substantially on the Rosarium (as well as on the Aurora "
            "Consurgens and the much older Turba Philosophorum)' — the same sources that contained Marian and "
            "Christological imagery that Maier transformed into his classicizing emblems."
            "\\n\\n"
            "The alchemical marriage in the Rosarium tradition involved an incestuous coupling of brother and "
            "sister (Sol and Luna), who then 'died' and putrefied — the same sequence Maier develops across "
            "multiple AF emblems (IV, XXX, XXXIII, XXXVIII). Szulakowska notes that this alchemical coniunctio "
            "drew on Marian theology through the Rosarium's mediation: the Virgin Mary as the vessel of "
            "transformation, the lac virginis as the volatile spirit that nourishes the philosophical embryo."
            "\\n\\n"
            "Szulakowska also identifies Adam McLean's observation that the Splendor Solis of Salomon Trismosin "
            "(1598) 'acts as a bridge between the Rosarium and the Rosicrucian period' — and argues that "
            "Maier's AF occupies the Rosicrucian end of this bridge, transforming the Rosarium's medieval "
            "Christian imagery into a classicized, humanist visual language while preserving its sacramental "
            "core."
        )}

        <h2>VI. Why Szulakowska Matters</h2>
        {format_paragraphs(
            "Szulakowska's contribution is unique because she reads the same images that De Jong analyzes "
            "source-critically and that Forshaw reads mytho-alchemically through a third lens: the religious "
            "politics of the Reformation. Her argument that Maier, Khunrath, and Fludd constituted an "
            "alchemical counter-church — performing a chemical Eucharist that usurped the Catholic sacramental "
            "monopoly — adds a political dimension that purely textual or symbolic readings miss."
            "\\n\\n"
            "Her most original contribution, from The Alchemy of Light, is her attention to the Pythagorean "
            "mathematical structure of both the geometric diagrams and the fugues. While her interpretation "
            "of these as astral-magical instruments goes further than most scholars in the field would "
            "endorse, she rightly identifies an underexplored dimension of the AF: the relationship between "
            "its mathematical structures (geometric, musical, arithmetical) and the alchemical content they "
            "accompany. This is territory that Forshaw's quadrivium analysis also addresses, from a more "
            "measured perspective."
            "\\n\\n"
            "Taken together, Szulakowska's three books reveal a Maier who is more politically and "
            "theologically engaged than either De Jong's source-critical method or Tilton's Rosicrucian "
            "framing alone suggest. Read alongside Smith's artisanal-knowledge framework and Forshaw's "
            "mytho-alchemical analysis, Szulakowska's religious-political lens adds a dimension that enriches "
            "without displacing these other approaches. The classical surface of the Atalanta Fugiens, in her "
            "reading, conceals not merely chemical knowledge in allegorical form but a sacramental theology "
            "and a political program — registers that become visible only when the images are read against "
            "the full backdrop of Reformation religious controversy."
        )}
    </div>"""

    html = page_shell('Szulakowska on Maier', body, active_nav='Szulakowska')
    (SITE_DIR / 'szulakowska.html').write_text(html, encoding='utf-8')
    print("  szulakowska.html")


def build_essay_pages(conn):
    """Build essay pages. Enriched content from staging/ overrides inline defaults."""
    essays_dir = SITE_DIR / 'essays'
    essays_dir.mkdir(exist_ok=True)

    # Load enriched content from staging if available
    enriched_path = BASE_DIR / 'staging' / 'enriched_essays.json'
    enriched = {}
    if enriched_path.exists():
        enriched = json.loads(enriched_path.read_text(encoding='utf-8'))

    ESSAYS = [
        {
            "slug": "music",
            "title": "Approaches to Music in Maier's Atalanta Fugiens",
            "subtitle": "How Scholars Have Understood the Fifty Fugues",
            "body": (
                "<p>The fifty three-voice fugues of <em>Atalanta Fugiens</em> constitute the most distinctive "
                "feature of Maier's emblem book — no other work in the alchemical or emblematic tradition "
                "integrates bespoke musical compositions into every emblem. Yet for centuries, these fugues "
                "were treated as curiosities rather than objects of serious musical analysis. The modern "
                "scholarly engagement with Maier's music begins with Joscelyn Godwin's 1987 edition and has "
                "since developed along several distinct interpretive lines: musicological, performative, "
                "therapeutic, and cosmological.</p>"

                "<h3>Godwin: The First Modern Edition (1987)</h3>"
                "<p>Joscelyn Godwin's edition of the Atalanta Fugiens, published by Adam McLean's Magnum Opus "
                "Hermetic Sourceworks in 1987 (reprinted by Phanes Press, 1989), included the first modern "
                "transcription of all fifty fugues into standard musical notation and the first complete "
                "recording, performed by Rachel Platt, Emily Van Evera, Rufus Muller, and Richard Wistreich. "
                "The introductory essay by Hildemarie Streich analyzed the musical structure, concluding "
                "that the three voice-parts represent the three mythic characters — Atalanta (soprano), "
                "Hippomenes (tenor), and the golden apple (cantus firmus) — and that the compositions should "
                "be understood as conceptual art-works rather than practical performance scores. Streich "
                "noted that the apple voice wanders from higher to lower pitch, as if describing the process "
                "of distillation, and that the fugues employ mirror canons (canon by inversion) between "
                "Atalanta and Hippomenes. A later Spanish edition, <em>La Fuga de Atalanta</em>, was published "
                "by Ediciones Atalanta in 2007.</p>"

                "<h3>Leedy: Musicological Assessment (1991)</h3>"
                "<p>Douglas Leedy's review in <em>Notes</em> (1991) provided the first sustained musicological "
                "evaluation of the fugues as compositions. Leedy, a specialist in early music and alternative "
                "tuning systems, characterized the Atalanta Fugiens as a <em>Gesamtkunstwerk</em> — a total "
                "artwork integrating visual, textual, and auditory elements. He praised the recording but "
                "criticized the quality of the emblem reproductions. Most significantly, Leedy identified the "
                "fugues as musically sophisticated works comparable to Machaut, Gesualdo, and Stravinsky in "
                "their handling of dissonance. He challenged the dismissive view, common in both musicological "
                "and alchemical scholarship, that the canons were crude or amateurish.</p>"

                "<h3>Wescott: Planetary-Modal Correspondences (n.d.)</h3>"
                "<p>Catherine Morris Wescott's analysis in the <em>AthanorX</em> journal represents the most "
                "technically detailed examination of the fugues' modal structure. She demonstrates that Maier's "
                "modal choices — Dorian, Phrygian, Mixolydian, and others — correspond to planetary associations "
                "established in classical and medieval music theory: Saturn governs the Mixolydian mode, Mars "
                "the Phrygian, Jupiter the Lydian, and so on. These planetary correspondences in turn relate "
                "to the alchemical stages depicted in each emblem's plate. Wescott identifies the cantus firmus "
                "as the structural anchor derived from the liturgical chant tradition — specifically the "
                "<em>Christe eleison</em> from Mass IV, as identified by Sleeper (1938). Her analysis of "
                "Emblems XXIV, XXVIII, XXXI, and XLIV reveals how chromatic text-painting in the musical lines "
                "mirrors the allegorical action described in the mottos, and argues that music, image, and "
                "text form a unified signification system in which each medium reinforces the others.</p>"

                "<h3>Hasler: The Performative Argument (2011)</h3>"
                "<p>Johann F.W. Hasler's article argues that the Atalanta Fugiens 'requires a performative "
                "attitude and activity (in the form of singing) and not merely to be read, for its original "
                "purpose to be fully accomplished.' Hasler identifies the work as a genuine precursor to modern "
                "multimedia — not merely a book with illustrations and music attached, but an integrated "
                "multi-sensory experience designed for simultaneous engagement of sight, sound, and intellect. "
                "He connects the AF to the tradition of <em>Gesprachspiele</em> (conversation games) and to "
                "the <em>Balet comique de la Reine</em> (1581) as a courtly performance context. Hasler also "
                "notes that Godwin regarded the fugues as 'conceptual art-works' rather than practical scores, "
                "but argues that the performative dimension — the act of singing — was essential to the "
                "meditative function Maier intended.</p>"

                "<h3>Long: Music as Therapy (2012)</h3>"
                "<p>Kathleen Perry Long's article in <em>Lo Sguardo</em> brings neuroscientific perspectives "
                "on music therapy into dialogue with Maier's alchemical program. She argues that Maier's "
                "integration of music was not merely decorative but therapeutically intentional, drawing on "
                "Marsilio Ficino's theory of music as a vehicle for healing melancholy. Long connects the AF's "
                "meditative program — 'to be looked at, read, meditated, understood, weighed, sung and "
                "listened to' — to the systematized prayer and visualization practices developed by Ignatius "
                "of Loyola and other Counter-Reformation spiritual directors. She proposes that Maier may have "
                "hoped to address social and political ills through musical-meditative practices, situating the "
                "AF within the context of the political upheaval and widespread war of the early seventeenth "
                "century. Her framework of embodied cognition — drawing on Antonio Damasio's work on somatic "
                "markers — suggests that the AF's multi-sensory design engages pre-rational bodily knowing as "
                "well as intellectual understanding.</p>"

                "<h3>Forshaw: The Quadrivium and Mytho-Alchemy (2012, 2020)</h3>"
                "<p>Peter Forshaw reveals that Maier structures each emblem's discourse around the four "
                "disciplines of the medieval quadrivium: arithmetic, music, geometry, and astronomy. The music "
                "is thus not an addition to the emblem but one of four parallel mathematical encodings of the "
                "alchemical concept — each emblem is mapped arithmetically (as the root of the cube), musically "
                "(as the disdiapason or double octave), geometrically (as a generative point on a flowing "
                "line), and astronomically (as the center of Saturn, Jupiter, and Mars). This systematic "
                "mapping has not been fully explored by other scholars. Forshaw also identifies John Farmer's "
                "1591 collection as the source for forty of the fifty fugues — a discovery made by Maximilian "
                "Ludwig and published in the Furnace and Fugue edition — which raises questions about Maier's "
                "role as composer versus arranger.</p>"

                "<h3>Szulakowska: Pythagorean Ratios and Astral Correspondences (2000)</h3>"
                "<p>Urszula Szulakowska, in <em>The Alchemy of Light</em>, proposes the most provocative "
                "interpretation of the fugues. She argues that Maier's Pythagorean musical score encoded "
                "correspondences with celestial forces, noting that the fifth interval (diapente), whose ratio "
                "of 3:2 Ficino had identified with the proportional distance from earth to the sun, served as "
                "a musical signifier of solar virtue. This interpretation — that the fugues function as "
                "instruments of astral correspondence — goes further than most scholars in the field would "
                "endorse. Forshaw and others in the new historiography of alchemy prefer to read the AF as a "
                "work of alchemical synthesis rather than active theurgy, and Maier himself describes his "
                "emblems as 'chemical' rather than magical. Nonetheless, Szulakowska usefully draws attention "
                "to the Pythagorean mathematical structure of the fugues and to the broader context of "
                "Ficinian music theory within which Maier's compositions operated.</p>"

                "<h3>Furnace and Fugue: Digital Performances (2020)</h3>"
                "<p>The Furnace and Fugue digital edition includes newly commissioned vocal recordings of all "
                "fifty fugues, allowing users to experience the music synchronized with the emblem images and "
                "texts for the first time in a digital environment. The edition's MEI (Music Encoding "
                "Initiative) player includes a piano-roll visualization that allows users without musical "
                "training to see the contrapuntal structure of the fugues in real time — a technological "
                "realization of the multi-sensory engagement Maier intended. Maximilian Ludwig's discovery "
                "that forty of the fifty fugues are based on compositions by the Elizabethan composer John "
                "Farmer (published in <em>Divers and Sundry Waies</em>, 1591) transformed understanding of "
                "Maier's compositional method: he was primarily an arranger and adapter, selecting pre-existing "
                "musical material and fitting it to his alchemical program, rather than composing original "
                "music from scratch.</p>"

                "<h3>The Question of Performance Practice</h3>"
                "<p>Nothing is known about Maier's ideas on how the fugues were to be performed in practice. "
                "The subtitle of the Atalanta Fugiens promises compositions 'suitable for singing in couplets, "
                "to be looked at, read, meditated on, understood, weighed, sung and listened to, not without "
                "a certain pleasure.' Since Maier served as counsellor to Rudolf II, it is possible that the "
                "music was performed at the imperial court. The 2006 performance by the early music ensemble "
                "Arcanum at the International Conference on the History of Alchemy in Philadelphia, the "
                "ongoing lecture-performances by Les Canards Chantants (from 2014, in collaboration with Donna "
                "Bilak and Tara Nummedal), and the 2011 complete recording by Ensemble Plus Ultra under "
                "Michael Noone represent the principal modern attempts to realize Maier's musical vision. "
                "Whether the fugues were intended for actual performance, private meditation, or — as "
                "Szulakowska suggests — astral-magical operation, they remain the least understood and most "
                "intriguing dimension of the Atalanta Fugiens.</p>"
            ),
        },
        {
            "slug": "social-world",
            "title": "Maier's Social World",
            "subtitle": "Courts, Patrons, Associates, and Alchemical Movements",
            "body": (
                "<p>Michael Maier moved through some of the most intellectually charged environments in early "
                "seventeenth-century Europe. His career traces an arc from the Baltic provinces through the "
                "imperial court in Prague, the royal court in London, the Landgrave's household in Hessen-Kassel, "
                "and the war-threatened cities of northern Germany — each stop adding new connections, patrons, "
                "and intellectual influences to the network within which the Atalanta Fugiens was conceived.</p>"

                "<h3>The Court of Rudolf II (1608-1611)</h3>"
                "<p>Rudolf II's court in Prague was the most important center of alchemical patronage in early "
                "modern Europe. As Tilton emphasizes, the court represented a rare space of intellectual tolerance "
                "where Protestant and Catholic humanists formed a single cosmopolitan body of scholars. Maier "
                "arrived around mid-1608, presenting himself with his claimed Universal Medicine at the Hradcany "
                "Palace. After a year of navigating courtly obstruction, he entered Rudolf's service on 19 "
                "September 1609 and was elevated to the nobility ten days later with three titles: Personal "
                "Physician, Count Palatine, and Knight Exemptus. As Godwin reveals, this ennoblement came "
                "without land or income, leaving Maier in 'the uncomfortable condition of an unlanded nobleman' "
                "— barred from modest employment yet having no property. Rudolf's court also hosted Tycho Brahe, "
                "Johannes Kepler, and the alchemist Sir Edward Kelley, creating an environment where astronomical "
                "observation, chemical experiment, and Hermetic philosophy intersected.</p>"

                "<h3>England and the Hermetic Circle (1611-1616)</h3>"
                "<p>After Rudolf's forced abdication (April 1611) and death (January 1612), Maier went to "
                "England, arriving before Christmas 1611. His Christmas greeting to James I — a folded parchment "
                "with a Rose-Cross emblem in gold and red, four Latin poems, and a six-part musical canon — is "
                "the earliest known appearance of the Rose-Cross symbol in England. Godwin argues that Maier's "
                "five-year English presence was 'almost certainly the fulfilment of a diplomatic mission' "
                "preparing the ground for the Frederick-Elizabeth dynastic marriage (1613). In London, Maier "
                "frequented the circle of Hermetic physicians close to the court, including Sir William Paddy, "
                "James I's personal physician and a close friend of Robert Fludd. Both Maier and Fludd employed "
                "the same engraver, Matthaeus Merian, and both published with Johann Theodore de Bry, but no "
                "direct evidence of their meeting survives. The English alchemist Francis Anthony, author of "
                "<em>Aurum Potabile</em>, was another associate; Maier dedicated his <em>Lusus Serius</em> (1616) "
                "partly to Anthony. During his English years, Maier also translated Thomas Norton's <em>Ordinal "
                "of Alchemy</em> into Latin, connecting himself to the English alchemical tradition.</p>"

                "<h3>Moritz of Hessen-Kassel (1616-1620)</h3>"
                "<p>After returning to Germany in mid-1616, Maier published eleven books in two years from "
                "Frankfurt, dedicating them to Hermetically-inclined Protestant rulers. He joined the court of "
                "Moritz von Hessen-Kassel, 'the foremost patron of alchemy in the German states,' as Forshaw "
                "describes him. Moritz was also the patron of Johannes Hartmann, the first-ever professor of "
                "chemical medicine at the University of Marburg (appointed 1609). In 1618, Moritz rewarded Maier "
                "with the title <em>Medicus und Chymicus von Haus aus</em> (Original Physician and Alchemist). "
                "But the political catastrophe of the Thirty Years' War — the Battle of the White Mountain "
                "(1620), the collapse of the Protestant cause — destroyed Moritz's ability to support scholarly "
                "pursuits, and Maier was forced north.</p>"

                "<h3>Maier and Paracelsianism</h3>"
                "<p>Forshaw is emphatic: 'Michael Maier is not Paracelsian.' The AF works exclusively with the "
                "Mercury-Sulphur dyad — the medieval alchemical theory — without Paracelsus's third principle "
                "(Salt). Maier praised Paracelsus's chemical medicines as effective cures but condemned him "
                "as 'a rogue and overly cynical.' He also preferred the term 'chemical' over 'alchemical' — a "
                "terminological distinction that Forshaw identifies as significant for the early seventeenth "
                "century when the two terms were becoming differentiated. At the same time, Maier operated "
                "within Paracelsian networks: Moritz's court was a center of Paracelsian iatrochemistry, and "
                "Maier's interest in potable gold connects him to the Paracelsian pharmaceutical tradition "
                "even as his theoretical framework remains Aristotelian.</p>"

                "<h3>Maier and the Rosicrucians</h3>"
                "<p>The publication of the Fama Fraternitatis (1614) and Confessio Fraternitatis (1615) during "
                "Maier's English sojourn intersected with his developing alchemical project. As Tilton argues, "
                "Maier did not merely sympathize with Rosicrucianism but sought to define it on his own terms "
                "through works like <em>Silentium post Clamores</em> and <em>Themis Aurea</em>, systematically "
                "distinguishing genuine natural philosophy from imposture. Godwin observes that Maier conceived "
                "of a <em>philosophia perennis</em> — a perennial philosophy transmitted through twelve mystery "
                "schools appearing in twelve nations, from Hermes Trismegistus in Egypt to the Rosicrucian "
                "Brotherhood in modern Germany. The Atalanta Fugiens can be understood as this tradition's "
                "visual and musical curriculum: fifty alchemical lessons encoding the wisdom of all twelve "
                "schools. Maier never claimed membership in the Brotherhood but left 'his readers in no doubt "
                "of his sympathy with Rosicrucian principles and aspirations.'</p>"

                "<h3>Final Years (1620-1622)</h3>"
                "<p>Maier spent his last years in Magdeburg, seeking patronage from Markgraf Christian Wilhelm "
                "von Brandenburg and petitioning Herzog Friedrich III von Schleswig-Holstein-Gottorf to return "
                "to his Baltic homeland. His final book, <em>Ulysses</em> (published posthumously 1624), "
                "treats 'how to recover from the shipwreck of bodily goods and fortune through the virtues of "
                "the intellect' — a valedictory note of Christian Stoicism. Maier died in Magdeburg in the late "
                "summer of 1622, aged approximately 53. As Tilton frames it, his death came as the Rosicrucian "
                "hopes and Calvinist political ambitions that had nourished his work collapsed into continental "
                "conflict. His travels had taken him from Kiel to Padua, Prague, London, Frankfurt, Kassel, "
                "and Magdeburg — almost full circle.</p>"
            ),
        },
        {
            "slug": "jung",
            "title": "Maier According to Jung",
            "subtitle": "Psychological Alchemy and Its Critics",
            "body": (
                "<p>Carl Gustav Jung's engagement with Michael Maier's Atalanta Fugiens in <em>Psychology and "
                "Alchemy</em> (1944) and subsequent works transformed the reception of alchemical imagery in "
                "the twentieth century — and provoked a counter-reaction from historians of science that "
                "continues to shape Maier scholarship today. Understanding this debate is essential for "
                "situating the Atalanta Fugiens within the broader historiography of alchemy.</p>"

                "<h3>Jung's Reading</h3>"
                "<p>Jung reproduced and analyzed numerous Atalanta Fugiens plates in <em>Psychology and "
                "Alchemy</em>, reading them as expressions of the individuation process — the psychological "
                "journey toward wholeness that Jung identified as the central goal of both alchemy and "
                "psychotherapy. The coniunctio of Sol and Luna became the integration of conscious and "
                "unconscious; the nigredo became the confrontation with the shadow; the philosopher's stone "
                "became the Self. Jung treated the alchemists not as proto-chemists or mystical dreamers but "
                "as pioneers of depth psychology who had projected their inner transformations onto the "
                "behavior of matter in the flask. The AF's imagery — hermaphrodites, devouring wolves, kings "
                "in steam baths, dragons locked in combat with women — provided Jung with a visual vocabulary "
                "for psychological processes that he argued were universal and archetypal.</p>"

                "<h3>The Newman-Principe Critique</h3>"
                "<p>The Jungian reading of alchemy was challenged most forcefully by William R. Newman and "
                "Lawrence Principe in a series of publications from the 1990s onward. They argued that Jung "
                "had fundamentally misunderstood alchemy by treating it as symbolic psychology rather than as "
                "a genuine natural-philosophical practice with real laboratory operations. Newman and Principe "
                "demonstrated that many alchemical texts that Jung read as psychological allegories were in "
                "fact descriptions of reproducible chemical procedures — the 'green lion' was not a Jungian "
                "archetype but a specific mineral acid, the 'wolf devouring the king' was not a myth of "
                "ego-death but a description of antimony purifying gold. Their program of 'chymistry' — a "
                "term they introduced to avoid the anachronistic split between 'alchemy' and 'chemistry' — "
                "insisted on reading alchemical texts within their original technical and intellectual context "
                "rather than as timeless expressions of the collective unconscious.</p>"

                "<h3>Tilton's Mediation</h3>"
                "<p>Hereward Tilton's <em>The Quest for the Phoenix</em> (2003) represents the most "
                "sophisticated attempt to navigate between the Jungian and Newman-Principe positions in "
                "relation to Maier specifically. Tilton explicitly critiques Jung's interpretation of alchemy "
                "while acknowledging that a purely laboratory-reductive reading is equally inadequate for "
                "understanding Maier. He argues for a 'spiritual alchemy' grounded not in Jungian psychology "
                "but in the Aristotelian elemental philosophy and the <em>prisca sapientia</em> tradition that "
                "Maier himself invoked. In Tilton's reading, Maier perceived his own life journey as mirroring "
                "the stages of the alchemical Great Work — not because he was unconsciously projecting (as Jung "
                "would have it) but because he consciously understood the alchemical process as a model for "
                "both material transformation and personal-spiritual development. The phoenix motif in Maier's "
                "final works represents this deliberate parallelism: the alchemist's quest for the stone and "
                "the individual's quest for wisdom are recognized as structurally identical without being "
                "reduced to either mere chemistry or mere psychology.</p>"

                "<h3>Forshaw and Smith: The New Historiography</h3>"
                "<p>The current consensus among historians of alchemy — represented by scholars like Peter "
                "Forshaw and Pamela H. Smith — largely follows the Newman-Principe critique of Jungian readings "
                "while acknowledging the multi-dimensional character of alchemical practice that Tilton "
                "identifies. Forshaw's characterization of Maier as practicing 'mytho-alchemy' — the reading "
                "of classical myths as encoded chemical knowledge — avoids both the Jungian projection model "
                "and the reductive laboratory model. Maier, in Forshaw's reading, is neither a proto-Jungian "
                "nor a disguised bench chemist but a humanist scholar who believed that the myths of antiquity "
                "contained genuine natural-philosophical truths, accessible to those who knew the allegorical "
                "code. Smith's framework of artisanal knowledge — where alchemy is understood as a sophisticated "
                "craft practice rather than either mysticism or modern chemistry — provides the most grounded "
                "context for understanding what the Atalanta Fugiens actually is: a work of alchemical synthesis "
                "that brings together inherited textual traditions, visual allegory, musical composition, and "
                "natural philosophy into a multi-sensory pedagogical program.</p>"

                "<h3>Why This Debate Matters</h3>"
                "<p>The Jung debate matters for this site because it determines how we read every emblem. If "
                "the wolf devouring the king (Emblem XXIV) is a Jungian archetype, it means one thing; if it "
                "is a description of antimony refining (as Principe demonstrates), it means another; if it is "
                "a mytho-alchemical allegory encoding chemical knowledge in classical narrative form (as "
                "Forshaw and De Jong argue), it means something richer than either reduction alone. The approach "
                "taken on this site follows De Jong's source-critical method as primary, enriched by Forshaw's "
                "mytho-alchemical framing, Tilton's spiritual-alchemy contextualization, and Smith's artisanal-"
                "knowledge perspective — while acknowledging that Jung's popularization of alchemical imagery "
                "did more than any other single factor to bring the Atalanta Fugiens to modern attention.</p>"
            ),
        },
    ]

    # Append additional essays to the list before building
    ESSAYS.append({
        "slug": "chemistry",
        "title": "The Chemistry, Medicine, and Alchemical Theories of the Emblems",
        "subtitle": "What Maier Encoded in Fifty Allegorical Scenes",
        "body": "<p>See the enriched version for full content.</p>",
    })
    ESSAYS.append({
        "slug": "dejong-sources",
        "title": "Maier's Sources According to De Jong",
        "subtitle": "How One Scholar Unlocked Fifty Alchemical Emblems",
        "body": "<p>See the enriched version for full content.</p>",
    })
    ESSAYS.append({
        "slug": "paracelsianism",
        "title": "Maier, Paracelsianism, and Chemical Medicine",
        "subtitle": "An Aristotelian Among the Paracelsians",
        "body": "<p>See the enriched version for full content.</p>",
    })
    ESSAYS.append({
        "slug": "playful-reading",
        "title": "Playful Reading in Atalanta Fugiens",
        "subtitle": "The Lusus Serius and Renaissance Pedagogy of Play",
        "body": "<p>See the enriched version for full content.</p>",
    })

    # Build individual essay pages (enriched content overrides inline defaults)
    for essay in ESSAYS:
        essay_body = enriched.get(essay['slug'], essay['body'])
        # For chemistry essay: inject emblem images after each <h3 id="emblem-N"> header
        if essay['slug'] == 'chemistry':
            import re
            def inject_emblem_img(m):
                num = int(m.group(1))
                fname = f'emblem-{num:02d}.jpg'
                link = f'../emblems/emblem-{num:02d}.html' if num > 0 else '../emblems/frontispiece.html'
                return m.group(0) + f'<figure style="float:right;margin:0 0 1rem 1.5rem;max-width:250px"><a href="{link}"><img src="../images/emblems/{fname}" alt="Emblem {num}" style="width:100%;border-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,0.12)"></a></figure>'
            essay_body = re.sub(r'<h3 id="emblem-(\d+)">[^<]+</h3>', inject_emblem_img, essay_body)
        body_html = f"""
        <div class="page-content">
            <a href="index.html" class="back-link">&larr; Essays</a>
            <h1 style="font-size:1.8rem;margin-bottom:0.3rem">{essay['title']}</h1>
            <p style="font-size:1.1rem;color:var(--text-muted);margin-bottom:1.5rem;font-style:italic">{essay['subtitle']}</p>

            <div style="font-size:0.95rem;line-height:1.8;margin-top:1.5rem">{essay_body}</div>
        </div>"""
        html = page_shell(essay['title'], body_html, active_nav='Essays', depth=1)
        (essays_dir / f'{essay["slug"]}.html').write_text(html, encoding='utf-8')

    # Build essays index
    cards = ''
    for essay in ESSAYS:
        cards += f"""
        <a href="{essay['slug']}.html" class="card" style="text-decoration:none;color:inherit">
            <div class="card-body">
                <div class="card-sig">{essay['title']}</div>
                <div class="card-desc">{essay['subtitle']}</div>
                <div style="margin-top:0.5rem"><span style="font-size:0.8rem;color:var(--accent);font-family:var(--font-sans)">Read essay &rarr;</span></div>
            </div>
        </a>"""

    # Dead inline Paracelsianism code removed — enriched version lives in staging/enriched_essays.json
    # Add planned essays too (none currently — all moved to ESSAYS list above)
    planned = [
    ]
    for title, desc in planned:
        cards += f"""
        <div class="card" style="cursor:default">
            <div class="card-body">
                <div class="card-sig">{title}</div>
                <div class="card-desc">{desc}</div>
                <div style="margin-top:0.5rem"><span class="review-badge">COMING SOON</span></div>
            </div>
        </div>"""

    idx_body = f"""
    <div class="page-content">
        <h2>Essays</h2>
        <p>AI-drafted essays synthesizing our corpus of scholarship on <em>Atalanta Fugiens</em>.</p>
        <div class="gallery" style="grid-template-columns:repeat(auto-fill, minmax(300px, 1fr));gap:1rem;padding:1rem 0">
            {cards}
        </div>
    </div>"""
    html = page_shell('Essays', idx_body, active_nav='Essays', depth=1)
    (essays_dir / 'index.html').write_text(html, encoding='utf-8')
    print(f"  essays/: {len(ESSAYS)} essays + {len(planned)} planned")


def build_modern_scholarship(conn):
    """Build 21st-century Maier studies showcase page."""

    body = """
    <div class="page-content">
        <h1 style="font-size:1.8rem;margin-bottom:0.3rem">Maier Studies in the 21st Century</h1>
        <p style="font-size:1.05rem;color:var(--text-muted);margin-bottom:1.5rem;font-style:italic">
            How a Renaissance Alchemist Became a Subject of Digital Humanities
        </p>


        <h2>A Renaissance in Maier Scholarship</h2>
        <p>For three centuries after his death in 1622, Michael Maier was known primarily to collectors of alchemical
        curiosities and to occultist readers who mined his emblems for esoteric symbolism. The modern scholarly recovery
        began with Craven's 1910 biography and De Jong's transformative 1969 monograph, but it was the twenty-first
        century that saw Maier scholarship explode into a genuinely interdisciplinary field. Since 2000, the Atalanta
        Fugiens has been the subject of at least twenty major scholarly publications spanning art history, musicology,
        history of science, digital humanities, religious studies, and literary criticism. The work has been performed
        in concert halls, analyzed by neuroscientists, re-encoded in digital formats, and read through lenses that
        Maier — and De Jong — could never have imagined.</p>

        <h2>The Tilton Revolution (2003)</h2>
        <p>Hereward Tilton's <em>The Quest for the Phoenix</em> (Walter de Gruyter, 2003) was the first full-length
        study of Maier since De Jong. Where De Jong had focused narrowly on the textual sources of the Atalanta Fugiens,
        Tilton placed Maier's entire bibliography of twenty-five published works within the broader context of
        Rosicrucianism, spiritual alchemy, and Habsburg court politics. Tilton corrected Maier's birth year from
        1568 to 1569, revealed his claim to have produced the Universal Medicine, traced the reception of his work
        through the Gold- und Rosenkreutz order to Jung, and proposed a nuanced "spiritual alchemy" that challenged
        both Jungian and laboratory-reductive readings. His monograph opened the door to the interdisciplinary
        approaches that followed.</p>

        <h2>New Dimensions: Music, Medicine, Multimedia (2011-2012)</h2>
        <p>Three publications in 2011-2012 opened entirely new dimensions of AF scholarship. Johann F.W. Hasler argued
        that the work is a genuine precursor to modern multimedia, requiring performative engagement (singing) for
        its original purpose to be accomplished. Kathleen Perry Long connected the fugues to Ficinian music therapy
        and contemporary neuroscience, proposing that Maier intended his musical program as a therapeutic intervention
        against melancholy and political disorder. And Peter Forshaw's Infinite Fire webinar for the Ritman Library
        introduced the concept of "mytho-alchemy" and revealed the quadrivium structure of each discourse — a
        systematic mapping of alchemical concepts across arithmetic, music, geometry, and astronomy that no previous
        scholar had identified.</p>

        <h2>The Religious-Political Turn: Szulakowska (2000-2011)</h2>
        <p>Urszula Szulakowska's three monographs — <em>The Alchemy of Light</em> (2000), <em>The Sacrificial Body</em>
        (2006), and <em>The Alchemical Virgin Mary</em> (2011) — added a dimension absent from both De Jong and
        Tilton: the religious politics of alchemical illustration. Szulakowska argued that Maier, Khunrath, and Fludd
        regarded their chemical procedures as essentially the same rite as the Catholic mass, and that Maier's
        classical mythological surface concealed a fundamentally Eucharistic understanding of alchemical transformation.
        Her analysis of the Pythagorean structure of the fugues and the optical geometry of Emblem VIII pushed
        interpretive boundaries, while her identification of the "Turkish Madonna" tradition in the Symbola Aureae
        Mensae connected Maier's imagery to Habsburg court politics and the Ottoman wars.</p>

        <h2>The Digital Turn: Furnace and Fugue (2020)</h2>
        <p>The most ambitious twenty-first-century engagement with the Atalanta Fugiens is Donna Bilak and Tara
        Nummedal's <em>Furnace and Fugue</em> (University of Virginia Press, 2020), the first born-digital scholarly
        edition. Built through Brown University's Digital Publications Initiative with Mellon Foundation support, the
        interactive edition allows users to hear, see, manipulate, and investigate the Atalanta Fugiens in ways that
        Maier imagined but that were technically impossible before digital publication. The MEI music player with
        piano-roll visualization lets users without musical training see the contrapuntal structure of the fugues
        in real time. The edition won the 2022 Roy Rosenzweig Prize for Creativity in Digital History from the
        American Historical Association.</p>
        <p>Bilak's own contribution — her steganography thesis proposing that the fifty emblems conceal a magic square
        — represents the most radical structural claim about the Atalanta Fugiens since De Jong's source identifications.
        Maximilian Ludwig's discovery that forty of the fifty fugues derive from compositions by the Elizabethan
        composer John Farmer (published in <em>Divers and Sundry Waies</em>, 1591) transformed understanding of
        Maier's compositional method: he was primarily an arranger and adapter, not an original composer. Peter
        Forshaw's essay on mytho-alchemy defined a new scholarly category for understanding Maier's method.</p>

        <h2>Performance and Recording (2006-2021)</h2>
        <p>The twenty-first century also saw the Atalanta Fugiens move from the page to the stage. The 2006 performance
        by the early music ensemble Arcanum at the International Conference on the History of Alchemy in Philadelphia
        initiated a tradition of live AF performances at scholarly gatherings. Les Canards Chantants have performed
        and workshopped the fugues regularly since 2014, in collaboration with Bilak and Nummedal, exploring the
        relationship between singing, seeing, and alchemical meditation. Ensemble Plus Ultra's 2011 recording for
        Claudio Records — the first commercial complete-cycle recording — made all fifty fugues available on streaming
        platforms. And the RIM c-Orchestra's 2021 electronic reimagining on Bandcamp extended the musical afterlife
        of Maier's compositions into contemporary electronic music.</p>

        <h2>Emerging Directions</h2>
        <p>The most recent scholarship suggests several emerging directions. Amber Rozenrichter's 2024 SHAC conference
        paper on "hidden dryads" in the AF emblems opens a feminist iconographic approach, arguing that concealed
        feminine figures serve as guiding forces for the alchemist. Sarah Lang's computational approaches at the
        University of Graz point toward digital methods for analyzing the structural patterns of emblem sequences.
        Paul Miner's 2012 study of Blake's visual borrowings from Maier demonstrates the reception-history approach,
        tracing the influence of the AF plates across two centuries of English art. And the continued availability
        of the work through Adam McLean's Alchemy Website (founded 1995, with hand-coloured plates from 1999) and
        the Furnace and Fugue digital edition ensures that Maier's multi-sensory masterpiece is more accessible
        to a global audience than at any point in its four-hundred-year history.</p>

        <h2>What We Now Know</h2>
        <p>Twenty-first-century scholarship has established several facts and frameworks that were unavailable to
        earlier generations of readers:</p>
        <ul style="font-size:0.95rem;line-height:1.7;margin-bottom:1.5rem">
            <li><strong>Biography</strong>: Maier was born in Kiel in 1569 (not 1568), his father was a gold embroiderer,
            he claimed to have produced the Universal Medicine of "bright lemon color," he was left an unlanded nobleman
            by Rudolf II, and his English sojourn was likely a diplomatic mission (Tilton, Godwin, Figala-Neumann)</li>
            <li><strong>Sources</strong>: The Artis Auriferae was Maier's primary reference anthology; 40 of 50 fugues
            derive from John Farmer's 1591 collection; the Rosarium Philosophorum provided the structural model
            (De Jong, Ludwig, Forshaw)</li>
            <li><strong>Method</strong>: Maier practiced "mytho-alchemy" — reading classical myths as encoded chemical
            knowledge — and structured each discourse around the four disciplines of the quadrivium (Forshaw)</li>
            <li><strong>Music</strong>: The fugues' modal choices correspond to planetary-alchemical associations, with
            the cantus firmus derived from the Christe eleison of Mass IV (Wescott, Leedy, Sleeper)</li>
            <li><strong>Politics</strong>: The AF conceals sacramental theology beneath its classical surface, and
            Maier's imagery connects to Reformation Eucharistic controversy (Szulakowska)</li>
            <li><strong>Reception</strong>: Blake borrowed visually from the AF plates; the AF influenced alchemical
            illustration for three centuries; and Jung's psychological reading was itself a form of alchemical
            practice, not scientific analysis (Miner, Szulakowska, Tilton)</li>
        </ul>
    </div>"""

    html = page_shell('Maier Studies in the 21st Century', body, active_nav='21st Century')
    (SITE_DIR / 'modern-scholarship.html').write_text(html, encoding='utf-8')
    print("  modern-scholarship.html")


def build_creatures_page():
    """Build the Creatures page — Maier's alchemical bestiary with essays on each creature."""
    creatures_path = BASE_DIR / 'staging' / 'creatures_essays.json'
    if not creatures_path.exists():
        print("  creatures.html: skipped (no staging/creatures_essays.json)")
        return

    creatures = json.loads(creatures_path.read_text(encoding='utf-8'))

    entries_html = ''
    for c in creatures:
        slug = c.get('slug', '')
        title = c.get('title', '')
        subtitle = c.get('subtitle', '')
        body = c.get('body_html', '')
        emblem_nums = c.get('emblems', [])

        # Emblem image badges
        # Build emblem illustration panel — large images alongside text
        emblem_figures = ''
        for n in emblem_nums[:3]:
            fname = f'emblem-{n:02d}.jpg'
            link = f'emblems/emblem-{n:02d}.html'
            roman = ['F','I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX','XXI','XXII','XXIII','XXIV','XXV','XXVI','XXVII','XXVIII','XXIX','XXX','XXXI','XXXII','XXXIII','XXXIV','XXXV','XXXVI','XXXVII','XXXVIII','XXXIX','XL','XLI','XLII','XLIII','XLIV','XLV','XLVI','XLVII','XLVIII','XLIX','L'][n]
            emblem_figures += f'''<figure style="margin:0 0 1rem 0;max-width:300px">
                <a href="{link}"><img src="images/emblems/{fname}" alt="Emblem {roman}" style="width:100%;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.15)"></a>
                <figcaption style="font-size:0.8rem;color:var(--text-muted);text-align:center;margin-top:0.3rem">Emblem {roman} &middot; <a href="{link}" style="color:var(--accent)">View full analysis</a></figcaption>
            </figure>'''

        if emblem_figures:
            # Grid layout: images left, text right
            entries_html += f"""
        <div class="ref-card" style="margin-bottom:2.5rem;padding:1.5rem" id="{slug}">
            <h3 style="font-size:1.2rem;color:var(--accent);margin-bottom:0.2rem">{title}</h3>
            <p style="font-size:0.95rem;font-style:italic;color:var(--text-muted);margin-bottom:1rem">{subtitle}</p>
            <div style="display:grid;grid-template-columns:minmax(200px,300px) 1fr;gap:1.5rem;align-items:start">
                <div>{emblem_figures}</div>
                <div style="font-size:0.95rem;line-height:1.7">{autolink_emblems(body, depth=0)}</div>
            </div>
        </div>"""
        else:
            # No emblem image (phoenix, pelican)
            entries_html += f"""
        <div class="ref-card" style="margin-bottom:2.5rem;padding:1.5rem" id="{slug}">
            <h3 style="font-size:1.2rem;color:var(--accent);margin-bottom:0.2rem">{title}</h3>
            <p style="font-size:0.95rem;font-style:italic;color:var(--text-muted);margin-bottom:1rem">{subtitle}</p>
            <div style="font-size:0.95rem;line-height:1.7">{autolink_emblems(body, depth=0)}</div>
        </div>"""

    body = f"""
    <div class="page-content">
        <h1 style="font-size:1.8rem;margin-bottom:0.3rem">Maier's Alchemical Bestiary</h1>
        <p style="font-size:1.05rem;color:var(--text-muted);margin-bottom:0.5rem;line-height:1.6">
            The emblems of <em>Atalanta Fugiens</em> are populated by a menagerie of allegorical creatures —
            lions, wolves, dragons, eagles, toads, and salamanders — each encoding specific chemical
            substances and operations within the alchemical tradition. This page collects Maier's bestiary
            and situates each creature within the broader history of alchemical imagery, drawing on
            Lyndy Abraham's <em>Dictionary of Alchemical Imagery</em>, De Jong's source identifications,
            and Lawrence Principe's chemical interpretations.
        </p>

        <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:2rem;font-family:var(--font-sans)">{len(creatures)} creatures surveyed</p>
        {entries_html}
    </div>"""

    html = page_shell("Maier's Alchemical Bestiary", body, active_nav='Creatures')
    (SITE_DIR / 'creatures.html').write_text(html, encoding='utf-8')
    print(f"  creatures.html: {len(creatures)} creatures")


def build_maier_page(conn):
    """Build 'Emblems According to Maier' — each emblem with large image, epigram summary, and discourse summary."""

    emblems = conn.execute("""
        SELECT number, roman_numeral, canonical_label,
               motto_latin, motto_english, epigram_english,
               discourse_summary, alchemical_stage, image_description
        FROM emblems ORDER BY number
    """).fetchall()

    cards_html = ''
    for e in emblems:
        num, roman, label = e[0], e[1], e[2]
        motto_lat, motto_en, epigram = e[3], e[4], e[5]
        discourse, stage, img_desc = e[6], e[7], e[8]

        display = roman or 'Frontispiece'
        title = f'Emblem {display}' if roman else 'Frontispiece'
        fname = f'emblem-{num:02d}.jpg' if num >= 0 else 'emblem-00.jpg'
        link = f'emblems/emblem-{num:02d}.html' if num > 0 else 'emblems/frontispiece.html'

        # Stage badge
        stage_colors = {'NIGREDO': '#2c2418', 'ALBEDO': '#a89880', 'CITRINITAS': '#b8860b', 'RUBEDO': '#c0392b'}
        stage_fg = {'NIGREDO': '#f5f0e8', 'ALBEDO': '#2c2418', 'CITRINITAS': '#2c2418', 'RUBEDO': '#f5f0e8'}
        sbadge = ''
        if stage:
            bg = stage_colors.get(stage, '#7f8c8d')
            fg = stage_fg.get(stage, '#fff')
            sbadge = f'<span class="badge" style="background:{bg};color:{fg};font-size:0.8rem;padding:0.25rem 0.6rem;border-radius:3px;margin-left:0.5rem">{stage}</span>'

        # Epigram section
        epigram_html = ''
        if epigram and epigram.strip():
            epigram_html = f"""
                <div style="margin-bottom:1rem">
                    <h4 style="font-size:0.9rem;color:var(--accent);margin-bottom:0.4rem;font-family:var(--font-sans)">Epigram</h4>
                    <div style="font-style:italic;font-size:0.92rem;line-height:1.6;padding:0.6rem 1rem;background:var(--bg);border-left:3px solid var(--accent-light)">{epigram}</div>
                </div>"""

        # Discourse section
        discourse_html = ''
        if discourse and discourse.strip():
            discourse_html = f"""
                <div>
                    <h4 style="font-size:0.9rem;color:var(--accent);margin-bottom:0.4rem;font-family:var(--font-sans)">Maier's Discourse</h4>
                    <div style="font-size:0.92rem;line-height:1.7">{autolink_emblems(discourse, depth=0)}</div>
                </div>"""

        # Motto block
        motto_html = ''
        if motto_lat:
            motto_html += f'<p style="font-style:italic;color:var(--accent);margin-bottom:0.2rem;font-size:0.95rem">{motto_lat}</p>'
        if motto_en:
            motto_html += f'<p style="margin-top:0;margin-bottom:1rem;font-size:0.95rem">{motto_en}</p>'

        cards_html += f"""
        <div class="ref-card" style="margin-bottom:2.5rem;padding:0;overflow:hidden" id="emblem-{num}">
            <div style="display:grid;grid-template-columns:minmax(250px, 1fr) 2fr;gap:0">
                <div style="padding:1rem;background:#faf8f4;display:flex;flex-direction:column;align-items:center;justify-content:flex-start">
                    <a href="{link}">
                        <img src="images/emblems/{fname}" alt="{title}" style="width:100%;max-width:350px;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.12)">
                    </a>
                    <div style="margin-top:0.8rem;text-align:center">
                        <a href="{link}" style="font-size:0.85rem;color:var(--accent);font-family:var(--font-sans)">View full analysis &rarr;</a>
                    </div>
                </div>
                <div style="padding:1.5rem">
                    <h3 style="font-size:1.15rem;margin-bottom:0.3rem">{title} — {label}{sbadge}</h3>
                    {motto_html}
                    {epigram_html}
                    {discourse_html}
                </div>
            </div>
        </div>"""

    body = f"""
    <div class="page-content" style="max-width:1200px">
        <h1 style="font-size:1.8rem;margin-bottom:0.5rem">The Emblems According to Maier</h1>
        <p style="font-size:1.05rem;color:var(--text-muted);margin-bottom:0.5rem;line-height:1.6">
            Each of the fifty emblems of <em>Atalanta Fugiens</em> is accompanied by a Latin epigram
            and a two-page prose discourse in which Maier develops the alchemical meaning of the emblem's
            visual allegory. Here we present each emblem with its verse and a scholarly summary of the
            discourse argument, as Maier intended them to be encountered: image and text together,
            inviting the reader to meditate on the secrets of Nature.
        </p>
        <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:2rem;font-family:var(--font-sans)">
            51 emblems &middot; Click any image for the full scholarly analysis
        </p>
        <style>
            @media (max-width: 768px) {{
                .ref-card > div {{
                    grid-template-columns: 1fr !important;
                }}
            }}
        </style>
        {cards_html}
    </div>"""

    html = page_shell('The Emblems According to Maier', body, active_nav='Maier')
    (SITE_DIR / 'maier.html').write_text(html, encoding='utf-8')
    print(f"  maier.html: {len(emblems)} emblems")


def build_works_page():
    """Build the Scholarly Works page from merged staging JSON."""
    merged_path = BASE_DIR / 'staging' / 'works_merged.json'
    if not merged_path.exists():
        print("  works.html: skipped (no staging/works_merged.json)")
        return

    works_data = json.loads(merged_path.read_text(encoding='utf-8'))
    works = works_data.get('works', [])

    sections_html = ''
    for w in works:
        source_id = w.get('source_id', '')
        author = w.get('author', '')
        title = w.get('title', '')
        year = w.get('year', '')
        summary_html = w.get('summary_html', '')
        emblems = w.get('emblems_discussed', [])
        findings = w.get('key_findings', [])

        year_display = str(year) if year else 'n.d.'
        emblem_badges = ''
        if emblems:
            emblem_badges = '<div style="margin-top:0.5rem">' + ' '.join(
                f'<a href="emblems/emblem-{n:02d}.html" class="source-link" style="font-size:0.75rem">Emblem {n}</a>'
                if n > 0 else '<a href="emblems/frontispiece.html" class="source-link" style="font-size:0.75rem">Frontispiece</a>'
                for n in emblems
            ) + '</div>'

        findings_html = ''
        if findings:
            items = ''.join(f'<li style="font-size:0.85rem;margin-bottom:0.3rem">{f}</li>' for f in findings)
            findings_html = f'<div style="background:#faf8f4;padding:0.8rem 1rem;border-radius:4px;margin-top:1rem"><strong style="font-size:0.85rem;font-family:var(--font-sans)">Key Findings</strong><ul style="margin:0.5rem 0 0 1rem;padding:0">{items}</ul></div>'

        sections_html += f"""
        <div class="ref-card" style="margin-bottom:2rem;padding:1.5rem" id="{source_id}">
            <h3 style="font-size:1.1rem;margin-bottom:0.3rem;color:var(--accent)">{author} ({year_display})</h3>
            <p style="font-size:1rem;font-style:italic;margin-bottom:1rem">{title}</p>
            <div style="font-size:0.95rem;line-height:1.7">{summary_html}</div>
            {emblem_badges}
            {findings_html}
        </div>"""

    body = f"""
    <div class="page-content">
        <h1 style="font-size:1.8rem;margin-bottom:0.5rem">Scholarly Works on <em>Atalanta Fugiens</em></h1>
        <p style="font-size:1.05rem;color:var(--text-muted);margin-bottom:1.5rem;line-height:1.6">
            A curated library of secondary scholarship on Michael Maier's <em>Atalanta Fugiens</em>,
            from J.B. Craven's pioneering 1910 biography through the 2020 <em>Furnace and Fugue</em>
            digital edition. Each entry summarizes the work's arguments, methods, and specific
            contributions to understanding Maier's alchemical emblems.
        </p>

        <p style="font-size:0.9rem;color:var(--text-muted);margin-bottom:2rem">{len(works)} works surveyed, ordered chronologically.</p>
        {sections_html}
    </div>"""

    html = page_shell('Works', body, active_nav='Works')
    (SITE_DIR / 'works.html').write_text(html, encoding='utf-8')
    print(f"  works.html: {len(works)} scholarly works")


def build_music_page():
    """Build the Music page: recordings, performances, MIDI, and web resources."""

    body = """
    <div class="page-content">
        <h1 style="font-size:1.8rem;margin-bottom:0.3rem">Musical Recordings &amp; Performances</h1>
        <p style="font-size:1.1rem;color:var(--text-muted);margin-bottom:2rem;font-style:italic">
            The fifty three-voice fugues of <em>Atalanta Fugiens</em> &mdash; composed for Atalanta (soprano),
            Hippomenes (tenor), and the Golden Apple (cantus firmus) &mdash; represent the earliest known
            attempt to integrate musical composition into an alchemical emblem book.
        </p>


        <h2>Recordings</h2>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Ensemble Plus Ultra, dir. Michael Noone</h4>
            <p><strong>&ldquo;Maier: Atalanta Fugiens&rdquo;</strong> &mdash; Complete cycle of all 50 fugues (~71 minutes).
            Claudio Records CR5468, issued 2011. Booklet notes by Joscelyn Godwin. Available on
            Apple Music, Spotify, and other streaming platforms. This is the standard modern recording and the
            most widely cited commercial release.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Joscelyn Godwin Edition Recording (1987)</h4>
            <p>The first complete recording of the fifty fugues, produced for Godwin's Magnum Opus Hermetic
            Sourceworks edition. Performed by <strong>Rachel Platt, Emily Van Evera, Rufus Muller, and Richard
            Wistreich</strong>. Originally issued on cassette tape; later remastered and released on CD by
            Claudio Records. The Godwin edition (Phanes Press, 1989) includes modern notation that has been
            the basis for most subsequent performances and digital realizations.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Furnace and Fugue Vocal Recordings (2020)</h4>
            <p>Newly commissioned vocal recordings of all fifty fugues, produced for the
            <a href="https://furnaceandfugue.org" target="_blank" rel="noopener">Furnace and Fugue</a>
            digital edition (Brown University / University of Virginia Press, 2020). Streamable emblem-by-emblem
            within the interactive edition. These recordings are integrated with high-resolution images and
            searchable text, allowing synchronized experience of Maier's multi-sensory program.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>RIM c-Orchestra / David Kanaga (2021)</h4>
            <p><strong>&ldquo;Atalanta Fugiens 1&ndash;18&rdquo;</strong> &mdash; Electronic and experimental
            re-imagining of fugues 1 through 18. Released via Bandcamp. A creative interpretation rather than
            a historically informed performance.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Camerata Mediolanense</h4>
            <p>Albums titled <em>Atalanta Fugiens</em> and <em>Atalanta Fugiens (Deluxe Edition)</em> &mdash;
            a free creative work inspired by Maier's themes rather than a direct realization of the 50 canons.
            Neo-medieval / dark ambient aesthetic.</p>
        </div>

        <h2>Known Performances</h2>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>International Conference on the History of Alchemy and Chymistry, Philadelphia (2006)</h4>
            <p>The conference &ldquo;commenced with a performance of the early music ensemble <strong>Arcanum</strong>,&rdquo;
            including three canons from Atalanta Fugiens, sung in Latin. Noted by Joscelyn Godwin as evidence
            that the work &ldquo;is an obligatory inclusion at any alchemical musical recital.&rdquo;</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Les Canards Chantants (2014&ndash;present)</h4>
            <p>This vocal ensemble has performed and workshopped Atalanta Fugiens regularly since 2014, in
            collaboration with historians Donna Bilak and Tara Nummedal. Their lecture-performances include
            events at the Bard Graduate Center with performance demonstrations exploring the relationship
            between singing, seeing, and alchemical meditation.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>MITO Festival (2020)</h4>
            <p>A performance project for the MITO SettembreMusica Festival, directed by <strong>Vanni Moretto</strong>.
            Documented in a four-video YouTube playlist titled &ldquo;Atalanta Fugiens a MITO 2020.&rdquo;</p>
        </div>

        <h2>MIDI Files &amp; Digital Realizations</h2>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Adam McLean&rsquo;s Alchemy Website</h4>
            <p>The most comprehensive free source of MIDI files for Maier's fugues. The
            <a href="https://www.alchemywebsite.com/atalanta.html" target="_blank" rel="noopener">Atalanta Fugiens section</a>
            includes downloadable MIDI realizations for a substantial subset of the 50 fugues, each with a
            &ldquo;Save the MIDI file to your computer&rdquo; link. McLean also hosts the
            <a href="https://alchemywebsite.com/atalanta_thumbnails.html" target="_blank" rel="noopener">hand-coloured emblem plates</a>
            (1999) and the English translation from British Library MS Sloane 3645.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>BitMidi / MidiCities</h4>
            <p>Individual fugue MIDI downloads available for selected fugues, including No. 22 and No. 33.
            Searchable by title on BitMidi.com and MidiCities.com.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Amaranth Publishing</h4>
            <p>Sells a notation and arrangement package of the Atalanta Fugiens with transcriptions.
            Useful as a source for creating custom MIDI realizations, though the files themselves are not free.</p>
        </div>

        <h2>Video &amp; Web Resources</h2>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Furnace and Fugue Digital Edition</h4>
            <p><a href="https://furnaceandfugue.org" target="_blank" rel="noopener">furnaceandfugue.org</a> &mdash;
            The born-digital scholarly edition by Donna Bilak and Tara Nummedal (University of Virginia Press, 2020).
            Features interactive synchronized text, image, and music for all 50 emblems. Winner of the 2022
            Roy Rosenzweig Prize for Creativity in Digital History. Includes essays by Peter Forshaw on mytho-alchemy
            and Donna Bilak on steganography.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Peter Forshaw: &ldquo;The Emblemata of the Atalanta Fugiens&rdquo;</h4>
            <p>Infinite Fire Webinar II, Ritman Library / University of Amsterdam (November 2012).
            A detailed scholarly lecture walking through individual emblems, discussing mytho-alchemy,
            the quadrivium structure of each discourse, and Maier's relationship to the emblem tradition.
            Available on YouTube via the Embassy of the Free Mind channel.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>&ldquo;Singing Nature&rsquo;s Secrets&rdquo; Lecture</h4>
            <p>Public lecture with live performances exploring Michael Maier's Atalanta Fugiens (1618)
            and the Furnace and Fugue digital edition (2020). Available on the Furnace and Fugue YouTube channel.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>MITO 2020 YouTube Playlist</h4>
            <p>&ldquo;Atalanta Fugiens a MITO 2020&rdquo; &mdash; Four-video playlist documenting Vanni Moretto's
            performance project for the MITO SettembreMusica Festival. Searchable on YouTube.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>YouTube Coloured Prints with Instrumental Music</h4>
            <p>A full set of 50 emblems with accompanying instrumental versions of the music has been uploaded
            to YouTube. Individual emblem videos pair Adam McLean's coloured prints with instrumental realizations
            of the corresponding fugues.</p>
        </div>

        <div class="ref-card" style="margin-bottom:1rem">
            <h4>Adam McLean's Alchemy Website</h4>
            <p><a href="https://www.alchemywebsite.com/atalanta.html" target="_blank" rel="noopener">alchemywebsite.com/atalanta.html</a> &mdash;
            The most comprehensive single web resource for <em>Atalanta Fugiens</em> outside of Furnace and Fugue.
            Hosts the English translation (from MS Sloane 3645, transcribed by Clay Holden, Hereward Tilton,
            and Peter Branwin), MIDI files, and hand-coloured plates.</p>
        </div>

        <h2>Scholarly Writing on the Music</h2>

        <div style="margin-bottom:1.5rem">
            <table style="width:100%;border-collapse:collapse;margin:1rem 0">
                <tr style="border-bottom:2px solid var(--border);font-family:var(--font-sans);font-size:0.85rem">
                    <th style="padding:0.5rem;text-align:left">Author</th>
                    <th style="padding:0.5rem;text-align:left">Work</th>
                    <th style="padding:0.5rem;text-align:left">Year</th>
                    <th style="padding:0.5rem;text-align:left">Focus</th>
                </tr>
                <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.5rem">Joscelyn Godwin</td>
                    <td style="padding:0.5rem"><em>Atalanta Fugiens: An Edition of the Fugues, Emblems, and Epigrams</em></td>
                    <td style="padding:0.5rem">1987</td>
                    <td style="padding:0.5rem">First modern musical edition with complete transcriptions and recording</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.5rem">Joscelyn Godwin</td>
                    <td style="padding:0.5rem">&ldquo;Musical Alchemy: the Work of Composer and Listener&rdquo; (<em>Temenos</em>)</td>
                    <td style="padding:0.5rem">1985</td>
                    <td style="padding:0.5rem">Theoretical foundations of Maier's musical-alchemical synthesis</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.5rem">Joscelyn Godwin</td>
                    <td style="padding:0.5rem">&ldquo;A Background for Michael Maier's Atalanta Fugiens&rdquo; (<em>Hermetic Journal</em>)</td>
                    <td style="padding:0.5rem">1985</td>
                    <td style="padding:0.5rem">Intellectual context for the musical emblem book</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.5rem">Douglas Leedy</td>
                    <td style="padding:0.5rem">Review of Godwin edition (<em>Notes</em>)</td>
                    <td style="padding:0.5rem">1991</td>
                    <td style="padding:0.5rem">Technical musicological assessment of the fugues' sophistication</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.5rem">C. Morris Wescott</td>
                    <td style="padding:0.5rem">&ldquo;Atalanta Fugiens&rdquo; (<em>AthanorX</em>)</td>
                    <td style="padding:0.5rem">n.d.</td>
                    <td style="padding:0.5rem">Modal-planetary correspondences; cantus firmus as structural anchor</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.5rem">Peter Forshaw</td>
                    <td style="padding:0.5rem">&ldquo;Laboratorium, Auditorium, Oratorium&rdquo;</td>
                    <td style="padding:0.5rem">n.d.</td>
                    <td style="padding:0.5rem">Alchemical music including Maier's fugues and Khunrath's songs</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.5rem">Johann F.W. Hasler</td>
                    <td style="padding:0.5rem">&ldquo;Performative and Multimedia Aspects of Late-Renaissance Meditative Alchemy&rdquo;</td>
                    <td style="padding:0.5rem">2011</td>
                    <td style="padding:0.5rem">AF as meditative practice; performance dimensions</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.5rem">Bilak &amp; Nummedal (eds.)</td>
                    <td style="padding:0.5rem"><em>Furnace and Fugue</em></td>
                    <td style="padding:0.5rem">2020</td>
                    <td style="padding:0.5rem">Digital edition with newly commissioned vocal recordings of all 50 fugues</td>
                </tr>
            </table>
        </div>

        <h2>About the Fugues</h2>
        <p style="font-size:0.95rem;line-height:1.7">
            Each of the fifty emblems includes a three-voice fugue (more precisely, a canon) composed for
            three vocal parts. The three voices represent the dramatis personae of the overarching
            Atalanta myth: <strong>Atalanta</strong> (the fleeing volatile principle, typically the soprano),
            <strong>Hippomenes</strong> (the pursuing fixed principle, typically the tenor), and
            <strong>the Golden Apple</strong> (the catalytic agent, as the cantus firmus or bass).
            C. Morris Wescott has demonstrated that Maier's modal choices &mdash; Dorian, Phrygian,
            Mixolydian &mdash; correspond to planetary associations that relate to the alchemical stages
            depicted in each emblem's plate. The cantus firmus derives from the liturgical chant tradition,
            and the canons employ archaic compositional techniques including retrograde motion and mensural
            manipulation. Forty of the fifty fugues have been identified as based on compositions by
            the Elizabethan composer John Farmer.
        </p>
        <p style="font-size:0.95rem;line-height:1.7">
            Nothing is known about Maier's ideas on how the fugues were to be performed in practice,
            though some scholars believe they served as auditory support during corresponding alchemical
            work in the laboratory. Since Maier served as counsellor to Rudolf II, it is possible
            that the music was performed at the imperial court. The subtitle of the work promises
            compositions &ldquo;suitable for singing in couplets, to be looked at, read, meditated on,
            understood, weighed, sung, and listened to, not without a certain pleasure.&rdquo;
        </p>
    </div>"""

    html = page_shell('Music', body, active_nav='Music')
    (SITE_DIR / 'music.html').write_text(html, encoding='utf-8')
    print("  music.html")


# ============================================================
# Biography
# ============================================================

def build_biography():
    """Build Maier biography page from seed JSON."""
    seed_path = BASE_DIR / 'atalanta_fugiens_seed.json'
    if not seed_path.exists():
        print("  biography: skipped (no seed JSON)")
        return

    seed = json.loads(seed_path.read_text(encoding='utf-8'))
    bio = seed.get('biography')
    if not bio:
        print("  biography: skipped (no biography data)")
        return

    sections_html = ''
    for section in bio.get('sections', []):
        heading = section.get('heading', '')
        content = section.get('content', '')
        # Convert newlines to paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        para_html = ''.join(f'<p style="font-size:0.95rem;line-height:1.7;margin-bottom:1rem">{p}</p>' for p in paragraphs)
        sections_html += f"""
        <h2>{heading}</h2>
        {para_html}"""

    body = f"""
    <div class="page-content">
        <h1 style="font-size:1.8rem;margin-bottom:0.3rem">{bio.get('title', 'Michael Maier')}</h1>
        <p style="font-size:1.1rem;color:var(--text-muted);margin-bottom:2rem;font-style:italic">{bio.get('subtitle', '')}</p>

        {sections_html}
    </div>"""
    html = page_shell('Biography', body, active_nav='Biography')
    (SITE_DIR / 'biography.html').write_text(html, encoding='utf-8')
    print(f"  biography.html: {len(bio.get('sections', []))} sections")


# ============================================================
# Site Search Index + Page
# ============================================================

def build_search(conn):
    """Emit search-index.json (emblems + dictionary + essays + scholars + sources)
    and a search.html page that does client-side substring matching."""
    entries = []

    # Emblems
    em_rows = conn.execute("""
        SELECT number, roman_numeral, canonical_label, motto_english,
               motto_latin, discourse_summary, alchemical_stage
        FROM emblems ORDER BY number
    """).fetchall()
    for r in em_rows:
        num, roman, label, motto, motto_lat, discourse, stage = r
        href = 'emblems/frontispiece.html' if num == 0 else f'emblems/emblem-{num:02d}.html'
        title = f'Emblem {roman} — {label}' if roman else (label or 'Frontispiece')
        snippet_parts = [s for s in (motto, motto_lat, (discourse or '')[:280]) if s]
        entries.append({
            'type': 'emblem',
            'kind': 'Emblem',
            'title': title,
            'href': href,
            'tags': [stage] if stage else [],
            'snippet': ' · '.join(snippet_parts)[:340],
        })

    # Dictionary terms
    dict_rows = conn.execute("""
        SELECT slug, label, label_latin, category, definition_short, definition_long
        FROM dictionary_terms ORDER BY label
    """).fetchall()
    for r in dict_rows:
        slug, label, lat, cat, dshort, dlong = r
        title = label
        if lat and lat != label:
            title = f'{label} ({lat})'
        snippet = (dshort or '')[:300]
        if not snippet and dlong:
            snippet = dlong[:300]
        entries.append({
            'type': 'dict',
            'kind': cat or 'Term',
            'title': title,
            'href': f'dictionary/{slug}.html',
            'tags': [cat] if cat else [],
            'snippet': snippet,
        })

    # Scholars
    sch_rows = conn.execute("""
        SELECT name, specialization, af_focus, overview FROM scholars ORDER BY name
    """).fetchall()
    for r in sch_rows:
        name, spec, focus, overview = r
        snippet = ' · '.join(filter(None, [spec, focus, (overview or '')[:240]]))[:340]
        entries.append({
            'type': 'scholar',
            'kind': 'Scholar',
            'title': name,
            'href': f'scholar/{slugify(name)}.html',
            'tags': [],
            'snippet': snippet,
        })

    # Sources / authorities
    src_rows = conn.execute("""
        SELECT authority_id, name, type, era, description_long, relationship_to_maier
        FROM source_authorities ORDER BY name
    """).fetchall()
    for r in src_rows:
        auth_id, name, atype, era, dlong, rel = r
        slug = _authority_slug(auth_id)
        snippet = ' · '.join(filter(None, [atype, era, (dlong or rel or '')[:260]]))[:340]
        entries.append({
            'type': 'source',
            'kind': atype or 'Source',
            'title': name,
            'href': f'source/{slug}.html',
            'tags': [atype] if atype else [],
            'snippet': snippet,
        })

    # Essays — read the existing HTML files and harvest title + first paragraph
    essays_dir = SITE_DIR / 'essays'
    if essays_dir.exists():
        import re as _re
        for html_path in sorted(essays_dir.glob('*.html')):
            if html_path.name == 'index.html':
                continue
            try:
                text = html_path.read_text(encoding='utf-8')
            except Exception:
                continue
            title_m = _re.search(r'<h1[^>]*>(.*?)</h1>', text, _re.S)
            title = _re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else html_path.stem.replace('-', ' ').title()
            # First paragraph in the body
            para_m = _re.search(r'<p[^>]*>(.*?)</p>', text, _re.S)
            snippet = _re.sub(r'<[^>]+>', '', para_m.group(1)).strip() if para_m else ''
            entries.append({
                'type': 'essay',
                'kind': 'Essay',
                'title': title,
                'href': f'essays/{html_path.name}',
                'tags': [],
                'snippet': snippet[:340],
            })

    out_path = SITE_DIR / 'search-index.json'
    out_path.write_text(json.dumps(entries, ensure_ascii=False), encoding='utf-8')

    # Search page
    body = """
    <div class="page-content" style="max-width:1100px">
        <h2>Search</h2>
        <p>Across emblems, dictionary terms, scholars, source traditions, and essays.</p>
        <div class="filter-bar">
            <input type="search" id="search-input" class="filter-search" placeholder="Type to search&hellip; (e.g. dragon, salamander, Rosarium, Tilton)" autocomplete="off" autofocus>
            <div class="filter-row" id="search-type-chips">
                <span class="filter-label">Type:</span>
                <button class="filter-chip filter-chip-all active" data-search-type="" type="button">All</button>
                <button class="filter-chip" data-search-type="emblem" type="button">Emblems</button>
                <button class="filter-chip" data-search-type="dict" type="button">Dictionary</button>
                <button class="filter-chip" data-search-type="scholar" type="button">Scholars</button>
                <button class="filter-chip" data-search-type="source" type="button">Sources</button>
                <button class="filter-chip" data-search-type="essay" type="button">Essays</button>
            </div>
            <div class="filter-status" id="search-status"></div>
        </div>
        <div id="search-results" style="margin-top:1rem"></div>
    </div>
    <script>
    (async function() {
        const resp = await fetch('search-index.json');
        const entries = await resp.json();
        const input = document.getElementById('search-input');
        const status = document.getElementById('search-status');
        const results = document.getElementById('search-results');
        let activeType = '';
        let activeQuery = '';

        const KIND_COLORS = {
            'emblem': '#8b4513', 'dict': '#7f8c8d', 'scholar': '#2980b9',
            'source': '#16a085', 'essay': '#8e44ad'
        };

        function escapeHtml(s) {
            return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
        }

        function highlight(s, q) {
            if (!q) return escapeHtml(s);
            const lc = (s || '').toLowerCase();
            const ql = q.toLowerCase();
            let out = '', i = 0;
            while (i < s.length) {
                const idx = lc.indexOf(ql, i);
                if (idx < 0) { out += escapeHtml(s.slice(i)); break; }
                out += escapeHtml(s.slice(i, idx));
                out += '<mark>' + escapeHtml(s.slice(idx, idx + q.length)) + '</mark>';
                i = idx + q.length;
            }
            return out;
        }

        function readHash() {
            if (!window.location.hash) return;
            const hash = window.location.hash.slice(1);
            hash.split('&').forEach(pair => {
                const [k, v] = pair.split('=');
                if (k === 'q' && v) {
                    activeQuery = decodeURIComponent(v);
                    input.value = activeQuery;
                }
                if (k === 'type' && v) activeType = decodeURIComponent(v);
            });
        }

        function applySearch() {
            const q = activeQuery.trim().toLowerCase();
            // Update chip active states
            document.querySelectorAll('#search-type-chips .filter-chip').forEach(chip => {
                const t = chip.dataset.searchType;
                const isAll = chip.classList.contains('filter-chip-all');
                chip.classList.toggle('active', isAll ? !activeType : activeType === t);
            });
            if (!q) {
                status.innerHTML = '<em>Type at least 2 characters.</em>';
                results.innerHTML = '';
                return;
            }
            if (q.length < 2) {
                status.innerHTML = '<em>Type at least 2 characters.</em>';
                results.innerHTML = '';
                return;
            }
            const matches = [];
            for (const e of entries) {
                if (activeType && e.type !== activeType) continue;
                const hay = (e.title + ' ' + e.snippet + ' ' + (e.tags || []).join(' ')).toLowerCase();
                if (hay.includes(q)) {
                    let score = 0;
                    if (e.title.toLowerCase().includes(q)) score += 10;
                    if (e.title.toLowerCase().startsWith(q)) score += 5;
                    score -= matches.length * 0.001; // stable order
                    matches.push({ e, score });
                }
            }
            matches.sort((a, b) => b.score - a.score);
            const top = matches.slice(0, 80);
            status.innerHTML = matches.length
                ? '<strong>' + matches.length + '</strong> result' + (matches.length !== 1 ? 's' : '') +
                    (matches.length > top.length ? ' (showing first ' + top.length + ')' : '') +
                    (activeType ? ' in ' + activeType : '')
                : 'No results.';
            results.innerHTML = top.map(({ e }) => {
                const color = KIND_COLORS[e.type] || '#7f8c8d';
                return '<a href="' + e.href + '" class="search-result">' +
                    '<div class="search-result-kind" style="background:' + color + '">' + escapeHtml(e.kind) + '</div>' +
                    '<div class="search-result-body">' +
                        '<div class="search-result-title">' + highlight(e.title, q) + '</div>' +
                        '<div class="search-result-snippet">' + highlight(e.snippet, q) + '</div>' +
                    '</div>' +
                '</a>';
            }).join('');
        }

        input.addEventListener('input', () => {
            activeQuery = input.value;
            applySearch();
        });
        document.querySelectorAll('#search-type-chips .filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const t = chip.dataset.searchType || '';
                activeType = (activeType === t) ? '' : t;
                applySearch();
            });
        });
        window.addEventListener('hashchange', () => {
            activeQuery = '';
            activeType = '';
            input.value = '';
            readHash();
            applySearch();
        });
        readHash();
        applySearch();
    })();
    </script>"""
    html = page_shell('Search', body, active_nav='Search')
    (SITE_DIR / 'search.html').write_text(html, encoding='utf-8')
    print(f"  search.html + search-index.json: {len(entries)} entries")


# ============================================================
# Visual Browser (cross-corpus image-tag explorer)
# ============================================================

ALCHEMYDB_PATH = Path(r"C:\Dev\AlchemyBeatEmUp\db\alchemical_images.db")
ALCHEMYBEATEMUP_DATA_PATH = Path(r"C:\Dev\AlchemyBeatEmUp\data.json")
ALCHEMYBEATEMUP_SITE_URL = "https://t3dy.github.io/AlchemyBeatEmUp/"


def _load_alchemybeatemup_raw_urls():
    """Read AlchemyBeatEmUp data.json and return {image_id: raw_image_url}.

    Only the ORIGINAL engravings (raw_url) are surfaced here — the pixelated
    sprites belong to the game-asset pipeline and are never shown on Claudiens.
    """
    if not ALCHEMYBEATEMUP_DATA_PATH.exists():
        return {}
    try:
        data = json.loads(ALCHEMYBEATEMUP_DATA_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}
    out = {}
    for img in data.get('images', []):
        iid = img.get('image_id')
        raw = img.get('raw_url')
        if iid is None or not raw:
            continue
        out[iid] = ALCHEMYBEATEMUP_SITE_URL + raw.replace('\\', '/')
    return out


def _autotag_description(description, tags, dict_terms_by_slug):
    """Match icon_tags + Claudiens dictionary terms against the description text.

    Returns: (alchemydb_tag_slugs, dictionary_term_slugs) — both sorted, deduped.
    Uses word-boundary substring matching on label phrases and slug-as-words.
    """
    import re as _re
    if not description:
        return [], []
    desc = description.lower()
    matched_alch = set()
    for tag_slug, category, label, _td in tags:
        patterns = set()
        label_lower = (label or '').lower().strip()
        if label_lower:
            patterns.add(label_lower)
        slug_words = (tag_slug or '').replace('_', ' ').lower().strip()
        if slug_words:
            patterns.add(slug_words)
        # For single-word, common-noun categories also match the bare word stem
        if category in ('FIGURE', 'MONSTER', 'SUBSTANCE', 'TOOL', 'FURNITURE', 'PROCESS', 'ACCIDENT'):
            for word in (label_lower.split() + slug_words.split()):
                if len(word) >= 5 and word not in {'small', 'large', 'fixed'}:
                    patterns.add(word)
        for p in patterns:
            if not p:
                continue
            try:
                if _re.search(r'\b' + _re.escape(p) + r'\b', desc):
                    matched_alch.add(tag_slug)
                    break
            except _re.error:
                continue

    matched_dict = set()
    for slug, label_l, latin_l in dict_terms_by_slug:
        for cand in filter(None, [label_l, latin_l]):
            cand_l = cand.lower().strip()
            if not cand_l:
                continue
            try:
                if _re.search(r'\b' + _re.escape(cand_l) + r'\b', desc):
                    matched_dict.add(slug)
                    break
            except _re.error:
                continue
    return sorted(matched_alch), sorted(matched_dict)


# Alchemical stage → suggested process/substance tags (used to lift PROCESS coverage
# on Atalanta emblems whose visual descriptions don't name the process).
STAGE_TO_PROCESS_TAGS = {
    'NIGREDO': ['nigredo', 'putrefaction', 'mortificatio', 'calcination', 'dissolution'],
    'ALBEDO': ['albedo', 'sublimatio', 'distillatio', 'solutio'],
    'CITRINITAS': ['citrinitas', 'fermentatio', 'circulatio'],
    'RUBEDO': ['rubedo', 'coagulation', 'fixatio', 'multiplicatio', 'projectio'],
}


def _wikimedia_thumb_url(source_url, width=400):
    """Convert a Wikimedia Commons File: URL into an inline-displayable thumbnail URL.

    Returns None if the URL doesn't look like a Wikimedia Commons File: page.
    """
    if not source_url:
        return None
    import re as _re
    import urllib.parse as _u
    m = _re.search(r'/wiki/File:(.+)$', source_url)
    if not m:
        return None
    raw = _u.unquote(m.group(1)).replace(' ', '_')
    # Wikimedia "Special:FilePath" produces a thumbnail when ?width= is passed
    return f'https://commons.wikimedia.org/wiki/Special:FilePath/{_u.quote(raw)}?width={width}'


def _load_supplemental_scene_summaries():
    """Read data/visual_scene_summaries.json (curated descriptions for non-Atalanta
    images) if it exists. Map keys: stringified image_id → {scene, folio?} or string.
    """
    path = BASE_DIR / "data" / "visual_scene_summaries.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def build_visual_browser(conn):
    """Cross-corpus visual element browser — joins AlchemyDB image catalog
    against Claudiens emblem image_descriptions to auto-tag visual elements.
    """
    if not ALCHEMYDB_PATH.exists():
        print("  visual.html: skipped (AlchemyDB not present)")
        return

    alch = sqlite3.connect(f"file:{ALCHEMYDB_PATH}?mode=ro", uri=True)
    a = alch.cursor()

    # Pull all icon_tags
    a.execute("SELECT tag_slug, category, display_label, description FROM icon_tags ORDER BY category, tag_slug")
    tags = a.fetchall()

    # Pull source works for display
    a.execute("SELECT slug, full_title, author, date_text, status FROM source_works ORDER BY full_title")
    works = {row[0]: {'slug': row[0], 'title': row[1], 'author': row[2], 'date': row[3], 'status': row[4]} for row in a.fetchall()}

    # Pull all images
    a.execute("""SELECT image_id, work_slug, folio, caption, scene_summary,
                        master_path, web_path, thumbnail_path
                 FROM images ORDER BY work_slug, folio""")
    images = a.fetchall()
    alch.close()

    # Claudiens dictionary terms for cross-linking
    dict_rows = conn.execute(
        "SELECT slug, label, label_latin FROM dictionary_terms ORDER BY label"
    ).fetchall()

    # Claudiens emblems with image_description (for tagging Atalanta Fugiens images)
    emblem_descs = {}
    em_rows = conn.execute(
        "SELECT number, image_description, motto_english, canonical_label, alchemical_stage FROM emblems"
    ).fetchall()
    for r in em_rows:
        emblem_descs[r[0]] = {
            'description': r[1] or '',
            'motto': r[2] or '',
            'label': r[3] or '',
            'stage': r[4],
        }

    # Tag-slug → Claudiens dict slug mapping (for cross-linking)
    dict_slugs = {ds for ds, _, _ in dict_rows}
    dict_label_to_slug = {l.lower(): s for s, l, _ in dict_rows if l}
    tag_to_dict = {}
    for tag_slug, category, label, _td in tags:
        # Try direct slug match
        cand_slug = tag_slug.replace('_', '-')
        if cand_slug in dict_slugs:
            tag_to_dict[tag_slug] = cand_slug
            continue
        # Try label match
        if label and label.lower() in dict_label_to_slug:
            tag_to_dict[tag_slug] = dict_label_to_slug[label.lower()]

    supplemental_scenes = _load_supplemental_scene_summaries()
    abe_raw_urls = _load_alchemybeatemup_raw_urls()

    # Re-pull images with source_url so we can build remote thumbnails
    alch2 = sqlite3.connect(f"file:{ALCHEMYDB_PATH}?mode=ro", uri=True)
    img_rows = alch2.execute(
        "SELECT image_id, work_slug, folio, caption, scene_summary, master_path, web_path, thumbnail_path, source_url FROM images ORDER BY work_slug, folio"
    ).fetchall()
    alch2.close()
    images = img_rows

    # Build the JSON entries for the front-end
    image_entries = []
    image_tag_count = 0
    images_with_tags = 0

    for img in images:
        image_id, work_slug, folio, caption, scene, master, web, thumb, source_url = img
        text_parts = []
        if caption:
            text_parts.append(caption)
        if scene:
            text_parts.append(scene)
        # Curated supplemental scene summary keyed by stringified image_id
        sup_key = str(image_id)
        sup_entry = supplemental_scenes.get(sup_key)
        sup_scene = None
        sup_folio = None
        if isinstance(sup_entry, dict):
            sup_scene = sup_entry.get('scene') or sup_entry.get('description')
            sup_folio = sup_entry.get('folio')
        elif isinstance(sup_entry, str):
            sup_scene = sup_entry
        if sup_scene:
            text_parts.append(sup_scene)
        if sup_folio:
            folio = sup_folio
        emblem_num = None
        if work_slug == 'atalanta_fugiens' and folio:
            try:
                emblem_num = int(folio.replace('plate', '').strip())
            except (ValueError, AttributeError):
                emblem_num = None
            if emblem_num is not None and emblem_num in emblem_descs:
                text_parts.append(emblem_descs[emblem_num]['description'])
                text_parts.append(emblem_descs[emblem_num]['motto'])
                text_parts.append(emblem_descs[emblem_num]['label'])
        text = ' '.join(text_parts).strip()
        alch_tags, claudiens_dict_tags = _autotag_description(text, tags, dict_rows) if text else ([], [])

        # Stage→process boost for Atalanta emblems (PROCESS tags rarely appear in
        # visual descriptions; the alchemical_stage column is a strong proxy).
        if work_slug == 'atalanta_fugiens' and emblem_num is not None and emblem_num in emblem_descs:
            stage = emblem_descs[emblem_num].get('stage')
            if stage and stage in STAGE_TO_PROCESS_TAGS:
                existing = set(alch_tags)
                tag_slugs_set = {t[0] for t in tags}
                for proc_tag in STAGE_TO_PROCESS_TAGS[stage]:
                    if proc_tag in tag_slugs_set and proc_tag not in existing:
                        alch_tags.append(proc_tag)
                        existing.add(proc_tag)
                alch_tags.sort()
                # Mirror onto dictionary cross-tags where the slug exists
                dict_slugs_set = {ds for ds, _, _ in dict_rows}
                for proc_tag in STAGE_TO_PROCESS_TAGS[stage]:
                    if proc_tag in dict_slugs_set and proc_tag not in claudiens_dict_tags:
                        claudiens_dict_tags.append(proc_tag)
                claudiens_dict_tags.sort()

        if alch_tags:
            images_with_tags += 1
        image_tag_count += len(alch_tags)

        # Choose displayable image url + a click-through link
        if work_slug == 'atalanta_fugiens' and emblem_num is not None:
            local_url = f'images/emblems/emblem-{emblem_num:02d}.jpg'
            link_url = (
                f'emblems/frontispiece.html' if emblem_num == 0 else
                f'emblems/emblem-{emblem_num:02d}.html'
            )
        else:
            # Prefer the original-quality engraving from the sister AlchemyBeatEmUp
            # repo (cross-served from its GitHub Pages); fall back to Wikimedia.
            local_url = abe_raw_urls.get(image_id) or _wikimedia_thumb_url(source_url, width=480)
            link_url = source_url or None

        title_parts = []
        work_title = works.get(work_slug, {}).get('title') or work_slug
        title_parts.append(work_title)
        if folio:
            title_parts.append(folio)
        title = ' — '.join(title_parts)

        snippet = caption or ''
        if not snippet and sup_scene:
            snippet = sup_scene[:240]
        if not snippet and emblem_num is not None and emblem_num in emblem_descs:
            snippet = emblem_descs[emblem_num]['label'] or emblem_descs[emblem_num]['motto'] or ''

        image_entries.append({
            'id': image_id,
            'work': work_slug,
            'work_title': work_title,
            'folio': folio,
            'title': title,
            'snippet': snippet[:240],
            'local_url': local_url,
            'link_url': link_url,
            'source_url': source_url,
            'is_external': not (work_slug == 'atalanta_fugiens'),
            'tags': alch_tags,
            'dict_tags': claudiens_dict_tags,
        })

    # Tag metadata for the front-end (with counts of tagged images)
    from collections import Counter
    tag_counts = Counter()
    for ie in image_entries:
        for t in ie['tags']:
            tag_counts[t] += 1

    tag_entries = []
    for tag_slug, category, label, td in tags:
        tag_entries.append({
            'slug': tag_slug,
            'category': category,
            'label': label,
            'description': td,
            'count': tag_counts.get(tag_slug, 0),
            'dict_link': tag_to_dict.get(tag_slug),
        })

    work_entries = list(works.values())
    work_image_counts = Counter(ie['work'] for ie in image_entries)
    work_tag_counts = Counter()
    for ie in image_entries:
        if ie['tags']:
            work_tag_counts[ie['work']] += 1
    for w in work_entries:
        w['image_count'] = work_image_counts.get(w['slug'], 0)
        w['tagged_count'] = work_tag_counts.get(w['slug'], 0)

    # Annotate each work with a slug-friendly key for the per-work page link
    for w in work_entries:
        w['page_slug'] = w['slug'].replace('_', '-')

    visual_data = {
        'images': image_entries,
        'tags': tag_entries,
        'works': sorted(work_entries, key=lambda w: -w['image_count']),
        'stats': {
            'total_images': len(image_entries),
            'tagged_images': images_with_tags,
            'total_tag_links': image_tag_count,
            'total_tags': len(tag_entries),
            'total_works': len(work_entries),
        },
    }
    (SITE_DIR / 'visual-data.json').write_text(json.dumps(visual_data, ensure_ascii=False), encoding='utf-8')

    # ── Per-source-work landing pages /work/<slug>.html ──
    work_dir = SITE_DIR / 'work'
    work_dir.mkdir(exist_ok=True)
    tag_meta_by_slug = {t['slug']: t for t in tag_entries}
    images_by_work = {}
    for ie in image_entries:
        images_by_work.setdefault(ie['work'], []).append(ie)

    CATEGORY_COLORS_PY = {
        'FIGURE': '#8b4513', 'MONSTER': '#c0392b', 'PROCESS': '#16a085',
        'SUBSTANCE': '#2980b9', 'FURNITURE': '#7f8c8d', 'TOOL': '#8e44ad',
        'ACCIDENT': '#e67e22', 'BODY_STATE': '#a89880', 'SCENERY': '#27ae60',
    }

    for w in work_entries:
        wslug = w['slug']
        page_slug = w['page_slug']
        work_imgs = images_by_work.get(wslug, [])
        # Tag-frequency for this work
        local_counts = {}
        for ie in work_imgs:
            for t in ie['tags']:
                local_counts[t] = local_counts.get(t, 0) + 1
        sorted_tags = sorted(local_counts.items(), key=lambda kv: -kv[1])
        tag_chips_html = ''
        for tag_slug, n in sorted_tags[:30]:
            meta = tag_meta_by_slug.get(tag_slug, {})
            color = CATEGORY_COLORS_PY.get(meta.get('category', ''), '#7f8c8d')
            label = meta.get('label', tag_slug)
            tag_chips_html += (
                f'<a href="../visual.html#tag={tag_slug}&work={wslug}" class="vis-tag-chip" '
                f'style="border-color:{color};color:{color};text-decoration:none">'
                f'{label} <span class="vis-tag-count">{n}</span></a>'
            )

        # Cards for the images in this work (capped at 60)
        card_html_parts = []
        for ie in work_imgs[:60]:
            link_attrs = ''
            if ie['link_url']:
                link_attrs = f'href="{("../" + ie["link_url"]) if not ie["is_external"] else ie["link_url"]}"'
                if ie['is_external']:
                    link_attrs += ' target="_blank" rel="noopener"'
                tag_open = f'<a {link_attrs} class="card" style="text-decoration:none;color:inherit">'
                tag_close = '</a>'
            else:
                tag_open = '<div class="card" style="cursor:default">'
                tag_close = '</div>'
            if ie['local_url']:
                src = ie['local_url'] if ie['is_external'] else ('../' + ie['local_url'])
                img_tag = f'<img src="{src}" alt="" loading="lazy" style="width:100%;display:block;aspect-ratio:auto">'
            else:
                folio_label = (ie['folio'] or '').replace('plate ', '').upper() or '?'
                img_tag = f'<div class="card-placeholder" style="aspect-ratio:1;font-size:1.4rem">{folio_label}</div>'
            card_html_parts.append(
                tag_open + img_tag + '<div class="card-body">'
                f'<div class="card-sig" style="font-size:0.78rem">{(ie["folio"] or "")}</div>'
                f'<div class="card-desc" style="font-size:0.78rem">{(ie["snippet"] or "")[:120]}</div>'
                + '</div>' + tag_close
            )
        cards_html = ''.join(card_html_parts)
        overflow = ''
        if len(work_imgs) > 60:
            overflow = f'<p style="grid-column:1/-1;color:var(--text-muted);font-style:italic;padding:1rem">…and {len(work_imgs) - 60} more in <a href="../visual.html#work={wslug}">the visual browser</a>.</p>'

        meta_line_parts = []
        if w.get('author'): meta_line_parts.append(w['author'])
        if w.get('date'): meta_line_parts.append(w['date'])
        if w.get('region'): meta_line_parts.append(w['region'])
        meta_line = ' &middot; '.join(meta_line_parts)

        body = f"""
        <div class="page-content" style="max-width:1200px">
            <a href="../visual.html" class="back-link">&larr; Visual Browser</a>
            <h1 style="font-size:1.8rem;margin-bottom:0.3rem">{w.get('title') or wslug}</h1>
            <p style="color:var(--text-muted);font-family:var(--font-sans);margin-bottom:1rem;font-size:0.9rem">{meta_line}</p>
            <p style="font-size:0.95rem">{w.get('image_count', 0)} image{'s' if w.get('image_count', 0) != 1 else ''} indexed; {w.get('tagged_count', 0)} carry visual-element tags.</p>
            {f'<h2>Visual elements depicted</h2><p style="font-size:0.85rem;color:var(--text-muted);font-family:var(--font-sans);margin-bottom:0.5rem">Click a tag to see all images of it across every emblem book.</p><div id="vis-tag-cloud" style="background:var(--bg-card);padding:0.6rem;border:1px solid var(--border);border-radius:4px;margin-bottom:1.2rem">{tag_chips_html}</div>' if tag_chips_html else '<p style="color:var(--text-muted);font-style:italic;margin-top:1rem">No visual-element tags applied yet for this work — captions and scene-summaries are still being curated.</p>'}
            <h2>Images</h2>
            <div class="gallery" style="grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));padding:0">{cards_html}{overflow}</div>
        </div>"""
        html = page_shell(w.get('title') or wslug, body, active_nav='Visual', depth=1)
        (work_dir / f'{page_slug}.html').write_text(html, encoding='utf-8')

    print(f"  work/: {len(work_entries)} per-source-work pages")

    # ── /galleries/index.html — landing tab for all alchemical emblem-book galleries ──
    galleries_dir = SITE_DIR / 'galleries'
    galleries_dir.mkdir(exist_ok=True)

    # Hand-curated capsule descriptions — explains what each work is and why it matters
    WORK_CAPSULES = {
        'atalanta_fugiens': "Maier's own 1617 emblem book — fifty engravings, mottos, epigrams, and three-voice fugues. The deepest gallery on this site (full scholarly apparatus on every plate).",
        'symbola_aureae_mensae': "Maier's 1617 companion to Atalanta Fugiens: twelve patriarchs of alchemy across twelve nations, from Hermes Trismegistus to Maier himself.",
        'splendor_solis': "The 1532 Berlin codex — twenty-two of the most luxurious miniatures in the alchemical canon, attributed to Salomon Trismosin.",
        'mutus_liber': "The 'silent book' (1677) — fifteen engravings narrating the work without text. An alchemical couple gathers celestial dew, distils, and completes the opus in pictures alone.",
        'rosarium_philosophorum': "The Rosary of the Philosophers (1550) — twenty foundational woodcuts of the chemical wedding. Every alchemical emblem book that follows quotes from this sequence.",
        'aurora_consurgens': "Late-medieval treatise (attributed to pseudo-Aquinas) — the Zürich manuscript carries a remarkable cycle of monsters, dragons, and biblical-alchemical hybrids.",
        'crowning_of_nature': "Sixty-seven plates of pure visual sequence — one of the longest emblematic narratives of the work, depicting the Stone's gestation in detail.",
        'khunrath_amphitheatrum': "Khunrath's Amphitheatre of Eternal Wisdom (1595/1609) — Christian-cabalistic-alchemical engravings combining laboratory, oratory, and mystical symbolism.",
        'lambsprinck': "De Lapide Philosophico (Lambsprinck, c. 1599) — fifteen animal-emblems including the unicorn-and-stag, the two fishes, and the father-and-son embrace.",
        'geber_summa': "Pseudo-Geber's Summa Perfectionis (13th c.) — the Latin alchemical corpus that medieval and Renaissance practitioners called 'Geber'; foundational distillation iconography.",
        'libavius_alchymia': "Andreas Libavius (1597) — the first systematic textbook of alchemy, including the famous diagram of the ideal alchemical laboratory.",
        'biringuccio_pirotechnia': "Vannoccio Biringuccio (1540) — the first printed treatise on metallurgy. Smelting, casting, assaying — the practical art alchemy theorizes.",
        'agricola_de_re_metallica': "Georgius Agricola (1556) — the great compendium of mining and metallurgy, with engravings of furnaces, water-wheels, and the descent into matter.",
        'glauber_furni_novi': "Johann Rudolf Glauber's Furni Novi Philosophici (1646–49) — 'New Philosophical Furnaces' that lifted the iatrochemical art toward modern chemistry.",
        'ripley_scrolls': "The Ripley Scrolls (15th–16th c. England) — vertical pictorial allegories of the entire opus, descended from George Ripley's Compound of Alchymy.",
    }

    sorted_works = sorted(work_entries, key=lambda w: -w['image_count'])
    cover_image_for = {}
    for ie in image_entries:
        wslug = ie['work']
        if wslug not in cover_image_for and ie.get('local_url'):
            cover_image_for[wslug] = ie

    cards_html = ''
    for w in sorted_works:
        wslug = w['slug']
        page_slug = w['page_slug']
        capsule = WORK_CAPSULES.get(wslug, '')
        cover = cover_image_for.get(wslug)
        if cover and cover.get('local_url'):
            raw = cover['local_url']
            # AlchemyBeatEmUp URLs are absolute https, Atalanta paths are repo-root-relative
            src = raw if raw.startswith('http') else ('../' + raw)
            img_tag = f'<img src="{src}" alt="{w.get("title", wslug)}" loading="lazy" style="width:100%;height:240px;object-fit:cover;display:block;background:var(--bg)">'
        else:
            img_tag = f'<div class="card-placeholder" style="height:240px;display:flex;align-items:center;justify-content:center;font-size:1.4rem">{w.get("title", wslug)[:30]}</div>'

        meta_parts = []
        if w.get('author'): meta_parts.append(w['author'])
        if w.get('date'): meta_parts.append(w['date'])
        meta_line = ' &middot; '.join(meta_parts)

        is_atalanta = wslug == 'atalanta_fugiens'
        primary_link = 'emblems/index.html' if is_atalanta else f'work/{page_slug}.html'
        link_path = '../' + primary_link

        cards_html += f"""
        <a href="{link_path}" class="gallery-tile" style="display:flex;flex-direction:column;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;overflow:hidden;text-decoration:none;color:inherit;transition:transform 0.15s, box-shadow 0.15s">
            {img_tag}
            <div style="padding:1rem 1.1rem;flex:1;display:flex;flex-direction:column">
                <h3 style="font-size:1.1rem;color:var(--accent);margin:0 0 0.2rem;font-family:var(--font-serif)">{w.get('title', wslug)}{(' <span class="badge badge-primary" style="font-size:0.65rem;vertical-align:middle">primary work</span>' if is_atalanta else '')}</h3>
                <div style="font-family:var(--font-sans);font-size:0.75rem;color:var(--text-muted);margin-bottom:0.4rem">{meta_line}</div>
                <div style="font-size:0.88rem;line-height:1.55;flex:1">{capsule}</div>
                <div style="font-family:var(--font-sans);font-size:0.78rem;color:var(--text-muted);margin-top:0.6rem;display:flex;justify-content:space-between;align-items:center">
                    <span>{w.get('image_count', 0)} plate{'s' if w.get('image_count', 0) != 1 else ''} · {w.get('tagged_count', 0)} tagged</span>
                    <span style="color:var(--accent)">Browse →</span>
                </div>
            </div>
        </a>"""

    galleries_body = f"""
    <div class="page-content" style="max-width:1300px">
        <h2>Alchemical Emblem Galleries</h2>
        <p style="font-size:0.95rem;line-height:1.7;max-width:780px">Browse the visual record of alchemy across {len(sorted_works)} source works ({sum(w['image_count'] for w in sorted_works)} plates total). Atalanta Fugiens is the centre of this site's scholarly apparatus — the other galleries surround it as comparison material. Click any tile to open that gallery; from inside each work-page you can drill into the visual element browser to see how its imagery overlaps with the rest of the corpus.</p>

        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:1rem 1.2rem;margin:1rem 0 1.5rem;font-size:0.88rem">
            <strong style="color:var(--accent);font-family:var(--font-sans)">How to compare</strong> — every plate is auto-tagged with its visual elements (dragons, lions, athanors, calcinations …). On the <a href="../visual.html" style="color:var(--accent)">Visual Browser</a> you can pin a tag and watch every emblem book light up; on the <a href="../stage/index.html" style="color:var(--accent)">Stages</a> pages you can compare nigredo plates from Atalanta against nigredo plates from Splendor Solis and Aurora Consurgens. Most non-Atalanta images are served via the sister project <a href="{ALCHEMYBEATEMUP_SITE_URL}" target="_blank" rel="noopener" style="color:var(--accent)">AlchemyBeatEmUp</a> (the original engravings, never the pixelated game-asset versions).</div>

        <div class="gallery-tile-grid" style="display:grid;grid-template-columns:repeat(auto-fill, minmax(320px, 1fr));gap:1.2rem">{cards_html}</div>
    </div>"""
    html = page_shell('Alchemical Emblem Galleries', galleries_body, active_nav='Galleries', depth=1)
    (galleries_dir / 'index.html').write_text(html, encoding='utf-8')
    print(f"  galleries/index.html: {len(sorted_works)} gallery tiles")

    # ── Inverted index: Claudiens dictionary slug → [image entries] ──
    # This gets consumed by dictionary term pages (Slice 3) to show
    # "Depicted in N emblem books" panels with cross-corpus thumbnails.
    depicts_by_slug = {}
    for ie in image_entries:
        if not ie['dict_tags']:
            continue
        compact = {
            'work': ie['work'],
            'work_title': ie['work_title'],
            'folio': ie['folio'],
            'snippet': ie['snippet'],
            'local_url': ie['local_url'],
            'link_url': ie['link_url'],
            'source_url': ie['source_url'],
            'is_external': ie['is_external'],
        }
        for dslug in ie['dict_tags']:
            depicts_by_slug.setdefault(dslug, []).append(compact)
    (SITE_DIR / 'dictionary-depicts.json').write_text(
        json.dumps(depicts_by_slug, ensure_ascii=False), encoding='utf-8'
    )

    # The HTML page
    body = """
    <div class="page-content" style="max-width:1300px">
        <h2>Visual Element Browser</h2>
        <p style="font-size:0.95rem">A cross-corpus index of visual elements depicted in alchemical emblem books. Click a tag to see every image (across <span id="vis-work-count">…</span> source works) that depicts it. Atalanta Fugiens emblems link directly into this site's analysis pages.</p>

        <div class="stats" id="vis-stats" style="max-width:900px"></div>

        <div class="filter-bar">
            <input type="search" id="vis-search" class="filter-search" placeholder="Search tags or images (e.g. dragon, athanor, calcination)&hellip;" autocomplete="off">
            <div class="filter-row" id="vis-cat-row">
                <span class="filter-label">Category:</span>
                <button class="filter-chip filter-chip-all active" data-vis-cat="" type="button">All</button>
            </div>
            <div class="filter-row" id="vis-work-row">
                <span class="filter-label">Source:</span>
                <button class="filter-chip filter-chip-all active" data-vis-work="" type="button">All</button>
            </div>
            <div class="filter-status" id="vis-status"></div>
        </div>

        <h3 style="font-size:1.05rem;color:var(--accent);font-family:var(--font-sans);margin:1.4rem 0 0.4rem">Tags <span style="font-size:0.78rem;color:var(--text-muted)">click to filter the gallery below</span></h3>
        <div id="vis-tag-cloud"></div>

        <h3 style="font-size:1.05rem;color:var(--accent);font-family:var(--font-sans);margin:1.5rem 0 0.4rem">Images</h3>
        <div id="vis-images" class="gallery" style="grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));padding:0"></div>
    </div>

    <script>
    (async function() {
        const resp = await fetch('visual-data.json');
        const data = await resp.json();
        const tagBySlug = {};
        for (const t of data.tags) tagBySlug[t.slug] = t;

        const CATEGORY_COLORS = {
            'FIGURE': '#8b4513', 'MONSTER': '#c0392b', 'PROCESS': '#16a085',
            'SUBSTANCE': '#2980b9', 'FURNITURE': '#7f8c8d', 'TOOL': '#8e44ad',
            'ACCIDENT': '#e67e22', 'BODY_STATE': '#a89880', 'SCENERY': '#27ae60'
        };

        let activeTag = '';
        let activeCat = '';
        let activeWork = '';
        let activeQuery = '';

        // Stats
        const statsEl = document.getElementById('vis-stats');
        statsEl.innerHTML = [
            ['total_images', 'Images'],
            ['total_works', 'Source works'],
            ['total_tags', 'Tags'],
            ['total_tag_links', 'Tag links'],
        ].map(([k, label]) => '<div class="stat-card"><span class="stat-number">' + (data.stats[k] || 0) + '</span><span class="stat-label">' + label + '</span></div>').join('');
        document.getElementById('vis-work-count').textContent = data.stats.total_works;

        // Build category chips
        const cats = [...new Set(data.tags.map(t => t.category))].sort();
        const catRow = document.getElementById('vis-cat-row');
        for (const c of cats) {
            const btn = document.createElement('button');
            btn.className = 'filter-chip';
            btn.type = 'button';
            btn.dataset.visCat = c;
            btn.style.background = CATEGORY_COLORS[c] || '#7f8c8d';
            btn.style.color = 'white';
            btn.style.border = '1px solid ' + (CATEGORY_COLORS[c] || '#7f8c8d');
            btn.textContent = c.replace('_', ' ');
            catRow.appendChild(btn);
        }

        // Build source-work chips (top 8 by image count)
        const workRow = document.getElementById('vis-work-row');
        for (const w of data.works.slice(0, 8)) {
            if (!w.image_count) continue;
            const btn = document.createElement('button');
            btn.className = 'filter-chip';
            btn.type = 'button';
            btn.dataset.visWork = w.slug;
            btn.title = (w.author || '') + (w.date ? ' · ' + w.date : '');
            btn.innerHTML = (w.title || w.slug) + ' <span class="filter-chip-count">' + w.image_count + '</span>';
            workRow.appendChild(btn);
        }
        // "Open as page" jump-link for the active source filter
        const workOpen = document.createElement('a');
        workOpen.id = 'vis-work-open';
        workOpen.style.cssText = 'margin-left:0.5rem;font-size:0.78rem;font-family:var(--font-sans);color:var(--accent);display:none';
        workRow.appendChild(workOpen);

        function escapeHtml(s) { return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

        function renderTagCloud() {
            const cloud = document.getElementById('vis-tag-cloud');
            const filtered = data.tags.filter(t => {
                if (activeCat && t.category !== activeCat) return false;
                if (activeQuery && !(t.slug + ' ' + t.label).toLowerCase().includes(activeQuery)) return false;
                return true;
            });
            // Sort: items with images first, by count desc, then alpha
            filtered.sort((a, b) => (b.count - a.count) || a.label.localeCompare(b.label));
            cloud.innerHTML = filtered.map(t => {
                const color = CATEGORY_COLORS[t.category] || '#7f8c8d';
                const isActive = activeTag === t.slug;
                const dim = !t.count ? 'opacity:0.45' : '';
                const dictLink = t.dict_link ? '<a href="dictionary/' + t.dict_link + '.html" class="vis-tag-dict-link" title="Open ' + escapeHtml(t.label) + ' in the dictionary">↗</a>' : '';
                return '<button class="vis-tag-chip ' + (isActive ? 'active' : '') + '" data-vis-tag="' + t.slug + '" type="button" style="border-color:' + color + (isActive ? ';background:' + color + ';color:white' : ';color:' + color) + ';' + dim + '">' +
                    escapeHtml(t.label) + ' <span class="vis-tag-count">' + t.count + '</span>' + dictLink +
                    '</button>';
            }).join('');
        }

        function renderImages() {
            const container = document.getElementById('vis-images');
            const status = document.getElementById('vis-status');
            const filtered = data.images.filter(im => {
                if (activeTag && !im.tags.includes(activeTag)) return false;
                if (activeWork && im.work !== activeWork) return false;
                if (activeCat && !im.tags.some(tg => tagBySlug[tg] && tagBySlug[tg].category === activeCat)) return false;
                if (activeQuery) {
                    const hay = (im.title + ' ' + im.snippet + ' ' + im.tags.join(' ')).toLowerCase();
                    if (!hay.includes(activeQuery)) return false;
                }
                return true;
            });
            const parts = [];
            if (activeTag) parts.push('tag <strong>' + activeTag + '</strong>');
            if (activeCat) parts.push('category <strong>' + activeCat + '</strong>');
            if (activeWork) parts.push('source <strong>' + activeWork + '</strong>');
            if (activeQuery) parts.push('text <strong>"' + escapeHtml(activeQuery) + '"</strong>');
            if (parts.length || filtered.length !== data.images.length) {
                status.innerHTML = 'Showing <strong>' + filtered.length + '</strong> of ' + data.images.length + ' images' +
                    (parts.length ? ' — filtered by ' + parts.join(', ') + ' <a href="#" id="vis-clear" class="filter-clear">clear</a>' : '');
                const clearLink = document.getElementById('vis-clear');
                if (clearLink) clearLink.addEventListener('click', e => { e.preventDefault(); clearAll(); });
            } else {
                status.innerHTML = '';
            }
            const top = filtered.slice(0, 200);
            container.innerHTML = top.map(im => {
                const linkOpen = im.link_url
                    ? '<a href="' + im.link_url + '"' + (im.is_external ? ' target="_blank" rel="noopener"' : '') + ' class="card" style="text-decoration:none;color:inherit">'
                    : '<div class="card" style="cursor:default">';
                const linkClose = im.link_url ? '</a>' : '</div>';
                const img = im.local_url
                    ? '<img src="' + im.local_url + '" alt="' + escapeHtml(im.title) + '" style="width:100%;display:block;aspect-ratio:auto">'
                    : '<div class="card-placeholder">' + escapeHtml((im.folio || '').replace('plate ', '').toUpperCase() || '?') + '</div>';
                const tagBadges = im.tags.slice(0, 6).map(tg => {
                    const meta = tagBySlug[tg] || { label: tg, category: '' };
                    const color = CATEGORY_COLORS[meta.category] || '#7f8c8d';
                    return '<span class="vis-img-tag" data-vis-tag="' + tg + '" style="background:' + color + '">' + escapeHtml(meta.label) + '</span>';
                }).join('');
                return linkOpen +
                    img +
                    '<div class="card-body">' +
                        '<div class="card-sig" style="font-size:0.8rem">' + escapeHtml(im.work_title || '') + '</div>' +
                        '<div class="card-label" style="font-size:0.78rem;color:var(--text-muted)">' + escapeHtml(im.folio || '') + '</div>' +
                        (im.snippet ? '<div class="card-desc" style="font-size:0.78rem">' + escapeHtml(im.snippet) + '</div>' : '') +
                        (tagBadges ? '<div class="vis-img-tags">' + tagBadges + '</div>' : '') +
                    '</div>' +
                    linkClose;
            }).join('') + (filtered.length > top.length ? '<p style="grid-column:1/-1;color:var(--text-muted);font-style:italic;padding:1rem">…and ' + (filtered.length - top.length) + ' more (refine the filters to narrow).</p>' : '');
        }

        function syncChips() {
            document.querySelectorAll('[data-vis-cat]').forEach(b => {
                const v = b.dataset.visCat;
                const isAll = b.classList.contains('filter-chip-all');
                b.classList.toggle('active', isAll ? !activeCat : activeCat === v);
            });
            document.querySelectorAll('[data-vis-work]').forEach(b => {
                const v = b.dataset.visWork;
                const isAll = b.classList.contains('filter-chip-all');
                b.classList.toggle('active', isAll ? !activeWork : activeWork === v);
            });
            const openLink = document.getElementById('vis-work-open');
            if (openLink) {
                if (activeWork) {
                    const w = data.works.find(x => x.slug === activeWork);
                    if (w && w.page_slug) {
                        openLink.href = 'work/' + w.page_slug + '.html';
                        openLink.textContent = 'Open ' + (w.title || activeWork) + ' page →';
                        openLink.style.display = '';
                    } else {
                        openLink.style.display = 'none';
                    }
                } else {
                    openLink.style.display = 'none';
                }
            }
        }

        function readHash() {
            if (!window.location.hash) return;
            const h = window.location.hash.slice(1);
            h.split('&').forEach(p => {
                const [k, v] = p.split('=');
                if (k === 'tag' && v) activeTag = decodeURIComponent(v);
                if (k === 'cat' && v) activeCat = decodeURIComponent(v);
                if (k === 'work' && v) activeWork = decodeURIComponent(v);
                if (k === 'q' && v) {
                    activeQuery = decodeURIComponent(v).toLowerCase();
                    document.getElementById('vis-search').value = decodeURIComponent(v);
                }
            });
        }

        function clearAll() {
            activeTag = ''; activeCat = ''; activeWork = ''; activeQuery = '';
            document.getElementById('vis-search').value = '';
            if (window.history && window.history.replaceState) {
                window.history.replaceState(null, '', window.location.pathname);
            }
            renderAll();
        }

        function renderAll() {
            syncChips();
            renderTagCloud();
            renderImages();
        }

        // Wire up interactions
        document.getElementById('vis-search').addEventListener('input', e => {
            activeQuery = e.target.value.trim().toLowerCase();
            renderAll();
        });
        document.body.addEventListener('click', e => {
            const catBtn = e.target.closest('[data-vis-cat]');
            if (catBtn) {
                const v = catBtn.dataset.visCat;
                activeCat = (activeCat === v) ? '' : v;
                if (activeTag && tagBySlug[activeTag] && activeCat && tagBySlug[activeTag].category !== activeCat) activeTag = '';
                renderAll();
                return;
            }
            const workBtn = e.target.closest('[data-vis-work]');
            if (workBtn) {
                const v = workBtn.dataset.visWork;
                activeWork = (activeWork === v) ? '' : v;
                renderAll();
                return;
            }
            const tagBtn = e.target.closest('[data-vis-tag]');
            if (tagBtn && !e.target.closest('.vis-tag-dict-link')) {
                e.preventDefault();
                const v = tagBtn.dataset.visTag;
                activeTag = (activeTag === v) ? '' : v;
                renderAll();
                return;
            }
        });
        window.addEventListener('hashchange', () => {
            activeTag = ''; activeCat = ''; activeWork = ''; activeQuery = '';
            document.getElementById('vis-search').value = '';
            readHash();
            renderAll();
        });
        readHash();
        renderAll();
    })();
    </script>"""
    html = page_shell('Visual Browser', body, active_nav='Visual')
    (SITE_DIR / 'visual.html').write_text(html, encoding='utf-8')
    print(f"  visual.html + visual-data.json: {len(image_entries)} images, {len(tag_entries)} tags, {image_tag_count} links")


# ============================================================
# Per-Stage Gallery Pages
# ============================================================

STAGE_DEFINITIONS = {
    'NIGREDO': {
        'name': 'Nigredo',
        'subtitle': 'The Blackening',
        'bg': '#2c2418',
        'fg': '#f5f0e8',
        'accent': '#8b4513',
        'epigraph': '"Putrefaction is the death of bodies and the cause of generation." — pseudo-Geber, Summa Perfectionis',
        'description': 'The first stage of the Great Work: putrefaction, blackening, and the death of the prima materia. Saturn presides; black bile and melancholy mark the body. The matter must die before it can be reborn. In Atalanta Fugiens this is the work of dragons devouring their tails (XIV), the king drowning (XXXI), the dragon-and-woman mortal embrace (L), the slaying of Osiris (XLIV).',
        'related_terms': ['nigredo', 'putrefaction', 'mortificatio', 'calcination', 'dissolution', 'prima-materia', 'kronos-saturn', 'raven-crow', 'screech-owl'],
    },
    'ALBEDO': {
        'name': 'Albedo',
        'subtitle': 'The Whitening',
        'bg': '#a89880',
        'fg': '#2c2418',
        'accent': '#8b4513',
        'epigraph': '"Make Latona white and tear up the books." — Atalanta Fugiens, motto of Emblem XI',
        'description': 'The second stage: purification by washing, sublimation, and distillation. The Moon presides; phlegmatic constitution restored; matter purified to lunar silver. In Atalanta Fugiens this is the washerwoman of Emblem III, the whitening of Latona (XI–XII), the white-lead cooking of Emblem XXII, the sowing of gold in white earth (VI).',
        'related_terms': ['albedo', 'sublimatio', 'distillatio', 'solutio', 'luna', 'lac-virginis', 'white-lead'],
    },
    'CITRINITAS': {
        'name': 'Citrinitas',
        'subtitle': 'The Yellowing',
        'bg': '#b8860b',
        'fg': '#2c2418',
        'accent': '#c0392b',
        'epigraph': '"As white silver yields to yellowing gold, so the soul moves from clarity into wisdom." — composite alchemical commonplace',
        'description': 'The transitional third stage between albedo and rubedo: the matter takes on a golden hue as solar virtue infiltrates the lunar substance. Yellow bile, choleric vigor, dawn light, the rising sun. Often elided in later texts as Jung favored a triadic schema, but historically attested by Maier, Mylius, and the Rosarium tradition.',
        'related_terms': ['citrinitas', 'fermentatio', 'circulatio', 'aurum-philosophicum', 'sol'],
    },
    'RUBEDO': {
        'name': 'Rubedo',
        'subtitle': 'The Reddening',
        'bg': '#c0392b',
        'fg': '#f5f0e8',
        'accent': '#fbe8a0',
        'epigraph': '"The Stone is red as blood, soft as wax, heavy as gold." — pseudo-Lull, Testamentum',
        'description': 'The fourth and final stage: the white stone is reddened by fermentation with gold to produce the Philosopher\'s Stone or Red Tincture. Sol presides; sanguine vitality perfected; the chemical wedding consummated; the Rebis-hermaphrodite achieved. In Atalanta Fugiens this is the staining of white roses by Adonis\'s blood (XLI), the standing hermaphrodite (XXXVIII), the multiplication of the Stone.',
        'related_terms': ['rubedo', 'coagulation', 'fixatio', 'multiplicatio', 'projectio', 'philosopher-s-stone', 'lapis', 'rebis', 'sol', 'hermaphrodite', 'alchemical-rose'],
    },
}


def build_stage_pages(conn):
    """One landing page + four per-stage deep pages combining:
    - Atalanta emblems classified to this stage
    - Cross-corpus images tagged with this stage's processes (from visual-data.json)
    - Dictionary terms in this stage's register cluster
    """
    stage_dir = SITE_DIR / 'stage'
    stage_dir.mkdir(exist_ok=True)

    # Load visual-data for cross-corpus images
    visual_data_path = SITE_DIR / 'visual-data.json'
    cross_corpus_images = []
    if visual_data_path.exists():
        try:
            cross_corpus_images = json.loads(visual_data_path.read_text(encoding='utf-8')).get('images', [])
        except Exception:
            cross_corpus_images = []

    # Identity map for emblem images
    identity_map = load_identity_map(conn)

    # Stage emblem counts for the index
    stage_counts = dict(conn.execute(
        "SELECT alchemical_stage, COUNT(*) FROM emblems WHERE alchemical_stage IS NOT NULL AND alchemical_stage != '' GROUP BY alchemical_stage"
    ).fetchall())

    # ── Index page ──
    cards_html = ''
    for stage_key in ['NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO']:
        stage = STAGE_DEFINITIONS[stage_key]
        n = stage_counts.get(stage_key, 0)
        cards_html += f"""
        <a href="{stage_key.lower()}.html" class="card stage-card" style="text-decoration:none;color:inherit;background:{stage['bg']};color:{stage['fg']}">
            <div class="card-body" style="padding:1.5rem">
                <div style="font-family:var(--font-serif);font-size:2rem;line-height:1;margin-bottom:0.4rem">{stage['name']}</div>
                <div style="font-family:var(--font-sans);font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;opacity:0.8;margin-bottom:0.6rem">{stage['subtitle']}</div>
                <div style="font-size:0.92rem;line-height:1.55">{stage['description'][:220]}…</div>
                <div style="margin-top:0.8rem;font-size:0.78rem;opacity:0.75;font-family:var(--font-sans)">{n} Atalanta emblem{'s' if n != 1 else ''} · related dictionary terms · cross-corpus images</div>
            </div>
        </a>"""
    index_body = f"""
    <div class="page-content" style="max-width:1100px">
        <h2>The Four Stages of the Great Work</h2>
        <p style="font-size:0.95rem">Alchemy traditionally distinguishes four colour-coded phases of the opus: nigredo (blackening), albedo (whitening), citrinitas (yellowing), and rubedo (reddening). Each stage gathers its own characteristic imagery, processes, and emblem subjects. Browse them as relational tours through Atalanta Fugiens and the wider alchemical corpus.</p>
        <div class="gallery" style="grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));padding:0;margin-top:1.5rem">{cards_html}</div>
    </div>"""
    html = page_shell('Stages of the Great Work', index_body, active_nav='Stages', depth=1)
    (stage_dir / 'index.html').write_text(html, encoding='utf-8')

    # ── Per-stage deep pages ──
    # Pre-fetch all dictionary terms once
    dict_terms = {
        r[0]: {'label': r[1], 'cat': r[2], 'def_short': r[3]}
        for r in conn.execute(
            "SELECT slug, label, category, definition_short FROM dictionary_terms"
        ).fetchall()
    }

    for stage_key in ['NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO']:
        stage = STAGE_DEFINITIONS[stage_key]

        # Atalanta emblems for this stage
        emblems_for = conn.execute(
            """SELECT id, number, roman_numeral, canonical_label, motto_english
               FROM emblems
               WHERE alchemical_stage = ? AND number > 0
               ORDER BY number""",
            (stage_key,)
        ).fetchall()
        emblem_cards_html = ''
        for em in emblems_for:
            _eid, num_, roman_, label_, motto_ = em
            img_path, img_exists = resolve_image(identity_map, num_)
            img_tag = (
                f'<img src="../{img_path}" alt="Emblem {roman_ or num_}" loading="lazy" style="width:100%;display:block;aspect-ratio:auto">'
                if img_exists else
                f'<div class="card-placeholder" style="aspect-ratio:1;font-size:1.6rem">{roman_ or num_}</div>'
            )
            emblem_cards_html += f"""
            <a href="../emblems/emblem-{num_:02d}.html" class="card" style="text-decoration:none;color:inherit">
                {img_tag}
                <div class="card-body">
                    <div class="card-sig">Emblem {roman_ or num_}</div>
                    <div class="card-label">{label_ or ''}</div>
                    <div class="card-desc">{(motto_ or '').strip()}</div>
                </div>
            </a>"""

        # Cross-corpus images tagged with any of this stage's process tags
        stage_process_tags = set(STAGE_TO_PROCESS_TAGS.get(stage_key, []))
        cross_imgs = []
        for ie in cross_corpus_images:
            if not ie.get('tags'):
                continue
            if stage_process_tags & set(ie['tags']):
                # Skip Atalanta — already shown above
                if ie['work'] == 'atalanta_fugiens':
                    continue
                cross_imgs.append(ie)

        cross_cards_html = ''
        for ie in cross_imgs[:30]:
            link_attrs = ''
            if ie['link_url']:
                href = ie['link_url'] if ie['is_external'] else ('../' + ie['link_url'])
                link_attrs = f'href="{href}"' + (' target="_blank" rel="noopener"' if ie['is_external'] else '')
                tag_open = f'<a {link_attrs} class="card" style="text-decoration:none;color:inherit">'
                tag_close = '</a>'
            else:
                tag_open = '<div class="card" style="cursor:default">'
                tag_close = '</div>'
            if ie['local_url']:
                src = ie['local_url'] if ie['is_external'] else ('../' + ie['local_url'])
                img_tag = f'<img src="{src}" alt="" loading="lazy" style="width:100%;display:block;aspect-ratio:auto">'
            else:
                folio_label = (ie['folio'] or '').replace('plate ', '').upper() or '?'
                img_tag = f'<div class="card-placeholder" style="aspect-ratio:1;font-size:1.4rem">{folio_label}</div>'
            cross_cards_html += (
                tag_open + img_tag + '<div class="card-body">'
                f'<div class="card-sig" style="font-size:0.78rem">{ie.get("work_title", "")}</div>'
                f'<div class="card-desc" style="font-size:0.78rem">{(ie.get("snippet") or "")[:120]}</div>'
                + '</div>' + tag_close
            )
        cross_overflow = ''
        if len(cross_imgs) > 30:
            # Build a visual-browser hash that filters for any process tag of this stage
            tag_param = STAGE_TO_PROCESS_TAGS.get(stage_key, [stage_key.lower()])[0]
            cross_overflow = f'<p style="grid-column:1/-1;color:var(--text-muted);font-style:italic;padding:1rem;font-size:0.88rem">…and {len(cross_imgs) - 30} more — open <a href="../visual.html#tag={tag_param}">all {tag_param} images</a> in the visual browser.</p>'

        # Related dictionary terms
        term_cards_html = ''
        for slug in stage['related_terms']:
            term = dict_terms.get(slug)
            if not term:
                continue
            term_cards_html += f"""
            <a href="../dictionary/{slug}.html" class="dict-related-card">
                <div class="dict-related-label">{term['label']}</div>
                <div class="dict-related-latin" style="text-transform:uppercase;letter-spacing:0.04em">{term['cat']}</div>
            </a>"""

        # Process tag jump links to visual browser
        proc_chip_html = ''
        for proc_tag in STAGE_TO_PROCESS_TAGS.get(stage_key, []):
            proc_chip_html += f'<a href="../visual.html#tag={proc_tag}" class="vis-tag-chip" style="border-color:#16a085;color:#16a085;text-decoration:none">{proc_tag}</a> '

        body = f"""
        <div class="page-content" style="max-width:1200px">
            <a href="index.html" class="back-link">&larr; All Stages</a>
            <div class="stage-banner" style="background:{stage['bg']};color:{stage['fg']};padding:2rem 1.5rem;border-radius:6px;margin-bottom:1.5rem">
                <div style="font-family:var(--font-sans);font-size:0.78rem;text-transform:uppercase;letter-spacing:0.1em;opacity:0.7;margin-bottom:0.3rem">Stage of the Great Work</div>
                <h1 style="font-size:2.4rem;margin:0 0 0.4rem">{stage['name']}</h1>
                <div style="font-family:var(--font-sans);font-size:1.05rem;opacity:0.85">{stage['subtitle']}</div>
                <p style="font-style:italic;font-size:0.9rem;opacity:0.85;margin-top:1rem;border-left:2px solid currentColor;padding-left:0.8rem">{stage['epigraph']}</p>
            </div>
            <p style="font-size:0.95rem;line-height:1.7;margin-bottom:1.5rem">{stage['description']}</p>

            <h2>Atalanta Fugiens emblems classified to {stage['name']} <span class="badge badge-contextual">{len(emblems_for)}</span></h2>
            <p style="font-size:0.85rem;color:var(--text-muted)"><a href="../index.html#stage={stage_key}">Open the gallery filtered to {stage['name']} →</a></p>
            <div class="gallery" style="grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));padding:0;margin-bottom:1.5rem">{emblem_cards_html}</div>

            {f'<h2>Across the broader corpus <span class="badge badge-contextual">{len(cross_imgs)}</span></h2>' if cross_imgs else ''}
            {f'<p style="font-size:0.85rem;color:var(--text-muted)">Plates from other emblem books tagged with {stage["name"].lower()}-phase processes.</p>' if cross_imgs else ''}
            {f'<div class="gallery" style="grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));padding:0;margin-bottom:1.5rem">{cross_cards_html}{cross_overflow}</div>' if cross_imgs else ''}

            {f'<h2>Process tags <span class="badge badge-contextual">{len(STAGE_TO_PROCESS_TAGS.get(stage_key, []))}</span></h2><p style="font-size:0.85rem;color:var(--text-muted)">Click to see all images of each process across every emblem book.</p><div style="display:flex;flex-wrap:wrap;gap:0.4rem;padding:0.6rem;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;margin-bottom:1.5rem">{proc_chip_html}</div>' if proc_chip_html else ''}

            {f'<h2>Related dictionary terms <span class="badge badge-contextual">{sum(1 for s in stage["related_terms"] if s in dict_terms)}</span></h2><div class="dict-related" style="margin-bottom:1.5rem">{term_cards_html}</div>' if term_cards_html else ''}
        </div>"""
        html = page_shell(f"{stage['name']} — Stages of the Great Work", body, active_nav='Stages', depth=1)
        (stage_dir / f"{stage_key.lower()}.html").write_text(html, encoding='utf-8')

    print(f"  stage/: 4 stage pages + index")


# ============================================================
# Main
# ============================================================

def main():
    conn = sqlite3.connect(DB_PATH)
    print("Building site...")
    identity_map = load_identity_map(conn)
    export_data_json(conn, identity_map)
    build_gallery(conn)
    build_emblem_pages(conn, identity_map)
    build_scholars_pages(conn)
    build_bibliography(conn)
    build_dictionary_pages(conn)
    build_timeline(conn)
    build_sources(conn, identity_map)
    # build_essays(conn)  # Replaced by build_essay_pages
    build_modern_scholarship(conn)
    build_maier_page(conn)
    build_creatures_page()
    build_essay_pages(conn)
    build_works_page()
    build_szulakowska_page()
    build_music_page()
    build_biography()
    build_about(conn)
    build_visual_browser(conn)
    build_stage_pages(conn)
    build_search(conn)
    conn.close()
    print("Site build complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
