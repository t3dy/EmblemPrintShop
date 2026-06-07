"""
Try multiple digital library APIs to find Mylius Philosophia Reformata
and Stolcius Viridarium Chymicum.

Known facts:
- Mylius, Philosophia Reformata, Frankfurt, 1622, with Stolcius engravings
- Stolcius, Viridarium Chymicum, Frankfurt, 1624 (uses same Mylius plates)
- These two works share their copper engravings

Target libraries: BSB Munich, ETH e-rara, Gallica, DFG Viewer
"""
import urllib.request, ssl, json, re, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get(url, accept="text/html"):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 EmblemPrintShop/1.0",
        "Accept": accept
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return r.read().decode("utf-8", errors="replace"), r.status
    except Exception as e:
        return str(e), 0

# Try Gallica (BNF) — excellent for early modern French and Latin texts
# Gallica SRU endpoint
GALLICA_SRU = "https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query=dc.title+all+{q}&maximumRecords=5"

for query in ["Mylius philosophia reformata", "Stolcius viridarium chymicum", "Fludd utriusque cosmi"]:
    url = GALLICA_SRU.format(q=urllib.request.quote(query))
    content, status = get(url, "application/xml")
    arks = re.findall(r'ark:/12148/([a-z0-9]+)', content)
    titles = re.findall(r'<dc:title>([^<]+)</dc:title>', content)
    print(f"\nGallica: {query}")
    print(f"  ARKs: {arks[:3]}")
    for t in titles[:3]: print(f"  {t[:70]}")
    time.sleep(1)

# Try ETH Zurich e-rara (different URL structure from what we tried before)
print("\n\ne-rara ETH searches:")
ERARA_QUERIES = {
    "mylius": "https://www.e-rara.ch/search?field=tit&query=Philosophia+Reformata&lang=en",
    "stolcius": "https://www.e-rara.ch/search?field=tit&query=Viridarium+chymicum&lang=en",
}
for key, url in ERARA_QUERIES.items():
    content, status = get(url)
    # Look for result links or identifiers
    hrefs = re.findall(r'href="(/[^"]+/content/titleinfo/\d+)"', content)
    titles_found = re.findall(r'class="title[^"]*">([^<]+)<', content)
    print(f"  {key}: {len(hrefs)} hits  {hrefs[:3]}")
    for t in titles_found[:3]: print(f"    {t[:60]}")
    time.sleep(1)

# Try ZVDD (Zentrales Verzeichnis Digitalisierter Drucke)
print("\n\nZVDD searches:")
ZVDD = "https://zvdd.de/api/search?q={q}&offset=0&limit=5"
for query in ["Mylius philosophia reformata", "Stolcius viridarium"]:
    url = ZVDD.format(q=urllib.request.quote(query))
    content, status = get(url, "application/json")
    if status > 0:
        try:
            d = json.loads(content)
            print(f"  {query}: {d}")
        except:
            print(f"  {query}: {content[:200]}")
    else:
        print(f"  {query}: {content[:100]}")
    time.sleep(0.5)
