"""
Reads emblem metadata from the source project files to build text prompts
for the detector, without manual prompt entry per image.

Searches three source projects in priority order:
  1. claudiens  - Maier Atalanta Fugiens emblem records
  2. hypnerotomachia-polyphili - Hypnerotomachia woodcut records
  3. theosophical-alchemy-db - broader alchemical emblem data

Returns extracted motif keywords as a natural-language detection prompt.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


SOURCES_ROOT    = Path(__file__).parent.parent.parent / "sources"
PROJECT_ROOT_META = Path(__file__).parent.parent.parent

# Controlled vocabulary mapping motif IDs (from data/motifs.json) to their
# detection terms. Each key is a motif id; the list contains the terms that
# GroundingDINO may return for that motif (the first entry is the canonical term).
# This aligns with the CATEGORY_PROMPTS in comprehensive_detector.py so that
# any detected label can be resolved to a motif record.
MOTIF_VOCABULARY: dict[str, list[str]] = {
    # FIGURES
    "figure":        ["person", "man", "woman", "figure", "pilgrim"],
    "warrior":       ["warrior"],
    "angel":         ["angel"],
    "king":          ["king", "crowned figure", "rex"],
    "queen":         ["queen", "crowned woman", "regina"],
    "hermaphrodite": ["hermaphrodite", "androgyne", "rebis", "coniunctio figure"],
    "philosopher":   ["old man", "philosopher", "witch"],
    "child":         ["child", "infant"],
    "skeleton":      ["skeleton", "death figure"],
    # ANIMALS
    "dragon":        ["dragon", "wyvern", "basilisk", "composite monster"],
    "lion":          ["lion", "feline", "beast"],
    "serpent":       ["serpent", "snake", "ouroboros"],
    "bird":          ["bird", "eagle"],
    "phoenix":       ["phoenix", "resurrection bird"],
    "pelican":       ["pelican"],
    "raven":         ["raven", "crow", "black bird"],
    "dove":          ["dove", "white bird"],
    "peacock":       ["peacock", "cauda pavonis"],
    "swan":          ["swan"],
    "horse":         ["horse", "steed"],
    "dog":           ["dog", "hound"],
    "wolf":          ["wolf"],
    "deer":          ["deer", "stag", "hart"],
    "ox":            ["ox", "bull"],
    "lamb":          ["lamb", "sheep"],
    "fish":          ["fish", "pisces"],
    "tortoise":      ["tortoise", "turtle"],
    "crab":          ["crab", "cancer"],
    "bee":           ["bee"],
    "butterfly":     ["butterfly", "psyche"],
    "fox":           ["fox"],
    "hare":          ["hare", "rabbit"],
    "bear":          ["bear"],
    # PLANTS
    "tree":          ["tree", "arbor philosophica", "branch", "bush"],
    "rose":          ["rose"],
    "lily":          ["lily"],
    "thistle":       ["thistle", "thorn"],
    "vine":          ["vine", "grape", "fruit"],
    "flower":        ["plant", "flower", "herb", "grass", "reed", "root", "palm"],
    "wreath":        ["wreath", "laurel"],
    "oak":           ["oak"],
    # LANDSCAPE
    "mountain":      ["mountain", "rock", "cliff", "hill", "cave", "rocky landscape"],
    "fountain":      ["fountain", "spring", "well", "wave"],
    "sun":           ["sun", "solar disc", "crowned sun"],
    "moon":          ["moon", "lunar crescent", "crowned moon"],
    "star":          ["star", "celestial body", "zodiac"],
    "fire":          ["fire", "flame"],
    "water":         ["water", "river"],
    "sea":           ["sea", "ocean"],
    "cloud":         ["cloud", "sky"],
    "earth":         ["earth", "forest", "volcano"],
    "rainbow":       ["rainbow"],
    "lightning":     ["lightning"],
    # ARCHITECTURE
    "furnace":       ["furnace", "athanor", "hearth", "chimney", "lab equipment"],
    "castle":        ["castle", "tower", "building", "wall", "ruin", "house"],
    "temple":        ["temple", "altar"],
    "bridge":        ["bridge"],
    "labyrinth":     ["labyrinth", "maze"],
    "gate":          ["gate", "arch", "column", "door", "window"],
    "tomb":          ["tomb", "obelisk"],
    # OBJECTS
    "vessel":        ["vessel", "flask", "retort", "cauldron", "cup", "chalice",
                      "alembic", "amphora", "egg", "philosophical egg"],
    "crucible":      ["crucible"],
    "sword":         ["sword"],
    "spear":         ["spear", "lance"],
    "shield":        ["shield"],
    "staff":         ["staff", "wand"],
    "scepter":       ["scepter", "sceptre", "royal staff"],
    "key":           ["key"],
    "chain":         ["chain", "rope"],
    "crown":         ["crown"],
    "ring":          ["ring"],
    "book":          ["book", "scroll"],
    "torch":         ["torch", "lamp", "candle"],
    "mirror":        ["mirror"],
    "hourglass":     ["hourglass"],
    "scales":        ["scales", "balance"],
    "globe":         ["globe", "sphere", "orb"],
    "wheel":         ["wheel", "bellows"],
    "axe":           ["axe", "hammer", "scythe"],
    "musical_instrument": ["lute", "trumpet", "drum"],
}

# Reverse lookup: detection term → motif id
TERM_TO_MOTIF_ID: dict[str, str] = {
    term: motif_id
    for motif_id, terms in MOTIF_VOCABULARY.items()
    for term in terms
}


def get_prompt_for_image(image_path: str) -> str | None:
    """
    Look up the source emblem record for image_path and build a detection prompt.

    Returns a natural-language string like "lion beast animal" or None if no
    metadata is found (caller should fall back to manual prompt).
    """
    image_path = Path(image_path)
    filename = image_path.stem  # e.g. "emblem-37" or "hp1499_p393"

    # Try claudiens first
    prompt = _prompt_from_claudiens(filename, image_path)
    if prompt:
        return prompt

    # Try hypnerotomachia
    prompt = _prompt_from_hypnerotomachia(filename, image_path)
    if prompt:
        return prompt

    # Try theosophical db
    prompt = _prompt_from_theosophical(filename, image_path)
    if prompt:
        return prompt

    return None


# Hard-coded overrides for Claudiens emblems whose discourse doesn't surface
# motif vocabulary terms automatically (narrative/geometric/mythological figures).
_CLAUDIENS_OVERRIDES: dict[int, str] = {
    0:  "running woman figure",          # Atalanta fleeing
    1:  "infant child earth figure",     # nurse is the earth
    2:  "infant child earth figure",     # nurse is the earth (variant)
    3:  "woman washing figure",          # woman washing sheets
    4:  "man woman figure",              # brother and sister joined
    5:  "woman figure toad animal",      # woman suckling toad
    6:  "man sowing figure earth",       # sow gold in white earth
    11: "woman figure moon",             # Latona / whitening
    12: "woman figure moon",             # Latona / whitening (variant)
    15: "man figure vessel clay",        # potter's work
    20: "figure nature",                 # nature teaches nature
    21: "man woman figure geometric",    # circle-square-triangle
    23: "figure rain gold",              # gold rains at Rhodes
    39: "sphinx monster man figure",     # Oedipus and the Sphinx
    41: "boar animal man woman",         # Adonis killed by boar, Venus
}


def _prompt_from_claudiens(filename: str, image_path: Path) -> str | None:
    """Search Claudiens emblem data for matching emblem."""
    claudiens_root = SOURCES_ROOT / "claudiens"
    if not claudiens_root.exists():
        return None

    # Check hard-coded overrides first (for emblems with no vocabulary match)
    match_num = re.search(r"emblem[_-](\d+)", filename, re.IGNORECASE)
    if match_num:
        emblem_num = int(match_num.group(1))
        if emblem_num in _CLAUDIENS_OVERRIDES:
            return _CLAUDIENS_OVERRIDES[emblem_num]

    # Primary source: site/data.json — matches by "image" field path suffix
    site_data_path = claudiens_root / "site" / "data.json"
    if site_data_path.exists():
        try:
            data = json.loads(site_data_path.read_text(encoding="utf-8"))
            entries = data.get("entries", data) if isinstance(data, dict) else data
            for record in entries:
                if not isinstance(record, dict):
                    continue
                rec_image = record.get("image", "")
                # Match: "images/emblems/emblem-37.jpg" ends with filename
                if rec_image.endswith(filename + ".jpg") or rec_image.endswith(filename):
                    return _extract_prompt_from_record(record)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    # Fallback: match by emblem number in emblem_manifest.json
    manifest_path = claudiens_root / "data" / "emblem_manifest.json"
    if manifest_path.exists():
        match = re.search(r"emblem[_-](\d+)", filename, re.IGNORECASE)
        if match:
            emblem_num = int(match.group(1))
            try:
                records = json.loads(manifest_path.read_text(encoding="utf-8"))
                for record in records:
                    if not isinstance(record, dict):
                        continue
                    if record.get("number") == emblem_num:
                        return _extract_prompt_from_record(record)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    return None


_hp_woodcut_cache: dict[int, dict] | None = None


def _load_hp_woodcut_data() -> dict[int, dict]:
    """
    Parse the HP seed_1499_woodcuts.py to get page → description/title lookup.
    The seed script stores (page_1499, signature, title, description, context, category)
    tuples; we extract them with regex rather than importing the script.
    """
    global _hp_woodcut_cache
    if _hp_woodcut_cache is not None:
        return _hp_woodcut_cache

    seed_path = (
        SOURCES_ROOT / "hypnerotomachia-polyphili" / "scripts" / "seed_1499_woodcuts.py"
    )
    _hp_woodcut_cache = {}
    if not seed_path.exists():
        return _hp_woodcut_cache

    text = seed_path.read_text(encoding="utf-8")
    # Match tuples: (page_int, "sig", "title", "description", "context", "CATEGORY")
    pattern = re.compile(
        r'\(\s*(\d+)\s*,\s*"[^"]*"\s*,\s*"([^"]*)"\s*,\s*"([^"]*)"\s*,\s*"([^"]*)"\s*,\s*"([^"]*)"',
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        page = int(m.group(1))
        _hp_woodcut_cache[page] = {
            "title": m.group(2),
            "description": m.group(3),
            "scene": m.group(4),
            "category": m.group(5),
        }
    return _hp_woodcut_cache


def _prompt_from_hypnerotomachia(filename: str, image_path: Path) -> str | None:
    """Search Hypnerotomachia seed data for matching woodcut by page number."""
    # Filename format: hp1499_p330.jpg → page 330
    match = re.search(r"_p(\d+)", filename)
    if not match:
        return None
    page_num = int(match.group(1))

    woodcuts = _load_hp_woodcut_data()
    # Try exact match and ±1 (IA offset differences)
    for candidate_page in [page_num, page_num - 1, page_num + 1]:
        record = woodcuts.get(candidate_page)
        if record:
            return _extract_prompt_from_record(record)

    return None


def _prompt_from_theosophical(filename: str, image_path: Path) -> str | None:
    """Search theosophical-alchemy-db for matching emblem."""
    theo_root = SOURCES_ROOT / "theosophical-alchemy-db"
    if not theo_root.exists():
        return None

    for json_path in theo_root.rglob("*.json"):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        records = data if isinstance(data, list) else [data]
        for record in records:
            if not isinstance(record, dict):
                continue
            rec_file = str(record.get("filename", "") or record.get("image", "") or "")
            if filename.lower() in rec_file.lower():
                return _extract_prompt_from_record(record)

    return None


def _extract_prompt_from_record(record: dict) -> str | None:
    """
    Pull motif keywords from a metadata record and return a detection prompt string.

    Looks in: tags, motifs, visual_elements, description, title, motto, discourse fields.
    Maps found terms to our controlled MOTIF_VOCABULARY for better model recall.
    """
    text_fields = []
    for field in ("tags", "motifs", "visual_elements", "visual_tags", "elements"):
        val = record.get(field)
        if isinstance(val, list):
            text_fields.extend(str(v) for v in val)
        elif isinstance(val, str):
            text_fields.append(val)

    for field in ("description", "title", "motto", "caption", "notes", "label", "discourse", "scene"):
        val = record.get(field)
        if isinstance(val, str):
            text_fields.append(val)

    combined = " ".join(text_fields).lower()

    # Match against vocabulary
    matched_terms = []
    for motif_key, synonyms in MOTIF_VOCABULARY.items():
        for syn in synonyms:
            if syn.lower() in combined:
                # Add the primary term plus first synonym for richer prompt
                matched_terms.append(motif_key)
                matched_terms.append(synonyms[0])
                break

    if not matched_terms:
        return None

    # Deduplicate while preserving order
    seen = set()
    unique_terms = []
    for t in matched_terms:
        if t not in seen:
            seen.add(t)
            unique_terms.append(t)

    return " ".join(unique_terms[:6])  # GroundingDINO handles multi-word prompts well


# ── Equipment-focused extraction ─────────────────────────────────────────────
# These prompts target alchemical apparatus rather than figures.
# Run as a separate batch pass with: batch_extract.py --mode equipment
EQUIPMENT_PROMPTS: list[str] = [
    "athanor furnace apparatus",
    "alchemical flask retort vessel",
    "alembic distillation vessel",
    "philosophical egg glass vessel",
    "crucible fire heating",
    "bellows fire apparatus",
    "scales balance measuring instrument",
    "distillation apparatus glass tube",
]

# Motifs that indicate alchemical equipment is present in the scene
EQUIPMENT_MOTIFS = {
    "furnace", "vessel", "athanor", "retort", "alembic", "crucible",
    "flask", "scales", "balance", "distillation", "apparatus",
}

# ── Cramer / Stolcius source metadata ────────────────────────────────────────
# Visual element descriptions for Cramer Emblemata Sacra (1617/1624)
# These are the 50 emblems on sacred/Rosicrucian themes; visual content
# is largely figurative with angels, hearts, crosses, and symbolic objects.
_CRAMER_PROMPTS: dict[int, str] = {
    # Page-number keys correspond to cramer_plate_XXXX.jpg numbering
    # Prompts will be derived from the image itself since Cramer metadata
    # is not as rich in TheoAlchemyDB. Using broad figurative prompts.
    # This dict is a fallback — auto-extraction uses visual content.
}

# For Cramer pages without known metadata, use these broad prompts by emblem theme
CRAMER_DEFAULT_PROMPTS = [
    "angel figure heart",
    "cross figure man",
    "heart flame figure",
    "figure symbolic emblem",
]


def list_available_emblems(include_wellcome: bool = True) -> list[dict]:
    """
    Return a list of all emblems/woodcuts we have metadata for,
    with their image path and auto-generated prompt.
    Useful for batch extraction planning.
    """
    emblems = []

    claudiens_images = (SOURCES_ROOT / "claudiens").rglob("emblem-*.jpg") if (
        SOURCES_ROOT / "claudiens"
    ).exists() else []
    for img_path in sorted(claudiens_images):
        prompt = get_prompt_for_image(str(img_path))
        emblems.append({
            "source_project": "claudiens",
            "image_path": str(img_path),
            "auto_prompt": prompt,
        })

    hp_images = (SOURCES_ROOT / "hypnerotomachia-polyphili").rglob("*.jpg") if (
        SOURCES_ROOT / "hypnerotomachia-polyphili"
    ).exists() else []
    for img_path in sorted(hp_images):
        if "woodcuts_1499" in str(img_path):
            prompt = get_prompt_for_image(str(img_path))
            emblems.append({
                "source_project": "hypnerotomachia",
                "image_path": str(img_path),
                "auto_prompt": prompt,
            })

    # All additional sourced corpora — read provenance.json from each
    NEW_SOURCES = {
        "paul_marshall":    ("Rosicrucian Emblems anthology", "alchemical figure rose cross emblem"),
        "splendor_solis":   ("Splendor Solis",                "alchemical king queen sun moon vessel figure"),
        "mclean_second":    ("McLean Second Collection",      "alchemical emblem hermetic figure symbol"),
        "obrist_medieval":  ("Obrist Medieval Imagery",       "medieval alchemical figure vessel dragon"),
        "khunrath":         ("Khunrath Amphitheatrum",        "oratory laboratory alchemical divine figure"),
        "maier_arcana":     ("Maier Arcana Arcanissima",      "hieroglyphic figure emblem allegorical"),
        "maier_viatorium":  ("Maier Viatorium",               "alchemical figure emblem symbol mountain"),
        "maier_af_mellon":  ("Maier Atalanta Fugiens Mellon", "atalanta figure emblem alchemical"),
        "fludd":            ("Fludd Philosophy",              "macrocosm microcosm divine figure cosmos"),
        "hall_manuscripts": ("Hall Alchemical Manuscripts",   "manuscript alchemical figure hermetic"),
        "stolcius":         ("Stolcius Viridarium Chymicum",  "alchemical figure emblem hermetic vessel"),
        "mylius_philosophia": ("Mylius Philosophia Reformata", "alchemical figure emblem vessel stage"),
        "mylius_philosophia_plates": ("Mylius Philosophia Reformata (plates)", "alchemical figure emblem vessel stage"),
    }
    # Override paths for sources that use a non-standard subdirectory
    _SRC_PATH_OVERRIDES = {
        "mylius_philosophia_plates": PROJECT_ROOT_META / "sources" / "mylius_philosophia" / "plates",
    }

    for src_key, (src_name, default_prompt) in NEW_SOURCES.items():
        src_root = _SRC_PATH_OVERRIDES.get(src_key,
                   PROJECT_ROOT_META / "sources" / src_key / "images")
        if src_root.exists():
            for img_path in sorted(src_root.rglob("*.jpg")):
                emblems.append({
                    "source_project": src_key,
                    "image_path": str(img_path),
                    "auto_prompt": default_prompt,
                })

    # Cramer Emblemata Sacra (downloaded from Internet Archive)
    cramer_root = PROJECT_ROOT_META / "sources" / "cramer" / "images"
    if include_wellcome and cramer_root.exists():
        import itertools
        for img_path in sorted(cramer_root.rglob("*.jpg")):
            # Rotate through default prompts for variety
            idx = int(re.search(r"(\d+)", img_path.stem).group(1)) if re.search(r"(\d+)", img_path.stem) else 0
            prompt = CRAMER_DEFAULT_PROMPTS[idx % len(CRAMER_DEFAULT_PROMPTS)]
            emblems.append({
                "source_project": "cramer",
                "image_path": str(img_path),
                "auto_prompt": prompt,
            })

    # Rosarium Philosophorum (downloaded from Internet Archive)
    rosarium_root = PROJECT_ROOT_META / "sources" / "rosarium" / "images"
    if include_wellcome and rosarium_root.exists():
        for img_path in sorted(rosarium_root.rglob("*.jpg")):
            emblems.append({
                "source_project": "rosarium",
                "image_path": str(img_path),
                "auto_prompt": "king queen figure vessel",  # Rosarium's main motif
            })

    return emblems


