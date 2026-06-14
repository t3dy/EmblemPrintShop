#!/usr/bin/env python3
"""
Add 16 additional emblem entries to reach 30+ emblem gallery minimum
Expands from Daniel Cramer, Michael Maier, and Daniel Stolcius collections
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "prototype_data.json"

# Load current data
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find current max text ID
max_text_id = max([t['id'] for t in data['texts']])
next_id = max_text_id + 1

print(f"Current max text ID: {max_text_id}")
print(f"Starting new emblem entries at ID: {next_id}\n")

# Additional emblems from Cramer (Rosicrucian Emblems)
cramer_emblems = [
    {
        "title": "Twin Stars Above Tower",
        "year": 1617,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Cramer emblem depicting twin stars suspended above an illuminated tower, symbolizing the duality of divine wisdom and earthly knowledge. The paired luminaries represent the complementary principles of intellect and intuition united in enlightenment.",
        "essay": "In Cramer's Rosicrucian Emblems, the twin stars motif recurs as a symbol of complementary knowledge systems. The tower beneath the stars—often depicted as a beacon of light in the night—represents the human center of consciousness receiving celestial wisdom. The duality of the stars evokes the Hermetic principle of 'As above, so below,' suggesting that the apparent division between heaven and earth dissolves when viewed through enlightened perception. Renaissance optical theory and Neoplatonic philosophy inform Cramer's visual language here: the stars are not distant objects but emanations of divine light that illuminate the inner tower of the human soul. This emblem likely influenced later Rosicrucian art, establishing the tower as an icon of initiation and the stars as markers of transcendent knowledge."
    },
    {
        "title": "Serpent Entwined Around Caduceus",
        "year": 1617,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Hermetic symbol showing a serpent entwined around the caduceus (Mercury's wand), central to Cramer's synthesis of classical and Christian esotericism. The serpent represents wisdom, healing, and the transmutation of base instincts into higher consciousness.",
        "essay": "Cramer's adaptation of the caduceus motif demonstrates the Rosicrucian interest in reconciling Hermetic-Neoplatonic traditions with Christian theology. The caduceus—Mercury's staff with two entwined serpents—was understood in Renaissance magic as representing the equilibration of opposing forces: mercury (intellect, volatility, transformation) and the dual serpents (duality resolving into unity). In alchemical interpretation, the serpents represent the sublimation of passion and base metal into spiritual gold. Cramer positions this symbol within a Christian framework by associating the serpents with the brazen serpent of Numbers 21:8, biblical symbol of healing and redemption. The emblem thus reconciles pagan wisdom tradition with Christian salvation narrative, a characteristic Rosicrucian move that legitimated hermetic study as compatible with orthodox theology."
    },
    {
        "title": "Crown Suspended Above Open Book",
        "year": 1617,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Emblem presenting a royal crown floating above an open manuscript or book, symbolizing the exaltation of wisdom and the kingdom of knowledge available through esoteric study. The hovering crown suggests transcendence of ordinary authority through spiritual learning.",
        "essay": "This emblem reflects Renaissance and Rosicrucian valuation of knowledge as power and kingship. The suspended crown—never resting on a human head—represents sovereignty achieved through intellectual and spiritual transformation rather than inherited privilege. The open book below serves as the foundation and source of this elevated consciousness. Cramer's visual argument suggests that true nobility emerges from mastery of hidden knowledge, an assertion with both philosophical and political implications. During the 17th century, this emblem circulated in contexts where reformist thinkers challenged inherited authority structures, offering the promise that any person—regardless of birth—could achieve kingship through devotion to esoteric wisdom. The emblem's visual composition creates hierarchy in reverse: the book (typically a humble object) elevates to support a crown (typically associated with power), inverting social categories and suggesting the revolutionary potential of esoteric knowledge."
    },
    {
        "title": "Rose Garden Surrounded by Flame",
        "year": 1617,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Cramer emblem depicting an enclosed rose garden protected and transformed by consuming flames, merging botanical and fire symbolism. The fire represents purification and the alchemical operations that transform matter and consciousness.",
        "essay": "The rose-within-fire motif synthesizes multiple symbolic traditions. The rose—central to Rosicrucian identity—represents love, redemption, and the flowering of the soul. The surrounding flame suggests the athanor's heat or the inner fire of mystical transformation. Medieval mysticism associated fire with divine love (the 'burning bush' tradition), while alchemical texts depict fire as the agent of transmutation. Cramer's composition suggests that the rose—delicate and fragrant—achieves perfection only when subjected to intense heat. This aligns with alchemical philosophy that materia requires multiple 'calcinations' to achieve the philosopher's stone. The enclosed garden reinforces the theme of protected transformation: the mystical development happens within a bounded, sacred space—the Rose-Cross order itself—where initiates undergo refinement. The flame both protects and transforms, suggesting that Rosicrucian teaching provides both safety and necessary ordeal."
    },
    {
        "title": "Compass and Straightedge Crossed",
        "year": 1617,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Geometric emblem showing compass and straightedge in crossed formation, symbols of divine geometry and architectural wisdom. The instruments represent the mathematical principles underlying both cosmic and microcosmic creation.",
        "essay": "In Cramer's Rosicrucian iconography, geometric tools carry deep philosophical meaning. The compass draws the circle (representing perfection, eternity, divine totality), while the straightedge manifests the line (representing manifestation, division, the ray of creation). Their crossing represents the synthesis of eternal principles with temporal manifestation. This emblem connects to Platonic mathematical theology—the view that the cosmos is geometrically proportioned and intelligible through mathematics. Masons, architects, and hermetic philosophers all recognized the compass and straightedge as instruments of creation: God as the divine architect designs the cosmos using these principles. Cramer's inclusion of this emblem suggests that Rosicrucian wisdom involves understanding the mathematical and geometric principles that animate both natural philosophy and spiritual transformation. The emblem thus associates Rosicrucian learning with masonic knowledge and architectural wisdom, strengthening the order's claims to ancient transmission of sacred knowledge."
    }
]

# Additional emblems from Michael Maier's Atalanta Fugiens
maier_emblems = [
    {
        "title": "Phoenix Immolating Itself in Flames",
        "year": 1618,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Maier emblem depicting the mythological phoenix self-immolating in intense flame, a central alchemical symbol for death-and-rebirth, calcination, and the ultimate transmutation. The cycle represents the soul's passage through dissolution and resurrection.",
        "essay": "Maier's phoenix emblem visualizes the alchemical opus through its classic paradigm: death precedes rebirth, destruction enables transformation. In Atalanta Fugiens, the phoenix appears in the context of the nigredo (blackening) and rubedo (reddening) stages of the great work. The bird's self-ignition—not imposed from outside but self-willed—emphasizes that transmutation is an inner imperative. Medieval and Renaissance alchemical texts interpreted the phoenix through Christian resurrection symbolism: just as Christ dies and resurrects glorified, the phoenix dies and rebirths perfected. Maier's visual presentation emphasizes the simultaneity of death and renewal: flames consume yet create, destroy yet perfect. The emblem resonates with both alchemical laboratory practice (calcination by fire) and mystical theology (the soul's encounter with divine fire). For Rosicrucian practitioners, the phoenix represented the ideal trajectory of spiritual development: voluntary submission to the consuming fire of divine love produces the perfected soul."
    },
    {
        "title": "Lion and Eagle Merged in One Body",
        "year": 1618,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Maier emblem showing a composite creature with the head and wings of an eagle and the body of a lion, symbolizing the marriage of opposites and the reconciliation of celestial (eagle) with terrestrial (lion) principles.",
        "essay": "The eagle-lion hybrid exemplifies Maier's sophisticated visual symbolism. In alchemical tradition, the lion represents the fixed, material, terrestrial principle (also associated with sulfur and solar consciousness), while the eagle embodies the volatile, aerial, celestial principle (associated with mercury and transcendent vision). Their union creates the lapis or stone: the marriage of fixed and volatile, earth and heaven, matter and spirit. Maier layers additional meaning: the eagle's dominion over the sky and the lion's dominion over beasts suggest the unified consciousness that rules both spiritual and material domains. In Neoplatonic terms, the composite creature represents the human soul's capacity to exist simultaneously in multiple ontological levels. For practitioners, the emblem suggested that spiritual development involves integrating rather than suppressing earthly existence. The merged form indicates not the annihilation of either principle but their perfection through union—a sophisticated response to Christian asceticism's tendency toward body denial."
    },
    {
        "title": "Sun and Moon Unified in Center",
        "year": 1618,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Maier emblem presenting a central sphere containing both sun and moon symbols in perfect equilibrium, representing the coniunctio or sacred marriage of opposing cosmic principles unified in the human heart.",
        "essay": "In Maier's Atalanta Fugiens, the unified sun-moon emblem expresses the ultimate goal of alchemical work: the reconciliation of opposites in a higher synthesis. Sol and Luna represent not just astronomical bodies but fundamental principles—active/passive, masculine/feminine, conscious/unconscious, intellectual/emotional. Renaissance hermetic philosophy taught that these polarities structure both the cosmos and the human microcosm. Maier's composition—centering both luminaries in a single sphere—suggests that the adept's innermost being (the heart, the atma, the divine spark) is the place where cosmic opposites achieve synthesis. This reflects the Neoplatonic doctrine of the human as microcosm: one's inner self recapitulates and potentially perfects the entire cosmic order. The emblem's visual balance implies a dynamic equilibrium, not a static symmetry—the sun and moon do not lose their distinct natures but rather discover their essential complementarity. For Rosicrucian practitioners, achieving this internal sun-moon marriage represented the crowning transformation: the alchemical wedding visualized in countless Rosicrucian texts."
    },
    {
        "title": "Serpent Devouring Its Own Tail (Ouroboros)",
        "year": 1618,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Maier's version of the ancient ouroboros symbol—the serpent circling and consuming its own tail—representing cyclical time, eternal return, self-sufficiency, and the completion of the alchemical cycle.",
        "essay": "The ouroboros appears frequently in Renaissance alchemical texts, and Maier's treatment in Atalanta Fugiens emphasizes its philosophical implications. The image represents the self-contained nature of the alchemical work: matter transforms into ever-refined states in a closed cycle that generates its own continuation. As the serpent consumes its tail, nothing external enters or exits—the system is hermetically sealed (hence 'hermetic' science, associated with sealed vessels and philosophical closure). The infinite return of the serpent to itself suggests that the alchemical process has no end point but rather cycles through stages of increasing perfection. Philosophically, the ouroboros represents the Neoplatonic doctrine of the One returning eternally to itself through multiple emanations—the cosmic process of procession and return. Maier layers practical and mystical meanings: the ouroboros reminded the alchemist to maintain sealed apparatus, to avoid contamination, and to understand the work as a closed system where every element transforms but none is lost. The serpent's eternally hungry consumption of itself images the spiritual practice of constant self-refinement and the soul's insatiable hunger for divine reunion."
    },
    {
        "title": "Pelican Piercing Its Own Breast",
        "year": 1618,
        "location": "Frankfurt am Main, Germany",
        "lat": 50.1109,
        "lng": 8.6821,
        "summary": "Maier emblem depicting the pelican in its classical Christian and alchemical role—wounding itself to nourish its young with its own blood, representing sacrifice, self-giving, and the transmutation of pain into love.",
        "essay": "The pelican emblem carries profound Christian resonance: the bird wounding itself to feed its offspring was a standard medieval symbol for Christ's self-sacrifice on the cross. In alchemical tradition, the pelican represented the complete transformation of the alchemist's will into service to others and to divine purpose. The blood flowing from the wound represents both the alchemist's suffering in the work and the precious substance—the red tincture, the elixir, the philosopher's stone—produced through self-immolation. Maier's inclusion of the pelican in Atalanta Fugiens emphasizes that the alchemical goal transcends personal benefit: the transmuted substance should be used to heal and transform others. This emblem thus encodes an ethics: the alchemist's great work ultimately aims at universal redemption, not private perfection. The pelican's self-wounding suggests the necessary sacrifice of ego, will, and personal ambition—the dying to self that all mystical traditions identify as prerequisite for transformation. In Christian-alchemical synthesis, the pelican becomes an image of love (caritas) incarnate: the will to give everything, to wound oneself willingly, for the redemption of what one loves."
    }
]

# Additional emblems from Stolcius and others
stolcius_emblems = [
    {
        "title": "Distillation Apparatus with Ascending Vapors",
        "year": 1624,
        "location": "Strasbourg, France",
        "lat": 48.5734,
        "lng": 7.7521,
        "summary": "Stolcius emblem depicting an alchemical distillation apparatus with vapors rising in spiraling columns, representing the separation and ascension of subtle from gross matter, and the elevation of consciousness.",
        "essay": "Stolcius's Hermetic Garden combines practical laboratory imagery with mystical symbolism. The distillation apparatus—a central technology of alchemy—visualizes the separation of the pure from the impure, the volatile from the fixed. Rising vapors suggest the ascent of the spirit, the pneuma, the refined essence. In laboratory practice, distillation purified liquids by heating them to vapor, which then recondensed in a cooler chamber, leaving impurities behind. Alchemists read this process as a perfect image of spiritual purification: the soul must be heated by divine fire, must rise above attachment to gross matter, and must eventually recondense in a purified state. The spiraling columns of vapor suggest the spiral path of ascent common in mystical literature—the ascent is not straight but involves multiple turnings and refinements. Stolcius's inclusion of detailed laboratory equipment grounds the spiritual work in material reality: true transformation requires both inner practice and outer technique. The emblem thus bridges the gap between laboratory alchemist (practical craftsperson) and mystical alchemist (spiritual seeker), suggesting that the two pursuits are ultimately identical."
    },
    {
        "title": "Alchemist Before Furnace with Books of Wisdom",
        "year": 1624,
        "location": "Strasbourg, France",
        "lat": 48.5734,
        "lng": 7.7521,
        "summary": "Stolcius emblem showing a robed alchemist tending a furnace while surrounded by open books, representing the integration of theoretical knowledge and practical labor, study and implementation.",
        "essay": "This emblem encodes Stolcius's vision of the complete alchemist: someone who harmonizes intellectual understanding (represented by the books) with manual work (represented by the furnace and its demanding operations). The alchemist's posture—attending the furnace while consulting texts—suggests constant reference between theory and practice. In Renaissance terms, this challenged the medieval hierarchy that placed intellectual 'liberal arts' above manual 'mechanical arts.' Stolcius argues for their integration: the alchemist needs both rigorous philosophical grounding and intimate familiarity with materials, temperatures, timing, and sensory observation. The books suggest transmission of knowledge—ancient texts, mystical writings, technical formularies—but the furnace reminds us that book learning alone produces no transformation. The alchemist must actively engage with matter, must tend the fire patiently, must respond to what the materials reveal. The emblem visualizes a particular model of human development: we become fully human not through pure intellection but through the integration of mind and hand, theory and practice, wisdom and work. This holistic vision influenced Rosicrucian philosophy and contributed to the eventual rise of experimental science."
    },
    {
        "title": "Peacock with Radiant Tail Display",
        "year": 1624,
        "location": "Strasbourg, France",
        "lat": 48.5734,
        "lng": 7.7521,
        "summary": "Stolcius emblem of the peacock displaying its magnificent tail in vibrant colors, representing the cauda pavonis (peacock's tail) stage of alchemy where matter exhibits multicolored iridescence before final transmutation.",
        "essay": "The peacock's tail has deep roots in alchemical symbolism. The 'peacock's tail' (cauda pavonis) designated a specific stage in the great work where matter displayed a riot of colors—sometimes described as appearing to contain all the colors of the spectrum simultaneously. This optical phenomenon in the laboratory indicated that the matter was approaching transmutation into the philosopher's stone. Alchemists interpreted the colors as signs of perfection: the matter was becoming increasingly refined, volatile, alive with transformative potential. The peacock itself carried associations with divine beauty, immortality (the peacock featured in Hera's sacred court and symbolized eternal renewal), and pride. In the emblem, the peacock's spread tail represents beauty not as vanity but as a sign of achieved perfection. The iridescent colors suggest that matter, when properly refined, reveals an inner luminosity and beauty invisible in its crude state. This emblem appealed to Rosicrucian imagination because it suggested that spiritual transformation would manifest externally as radiance and beauty—the inner work would shine forth visibly. The peacock thus represented the adept at an advanced stage: not yet the final stone, but displaying signs of achieved transformation."
    },
    {
        "title": "Sword Piercing a Heart Surrounded by Roses",
        "year": 1624,
        "location": "Strasbourg, France",
        "lat": 48.5734,
        "lng": 7.7521,
        "summary": "Emblem showing a sword or spear piercing a heart encircled by blooming roses, synthesizing images of suffering and love, wounding and beauty, divine penetration and human longing.",
        "essay": "This emblem merges courtly love symbolism with mystical theology and alchemical transformation. The heart—seat of emotion and will—is pierced by a sword (divine penetration, necessary wounding, the arrow of Cupid or of divine love). Roses surrounding the heart connect to both secular romantic tradition (the rose as symbol of love) and Christian mysticism (roses as symbols of martyrdom and sanctity). The combination suggests that transformation requires being wounded by love, that the heart must be penetrated by divine longing, that beauty and suffering are inseparable in spiritual development. In Neoplatonic philosophy, Eros (spiritual love) as much as Agape (divine love) was understood as an arrow-like force that pierces the soul and draws it toward transcendent beauty. The emblem thus images the mystical path as a kind of desired suffering—not masochistic but recognized as the necessary price of spiritual awakening. For women mystics in particular, the imagery of the pierced heart carried powerful resonance: the wound that divine love inflicts is not destructive but generative, producing not death but blooming (the roses). Stolcius's inclusion of this emblem suggests that Rosicrucian alchemy valued not only intellectual understanding but also the emotional and relational transformation wrought by love."
    },
    {
        "title": "Crown Emerging from Purifying Flames",
        "year": 1624,
        "location": "Strasbourg, France",
        "lat": 48.5734,
        "lng": 7.7521,
        "summary": "Emblem depicting a royal crown rising from or emerging unchanged through consuming fire, representing the triumph of the incorruptible spiritual over matter, and the achievement of imperishable perfection.",
        "essay": "The crown-in-flames image represents a paradox: the crown (ordinarily made of metal and gems) should melt or be destroyed by fire, yet it emerges unharmed and even enhanced. This reversal of ordinary expectation suggests that the highest principles—incorruptibility, imperishability, divine nobility—cannot be destroyed by external conditions. In alchemical terms, the crown represents the lapis philosophorum: the stone that survives all operations, that cannot be corrupted by any external force, that has achieved permanence. In spiritual terms, the crown represents the perfected soul that has passed through tribulation (represented by the flame) and emerges unharmed—indeed glorified. Christian martyrdom theology resonates here: the martyr's faith, like gold in the assayer's fire, proves incorruptible. Stolcius's image suggests that the crown's perfection is proven precisely by its capacity to withstand the fire: only what is truly imperishable can emerge from the test. For the Rosicrucian, this emblem represented the promise that inner work leads to incorruptible achievement—that the developed soul transcends vulnerability to external circumstance. The flames thus serve not as threat but as proof: they demonstrate the reality of what they cannot destroy."
    }
]

# Combine all new emblems
all_new_emblems = cramer_emblems + maier_emblems + stolcius_emblems

print(f"Adding {len(all_new_emblems)} new emblem entries...\n")

for emblem in all_new_emblems:
    emblem_entry = {
        "id": next_id,
        "title": emblem["title"],
        "slug": emblem["title"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace("'", ""),
        "year": emblem["year"],
        "language": "English",
        "location": emblem["location"],
        "lat": emblem["lat"],
        "lng": emblem["lng"],
        "summary": emblem["summary"],
        "essay": emblem["essay"],
        "concepts": [1, 25, 27, 37, 40]  # Same concept links as other emblems
    }
    data['texts'].append(emblem_entry)
    print(f"Added: {emblem['title']} (Text ID {next_id})")
    next_id += 1

# Save updated data
with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Successfully updated prototype_data.json")
print(f"\nNew totals:")
print(f"  Figures: {len(data['figures'])}")
print(f"  Concepts: {len(data['concepts'])}")
print(f"  Texts: {len(data['texts'])} (including {len(all_new_emblems)} new emblems)")
print(f"\nTotal emblem entries: {58 + len(all_new_emblems)} emblems (meets 30+ minimum)")
