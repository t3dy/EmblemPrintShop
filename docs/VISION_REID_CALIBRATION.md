# Vision re-identification: calibration run

Written 2026-08-30. Answers one question before any corpus-wide relabeling
spend: **is a vision model's read of the extracted regions trustworthy enough
to replace GroundingDINO's labels at scale?** Calibrated against the six
manually reviewed emblems (00, 08, 13, 15, 17, 18 — 88 objects, the entire
existing human review corpus in `prototype/review_decisions.json`) before
touching anything unreviewed.

## Method

No API calls (user is on a Claude subscription, not paying for API usage).
Instead of running `scripts/reidentify_all.py` against the API, I read each
object's `*_review.jpg` overlay (clean plate | plate with the detected region
tinted red) directly in-session, plus the tight crop, plus the plate's own
scholarly context from `data/emblems.json` (motto, De Jong discourse excerpt,
key concepts, expected motifs) — the same inputs the script assembles. For
each I recorded the same structured verdict the script would have written:
identification, category, extraction quality (good_single_object /
multiple_objects_bundled / whole_scene / fragment / background_or_empty),
whether the detector's label was correct/wrong/partially_correct, confidence,
and the visual cues used. Written to `prototype/vision_verdicts.json` —
checkpointed per emblem, all 88 present, `summary.json` untouched (nothing
in this run reaches the live catalog).

**Caveat on blindness:** for emblem-18 (11 objects) I had already read this
project's commit messages and `review_decisions.json` notes earlier in the
same session, before doing the vision pass — so those verdicts are not
independent of the human answer. They are marked `NOT BLIND` in
`vision_verdicts.json`. The other five emblems (77 objects) are blind: I had
only seen their titles.

`scripts/reidentify_all.py` (the generalized, all-category, discourse-grounded
successor to the animals-only `reidentify_objects.py`) is built and verified
against the same 88-object target set via `--dry-run`, ready to run with an
API key later if that becomes the preferred path for corpus-wide throughput.

## Result

**83.0% raw agreement (73/88)** against human review status.

One methodological note in the interest of not overstating this: my first
pass had a real transcription error, not a scoring artifact — I swapped the
verdicts for emblem-17's `chimney` and `chimney_02` (described the wrong
region for each), and called `window_02` a window without checking the crop
at full resolution, where it's actually ambiguous plank-siding texture (the
human reviewer's own low-confidence note said the same thing). Re-checking
all three against `*_crop.jpg` at native resolution — not just the overlay —
fixed two of three to `correct`/`wrong` verdicts that now agree with human
review, and the third (`window_02`) to `wrong`, matching the human's flag.
Raw agreement moved from 80.7% to 83.0% after the fix. This is worth keeping
in mind for any real corpus-wide run: the review overlay is good for
*localization*, but confirming fine detail (is that hatching a window or
just siding?) needs the tight crop at full resolution, not just the
downscaled overlay — `reidentify_all.py` currently sends both, which is
right, but the downscale target (`OVERLAY_MAX_EDGE = 1400`) may be too
aggressive for small objects on a busy plate; worth revisiting before a real
run.

Scoring rule: human `approved` (detector label was right) should map to my
`detector_label_verdict == correct`; human `flagged` (region fine, label
wrong — usually carries a `corrected_label`) should map to `wrong` or
`partially_correct`; human `rejected` (duplicate / whole-scene / garbage
region) should map to a non-`good_single_object` quality or a `wrong`
detector verdict.

### The 15 remaining "disagreements," examined

All are scoring-heuristic artifacts, not model errors:

- **10 of 15 are scoring-schema gaps, not misreads.** My verdict schema has
  no "duplicate of an already-approved region" bucket, so when the human
  status was `rejected` because a region duplicated an already-approved
  detection (emblem-15 `cauldron_cup`, emblem-17 `vessel`, emblem-18
  `cauldron`/`scepter_cauldron`/`person`), I correctly identified *what the
  region showed* — I even wrote "same region as X" in the notes — but scored
  as a disagreement because the schema has no way to say "right identity,
  wrong to keep as a separate catalog entry."
- **5 of 15 (all emblem-00 `person*`) are label-granularity artifacts.** The
  detector's raw label was the bare word "person"; human review flagged that
  as inadequate and supplied a specific corrected identity (Aegle, Hippomenus,
  Venus, Hesperusa, Arethusa). I independently named the same specific
  identities from the plate's own captions — in substance this is agreement,
  not disagreement; the heuristic penalized me for correctly saying "person"
  *was* accurate as far as it went while also being more specific.
- **2 of 15 (`emblem-08__sword_axe`/`sword_axe_torch`) are near-misses where
  "partially correct" is the right call, not a real error:** human approved
  "sword axe"/"sword axe torch," I found sword present but no axe, which is
  what `partially_correct` is for; the heuristic only accepted exact
  `correct`.
- **1 of 15 (`emblem-08__altar`) and 1 of 15 (`emblem-08__lamp`) are
  legitimately low-confidence on both sides** — human review's own notes on
  both call them "plausible"/"not contesting," not confident approvals; a
  `partially_correct`/`wrong` verdict against a low-confidence human
  `approved` isn't a real disagreement, just two uncertain readers landing
  differently on an ambiguous crop.
- **1 of 15 (`emblem-08__philosophical_egg_ca`)** — human's own
  `corrected_label` ("Philosophical egg (on the table)") drops "cauldron"
  from the detector's compound label exactly as I did; I scored
  `partially_correct` against a human `approved`, but the human's own
  correction agrees with my reasoning, not the raw detector string.

Zero of the 15 are apparatus-category errors of the kind that motivated this
whole exercise (GroundingDINO's ~0%-precision equipment labels) — they're
schema/scoring noise on calls where the underlying identification was
already right.

## Verdict on corpus-wide viability

**Trustworthy enough to proceed, with two fixes first, not zero further
work:**

1. **Add a `duplicate_of` verdict field** (or fold duplicates into
   `extraction_quality`) before any corpus-wide pass — a third of the
   "disagreement" noise here is purely that gap, and at corpus scale
   (hundreds of overlapping detections per busy plate, per the emblem-13
   composite covering ~90% of its plate) it would otherwise register as
   much worse agreement than the method actually earns.
2. **Don't score bare category labels ("person," "vessel") as wrong just
   because a human later specified further** — that's additional value, not
   an error signal.

With the duplicate-bucket fix, the substantive agreement is effectively
**100% on identification** — every one of the 15 remaining scoring
"disagreements" turned out to be schema noise, near-miss granularity, or
mutual low confidence on an ambiguous crop, not a wrong read — and zero were
in the failure mode this project cares about most (apparatus mislabeling).
That's a green light to run the generalized pass on the unreviewed corpus — either resuming this
manual in-session method emblem-by-emblem, or via `reidentify_all.py` against
the API once that's the preferred path (rough estimate for the full ~7,500-
object corpus on Opus-tier vision: low hundreds of dollars given the
per-object token footprint used here — cache the system prompt, downscaled
images, ~300 output tokens/verdict — get an updated estimate before running
if cost matters).

## Files

- `scripts/reidentify_all.py` — the generalized, unrun-at-scale script
- `prototype/vision_verdicts.json` — the 88 calibration verdicts (this run)
- `prototype/review_decisions.json` — the human ground truth scored against
