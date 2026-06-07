"""
End-to-end integration tests for the full extraction pipeline.

These run the complete detect → segment → postprocess chain on known images
and assert that outputs are plausible. They are slow (model inference) so
run separately from unit tests: pytest tests/test_pipeline_integration.py -v -s
"""
import pytest
import numpy as np
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.extractor import extract_element

EMBLEM_37 = Path(__file__).parent.parent / "sources/claudiens/site/images/emblems/emblem-37.jpg"
EMBLEM_25 = Path(__file__).parent.parent / "sources/claudiens/site/images/emblems/emblem-25.jpg"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


@pytest.mark.slow
@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_full_pipeline_lion_produces_rgba_output():
    """Full pipeline on emblem 37 should produce a valid RGBA transparent PNG."""
    result = extract_element(str(EMBLEM_37), prompt="lion")
    assert result is not None, "Pipeline returned None"
    assert "transparent_png" in result, "Result must include transparent_png"
    img = Image.open(result["transparent_png"])
    assert img.mode == "RGBA", f"Output must be RGBA, got {img.mode}"


@pytest.mark.slow
@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_lion_transparent_png_has_significant_figure_pixels():
    """The lion cutout should have a meaningful number of opaque pixels."""
    result = extract_element(str(EMBLEM_37), prompt="lion")
    arr = np.array(Image.open(result["transparent_png"]))
    opaque_pixels = (arr[:, :, 3] == 255).sum()
    assert opaque_pixels > 5000, (
        f"Only {opaque_pixels} opaque pixels — figure may not have been captured"
    )


@pytest.mark.slow
@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_lion_mask_does_not_fill_entire_image():
    """
    The lion mask should cover < 45% of the image area.
    The lion is the dominant figure in emblem 37 but the plate also contains
    landscape, text bands, and border — a mask covering more than 45% is
    almost certainly capturing the whole scene rather than just the animal.
    """
    import cv2
    result = extract_element(str(EMBLEM_37), prompt="lion")
    arr = np.array(Image.open(result["transparent_png"]))
    h, w = arr.shape[:2]
    opaque_pixels = (arr[:, :, 3] == 255).sum()
    total_pixels = h * w
    coverage = opaque_pixels / total_pixels
    assert coverage < 0.45, (
        f"Mask covers {coverage:.1%} of image — likely captured entire scene, not just lion"
    )


@pytest.mark.slow
@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_result_includes_required_metadata_fields():
    """Each result should include bbox, score, motif, and file paths."""
    result = extract_element(str(EMBLEM_37), prompt="lion")
    for field in ["bbox", "score", "prompt", "source_image", "transparent_png", "crop_jpg"]:
        assert field in result, f"Result missing required field: {field}"


@pytest.mark.slow
@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_pipeline_saves_outputs_to_disk(tmp_path):
    """Pipeline should write transparent PNG and crop JPG to the specified output dir."""
    result = extract_element(str(EMBLEM_37), prompt="lion", output_dir=str(tmp_path))
    assert Path(result["transparent_png"]).exists(), "Transparent PNG was not saved to disk"
    assert Path(result["crop_jpg"]).exists(), "Crop JPG was not saved to disk"


@pytest.mark.slow
@pytest.mark.skipif(not EMBLEM_25.exists(), reason="Test image not found")
def test_full_pipeline_dragon_produces_output():
    """Full pipeline on emblem 25 should detect and segment a dragon/serpent."""
    result = extract_element(str(EMBLEM_25), prompt="dragon serpent")
    assert result is not None, "No result for dragon/serpent in emblem 25"
