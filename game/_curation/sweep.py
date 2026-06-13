"""Comprehensive curation sweep: build metric-annotated contact sheets for
dragons, quadrupeds (lions hide here), birds, and landscapes."""
import json, os, sys
from PIL import Image, ImageDraw
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
d = json.load(open('prototype/gallery_catalog.json'))
recs = d['records']

def g(r, k): return (r.get(k) or '')
def ok(r):
    p = r.get('transparent_png', '')
    return p and os.path.exists(os.path.join('.', p))
def path(r): return os.path.join('.', r['transparent_png'])

def alpha_info(im):
    a = np.array(im.convert('RGBA'))[:, :, 3]
    ys, xs = np.where(a > 16)
    if len(xs) == 0:
        return None
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    bw, bh = x1-x0+1, y1-y0+1
    cov = (bw*bh) / (im.width*im.height)          # how much of canvas the subject bbox fills
    fill = len(xs) / (bw*bh)                        # how solid the bbox is (paper-removed -> lower)
    return im.crop((x0, y0, x1+1, y1+1)), bw, bh, cov, fill

def build(name, records, cols=4, cell=250, max_n=16):
    records = records[:max_n]
    rows = max(1, (len(records)+cols-1)//cols)
    sheet = Image.new('RGBA', (cols*cell, rows*cell), (38, 36, 48, 255))
    dr = ImageDraw.Draw(sheet)
    idx = []
    for i, r in enumerate(records):
        try:
            im = Image.open(path(r)).convert('RGBA')
            info = alpha_info(im)
            if not info: continue
            crop, bw, bh, cov, fill = info
            crop.thumbnail((cell-20, cell-40))
            cx, cy = (i % cols)*cell, (i//cols)*cell
            bg = Image.new('RGBA', (crop.width, crop.height), (250, 248, 240, 255))
            bg.alpha_composite(crop)
            sheet.alpha_composite(bg, (cx+10, cy+6))
            flag = 'PLATE' if cov > 0.5 else 'iso'
            col = (255, 140, 140, 255) if cov > 0.5 else (150, 255, 150, 255)
            dr.text((cx+4, cy+cell-32), f"{i}:{g(r,'object_label')[:15]}", fill=(255, 235, 150, 255))
            dr.text((cx+4, cy+cell-20), f"{r.get('project_key')} {bw}x{bh}", fill=(170, 210, 255, 255))
            dr.text((cx+4, cy+cell-9), f"{flag} cov{cov:.2f}", fill=col)
            idx.append((i, r['transparent_png'], g(r, 'object_label'), r.get('project_key'), round(cov, 2)))
        except Exception:
            pass
    sheet.convert('RGB').save(f'game/_curation/sweep_{name}.png')
    with open(f'game/_curation/sweep_{name}.txt', 'w', encoding='utf-8') as f:
        for row in idx:
            f.write('\t'.join(str(x) for x in row)+'\n')
    print(f'{name}: {len(idx)} tiles')

def pool(pred):
    out = [r for r in recs if ok(r) and pred(r)]
    out.sort(key=lambda r: -(r.get('score') or 0))
    return out

def has_tag(r, tags): return bool(set(r.get('tags') or []) & tags)
def lbl(r): return g(r, 'object_label').lower()

# DRAGONS — tag dragon or serpent, exclude obrist manuscript blobs by preferring others
drag = pool(lambda r: (has_tag(r, {'dragon','serpent'}) or 'dragon' in lbl(r) or 'serpent' in lbl(r)))
# put non-obrist first (obrist dragon extractions were bad manuscript pages)
drag.sort(key=lambda r: (r.get('project_key') == 'obrist', -(r.get('score') or 0)))
build('DRAGON', drag)

# QUADRUPEDS — lions hide under these
quad = pool(lambda r: r.get('category') == 'animals' and has_tag(r, {'dog','bear','ox','fox','wolf','lamb','deer','horse','hare'}))
build('QUADRUPED', quad)

# BIRDS
bird = pool(lambda r: r.get('category') == 'animals' and has_tag(r, {'eagle','bird','dove','peacock','phoenix'}))
build('BIRD', bird)

# LANDSCAPES
land = pool(lambda r: r.get('category') == 'landscape' and has_tag(r, {'mountain','hill','cliff','cave','forest','tree','rock','river','bridge','sea'}))
build('LAND', land)

print('done')
