# Emblem Print Shop — Research Guide

A guide for scholars using this platform for alchemical emblem research.

## Getting Started

### For Emblem Scholars

Start at **[Emblem Catalog](../prototype/emblems.html)** — Browse the 51 Atalanta Fugiens emblems with full apparatus:
- Maier's original discourse and commentary
- Alchemical stage classification (nigredo/albedo/citrinitas/rubedo)
- Planetary and color symbolism
- Related emblems and visual elements
- Scholarly references and citations

Each emblem has a "Scholarship & Sources" section linking to:
- H.M.E. de Jong's scholarly commentary (1969)
- Original source authorities (Rosarium, Aurora Consurgens, Ripley, etc.)
- Further reading bibliography

### For Visual Analysis

Go to **[Visual Gallery](../prototype/gallery.html)** — Browse and filter 7,097 extracted motifs:
- Filter by motif (lion, eagle, serpent, vessel, star, etc.)
- Filter by category (figures, animals, objects, landscapes, architecture)
- Filter by source corpus (Atalanta Fugiens, Cramer, Splendor Solis, etc.)
- Inspect individual crops with metadata: confidence score, bounding box, detector label
- Edit extractions and save corrections

### For Conceptual Research

Use **[Concept Browser](../prototype/concepts.html)** — Explore by alchemical theme:
- Search for concepts: "mercury," "distillation," "calcination," "union," "stone"
- See which emblems mention each concept (with sample thumbnails)
- Discover related concepts and their co-occurrence patterns
- Read source text chapters that mention the concept
- Click through to full emblem details or open texts in new tabs

## Research Workflows

### Workflow 1: Tracing a Motif Across Corpora

**Question:** How is the lion depicted across different emblem books? What meanings does it carry?

**Steps:**
1. Go to [Concept Browser](../prototype/concepts.html)
2. Search for "lion"
3. Click the "lion" concept card
4. View sample emblems (all lion crops across all sources)
5. Click each emblem to see:
   - Full emblem page with context
   - Related source texts mentioning lions
   - Alchemical meaning in this context
6. Compare: How does Maier's lion differ from Cramer's? From Khunrath's?

**Export for Further Analysis:**
- Go to [Export](../prototype/export.html)
- Filter by concept "lion"
- Download as CSV with all lion records
- Analyze in spreadsheet: count by source, by stage, by category

### Workflow 2: Reading an Emblem with Its Source Text

**Question:** What does Maier say about the Fleeing Atalanta (AF I)? Where does this discourse sit in the alchemical tradition?

**Steps:**
1. Go to [Emblem Catalog](../prototype/emblems.html)
2. Click "Atalanta Fugiens I — The Fleeing Atalanta"
3. Read:
   - **Maier's Discourse:** The symbolic interpretation
   - **Alchemical Classification:** Stage, planetary association, color
   - **Related Emblems:** See which other Atalanta emblems engage similar themes
   - **Extracted Elements:** Visual analysis of what's depicted (angel, serpent, etc.)
   - **Related Source Texts:** Scroll to see chapters from other sources that mention related concepts
4. Click "Read full chapter" to open the source text in a new tab
5. Search the text for keywords (mercury, volatility, flight)

**Scholarly Notes:**
- The discourse section often synthesizes multiple scholarly analyses
- Check de Jong's page references to read the academic literature
- Compare Maier's treatment with how other emblemists handle similar motifs

### Workflow 3: Discovering Concept Networks

**Question:** Which alchemical concepts cluster together? What's the relationship between calcination, dissolution, and putrefaction?

**Steps:**
1. Go to [Export](../prototype/export.html)
2. Download concept_index.json
3. Open in text editor or JSON viewer
4. Look for the "related" field in each concept entry
   - Shows which concepts co-occur with it in emblems
5. Build a network map by hand or in Gephi:
   - Nodes = concepts
   - Edges = co-occurrence (weight by count)
6. Alternatively:
   - Concept Browser shows related concepts inline
   - Click through related concepts to explore the graph interactively

### Workflow 4: Comparing Corpora

**Question:** Which sources emphasize distillation? Which focus on mineral substances?

**Steps:**
1. Go to [Export](../prototype/export.html)
2. Download gallery_catalog.json
3. In your analysis tool (Python, R, Excel):
   - Group records by `project_key`
   - For each project, count:
     - How many records tagged "distillation," "mercury," "gold," etc.
     - Distribution of categories
     - Average confidence score
4. Visualize: Bar charts of concept frequency by corpus

**Example Python:**
```python
import json
from collections import defaultdict

catalog = json.load(open('gallery_catalog.json'))
concepts_by_project = defaultdict(lambda: defaultdict(int))

for record in catalog['records']:
  project = record.get('project_key')
  for tag in record.get('tags', []):
    concepts_by_project[project][tag] += 1

# Print top 10 concepts per project
for project, tags in concepts_by_project.items():
  top = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]
  print(f"{project}: {top}")
```

### Workflow 5: Analyzing Junk Filtering Quality

**Question:** Did the junk filter work? Are there false positives or false negatives?

**Steps:**
1. Go to [Gallery](../prototype/gallery.html)
2. Try to find "scene" crops (large compositions that should have been filtered)
   - Filter by source, scroll through
   - These should be rare (only ~5 per corpus if filter worked)
3. Check for false negatives: Legitimate single objects misclassified
   - Look for small crops with high confidence scores
4. Go to [Review Queue](../prototype/review.html)
   - Use the Edit tool to flag crops needing reconsideration
   - Save your edits
5. Summarize findings in your research notes

## Understanding the Data

### Extraction Process

```
PDF Source → GroundingDINO + SAM → Transparent PNGs
             ↓
         Bounding boxes + labels
             ↓
         Heuristic junk filter (text_page, scene)
             ↓
         Claude Vision re-identification (animals only)
             ↓
         Verified labels in summary.json
             ↓
         build_catalog.py aggregates → gallery_catalog.json
```

### Metadata Fields Explained

In gallery_catalog.json, each element record contains:

| Field | Meaning |
|-------|---------|
| `emblem_id` | Unique ID for the source emblem (e.g., "emblem-00") |
| `object_label` | What the object is (e.g., "angel herphrodite skeleton") |
| `category` | Category: figures, animals, objects, plants, landscapes, architecture |
| `tags` | Normalized atomic labels (e.g., ["angel", "skeleton"]) |
| `project` | Source corpus (e.g., "Atalanta Fugiens (Maier)") |
| `project_key` | Short key (e.g., "claudiens") |
| `score` | Detector confidence (0–1; unreliable) |
| `verified_label` | Human-corrected label if available |
| `label_source` | Where label came from (detector, manual, heuristic) |
| `transparent_png_web` | Path to transparent PNG crop |
| `crop_jpg_web` | Path to JPG preview |
| `source_image_web` | Path to original full-page scan |
| `source_image` | Absolute path to source |
| `bbox` | Bounding box [x, y, width, height] in source image |

### Understanding Confidence

**Detector Confidence** (`score` field):
- Range: 0.0 (uncertain) to 1.0 (confident)
- **NOT trustworthy for label quality** (GroundingDINO labels are often wrong)
- **IS trustworthy for bounding box quality** (boxes are usually good even when labels are wrong)
- Use this to filter: keep score >= 0.25, discard < 0.25

**Re-identification Confidence** (`verified_confidence` field when present):
- Values: "high", "medium", "low"
- Reflects human/vision judgment of label reliability
- Based on: discriminating features matched, number of cues, visual clarity
- Use this when available (prioritized over detector confidence)

## Citing This Work

If you use data from Emblem Print Shop in your research:

**For extracted visual elements:**
> Emblem Print Shop Visual Element Database. Accessed [DATE]. https://[URL]. [Specific source corpus], extracted using GroundingDINO + SAM (vision foundation models) and vision-verified with Claude Opus.

**For text excerpts:**
> [Author]. [Title]. [Publication details]. Extracted and transcribed [DATE] via Emblem Print Shop OCR pipeline (PyMuPDF).

**For concept/metadata analysis:**
> Emblem Print Shop Concept Index (140 concepts, 7,097 emblems, 9 source corpora) [DATE]. https://[URL].

## Limitations & Caveats

### Known Issues

1. **Junk filtering:** ~1–2% false negatives (some scenes slip through); ~0.5% false positives
2. **GroundingDINO labels:** Heavily garbled before re-ID (e.g., "wolf lambtoise frog" → corrected to "hare")
3. **Animal re-ID:** Only 121 animal crops corrected; other categories not yet re-identified
4. **Text extraction:** OCR quality varies; some books are image-only (no text layer)
5. **Text-visual links:** Only 56 of 7,097 records have chapter links (motif keyword matching is imperfect)

### What to Trust

✅ **Trust these:**
- Bounding boxes (GroundingDINO localization is excellent)
- Source image paths and metadata
- Emblem catalog (51 Atalanta Fugiens, scholarly verified)
- Concept index (based on clean tags, not detector labels)

⚠️ **Verify these before use:**
- Object labels (detector guesses; many corrected but not all)
- Confidence scores (unreliable; use verified_label if present)
- Text-visual links (keyword-based; may miss or falsely match)

### Data Not Included

- Full-resolution source PDFs (license restrictions)
- Detector confidence for rejected crops
- Image-only sources (Maier Mellon Atalanta Fugiens, etc.) — needs OCR
- Crowdsourced corrections/annotations (not yet open to contributions)

## Extending This Research

### Possible Next Steps

1. **OCR image-only sources** — Digitize Maier Mellon, others without text layers
2. **Crowdsourced annotation** — Open platform for experts to correct labels, add interpretations
3. **Concept genealogy** — Trace how concepts evolve across centuries and corpora
4. **Network analysis** — Build concept co-occurrence graphs, identify clusters
5. **Federated search** — Link with other emblem/alchemy collections (DH projects, libraries)
6. **Linked data exports** — RDF/Turtle format for integration with semantic web

## Contact & Feedback

Questions? Issues with data? Suggestions?

- Check [CURRENT_HANDOVER.md](CURRENT_HANDOVER.md) for technical architecture
- See individual script docstrings for tool documentation
- Review commit messages for context on recent changes

---

**Happy researching!** May your emblems illuminate the work.
