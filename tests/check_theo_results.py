import json
from pathlib import Path

extracted = Path("assets/extracted")
theo_files = sorted(f for f in extracted.glob("emblem-0*_meta.json"))

print(f"{'Emblem':<12} {'Prompt':<40} {'Score':>6}  {'Coverage':>9}  {'Mask px':>10}")
print("-" * 82)
for f in theo_files[:12]:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        prompt = d.get("prompt", "?")[:38]
        score = d.get("score", 0) * 100
        mask = d.get("mask_pixel_count", 0)
        cov = mask / 2_472_000 * 100  # approx for 1600x1545
        print(f"{f.stem[:10]:<12} {prompt:<40} {score:>5.1f}%  {cov:>8.1f}%  {mask:>10,}")
    except Exception as e:
        print(f"{f.name}: ERROR {e}")
