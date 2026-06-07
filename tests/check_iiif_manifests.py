import urllib.request, json, time

work_ids = {
    "cramer": "d4pc2pcu",
    "stolcius_latin": "qynyxr3c",
    "stolcius_german": "txahsj9s",
    "rosarium_1": "kkdktv38",
    "rosarium_2": "uz8h5rv2",
}

for name, wid in work_ids.items():
    # Check IIIF v3
    url = f"https://iiif.wellcomecollection.org/presentation/v3/{wid}/manifest"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        items = d.get("items", [])
        print(f"{name:20s} ({wid}): v3 manifest OK — {len(items)} canvases")
    except Exception as e:
        # Try v2
        url2 = f"https://iiif.wellcomecollection.org/presentation/v2/{wid}/manifest"
        req2 = urllib.request.Request(url2, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req2, timeout=10) as r2:
                d2 = json.loads(r2.read())
            seqs = d2.get("sequences", [])
            canvases = sum(len(s.get("canvases", [])) for s in seqs)
            print(f"{name:20s} ({wid}): v2 manifest OK — {canvases} canvases")
        except Exception as e2:
            print(f"{name:20s} ({wid}): NO manifest — {e2}")
    time.sleep(0.5)
