"""
seed_image_descriptions.py — Populate NULL image_description fields in emblems table.

Updates only rows where image_description IS NULL.
Does not overwrite existing descriptions.

Idempotent: safe to re-run.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "atalanta.db"

# Image descriptions for emblems currently missing them.
# Each describes what the viewer sees in the emblem plate.
DESCRIPTIONS = {
    8: (
        "A man pierces a large egg with a flaming sword. "
        "The egg rests on a surface while fire engulfs the blade, symbolizing the philosophical egg opened by heat."
    ),
    9: (
        "An old man sits locked inside a glass house with a fruit-bearing tree. "
        "Dew falls on the sealed enclosure as the elder eats the tree's fruit, growing young again."
    ),
    10: (
        "A woman washes clothes at a riverbank, wringing and beating linens in flowing water. "
        "The scene of laundering evokes the alchemical ablution and purification of matter."
    ),
    11: (
        "The goddess Latona stands with her children Apollo and Diana. "
        "Peasants in the background are transformed into frogs for mocking her, the water of a pond at their feet."
    ),
    12: (
        "A man tears pages from books while a lion devours the sun nearby. "
        "The scene combines the whitening of Latona (lead into silver) with the destruction of false learning."
    ),
    14: (
        "A potter shapes clay on a wheel, working with wet and dry materials. "
        "The workshop scene shows the craft of forming vessels, an analogy for the alchemical regulation of elements."
    ),
    15: (
        "A potter works at his craft, shaping vessels from earth and water. "
        "Smoke rises from a kiln in the background, illustrating the interplay of the four elements in creation."
    ),
    18: (
        "Four spheres of fire burn at graduated intensities, from gentle warmth to roaring blaze. "
        "The scene illustrates the four degrees of alchemical fire required for the work."
    ),
    19: (
        "A warrior strikes down one of four figures standing together. "
        "The death of one causes the others to fall, representing the interdependence of the four elements."
    ),
    20: (
        "A pregnant woman rests while Nature, depicted as a maternal figure, oversees the gestation. "
        "The scene parallels the philosophical child's growth to the regulation of an embryo in the womb."
    ),
    22: (
        "A woman stands before a hearth, cooking in a pot over a fire. "
        "The domestic scene of women's kitchen work represents the slow, patient coction of the white lead into gold."
    ),
    23: (
        "Two fish swim in a sea, circling one another. "
        "They represent spirit and soul moving through the body (the water), destined to dissolve into unity."
    ),
    25: (
        "A dragon coils in a landscape while Sol and Luna — brother and sister — approach to slay it. "
        "The dragon cannot die unless killed by both solar and lunar principles together."
    ),
    29: (
        "A salamander sits calmly within roaring flames, unharmed by the fire. "
        "The creature's imperviousness to heat symbolizes the Stone's ability to endure the alchemical fire."
    ),
    30: (
        "A hermaphrodite figure stands between two mountains labeled Mercury and Venus. "
        "The Rebis, born from the union of opposites, displays both male and female attributes."
    ),
    32: (
        "A diver retrieves coral from beneath the sea while above, harvested branches harden in the open air. "
        "Soft underwater coral turns rigid and red when exposed, paralleling the Stone's solidification."
    ),
    35: (
        "A mother nurses an infant at her breast in an interior setting. "
        "The philosophical child feeds on maternal milk, growing toward perfection through sustained nourishment."
    ),
    36: (
        "A stone is shown cast upon the earth, raised onto a mountaintop, suspended in the air, and fed by a river. "
        "Mercury passes through all four elements — earth, mountain, air, and water."
    ),
    37: (
        "White smoke, a lion, and water issue from an athanor or furnace. "
        "Three substances sufficient for the mastery — fume, beast, and liquid — converge in the alchemical vessel."
    ),
    39: (
        "Oedipus confronts the Sphinx on a rocky crag, answering her riddle. "
        "In the background, the defeated Sphinx falls from the cliff. Oedipus's triumph leads to his fateful marriage."
    ),
    40: (
        "Figures drink from two springs that merge into a single stream. "
        "The two waters — one white, one red — unite into the Virgin's Milk, the single mercurial fountain."
    ),
    41: (
        "Venus rushes toward the fallen Adonis, gored by a wild boar in a woodland clearing. "
        "Her blood stains the white roses red as she reaches the dying youth."
    ),
    42: (
        "Lady Nature walks ahead while a man follows her with a staff and lantern. "
        "The alchemist tracks Nature's footsteps through a landscape, guided by experience and illumination."
    ),
    43: (
        "A figure listens intently as sound resonates between two mountaintops. "
        "Echo returns the voice from peak to peak, symbolizing the hearing of Nature's hidden speech."
    ),
    45: (
        "Two eagles meet at a central point, one flying from the East and the other from the West. "
        "They converge at Jupiter's marker, the omphalos or navel of the world."
    ),
    46: (
        "Two eagles soar toward each other from opposite horizons. "
        "Their meeting at the center marks the equilibrium of volatile and fixed principles."
    ),
    47: (
        "A wolf from the East and a dog from the West bite each other viciously. "
        "Their mutual combat in a landscape represents the fierce union of opposing mercurial and sulphurous natures."
    ),
    49: (
        "The child Orion stands with three fathers — Jupiter, Neptune, and Mercury — who claim parentage. "
        "The philosophical child acknowledges three origins, born of celestial, aqueous, and mercurial seed."
    ),
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    updated = 0
    for number, desc in DESCRIPTIONS.items():
        cur = conn.execute(
            "UPDATE emblems SET image_description = ? "
            "WHERE number = ? AND image_description IS NULL",
            (desc, number),
        )
        if cur.rowcount > 0:
            updated += 1

    conn.commit()
    conn.close()
    print(f"Updated {updated} emblem image_descriptions (of {len(DESCRIPTIONS)} provided).")


if __name__ == "__main__":
    main()
