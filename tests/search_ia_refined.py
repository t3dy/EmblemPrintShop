"""Refined IA searches with exact Latin titles and alternate queries."""
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

def check_files(identifier):
    try:
        url = f"https://archive.org/metadata/{identifier}/files"
        req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            files = json.loads(r.read()).get("result", [])
        pdfs = [f["name"] for f in files if f.get("name","").endswith(".pdf")]
        jp2s = [f["name"] for f in files if f.get("name","").endswith(".jp2")]
        return {"pdfs": pdfs[:3], "jp2_count": len(jp2s)}
    except Exception as e:
        return {"error": str(e)}

REFINED_QUERIES = [
    ("Mylius Philosophia reformata 1622 emblem", "mylius"),
    ("Joannis Danielis Mylii opus medico chymicum", "mylius2"),
    ("Chymisches Lustgartlein Stolzius 1624", "stolcius_de"),
    ("Khunrath Amphitheatrum sapientiae", "khunrath_orig"),
    ("Fludd Tomus secundus philosophia moysaica", "fludd_mosaic"),
    ("Fludd Medicina catholica tract", "fludd_med"),
    ("Maier Symbola aureae mensae duodecim", "maier_symbola2"),
    ("Maier Atalanta fugiens 1618", "maier_af"),
    ("Boehme Jacob alchemical works illustrations", "boehme"),
    ("Ripley scroll alchemical George", "ripley2"),
    ("Aurora consurgens medieval manuscript alchemy illustration", "aurora"),
    ("Buch der Heiligen Dreifaltigkeit manuscript alchemical", "trinity"),
    ("alchemical manuscript illuminated medieval british library", "medieval_ms"),
    ("Thurneisser Quinta essentia alchemical", "thurneisser"),
    ("Paracelsus alchemical illustrations woodcuts", "paracelsus_illus"),
]

for query, key in REFINED_QUERIES:
    try:
        results = search(query)
        if results:
            top = results[0]
            ident = top.get("identifier","?")
            year = str(top.get("year","?"))
            title = top.get("title","?")[:55]
            files = check_files(ident)
            pdf_info = f"{len(files.get('pdfs',[]))} pdf, {files.get('jp2_count',0)} jp2"
            print(f"{key:<20} {ident:<45} {year:<6} [{pdf_info}]")
            print(f"  Title: {title}")
        else:
            print(f"{key:<20} (no results)")
        time.sleep(0.4)
    except Exception as e:
        print(f"{key:<20} ERROR: {e}")
