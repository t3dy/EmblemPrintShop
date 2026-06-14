"""
Re-identify extracted cutouts by LOOKING at the image with a Claude vision model,
instead of trusting GroundingDINO's (frequently wrong) label.

The detector is good at finding objects but bad at naming them: it emits garbled
compound labels ("wolf lambtoise frog"), wrong species (hare -> "wolf",
lion -> "horse"), and category errors (a winged angel filed under "animals").
This pass sends each crop to claude-opus-4-8 with the diagnostic rubric in
docs/ANIMAL_RECOGNITION_SYSTEM.md and the controlled vocabulary from
data/motifs.json, and records a structured verdict back into each emblem's
summary.json -- preserving the original detector label for audit.

Usage:
    setx ANTHROPIC_API_KEY "sk-ant-..."        # (Windows; new shell after)
    python -m scripts.reidentify_objects                       # all animal crops, resume
    python -m scripts.reidentify_objects --category animals     # default
    python -m scripts.reidentify_objects --category all         # every crop (expensive)
    python -m scripts.reidentify_objects --stems cramer_page_0045 stolcius_plate_012
    python -m scripts.reidentify_objects --limit 20 --dry-run   # preview, no write
    python -m scripts.reidentify_objects --force                # re-verify already-done

Resumable: skips objects that already have a `verified_label` unless --force.
Writes a run report to assets/extracted_all/reidentify_report.json and prints a diff.

The verdict fields added to each individual object in summary.json:
    verified_label        canonical motif id, or not_an_animal / unknown_creature /
                          multiple / unidentifiable
    verified_category     animal | human_figure | object | plant | architecture | mixed | other
    verified_is_animal    bool
    verified_confidence   high | medium | low
    verified_multiple     bool   (crop holds >1 distinct subject -> candidate for re-segmentation)
    verified_secondary    [other motif ids visible in the crop]
    verified_features     short text: the discriminating features that drove the call
    verified_notes        anything else worth recording
    label_source          "claude-vision:<model>"
    verified_at           ISO timestamp
The original `label` and `score` are never overwritten.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# UTF-8 stdout so motif names / unicode don't crash cp1252 consoles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent
EXTRACTED = ROOT / "assets" / "extracted_all"
MOTIFS_PATH = ROOT / "data" / "motifs.json"
RUBRIC_PATH = ROOT / "docs" / "ANIMAL_RECOGNITION_SYSTEM.md"
MODEL = "claude-opus-4-8"
MAX_EDGE = 768          # downscale crops before upload to save image tokens

ESCAPE_HATCHES = ["not_an_animal", "unknown_creature", "multiple", "unidentifiable"]


def load_animal_vocab() -> list[dict]:
    m = json.loads(MOTIFS_PATH.read_text(encoding="utf-8"))
    items = m if isinstance(m, list) else m.get("motifs", m)
    if isinstance(items, dict):
        items = list(items.values())
    out = []
    for i in items:
        if str(i.get("category", "")).lower() in ("animal", "animals", "creature", "beast"):
            out.append({"id": i.get("id"), "appearance": i.get("appearance", "")})
    return out


def build_system_prompt(vocab: list[dict]) -> str:
    rubric = RUBRIC_PATH.read_text(encoding="utf-8") if RUBRIC_PATH.exists() else ""
    vocab_lines = "\n".join(f"- {v['id']}: {v['appearance']}" for v in vocab)
    return (
        "You are an iconographer identifying figures cut out of early-modern "
        "alchemical emblem prints (17th-century intaglio/woodcut: heavy hatching, "
        "paper tone, stylised anatomy). You will be shown ONE extracted cutout and "
        "the label a text-grounding object detector guessed for it. The detector's "
        "label is UNRELIABLE and frequently wrong (wrong species, garbled compound "
        "terms, or a non-animal miscategorised). Identify the figure from the PIXELS "
        "ONLY. Treat the detector label as noise to be checked, not a hint to follow.\n\n"
        "Apply this diagnostic key (read structural features in order; rely on "
        "limbs/wings/tail/head-furniture, not surface texture):\n\n"
        f"{rubric}\n\n"
        "CONTROLLED VOCABULARY (choose verified_label from these ids, or an escape hatch):\n"
        f"{vocab_lines}\n"
        f"Escape hatches: {', '.join(ESCAPE_HATCHES)}\n\n"
        "Always call the record_identification tool with your verdict. In "
        "distinguishing_features, name the concrete cues you used (e.g. 'long ears + "
        "leaping pose + short tail -> hare'). Be honest with confidence: high only "
        "when two or more cues agree."
    )


TOOL = {
    "name": "record_identification",
    "description": "Record the visual identification of the cutout.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verified_label": {
                "type": "string",
                "description": "Canonical motif id, or one of: "
                + ", ".join(ESCAPE_HATCHES),
            },
            "verified_category": {
                "type": "string",
                "enum": ["animal", "human_figure", "object", "plant",
                         "architecture", "mixed", "other"],
            },
            "verified_is_animal": {"type": "boolean"},
            "verified_confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "verified_multiple": {
                "type": "boolean",
                "description": "True if the crop contains more than one distinct subject.",
            },
            "verified_secondary": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Other motif ids visible in the crop (may be empty).",
            },
            "distinguishing_features": {
                "type": "string",
                "description": "The concrete visual cues that drove the identification.",
            },
            "notes": {"type": "string"},
        },
        "required": [
            "verified_label", "verified_category", "verified_is_animal",
            "verified_confidence", "verified_multiple", "distinguishing_features",
        ],
    },
}


def encode_image(path: Path) -> tuple[str, str]:
    """Downscale to MAX_EDGE and return (media_type, base64)."""
    from PIL import Image
    import io

    im = Image.open(path).convert("RGB")
    w, h = im.size
    if max(w, h) > MAX_EDGE:
        scale = MAX_EDGE / max(w, h)
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=88)
    return "image/jpeg", base64.standard_b64encode(buf.getvalue()).decode("ascii")


def collect_targets(category: str, stems: list[str] | None, force: bool):
    """Yield (summary_path, summary_dict, object_dict) for crops to process."""
    summaries = sorted(EXTRACTED.glob("*/summary.json"))
    for sp in summaries:
        stem = sp.parent.name
        if stems and stem not in stems:
            continue
        try:
            data = json.loads(sp.read_text(encoding="utf-8"))
        except Exception:
            continue
        for obj in data.get("individual", []):
            if category != "all" and obj.get("category") != category:
                continue
            if obj.get("verified_label") and not force:
                continue
            cj = obj.get("crop_jpg")
            if cj and Path(cj).exists():
                yield sp, data, obj


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--category", default="animals",
                    help="Object category to re-identify ('all' for every crop). Default: animals")
    ap.add_argument("--stems", nargs="*", help="Only these emblem stems (dir names).")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="Re-verify already-done objects.")
    ap.add_argument("--dry-run", action="store_true", help="Don't write summary.json.")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set. Set it and re-run.")
        sys.exit(2)

    import anthropic
    client = anthropic.Anthropic()

    vocab = load_animal_vocab()
    system = build_system_prompt(vocab)

    targets = list(collect_targets(args.category, args.stems, args.force))
    if args.limit:
        targets = targets[: args.limit]
    if not targets:
        print("Nothing to do (all done? use --force to redo).")
        return

    print(f"Re-identifying {len(targets)} crop(s) with {args.model} "
          f"({'DRY RUN' if args.dry_run else 'writing back'})\n")

    report = []
    changed = 0
    # group writes per summary file so we patch each file once
    by_summary: dict[Path, dict] = {}

    for n, (sp, data, obj) in enumerate(targets, 1):
        by_summary.setdefault(sp, data)
        crop = Path(obj["crop_jpg"])
        try:
            media_type, b64 = encode_image(crop)
            resp = client.messages.create(
                model=args.model,
                max_tokens=1024,
                # system + tools are identical on every call -> cache the prefix
                # (~90% cheaper input tokens after the first request).
                system=[{"type": "text", "text": system,
                         "cache_control": {"type": "ephemeral"}}],
                tools=[TOOL],
                tool_choice={"type": "tool", "name": "record_identification"},
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image",
                         "source": {"type": "base64", "media_type": media_type, "data": b64}},
                        {"type": "text",
                         "text": f"Detector's (unreliable) label for this cutout: "
                                 f"\"{obj.get('label')}\" (category guessed: "
                                 f"{obj.get('category')}). Identify it from the image."},
                    ],
                }],
            )
            verdict = next((b.input for b in resp.content if b.type == "tool_use"), None)
            if verdict is None:
                print(f"[{n}/{len(targets)}] {crop.name}: no verdict, skipping")
                continue
        except Exception as exc:
            print(f"[{n}/{len(targets)}] {crop.name}: ERROR {exc}")
            continue

        old = obj.get("label")
        new = verdict.get("verified_label")
        obj.update({
            "verified_label": new,
            "verified_category": verdict.get("verified_category"),
            "verified_is_animal": verdict.get("verified_is_animal"),
            "verified_confidence": verdict.get("verified_confidence"),
            "verified_multiple": verdict.get("verified_multiple"),
            "verified_secondary": verdict.get("verified_secondary", []),
            "verified_features": verdict.get("distinguishing_features"),
            "verified_notes": verdict.get("notes", ""),
            "label_source": f"claude-vision:{args.model}",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        })
        flag = "  CHANGED" if (new != old) else ""
        if new != old:
            changed += 1
        conf = verdict.get("verified_confidence")
        print(f"[{n}/{len(targets)}] {sp.parent.name}: '{old}' -> '{new}' "
              f"({conf}){flag}")
        report.append({
            "stem": sp.parent.name, "crop": crop.name, "old_label": old,
            "verified_label": new, "category": verdict.get("verified_category"),
            "confidence": conf, "multiple": verdict.get("verified_multiple"),
            "features": verdict.get("distinguishing_features"),
        })

    if not args.dry_run:
        for sp, data in by_summary.items():
            sp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        report_path = EXTRACTED / "reidentify_report.json"
        existing = []
        if report_path.exists():
            try:
                existing = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        report_path.write_text(json.dumps(existing + report, indent=2, ensure_ascii=False),
                               encoding="utf-8")
        print(f"\nReport appended -> {report_path}")

    print(f"\nDone: {len(report)} identified, {changed} labels changed.")


if __name__ == "__main__":
    main()
