# Visual evidence decomposition — findings from an independent investigation

Investigated 2026-08-28 in response to a request to design a segmentation +
edge-detection capability for decomposing emblem plates into reusable evidence
assets, in service of 3dprintlab's parametric apparatus and EMBLEMSIN3D's walkable
worlds. **This is not the canonical design document** — partway through this
investigation it turned out `C:\Dev\3dprintlab\docs\EXTRACTION.md` already answers
the same question, in more depth, dated 2026-07-29 (roughly a month prior), with
`DATA_SCHEMAS.md`/`INTEGRATIONS.md` already updated, a `docs/briefs/extraction.md`
role brief already written, and two dispatchable work orders
(`docs/workorders/WO-012-emblem-extraction-prototype.md`,
`WO-013-wire-extraction-into-judge-panel.md`) already sitting ready. That is the
document to read and act on. This file records what this independent pass found that
the existing one didn't, and one correction to something it asserted — both now also
folded into `EXTRACTION.md` directly as dated addenda, so this file is a trace, not a
second source of truth.

## What this pass found that EXTRACTION.md didn't have

**EMBLEMSIN3D already places extracted cutouts in 3D — it isn't speculative.**
EXTRACTION.md's section A treats "a cutout as a textured plane in EMBLEMSIN3D" as
"plausible later... explicitly deferred, not designed here." That's not accurate as of
today: a third sibling project, `C:\Dev\EmblemPapercraft`, already regenerates
cutouts + a depth-ordered `layers.json` manifest from this repo's
`assets/extracted_all/` output (`scripts/build_layers.py`), and
`C:\Dev\EMBLEMSIN3D\papercards.js` is the **current, live** per-emblem renderer:
every figure is an alpha-tested, gently-curled, depth-positioned plane whose
`customDepthMaterial` casts the *cut silhouette* as a shadow, not a bounding box.

This matters architecturally, not just as trivia. `EMBLEMSIN3D\docs\HISTORY.md`
documents that this replaced two earlier attempts at exactly the thing EXTRACTION.md
leaves open ("a cutout as a textured plane") — both built with primitive `THREE.*`
geometry standing in for figures, both explicitly rejected by Ted for not looking like
the real engravings. Direct quote preserved there: *"I don't want you to just make
wavy 3d pop-outs I want you to reconstruct the spaces... so that we can make
papercraft emblems that are more like pop-up books where each figure... has its own
paper cut out."* `EMBLEMSIN3D\props.js`'s primitive builders are deprecated for
individual emblem scenes and kept only for four generic overflow rooms.

Practical consequence for any WORLDS-facing extraction work later: don't design new
Three.js loading code for cutouts — it exists, works, and has a settled design
history behind it. The open gap on that side is narrower and more mundane:
`build_layers.py` infers card depth purely from vertical position + a per-category
bias (`CAT_BIAS`), with no edge/geometry signal at all — so if edge-aware extraction
ever wants to improve *that* pipeline, it's a depth-inference quality question, not a
missing-capability question.

I've added this as a dated correction directly in `3dprintlab/docs/EXTRACTION.md`
(section A, the WORLDS bullet) rather than leaving it only here.

## One correction to EXTRACTION.md's own claim

Its inventory table (section B) lists human review as "Yes — `prototype/review.html`
+ `POST /api/save-review`," reading as though the two are connected. They're not
connected today: `prototype/serve.py` genuinely implements a working
`POST /api/save-review` endpoint, but `prototype/review.html`'s approve/reject/flag
buttons only write to `localStorage` (`setReview`/`saveReviews` in the page's own JS)
— there's no `fetch('/api/save-review', ...)` call anywhere in the file. It's a live
but unwired capability: the durable-persistence piece EXTRACTION.md's prototype plan
(and the original request's step 9, "store the accepted regions with provenance")
needs already has a server-side home, it just needs the four or so lines in
`review.html` to actually call it. Also folded into `EXTRACTION.md` section B
directly.

## Status

No pipeline code was changed by this pass — same as EXTRACTION.md's own stated
posture. `EXTRACTION.md`'s WO-012 (dispatchable now, brief: `docs/briefs/extraction.md`)
and WO-013 (blocked on WO-012's actual output) are the concrete next steps; nothing
here supersedes them.
