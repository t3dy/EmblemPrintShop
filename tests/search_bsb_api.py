"""Try BSB MDZ API to find Mylius Philosophia Reformata and Stolcius."""
import urllib.request, ssl, json, re, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def bsb_search(q):
    # BSB MDZ catalog search API
    url = f"https://www.digitale-sammlungen.de/de/search?q={urllib.request.quote(q)}&output=json"
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return str(e)

def bsb_iiif(bsb_id):
    """Get IIIF manifest for a BSB item."""
    url = f"https://api.digitale-sammlungen.de/iiif/presentation/v2/{bsb_id}/manifest"
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            d = json.loads(r.read())
        seqs = d.get("sequences", [{}])
        canvases = seqs[0].get("canvases", []) if seqs else []
        return len(canvases), d.get("label", "?")
    except Exception as e:
        return 0, str(e)

# Try known/guessed BSB IDs for these works
# BSB IDs typically follow pattern: bsb10XXXXXX
BSB_GUESSES = {
    "Mylius Philosophia Reformata": [
        "bsb10214982",  # guess
        "bsb00049619",
        "bsb10293649",
    ],
    "Stolcius Viridarium Chymicum": [
        "bsb10223506",  # guess
        "bsb11214982",
    ],
    "Fludd Utriusque Cosmi": [
        "bsb10148810",
        "bsb11148810",
    ],
}

# Try the BSB catalog SRU endpoint
def bsb_sru(query):
    url = (f"https://opacplus.bsb-muenchen.de/metaopac/sru"
           f"?operation=searchRetrieve&version=1.1"
           f"&query=title+all+{urllib.request.quote(query)}"
           f"&recordSchema=oai_dc&maximumRecords=5")
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            content = r.read().decode("utf-8", errors="replace")
        # Extract identifiers from SRU response
        ids = re.findall(r'bsb\d{8}', content)
        titles = re.findall(r'<dc:title>([^<]+)</dc:title>', content)
        return ids[:5], titles[:5]
    except Exception as e:
        return [], [str(e)]

print("BSB SRU catalog searches:")
for query in ["Mylius Philosophia Reformata", "Stolcius Viridarium chymicum", "Fludd Utriusque cosmi historia"]:
    ids, titles = bsb_sru(query)
    print(f"\n  Query: {query}")
    print(f"  IDs: {ids}")
    for t in titles:
        print(f"  Title: {t[:70]}")
    time.sleep(0.5)

# Check HAB WDB (Wolfenbüttel) more specifically
print("\nHAB Wolfenbüttel catalog:")
HAB_GUESSES = {
    "Mylius Philosophia Reformata 1622": "http://diglib.hab.de/drucke/xb-4f-13/start.htm",
}
for name, url in HAB_GUESSES.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            content = r.read().decode("utf-8", errors="replace")
        title_m = re.search(r'<title[^>]*>([^<]+)</title>', content)
        print(f"  {name}: {title_m.group(1)[:80] if title_m else 'no title'}")
    except Exception as e:
        print(f"  {name}: {e}")
