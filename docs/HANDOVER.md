# Emblem Print Shop — Project Handover Document

**Date**: 2026-06-04  
**Status**: Active — cross-page gallery linking, review queue, Stolcius/Mylius sources found  
**Continuing in**: `C:\Dev\EmblemPrintShop`

---

## 1. What This Project Is

A **scholarly visual inventory and extraction pipeline** for early modern alchemical emblem books. The goal is a print-shop-style library of reusable visual elements — lions, dragons, vessels, furnaces, hermaphrodites, ouroboros, peacocks — extracted as transparent PNGs from digitized emblem plates, cataloged with full alchemical metadata, and browsable through a web gallery.

**Not** a general image processing tool. Everything is specific to:
- 17th-century intaglio/woodcut prints (dense hatching, paper tone, overlapping figures)
- Alchemical iconography (dragons coiled as ouroboros, king/queen conjunctions, Splendor Solis illuminations)
- Multi-layer scholarly metadata (stage, planetary association, concept links, De Jong scholarship)

---

## 2. Repository Structure

```
C:\Dev\EmblemPrintShop\
├── assets/
│   ├── cutout-examples/      # Original hand-made reference cutouts (ground truth)
│   └── extracted/            # Pipeline output: transparent PNGs, crops, meta JSONs
├── docs/
│   ├── HANDOVER.md           # This file
│   ├── SOURCE_INVENTORY_COMPREHENSIVE.md  # What's been sourced, what's missing
│   └── VISUAL_ELEMENT_EXTRACTION_STRATEGY.md
├── prototype/
│   ├── gallery.html          # Element gallery (filter by motif, project, confidence)
│   ├── emblems.html          # Emblem catalog (full metadata, concept links, discourse)
│   ├── gallery_catalog.json  # Built by build_catalog.py — drives gallery.html
│   ├── emblem_catalog.json   # Built by build_emblem_catalog.py — drives emblems.html
│   └── serve.py              # Local HTTP server: python prototype/serve.py → localhost:8765
├── scripts/
│   ├── extract_element.py    # CLI: python scripts/extract_element.py <image> --prompt "lion"
│   ├── batch_extract.py      # Batch extraction across all sources
│   ├── batch_extract.py      # Equipment mode: --mode equipment
│   ├── build_catalog.py      # Rebuild gallery_catalog.json
│   ├── build_emblem_catalog.py  # Rebuild emblem_catalog.json
│   ├── source_all_emblems.py # Download + extract PDFs from IA and local
│   ├── fetch_ia_emblems.py   # Download individual IA sources
│   ├── theoalchemy_extract.py # Re-extract Maier 1-20 with TheoAlchemyDB prompts
│   ├── extract_all_objects.py    # Comprehensive single-emblem extraction  [NEW]
│   ├── batch_extract_all.py      # Batch comprehensive extraction  [NEW]
│   ├── build_object_catalog.py   # Write object_catalog into emblems.json  [NEW]
│   └── pipeline/
│       ├── detector.py               # GroundingDINO: text → bbox
│       ├── comprehensive_detector.py # 6-category all-object detection  [NEW]
│       ├── overlap_analyzer.py       # Pairwise overlap matrix + composites  [NEW]
│       ├── segmenter.py              # SAM ViT-base: bbox → pixel mask
│       ├── postprocessor.py          # Background removal, hole-fill, bridge removal
│       ├── extractor.py              # Targeted pipeline orchestrator
│       └── metadata.py               # MOTIF_VOCABULARY + TERM_TO_MOTIF_ID lookup
├── sources/                  # Raw emblem image sources (NOT the pipeline output)
│   ├── claudiens/            # Maier Atalanta Fugiens images + scholarly data
│   ├── cramer/               # Cramer Emblemata Sacra (from IA PDF)
│   ├── rosarium/             # Rosarium Philosophorum (from IA PDF)
│   ├── paul_marshall/        # Christian Rosenkreutz Anthology (local PDF)
│   ├── splendor_solis/       # Splendor Solis (local + IA)
│   ├── mclean_second/        # McLean Second Collection
│   ├── obrist_medieval/      # Obrist medieval imagery (Claudiens & TheoAlchemyDB)
│   ├── khunrath/             # Amphitheatrum Sapientiae Aeternae (IA)
│   ├── maier_arcana/         # Arcana Arcanissima (IA)
│   └── hypnerotomachia-polyphili/  # HP woodcuts
└── tests/
    ├── test_detector.py           # 5 GroundingDINO behavioral tests
    ├── test_segmenter.py          # 5 SAM behavioral tests
    ├── test_postprocessor.py      # 5 postprocessor tests
    ├── test_pipeline_integration.py  # 6 end-to-end tests
    └── test_boundary_fixes.py     # 7 boundary quality tests (donut hole, bridge removal)
```

---

## 3. The Data Ontology

### Unified Emblem Record (synthesized from Claudiens + TheoAlchemyDB)

```
IDENTITY
  id                    "af_37"
  source_work           "Atalanta Fugiens"
  source_key            "claudiens"
  emblem_number         37
  roman                 "XXXVII"
  label                 "Emblem XXXVII"
  latin_title           "Si vis perfectum..."
  english_title         "Self-Nourishment and Closed System"

TEXTUAL CONTENT
  motto                 "Three things are sufficient..."
  motto_source          "Alchemical tradition"
  discourse             [full Maier discourse paragraph]
  de_jong_pages         "125-130"

ALCHEMICAL CLASSIFICATION
  stage                 "CITRINITAS"   ← enum: NIGREDO / ALBEDO / CITRINITAS / RUBEDO
  stage_detailed        "Late Work - Self-Sustaining Perfection"
  color_association     "Red (mature, perfected)"
  planetary_association "Sol (self-luminous, self-sufficient)"
  divine_principle      "The infinite regress of divine self-reflection"
  spiritual_meaning     "The soul consuming and perfecting its own essence"

ICONOGRAPHIC
  visual_elements       ["Self-feeding figure (ouroboros)", "Circular ingestion"]
  key_concepts          ["Self-Sufficiency", "Ouroboros", "Closed System"]
  related_emblems       [1, 9]

PROVENANCE
  confidence            "HIGH"
  sources               ["AUTH_LULLIUS", "AUTH_ROSARIUM", "AUTH_SOLOMONIC"]
  de_jong_pages         "125-130"

IMAGES
  image_path            "sources/claudiens/site/images/emblems/emblem-37.jpg"
  extracted_elements    [{prompt, score, bbox, transparent_png, crop_jpg, ...}]  ← legacy

OBJECT CATALOG  (new — populated by build_object_catalog.py after comprehensive extraction)
  object_catalog        [
    {
      "type":                 "individual" | "composite",
      "label":                "lion",
      "motif_id":             "lion",          ← maps to data/motifs.json id
      "constituent_motif_ids": null,           ← for composites: ["lion","sun"]
      "category":             "animals",
      "detection_score":      0.73,
      "appearance":           "Rampant lion facing left...",   ← emblem-specific description
      "iconographic_meaning": "Green lion = vitriol...",       ← emblem-specific interpretation
      "alchemical_valence":   ["sulphur","fixation","sol"],
      "review_status":        "auto" | "approved" | "flagged",
      "transparent_png":      "assets/extracted_all/emblem-37/individual/lion_transparent.png",
      "crop_jpg":             "assets/extracted_all/emblem-37/individual/lion_crop.jpg"
    }
  ]
  object_catalog_count  {"individual": 8, "composite": 3, "total": 11}
  object_catalog_extracted_at  "2026-06-03T..."

CONCEPT LINKS
  concept_links         [{concept_id, concept_name, link_type, confidence, explanation}]
```

### Source Databases

**Claudiens** (`C:\Dev\Claudiens`, `sources/claudiens/`):
- `site/data.json` — 51 AF emblem records: number, roman, label, motto, discourse, stage, confidence, sources
- `data/emblem_manifest.json` — image file grounding, latin_motto, page in 1618 edition, Furnace & Fugue URLs
- `site/visual-data.json` — visual tags, dict_tags, folio references
- `site/dictionary-depicts.json` — motif→emblem cross-reference
- Schema in `C:\Dev\Claudiens\docs\ONTOLOGY.md` — 48+ field emblem schema

**TheosophicalAlchemyDB** (`C:\Dev\TheosophicalAlchemyDB`):
- `data/maier_atalanta_fugiens_emblems_metadata.json` — De Jong scholarship for emblems 1-20: visual_elements, key_concepts, planetary_association, divine_principle, spiritual_meaning, color_association, related_emblems, de_jong_pages
- `data/prototype_data.json` — 178 emblems across AF/Hermetic Garden/Rosicrucian Emblems with figures, concepts, scholarship
- `docs/COMPREHENSIVE_CONCEPT_EMBLEM_MAPPINGS.json` — 67 concepts × 178 emblems: link_type, confidence, explanation, scholarly_support

---

## 4. The Extraction Pipeline

Two modes: **comprehensive** (new, recommended) and **targeted** (legacy, one prompt per emblem).

### Comprehensive Extraction Architecture

```
source emblem image
    ↓
[comprehensive_detector.py] — 6 GroundingDINO passes (one per category)
    categories: figures | animals | plants | landscape | architecture | objects
    → all detections merged, NMS-deduplicated (IoU > 0.5 collapses cross-category dupes)
    ↓
[segmenter.py] × N detections
    → SAM ViT-base: bbox → pixel mask for each object
    ↓
[postprocessor.py] per mask
    → remove_paper_background: Otsu ink detection + dilation + hole fill
    → remove_background_bridges: morphological opening (10px) severs hatching bridges
    → select_figure_mask: keeps only connected components overlapping core bbox
    → _fill_holes_smart: fills holes < 1% image area only (donut-hole fix)
    ↓
[overlap_analyzer.py]
    → compute_overlap_matrix: pairwise containment ratio (intersection / min-area)
    → find_overlap_groups: union-find clustering of objects with > 15% containment
    → build_composite_mask: pixel-wise union of overlapping object masks
    ↓
output:  assets/extracted_all/{emblem_stem}/
    individual/   {label}_transparent.png + _crop.jpg + _review.jpg + _meta.json
    composites/   {label_a}+{label_b}_composite_transparent.png + ...
    summary.json  ← machine-readable record of all detections, masks, groups
    ↓
[build_object_catalog.py]
    → reads summary.json for each emblem stem
    → writes object_catalog[] into matching data/emblems.json record
    → appends new entries to data/visual_elements.json
```

### Targeted Extraction Architecture (legacy)

```
source image + text prompt
    ↓
[GroundingDINO-tiny] → bounding box (score, label)
    ↓
[SAM ViT-base] → pixel mask
  - Point+box prompting for large-scene detections (>35% bbox)
  - _pick_best_mask: smallest mask covering detection center
    ↓
[remove_background_bridges] → sever thin hatching connections (10px bridge)
    ↓
[select_figure_mask] → keep only components overlapping core bbox
    ↓
[remove_paper_background] → Otsu ink detection, dilation, hole fill
    ↓
[_fill_holes_smart] → fill ONLY holes <1% of image (donut-hole fix)
    ↓
transparent PNG + crop JPG + review overlay + meta JSON
```

### Key Design Decisions

1. **Both failures fixed:**
   - "Clipped extremities" (lion legs): bbox expanded 20% + SAM dilation
   - "Background leakage" (lion+mountain): morphological bridge removal (10px kernel)
   - "Donut hole" (ouroboros interior): size-limited hole filling (<1% threshold)

2. **CPU-only**: PyTorch 2.10+cpu, no GPU needed

3. **Models** (cached in HuggingFace hub after first run):
   - `IDEA-Research/grounding-dino-tiny` — text → bbox
   - `facebook/sam-vit-base` — bbox → mask

4. **Timing**: ~50-60 seconds per image on modern CPU

### Running Extraction

**Comprehensive mode (recommended — all objects, all categories, with composites):**
```bash
# Single emblem: extract every object
python -m scripts.extract_all_objects sources/claudiens/site/images/emblems/emblem-37.jpg

# Tune detection sensitivity
python -m scripts.extract_all_objects emblem.jpg --threshold 0.20 --overlap-threshold 0.10

# Run on a specific category subset only
python -m scripts.extract_all_objects emblem.jpg --categories figures animals

# Batch: whole collection, skip already-done
python -m scripts.batch_extract_all claudiens --resume
python -m scripts.batch_extract_all claudiens rosarium splendor_solis

# Update emblem records with object catalogs
python -m scripts.build_object_catalog
python -m scripts.build_object_catalog --stem emblem-37 --dry-run
```

**Targeted mode (legacy — single prompt per emblem):**
```bash
# Single image
python scripts/extract_element.py sources/claudiens/site/images/emblems/emblem-37.jpg --prompt "lion"

# All Claudiens emblems (auto-prompts from metadata)
python scripts/batch_extract.py --source claudiens --output assets/extracted/

# Equipment pass (athanor, vessel, retort, etc.)
python scripts/batch_extract.py --mode equipment --source claudiens --output assets/extracted/

# TheoAlchemyDB-guided Maier 1-20
python scripts/theoalchemy_extract.py
```

**Catalog rebuild:**
```bash
python scripts/build_catalog.py          # gallery_catalog.json
python scripts/build_emblem_catalog.py   # emblem_catalog.json
```

---

## 5. Current State (2026-06-03)

### Image Sources

| Source | Images | Status |
|--------|--------|--------|
| Atalanta Fugiens (Maier 1618) | 51 plates | ✅ Segmented |
| Cramer Emblemata Sacra (1624) | 75 pages | ✅ Segmented |
| Rosarium Philosophorum | 19 pages | ✅ Segmented |
| Splendor Solis (Trismosin 22 plates) | 22 | ✅ Segmented |
| McLean Second Collection | 56 | ✅ Segmented |
| Maier Arcana Arcanissima | 22 | ✅ Segmented |
| Paul Marshall Anthology | 264 | ✅ Segmented (2026-06-03) |
| Obrist Medieval Imagery | 319 | ✅ Segmented (2026-06-03) |
| Khunrath Amphitheatrum (IA) | 92 | ✅ Segmented (2026-06-03) |
| Stolcius Viridarium Chymicum | 108 | ✅ Segmented (2026-06-03) |
| Mylius Philosophia Reformata | 134 plates (filtered) | 🔄 Segmenting (background) |
| Fludd Mosaicall Philosophy (IA) | TBD | ⏳ Sourcing |
| Manly Palmer Hall MSS (IA) | TBD | ⏳ Sourcing |
| Maier Viatorium + Mellon AF (IA) | TBD | ⏳ Sourcing |

**Gallery totals as of 2026-06-03**: 1,028 extracted elements · 10 projects · 71 tags

**Stolcius & Mylius FOUND**:
- Stolcius *Viridarium Chymicum* (1624) — 108 plates at `innergarden.org/artwork/viridarium/`
  - Script: `python scripts/fetch_stolcius_mylius.py --source stolcius`
- Mylius *Philosophia Reformata* (1622) — Princeton Digital Library IIIF, 776 pages → 134 plate candidates
  - Figgy manifest: `https://figgy.princeton.edu/concern/scanned_resources/8fff50d6-8f43-47fd-934d-c57b71d1dfdf/manifest`
  - Script: `python scripts/fetch_stolcius_mylius.py --source mylius --plates-only`
  - Images at 1800px wide (originals 6575×8535 px)

**Still not found digitally**:
- Fludd *Utriusque Cosmi Historia* (1617)
- Aurora Consurgens (medieval MS)

### Gallery & Catalog

Three web pages at `http://localhost:8765/prototype/`:
- `gallery.html` — element gallery (196 extracted elements, 69 tags, 5 projects)
  - **New**: URL param filtering (`?tag=dragon`, `?search=lion`, `?emblem=af_37`)
  - **New**: Nav bar links to Emblem Catalog and Review Queue
- `emblems.html` — scholarly emblem catalog (136 emblems)
  - **New**: Visual elements and key concepts link to gallery (`gallery.html?search=term`)
  - **New**: "View N elements in Gallery →" button in emblem detail
- `review.html` — **NEW** human review queue
  - Approve/Reject/Flag each extracted element
  - Side-by-side source crop + transparent cutout
  - Filter by status, project, search
  - Saves to localStorage, exportable as JSON

### Segmentation Batches

The batch script `scripts/run_all_batches.ps1` runs all queued sources sequentially:
```powershell
.\scripts\run_all_batches.ps1  # Runs: mclean, maier_arcana, khunrath, paul_marshall, obrist, equipment
```
Check progress: `cat logs/batch_run.log`

After batches complete:
```bash
python scripts/build_catalog.py && python scripts/build_emblem_catalog.py
python scripts/batch_extract.py --source stolcius --output assets/extracted/
python scripts/batch_extract.py --source mylius_philosophia --output assets/extracted/
```

### Tests

50 tests passing across 7 test files. Run:
```bash
python -m pytest tests/ -v --ignore=tests/test_pipeline_integration.py  # fast (no model)
python -m pytest tests/ -v  # includes model inference (~3 min)
```

New test files:
- `tests/test_comprehensive_detector.py` — 13 tests: IoU logic, NMS deduplication, category prompt structure
- `tests/test_overlap_analyzer.py` — 15 tests: overlap matrix, group finding, composite mask building

---

## 6. Immediate Next Steps

### High priority

1. **Run comprehensive extraction on all Claudiens emblems** (the flagship corpus):
   ```bash
   python -m scripts.batch_extract_all claudiens
   python -m scripts.build_object_catalog
   python scripts/build_catalog.py && python scripts/build_emblem_catalog.py
   ```

2. **Review Claudiens object catalog**: Open `prototype/review.html`, work through the `auto`-status extractions, approve or flag each one, refine the `appearance` and `iconographic_meaning` fields in flagged entries.

3. **Run comprehensive extraction on remaining queued sources**:
   ```bash
   python -m scripts.batch_extract_all rosarium splendor_solis cramer --resume
   python -m scripts.batch_extract_all mclean_second paul_marshall khunrath --resume
   python -m scripts.build_object_catalog
   ```

### Medium priority

4. **AI-assisted appearance annotation**: After extraction, use a secondary Claude API pass to auto-populate the emblem-specific `appearance` and `iconographic_meaning` fields in each `object_catalog` entry. The canonical `data/motifs.json` descriptions provide the template; the AI pass should refine them with specific details from the emblem plate (size, position, relationship to other objects, variant form).

5. **Motif genealogy view**: Show how a motif travels across corpora — e.g. "green lion devouring the sun" in Maier emblem 16 → Rosarium plate → Khunrath. The `object_catalog` + `motif_id` fields enable this cross-corpus query.

6. **Gallery enrichment**: Connect `emblems.html` to `gallery.html` (concept → motif filter). The `object_catalog` makes this straightforward: each catalog entry has both a `motif_id` and a `transparent_png`.

7. **Stolcius/Mylius sourcing**: 108 + 50-100 plates not yet extracted. Try Warburg Institute digital library (warburg.sas.ac.uk/library) or BSB Munich (digitale-sammlungen.de).

### Architecture upgrade

8. **SQLite database**: Move from JSON catalog files to SQLite for proper relational queries. The new `object_catalog` + `motifs` + `visual_elements` schema maps cleanly to relational tables. Python `sqlite3` is built-in.

9. **Vector embeddings**: Index the `appearance` + `iconographic_meaning` + discourse fields using sentence-transformers to enable semantic search ("emblems with vessels and fire", "figures holding swords in nigredo stage").

---

## 7. Key Files to Know

| File | Purpose |
|------|---------|
| `scripts/pipeline/comprehensive_detector.py` | Multi-category GroundingDINO passes + NMS; `CATEGORY_PROMPTS` defines all six groups |
| `scripts/pipeline/overlap_analyzer.py` | Pairwise containment matrix, union-find groups, composite mask builder |
| `scripts/pipeline/postprocessor.py` | All boundary logic: `remove_background_bridges`, `_fill_holes_smart`, `select_figure_mask` |
| `scripts/pipeline/segmenter.py` | SAM inference + `_pick_best_mask` (prefers smallest mask covering center) |
| `scripts/pipeline/metadata.py` | `MOTIF_VOCABULARY` (motif id → detection terms) + `TERM_TO_MOTIF_ID` (reverse lookup) |
| `scripts/extract_all_objects.py` | Main comprehensive extraction CLI |
| `scripts/batch_extract_all.py` | Batch comprehensive extraction across collections |
| `scripts/build_object_catalog.py` | Reads extraction summaries → writes `object_catalog` into `data/emblems.json` |
| `data/motifs.json` | 65-entry controlled vocabulary: id, category, appearance, description, alchemical_valence |
| `data/emblems.json` | Emblem records; after `build_object_catalog.py`: includes `object_catalog[]` per emblem |
| `scripts/build_emblem_catalog.py` | Merges both databases into `prototype/emblem_catalog.json` |
| `prototype/emblems.html` | Scholarly emblem catalog with metadata, discourse, concept links |
| `prototype/gallery.html` | Element gallery (extracted cutouts) |
| `docs/VISUAL_ELEMENT_EXTRACTION_STRATEGY.md` | Full extraction strategy doc with pipeline diagram and schema |
| `C:\Dev\TheosophicalAlchemyDB\data\maier_atalanta_fugiens_emblems_metadata.json` | Best scholarly data for Maier emblems 1-20 |
| `C:\Dev\Claudiens\site\data.json` | All 51 Maier emblems: motto, discourse, stage |

---

## 8. Handover Prompt

Copy the following to start a new session continuing this work:

---

**PASTE THIS INTO A NEW CONVERSATION:**

```
I'm continuing work on the Emblem Print Shop project at C:\Dev\EmblemPrintShop.

This is a scholarly visual extraction pipeline for early modern alchemical emblem books. The infrastructure is complete:

EXTRACTION:
- Comprehensive multi-category extraction: scripts/extract_all_objects.py detects EVERY object in an emblem (6 categories: figures, animals, plants, landscape, architecture, objects/weapons/equipment), segments each with SAM, and produces composites for overlapping objects (man + sword he's holding → extracted separately AND together)
- Targeted extraction (legacy): scripts/extract_element.py for single-prompt extraction
- 12+ emblem corpora sourced (Maier, Cramer, Rosarium, Splendor Solis, Khunrath, McLean, Paul Marshall, Obrist medieval, Fludd, etc.)
- 50 tests passing across 7 test files

DATA ONTOLOGY:
- data/motifs.json — 65-entry controlled vocabulary with id, category, appearance, description, alchemical_valence, detection_terms
- data/emblems.json — emblem records; includes object_catalog[] after build_object_catalog.py runs
- data/visual_elements.json — individual extracted element records
- scripts/pipeline/metadata.py — MOTIF_VOCABULARY and TERM_TO_MOTIF_ID for mapping detections to motifs

CATALOG PIPELINE:
  python -m scripts.batch_extract_all claudiens   # comprehensive extraction
  python -m scripts.build_object_catalog          # write object_catalog into emblems.json
  python scripts/build_catalog.py                 # rebuild gallery
  python scripts/build_emblem_catalog.py          # rebuild scholarly catalog

Read docs/HANDOVER.md for full architecture, current state, and next steps.
Read docs/VISUAL_ELEMENT_EXTRACTION_STRATEGY.md for extraction pipeline diagram and schema details.

Immediate tasks:
1. Run comprehensive extraction on all Claudiens emblems (python -m scripts.batch_extract_all claudiens)
2. Build and review the object catalogs (python -m scripts.build_object_catalog)
3. Run on remaining collections: rosarium, splendor_solis, cramer
4. Consider AI-assisted annotation pass to refine appearance/iconographic_meaning fields per emblem
5. Find Mylius Philosophia Reformata and Stolcius Viridarium Chymicum via Warburg or BSB Munich

Local server: python prototype/serve.py → http://localhost:8765
```

---

## 9. Environment

- Python 3.14.3 (Windows)
- PyTorch 2.10.0+cpu
- transformers 5.2.0 (GroundingDINO + SAM)
- OpenCV 4.13.0
- PyMuPDF (fitz) 1.27.2 — PDF page extraction
- PIL/Pillow 12.1.1
- pytest 9.0.2

All models cached in HuggingFace hub after first run (~500MB total).

No GPU required. CPU timing: ~50-60s per image (detector + segmenter + postprocessor).
