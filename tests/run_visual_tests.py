"""
Visual test runner — outputs review images for manual inspection.

This is NOT a pytest test. Run directly:
  python tests/run_visual_tests.py

Processes the known test cases (lion, dragon, amphora) and saves outputs to
tests/output/ for side-by-side visual review.

Each test case saves:
  tests/output/<name>_transparent.png  — the cutout
  tests/output/<name>_review.jpg       — original vs mask overlay
  tests/output/<name>_meta.json        — detection metadata
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

TEST_CASES = [
    {
        "name": "emblem37_lion",
        "image": "sources/claudiens/site/images/emblems/emblem-37.jpg",
        "prompt": "lion",
        "expected_bbox_approx": [180, 330, 1070, 430],  # from manifest
    },
    {
        "name": "emblem25_dragon",
        "image": "sources/claudiens/site/images/emblems/emblem-25.jpg",
        "prompt": "dragon serpent",
        "expected_bbox_approx": [460, 520, 220, 200],
    },
    {
        "name": "emblem16_dragon",
        "image": "sources/claudiens/site/images/emblems/emblem-16.jpg",
        "prompt": "dragon serpent",
        "expected_bbox_approx": None,
    },
    {
        "name": "emblem30_androgyne",
        "image": "sources/claudiens/site/images/emblems/emblem-30.jpg",
        "prompt": "hermaphrodite androgyne figure",
        "expected_bbox_approx": [70, 110, 550, 1150],
    },
    {
        "name": "hp_p330_amphora",
        "image": "sources/hypnerotomachia-polyphili/site/images/woodcuts_1499/hp1499_p330.jpg",
        "prompt": "amphora vessel",
        "expected_bbox_approx": [960, 1850, 460, 650],
    },
    {
        "name": "hp_p393_lion",
        "image": "sources/hypnerotomachia-polyphili/site/images/woodcuts_1499/hp1499_p393.jpg",
        "prompt": "lion",
        "expected_bbox_approx": None,
    },
]

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def run():
    from pipeline.extractor import extract_element

    passed = 0
    failed = 0
    skipped = 0
    summary = []

    for case in TEST_CASES:
        img_path = PROJECT_ROOT / case["image"]
        if not img_path.exists():
            print(f"[SKIP] {case['name']}: image not found at {img_path}")
            skipped += 1
            continue

        print(f"\n[RUN ] {case['name']} — prompt: '{case['prompt']}'")
        try:
            result = extract_element(
                str(img_path),
                prompt=case["prompt"],
                output_dir=str(OUTPUT_DIR),
                use_paper_removal=True,
                save_review_overlay=True,
            )

            if result is None:
                print(f"  [FAIL] No detection")
                failed += 1
                summary.append({"name": case["name"], "status": "no_detection"})
                continue

            print(f"  score     : {result['score']:.3f}")
            print(f"  bbox      : {result['bbox']}")
            print(f"  mask px   : {result['mask_pixel_count']:,}")
            print(f"  output    : {result['transparent_png']}")

            # Check against expected bbox if provided
            if case["expected_bbox_approx"]:
                ex, ey, ew, eh = case["expected_bbox_approx"]
                dx, dy, dw, dh = result["bbox"]
                cx_expected = ex + ew / 2
                cy_expected = ey + eh / 2
                cx_detected = dx + dw / 2
                cy_detected = dy + dh / 2
                dist = ((cx_expected - cx_detected)**2 + (cy_expected - cy_detected)**2)**0.5
                print(f"  centroid dist from expected: {dist:.0f}px", end="")
                if dist > max(ew, eh) * 0.5:
                    print(" [WARNING: may be wrong region]")
                else:
                    print(" [ok]")

            print(f"  [PASS]")
            passed += 1
            summary.append({"name": case["name"], "status": "ok", **result})

        except Exception as exc:
            print(f"  [ERROR] {exc}")
            import traceback
            traceback.print_exc()
            failed += 1
            summary.append({"name": case["name"], "status": "error", "error": str(exc)})

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"Review images saved to: {OUTPUT_DIR}")

    summary_path = OUTPUT_DIR / "visual_test_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    run()
