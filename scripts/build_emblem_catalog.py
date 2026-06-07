"""
Build the unified alchemical emblem catalog JSON.

Merges data from:
  1. Claudiens site/data.json — discourse, motto, stage, confidence
  2. TheoAlchemyDB maier_atalanta_fugiens_emblems_metadata.json — visual_elements,
     key_concepts, planetary_association, divine_principle, spiritual_meaning
  3. TheoAlchemyDB prototype_data.json — source_book, image_url, figures, concepts
  4. TheoAlchemyDB COMPREHENSIVE_CONCEPT_EMBLEM_MAPPINGS.json — concept links
  5. EmblemPrintShop extracted elements (assets/extracted/*_meta.json)

Output: prototype/emblem_catalog.json
Schema: one record per emblem plate, with all ontology layers merged.

Usage:
    python scripts/build_emblem_catalog.py
"""
import json
import re
from pathlib import Path

PROJECT_ROOT  = Path(__file__).parent.parent
THEO_ROOT     = Path(r"C:\Dev\TheosophicalAlchemyDB")
CLAUDIENS_ROOT = PROJECT_ROOT / "sources" / "claudiens"
EXTRACTED_DIR  = PROJECT_ROOT / "assets" / "extracted"
OUT_PATH       = PROJECT_ROOT / "prototype" / "emblem_catalog.json"

# ── Load source data ──────────────────────────────────────────────────────────

def load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def load_claudiens_records() -> dict[int, dict]:
    """Load Claudiens emblem records keyed by emblem number."""
    data = load_json(CLAUDIENS_ROOT / "site" / "data.json")
    if not data:
        return {}
    entries = data.get("entries", [])
    return {e["number"]: e for e in entries if isinstance(e, dict) and "number" in e}

def load_theo_maier() -> dict[int, dict]:
    """Load TheoAlchemyDB Maier metadata keyed by emblem_number."""
    data = load_json(THEO_ROOT / "data" / "maier_atalanta_fugiens_emblems_metadata.json")
    if not data:
        return {}
    return {e["emblem_number"]: e for e in data.get("emblems", [])}

def load_theo_prototype() -> dict[str, list[dict]]:
    """Load prototype_data.json — returns {source_book: [emblem_records]}."""
    data = load_json(THEO_ROOT / "data" / "prototype_data.json")
    if not data:
        return {}
    emblems = data.get("emblems", [])
    by_book: dict[str, list] = {}
    for e in emblems:
        sb = e.get("source_book", "Unknown")
        by_book.setdefault(sb, []).append(e)
    return by_book

def load_concept_mappings() -> dict[str, list[dict]]:
    """Load concept-emblem mappings keyed by emblem_id string."""
    data = load_json(THEO_ROOT / "docs" / "COMPREHENSIVE_CONCEPT_EMBLEM_MAPPINGS.json")
    if not data:
        return {}
    # Build reverse index: emblem_id → [concept_links]
    by_emblem: dict[str, list] = {}
    for concept in data.get("concept_emblem_links", []):
        cid   = concept.get("concept_id")
        cname = concept.get("concept_name", "")
        for link in concept.get("emblem_links", []):
            eid = str(link.get("emblem_id", ""))
            by_emblem.setdefault(eid, []).append({
                "concept_id":   cid,
                "concept_name": cname,
                "link_type":    link.get("link_type", ""),
                "confidence":   link.get("confidence", ""),
                "explanation":  link.get("explanation", ""),
            })
    return by_emblem

EXTRACTED_ALL_DIR = PROJECT_ROOT / "assets" / "extracted_all"


def load_visual_tags() -> dict[int, dict]:
    """Load visual-data.json tags keyed by AF emblem number.
    Returns {emblem_number: {tags: [...], dict_tags: [...]}}.
    """
    path = CLAUDIENS_ROOT / "site" / "visual-data.json"
    data = load_json(path)
    if not data:
        return {}
    result: dict[int, dict] = {}
    for img in (data.get("images") or []):
        url = img.get("local_url", "") or ""
        if "atalanta_fugiens" not in img.get("work", "") and "emblem-" not in url:
            continue
        m = re.search(r"emblem-(\d+)", url)
        if not m:
            continue
        num = int(m.group(1))
        result[num] = {
            "motif_tags":     img.get("tags", []),
            "operation_tags": img.get("dict_tags", []),
        }
    return result


def load_extractions() -> dict[str, list[dict]]:
    """Load extracted element metadata keyed by emblem_id (source stem).

    Prefers comprehensive extraction (assets/extracted_all/) for sources that
    have been through the multi-category pipeline; falls back to the legacy
    flat extractions (assets/extracted/) for all others.
    """
    by_emblem: dict[str, list] = {}

    # ── Comprehensive extraction (assets/extracted_all/<stem>/individual/) ──
    if EXTRACTED_ALL_DIR.exists():
        for emblem_dir in sorted(EXTRACTED_ALL_DIR.iterdir()):
            if not emblem_dir.is_dir():
                continue
            stem = emblem_dir.name  # e.g. "emblem-08"
            for meta_path in sorted((emblem_dir / "individual").glob("*_meta.json")):
                try:
                    rec = json.loads(meta_path.read_text(encoding="utf-8"))
                    _rl = rec.get("label", "")
                    _cl = " ".join(t.lstrip("#") for t in str(_rl).split()).strip()
                    by_emblem.setdefault(stem, []).append({
                        "prompt":           _cl,
                        "score":            rec.get("score", 0),
                        "bbox":             rec.get("det_bbox", rec.get("tight_bbox", [])),
                        "transparent_png":  rec.get("transparent_png", ""),
                        "crop_jpg":         rec.get("crop_jpg", ""),
                        "mask_pixel_count": rec.get("mask_pixel_count", 0),
                        "coverage_pct":     None,
                        "extracted_at":     rec.get("extracted_at", ""),
                        "category":         rec.get("category", ""),
                        "type":             rec.get("type", "individual"),
                    })
                except Exception:
                    continue

    # ── Legacy flat extractions for sources not yet in extracted_all ──
    comprehensive_stems = set(by_emblem.keys())
    for meta_path in EXTRACTED_DIR.glob("*_meta.json"):
        try:
            rec = json.loads(meta_path.read_text(encoding="utf-8"))
            src = rec.get("source_image", "")
            stem = Path(src).stem
            if stem in comprehensive_stems:
                continue  # already covered by comprehensive extraction
            by_emblem.setdefault(stem, []).append({
                "prompt":           rec.get("prompt", ""),
                "score":            rec.get("score", 0),
                "bbox":             rec.get("bbox", []),
                "transparent_png":  rec.get("transparent_png", ""),
                "crop_jpg":         rec.get("crop_jpg", ""),
                "mask_pixel_count": rec.get("mask_pixel_count", 0),
                "coverage_pct":     rec.get("coverage_pct"),
                "extracted_at":     rec.get("extracted_at", ""),
            })
        except Exception:
            continue
    return by_emblem

def relative_path(abs_path: str) -> str:
    """Convert absolute path to web-relative (from prototype/)."""
    if not abs_path:
        return ""
    try:
        p = Path(abs_path)
        if p.is_absolute():
            rel = p.relative_to(PROJECT_ROOT)
        else:
            rel = Path(abs_path)
        return "../" + str(rel).replace("\\", "/")
    except ValueError:
        return abs_path.replace("\\", "/")

# ── Build unified records ─────────────────────────────────────────────────────

def build_maier_records(
    claudiens: dict[int, dict],
    theo_maier: dict[int, dict],
    theo_proto: list[dict],
    concept_map: dict[str, list],
    extractions: dict[str, list],
    visual_tags: dict[int, dict] | None = None,
) -> list[dict]:
    """Build unified records for Maier's Atalanta Fugiens (51 emblems)."""
    records = []
    # Index proto by emblem number
    proto_by_num: dict[int, dict] = {}
    for p in theo_proto:
        # Proto emblems have id field (100+)
        # Match Maier by source_book == "Atalanta Fugiens"
        pass

    for num in range(0, 51):
        cl = claudiens.get(num, {})
        th = theo_maier.get(num, {})

        stem = f"emblem-{num:02d}"
        image_path = f"sources/claudiens/site/images/emblems/{stem}.jpg"
        ext = extractions.get(stem, [])
        ext_sorted = sorted(ext, key=lambda x: x.get("score", 0), reverse=True)

        rec = {
            # ── Identity ──
            "id":             f"af_{num:02d}",
            "source_work":    "Atalanta Fugiens",
            "source_key":     "claudiens",
            "emblem_number":  num,
            "roman":          cl.get("roman", ""),
            "label":          cl.get("label", th.get("english_title", f"Emblem {num}")),
            "latin_title":    th.get("title", ""),
            "english_title":  th.get("english_title", cl.get("label", "")),

            # ── Textual content ──
            "motto":          cl.get("motto", ""),
            "motto_source":   th.get("motto_source", ""),
            "discourse":      cl.get("discourse", ""),
            "de_jong_pages":  th.get("de_jong_pages", ""),

            # ── Alchemical classification ──
            "stage":              cl.get("stage", ""),
            "stage_detailed":     th.get("alchemical_stage", ""),
            "color_association":  th.get("color_association", ""),
            "planetary_association": th.get("planetary_association", ""),
            "divine_principle":   th.get("divine_principle", ""),
            "spiritual_meaning":  th.get("spiritual_meaning", ""),

            # ── Iconographic ──
            "visual_elements": th.get("visual_elements", []),
            "key_concepts":    th.get("key_concepts", []),
            "related_emblems": th.get("related_emblems", []),
            # Controlled-vocabulary tags from Claudiens visual-data.json
            # motif_tags = iconographic figures/animals (lion, dragon, ouroboros…)
            # operation_tags = alchemical operations (circulatio, fermentatio…)
            "motif_tags":     (visual_tags or {}).get(num, {}).get("motif_tags", []),
            "operation_tags": (visual_tags or {}).get(num, {}).get("operation_tags", []),

            # ── Provenance ──
            "confidence":   cl.get("confidence", ""),
            "sources":      cl.get("sources", []),
            "page":         cl.get("page", ""),

            # ── Images ──
            "image_path":    image_path,
            "image_web":     "../" + image_path,
            "furnace_url":   "",   # will fill if available

            # ── Extracted elements ──
            "extracted_elements": [
                {**e, "transparent_png_web": relative_path(e["transparent_png"]),
                       "crop_jpg_web": relative_path(e["crop_jpg"])}
                for e in ext_sorted
            ],

            # ── Concept links ──
            "concept_links": concept_map.get(str(num), []),
        }
        records.append(rec)
    return records


def build_other_records(
    source_book: str,
    source_key: str,
    proto_records: list[dict],
    concept_map: dict[str, list],
    extractions: dict[str, list],
    img_dir: str,
) -> list[dict]:
    """Build unified records for non-Maier works."""
    records = []
    for i, p in enumerate(proto_records):
        pid = str(p.get("id", i))
        title = p.get("title", f"{source_book} {i+1}")
        slug = re.sub(r"[^\w]", "_", title.lower())[:40]
        rec_id = f"{source_key}_{pid}"

        # Find image pages extracted from this corpus
        # Images are named like cramer_page_0021.jpg
        ext_list = []
        for stem, exts in extractions.items():
            if source_key in stem:
                ext_list.extend(exts)
        ext_sorted = sorted(ext_list, key=lambda x: x.get("score", 0), reverse=True)

        # Guess image path from page number if available
        year = p.get("year", "")
        image_web = ""

        rec = {
            "id":            rec_id,
            "source_work":   source_book,
            "source_key":    source_key,
            "emblem_number": int(pid) if pid.isdigit() else i,
            "roman":         "",
            "label":         title,
            "latin_title":   "",
            "english_title": title,

            "motto":         "",
            "motto_source":  "",
            "discourse":     p.get("summary", "") or p.get("essay", "")[:500],
            "de_jong_pages": "",

            "stage":             "",
            "stage_detailed":    "",
            "color_association": "",
            "planetary_association": "",
            "divine_principle":  "",
            "spiritual_meaning": p.get("summary", ""),

            "visual_elements": p.get("visual_elements", []),
            "key_concepts":    [],
            "related_emblems": [],

            "confidence":   p.get("authenticity", ""),
            "sources":      [s.get("reference", "") for s in p.get("scholarship", [])],
            "page":         "",

            "image_path":  image_web,
            "image_web":   image_web,
            "wellcome_url": p.get("image_url", ""),

            "extracted_elements": [
                {**e, "transparent_png_web": relative_path(e["transparent_png"]),
                       "crop_jpg_web": relative_path(e["crop_jpg"])}
                for e in ext_sorted[:3]  # top 3 extractions per plate
            ],

            "concept_links": concept_map.get(pid, []),
        }
        records.append(rec)
    return records


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading source data...")
    claudiens    = load_claudiens_records()
    theo_maier   = load_theo_maier()
    theo_proto   = load_theo_prototype()
    concept_map  = load_concept_mappings()
    extractions  = load_extractions()
    visual_tags  = load_visual_tags()

    print(f"  Claudiens:   {len(claudiens)} records")
    print(f"  Theo/Maier:  {len(theo_maier)} records")
    print(f"  Extractions: {sum(len(v) for v in extractions.values())} elements from {len(extractions)} emblems")

    all_records: list[dict] = []

    # Maier Atalanta Fugiens
    maier = build_maier_records(
        claudiens, theo_maier,
        theo_proto.get("Atalanta Fugiens", []),
        concept_map, extractions, visual_tags,
    )
    all_records.extend(maier)
    print(f"  Built {len(maier)} Maier records")

    # Other TheoAlchemyDB sources
    for book, src_key, img_dir in [
        ("Rosicrucian Emblems", "cramer", "sources/cramer/images"),
        ("Hermetic Garden",     "stolcius", "sources/stolcius/images"),
    ]:
        proto_recs = theo_proto.get(book, [])
        if proto_recs:
            recs = build_other_records(
                book, src_key, proto_recs, concept_map, extractions, img_dir
            )
            all_records.extend(recs)
            print(f"  Built {len(recs)} {book} records")

    # Build concept index
    all_concepts: dict[str, dict] = {}
    for rec in all_records:
        for cl in rec.get("concept_links", []):
            cid = str(cl.get("concept_id", ""))
            if cid not in all_concepts:
                all_concepts[cid] = {
                    "id":   cl["concept_id"],
                    "name": cl["concept_name"],
                    "emblem_count": 0,
                }
            all_concepts[cid]["emblem_count"] += 1

    # Build stage index
    stages = {}
    for rec in all_records:
        s = rec.get("stage", "") or ""
        if s:
            stages[s] = stages.get(s, 0) + 1

    catalog = {
        "version":      "1.0",
        "total":        len(all_records),
        "source_works": list({r["source_work"] for r in all_records}),
        "stages":       stages,
        "concepts":     list(all_concepts.values()),
        "emblems":      all_records,
    }

    OUT_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nCatalog written: {OUT_PATH}")
    print(f"  {len(all_records)} emblems | {len(all_concepts)} concepts | {len(stages)} stages")


if __name__ == "__main__":
    main()
