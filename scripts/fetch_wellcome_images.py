"""
Download emblem plate images from Wellcome Collection for Cramer and Stolcius.

The TheosophicalAlchemyDB records for Rosicrucian Emblems (Cramer, 1617) and
Hermetic Garden (Stolcius, 1624) all reference a single Wellcome work URL per
book (d4pc2pcu for Cramer). Individual emblem plates live in the IIIF manifest
as separate canvases — we download each canvas as a separate JPG.

Known Wellcome work IDs (from DB and Wellcome search):
  - Cramer Rosicrucian Emblems 1617: d4pc2pcu
  - Stolcius Viridarium Chymicum 1624: Search by title via API

Usage:
    python scripts/fetch_wellcome_images.py --dry-run
    python scripts/fetch_wellcome_images.py --source cramer --output sources/cramer/
    python scripts/fetch_wellcome_images.py --source stolcius --output sources/stolcius/
    python scripts/fetch_wellcome_images.py --source all
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Known Wellcome Collection work IDs for each emblem book
SOURCES = {
    "cramer": {
        "name": "Rosicrucian Emblems (Cramer 1617)",
        "work_id": "d4pc2pcu",
        "output_subdir": "cramer",
    },
    "stolcius": {
        "name": "Viridarium Chymicum / Hermetic Garden (Stolcius 1624)",
        "work_id": None,  # Will search by title
        "search_query": "Viridarium chymicum Stolcius",
        "output_subdir": "stolcius",
    },
    "rosarium": {
        "name": "Rosarium Philosophorum (1550)",
        "work_id": None,
        "search_query": "Rosarium philosophorum 1550",
        "output_subdir": "rosarium",
    },
}

WELLCOME_API   = "https://api.wellcomecollection.org/catalogue/v2"
IIIF_PRES_V3   = "https://iiif.wellcomecollection.org/presentation/v3"
IIIF_PRES_V2   = "https://iiif.wellcomecollection.org/presentation/v2"
TARGET_SIZE    = "1024,"   # 1024px wide, proportional height


def api_get(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "EmblemPrintShop/1.0 (scholarly research; ted.hand@gmail.com)",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    API error: {e}")
        return None


def search_wellcome(query: str) -> list[dict]:
    """Search for works by title query."""
    url = f"{WELLCOME_API}/works?query={urllib.request.quote(query)}&pageSize=5"
    data = api_get(url)
    if not data:
        return []
    return data.get("results", [])


def get_work_info(work_id: str) -> dict | None:
    url = f"{WELLCOME_API}/works/{work_id}?include=items,images"
    return api_get(url)


def get_iiif_manifest(work_id: str) -> dict | None:
    """Try IIIF v3 then v2 manifest."""
    for base in [IIIF_PRES_V3, IIIF_PRES_V2]:
        url = f"{base}/{work_id}/manifest"
        result = api_get(url)
        if result:
            return result
    return None


def extract_canvas_images_v3(manifest: dict) -> list[str]:
    """Extract image URLs from an IIIF v3 manifest."""
    urls = []
    for item in manifest.get("items", []):
        for page in item.get("items", []):
            for anno in page.get("items", []):
                body = anno.get("body", {})
                if isinstance(body, list):
                    body = body[0]
                svc = body.get("service", {})
                if isinstance(svc, list):
                    svc = svc[0]
                svc_id = svc.get("id", "") or svc.get("@id", "")
                if svc_id:
                    urls.append(f"{svc_id}/full/{TARGET_SIZE}/0/default.jpg")
                elif body.get("id", ""):
                    urls.append(body["id"])
    return urls


def extract_canvas_images_v2(manifest: dict) -> list[str]:
    """Extract image URLs from an IIIF v2 manifest."""
    urls = []
    for seq in manifest.get("sequences", []):
        for canvas in seq.get("canvases", []):
            for img_res in canvas.get("images", []):
                res = img_res.get("resource", {})
                svc = res.get("service", {})
                svc_id = svc.get("@id", "") if isinstance(svc, dict) else ""
                if svc_id:
                    urls.append(f"{svc_id}/full/{TARGET_SIZE}/0/default.jpg")
                elif res.get("@id", ""):
                    urls.append(res["@id"])
    return urls


def extract_canvas_images(manifest: dict) -> list[str]:
    """Try v3 then v2 canvas extraction."""
    if "items" in manifest:
        urls = extract_canvas_images_v3(manifest)
        if urls:
            return urls
    return extract_canvas_images_v2(manifest)


def download_image(url: str, out_path: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "EmblemPrintShop/1.0 (scholarly research)"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            out_path.write_bytes(resp.read())
        return out_path.stat().st_size > 1000
    except Exception as e:
        print(f"    Download error: {e}")
        return False


def process_source(source_key: str, source_cfg: dict, out_dir: Path,
                   dry_run: bool = False, limit: int | None = None) -> int:
    print(f"\n{'='*60}")
    print(f"Source: {source_cfg['name']}")

    work_id = source_cfg.get("work_id")
    if not work_id and source_cfg.get("search_query"):
        print(f"Searching: {source_cfg['search_query']}")
        results = search_wellcome(source_cfg["search_query"])
        time.sleep(1)
        if not results:
            print("  No results found.")
            return 0
        for r in results[:3]:
            print(f"  Found: {r.get('id')} — {r.get('title','?')[:60]}")
        work_id = results[0]["id"]

    if not work_id:
        print("  No work ID found. Skipping.")
        return 0

    print(f"Work ID: {work_id}  (https://wellcomecollection.org/works/{work_id})")

    print("Fetching IIIF manifest...")
    manifest = get_iiif_manifest(work_id)
    time.sleep(1)

    if not manifest:
        print("  Could not fetch manifest.")
        return 0

    image_urls = extract_canvas_images(manifest)
    print(f"  Found {len(image_urls)} canvas images")

    if not image_urls:
        print("  No image URLs extracted from manifest.")
        return 0

    if limit:
        image_urls = image_urls[:limit]

    out_dir.mkdir(parents=True, exist_ok=True)

    # Save manifest
    (out_dir / "iiif_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if dry_run:
        print(f"  [dry-run] Would download {len(image_urls)} images to {out_dir}")
        for i, u in enumerate(image_urls[:5]):
            print(f"    [{i+1:>3}] {u[:80]}")
        if len(image_urls) > 5:
            print(f"    ... and {len(image_urls)-5} more")
        return len(image_urls)

    downloaded = 0
    for i, url in enumerate(image_urls):
        # Name by canvas position
        fname = f"{source_key}_plate_{i+1:03d}.jpg"
        out_path = out_dir / fname

        if out_path.exists() and out_path.stat().st_size > 5000:
            print(f"  [{i+1:>3}/{len(image_urls)}] SKIP: {fname}")
            downloaded += 1
            continue

        print(f"  [{i+1:>3}/{len(image_urls)}] {fname}", end=" ", flush=True)
        ok = download_image(url, out_path)
        if ok:
            kb = out_path.stat().st_size // 1024
            print(f"({kb}KB)")
            downloaded += 1
        else:
            print("FAILED")

        # Save URL sidecar for provenance
        (out_path.with_suffix(".txt")).write_text(
            f"source: {source_cfg['name']}\nwork_id: {work_id}\ncanvas_index: {i+1}\nurl: {url}\n",
            encoding="utf-8"
        )
        time.sleep(0.8)

    print(f"\n  Downloaded {downloaded}/{len(image_urls)} images -> {out_dir}")
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Download Wellcome Collection emblem images")
    parser.add_argument("--source", default="all",
                        choices=["all", "cramer", "stolcius", "rosarium"],
                        help="Which emblem book to download")
    parser.add_argument("--output", "-o", default="sources/wellcome",
                        help="Base output directory (subdirs per source)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max canvases per source (for testing)")
    args = parser.parse_args()

    base_out = PROJECT_ROOT / args.output
    to_process = {args.source: SOURCES[args.source]} if args.source != "all" else SOURCES
    total = 0

    for key, cfg in to_process.items():
        out_dir = base_out / cfg["output_subdir"]
        n = process_source(key, cfg, out_dir, dry_run=args.dry_run, limit=args.limit)
        total += n

    print(f"\nTotal images: {total}")


if __name__ == "__main__":
    main()
