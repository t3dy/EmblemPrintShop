import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.metadata import list_available_emblems

emblems = list_available_emblems()
with_prompt = [e for e in emblems if e["auto_prompt"]]
without = [e for e in emblems if not e["auto_prompt"]]
print(f"With prompt: {len(with_prompt)}/{len(emblems)}")
for e in with_prompt[:15]:
    name = Path(e["image_path"]).name
    print(f"  {name:35s} | {e['auto_prompt']}")
print("...")
print(f"Without prompt (first 5): {[Path(e['image_path']).name for e in without[:5]]}")
