import json, os
from PIL import Image, ImageDraw
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

d = json.load(open('prototype/gallery_catalog.json'))
recs = d['records']

def g(r, k): return r.get(k) or ''
def path(r): return os.path.join('.', r.get('transparent_png', ''))
def ok(r):
    p = r.get('transparent_png', '')
    return p and os.path.exists(os.path.join('.', p))

def alpha_crop(im):
    a = np.array(im.convert('RGBA'))[:, :, 3]
    ys, xs = np.where(a > 16)
    if len(xs) == 0: return None
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    return im.crop((int(x0), int(y0), int(x1)+1, int(y1)+1)), int(x1-x0+1), int(y1-y0+1)

def pool(pred, n):
    out = [r for r in recs if ok(r) and pred(r)]
    out.sort(key=lambda r: -(r.get('score') or 0))
    return out[:n]

cats = {
 'KNIGHT': pool(lambda r: r.get('category') == 'figures' and any(k in g(r,'object_label').lower() for k in ['man','king','person','soldier']), 18),
 'BEAST':  pool(lambda r: r.get('category') == 'animals' and (set(r.get('tags') or []) & {'lion','bear','wolf','dog','fox','dragon','frog','toad'}), 18),
 'BIRD':   pool(lambda r: r.get('category') == 'animals' and (set(r.get('tags') or []) & {'eagle','bird','dove','peacock'}), 12),
 'CASTLE': pool(lambda r: r.get('category') == 'architecture', 18),
 'LAND':   pool(lambda r: r.get('category') == 'landscape', 18),
 'DRAGON': pool(lambda r: 'dragon' in g(r,'object_label').lower() or (r.get('project_key')=='obrist' and 'medieval_alchemical' in r.get('transparent_png','')), 18),
}

outdir = os.path.join('game', '_curation')
os.makedirs(outdir, exist_ok=True)
for name, rs in cats.items():
    cell, cols = 160, 6
    rows = max(1, (len(rs)+cols-1)//cols)
    sheet = Image.new('RGBA', (cols*cell, rows*cell), (40,40,50,255))
    dr = ImageDraw.Draw(sheet)
    for i, r in enumerate(rs):
        try:
            im = Image.open(path(r)).convert('RGBA')
            cr = alpha_crop(im)
            if cr is None: continue
            cim, w, h = cr
            cim.thumbnail((cell-24, cell-34))
            cx, cy = (i%cols)*cell, (i//cols)*cell
            bg = Image.new('RGBA', (cim.width, cim.height), (250,248,240,255))
            bg.alpha_composite(cim)
            sheet.alpha_composite(bg, (cx+12, cy+6))
            dr.text((cx+4, cy+cell-26), f"{i}:{g(r,'object_label')[:14]} {round(r.get('score',0),2)}", fill=(255,255,180,255))
            dr.text((cx+4, cy+cell-14), f"{r.get('project_key')} {w}x{h}", fill=(180,220,255,255))
        except Exception:
            pass
    sheet.convert('RGB').save(os.path.join(outdir, f'sheet_{name}.png'))
    with open(os.path.join(outdir, f'idx_{name}.txt'), 'w') as f:
        for i, r in enumerate(rs):
            f.write(f"{i}\t{r.get('transparent_png')}\t{g(r,'object_label')}\t{r.get('score')}\n")
    print('wrote', name, len(rs))
