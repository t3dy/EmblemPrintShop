# Emblem Print Shop

### ▶ [Open the live site](https://t3dy.github.io/EmblemPrintShop/)

**→ [Visual Element Gallery](prototype/gallery.html)** &nbsp;|&nbsp; **→ [Complete Alchemical Images](prototype/alchemical-images/index.html)** &nbsp;|&nbsp; **→ [Emblem Catalog](prototype/emblems.html)** &nbsp;|&nbsp; **→ [Motif Atlas](prototype/motifs.html)** &nbsp;|&nbsp; **→ [WO-012 Results (new)](prototype/wo012-results.html)**

---

Working hub for an alchemical print-shop project: a catalog and design system for reusable visual elements from alchemical emblems, emblem books, woodcuts, marginalia, and related early modern image traditions.

The practical goal is to turn existing catalog work into a searchable image-parts library: dragons, lions, hermaphrodites, vessels, furnaces, suns, moons, trees, birds, kings, queens, and other recurring figures should become tagged, sourced, citable elements that can be browsed, compared, and eventually recomposed into print-shop style outputs.

## Prototype Pages

| Page | Description |
|------|-------------|
| [`prototype/gallery.html`](prototype/gallery.html) | **Visual Element Gallery** — browse 7,000+ extracted objects by tag, corpus, and motif. Paginated, filterable, with confidence scores and provenance links. |
| [`prototype/alchemical-images/index.html`](prototype/alchemical-images/index.html) | **Complete Alchemical Images** — scholarly reference for ~30 extant image sequences from ancient Egypt through 1788. Essay pages with full visual description, historical context, provenance, bibliography, and links for each work. |
| [`prototype/emblems.html`](prototype/emblems.html) | **Emblem Catalog** — 136 emblems (Maier, Cramer, Stolcius) with concept links and object catalogs. |
| [`prototype/motifs.html`](prototype/motifs.html) | **Motif Atlas** — 65-entry controlled vocabulary with iconographic descriptions and alchemical valences. |
| [`prototype/emblem.html`](prototype/emblem.html) | Single emblem viewer — object catalog, extracted crops, alchemical stage. |
| [`prototype/review.html`](prototype/review.html) | Extraction review queue — approve or reject detected objects. |
| [`prototype/wo012-results.html`](prototype/wo012-results.html) | **New** — WO-012 prototype results: does Canny edge detection improve SAM's masks on engraved line art? Two independent runs, six techniques, an honest agree/disagree writeup, and a headline finding that 4 of 4 sampled apparatus labels were wrong. |

## What Was Consolidated

- `sources/claudiens`: Atalanta Fugiens / Michael Maier emblem data, rendered site snapshots, visual tags, scripts, and 51 emblem images.
- `sources/theosophical-alchemy-db`: broader alchemical and Rosicrucian emblem data, concept-emblem mappings, figure genealogy specs, scripts, and prototype site files.
- `sources/hypnerotomachia-polyphili`: Hypnerotomachia woodcut catalog/display data, marginalia data, image-processing scripts, woodcut pages, and image assets.
- `docs`: critique and planning documents, sourcing inventories, and research notes.
- `data`, `assets`, `scripts`, `prototype`: canonical project folders for normalized data, extracted assets, tooling, and UI.

## Source Posture

The `sources` directory is a snapshot of useful work from nearby projects, not the final application architecture. Treat it as raw material. New canonical work happens in the top-level `data`, `assets`, `scripts`, and `prototype` folders.

> **Note:** `assets/extracted/` and `assets/extracted_all/` are not tracked in git (25GB+ of extracted PNG/JPG files). Run the extraction pipeline locally to regenerate them. See the pipeline docs below.

## Visual Element Extraction Pipeline

`scripts/` contains an open-source local extraction pipeline:

- **Stack**: GroundingDINO-tiny (text → bbox) + SAM ViT-base (bbox → mask) + OpenCV — all via HuggingFace `transformers`, CPU-only, no API keys.
- **Two extraction modes**: targeted (single prompt per emblem, legacy) and comprehensive (all-objects, all categories, with composite extraction for overlapping objects).

### Comprehensive extraction (new — recommended)

Detects every object in an emblem across six semantic categories (figures, animals, plants, landscape, architecture, objects/weapons/equipment). Overlapping objects (e.g. a man holding a sword) are extracted both individually and as a composite.

**Run on a single emblem:**
```
python -m scripts.extract_all_objects sources/claudiens/site/images/emblems/emblem-37.jpg
```

**Run on a whole collection:**
```
python -m scripts.batch_extract_all claudiens
python -m scripts.batch_extract_all claudiens rosarium --resume
```

**Tune sensitivity:**
```
python -m scripts.extract_all_objects emblem.jpg --threshold 0.20 --overlap-threshold 0.10
python -m scripts.extract_all_objects emblem.jpg --categories figures animals
```

**Update emblem records with extracted object catalog:**
```
python -m scripts.build_object_catalog
python -m scripts.build_object_catalog --stem emblem-37 --dry-run
```

Output goes to `assets/extracted_all/{emblem_stem}/individual/` and `.../composites/`, with a `summary.json` per emblem. After running `build_object_catalog`, each emblem record in `data/emblems.json` gains a structured `object_catalog` field listing every found object with its motif mapping, appearance notes, and iconographic meaning.

### Targeted extraction (legacy)

**Run a single extraction:**
```
python scripts/extract_element.py sources/claudiens/site/images/emblems/emblem-37.jpg --prompt "lion"
```

**Run all Claudiens emblems:**
```
python scripts/batch_extract.py --source claudiens --output assets/extracted/
```

### Gallery and catalog

**Build the gallery catalog:**
```
python scripts/build_catalog.py
```

**Open the gallery viewer:**
```
python prototype/serve.py
# Then open: http://localhost:8765/prototype/gallery.html
```

**Run tests (28 behavioral tests):**
```
python -m pytest tests/ -v --ignore=tests/test_pipeline_integration.py  # fast (no model)
python -m pytest tests/ -v  # full including model inference (~3 min)
```

## WO-012: edge-assisted segmentation prototype (2026-08-28)

New module `scripts/pipeline/edge_refiner.py` (unwired into the default pipeline —
opt-in only) tests whether Canny edge detection can refine SAM's masks on dense
engraved hatching, where the base pipeline's hand-tuned OpenCV morphology
(`postprocessor.py`) already fights soft boundaries and background bleed. Two
independent prototype runs tested this the same day, on two different Atalanta
Fugiens plates, without coordinating in advance:

- **[Results page](prototype/wo012-results.html)** — both runs side by side, with an
  honest "where they agree / where they disagree" synthesis, not just a combined
  highlight reel.
- **[Full report (Run A)](docs/EXTRACTION_PROTOTYPE_REPORT.md)** — methodology,
  per-technique verdicts, quantitative deltas (IoU, pixel counts).
- **[Review sheet (Run B)](prototype/wo012_canny_prototype/review.html)** — the
  furnace-region run, including an exploratory SAM2 comparison.

**Headline finding, independent of the edge-detection question itself:** of six
apparatus-category labels checked across both runs ("athanor," "furnace," "hourglass,"
"philosophical egg," "hearth"), only one bounded genuine apparatus, and even that one
had the wrong name attached. Apparatus-category labels from this pipeline should not
be trusted as evidence without a visual check first — a finding now folded into
[3dprintlab's `docs/EXTRACTION.md`](https://github.com/t3dy/3dprinteralchemylab/blob/main/docs/EXTRACTION.md),
which has its own writeup of this work at
**[t3dy.github.io/3dprinteralchemylab/extraction.html](https://t3dy.github.io/3dprinteralchemylab/extraction.html)**,
framed around 3dprintlab's Judge panel and its five-state evidence model (Source /
Machine proposal / Human confirmed / Reconstructed / Generated).

Nothing from this prototype is marked human-confirmed anywhere. `requirements.txt`
(new — this repo didn't have one before) captures the actually-installed environment
for reproducibility.

## Corpus Status

| Corpus | Plates | Objects | Status |
|--------|--------|---------|--------|
| Atalanta Fugiens (Claudiens) | 51 | ~1,200 | ✅ complete (6 + equipment categories) |
| Cramer Emblemata Sacra | 75 | ~900 | ✅ complete |
| Rosarium Philosophorum | 19 | ~250 | ✅ complete |
| Splendor Solis | 46 | ~600 | ✅ complete (24 IA + 22 local) |
| McLean Second Collection | 56 | ~700 | ✅ complete |
| Maier Arcana Arcanissima | 22 | ~300 | ✅ complete |
| Paul Marshall Anthology | 23 | ~280 | ✅ complete |
| Khunrath Amphitheatrum | 92 | ~1,100 | ✅ complete |
| Stolcius Viridarium Chymicum | 108 | ~1,400 | ✅ complete |
| Mylius Philosophia Reformata | 134 | ~1,700 | ✅ complete (filtered plate candidates) |
| Obrist Medieval Imagery | 319 | — | 🔄 extraction in progress |

**Total catalog:** 7,066 elements, 120 atomic tags, 15 projects (as of 2026-06-06).

## Data Ontology

The project's object model lives in `data/`:

- **`works.json`** — source books/manuscripts (Atalanta Fugiens, Rosarium, Hypnerotomachia, etc.)
- **`emblems.json`** — whole-plate emblem records with citation, mottos, alchemical stage, concept links, and `object_catalog` (populated by `build_object_catalog.py`)
- **`motifs.json`** — 65-entry controlled vocabulary of visual motifs covering all six extraction categories. Each entry has: `id`, `label`, `category`, `variants`, `detection_terms`, `appearance` (how it looks in early modern prints), `description` (iconographic meaning), `alchemical_valence`, `planetary`.
- **`visual_elements.json`** — individual extracted element records; populated by `build_object_catalog.py` from extraction results.

The `object_catalog` field in each emblem record:
```json
{
  "object_catalog": [
    {
      "type": "individual",
      "label": "lion",
      "motif_id": "lion",
      "category": "animals",
      "detection_score": 0.73,
      "appearance": "Rampant lion facing left, hatched mane...",
      "iconographic_meaning": "Green lion = vitriol dissolving gold...",
      "alchemical_valence": ["sulphur", "fixation", "sol"],
      "transparent_png": "assets/extracted_all/emblem-37/individual/lion_transparent.png"
    },
    {
      "type": "composite",
      "label": "lion + sun",
      "constituent_motif_ids": ["lion", "sun"],
      "transparent_png": "assets/extracted_all/emblem-37/composites/lion+sun_composite_transparent.png"
    }
  ]
}
```

## Alchemical Images Reference Site

`prototype/alchemical-images/` is a standalone scholarly reference site covering ~30 extant alchemical image sequences from ancient Egypt through the late eighteenth century. It is linked from and links back to the main gallery.

**Structure:**
- `index.html` — browse by period (Ancient / Medieval / Early Modern), filter by status and priority
- `work.html?id=<id>` — full essay page: image sequence cards, tabbed essay (visual description, historical context, provenance, alchemical processes, scholarly discussion), bibliography, external links
- `data.js` — ancient and medieval works (Codex Marcianus, Leiden/Stockholm Papyri, Aurora Consurgens, Ripley Scroll, etc.)
- `data-em.js` — early modern works (Splendor Solis, Khunrath, Fludd, Maier, Mutus Liber, Geheime Figuren, etc.)

**Works covered:** Codex Marcianus gr. Z. 299 · Leiden/Stockholm Papyri · Aurora Consurgens · Ripley Scroll · Buch der Heiligen Dreifaltigkeit · Donum Dei · Turba Philosophorum · Flamel Figures · Rosarium Philosophorum 1550 · Splendor Solis (Berlin & BL) · Hypnerotomachia Poliphili · Libavius Alchymia · Khunrath Amphitheatrum · Basil Valentine Azoth · Fludd Utriusque Cosmi · Maier Atalanta Fugiens · Maier Symbola Aureae Mensae · Mylius Opus Medico-Chymicum · Lambspring De Lapide · Stolcius Viridarium · Cramer Emblemata Sacra · Mylius Philosophia Reformata · Maier Arcana Arcanissima · Mutus Liber · Maier Septimana · Geheime Figuren der Rosenkreuzer

**Image sourcing status:**

| Work | Image source | Status |
|------|-------------|--------|
| Aurora Consurgens | e-codices IIIF (ZBZ Ms. Rh. 172) | ✅ 3 folios live |
| Ripley Scroll | Huntington ContentDM IIIF (HM 30313) | ✅ 4 sections live |
| Buch der Dreifaltigkeit | BSB MDZ IIIF (Cgm 598) | ✅ 4 folios live |
| Flamel Figures | BnF Gallica IIIF (fr. 14765) | ✅ 3 pages live |
| Splendor Solis (BL Harley) | Wikimedia Commons (5 folios available) | ⚠️ partial — BL IIIF offline (cyberattack) |
| Libavius Alchymia | Wellcome/Wikimedia CC BY 4.0 | ✅ 3 plates live |
| Basil Valentine Azoth | SLUB Deutsche Fotothek CC BY-SA 3.0 | ✅ Azoth diagram + 2 plates live |
| Fludd Utriusque Cosmi | Internet Archive (utriusquecosmima01flud) | ✅ 3 pages live |
| Mutus Liber | BnF Gallica IIIF (bpt6k15122214) | ✅ all 15 plates live |
| Geheime Figuren | Internet Archive (GeheimeFigurenDerRosenkreutz) | ✅ 3 plates live |
| Codex Marcianus | Biblissima IIIF viewer — no direct img URL confirmed | 🔴 needs sourcing |
| Leiden/Stockholm Papyri | RMO/KB — no IIIF confirmed | 🔴 needs sourcing (no illustrations) |
| Donum Dei | Leiden University IIIF (VCF 15, fol. 319v–335r, 4 confirmed roundels) | ✅ 4 roundels live |
| Maier Symbola Aureae Mensae | Internet Archive (symbolaavreaemen00maie) | ✅ 3 pages live |
| Maier Viatorium | Internet Archive (majeriviatoriumh00maie) | ✅ 2 pages live |
| Maier Septimana Philosophica | Internet Archive (septimanaphiloso00maie) | ✅ 2 pages live |
| Turba Philosophorum | No illustrated copy with IIIF confirmed | 🔴 needs sourcing |
| Splendor Solis Berlin | SMB — not fully digitized | 🔴 needs sourcing |

**Sourcing inventory:** [`docs/IMAGES_TO_SOURCE.md`](docs/IMAGES_TO_SOURCE.md) — full provenance records, repository shelfmarks, digitization URLs, and download notes for each work.

## Related Projects

- **[AtalantaClaudiens](https://github.com/t3dy/AtalantaClaudiens)** — DH site on Maier's Atalanta Fugiens; Phase 3A and 5A complete
- **[TheosophicalAlchemyDB](https://github.com/t3dy/TheosophicalAlchemyDB)** — broader Rosicrucian emblem database
- **[AlchemyTimelineMap](https://github.com/t3dy/AlchemyTimelineMap)** — chronological mapping of alchemical works
