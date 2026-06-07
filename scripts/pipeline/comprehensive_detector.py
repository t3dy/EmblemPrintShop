"""
Comprehensive multi-category object detection for emblem images.

Runs GroundingDINO across six semantic category groups to detect every visual
object present in an emblem — figures, animals, plants, landscape features,
architecture, and hand-held objects/equipment. Results from all passes are
merged and deduplicated via IoU-NMS so that the same physical object detected
by two different category prompts collapses to one entry.

Category groupings are tuned for early modern alchemical and mythological
emblem vocabulary: Atalanta Fugiens, Hypnerotomachia, Rosarium, Splendor Solis,
etc. Terms within a prompt are period-separated as GroundingDINO requires.
"""
from __future__ import annotations

from .detector import detect_elements

# Six semantic groups. Each value is a single GroundingDINO prompt containing
# period-separated terms. Kept to ~15-20 terms each to avoid tokeniser overflow.
CATEGORY_PROMPTS: dict[str, str] = {
    "figures": (
        "person . man . woman . angel . child . king . queen . hermaphrodite . "
        "skeleton . warrior . old man . witch . pilgrim . philosopher . figure"
    ),
    "animals": (
        "lion . eagle . bird . serpent . dragon . horse . dog . wolf . fish . "
        "deer . bear . ox . lamb . peacock . swan . dove . raven . pelican . "
        "phoenix . tortoise . crab . bee . butterfly . frog . hare . fox"
    ),
    "plants": (
        "tree . plant . flower . herb . rose . lily . thistle . vine . branch . "
        "bush . fruit . root . grass . reed . palm . wreath . laurel . oak . thorn"
    ),
    "landscape": (
        "mountain . rock . cliff . river . water . sea . cloud . sun . moon . "
        "star . fire . flame . earth . sky . hill . cave . spring . wave . "
        "rainbow . lightning . volcano . forest"
    ),
    "architecture": (
        "castle . tower . building . arch . column . wall . gate . bridge . "
        "ruin . temple . house . furnace . athanor . hearth . door . window . "
        "chimney . tomb . obelisk . labyrinth . altar"
    ),
    "objects": (
        "sword . spear . shield . axe . staff . wand . scepter . key . chain . "
        "crown . ring . book . scroll . torch . lamp . mirror . hourglass . "
        "vessel . flask . retort . cauldron . cup . chalice . globe . egg . "
        "wheel . bellows . scales . crucible . anvil . lute . trumpet . drum"
    ),
    # Focused apparatus pass — shorter prompts get better precision on
    # alchemical lab equipment that the broad objects prompt can miss.
    "equipment": (
        "athanor . furnace . alembic . retort . flask . crucible . "
        "distillation vessel . philosophical egg . scales . balance . "
        "bellows . cauldron . mortar . pestle"
    ),
}


def _iou(bbox_a: list[int], bbox_b: list[int]) -> float:
    """IoU between two [x, y, w, h] bounding boxes."""
    ax1, ay1, aw, ah = bbox_a
    bx1, by1, bw, bh = bbox_b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    inter = (ix2 - ix1) * (iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def _nms(detections: list[dict], iou_threshold: float = 0.5) -> list[dict]:
    """
    Greedy NMS across detections from multiple category passes.

    Two detections from different category groups that have IoU > iou_threshold
    are treated as duplicates; the higher-confidence one is kept. This collapses
    'person' and 'man' detecting the same figure, while preserving genuinely
    distinct overlapping objects like 'man' and 'sword' (whose IoU is typically
    0.1-0.25 since the sword bbox is much smaller than the man bbox).
    """
    detections = sorted(detections, key=lambda d: d["score"], reverse=True)
    kept: list[dict] = []
    for det in detections:
        suppressed = any(_iou(det["bbox"], k["bbox"]) > iou_threshold for k in kept)
        if not suppressed:
            kept.append(det)
    return kept


def detect_all_objects(
    image_path: str,
    threshold: float = 0.25,
    categories: list[str] | None = None,
    nms_iou_threshold: float = 0.50,
) -> list[dict]:
    """
    Run comprehensive multi-category detection on a single emblem image.

    Args:
        image_path: Path to the emblem image (JPG or PNG).
        threshold: Minimum confidence score for each individual detection.
        categories: Subset of CATEGORY_PROMPTS keys to run (default: all six).
        nms_iou_threshold: IoU threshold for cross-category duplicate suppression.

    Returns:
        List of detection dicts, sorted descending by score:
            {
                "bbox": [x, y, w, h],
                "bbox_xyxy": [x1, y1, x2, y2],
                "score": float,
                "label": str,
                "category": str,   # which category group found it
            }
    """
    target_categories = categories or list(CATEGORY_PROMPTS.keys())
    all_detections: list[dict] = []

    for cat in target_categories:
        prompt = CATEGORY_PROMPTS[cat]
        detections = detect_elements(image_path, prompt, threshold=threshold)
        for det in detections:
            det["category"] = cat
        all_detections.extend(detections)
        print(f"  [{cat}] {len(detections)} detection(s)")

    deduped = _nms(all_detections, iou_threshold=nms_iou_threshold)
    print(f"  -> {len(all_detections)} total -> {len(deduped)} after NMS")
    return deduped
