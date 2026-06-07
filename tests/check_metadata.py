import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.metadata import get_prompt_for_image, list_available_emblems

prompt = get_prompt_for_image("sources/claudiens/site/images/emblems/emblem-37.jpg")
print("Auto-prompt for emblem-37:", repr(prompt))

emblems = list_available_emblems()
print(f"Found {len(emblems)} emblems in sources")
for e in emblems[:8]:
    name = Path(e["image_path"]).name
    print(f"  {name:35s} | {e['auto_prompt']}")
