"""Search Internet Archive for alchemical emblem books (SSL-relaxed for Python 3.14)."""
import urllib.request, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def ia_search(query, rows=6):
    url = (f"https://archive.org/advancedsearch.php"
           f"?q={urllib.request.quote(query)}"
           f"&fl[]=identifier,title,year,mediatype"
           f"&rows={rows}&output=json")
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read()).get("response", {}).get("docs", [])

def ia_files(identifier):
    url = f"https://archive.org/metadata/{identifier}/files"
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        d = json.loads(r.read())
    return d.get("result", [])

queries = [
    ("Cramer Emblemata Sacra", "cramer"),
    ("Viridarium chymicum Stolcius", "stolcius"),
    ("Rosarium philosophorum 1550 alchemical", "rosarium"),
    ("Lambsprinck De Lapide Philosophico", "lambsprinck"),
    ("Mutus Liber 1677 alchemical", "mutus_liber"),
]

for query, key in queries:
    try:
        results = ia_search(query)
        print(f"\n{key.upper()}")
        for r in results:
            print(f"  {r.get('identifier','?'):35s}  {str(r.get('year','?')):8s}  {r.get('title','?')[:50]}")
        if results:
            # Check first result for image files
            first_id = results[0]["identifier"]
            files = ia_files(first_id)
            img_files = [f for f in files if f.get("name","").lower().endswith((".jp2",".jpg",".png"))]
            print(f"  -> {first_id}: {len(img_files)} image files")
            if img_files:
                print(f"     Sample: {img_files[0].get('name','?')}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  {key}: Error — {e}")
