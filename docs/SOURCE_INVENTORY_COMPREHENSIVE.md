# Emblem Print Shop — Comprehensive Source Inventory

Generated as part of the alchemical emblem sourcing project.
Updated: 2026-06-03

## Already Extracted & Segmented

| Corpus | Images | Source | Notes |
|--------|--------|--------|-------|
| Atalanta Fugiens (Maier 1618) | 51 plates | Claudiens project | All 51 emblems extracted |
| Emblemata Sacra (Cramer 1624) | 75 pages | Internet Archive `emblematasacraho00cram` | 50 emblems + text pages |
| Rosarium Philosophorum | 19 pages | Internet Archive `rosarium-philosophorum-the-rosary-of-the-philosophers` | King-queen conjunction series |

## Sourced & Awaiting Segmentation (Local PDFs)

| Corpus | Images | Source PDF | Location |
|--------|--------|-----------|----------|
| Christian Rosenkreutz Anthology (Paul Marshall) | 264 pages | `e:\pdf\Rosicrucian\a christian rosenkreutz anthology_paul marshall al.pdf` | `sources/paul_marshall/images/` |
| Splendor Solis (Trismosin) | 22 plates | `e:\pdf\alchemy\illustrations\Salomon Trismossin SPLENDOR SOLIS libgen li.pdf` | `sources/splendor_solis/images/` |
| McLean Second Emblem Collection | 56 pages | `e:\pdf\alchemy\Adam McLean The Second Collection of Alchemical and Hermetic Emblems.pdf` | `sources/mclean_second/images/` |
| Obrist — Les débuts de l'imagerie alchimique | 305 pages | `e:\pdf\alchemy\Barbara Obrist Les débuts de l imagerie alchimique Le Sycomore.pdf` | `sources/obrist_medieval/images/` |
| Obrist — Visualization in Medieval Alchemy | 14 pages | `e:\pdf\alchemy\Obrist Barbara Visualization in medieval alchemy.pdf` | `sources/obrist_medieval/images/` |

## Sourced & Awaiting Segmentation (Internet Archive)

| Corpus | IA Identifier | Images (est.) | Notes |
|--------|--------------|--------------|-------|
| Khunrath — Amphitheatrum Sapientiae Aeternae (1609) | `amphitheatrum-sapientiae-aeternae-solius-verae-christiano-kabalisticum-divino-ma` | 92 extracted | Famous 5 large engraved plates + text figures |
| Maier — Arcana Arcanissima (1614) | `arcanaarcanissim00maie` | ~7 extracted | Hieroglyphic emblems |
| Splendor Solis (IA 1920 ed., 22 color plates) | `SplendorSolisAlchemicalTreatisesOfSolomonTrismosin...Including22` | 22 expected | Color versions of the 22 plates |
| Fludd — Mosaicall Philosophy (1659) | `bim_early-english-books-1641-1700_mosaicall-philosophy-_fludd-robert_1659` | TBD | Macrocosm/microcosm diagrams |
| Manly Palmer Hall — Alchemical Manuscripts | `manlypalmerhabox18v6hall` | TBD | Manuscript facsimiles |
| Maier — Viatorium (1618) | `majeriviatoriumh00maie` | TBD | Mountains of the planets |
| Maier — Atalanta Fugiens Mellon edition | `mellon48atalanta` | TBD | Alternative high-quality scan |

## Newly Found — Ready to Download

| Work | Author | Date | Source | Script |
|------|--------|------|--------|--------|
| Viridarium Chymicum | Daniel Stolcius | 1624 | innergarden.org/artwork/viridarium/ (108 plates) | `fetch_stolcius_mylius.py --source stolcius` |
| Philosophia Reformata | Johann Daniel Mylius | 1622 | Princeton Digital Library IIIF (792 pages, ~50-100 plates) | `fetch_stolcius_mylius.py --source mylius --plates-only` |

**Stolcius note**: All 108 emblem plates downloaded to `sources/stolcius/images/`. These are the copper engravings Stolcius collected from earlier works including Mylius.

**Mylius note**: Princeton's copy is 6575×8535px (original resolution). Script downloads at 1800px wide. Manifest cached at `sources/mylius_philosophia/manifest.json`. 792 canvases total; plates-only filter keeps ~100.

## Not Yet Sourced — Digital Copies Not Located
| Amphitheatrum Sapientiae Aeternae | Heinrich Khunrath | 1595/1609 | Original first edition. IA has a copy (see above). |
| Utriusque Cosmi Historia | Robert Fludd | 1617-1621 | Major cosmological work. Not found on IA. Wellcome has physical copy only. |
| Opus Medico-Chymicum | Johann Daniel Mylius | 1618 | Not digitized publicly. |
| Symbola Aureae Mensae | Michael Maier | 1617 | Not found as standalone on IA. |
| Aurora Consurgens | Anonymous (medieval) | ~1420 | Manuscript tradition. No open digitization found. |
| Buch der Heiligen Dreifaltigkeit | Anonymous | ~1410-1420 | German alchemical MS. No open digitization found. |
| Ripley Scroll | George Ripley | ~1490 | MS tradition. Partial reproductions in McLean collection. |
| Mutus Liber | Jacob Saulat | 1677 | Not found as standalone on IA. McLean commentary reproduces plates. |
| Lambspring — De Lapide Philosophico | Anonymous | 1599/1607 | McLean Threefold Journey reproduces emblems. |

## Suggested Next Sources

1. **Warburg Institute Digital Library** — Has medieval alchemical MSS including Aurora Consurgens
2. **Getty Museum Open Content** — Splendor Solis British Library MS (color, high resolution)
3. **Wellcome Collection Library** — Khunrath plates, Fludd diagrams (physical access needed)
4. **BSB Munich** — May have Mylius under different catalog ID
5. **HAB Wolfenbüttel** — Specialist in 17th-century German alchemical texts

## Extraction Commands

To run the segmentation pipeline on each new corpus after images are extracted:

```bash
# Splendor Solis (22 plates — alchemical king/queen/sun/moon figures)
python scripts/batch_extract.py --source splendor_solis --output assets/extracted/

# McLean Second Collection (56 emblems — diverse hermetic figures)
python scripts/batch_extract.py --source mclean_second --output assets/extracted/

# Paul Marshall anthology (264 pages — Rosicrucian emblems)
python scripts/batch_extract.py --source paul_marshall --output assets/extracted/

# Obrist medieval imagery (319 pages — medieval MS images, figures, vessels)
python scripts/batch_extract.py --source obrist_medieval --output assets/extracted/

# Khunrath Amphitheatrum (92 pages — oratory/laboratory, divine figures)
python scripts/batch_extract.py --source khunrath --output assets/extracted/

# Maier Arcana Arcanissima (hieroglyphic emblems)
python scripts/batch_extract.py --source maier_arcana --output assets/extracted/

# Equipment extraction pass (all emblems with furnace/vessel motifs)
python scripts/batch_extract.py --mode equipment --source claudiens --output assets/extracted/
```

## Rebuild Gallery

After each batch completes:
```bash
python scripts/build_catalog.py
# Then refresh: http://localhost:8765/prototype/gallery.html
```
