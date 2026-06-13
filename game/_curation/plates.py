import os, glob
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

def grid(name, files, cols=5, cell=240):
    files = sorted(files)
    rows = max(1, (len(files)+cols-1)//cols)
    sheet = Image.new('RGB', (cols*cell, rows*cell), (30, 30, 38))
    dr = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        try:
            im = Image.open(f).convert('RGB')
            im.thumbnail((cell-12, cell-26))
            cx, cy = (i % cols)*cell, (i//cols)*cell
            sheet.paste(im, (cx+6+(cell-12-im.width)//2, cy+6))
            dr.text((cx+6, cy+cell-18), os.path.basename(f).replace('.jpg', ''), fill=(255, 230, 150))
        except Exception:
            pass
    out = f'game/_curation/plates_{name}.png'
    sheet.save(out)
    print(name, len(files), '->', out)

grid('ROSARIUM', glob.glob('sources/rosarium/images/*.jpg'))
grid('SPLENDOR', glob.glob('sources/splendor_solis/images/*.jpg'))
