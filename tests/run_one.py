"""Run a single extraction to see the full error without stdout flood."""
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

from pipeline.extractor import extract_element

IMG = str(Path(__file__).parent.parent / "sources/claudiens/site/images/emblems/emblem-37.jpg")
print("Running extraction on emblem-37 / prompt: lion")
try:
    result = extract_element(IMG, prompt="lion", output_dir=str(OUTPUT_DIR))
    if result:
        print("SUCCESS")
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        print("No detection returned")
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
