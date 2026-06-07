"""
Search BSB Munich and Heidelberg Digital Library for missing alchemical emblem books.
These are European digital libraries with excellent early modern German holdings.
"""
import urllib.request, ssl, json, time, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def check_url(url, label):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 EmblemPrintShop/1.0",
            "Accept": "application/json, text/html"
        })
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            content = r.read().decode("utf-8", errors="replace")
        status = r.status if hasattr(r, 'status') else 200
        title_m = re.search(r'<title[^>]*>([^<]+)</title>', content, re.I)
        title = title_m.group(1).strip()[:80] if title_m else "(no title)"
        return f"OK ({len(content)} chars) — {title}"
    except Exception as e:
        return f"Error: {e}"

# BSB Munich catalog API
# BSB has a REST API for their catalog
BSB_API = "https://api.digitale-sammlungen.de/iiif/presentation/v2"

# Known BSB identifiers for alchemical works
# Mylius Philosophia Reformata: BSB might have it
BSB_SEARCHES = {
    "mylius_pr": "https://www.digitale-sammlungen.de/de/search?q=Mylius+Philosophia+reformata&mods.genre=Druckschriften",
    "stolcius_vc": "https://www.digitale-sammlungen.de/de/search?q=Stolcius+Viridarium+chymicum",
    "fludd_utriusque": "https://www.digitale-sammlungen.de/de/search?q=Fludd+utriusque+cosmi",
}

print("BSB Munich searches:")
for key, url in BSB_SEARCHES.items():
    result = check_url(url, key)
    print(f"  {key}: {result[:80]}")
    time.sleep(1)

# Heidelberg Digital Library (digi.ub.uni-heidelberg.de)
# They have many early modern emblem books
HEIDELBERG_SEARCHES = {
    "mylius": "https://digi.ub.uni-heidelberg.de/cgi-bin/diglit.cgi?mode=suche&query=Mylius+Philosophia&lang=de",
    "stolcius": "https://digi.ub.uni-heidelberg.de/cgi-bin/diglit.cgi?mode=suche&query=Stolcius+Viridarium",
    "fludd": "https://digi.ub.uni-heidelberg.de/cgi-bin/diglit.cgi?mode=suche&query=Fludd+Utriusque",
}

print("\nHeidelberg Digital Library searches:")
for key, url in HEIDELBERG_SEARCHES.items():
    result = check_url(url, key)
    print(f"  {key}: {result[:80]}")
    time.sleep(1)

# Try direct known Heidelberg identifiers for emblem books
# The Heidelberg emblem project (www.emblematica.de) has comprehensive coverage
EMBLEMATICA = {
    "emblematica_search": "https://www.emblematica.de/api/v1/search?q=mylius+philosophia",
    "emblematica_stolcius": "https://www.emblematica.de/api/v1/search?q=stolcius",
}
print("\nEmblematica.de searches:")
for key, url in EMBLEMATICA.items():
    result = check_url(url, key)
    print(f"  {key}: {result[:100]}")
    time.sleep(1)

# Check the HAB (Herzog August Bibliothek) - excellent for Rosicrucian/alchemical
HAB = {
    "hab_mylius": "https://diglib.hab.de/?list=mss&id=mylius+philosophia",
    "hab_search": "https://search.hab.de/?q=Mylius+Philosophia+reformata&field=all",
}
print("\nHAB searches:")
for key, url in HAB.items():
    result = check_url(url, key)
    print(f"  {key}: {result[:80]}")
    time.sleep(1)
