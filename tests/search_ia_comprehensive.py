"""Search Internet Archive for all target alchemical emblem books."""
import urllib.request, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def search(q, rows=4):
    url = (f"https://archive.org/advancedsearch.php"
           f"?q={urllib.request.quote(q)}"
           f"&fl[]=identifier,title,year,mediatype"
           f"&rows={rows}&output=json")
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read()).get("response", {}).get("docs", [])

def has_pdf(identifier):
    try:
        url = f"https://archive.org/metadata/{identifier}/files"
        req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            files = json.loads(r.read()).get("result", [])
        return any(f.get("name","").endswith(".pdf") for f in files)
    except:
        return False

QUERIES = [
    ("Mylius Philosophia Reformata 1622", "mylius_philosophia"),
    ("Stolcius Viridarium chymicum 1624 emblematum", "stolcius"),
    ("Khunrath Amphitheatrum sapientiae aeternae 1609", "khunrath"),
    ("Fludd Utriusque cosmi historia 1617", "fludd"),
    ("Splendor Solis Trismosin alchemical manuscript", "splendor_solis"),
    ("Mutus Liber 1677 alchemical emblem", "mutus_liber"),
    ("Lambspring De lapide philosophico emblems", "lambspring"),
    ("Maier Symbola aureae mensae 1617", "maier_symbola"),
    ("Michael Maier Arcana arcanissima", "maier_arcana"),
    ("Boschius Symbolographia 1702", "boschius"),
    ("Steffan Michelspacher Cabala speculum alchemiae", "michelspacher"),
    ("Abraham Eleazar manuscript rabbi alchemical", "eleazar"),
    ("Aurora consurgens alchemical manuscript medieval", "aurora_consurgens"),
    ("Ripley Scrowle scroll alchemical George Ripley", "ripley"),
]

print(f"{'Key':<25} {'Identifier':<40} {'Year':<8} PDF?")
print("-" * 85)
results_found = {}

for query, key in QUERIES:
    try:
        results = search(query)
        if results:
            top = results[0]
            identifier = top.get("identifier", "?")
            year = str(top.get("year", "?"))[:8]
            has_p = has_pdf(identifier)
            print(f"{key:<25} {identifier:<40} {year:<8} {'YES' if has_p else 'no'}")
            results_found[key] = {"identifier": identifier, "title": top.get("title","?"), "has_pdf": has_p}
        else:
            print(f"{key:<25} {'(no results)':<40}")
        time.sleep(0.5)
    except Exception as e:
        print(f"{key:<25} ERROR: {e}")

print("\n\nFull results:")
print(json.dumps(results_found, indent=2))
