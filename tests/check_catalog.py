import json
from pathlib import Path
cat = json.loads(Path("prototype/gallery_catalog.json").read_text(encoding="utf-8"))
records = cat["records"]
print(f"Total: {len(records)} elements")
print(f"Tags ({len(cat['tags'])}): {', '.join(cat['tags'])}")
print()
by_tag = {}
for r in records:
    for t in r.get("tags", []):
        by_tag[t] = by_tag.get(t, 0) + 1
print("Tag counts (top 15):")
for tag, cnt in sorted(by_tag.items(), key=lambda x: -x[1])[:15]:
    print(f"  {tag:22s} {cnt}")
print()
scores = [r["score"] for r in records]
print(f"Score range: {min(scores):.3f} - {max(scores):.3f}  avg {sum(scores)/len(scores):.3f}")
covs = [r["coverage_pct"] for r in records if r.get("coverage_pct") is not None]
print(f"Coverage range: {min(covs):.1f}% - {max(covs):.1f}%  avg {sum(covs)/len(covs):.1f}%")
mottos = [r for r in records if r.get("motto")]
print(f"Records with motto: {len(mottos)}/{len(records)}")
stages = [r.get("stage") for r in records if r.get("stage")]
print(f"Stage distribution: {sorted(set(stages))}")
