# Visual Element Extraction Strategy

## Current Approach: Comprehensive Multi-Category Extraction

The extraction pipeline now runs in **comprehensive mode**: every object in every emblem is detected and segmented across six semantic categories, with composite extractions for overlapping objects.

### Six Extraction Categories

| Category | What it covers |
|----------|---------------|
| **figures** | person, man, woman, angel, child, king, queen, hermaphrodite, skeleton, warrior, old man/philosopher, witch, pilgrim |
| **animals** | lion, eagle, serpent, dragon, horse, dog, wolf, fish, deer, bear, ox, lamb, peacock, swan, dove, raven, pelican, phoenix, tortoise, crab, bee, butterfly, frog, hare, fox |
| **plants** | tree, flower, herb, rose, lily, thistle, vine, wreath, laurel, oak, grass, reed, palm, thorn |
| **landscape** | mountain, rock, river, water, sea, cloud, sun, moon, star, fire, flame, earth, sky, cave, spring, rainbow, lightning, volcano, forest |
| **architecture** | castle, tower, furnace, athanor, hearth, bridge, temple, altar, labyrinth, tomb, obelisk, gate, arch, column |
| **objects** | sword, spear, shield, axe, staff, wand, scepter, key, chain, crown, ring, book, scroll, torch, lamp, mirror, hourglass, vessel, flask, retort, cauldron, chalice, globe, egg, wheel, bellows, scales, crucible, anvil, lute, trumpet, drum |

### Overlap Handling

When objects physically overlap in the plate (a man holding a sword, a figure standing on a mountain, a dragon coiling around a tree), the pipeline:

1. Extracts each object **individually** — the man alone, the sword alone
2. Detects overlap using pairwise containment ratio (intersection / min-area)
3. Extracts **composites** — the man-with-sword together as a single cutout

Overlap threshold is 15% containment by default; tune with `--overlap-threshold`.

### Pipeline Architecture

```
source emblem image
    ↓
[comprehensive_detector.py] ← 6 GroundingDINO passes, one per category
    → all detections merged and NMS-deduplicated (IoU > 0.5 collapses duplicates)
    ↓
[segmenter.py] × N detections
    → SAM ViT-base bbox → pixel mask per object
    ↓
[postprocessor.py] per mask
    → paper background removal (Otsu ink detection)
    → bridge removal (severs thin hatching connections to background)
    → figure component selection (keeps only bbox-overlapping components)
    ↓
[overlap_analyzer.py]
    → pairwise containment matrix
    → union-find grouping of overlapping objects
    → composite masks for each group
    ↓
per-emblem output:  assets/extracted_all/{stem}/
    individual/  {label}_transparent.png + _crop.jpg + _review.jpg + _meta.json
    composites/  {label_a}+{label_b}_composite_transparent.png + ...
    summary.json
    ↓
[build_object_catalog.py]
    → reads summary.json
    → writes object_catalog into data/emblems.json emblem record
    → appends new entries to data/visual_elements.json
```

### Object Catalog in Emblem Records

After running `build_object_catalog.py`, each emblem record in `data/emblems.json` contains:

```json
"object_catalog": [
  {
    "type": "individual",
    "label": "lion",
    "motif_id": "lion",
    "category": "animals",
    "detection_score": 0.73,
    "appearance": "Rampant lion facing left, hatched mane...",
    "iconographic_meaning": "The green lion (vitriol) devours the sun...",
    "alchemical_valence": ["sulphur", "fixation", "sol", "dissolution"],
    "review_status": "auto",
    "transparent_png": "assets/extracted_all/emblem-37/individual/lion_transparent.png",
    "crop_jpg": "assets/extracted_all/emblem-37/individual/lion_crop.jpg"
  },
  {
    "type": "composite",
    "label": "lion + sun",
    "constituent_motif_ids": ["lion", "sun"],
    "appearance": "...",
    "iconographic_meaning": "...",
    "transparent_png": "assets/extracted_all/emblem-37/composites/lion+sun_composite_transparent.png"
  }
]
```

The `appearance` and `iconographic_meaning` fields are seeded from the canonical motifs.json descriptions and should be refined with emblem-specific annotation. The `review_status` field is `"auto"` until a human reviewer approves (`"approved"`) or flags (`"flagged"`) the entry.

### Motif Ontology (`data/motifs.json`)

The motif vocabulary (65 entries) defines every detectable object class. Each entry contains:

| Field | Content |
|-------|---------|
| `id` | Canonical identifier, matches `MOTIF_VOCABULARY` in metadata.py |
| `label` | Human-readable name |
| `category` | One of six extraction categories |
| `variants` | Synonyms and sub-types |
| `detection_terms` | Exact terms used in GroundingDINO prompts |
| `appearance` | How this object looks in early modern engraving |
| `description` | Iconographic meaning in alchemical/emblematic tradition |
| `alchemical_valence` | Alchemical associations and operations |
| `planetary` | Planetary ruler (null if none) |

## Questions Settled by the Current Approach

The original strategy document raised these questions; current answers:

- **"Do we want 'visual element' to mean the whole depicted object, or only a clean isolated silhouette?"** → Both: individual objects are extracted separately; overlapping objects are also extracted together as composites.
- **"Should a monster crop include its victim/prey?"** → Yes, as a composite. The dragon and the king it devours are extracted separately, then together.
- **"Are we cataloging for scholarship, reusable design assets, or both?"** → Both. The motifs.json gives scholarly iconographic meaning; the transparent PNGs give reusable design assets.
- **"Do we want a controlled motif vocabulary from the start?"** → Yes. `data/motifs.json` is the controlled vocabulary, aligned with `MOTIF_VOCABULARY` in `metadata.py` and `CATEGORY_PROMPTS` in `comprehensive_detector.py`.
- **"Should crops preserve the original paper tone, or be transparent?"** → Transparent PNG (RGBA) is the default asset; crop JPGs are kept for reference.

## Human Review Workflow

After automatic extraction:

1. Run `build_object_catalog.py` to write `object_catalog` into emblem records
2. Open `prototype/review.html` to approve/flag individual and composite extractions
3. Refine `appearance` and `iconographic_meaning` fields in flagged entries
4. Promote `review_status` from `"auto"` to `"approved"` once verified

The `review_overlay` JPG (side-by-side original vs red-masked) is generated for every extraction to facilitate rapid visual review.
