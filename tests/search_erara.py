"""Search e-rara.ch and BSB for Mylius, Stolcius, and other missing works."""
import urllib.request, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def erara_search(q):
    """Search e-rara.ch OAI/API for digitized books."""
    url = f"https://www.e-rara.ch/search?query={urllib.request.quote(q)}&output=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            return r.read().decode("utf-8", errors="replace")[:500]
    except Exception as e:
        return f"Error: {e}"

def erara_iiif(doi):
    """Get IIIF manifest for an e-rara work by DOI."""
    url = f"https://www.e-rara.ch/i3f/v20/{doi}/manifest"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            d = json.loads(r.read())
        items = d.get("sequences", [{}])[0].get("canvases", [])
        return len(items), d.get("label", "?")
    except Exception as e:
        return 0, str(e)

# Known e-rara identifiers (from previous research)
KNOWN_ERARA = {
    "Mylius Philosophia Reformata 1622": "5020807",
    "Stolcius Viridarium Chymicum 1624": "6029027",
    "Maier Atalanta Fugiens 1618": "5027458",
}

print("Testing known e-rara identifiers:")
for title, doi in KNOWN_ERARA.items():
    n, label = erara_iiif(doi)
    print(f"  {title[:45]}: DOI={doi}, {n} canvases, label='{str(label)[:40]}'")
    time.sleep(0.5)

# Also try direct URL check
print("\nDirect URL checks for e-rara works:")
ERARA_URLS = {
    "Mylius PR (guess)": "https://www.e-rara.ch/zut/wihibe/content/titleinfo/5020807",
    "Stolcius (guess)": "https://www.e-rara.ch/zut/wihibe/content/titleinfo/6029027",
}
for name, url in ERARA_URLS.items():
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            content = r.read().decode("utf-8", errors="replace")
        # Look for title in content
        import re
        title_match = re.search(r"<title>([^<]+)</title>", content)
        print(f"  {name}: {title_match.group(1)[:60] if title_match else 'no title'}")
    except Exception as e:
        print(f"  {name}: {e}")
    time.sleep(0.5)
