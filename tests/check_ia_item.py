"""Check Internet Archive item details for our emblem books."""
import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def ia_metadata(identifier):
    url = f"https://archive.org/metadata/{identifier}"
    req = urllib.request.Request(url, headers={"User-Agent": "EmblemPrintShop/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read())

for identifier in ["emblematasacraho00cram", "rosarium-philosophorum-the-rosary-of-the-philosophers"]:
    print(f"\n=== {identifier} ===")
    try:
        meta = ia_metadata(identifier)
        md = meta.get("metadata", {})
        print(f"Title: {md.get('title','?')}")
        print(f"Year: {md.get('date','?')}")
        print(f"Creator: {md.get('creator','?')}")
        print(f"Subject: {md.get('subject','?')}")

        files = meta.get("files", [])
        # Show all image/scan files
        img_files = [f for f in files if any(f.get("name","").lower().endswith(ext)
                     for ext in (".jp2", ".jpg", ".jpeg", ".png", ".pdf"))]
        print(f"Image/PDF files: {len(img_files)}")
        for f in img_files[:10]:
            print(f"  {f.get('name','?'):60s}  {f.get('size','?')} bytes")

        # Check for _jp2 directory format
        jp2_files = [f for f in files if "_jp2" in f.get("name","").lower() or f.get("name","").endswith(".jp2")]
        print(f"JP2 files: {len(jp2_files)}")

        # Check server/dir
        server = meta.get("server","")
        d = meta.get("dir","")
        print(f"Server: {server}  Dir: {d}")

    except Exception as e:
        print(f"Error: {e}")
