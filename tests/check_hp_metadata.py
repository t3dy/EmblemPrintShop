import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.metadata import get_prompt_for_image, _load_hp_woodcut_data, list_available_emblems

# Test HP parsing
wc = _load_hp_woodcut_data()
print(f"HP woodcut records loaded: {len(wc)}")
for page in [330, 391, 392, 393, 52]:
    print(f"  p{page}: {wc.get(page, 'NOT FOUND')}")

# Test lookup
p330 = get_prompt_for_image("sources/hypnerotomachia-polyphili/site/images/woodcuts_1499/hp1499_p330.jpg")
p391 = get_prompt_for_image("sources/hypnerotomachia-polyphili/site/images/woodcuts_1499/hp1499_p391.jpg")
print(f"\nAuto-prompt hp1499_p330: {repr(p330)}")
print(f"Auto-prompt hp1499_p391: {repr(p391)}")

# Count HP images in list
all_emblems = list_available_emblems()
hp = [e for e in all_emblems if "hypnerotomachia" in e["source_project"]]
print(f"\nHP emblems in list: {len(hp)}")
for e in hp[:5]:
    print(f"  {Path(e['image_path']).name:30s} | {e['auto_prompt']}")
