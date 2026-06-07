"""Final IA search pass for remaining missing works."""
import urllib.request, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def search(q, rows=3):
    url = (f"https://archive.org/advancedsearch.php"
           f"?q={urllib.request.quote(q)}"
           f"&fl[]=identifier,title,year&rows={rows}&output=json")
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read()).get("response", {}).get("docs", [])

def has_pdf(ident):
    try:
        url = f"https://archive.org/metadata/{ident}/files"
        req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            files = json.loads(r.read()).get("result", [])
        return any(f.get("name","").endswith(".pdf") for f in files)
    except: return False

queries = [
    # Mylius - try different titles
    ("subject:alchemy author:mylius", "mylius_author"),
    ("philosophia reformata 1622", "mylius_pr"),
    # Stolcius - try German
    ("Stolzius Lustgartlein 1624", "stolcius2"),
    ("viridarium chymicum 1624", "stolcius3"),
    # Fludd
    ("Robert Fludd Mosaicall Philosophy", "fludd2"),
    ("fludd historia macrographia", "fludd3"),
    # More alchemical illustration sources
    ("Summum Bonum alchemical Fludd 1629", "fludd_sb"),
    ("Philosophia Sacra Robert Fludd", "fludd_ps"),
    ("alchemical illustrations Hartmann Schedel medieval", "schedel"),
    ("Buch der Heiligen Dreifaltigkeit alchemical codex", "bht"),
    ("Pretiosa margarita novella alchemical Petrus Bonus", "petrus"),
    ("Alchemy emblems manuscripts British Library Wellcome", "brit_lib"),
    ("Johann Daniel Mylius opus medico chymicum Frankfort", "mylius_opus"),
    ("Viridarium philosophicum alchemical images", "viridarium_phil"),
    ("Alchymia Andreas Libavius 1606", "libavius"),
]

print(f"{'Key':<22} {'Identifier':<50} {'PDF?'}")
print("-"*80)
found = {}
for q, key in queries:
    try:
        results = search(q)
        if results:
            top = results[0]
            ident = top.get("identifier","?")
            title = top.get("title","?")[:50]
            has_p = has_pdf(ident)
            print(f"{key:<22} {ident:<50} {'YES' if has_p else 'no'}")
            print(f"  {title}")
            if has_p:
                found[key] = {"identifier": ident, "title": top.get("title","")}
        else:
            print(f"{key:<22} no results")
        time.sleep(0.5)
    except Exception as e:
        print(f"{key:<22} ERROR: {e}")

print("\nWorks with PDFs found:")
for k, v in found.items():
    print(f"  {k}: {v['identifier']}")
