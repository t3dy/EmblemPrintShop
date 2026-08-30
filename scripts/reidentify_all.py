"""
Generalized vision re-identification: all categories, discourse-grounded.

Successor to scripts/reidentify_objects.py (animals-only). For every extracted
object it sends a Claude vision model:
  1. the *_review.jpg overlay (clean plate | plate with the detection's mask
     highlighted red) -- gives the model both scene context and localization,
  2. the tight crop, for detail,
  3. the emblem's own scholarly context from data/emblems.json (motto,
     discourse excerpt, key concepts, motif candidates) -- the emblem-00
     lesson: the primary source and its scholarship are the best grounding.

The detector's label is passed only as a claim to be checked; GroundingDINO's
apparatus labels ran ~0% precision across the six manually reviewed emblems.

Calibration mode (--reviewed-only) restricts targets to objects that already
have a human verdict in prototype/review_decisions.json and writes verdicts to
prototype/vision_verdicts.json WITHOUT touching any summary.json -- so the
model can be scored against human review before being trusted corpus-wide.

Usage:
    python -m scripts.reidentify_all --reviewed-only            # calibration run
    python -m scripts.reidentify_all --stems emblem-00 --limit 3 --dry-run
    python -m scripts.reidentify_all --stems cramer_page_0045   # full run, one emblem
    python -m scripts.reidentify_all --force                    # redo existing verdicts

Resumable: verdicts are checkpointed to the output file after every call;
already-verdicted objects are skipped unless --force.

API key: reads ANTHROPIC_API_KEY from the environment, falling back to a
KEY=VALUE line in the project root .env file (never committed).
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
EXTRACTED = ROOT / "assets" / "extracted_all"
EMBLEMS_JSON = ROOT / "data" / "emblems.json"
REVIEW_DECISIONS = ROOT / "prototype" / "review_decisions.json"
VERDICTS_OUT = ROOT / "prototype" / "vision_verdicts.json"

MODEL = "claude-opus-5"
OVERLAY_MAX_EDGE = 1400
CROP_MAX_EDGE = 700

CATEGORIES = [
    "human_figure", "animal", "hybrid_or_mythical_creature", "apparatus",
    "vessel_or_container", "tool_or_object", "plant", "architecture",
    "landscape_feature", "celestial", "scene", "mixed", "other",
]

QUALITY = [
    "good_single_object",     # one coherent object/figure, cleanly bounded
    "multiple_objects_bundled",  # region spans several distinct elements
    "whole_scene",            # the region is (most of) the entire plate
    "fragment",               # only part of an object
    "background_or_empty",    # no meaningful subject in the region
]


def load_env_key() -> str | None:
    import os
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    envfile = ROOT / ".env"
    if envfile.exists():
        for line in envfile.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def load_emblem_context() -> dict[str, dict]:
    """Map extraction dir stem (e.g. 'emblem-18') -> emblem record."""
    if not EMBLEMS_JSON.exists():
        return {}
    records = json.loads(EMBLEMS_JSON.read_text(encoding="utf-8"))
    out = {}
    for r in records:
        ip = r.get("image_path") or ""
        stem = Path(ip).stem
        if stem:
            out[stem] = r
    return out


def context_block(emblem: dict | None) -> str:
    if not emblem:
        return "(No scholarly context is available for this plate.)"
    parts = [f"Plate: {emblem.get('label', '?')} of {emblem.get('work_id', '?')}"]
    if emblem.get("english_motto"):
        parts.append(f"Motto: {emblem['english_motto']}")
    if emblem.get("discourse_excerpt"):
        parts.append(f"Discourse (De Jong): {emblem['discourse_excerpt']}")
    if emblem.get("key_concepts"):
        parts.append("Key concepts: " + "; ".join(emblem["key_concepts"]))
    if emblem.get("motif_candidates"):
        parts.append("Motifs scholars expect on this plate: "
                     + "; ".join(emblem["motif_candidates"]))
    if emblem.get("alchemical_stage"):
        parts.append(f"Alchemical stage: {emblem['alchemical_stage']}")
    return "\n".join(parts)


SYSTEM = f"""You are an iconographer cataloging early modern (16th-17th c.) \
alchemical and emblematic prints: engravings and woodcuts with heavy hatching, \
stylised anatomy, and period apparatus. An object detector has cut regions out \
of whole plates, and its labels are known to be UNRELIABLE -- in a manual audit \
its apparatus labels were almost always wrong (a "furnace" that is a standing \
man, an "anvil" that is a dog, three different vessel labels on one basin). \
Treat the detector's label as a claim to verify against the pixels, never as \
a hint to follow. Do not overcorrect either: sometimes the detector is right.

You will see, per object:
1. A side-by-side review image: the clean plate on the left, and on the right \
the SAME plate with the detected region tinted red. Identify what the RED \
region depicts -- use the surrounding scene to disambiguate.
2. The tight crop of that region, for detail.
3. Scholarly context for the plate (motto, discourse, expected motifs). Use it \
to inform naming, but your identification must be driven by what is visibly in \
the red region -- if the discourse mentions a salamander and the red region \
shows a dog, say dog.

Naming rules:
- Name what is depicted concisely and concretely ("standing operator feeding a \
furnace with a blow-pipe", "coin-filled two-handled basin on a stone block").
- Use period-accurate apparatus vocabulary only when the form genuinely \
supports it (athanor, cucurbit, alembic, retort, crucible, bellows, still); \
otherwise use plain words. Never use an apparatus term for a human figure, \
animal, or building.
- If the plate itself carries an engraved caption naming the figure, prefer it.

Quality verdict (independent of the label -- judge the REGION):
- good_single_object: one coherent object/figure, cleanly bounded
- multiple_objects_bundled: the region lumps several distinct elements together
- whole_scene: the region covers all or nearly all of the plate
- fragment: only part of an object (a head without its body, half a vessel)
- background_or_empty: no meaningful subject

Always answer by calling the record_identification tool. Be honest with \
confidence: "high" only when the identification is unambiguous."""


TOOL = {
    "name": "record_identification",
    "description": "Record the visual identification of the highlighted region.",
    "input_schema": {
        "type": "object",
        "properties": {
            "identification": {
                "type": "string",
                "description": "Concise, concrete name of what the red region "
                               "depicts (a short noun phrase, not a sentence).",
            },
            "category": {"type": "string", "enum": CATEGORIES},
            "extraction_quality": {"type": "string", "enum": QUALITY},
            "detector_label_verdict": {
                "type": "string", "enum": ["correct", "wrong", "partially_correct"],
                "description": "Whether the detector's label names what the "
                               "region actually depicts.",
            },
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "distinguishing_features": {
                "type": "string",
                "description": "The concrete visual cues that drove the call.",
            },
            "notes": {"type": "string"},
        },
        "required": ["identification", "category", "extraction_quality",
                     "detector_label_verdict", "confidence",
                     "distinguishing_features"],
    },
}


def encode_image(path: Path, max_edge: int) -> tuple[str, str]:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if max(w, h) > max_edge:
        scale = max_edge / max(w, h)
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return "image/jpeg", base64.standard_b64encode(buf.getvalue()).decode("ascii")


def resolve_asset(meta_path: Path, recorded: str | None, suffix: str) -> Path | None:
    """Prefer the absolute path recorded in meta.json; fall back to a sibling
    file derived from the meta filename (paths break if the repo moves)."""
    if recorded and Path(recorded).exists():
        return Path(recorded)
    cand = meta_path.with_name(meta_path.name.replace("_meta.json", suffix))
    return cand if cand.exists() else None


def collect_targets(stems: list[str] | None, reviewed_only: bool,
                    force: bool, existing: dict) -> list[dict]:
    reviewed = {}
    if REVIEW_DECISIONS.exists():
        reviewed = json.loads(REVIEW_DECISIONS.read_text(encoding="utf-8"))

    targets = []
    for emblem_dir in sorted(p for p in EXTRACTED.iterdir() if p.is_dir()):
        emblem_id = emblem_dir.name
        if stems and emblem_id not in stems:
            continue
        for sub in ("individual", "composites"):
            for meta_path in sorted((emblem_dir / sub).glob("*_meta.json")):
                obj_stem = meta_path.name[: -len("_meta.json")]
                key = f"{emblem_id}__{obj_stem}"
                if reviewed_only and key not in reviewed:
                    continue
                if key in existing and not force:
                    continue
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                crop = resolve_asset(meta_path, meta.get("crop_jpg"), "_crop.jpg")
                overlay = resolve_asset(meta_path, meta.get("review_overlay"),
                                        "_review.jpg")
                if not crop or not overlay:
                    print(f"  ! {key}: missing crop/overlay, skipped")
                    continue
                targets.append({
                    "key": key, "emblem_id": emblem_id, "obj_stem": obj_stem,
                    "meta": meta, "crop": crop, "overlay": overlay,
                })
    return targets


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stems", nargs="*", help="Only these emblem dirs.")
    ap.add_argument("--reviewed-only", action="store_true",
                    help="Calibration: only objects with a human verdict in "
                         "review_decisions.json.")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="Collect and list targets; no API calls, no writes.")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--out", default=str(VERDICTS_OUT))
    args = ap.parse_args()

    out_path = Path(args.out)
    existing = {}
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))

    targets = collect_targets(args.stems, args.reviewed_only, args.force, existing)
    if args.limit:
        targets = targets[: args.limit]
    if not targets:
        print("Nothing to do (all verdicted? use --force).")
        return
    print(f"{len(targets)} object(s) to identify with {args.model}"
          f"{' (DRY RUN)' if args.dry_run else ''}\n")
    if args.dry_run:
        for t in targets:
            print(f"  {t['key']}  detector={t['meta'].get('label')!r} "
                  f"cat={t['meta'].get('category')}")
        return

    key = load_env_key()
    if not key:
        print("ERROR: no ANTHROPIC_API_KEY in environment or .env -- aborting "
              "before any API call.")
        sys.exit(2)

    import anthropic
    client = anthropic.Anthropic(api_key=key)
    emblem_ctx = load_emblem_context()

    n_err = 0
    usage_in = usage_out = 0
    for n, t in enumerate(targets, 1):
        meta = t["meta"]
        ctx = context_block(emblem_ctx.get(t["emblem_id"]))
        try:
            ov_mt, ov_b64 = encode_image(t["overlay"], OVERLAY_MAX_EDGE)
            cr_mt, cr_b64 = encode_image(t["crop"], CROP_MAX_EDGE)
            resp = client.messages.create(
                model=args.model,
                max_tokens=2048,
                system=[{"type": "text", "text": SYSTEM,
                         "cache_control": {"type": "ephemeral"}}],
                tools=[TOOL],
                tool_choice={"type": "tool", "name": "record_identification"},
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {
                            "type": "base64", "media_type": ov_mt, "data": ov_b64}},
                        {"type": "image", "source": {
                            "type": "base64", "media_type": cr_mt, "data": cr_b64}},
                        {"type": "text", "text":
                            f"PLATE CONTEXT:\n{ctx}\n\n"
                            f"Detector's (unreliable) claim for the red region: "
                            f"label=\"{meta.get('label')}\", "
                            f"category=\"{meta.get('category')}\", "
                            f"score={meta.get('score', 0):.2f}. "
                            f"Identify the red region from the images."},
                    ],
                }],
            )
            verdict = next((b.input for b in resp.content if b.type == "tool_use"),
                           None)
            if verdict is None:
                raise RuntimeError("no tool_use block in response")
            usage_in += resp.usage.input_tokens + \
                getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
            usage_out += resp.usage.output_tokens
        except Exception as exc:
            n_err += 1
            print(f"[{n}/{len(targets)}] {t['key']}: ERROR {exc}")
            continue

        existing[t["key"]] = {
            "emblem_id": t["emblem_id"],
            "object_stem": t["obj_stem"],
            "detector_label": meta.get("label"),
            "detector_category": meta.get("category"),
            "detector_score": meta.get("score"),
            **verdict,
            "model": args.model,
            "verdicted_at": datetime.now(timezone.utc).isoformat(),
        }
        # checkpoint after every verdict (rate-limit-kill safe)
        out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False),
                            encoding="utf-8")
        mark = "==" if verdict["detector_label_verdict"] == "correct" else "!="
        print(f"[{n}/{len(targets)}] {t['key']}: '{meta.get('label')}' {mark} "
              f"'{verdict['identification']}' "
              f"({verdict['confidence']}, {verdict['extraction_quality']})")

    print(f"\nDone: {len(targets) - n_err} verdicts ({n_err} errors) -> {out_path}")
    print(f"Tokens: ~{usage_in} in / ~{usage_out} out")


if __name__ == "__main__":
    main()
