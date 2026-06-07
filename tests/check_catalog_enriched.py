import json
from pathlib import Path

cat = json.loads(Path("prototype/gallery_catalog.json").read_text(encoding="utf-8"))
records = cat["records"]

# Show records that have TheoAlchemyDB enrichment
theo_enriched = [r for r in records if r.get("theo_title")]
print(f"Records with TheoAlchemyDB enrichment: {len(theo_enriched)}")
print()
for r in sorted(theo_enriched, key=lambda x: x["emblem_id"])[:8]:
    print(f"{r['emblem_id']}")
    print(f"  Prompt: {r.get('prompt', '?')}")
    print(f"  Motto:  {r.get('motto', '?')[:60]}")
    print(f"  Theo:   {r.get('theo_title', '?')}")
    print(f"  Stage:  {r.get('theo_stage', '?')}")
    print(f"  VE:     {', '.join(r.get('theo_visual_elements', [])[:3])}")
    print()
