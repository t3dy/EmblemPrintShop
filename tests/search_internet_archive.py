"""Search Internet Archive for our emblem books."""
import urllib.request, json, time

def ia_search(query, rows=5):
    url = (f"https://archive.org/advancedsearch.php"
           f"?q={urllib.request.quote(query)}"
           f"&fl[]=identifier,title,year,mediatype,description"
           f"&rows={rows}&output=json")
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read()).get("response", {}).get("docs", [])

queries = [
    ("Cramer Emblemata Sacra", "cramer"),
    ("Viridarium chymicum Stolcius 1624", "stolcius"),
    ("Rosarium philosophorum alchemical 1550", "rosarium"),
    ("Atalanta Fugiens Maier", "maier"),
]

for query, key in queries:
    try:
        results = ia_search(query, rows=5)
        print(f"\n{key.upper()}: {query!r}")
        for r in results:
            print(f"  {r.get('identifier','?'):30s}  {str(r.get('year','?')):8s}  {r.get('title','?')[:55]}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  Error: {e}")
