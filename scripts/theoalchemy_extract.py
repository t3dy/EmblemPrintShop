"""
Re-extract Maier emblems 1-20 using the richer visual_elements descriptions
from TheosophicalAlchemyDB's maier_atalanta_fugiens_emblems_metadata.json.

These prompts are concrete visual descriptions ("woman nursing toad",
"salamander in flames", "peacock tail feathers") vs. our earlier generic
auto-prompts derived only from motto keywords.

Usage:
    python scripts/theoalchemy_extract.py
    python scripts/theoalchemy_extract.py --dry-run
    python scripts/theoalchemy_extract.py --emblem 5   # single emblem
"""
import argparse
import json
import os
import sys
import warnings
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

PROJECT_ROOT = Path(__file__).parent.parent
THEO_META    = Path(r"C:\Dev\TheosophicalAlchemyDB\data\maier_atalanta_fugiens_emblems_metadata.json")
EMBLEM_IMGS  = PROJECT_ROOT / "sources" / "claudiens" / "site" / "images" / "emblems"
OUTPUT_DIR   = PROJECT_ROOT / "assets" / "extracted"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


def _concrete_prompt(visual_elements: list[str]) -> str:
    """
    Derive a GroundingDINO-friendly prompt from TheoAlchemyDB visual_elements.
    Works at word-token level to avoid redundant repetition.
    """
    # Priority-ordered mapping: first matching element wins for its category
    ELEMENT_PROMPTS: list[tuple[str, str]] = [
        # Specific creatures / figures first (most distinctive)
        ("toad",         "woman nursing toad"),
        ("salamander",   "salamander fire creature"),
        ("peacock",      "peacock bird feathers"),
        ("chick",        "egg hatching chick bird"),
        ("ouroboros",    "ouroboros serpent dragon"),
        ("androgyn",     "androgyne hermaphrodite figure"),
        ("bride",        "woman bride figure"),
        ("naaman",       "man figure river water"),
        ("potter",       "man potter wheel clay vessel"),
        ("scales",       "scales balance stone water"),
        # Paired figures
        ("brother and sister", "man woman figure cup"),
        ("two figures",  "two figures bath water"),
        # Generic figure types
        ("royal figure", "king crown figure"),
        ("king",         "king figure"),
        ("woman nursing","woman nursing infant"),
        ("earth mother", "woman nursing infant figure"),
        ("nursing",      "woman nursing infant figure"),
        ("woman at work","woman figure washing"),
        ("washing linen","woman washing cloth"),
        ("woman",        "woman figure"),
        ("man",          "man figure"),
        # Objects / apparatus
        ("furnace",      "furnace fire"),
        ("vessel",       "alchemical vessel"),
        ("egg",          "egg"),
        ("fire",         "fire furnace"),
        ("river",        "figure water river"),
        ("bath",         "figures bath water"),
        ("cave",         "figure cave darkness"),
        ("star",         "figure star sky"),
        # Landscape / abstract
        ("wind",         "figure wind"),
        ("decay",        "figure plant decay"),
        ("circle",       "group figures circle"),
        ("philosophers", "group figures men"),
    ]
    lower_elements = [e.lower() for e in visual_elements]
    combined = " ".join(lower_elements)

    # Collect matching prompts, stop when we have 2 distinct prompts
    tokens: list[str] = []
    seen_words: set[str] = set()
    for key, prompt in ELEMENT_PROMPTS:
        if key in combined:
            for word in prompt.split():
                if word not in seen_words:
                    seen_words.add(word)
                    tokens.append(word)
            if len(seen_words) >= 8:
                break

    return " ".join(tokens) if tokens else ""


def load_emblem_prompts() -> dict[int, dict]:
    """
    Returns {emblem_number: {"prompt": str, "visual_elements": [...], ...}}
    """
    if not THEO_META.exists():
        raise FileNotFoundError(f"TheoAlchemyDB metadata not found: {THEO_META}")
    data = json.loads(THEO_META.read_text(encoding="utf-8"))
    result = {}
    for rec in data.get("emblems", []):
        n = rec["emblem_number"]
        ve = rec.get("visual_elements", [])
        prompt = _concrete_prompt(ve)
        result[n] = {
            "emblem_number": n,
            "title": rec.get("english_title", ""),
            "alchemical_stage": rec.get("alchemical_stage", ""),
            "visual_elements": ve,
            "prompt": prompt,
            "source": "TheosophicalAlchemyDB",
        }
    return result


def main():
    parser = argparse.ArgumentParser(description="Extract Maier emblems 1-20 with TheoAlchemyDB prompts")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without running extraction")
    parser.add_argument("--emblem", type=int, default=None, help="Process only this emblem number")
    parser.add_argument("--threshold", type=float, default=0.20, help="Detection threshold (default 0.20)")
    args = parser.parse_args()

    prompts = load_emblem_prompts()

    if args.emblem:
        subset = {args.emblem: prompts[args.emblem]} if args.emblem in prompts else {}
        if not subset:
            print(f"Emblem {args.emblem} not found in TheoAlchemyDB metadata")
            sys.exit(1)
        prompts = subset

    print(f"TheoAlchemyDB prompts for Maier emblems 1–20")
    print(f"{'#':>3}  {'Prompt':<45}  Visual elements")
    print("-" * 100)
    for n, info in sorted(prompts.items()):
        ve_short = ", ".join(info["visual_elements"][:2])
        print(f"{n:>3}  {info['prompt']:<45}  {ve_short}")

    if args.dry_run:
        print("\n[dry-run] No extraction performed.")
        return

    from pipeline.extractor import extract_element

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    skipped = []

    for n, info in sorted(prompts.items()):
        img_path = EMBLEM_IMGS / f"emblem-{n:02d}.jpg"
        if not img_path.exists():
            print(f"[{n:>2}] MISSING image: {img_path.name}")
            skipped.append(n)
            continue

        prompt = info["prompt"]
        if not prompt:
            print(f"[{n:>2}] SKIP (no concrete prompt): {info['visual_elements']}")
            skipped.append(n)
            continue

        print(f"[{n:>2}] {img_path.name} | {prompt}")
        try:
            result = extract_element(
                str(img_path),
                prompt=prompt,
                output_dir=str(OUTPUT_DIR),
                detection_threshold=args.threshold,
                use_paper_removal=True,
                save_review_overlay=True,
            )
            if result:
                # Tag with TheoAlchemyDB provenance
                result["theo_title"] = info["title"]
                result["theo_stage"] = info["alchemical_stage"]
                result["theo_visual_elements"] = info["visual_elements"]
                result["prompt_source"] = "TheosophicalAlchemyDB"
                results.append(result)
                px = result["mask_pixel_count"]
                score = result["score"]
                print(f"     score={score:.3f}  mask={px:,}px  -> {Path(result['transparent_png']).name}")
            else:
                print(f"     no detection (try lowering --threshold)")
                skipped.append(n)
        except Exception as e:
            import traceback
            print(f"     ERROR: {e}")
            traceback.print_exc()
            skipped.append(n)

    print(f"\nDone: {len(results)} extracted, {len(skipped)} skipped/failed")
    if skipped:
        print(f"Skipped emblems: {skipped}")

    # Save TheoAlchemyDB-sourced results alongside the main batch
    out_path = OUTPUT_DIR / "theoalchemy_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
