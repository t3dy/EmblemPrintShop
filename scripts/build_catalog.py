"""
Build the gallery catalog JSON from all *_meta.json files in assets/extracted/.

Run this after batch_extract.py completes (or at any point to get current state).
Writes: prototype/gallery_catalog.json
"""
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT  = Path(__file__).parent.parent
EXTRACTED_DIR = PROJECT_ROOT / "assets" / "extracted"
PROTOTYPE_DIR = PROJECT_ROOT / "prototype"
SOURCES_ROOT  = PROJECT_ROOT / "sources"
REVIEW_DECISIONS_PATH = PROTOTYPE_DIR / "review_decisions.json"
PROTOTYPE_DIR.mkdir(exist_ok=True)


def load_human_corrections() -> dict:
    """
    Load reviewer-entered corrected_label values from
    prototype/review_decisions.json (written by review.html's "Corrected
    label" field via serve.py's /api/save-review).

    Keyed the same way review.html keys its own state: f"{emblem_id}__
    {object_stem}" -- the unique per-object filename stem, not the label
    (multiple distinct objects routinely share the same generic detector
    label within one emblem). A human's correction is the highest-priority
    label source -- it overrides both the raw detector label and any AI
    vision verified_label.
    """
    if not REVIEW_DECISIONS_PATH.exists():
        return {}
    try:
        decisions = json.loads(REVIEW_DECISIONS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return {k: v["corrected_label"] for k, v in decisions.items() if v.get("corrected_label")}


def load_rejected_keys() -> set:
    """
    Object stems a human reviewer marked "rejected" in review.html (duplicate
    detections, whole-scene/bundled boxes, or regions with no real subject).
    These must be dropped from the catalog entirely, not just relabeled --
    otherwise manual review corrects the label text but the junk detection
    still ships to the public gallery.
    """
    if not REVIEW_DECISIONS_PATH.exists():
        return set()
    try:
        decisions = json.loads(REVIEW_DECISIONS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return set()
    return {k for k, v in decisions.items() if v.get("status") == "rejected"}


def resolve_path(path_str: str) -> Path:
    """Resolve a path that may be absolute or relative to the project root."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    # Relative — resolve from project root
    return (PROJECT_ROOT / p).resolve()


def relative_to_gallery(path_str: str) -> str:
    """Convert any path (absolute or relative) to a path relative to prototype/ for web serving."""
    if not path_str:
        return ""
    try:
        p = resolve_path(path_str)
        rel = p.relative_to(PROJECT_ROOT)
        return "../" + str(rel).replace("\\", "/")
    except (ValueError, TypeError):
        return path_str.replace("\\", "/")


# Known alchemical/iconographic vocabulary — used to normalize compound labels
# into atomic tags for the filter sidebar.
_KNOWN_VOCAB: frozenset[str] = frozenset({
    # Figures
    "person", "man", "woman", "angel", "child", "king", "queen",
    "hermaphrodite", "skeleton", "warrior", "witch", "pilgrim",
    "philosopher", "figure", "old",
    # Animals
    "lion", "eagle", "bird", "serpent", "dragon", "horse", "dog",
    "wolf", "fish", "deer", "bear", "ox", "lamb", "peacock", "swan",
    "dove", "raven", "pelican", "phoenix", "tortoise", "crab", "bee",
    "butterfly", "frog", "hare", "fox",
    # Plants
    "tree", "plant", "flower", "herb", "rose", "lily", "thistle",
    "vine", "branch", "bush", "fruit", "root", "grass", "reed",
    "palm", "wreath", "laurel", "oak", "thorn",
    # Landscape
    "mountain", "rock", "cliff", "river", "water", "sea", "cloud",
    "sun", "moon", "star", "fire", "flame", "earth", "sky", "hill",
    "cave", "spring", "wave", "rainbow", "lightning", "volcano", "forest",
    # Architecture / equipment
    "castle", "tower", "building", "arch", "column", "wall", "gate",
    "bridge", "ruin", "temple", "house", "furnace", "athanor", "hearth",
    "door", "window", "chimney", "tomb", "obelisk", "labyrinth", "altar",
    # Objects / instruments
    "sword", "spear", "shield", "axe", "staff", "wand", "scepter",
    "key", "chain", "crown", "ring", "book", "scroll", "torch", "lamp",
    "mirror", "hourglass", "vessel", "flask", "retort", "cauldron",
    "cup", "chalice", "globe", "egg", "wheel", "bellows", "scales",
    "crucible", "anvil", "lute", "trumpet", "drum", "alembic", "mortar",
    "pestle", "balance",
})


def normalize_label_tags(label: str) -> list[str]:
    """Decompose a (possibly compound) GroundingDINO label into atomic vocab tags.

    GroundingDINO returns multi-token labels when several period-separated terms
    in the prompt match the same region (e.g. 'angel skeleton witch').  Split by
    whitespace, keep only tokens that appear in the known vocabulary, deduplicate.

    For garbled concatenations (e.g. 'cauldronvil' = cauldron+anvil), scan each
    token for vocab substrings of length ≥4 as a fallback.
    Falls back to [] (drops the label) if nothing maps to vocabulary.
    """
    tokens = [t.lower().strip() for t in label.split() if t.strip()]
    known: list[str] = []
    for tok in tokens:
        if tok in _KNOWN_VOCAB:
            known.append(tok)
        elif len(tok) >= 8:
            # Garbled concatenation (e.g. 'cauldronvil' = cauldron+anvil):
            # scan for vocab words that are a prefix or suffix AND cover ≥55%
            # of the token length, so short words like 'vine' don't fire on
            # 'divine', 'old' on 'bold', etc.
            found = sorted(
                (v for v in _KNOWN_VOCAB if len(v) >= 4
                 and len(v) / len(tok) >= 0.55
                 and (tok.startswith(v) or tok.endswith(v))),
                key=len, reverse=True,
            )
            known.extend(found[:2])  # at most 2 recovered vocab words per token
    return list(dict.fromkeys(known)) if known else []


def motif_tags(prompt: str) -> list[str]:
    """Split a prompt into individual motif tags (legacy path)."""
    return [t.strip() for t in prompt.split() if t.strip()]


def _load_theo_lookup() -> dict[int, dict]:
    """Load TheoAlchemyDB emblem metadata keyed by emblem_number."""
    theo_path = Path(r"C:\Dev\TheosophicalAlchemyDB\data\maier_atalanta_fugiens_emblems_metadata.json")
    if not theo_path.exists():
        return {}
    try:
        data = json.loads(theo_path.read_text(encoding="utf-8"))
        return {e["emblem_number"]: e for e in data.get("emblems", [])}
    except Exception:
        return {}


_THEO_LOOKUP = _load_theo_lookup()


def enrich_theo(rec: dict, emblem_id: str) -> dict:
    """Add TheoAlchemyDB scholarly data if this is a Maier emblem."""
    import re
    m = re.search(r"emblem-(\d+)", emblem_id)
    if not m:
        return rec
    n = int(m.group(1))
    entry = _THEO_LOOKUP.get(n, {})
    if entry:
        rec["theo_title"]           = entry.get("english_title", "")
        rec["theo_stage"]           = entry.get("alchemical_stage", "")
        rec["theo_visual_elements"] = entry.get("visual_elements", [])
        rec["theo_planetary"]       = entry.get("planetary_association", "")
        rec["theo_color"]           = entry.get("color_association", "")
    return rec


def _load_claudiens_lookup() -> dict[str, dict]:
    """Build a filename→record lookup from claudiens site/data.json."""
    data_path = SOURCES_ROOT / "claudiens" / "site" / "data.json"
    if not data_path.exists():
        return {}
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        return {e.get("image", "").split("/")[-1]: e for e in entries if e.get("image")}
    except Exception:
        return {}


_CLAUDIENS_LOOKUP = _load_claudiens_lookup()


def enrich_claudiens(rec: dict, emblem_id: str) -> dict:
    """Add label, motto, stage from Claudiens metadata."""
    # emblem_id is like "emblem-37" → filename is "emblem-37.jpg"
    key = emblem_id + ".jpg"
    entry = _CLAUDIENS_LOOKUP.get(key, {})
    rec["emblem_label"] = entry.get("label", "")
    rec["motto"] = entry.get("motto", "")
    rec["stage"] = entry.get("stage", "")
    rec["furnace_fugue_url"] = ""
    return rec


EXTRACTED_ALL_DIR = PROJECT_ROOT / "assets" / "extracted_all"

ALL_SOURCES_MAP = {
    "claudiens":    ("Atalanta Fugiens (Maier)",        "claudiens"),
    "rosarium":     ("Rosarium Philosophorum",          "rosarium"),
    "splendor_solis": ("Splendor Solis (Trismosin)",   "splendor_solis"),
    "cramer":       ("Emblemata Sacra (Cramer 1624)",   "cramer"),
    "paul_marshall": ("Christian Rosenkreutz Anthology","paul_marshall"),
    "mclean":       ("McLean Second Emblem Collection", "mclean"),
    "obrist":       ("Obrist Medieval Imagery",         "obrist"),
    "khunrath":     ("Amphitheatrum Sapientiae (Khunrath)","khunrath"),
    "maier_arcana": ("Arcana Arcanissima (Maier)",      "maier_arcana"),
    "stolcius":     ("Stolcius Viridarium Chymicum",    "stolcius"),
    "mylius":       ("Mylius Philosophia Reformata",    "mylius"),
    "splendor":     ("Splendor Solis (Trismosin)",      "splendor_solis"),
    "hypnerotomachia": ("Hypnerotomachia Poliphili",    "hypnerotomachia"),
    "fludd":        ("Fludd — Mosaicall Philosophy",    "fludd"),
    "hall":         ("Hall Alchemical Manuscripts",     "hall"),
    "maier_af":     ("Atalanta Fugiens Mellon",         "maier_af"),
    "maier_viatorium": ("Viatorium (Maier)",            "maier_viatorium"),
}


def _project_from_stem(stem: str, fallback_src: str = "") -> tuple[str, str]:
    """Return (project_name, project_key) for a given image stem or source path."""
    text = (stem + " " + fallback_src).lower()
    if "claudiens" in text or "emblem-" in text:
        return "Atalanta Fugiens (Maier)", "claudiens"
    if "rosarium" in text:
        return "Rosarium Philosophorum", "rosarium"
    if "splendor_solis" in text or "splendor_solis" in stem:
        return "Splendor Solis (Trismosin)", "splendor_solis"
    if "cramer" in text:
        return "Emblemata Sacra (Cramer 1624)", "cramer"
    if "hypnerotomachia" in text:
        return "Hypnerotomachia Poliphili", "hypnerotomachia"
    for key, (proj_name, proj_key) in ALL_SOURCES_MAP.items():
        if key in text:
            return proj_name, proj_key
    return "Unknown", "unknown"


def load_comprehensive_extractions() -> list[dict]:
    """Load individual object extractions from assets/extracted_all/.

    Each detected object becomes a separate gallery record, enabling the
    gallery to show every extracted element (figure, animal, vessel, etc.)
    as its own card rather than one card per source image.
    """
    records = []
    if not EXTRACTED_ALL_DIR.exists():
        return records

    corrections = load_human_corrections()
    rejected = load_rejected_keys()

    for emblem_dir in sorted(EXTRACTED_ALL_DIR.iterdir()):
        if not emblem_dir.is_dir():
            continue
        src_stem = emblem_dir.name  # e.g. "emblem-08", "rosarium_page_0003"
        indiv_dir = emblem_dir / "individual"
        if not indiv_dir.exists():
            continue

        # Vision re-identification verdicts (written into summary.json by
        # scripts/reidentify_objects.py) override the detector label. Keyed by
        # the object stem (e.g. "bird_02" from "bird_02_crop.jpg").
        verified = {}
        summary_path = emblem_dir / "summary.json"
        if summary_path.exists():
            try:
                summ = json.loads(summary_path.read_text(encoding="utf-8"))
                for o in summ.get("individual", []):
                    if o.get("verified_label"):
                        key = Path(o.get("crop_jpg", "")).name
                        for suf in ("_crop.jpg", "_crop.jpeg", "_crop.png"):
                            if key.endswith(suf):
                                key = key[: -len(suf)]
                                break
                        verified[key] = o
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        for meta_path in sorted(indiv_dir.glob("*_meta.json")):
            try:
                raw = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            src = raw.get("source_image", "")
            project, project_key = _project_from_stem(src_stem, src)

            # Prefer a human/vision-verified label over the detector's guess.
            obj_stem = meta_path.stem[:-5] if meta_path.stem.endswith("_meta") else meta_path.stem
            v = verified.get(obj_stem)
            if v:
                vlabel = v.get("verified_label", "")
                # Drop crops re-identified as junk / category errors from the
                # gallery's object stream (non-animals, text pages from source
                # PDFs, whole-scene crops, unidentifiable fragments, and explicit
                # not-an-X verdicts).
                _DROP = {"not_an_animal", "unidentifiable", "text_page", "scene"}
                if vlabel in _DROP or vlabel.startswith("not_an_"):
                    continue
                raw_label = vlabel
            else:
                raw_label = raw.get("label", meta_path.stem)
            # Strip WordPiece ## sub-token markers left by older detector builds
            label = " ".join(tok.lstrip("#") for tok in str(raw_label).split()).strip()

            # A human reviewer's correction (review.html) outranks the detector
            # and any AI vision verified_label.
            #
            # Keyed by object_stem (the unique per-object filename stem, e.g.
            # "person_02"), NOT by label/prompt: comprehensive extraction
            # routinely gives several distinct objects in the same emblem the
            # identical generic prompt ("person" x5 on emblem-00 alone --
            # Aegle, Arethusa, Hesperusa, Venus, and Hippomenus all share the
            # literal string "person"). Keying by label would silently
            # collapse all of them onto one review decision and one
            # correction. object_stem is unique by construction (it's the
            # actual filename each extraction wrote).
            correction_key = f"{src_stem}__{obj_stem}"
            if correction_key in rejected:
                continue
            label_source = "vision-verified" if v else "detector"
            display_label = label
            if correction_key in corrections:
                display_label = corrections[correction_key]
                label_source = "human-corrected"

            rec = {
                "source_image":    src,
                "prompt":          label,
                "score":           raw.get("score", 0),
                "bbox":            raw.get("det_bbox", raw.get("tight_bbox", [])),
                "mask_pixel_count": raw.get("mask_pixel_count", 0),
                "extracted_at":    raw.get("extracted_at", ""),
                "transparent_png": raw.get("transparent_png", ""),
                "crop_jpg":        raw.get("crop_jpg", ""),
                "review_overlay":  raw.get("review_overlay", ""),
                "category":        raw.get("category", ""),
                "type":            raw.get("type", "individual"),
                "project":         project,
                "project_key":     project_key,
                "emblem_id":       src_stem,
                "object_stem":     obj_stem,
                "object_label":    display_label,
                "tags":            normalize_label_tags(display_label),
                "coverage_pct":    None,
                "label_source":    label_source,
            }
            if label_source == "human-corrected":
                rec["original_label"] = label  # audit trail; never silently dropped
            rec["transparent_png_web"] = relative_to_gallery(rec["transparent_png"])
            rec["crop_jpg_web"]        = relative_to_gallery(rec["crop_jpg"])
            rec["source_image_web"]    = relative_to_gallery(src)
            rec["review_overlay_web"]  = relative_to_gallery(rec["review_overlay"])
            rec["display_label"]       = f"{src_stem} — {display_label}"

            # Canonical ID for Claudiens
            import re as _re
            _m = _re.search(r"emblem-(\d+)", src_stem)
            if _m:
                rec["canonical_emblem_id"] = f"af_{int(_m.group(1)):02d}"
                enrich_claudiens(rec, src_stem)
                enrich_theo(rec, src_stem)
            else:
                rec["canonical_emblem_id"] = src_stem

            records.append(rec)

    return records


def load_all_extractions() -> list[dict]:
    records = []
    for meta_path in sorted(EXTRACTED_DIR.glob("*_meta.json")):
        try:
            rec = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        # Determine source project from image path
        src = rec.get("source_image", "")
        if "claudiens" in src:
            project = "Atalanta Fugiens (Maier)"
            project_key = "claudiens"
        elif "hypnerotomachia" in src:
            project = "Hypnerotomachia Poliphili"
            project_key = "hypnerotomachia"
        elif "cramer" in src or "cramer_page" in (Path(src).stem if src else ""):
            project = "Emblemata Sacra (Cramer 1624)"
            project_key = "cramer"
        elif "rosarium" in src or "rosarium_page" in (Path(src).stem if src else ""):
            project = "Rosarium Philosophorum"
            project_key = "rosarium"
        else:
            # Try to determine from source path segments or meta filename
            meta_stem = meta_path.stem
            SOURCE_MAP = {
                "paul_marshall":    ("Christian Rosenkreutz Anthology",   "paul_marshall"),
                "splendor_solis":   ("Splendor Solis (Trismosin)",        "splendor_solis"),
                "mclean_second":    ("McLean Second Emblem Collection",   "mclean"),
                "obrist":           ("Obrist Medieval Imagery",           "obrist"),
                "khunrath":         ("Amphitheatrum Sapientiae (Khunrath)","khunrath"),
                "maier_arcana":     ("Arcana Arcanissima (Maier)",        "maier_arcana"),
                "maier_viatorium":  ("Viatorium (Maier)",                 "maier_viatorium"),
                "maier_af_mellon":  ("Atalanta Fugiens Mellon",           "maier_af"),
                "fludd":            ("Fludd — Mosaicall Philosophy",      "fludd"),
                "hall_manuscript":  ("Hall Alchemical Manuscripts",       "hall"),
                "stolcius":         ("Stolcius Viridarium Chymicum",      "stolcius"),
                "mylius_philosophia": ("Mylius Philosophia Reformata",    "mylius"),
                "mylius_philosophia_plates": ("Mylius Philosophia Reformata", "mylius"),
            }
            matched = False
            for key, (proj_name, proj_key) in SOURCE_MAP.items():
                if key in src or key in meta_stem:
                    project = proj_name
                    project_key = proj_key
                    matched = True
                    break
            if not matched:
                project = "Unknown"
                project_key = "unknown"

        # Build web-relative paths
        rec["project"] = project
        rec["project_key"] = project_key
        rec["tags"] = normalize_label_tags(rec.get("prompt", ""))
        rec["transparent_png_web"] = relative_to_gallery(rec.get("transparent_png", ""))
        rec["crop_jpg_web"] = relative_to_gallery(rec.get("crop_jpg", ""))
        rec["source_image_web"] = relative_to_gallery(rec.get("source_image", ""))

        if rec.get("review_overlay"):
            rec["review_overlay_web"] = relative_to_gallery(rec["review_overlay"])
        else:
            rec["review_overlay_web"] = ""

        # Derive emblem/woodcut ID from source filename
        src_stem = Path(src).stem
        rec["emblem_id"] = src_stem
        rec["canonical_emblem_id"] = src_stem  # overridden below for Claudiens

        # Human-readable label
        prompt = rec.get("prompt", "")
        rec["display_label"] = f"{src_stem} — {prompt}"

        # Enrich from source project metadata
        if project_key == "claudiens":
            enrich_claudiens(rec, src_stem)
            enrich_theo(rec, src_stem)  # adds TheoAlchemyDB scholarly context
            # Canonical ID: "emblem-37" → "af_37" to match emblem_catalog.json
            import re as _re
            _m = _re.search(r"emblem-(\d+)", src_stem)
            if _m:
                rec["canonical_emblem_id"] = f"af_{int(_m.group(1)):02d}"

        # Coverage percentage (for quality indicator)
        img_path = Path(src)
        try:
            import cv2
            img = cv2.imread(str(resolve_path(src)))
            if img is not None:
                h, w = img.shape[:2]
                coverage = rec.get("mask_pixel_count", 0) / (h * w)
                rec["coverage_pct"] = round(coverage * 100, 1)
            else:
                rec["coverage_pct"] = None
        except Exception:
            rec["coverage_pct"] = None

        records.append(rec)

    # Deduplicate: keep only the most recently extracted record per (emblem_id, project)
    seen: dict[str, dict] = {}
    for rec in records:
        key = f"{rec['project_key']}:{rec['emblem_id']}"
        if key not in seen or rec.get("extracted_at", "") > seen[key].get("extracted_at", ""):
            seen[key] = rec
    records = list(seen.values())

    return records


def main():
    # Load comprehensive per-object extractions first
    comp_records = load_comprehensive_extractions()
    comp_stems = {r["emblem_id"] for r in comp_records}
    print(f"Comprehensive extractions: {len(comp_records)} objects from {len(comp_stems)} images")

    # Load legacy flat extractions, skipping any image already covered by comprehensive
    print(f"Scanning {EXTRACTED_DIR} for legacy extraction metadata...")
    legacy_records = load_all_extractions()
    legacy_records = [r for r in legacy_records if r["emblem_id"] not in comp_stems]
    print(f"Legacy extractions (non-comprehensive sources): {len(legacy_records)}")

    records = comp_records + legacy_records
    print(f"Total: {len(records)} elements")

    # Sort by project then emblem_id
    records.sort(key=lambda r: (r["project_key"], r["emblem_id"]))

    # Collect all unique tags
    all_tags = sorted(set(t for r in records for t in r["tags"]))
    all_projects = sorted(set(r["project"] for r in records))

    catalog = {
        "total": len(records),
        "tags": all_tags,
        "projects": all_projects,
        "records": records,
    }

    out_path = PROTOTYPE_DIR / "gallery_catalog.json"
    out_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Catalog written: {out_path}")
    print(f"  {len(records)} elements | {len(all_tags)} tags | {len(all_projects)} projects")


if __name__ == "__main__":
    main()
