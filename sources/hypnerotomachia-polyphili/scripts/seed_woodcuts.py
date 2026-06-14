"""Seed the woodcuts table with 18 woodcuts detected from BL photograph reading.

Creates the woodcuts table and populates it from verified image observations.
All data sourced from direct reading of BL C.60.o.12 photographs.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "hp.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS woodcuts (
    id INTEGER PRIMARY KEY,
    woodcut_number INTEGER,
    slug TEXT UNIQUE,
    title TEXT NOT NULL,
    signature_1499 TEXT,
    page_1499 INTEGER,
    signature_1545 TEXT,
    page_1545 INTEGER,
    chapter_context TEXT,
    description TEXT,
    subject_category TEXT,
    depicted_elements TEXT,
    woodcut_type TEXT,
    signed TEXT,
    attributed_to TEXT,
    scholarly_discussion TEXT,
    influence TEXT,
    has_bl_photo BOOLEAN DEFAULT 0,
    bl_photo_number INTEGER,
    has_siena_photo BOOLEAN DEFAULT 0,
    has_annotation BOOLEAN DEFAULT 0,
    alchemical_annotation BOOLEAN DEFAULT 0,
    annotation_density TEXT,
    dictionary_terms TEXT,
    review_status TEXT DEFAULT 'DRAFT',
    source_method TEXT DEFAULT 'CORPUS_EXTRACTION',
    source_basis TEXT,
    confidence TEXT DEFAULT 'MEDIUM',
    notes TEXT
);
"""

WOODCUTS = [
    {
        "slug": "dark-forest",
        "title": "The Dark Forest (Selva Oscura)",
        "signature_1499": "a2v", "page_1499": 4,
        "bl_photo_number": 17,
        "subject_category": "LANDSCAPE",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "dense woodland, trees, dark canopy",
        "chapter_context": "Poliphilo's dream begins in a dark forest, echoing Dante's Commedia. He is lost and afraid. This woodcut establishes the visual register for the entire journey: detailed natural scenery rendered in precise line work.",
        "description": "A dense woodland scene showing tall trees with intertwining branches and thick foliage. The composition creates a sense of enclosure and disorientation. The woodcut introduces the HP's characteristic style: architectural precision applied to natural forms.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "dark-forest,dream-narrative,dream-within-dream",
        "scholarly_discussion": "Priki (2016) reads the dark forest as a structural device common to dream narratives. The Dantean echo is noted by most scholars.",
        "source_basis": "BL photo 017 direct observation; Priki 2016; Godwin 1999",
    },
    {
        "slug": "poliphilo-reclining",
        "title": "Poliphilo in the Landscape",
        "signature_1499": "a4v", "page_1499": 8,
        "bl_photo_number": 21,
        "subject_category": "NARRATIVE",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "reclining figure, landscape, trees, rocks",
        "chapter_context": "After emerging from the dark forest, Poliphilo rests in an open landscape. The transition from enclosed forest to open terrain marks the beginning of his architectural and erotic education.",
        "description": "A figure reclines or lies in an open landscape with trees and rocky terrain. The composition shifts from the claustrophobic forest to a more expansive view, signaling narrative progress.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "source_basis": "BL photo 021 direct observation",
    },
    {
        "slug": "dream-within-dream",
        "title": "Poliphilo Sleeping (Dream within a Dream)",
        "signature_1499": "a5v", "page_1499": 10,
        "bl_photo_number": 23,
        "subject_category": "NARRATIVE",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "sleeping figure, landscape, trees",
        "chapter_context": "At a5v, Poliphilo falls asleep within his own dream, creating the double dream structure that defines the HP's narrative. The inner dream contains the main journey.",
        "description": "Poliphilo sleeps in a landscape setting, entering the dream-within-a-dream that contains the HP's principal narrative. The woodcut visually marks this crucial structural transition.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "dream-within-dream,dream-narrative,dream-vision",
        "scholarly_discussion": "Priki (2016) reads the double dream as adapting the Roman de la Rose model. Gollnick (1999) provides theoretical framework for dream-narrative initiation.",
        "source_basis": "BL photo 023 direct observation; Priki 2016",
    },
    {
        "slug": "poliphilo-garden-palms",
        "title": "Poliphilo in a Garden with Palms",
        "signature_1499": "a6r", "page_1499": 11,
        "bl_photo_number": 24,
        "subject_category": "LANDSCAPE",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "figure, palm trees, well or fountain, garden",
        "chapter_context": "Poliphilo encounters a garden setting with palm trees and what appears to be a well or fountain. This marks the beginning of the HP's sustained garden descriptions.",
        "description": "A figure stands in a garden with palm trees and a circular well or fountain structure. The garden setting introduces the botanical precision that characterizes the HP's landscape descriptions.",
        "has_annotation": True, "annotation_density": "HEAVY",
        "dictionary_terms": "water-garden,fountain",
        "source_basis": "BL photo 024 direct observation",
    },
    {
        "slug": "horse-sarcophagus",
        "title": "Horse and Rider on a Sarcophagus",
        "signature_1499": "b3v", "page_1499": 22,
        "bl_photo_number": 35,
        "subject_category": "ARCHITECTURAL",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "horse, rider or figure, sarcophagus, pedestal",
        "chapter_context": "Poliphilo encounters classical monuments during his exploration of the ruined architectural complex. This sarcophagus relief depicts a horse and figure in the classical manner.",
        "description": "A horse bearing a figure stands on a sarcophagus or raised pedestal. The composition reflects classical funerary relief sculpture, consistent with the HP's antiquarian program.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "ruined-temple,antiquarianism",
        "source_basis": "BL photo 035 direct observation",
    },
    {
        "slug": "twin-monuments-ambig",
        "title": "Twin Inscribed Monuments (D.AMBIG.D.D.)",
        "signature_1499": "b4r", "page_1499": 23,
        "bl_photo_number": 36,
        "subject_category": "HIEROGLYPHIC",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "two monument bases, inscriptions, decorative frames, wreaths",
        "chapter_context": "Poliphilo encounters paired inscribed monuments. The inscription D.AMBIG.D.D. is read by the Buffalo alchemist (Hand E) as referring to 'ambiguous gods' — metallic hermaphrodites produced by the chemical wedding.",
        "description": "Two paired rectangular monument bases, each bearing inscriptions within decorative wreaths or circular frames. The left monument is partially damaged. Both sit on classical pedestal bases.",
        "has_annotation": True, "annotation_density": "HEAVY",
        "alchemical_annotation": True,
        "dictionary_terms": "chemical-wedding,hermaphrodite,in-text-inscription",
        "scholarly_discussion": "Russell (2014, pp. 189-190) documents how Buffalo Hand E reads D.AMBIG.D.D. as encoding the alchemical hermaphrodite principle.",
        "source_basis": "BL photo 036 direct observation; Russell 2014",
    },
    {
        "slug": "gonos-kai-etousia",
        "title": "Inscription Monument (GONOS KAI ETOUSIA)",
        "signature_1499": "b6r", "page_1499": 27,
        "bl_photo_number": 40,
        "subject_category": "HIEROGLYPHIC",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "rectangular monument, Greek inscription, decorative frame",
        "chapter_context": "A monument bearing a Greek inscription that Poliphilo reads and interprets. The inscription relates to generation and yearly cycles.",
        "description": "A rectangular inscribed monument with a Greek text reading GONOS KAI ETOUSIA within a decorative architectural frame. The monument exemplifies the HP's characteristic fusion of pseudo-classical epigraphy and visual design.",
        "has_annotation": True, "annotation_density": "HEAVY",
        "dictionary_terms": "in-text-inscription,hieroglyph,antiquarianism",
        "source_basis": "BL photo 040 direct observation",
    },
    {
        "slug": "elephant-obelisk",
        "title": "The Elephant and Obelisk",
        "signature_1499": "b6v", "page_1499": 28,
        "bl_photo_number": 41,
        "subject_category": "HIEROGLYPHIC",
        "woodcut_type": "FULL_PAGE",
        "depicted_elements": "elephant, obelisk, hieroglyphs, circular base, pedestal",
        "chapter_context": "The most famous woodcut in the HP. An elephant bears an obelisk decorated with pseudo-hieroglyphic carvings on a circular base. This image directly influenced Bernini's 1667 sculpture in Piazza della Minerva, commissioned by Pope Alexander VII.",
        "description": "An elephant stands on a circular plinth bearing a tall obelisk decorated with pseudo-Egyptian hieroglyphic carvings and ornamental motifs. The obelisk is topped with a sphere. The composition combines Egyptian and classical elements in the HP's characteristic mode of syncretic antiquarianism. In the BL copy, Hand B (the alchemist) densely annotated this woodcut with alchemical ideograms, reading the elephant-obelisk as encoding alchemical processes.",
        "has_annotation": True, "annotation_density": "HEAVY",
        "alchemical_annotation": True,
        "dictionary_terms": "elephant-obelisk,obelisk,hieroglyph,ideogram,alchemical-allegory",
        "scholarly_discussion": "Heckscher (1947) documented how Bernini drew on this woodcut for his 1667 Piazza della Minerva sculpture. Russell (2014, pp. 156-157) analyzes Hand B's alchemical ideograms on this page. Curran (1998) situates it within Renaissance Egyptology.",
        "influence": "Bernini's Elephant and Obelisk (1667), Piazza della Minerva, Rome. Commissioned by Alexander VII, who annotated his own HP copy.",
        "source_basis": "BL photo 041 direct observation; Heckscher 1947; Russell 2014; Curran 1998",
        "confidence": "HIGH",
    },
    {
        "slug": "figure-monument-greek",
        "title": "Figure on Monument with Greek Inscription",
        "signature_1499": "b7r", "page_1499": 29,
        "bl_photo_number": 42,
        "subject_category": "HIEROGLYPHIC",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "standing figure, pedestal, Greek inscription, monument",
        "chapter_context": "Poliphilo encounters another inscribed monument, this one bearing a figure and a Greek text. The page is heavily annotated in the BL copy.",
        "description": "A figure stands on a monument or pedestal base bearing a Greek inscription. Below the main figure is a smaller inscription panel. The composition combines figurative sculpture with epigraphic elements.",
        "has_annotation": True, "annotation_density": "HEAVY",
        "dictionary_terms": "in-text-inscription,hieroglyph",
        "source_basis": "BL photo 042 direct observation",
    },
    {
        "slug": "poliphilo-dragon-portal",
        "title": "Poliphilo at a Portal with a Dragon",
        "signature_1499": "d2v", "page_1499": 52,
        "bl_photo_number": 65,
        "subject_category": "NARRATIVE",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "figure, dragon or beast, portal, columns, architectural frame",
        "chapter_context": "Poliphilo confronts a dragon or monstrous beast at an architectural portal. This scene represents one of the HP's threshold encounters where the protagonist must overcome fear to proceed.",
        "description": "Poliphilo faces a dragon or beast at the entrance to an architectural structure with classical columns. The portal frames the encounter, making architecture itself a participant in the narrative drama.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "portal,meraviglia",
        "source_basis": "BL photo 065 direct observation",
    },
    {
        "slug": "grotesque-frieze",
        "title": "Grotesque Frieze with Hybrid Figures",
        "signature_1499": "f4r", "page_1499": 87,
        "bl_photo_number": 100,
        "subject_category": "DECORATIVE",
        "woodcut_type": "FRIEZE",
        "depicted_elements": "hybrid figures, acanthus scrolls, animal forms, decorative band",
        "chapter_context": "A horizontal decorative band featuring grotesque ornament — hybrid creatures combining human, animal, and vegetal forms. This style was rediscovered in the grottoes of Nero's Domus Aurea around 1480.",
        "description": "A horizontal frieze band showing intertwined human and animal figures emerging from acanthus scrollwork. The grotesque style combines classical ornamental vocabulary with fantastical hybrid invention.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "grotesque",
        "scholarly_discussion": "Dacos (1969) provides the standard account of grotesque ornament's Renaissance revival. The HP is among the earliest printed works to depict this style.",
        "source_basis": "BL photo 100 direct observation; Dacos 1969",
    },
    {
        "slug": "circular-medallion-deity",
        "title": "Circular Medallion with Deity Figure",
        "signature_1499": "f6v", "page_1499": 92,
        "bl_photo_number": 105,
        "subject_category": "PORTRAIT",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "circular medallion, bust or deity figure, ornamental frame",
        "chapter_context": "A medallion portrait of a deity figure within a circular frame. The page is extremely heavily annotated on all margins, with possible alchemical marks.",
        "description": "A circular medallion containing a bust or deity figure, framed by ornamental borders. The circular format echoes classical coin and gem designs, consistent with the HP's antiquarian visual vocabulary.",
        "has_annotation": True, "annotation_density": "HEAVY",
        "alchemical_annotation": True,
        "notes": "Possible zodiac/planetary marks in margins. Needs further verification.",
        "source_basis": "BL photo 105 direct observation",
    },
    {
        "slug": "candelabrum-fountain",
        "title": "Ornate Candelabrum or Fountain Structure",
        "signature_1499": "g3v", "page_1499": 102,
        "bl_photo_number": 115,
        "subject_category": "ARCHITECTURAL",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "candelabrum, decorative structure, botanical elements, base",
        "chapter_context": "An elaborate decorative structure combining architectural and botanical forms. Annotations identify it with 'Fontana' (fountain) and reference 'Berillus' (beryl) and 'Dioscurius.'",
        "description": "A tall ornate structure resembling a candelabrum or fountain, with decorative tiers incorporating botanical elements (leaves, flowers) and architectural moldings. It sits on a broad base.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "fountain",
        "source_basis": "BL photo 115 direct observation",
    },
    {
        "slug": "medallion-cameo",
        "title": "Circular Medallion or Cameo",
        "signature_1499": "h5v", "page_1499": 122,
        "bl_photo_number": 135,
        "subject_category": "PORTRAIT",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "circular medallion, figure, ornamental border",
        "chapter_context": "Another circular portrait medallion. The page is heavily annotated, with 'Jupiter' visible in the marginal text, connecting to the planetary hierarchy.",
        "description": "A circular medallion containing a figure, set within the text flow. Annotations reference Jupiter, suggesting this image was read within the planetary-metal correspondence framework.",
        "has_annotation": True, "annotation_density": "HEAVY",
        "dictionary_terms": "column-orders",
        "source_basis": "BL photo 135 direct observation",
    },
    {
        "slug": "figures-at-portal",
        "title": "Figures at a Portal or Doorway",
        "signature_1499": "h8r", "page_1499": 127,
        "bl_photo_number": 140,
        "subject_category": "NARRATIVE",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "figures, portal, doorway, architectural setting",
        "chapter_context": "A scene at an architectural portal. Above the woodcut, a hand has written 'Synostra Gloria mundi' — a possible alchemical annotation, since 'Gloria mundi' is standard alchemical phraseology.",
        "description": "Multiple figures at an architectural portal or doorway, in a scene that may depict a greeting, a departure, or a ceremonial encounter. The composition uses the portal as a framing device.",
        "has_annotation": True, "annotation_density": "HEAVY",
        "alchemical_annotation": True,
        "dictionary_terms": "portal,great-work",
        "notes": "Handwritten 'Synostra Gloria mundi' above woodcut. PROVISIONAL alchemical attribution.",
        "source_basis": "BL photo 140 direct observation",
    },
    {
        "slug": "garden-pergola-nymph",
        "title": "Garden Scene with Pergola and Nymph",
        "signature_1499": "i2v", "page_1499": 132,
        "bl_photo_number": 145,
        "subject_category": "LANDSCAPE",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "garden, pergola, architectural gateway, nymph figure, vegetation",
        "chapter_context": "A garden scene showing an architectural pergola or gateway structure with a nymph figure amid lush vegetation. This belongs to the HP's extended garden descriptions.",
        "description": "An architectural gateway or pergola structure surrounded by vegetation, with figures approaching or present within the garden setting. The composition integrates built and natural forms in the HP's characteristic garden mode.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "pergola,nymphs-five-senses,circular-garden",
        "source_basis": "BL photo 145 direct observation",
    },
    {
        "slug": "triumphal-procession-soldiers",
        "title": "Triumphal Procession with Soldiers",
        "signature_1499": "k5r", "page_1499": 157,
        "bl_photo_number": 170,
        "subject_category": "PROCESSION",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "soldiers, standards, flags, musicians, processional figures",
        "chapter_context": "One of the HP's triumphal procession woodcuts, showing a procession of soldiers bearing standards, musicians, and other participants. The heading 'SECVNDVS' appears above.",
        "description": "A procession of soldiers and musicians bearing standards and flags, depicted in a dense figural composition. The procession moves across the page in the HP's characteristic frieze-like arrangement.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "triumphal-procession",
        "scholarly_discussion": "The triumph woodcuts connect the HP to Renaissance festival culture and the classical literary tradition of the triumphus.",
        "source_basis": "BL photo 170 direct observation",
    },
    {
        "slug": "triumph-pars-antiqua",
        "title": "Triumph Scene (PARS ANTIQVA ET POSTERIOR)",
        "signature_1499": "k7v", "page_1499": 162,
        "bl_photo_number": 175,
        "subject_category": "PROCESSION",
        "woodcut_type": "IN_TEXT",
        "depicted_elements": "triumph scene, central figure, attendants, inscription",
        "chapter_context": "A triumph scene with a central standing figure, part of the HP's extended procession sequence. The heading PARS ANTIQVA ET POSTERIOR and the inscription TEPEFA SCINTILLAM QVI CAELVM ACCENDIT ET ORBEM appear.",
        "description": "A triumphal scene with a central elevated figure surrounded by attendants. An inscription above reads TEPEFA SCINTILLAM QVI CAELVM ACCENDIT ET ORBEM ('the spark that kindled heaven and earth'). The composition combines processional narrative with epigraphic elements.",
        "has_annotation": True, "annotation_density": "MODERATE",
        "dictionary_terms": "triumphal-procession,in-text-inscription",
        "source_basis": "BL photo 175 direct observation",
    },
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Creating woodcuts table...")
    cur.executescript(SCHEMA)

    print("Seeding 18 detected woodcuts...")
    inserted = 0
    for w in WOODCUTS:
        cur.execute("""
            INSERT OR IGNORE INTO woodcuts
                (slug, title, signature_1499, page_1499, bl_photo_number,
                 subject_category, woodcut_type, depicted_elements,
                 chapter_context, description, has_bl_photo,
                 has_annotation, alchemical_annotation, annotation_density,
                 dictionary_terms, scholarly_discussion, influence,
                 source_basis, confidence, notes,
                 review_status, source_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'DRAFT', 'CORPUS_EXTRACTION')
        """, (w["slug"], w["title"], w.get("signature_1499"), w.get("page_1499"),
              w.get("bl_photo_number"), w.get("subject_category"), w.get("woodcut_type"),
              w.get("depicted_elements"), w.get("chapter_context"), w.get("description"),
              w.get("has_annotation", False), w.get("alchemical_annotation", False),
              w.get("annotation_density"), w.get("dictionary_terms"),
              w.get("scholarly_discussion"), w.get("influence"),
              w.get("source_basis"), w.get("confidence", "MEDIUM"), w.get("notes")))
        inserted += cur.rowcount

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM woodcuts")
    total = cur.fetchone()[0]
    cur.execute("SELECT subject_category, COUNT(*) FROM woodcuts GROUP BY subject_category ORDER BY COUNT(*) DESC")
    print(f"\n{total} woodcuts seeded:")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
