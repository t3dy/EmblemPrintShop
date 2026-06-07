import json
from pathlib import Path

data = json.loads(Path(r"C:\Dev\TheosophicalAlchemyDB\data\prototype_data.json").read_text(encoding="utf-8"))
emblems = data["emblems"]
print(f"{len(emblems)} total emblems")

# Source books
books = {}
for e in emblems:
    sb = e.get("source_book", "?")
    books[sb] = books.get(sb, 0) + 1
print("Source books:")
for k, v in sorted(books.items(), key=lambda x: -x[1]):
    print(f"  {v:>4}  {k}")

# Wellcome URLs
wellcome = [e for e in emblems if "wellcomecollection" in str(e.get("image_url", ""))]
print(f"\n{len(wellcome)} emblems with Wellcome URLs")
for e in wellcome[:5]:
    print(f"  id={e.get('id')}  book={e.get('source_book','?')!r}")
    print(f"    url={e.get('image_url','?')}")

# Also check for any image_url fields at all
with_url = [e for e in emblems if e.get("image_url")]
print(f"\n{len(with_url)} emblems with any image_url")
url_samples = set(e.get("image_url","")[:50] for e in with_url[:20])
for u in sorted(url_samples):
    print(f"  {u}")
