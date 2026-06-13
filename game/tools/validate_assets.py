"""
validate_assets.py -- catch the "invisible monster" class of bug.

The game requests sprites by name (data.js MONSTERS[*].sprite / CLASSES[*].sprite,
the tile->sprite map in world.js, and direct Assets.img('name') calls). assets.js
only console.warn()s on a miss and draws nothing, so a typo or a dropped manifest
entry ships a monster you can't see until you fight it on floor 9.

This validator resolves every name the game actually requests against
game/assets/manifest.json and the sprite files on disk. It exits non-zero on any
HARD failure so it can gate a build/deploy.

Checks:
  HARD  every requested sprite name exists in manifest.json
  HARD  every manifest entry's output .png exists on disk
  WARN  every manifest 'src' (original source) still exists (regen safety)
  INFO  manifest entries never referenced in js/ (possible orphans)

Run:  python game/tools/validate_assets.py
"""
import os, re, json, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # EmblemPrintShop
GAME = os.path.join(ROOT, 'game')
JS   = os.path.join(GAME, 'js')


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def requested_names():
    """Names the game asks for, gathered at the real access points (no prefix guessing)."""
    refs = {}  # name -> set(source locations)

    def add(name, where):
        refs.setdefault(name, set()).add(where)

    # 1) data.js -- monster + class sprite fields
    data = read(os.path.join(JS, 'data.js'))
    for m in re.finditer(r"sprite:\s*'([^']+)'", data):
        add(m.group(1), 'data.js sprite:')

    # 2) world.js -- the tile -> sprite map values (s_* / t_*)
    world = read(os.path.join(JS, 'world.js'))
    for m in re.finditer(r":\s*'((?:s_|t_)[a-z0-9_]+)'", world):
        add(m.group(1), 'world.js tile-map')

    # 3) any js -- quoted tokens on lines that call .img( or .meta(
    #    (covers Assets.img('d_sun'), img('hero'), and the q_king/q_queen ternary)
    for path in glob.glob(os.path.join(JS, '*.js')):
        base = os.path.basename(path)
        for line in read(path).splitlines():
            if '.img(' in line or '.meta(' in line:
                for m in re.finditer(r"'([a-z0-9_]+)'", line):
                    add(m.group(1), base + ' img()/meta()')
    return refs


def validate():
    """Return (hard, warn, info, stats). hard != [] means the build should fail."""
    manifest = json.loads(read(os.path.join(GAME, 'assets', 'manifest.json')))
    names = {rec['name'] for rec in manifest}

    hard = []   # (msg)
    warn = []
    info = []

    # HARD: requested -> must be in manifest
    refs = requested_names()
    for name, where in sorted(refs.items()):
        if name not in names:
            hard.append("requested sprite '%s' is NOT in manifest  (used in: %s)"
                        % (name, ', '.join(sorted(where))))

    # HARD: manifest output png must exist on disk
    for rec in manifest:
        png = os.path.join(GAME, rec['file'].replace('/', os.sep))
        if not os.path.exists(png):
            hard.append("manifest entry '%s' -> output file missing: %s" % (rec['name'], rec['file']))

    # WARN: original source must still exist (so the sprite can be regenerated)
    for rec in manifest:
        src = rec.get('src')
        if not src:
            continue
        srcp = os.path.join(ROOT, src.replace('/', os.sep))
        if not os.path.exists(srcp):
            warn.append("manifest entry '%s' -> SOURCE missing, cannot regen: %s" % (rec['name'], src))

    # INFO: manifest names never quoted anywhere in js/ (possible orphans)
    alljs = '\n'.join(read(p) for p in glob.glob(os.path.join(JS, '*.js')))
    for name in sorted(names):
        if ("'%s'" % name) not in alljs:
            info.append("manifest entry '%s' is never referenced in js/ (orphan?)" % name)

    # sprite-file count excludes QA artifacts like _SHEET.png
    sprite_files = [p for p in glob.glob(os.path.join(GAME, 'assets', 'sprites', '*.png'))
                    if not os.path.basename(p).startswith('_')]
    stats = {'entries': len(manifest), 'sprites': len(sprite_files), 'requested': len(refs)}
    return hard, warn, info, stats


def report(hard, warn, info, stats):
    print("Emblem Knight -- asset validation")
    print("  manifest entries: %d   sprite files: %d   requested names: %d"
          % (stats['entries'], stats['sprites'], stats['requested']))
    print()
    for label, items in (('HARD', hard), ('WARN', warn), ('INFO', info)):
        if items:
            print("[%s] %d" % (label, len(items)))
            for it in items:
                print("   - " + it)
            print()
    if not hard and not warn:
        print("OK -- every requested sprite resolves and every output file is present.")


def main():
    hard, warn, info, stats = validate()
    report(hard, warn, info, stats)
    sys.exit(1 if hard else 0)


if __name__ == '__main__':
    main()
