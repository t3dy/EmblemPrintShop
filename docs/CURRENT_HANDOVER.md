# Emblem Print Shop — Current State & Handover (2026-06-14)

## Overview

A comprehensive scholarly extraction and browsing platform for early modern alchemical emblem books. Extracts 7,097+ visual motifs from 13+ sources using GroundingDINO + SAM, with vision-based re-identification and rich textual integration.

## Current Status

### ✅ Completed Work (This Session)

1. **Vision-Based Re-Identification** (121 animal crops)
   - Script: `scripts/reidentify_objects.py` + Claude Vision
   - Rubric: `docs/ANIMAL_RECOGNITION_SYSTEM.md` (diagnostic key)
   - Results: 121 crops manually verified; labels corrected (e.g., "wolf lambtoise frog" → "hare")
   - Status: Integrated into catalog rebuild via `build_catalog.py` verified_label preference

2. **Junk Filtering** (268 objects dropped)
   - Script: `scripts/flag_junk_crops.py` with heuristics
   - Results: 15 text_page + 253 full-scene verdicts written to summary.json
   - Status: Integrated; catalog builder drops these automatically

3. **Text Extraction** (200+ chapters from 9 books)
   - Script: `tools/pdf_to_markdown.py`
   - Books: Rosarium (5), Splendor Solis (8), Cramer (58), Fludd (61), Viatorium (5), Arcana, Khunrath, Hall
   - Maier Atalanta Fugiens (Mellon): image-only; needs OCR (not done)
   - Format: Chapter-split Markdown with OCR text as-is, page markers

4. **Text-Visual Linkage** (56 emblems → chapters)
   - Script: `scripts/build_text_visual_links.py`
   - Output: `text_chapters.json` (140 chapters + excerpts), `emblem_text_links.json` (56 emblems → chapters)
   - Integration: `prototype/emblem.html` now displays related source text inline

5. **Scholarly Concept Index** (140 concepts)
   - Script: `scripts/build_concept_index.py`
   - Output: `concept_index.json` mapping concepts to emblems/chapters
   - Top concepts: figure (1009), person (623), vessel (444), star (372), book (304)

6. **Research Browser** — `prototype/concepts.html`
   - Interactive concept explorer
   - Search, filter, click-through to emblems & source texts
   - Related concept suggestions (co-occurrence)
   - Sample emblem thumbnails per concept

7. **Automated Catalog Rebuild** — `scripts/watch_and_rebuild.py`
   - Monitors extraction job; triggers rebuild when idle 120s
   - Resumable; logs activity
   - Ready to run when extraction completes

8. **Catalog Rebuild** (current data)
   - 7,097 elements (6,095 comprehensive + 1,002 legacy)
   - 124 tags, 16 projects
   - Junk-filtered (268 dropped); verified labels preferred
   - Built with: `scripts/build_catalog.py` + `build_emblem_catalog.py`
   - Last built: 2026-06-14 03:45

### ⏳ In Progress

**Image Extraction Job** (slow; est. 20-40 hrs remaining)
- Hall Alchemical Manuscripts: 23/254 (9% done)
- Fludd Utriusque Cosmi Historia: 0/311 (not started)
- Hypnerotomachia Polyphili: 1/162 (not started)
- Total est.: 23/727 complete (~3% of final batch)

### 🚫 Blocked by Extraction

**Final Catalog Rebuild** — Once Hall/Fludd/HP extraction finishes:
```bash
python -m scripts.build_object_catalog  # Optional
python scripts/build_catalog.py
python scripts/build_emblem_catalog.py
```
Then: `prototype/gallery_catalog.json` will have 8,500-9,000+ elements.

## Architecture

### Pipeline Stages

1. **Image Extraction** (GroundingDINO + SAM) → PNG crops + metadata
2. **Junk Filtering** (heuristics) → flag text_page, full_scene
3. **Vision Re-ID** (Claude Opus) → fix animal labels
4. **Text Extraction** (PyMuPDF OCR) → chapter-split Markdown
5. **Catalog Rebuild** (aggregate + filter) → JSON galleries
6. **Research Tools** (search, browse, link) → scholarly interface

### Key Files

```
Scripts:
  batch_extract.py                — Image extraction (GroundingDINO)
  reidentify_objects.py            — Vision re-ID w/ rubric
  flag_junk_crops.py              — Heuristic junk filtering
  build_text_visual_links.py       — Motif-chapter linking
  build_concept_index.py           — Concept cross-reference
  build_catalog.py                 — Gallery JSON aggregation
  build_emblem_catalog.py          — Emblem record catalog
  watch_and_rebuild.py             — Auto-rebuild monitor
  tools/pdf_to_markdown.py         — PDF text extraction

Prototype Pages:
  emblems.html                     — Catalog (51 AF emblems)
  emblem.html (?id=af_16)          — Detail page w/ text links
  gallery.html (?emblem=)          — Visual element gallery
  concepts.html                    — Concept research browser (NEW)
  motifs.html                      — Motif cross-browser
  editor.html                      — Extraction editor
  review.html                      — Review queue

Catalogs (JSON):
  gallery_catalog.json             — 7,097 elements (current)
  emblem_catalog.json              — 51-136 Atalanta Fugiens emblems
  text_chapters.json               — 140 chapters w/ metadata
  emblem_text_links.json           — 56 emblems → chapters
  concept_index.json               — 140 concepts → emblems/chapters

Extracted Materials:
  Markdown/                        — 9 books, 200+ chapters
  assets/extracted_all/            — 1,180 dirs w/ PNG crops
  sources/                         — 18 corpus metadata
```

### Serving

**Dev Server:** `python prototype/serve.py` (port 8765)
- Serves from project root; paths resolve correctly
- POST /api/save-edit, /api/save-review

**Static hosting ready:** Entire `prototype/` can be deployed to web server.

## Testing Checklist

- [ ] Run `python prototype/serve.py`
- [ ] Open `http://localhost:8765/prototype/emblems.html` — emblem catalog loads
- [ ] Open emblem detail page (`?id=af_00`) — shows text links
- [ ] Open gallery.html — 7,097 elements displayed
- [ ] Open concepts.html — 140 concepts, click one → detail panel
- [ ] Search in concepts — filter works
- [ ] Click emblem thumbnail in concept detail → gallery opens
- [ ] Click chapter link in detail → Markdown opens

## Next Actions

### Short-term (next session)

1. **Watch extraction job** — Run `watch_and_rebuild.py` to auto-rebuild when Hall/Fludd/HP complete
2. **Deploy dev** — Test full stack (all pages, all links, all data)
3. **Export capability** — Add ability to download emblem/chapter data as CSV/JSON
4. **Mobile optimization** — Responsive CSS for emblem detail pages

### Medium-term

1. **OCR for image-only sources** (Maier Atalanta Fugiens Mellon)
2. **Genealogy/timeline visualization** (show alchemical process flows)
3. **Search across text + visual** (unified full-text search)
4. **Concept genealogy** (show how concepts evolve across sources)
5. **Contributor tools** (annotation, correction, linking)

### Long-term (Phase 6: Scholarly Integration)

1. **Linked Open Data** (RDF exports for DH projects)
2. **Federated search** (other emblem/alchemy collections)
3. **Collaborative curation** (crowdsourced metadata)
4. **Advanced visualization** (network graphs, process diagrams)

## Troubleshooting

**Extraction slow?**
- GroundingDINO + SAM are compute-intensive (~3-5 sec/image)
- Normal: Hall/Fludd/HP will take 20-40 hours total
- Can resume if job stops: `batch_extract.py` skips completed sources

**Text links missing?**
- `build_text_visual_links.py` matches by motif keywords
- Only 56 of 7,097 have matches (motif keywords are rough)
- Could improve with NLP/embedding-based matching

**Catalog out of date?**
- Run `python scripts/build_catalog.py` manually
- Or start `watch_and_rebuild.py` to auto-rebuild

**Vision re-ID incomplete?**
- All 121 animal crops done
- `reidentify_objects.py --force` to re-verify
- For other categories: edit prompt to `--category all` (expensive)

## Memory & Knowledge

See `memory/` directory for:
- `project_overview.md` — What is this project
- `pipeline_phases.md` — Five-stage extraction pipeline
- `project_batch_state.md` — Current extraction status
- `canonical-game-repo.md` — EmblemRoguelike is canonical
- `bad-detector-labels.md` — Why vision re-ID matters

## Contact

Questions? Check:
1. `HANDOVER.md` (comprehensive original documentation)
2. Each script's docstring (Python triple-quoted at top)
3. `docs/ANIMAL_RECOGNITION_SYSTEM.md` (re-ID rubric)
4. Latest commit message for context on recent changes
