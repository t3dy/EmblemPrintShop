import urllib.request, json

queries = [
    "Cramer rosicrucian emblems 1617",
    "Viridarium chymicum stolcius",
    "Rosarium philosophorum",
]

for query in queries:
    url = f"https://api.wellcomecollection.org/catalogue/v2/works?query={urllib.request.quote(query)}&pageSize=5"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        results = d.get("results", [])
        print(f"\nQuery: {query!r}  -> {len(results)} results")
        for w in results[:5]:
            wid = w.get("id", "?")
            title = w.get("title", "?")[:70]
            # Check if digitized
            imgloc = any(
                loc.get("locationType", {}).get("id") in ("iiif-presentation", "digital-location")
                for item in w.get("items", [])
                for loc in item.get("locations", [])
            )
            print(f"  {wid}  {title}")
    except Exception as e:
        print(f"  Error: {e}")
