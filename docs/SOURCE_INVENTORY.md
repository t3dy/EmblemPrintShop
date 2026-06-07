# Source Inventory

Consolidated on 2026-05-27 into `C:\Dev\EmblemPrintShop`.

## Claudiens

Source: `C:\Dev\Claudiens`

Copied:

- `data/emblem_manifest.json`: 51 Atalanta Fugiens emblem records.
- `data/emblem_identity_seed.json`: identity seed data for emblem cataloging.
- `data/visual_scene_summaries.json`: scene-level visual descriptions.
- `site/visual-data.json`: 324 image records, 134 tags, 15 works.
- `site/dictionary-depicts.json`, `site/search-index.json`, `site/data.json`: site search and entity data.
- `site/images/emblems`: 51 emblem images.
- selected scripts: `build_site.py`, visual-element and seed scripts.

Strength: best local source for concrete emblem images with image files.

## TheosophicalAlchemyDB

Source: `C:\Dev\TheosophicalAlchemyDB`

Copied:

- `data/prototype_data.json`: 178 emblems, 100 figures, 87 texts, 67 concepts, 6 scholars, 1 essay.
- `data/maier_atalanta_fugiens_emblems_1_20_extraction.md`.
- `data/maier_atalanta_fugiens_emblems_metadata.json`.
- concept, figure-genealogy, and emblem extraction specification files.
- selected scripts for emblem ingestion, concept mapping, figure genealogy, and summary generation.
- selected prototype site files.

Strength: broad conceptual and relational framework.

## Hypnerotomachia Polyphili

Source: `C:\Dev\hypnerotomachia polyphili`

Copied:

- `site/data.json`: 223 catalog/marginalia entries.
- `site/woodcuts`: 112 generated woodcut pages.
- `site/images`: BL, Siena, and 1499 woodcut image assets.
- selected scripts for fetching, seeding, reading, and cataloging woodcuts.

Strength: image-catalog and marginalia logic, especially the bridge from non-alchemical visual material into alchemical reading practices.

## Current Size

The consolidated folder currently contains 1,058 files totaling about 658 MB.

## What Was Not Copied

Large PDF libraries, full Git histories, `.claude` worktrees, environment folders, and unrelated generated caches were not copied. The new folder is meant to be a working project hub rather than a duplicate of every source repository.
