# Quality and review system

Written 2026-08-29 after a corpus-wide audit found real, systematic problems with
both the extraction pipeline's geometry and its labels. This doc is the "system
file" for avoiding them going forward — read it before trusting an extracted
element, and before extending the pipeline or the review tools.

## The three things that can be wrong with an extraction, and how each is caught

These are independent failure modes. Fixing one does nothing for the others —
treat them as three separate checks, not one "is this good?" verdict.

| Failure | Example found | How it's caught |
|---|---|---|
| **Geometry**: the cutout drags in a second, disconnected blob of noise (or is split into unrelated fragments) | — | `scripts/pipeline/qc_checks.py` — deterministic, no AI, runs over the whole corpus in seconds |
| **Label**: the region is cleanly cut but named wrong | emblem-00: a clean, single-blob crop of two fighting lions labeled "angel herphrodite skeleton" (GroundingDINO's composite "figures" category prompt hallucinating) | Human review in `prototype/review.html`, or a future automated AI-vision pass (see "Not yet automated" below) |
| **Wrong region entirely** (whole-scene / duplicate detections) | emblem-00: a "window" detection whose bbox covers 98% of the entire plate; two independent detections both landing on the same tholos region under different wrong labels | Human review — `rejected` status, not a relabel |

**Never conflate these.** A geometrically clean mask can carry a garbage label
(the lions case) and vice versa — a fragmented mask can have the right label.
The review UI shows both signals side by side for exactly this reason.

## 1. Geometry QC — `scripts/pipeline/qc_checks.py` + `scripts/run_geometry_qc.py`

Connected-component analysis on each cutout's alpha channel (no mask file is
stored separately — the transparent PNG's own alpha *is* the mask of record).
A secondary component covering more than ~3% of the total mask area after
dust-filtering (<1% components) is flagged `fragmented`.

**Run corpus-wide, 2026-08-29: 1,717 of 7,519 elements (23%) are geometrically
fragmented.** This is the corpus-wide version of "sometimes there's a bunch of
noise attached, sometimes not even connected" — now a real, checkable number
instead of an impression from casually browsing the gallery.

```bash
python -m scripts.run_geometry_qc              # whole catalog, writes prototype/geometry_qc.json
python -m scripts.run_geometry_qc --emblem-id emblem-00
python -m scripts.run_geometry_qc --project claudiens
```

Re-run after any re-extraction or postprocessing change — it's cheap (pure
OpenCV, no model inference) and safe to re-run over the whole corpus. Results
surface in `review.html` as an orange "⚠ fragmented" badge and a "Fragmented
only" filter, so a reviewer can triage the worst geometry problems first
regardless of what the label says.

**This does not fix anything by itself.** It's a gate that flags, not a
refinement that repairs — WO-012's edge-detection experiments
(`scripts/pipeline/edge_refiner.py`) are the place mask-refinement techniques
live, and none of them are wired into the default pipeline yet (see
`docs/EXTRACTION_PROTOTYPE_REPORT.md`). Use the manual lasso/wand tools
(section 3 below) to fix a flagged element by hand in the meantime.

## 2. The label-correction feedback loop

Reviewer corrections in `review.html` are not just notes that sit inert —
`scripts/build_catalog.py` reads them back on every rebuild and applies them.

- Enter a corrected label in a card's "Corrected label" field → written to
  `prototype/review_decisions.json` (via `serve.py`'s `/api/save-review`,
  same file the approve/reject/flag buttons use) as `corrected_label`, keyed
  by `emblem_id + '__' + object_stem`.
- `python scripts/build_catalog.py` picks it up: `object_label`, `tags`, and
  `display_label` in `gallery_catalog.json` all use the correction; `prompt`
  (the stable identity key) and `original_label` (audit trail) are never
  overwritten — see the docstring on `load_human_corrections()` for why.
- `label_source` on every record is `"detector"`, `"vision-verified"`, or
  `"human-corrected"` — always checkable, never silently blended.

**Key-collision fix (2026-08-29):** review state used to be keyed by
`emblem_id + '__' + prompt` (the raw label). Multiple distinct objects in one
emblem routinely share an identical generic label — emblem-00 alone has five
different figures (Aegle, Arethusa, Hesperusa, Venus, Hippomenus) all
detected as bare `"person"`. Keying by label meant approving one silently
applied to all five. Fixed by keying on `object_stem` (the unique per-object
filename stem) instead, in `review.html`, `build_catalog.py`, and
`run_geometry_qc.py` together — if you add a fourth place that needs a
review-state key, use `object_stem`, not `prompt`.

**Demonstrated on emblem-00** (the Atalanta Fugiens title page, chosen because
it's what first surfaced the labeling problem): all 18 extracted objects
manually reviewed against the plate's own printed captions (Aegle, Arethusa,
Hesperusa, Hercules, Venus, Hippomenus, Atalanta are all labeled directly in
the engraving — the primary source is its own best grounding text where it
exists). 11 corrected, 4 approved, 3 rejected (2 duplicate detections of
regions already correctly labeled elsewhere, 1 whole-scene garbage box). See
`prototype/review_decisions.json` and rebuild the catalog to see the result.

**Not yet automated / explicitly out of scope for this pass:**
- `scripts/reidentify_objects.py` already does exactly this kind of
  vision-grounded relabeling for the `animals` category via the Claude API
  (see `docs/ANIMAL_RECOGNITION_SYSTEM.md`) — generalizing it to all six
  categories, and to use each emblem's own `discourse_excerpt` /
  `key_concepts` as grounding context, is real, valuable, unbuilt work.
  Requires `ANTHROPIC_API_KEY` set in the environment (not set as of this
  writing) to run at corpus scale.
- `build_object_catalog.py` (populates `data/emblems.json`'s
  `object_catalog`, used by `emblems.html`) does **not** yet read
  `review_decisions.json` the way `build_catalog.py` does. It also reads
  `assets/extracted_all/*/summary.json` directly rather than the union of
  `*_meta.json` files on disk — and at least one emblem (emblem-13) has a
  `summary.json` that a later, smaller re-extraction run overwrote wholesale,
  leaving it describing far fewer objects than actually exist and are shown
  in `gallery_catalog.json`. `build_catalog.py` already works around this by
  globbing `*_meta.json` directly; `build_object_catalog.py` should adopt the
  same pattern before it's trusted as a corrections target.
- Only emblem-00 has been manually reviewed. 7,501 elements have not been —
  the corpus-wide "identify every visual element correctly" goal is
  nowhere near done; this section is the infrastructure for doing it
  incrementally, not a claim that it's finished.

## 3. Manual cutout tools — `prototype/editor.html`

Beyond the existing eraser/restore-brush/crop tools, `editor.html` now has:

- **Magic wand** — click a pixel, flood-fills the connected region within a
  tolerance of that pixel's color (classic Photoshop wand). Tolerance slider.
- **Lasso** — freehand polygon select.
- **Magnetic lasso** ("Snap to edges" toggle on the lasso) — each dragged
  point snaps to the strongest nearby image gradient (a client-side Sobel
  magnitude map computed once per image load), the same "trace the line the
  engraver actually drew" idea as WO-012's Canny experiments, just computed
  in-browser for zero latency while dragging instead of as a server-side
  batch step.
- **Keep selection / Erase selection** — apply a lasso or wand selection as
  "erase everything outside" or "erase everything inside." This is the direct
  fix for a `fragmented` QC flag: open the flagged element, lasso around just
  the real figure, "Keep selection" removes everything else in one action.
- **New extraction from source** — `editor.html?source=<path>&emblem_id=<id>`
  (linked from every card in `review.html` as "✂ New from source") loads the
  *original, full source plate*, not an existing cutout. Lasso or wand a
  region the pipeline missed or mangled entirely, enter a label, "Save as new
  element" — `serve.py`'s new `/api/save-new-extraction` endpoint composites
  the selection against its **own** read of the source plate (never trusting
  browser-side RGB, only the alpha mask, so a saved cutout is always genuine
  plate ink) and writes a `*_meta.json` / `*_transparent.png` / `*_crop.jpg`
  triple into `assets/extracted_all/<emblem>/individual/` in the exact shape
  `extract_all_objects.py` writes — `build_catalog.py` picks it up with no
  special-casing, because it already discovers objects by globbing
  `*_meta.json` files rather than trusting any manifest. A "Rebuild catalog"
  round-trip (`/api/rebuild-catalog`) runs automatically after a successful
  save so the new element shows up in the gallery immediately.

Verified end-to-end 2026-08-29: wand-selected a region on emblem-00's source
plate, saved as a new element, confirmed the written PNG contained real
source-plate pixels (not a re-encoded browser copy) and that the rebuilt
catalog listed it with a working `object_stem`; then deleted the test files.

**Both editing paths require `prototype/serve.py` running** — like the
review-decision sync (see `EXTRACTION_PROTOTYPE_REPORT.md`'s note on that),
none of this works against the static GitHub Pages copy of the site, only
against a local server.
