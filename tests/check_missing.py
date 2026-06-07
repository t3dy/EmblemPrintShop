import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

data = json.loads((Path(__file__).parent.parent / "sources/claudiens/site/data.json").read_text(encoding="utf-8"))
entries = data["entries"]

missing = [e for e in entries if e.get("number", -1) in [0,1,2,3,4,5,6,11,12,15,20,21,23,39,41]]
for e in missing:
    num = e.get("number")
    label = e.get("label", "")
    motto = e.get("motto", "") or ""
    print(f"Emblem {num:2d}: {label}")
    print(f"         motto: {motto[:80]}")
    print()
