"""
cast.py -- cast Emblem Knight sprites from the 6,201 extracted cutouts by motif,
instead of hunting for file paths by hand.

Every individual extraction under assets/extracted_all/*/individual/ has a
*_meta.json carrying a label, category, detection score, and mask_pixel_count.
This tool indexes them all and ranks candidates for a motif so you can audition
a "wolf" or "dragon" in seconds and emit a ready-to-paste build_assets MANIFEST
entry pointing at the winner.

Ranking blends confidence and substance:  score * sqrt(mask_pixel_count)
so a big, clearly-detected subject beats a tiny confident fragment.

Usage:
  python game/tools/cast.py wolf                 # top candidates labelled "wolf"
  python game/tools/cast.py "wolf,fox,hound"     # any of several synonyms
  python game/tools/cast.py lion --cat figures   # restrict by category
  python game/tools/cast.py dragon --top 15 --min-px 8000
  python game/tools/cast.py dragon --emit m_dragon --kind monster --size 300
  python game/tools/cast.py --reindex            # rebuild the cache

The cache lives at game/tools/.cast_index.json (delete or --reindex to refresh).
"""
import os, re, json, glob, math, argparse

ROOT  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # EmblemPrintShop
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cast_index.json')


def rel(p):
    """Absolute (possibly Windows backslash) path -> forward-slash path relative to ROOT."""
    p = p.replace('\\', '/')
    r = ROOT.replace('\\', '/')
    if p.lower().startswith(r.lower()):
        p = p[len(r):].lstrip('/')
    return p


def build_index():
    recs = []
    metas = glob.glob(os.path.join(ROOT, 'assets', 'extracted_all', '*', 'individual', '*_meta.json'))
    for mp in metas:
        try:
            with open(mp, encoding='utf-8') as f:
                m = json.load(f)
        except Exception:
            continue
        tp = m.get('transparent_png')
        if not tp:
            continue
        bbox = m.get('tight_bbox') or m.get('det_bbox') or [0, 0, 1, 1]
        w, h = max(1, bbox[2]), max(1, bbox[3])
        recs.append({
            'label':    (m.get('label') or '').lower(),
            'category': (m.get('category') or '').lower(),
            'score':    float(m.get('score') or 0.0),
            'px':       int(m.get('mask_pixel_count') or 0),
            'aspect':   round(w / h, 2),
            'work':     os.path.basename(os.path.dirname(os.path.dirname(mp))),
            'src':      rel(tp),
        })
    with open(CACHE, 'w', encoding='utf-8') as f:
        json.dump(recs, f)
    return recs


def load_index(reindex=False):
    if reindex or not os.path.exists(CACHE):
        print('indexing extracted cutouts ...')
        recs = build_index()
        print('indexed %d individual cutouts -> %s' % (len(recs), rel(CACHE)))
        return recs
    with open(CACHE, encoding='utf-8') as f:
        return json.load(f)


def rank(recs, terms, cat, min_px, min_score):
    terms = [t.strip().lower() for t in terms if t.strip()]
    out = []
    for r in recs:
        if r['px'] < min_px or r['score'] < min_score:
            continue
        if cat and r['category'] != cat:
            continue
        words = set(re.split(r'[\s_]+', r['label']))
        exact = any(t in words for t in terms)
        sub   = any(t in r['label'] for t in terms)
        if not sub:
            continue
        key = r['score'] * math.sqrt(r['px']) * (1.5 if exact else 1.0)
        out.append((key, exact, r))
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def emit(name, kind, size, rec):
    is_jpg = rec['src'].lower().endswith(('.jpg', '.jpeg'))
    bg = 'paper' if (is_jpg or 'transparent' not in rec['src']) else 'paper'
    print("\n# paste into build_assets.py MANIFEST (then: python game/tools/build_assets.py):")
    print(" dict(name='%s', kind='%s', label='%s'," % (name, kind, rec['label'].title()))
    print("      src=r'%s'," % rec['src'].replace('/', '\\'))
    print("      bg='%s', size=%d)," % (bg, size))
    print("# source: %s  (score %.2f, %d px, aspect %.2f)" % (rec['work'], rec['score'], rec['px'], rec['aspect']))


def main():
    ap = argparse.ArgumentParser(description='Cast Emblem Knight sprites from extracted cutouts by motif.')
    ap.add_argument('query', nargs='?', default='', help='motif term(s), comma-separated synonyms ok')
    ap.add_argument('--top', type=int, default=10)
    ap.add_argument('--cat', default='', help='restrict to a category (figures, objects, architecture, plants, landscape ...)')
    ap.add_argument('--min-px', type=int, default=4000, help='drop fragments smaller than this mask area')
    ap.add_argument('--min-score', type=float, default=0.0)
    ap.add_argument('--emit', metavar='SPRITE_NAME', help='print a MANIFEST entry for the top hit')
    ap.add_argument('--kind', default='monster', help='kind for --emit (hero|npc|monster|structure|terrain|decor)')
    ap.add_argument('--size', type=int, default=240, help='longest-edge px for --emit')
    ap.add_argument('--pick', type=int, default=1, help='which ranked hit to --emit (1 = best)')
    ap.add_argument('--reindex', action='store_true')
    args = ap.parse_args()

    recs = load_index(reindex=args.reindex)
    if not args.query:
        if args.reindex:
            return
        ap.error('give a motif query, e.g.  python game/tools/cast.py wolf')

    ranked = rank(recs, args.query.split(','), args.cat.lower().strip(), args.min_px, args.min_score)
    if not ranked:
        print("no candidates for '%s' (try a broader term, lower --min-px, or --reindex)" % args.query)
        return

    print("candidates for '%s'  (%d matches, showing %d)\n" % (args.query, len(ranked), min(args.top, len(ranked))))
    print("  #  score   px       aspect cat          work                      label")
    print("  -- ------- -------- ------ ------------ ------------------------- -----")
    for i, (_, exact, r) in enumerate(ranked[:args.top], 1):
        print("  %-2d %.3f   %-8d %-6.2f %-12s %-25s %s%s"
              % (i, r['score'], r['px'], r['aspect'], r['category'][:12], r['work'][:25],
                 r['label'], '  *exact' if exact else ''))

    if args.emit:
        idx = max(1, args.pick) - 1
        if idx < len(ranked):
            emit(args.emit, args.kind, args.size, ranked[idx][2])


if __name__ == '__main__':
    main()
