# WO-012 prototype report — Canny-assisted segmentation on one plate

Run 2026-08-28. Work order: `3dprintlab/docs/workorders/WO-012-emblem-extraction-prototype.md`.
Brief: `3dprintlab/docs/briefs/extraction.md`. Nothing in this session set
`review_status`, `identificationStatus`, or `humanVerified` on anything — every
result below is a machine proposal awaiting Ted's review, per the work order's
explicit instruction.

**Code:** `scripts/pipeline/edge_refiner.py` (new, five standalone functions, not
wired into the default pipeline), `scripts/wo012_prototype.py` (driver for the three
refinement tests), `scripts/wo012_amg.py` (driver for the AMG pass). `detector.py`,
`segmenter.py`, `postprocessor.py`, `overlap_analyzer.py`, `extractor.py`: unmodified.
`requirements.txt` added at repo root (didn't exist before).

## Headline finding: the apparatus-category labels I picked to test on were wrong

Before reporting on Canny, the more important result. I picked three
apparatus-category detections from the existing `object_catalog` to test refinements
against — `athanor` and `hourglass` from emblem-13 (Atalanta Fugiens XIII), plus a
quick check of `furnace` from emblem-8 for comparison. I looked at what each one
actually shows:

- **emblem-13's "athanor" (score 0.42)** is a seated nude figure on a riverbank rock,
  in front of a walled town and a stone bridge — the plate has no furnace, tower, or
  heat source of any kind in it. It's a river-god/landscape figure.
- **emblem-13's "hourglass" (score 0.26)** is a bearded human head in profile — part
  of the same figure above, not a timekeeping instrument.
- **emblem-8's "furnace" (score 0.39)**, checked as a sanity comparison, is a
  cross-hatched barrel-vaulted corridor in perspective — architecture, but not a
  furnace.

Three for three wrong, on the specific apparatus-category labels I sampled. This is
an informal spot check (n=3, not a systematic audit — I did not check the corpus's
other apparatus-labeled entries), but it's a clean, direct confirmation of
`3dprintlab/docs/EXTRACTION.md`'s own risk warning: GroundingDINO's raw labels for
apparatus categories are unreliable on this corpus, plausibly more so than for the
animal categories `scripts/reidentify_objects.py` was already built to correct.
**Consequence for WO-013: none of the three detections tested here should be treated
as a candidate for the Judge ghost-overlay demo.** No apparatus-category label from
this corpus should be trusted without looking at the actual crop first.

This didn't block the actual mask-refinement experiment below — a seated figure and a
human head are still real engraved subjects with real hatching and real boundary
problems, so testing Canny-based refinement on them is still methodologically valid,
even though the semantic labels attached to them are wrong.

## Setup

Plate: `sources/claudiens/site/images/emblems/emblem-13.jpg` (1600×1418 px). Three
existing detections from its `object_catalog`, all from this one plate:

| Object (as labeled) | What it actually is | det_bbox [x,y,w,h] | Refinement tested |
|---|---|---|---|
| "athanor" | seated nude figure | [345, 558, 731, 788] | boundary snapping |
| "tree" | foliage over a townscape (label plausible) | [33, 35, 474, 828] | contour-informed bridge severing |
| "hourglass" | bearded human head | [544, 628, 99, 92] | erosion guard |

For each, the baseline is the *exact, unmodified* call sequence
`extract_all_objects.py` uses (`segment_from_bbox` → `remove_paper_background` →
`remove_background_bridges` → `select_figure_mask`). Each refinement was applied at
the specific pipeline stage it targets, isolated so the comparison is fair (see
`scripts/wo012_prototype.py` docstrings for exactly how each was isolated).

Edge maps generated once for the whole plate: plain Canny (508,297 edge px) and a
per-tile adaptive-threshold variant (472,351 edge px, `edge_refiner.
adaptive_canny_edges`, 200px tiles, median-derived thresholds). All refinement
comparisons below use the adaptive map. Both maps: `assets/wo012_prototype/
emblem-13_canny_plain.png` / `_canny_adaptive.png`.

## Per-technique verdict

### 1. Boundary snapping — helped, modestly, on this case

`assets/wo012_prototype/athanor_comparison.png`. Baseline mask: 324,375 px.
Boundary-snapped: 335,474 px (+3.4%). IoU vs. baseline: 0.954.

Looking at the diff overlay, the change traces almost exactly along the figure's
drawn silhouette — arms, legs, the seated contour on the rock — rather than
fragmenting the mask or bleeding into background. This is the technique doing what it
was designed to do: trimming SAM's slightly soft/dilated boundary back toward the
actual ink line, and recovering a couple of small extremities the baseline mask
undershot. It did not visibly damage anything. **Verdict: worth testing on more
cases** — one image isn't enough to adopt as a default, but nothing here argues
against it either.

**Plain vs. adaptive Canny, isolated:** ran boundary snapping against both edge-map
variants separately for a direct comparison (`athanor_boundary_snapped_PLAINCANNY_
transparent.png` / `_ADAPTIVECANNY_transparent.png`). Plain-Canny-snapped: 335,966 px;
adaptive-Canny-snapped: 335,474 px; IoU between the two results: 0.9978 — essentially
no difference on this plate. The adaptive per-tile thresholding didn't earn its
complexity here; this particular scan may not have the uneven-illumination problem it
was designed for. Worth re-checking on a plate with visibly uneven paper tone before
concluding adaptive Canny is unnecessary in general.

### 2. Contour-informed bridge severing — no measurable difference on this case

`assets/wo012_prototype/tree_comparison.png`. Baseline (fixed-radius severing):
293,782 px. Contour-informed severing: 293,993 px (+0.07%). IoU: 0.9993 — essentially
identical.

The candidate-bridge region the contour-informed version starts from (the same
thin-connector pixels the baseline's morphological opening would also find) turned
out to contain almost no strong Canny edges to sever at, so it left almost everything
intact — same as the baseline. **This is a clean negative result, not a bug**: on
this particular mask, there wasn't a genuine touching-figure bridge case to test the
technique's actual value proposition against (severing where a real boundary crosses,
vs. leaving intact where it doesn't). The "mountain behind the lion" style case
`postprocessor.py`'s docstring describes wasn't well represented by this detection.
**Verdict: inconclusive — needs a real touching-figure test case**, e.g. a
figure-over-landscape or coiled-serpent detection, not this one.

### 3. Erosion guard — measurable difference, but not the intended kind

`assets/wo012_prototype/hourglass_comparison.png`. Plain erosion (baseline,
`edge_erosion_px=4`): 12,172 px. Edge-guarded: 13,700 px (+12.5%). IoU: 0.8885 — the
largest change of the three.

But looking at the diff overlay: the recovered pixels form a near-uniform ring around
the *entire* head, not a selective recovery of thin extremities (a beard tip, a
strand of hair) while leaving genuine fringe noise eroded. The reason is visible in
the adaptive Canny panel: a densely cross-hatched engraved head produces strong edges
almost everywhere across its surface, not just at true silhouette boundaries — so
"near a strong edge" stops being a selective signal on this kind of subject and just
broadly undoes the erosion. **Verdict: didn't achieve its intended purpose on this
case.** The technique's assumption (edges are sparse, so "near an edge" picks out
genuine thin features) holds on cleaner-contour subjects but breaks down on
heavily-hatched engraved surfaces, which is most of what this corpus is made of. A
real fix would need to distinguish silhouette edges from interior hatching edges
(e.g. by edge orientation/coherence, or by only protecting edges that lie on the
mask's own boundary rather than anywhere nearby) — out of scope for this prototype.

### 4. SAM automatic-mask-generation (AMG) — complementary, different granularity, not better/worse

`assets/wo012_prototype/athanor_amg_overlay.png`, `wo012_amg_report.json`. Run on a
crop around the seated-figure detection (scoped down from the full plate for CPU
time, disclosed in `wo012_amg.py`'s docstring), coarse 16×16 point grid: 32 raw
proposals in 63.8s, 14 kept after dropping specks and near-whole-crop blobs.

AMG did not propose the whole seated figure as one region the way the prompt-driven
detector did. Instead it proposed several tight, class-agnostic sub-parts: notably a
well-fit ellipse around just the *head* (a genuinely clean boundary GroundingDINO's
category prompts never specifically asked for), a small quadrilateral in the
background gap between the figure's legs, and several individual background
towers/buildings as separate proposals rather than merged into one townscape blob.
**Verdict: not a replacement for the prompt-driven baseline, but a real complement** —
it's the literal "segmentation/object-proposals-first" ordering the original request
asked about, and on this one image it surfaced a finer decomposition (head as its own
part) that the label-first pipeline wouldn't produce on its own. Whether that's useful
depends on whether sub-figure parts are wanted as their own catalog entries — an open
product question, not a technical one, and out of scope to decide here.

## Not attempted

SAM-HQ / SAM2 comparison (WO-012 step 4) — explicitly optional in the work order.
Skipped to keep this prototype time-bounded, consistent with "prototype on a small
number of images... don't build an elaborate framework first." Both remain live
options per `EXTRACTION.md` section C if a future work order wants them; `transformers`
in this environment already imports `Sam2Model` cleanly with no new install.

## Recommendation

- Do not carry the "athanor," "hourglass," or emblem-8 "furnace" labels forward into
  WO-013 — none actually depict apparatus. Finding a genuine apparatus candidate for
  the Judge ghost-overlay demo needs its own quick visual check, not an inherited
  label.
- Boundary snapping is the one refinement with a plausible positive signal here;
  worth a second test on a cleaner-contour subject before deciding whether to gate it
  behind a flag in the real pipeline.
- Bridge severing and erosion guard need re-testing on cases that actually exercise
  their target failure mode (a real touching-figure bridge; a cleaner-contour thin
  extremity) before either can be judged fairly — this prototype's test objects
  happened not to be good exercises for them.
- AMG is worth keeping in mind as a complementary, not competing, proposal source if
  sub-figure decomposition (e.g. cataloging a head separately from a body) is ever
  wanted.

No file outside `C:\Dev\EmblemPrintShop` changed as part of this work order.
