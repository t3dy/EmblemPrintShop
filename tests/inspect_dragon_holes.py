"""Inspect the connected background regions inside the dragon mask for emblem-14."""
import cv2, numpy as np
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).parent.parent
png = PROJECT / "assets/extracted/emblem-14_dragon_serpent_transparent.png"

if not png.exists():
    # Try other naming patterns
    candidates = list((PROJECT / "assets/extracted").glob("emblem-14_*_transparent.png"))
    if candidates:
        png = candidates[-1]
    else:
        print("No emblem-14 transparent PNG found"); exit()

print(f"Loading: {png.name}")
arr = np.array(Image.open(str(png)))
h, w = arr.shape[:2]
print(f"Image: {w}x{h} = {w*h:,} px")

# Build binary mask from alpha channel
mask = (arr[:,:,3] > 0).astype(np.uint8) * 255
opaque = int(mask.sum() / 255)
print(f"Masked (opaque) pixels: {opaque:,} ({opaque/(w*h):.1%})")

# Find connected background regions (inverse of mask)
inv_mask = cv2.bitwise_not(mask)
num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(inv_mask, connectivity=8)

# Classify: exterior (touches border) vs interior (enclosed)
exterior_area = 0
interior_holes = []
for lbl in range(1, num_labels):
    area = int(stats[lbl, cv2.CC_STAT_AREA])
    lx, ly, lw, lh = (int(stats[lbl, cv2.CC_STAT_LEFT]), int(stats[lbl, cv2.CC_STAT_TOP]),
                       int(stats[lbl, cv2.CC_STAT_WIDTH]), int(stats[lbl, cv2.CC_STAT_HEIGHT]))
    touches_border = (lx == 0 or ly == 0 or lx + lw >= w or ly + lh >= h)
    if touches_border:
        exterior_area += area
    else:
        interior_holes.append((area, lx, ly, lw, lh))

print(f"\nExterior background: {exterior_area:,} px ({exterior_area/(w*h):.1%})")
print(f"Interior holes: {len(interior_holes)}")
interior_holes.sort(reverse=True)
for i, (area, lx, ly, lw, lh) in enumerate(interior_holes[:10]):
    pct = area / (w*h) * 100
    print(f"  Hole {i+1}: {area:>8,} px ({pct:.2f}%)  at ({lx},{ly}) size {lw}x{lh}")

total_interior = sum(a for a, *_ in interior_holes)
print(f"\nTotal interior hole area: {total_interior:,} px ({total_interior/(w*h):.1%})")
print(f"If these holes were excluded, coverage would be: {(opaque-total_interior)/(w*h):.1%}")
print(f"\nCurrent max_hole_fraction threshold: 1% = {int(w*h*0.01):,} px")
print(f"Holes above threshold (not filled): {[a for a,*_ in interior_holes if a > w*h*0.01]}")
print(f"Holes below threshold (were filled): {[a for a,*_ in interior_holes if a <= w*h*0.01]}")
