import os
from PIL import Image, ImageDraw
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

picks = [
 ('HERO?a', r'assets\extracted_all\splendor_solis_local_p0013\individual\man_old_man_transparent.png'),
 ('HERO?b', r'assets\extracted_all\mclean_second_p0025\individual\person_transparent.png'),
 ('HERO?c', r'assets\extracted_all\splendor_solis_ia_p0019\individual\person_transparent.png'),
 ('HERO?d', r'assets\extracted_all\stolcius_plate_013\individual\person_transparent.png'),
 ('KING',   r'assets\extracted_all\emblem-47\individual\angel_king_man_witch_transparent.png'),
 ('beast:dog', r'assets\extracted_all\stolcius_plate_006\individual\dog_transparent.png'),
 ('beast:wolf', r'assets\extracted_all\splendor_solis_ia_p0019\individual\wolf_frog_transparent.png'),
 ('beast:bearC', r'assets\extracted_all\emblem-24\individual\bear_ox_frog_transparent.png'),
 ('beast:eagleDragon', r'assets\extracted_all\splendor_solis_local_p0020\individual\eagle_dragon_peacock_transparent.png'),
 ('beast:wolfFoxC', r'assets\extracted_all\splendor_solis_local_p0008\individual\wolf_frog_fox_transparent.png'),
 ('bird:eagle', r'assets\extracted_all\splendor_solis_ia_p0054\individual\eagle_bird_butterfly_transparent.png'),
 ('bird:swan', r'assets\extracted_all\mclean_second_p0009\individual\eagle_transparent.png'),
 ('bird:colorA', r'assets\extracted_all\splendor_solis_ia_p0035\individual\wolf_lamb_frog_transparent.png'),
 ('castle:big', r'assets\extracted_all\stolcius_plate_002\individual\castle_transparent.png'),
 ('castle:claud', r'assets\extracted_all\emblem-28\individual\tower_chimney_transparent.png'),
 ('tower:cramer', r'assets\extracted_all\cramer_page_0077\individual\tower_transparent.png'),
 ('gate:bridge', r'assets\extracted_all\mclean_second_p0050\individual\gate_bridge_transparent.png'),
 ('door', r'assets\extracted_all\emblem-08\individual\door_transparent.png'),
 ('sun', r'assets\extracted_all\claudiens'.replace('claudiens','') + r'extracted_all'),  # placeholder removed below
]
picks = [p for p in picks if 'placeholder' not in p[1] and os.path.exists(p[1])]

def alpha_crop(im):
    a = np.array(im.convert('RGBA'))[:, :, 3]
    ys, xs = np.where(a > 16)
    if len(xs) == 0: return im
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    return im.crop((int(x0), int(y0), int(x1)+1, int(y1)+1))

cell, cols = 250, 5
rows = (len(picks)+cols-1)//cols
sheet = Image.new('RGBA', (cols*cell, rows*cell), (35,35,45,255))
dr = ImageDraw.Draw(sheet)
for i, (name, p) in enumerate(picks):
    try:
        im = alpha_crop(Image.open(p).convert('RGBA'))
        im.thumbnail((cell-20, cell-30))
        cx, cy = (i%cols)*cell, (i//cols)*cell
        bg = Image.new('RGBA', (im.width, im.height), (250,248,240,255))
        bg.alpha_composite(im)
        sheet.alpha_composite(bg, (cx+10, cy+6))
        dr.text((cx+6, cy+cell-16), f"{i}:{name}", fill=(255,255,160,255))
    except Exception as e:
        dr.text((10+(i%cols)*cell, 10+(i//cols)*cell), f"ERR {name}", fill=(255,80,80,255))
sheet.convert('RGB').save(os.path.join('game','_curation','FINALISTS.png'))
print('ok', len(picks))
