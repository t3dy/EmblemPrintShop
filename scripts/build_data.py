"""
build_data.py — Build normalized data layer for EmblemPrintShop.

Outputs to data/:
  works.json
  emblems.json
  motifs.json
  visual_elements.json

Run from project root:
  python scripts/build_data.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_OUT = ROOT / "data"
SOURCES = ROOT / "sources"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path, encoding="utf-8"):
    with open(path, encoding=encoding) as f:
        return json.load(f)

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    print(f"  wrote {path.relative_to(ROOT)}  ({len(obj)} items)")


# ---------------------------------------------------------------------------
# WORKS
# ---------------------------------------------------------------------------

WORKS = [
    {
        "id": "atalanta_fugiens",
        "short_id": "AF",
        "title": "Atalanta Fugiens",
        "author": "Michael Maier",
        "date": 1618,
        "publisher": "Johann Theodor de Bry",
        "place": "Oppenheim",
        "language": "Latin",
        "description": (
            "Maier's polymodal emblem book: 50 emblems plus a frontispiece, "
            "each combining an engraved plate, a Latin epigram, and a polyphonic fugue. "
            "The sequence encodes the alchemical opus from prima materia to the Philosopher's Stone."
        ),
        "tradition": "alchemical_emblem",
        "rights_note": "Public domain. Images from furnaceandfugue.org and Science History Institute.",
        "source_project": "claudiens",
        "local_image_dir": "sources/claudiens/site/images/emblems",
        "provenance_url": "https://furnaceandfugue.org/atalanta-fugiens/",
    },
    {
        "id": "hypnerotomachia_poliphili",
        "short_id": "HP",
        "title": "Hypnerotomachia Poliphili",
        "author": "Francesco Colonna",
        "date": 1499,
        "publisher": "Aldus Manutius",
        "place": "Venice",
        "language": "Vernacular Italian / Latin / Greek",
        "description": (
            "Aldine first edition. One of the most lavishly illustrated incunabula, "
            "containing ~172 woodcut illustrations. Classified here as alchemical reception "
            "context: the book encodes Neoplatonic, Hermetic, and architectural themes that "
            "overlap significantly with contemporary alchemical emblem traditions."
        ),
        "tradition": "alchemical_reception",
        "rights_note": "Public domain. Images from Internet Archive (1499 Aldine edition).",
        "source_project": "hypnerotomachia-polyphili",
        "local_image_dir": "sources/hypnerotomachia-polyphili/site/images/woodcuts_1499",
        "provenance_url": "https://archive.org/details/hypnerotomachiap00colo",
    },
]


# ---------------------------------------------------------------------------
# MOTIFS
# ---------------------------------------------------------------------------

MOTIFS = [
    {
        "id": "dragon",
        "label": "Dragon / Serpent",
        "variants": ["dragon", "serpent", "ouroboros", "worm", "basilisk"],
        "description": (
            "Winged or wingless reptilian creature; the volatile mercury, the prima materia "
            "before fixation, or the guardian of the threshold. The ouroboros (self-devouring serpent) "
            "is a specialised form."
        ),
        "alchemical_valence": ["mercury", "volatility", "prima_materia", "nigredo"],
        "planetary": "Mercury / Saturn",
    },
    {
        "id": "lion",
        "label": "Lion",
        "variants": ["lion", "green lion", "red lion"],
        "description": (
            "The green lion (vitriol) devours the sun (gold); the red lion is the perfected sulphur. "
            "Lions also appear as royal, solar beasts in heraldic and triumphalist contexts."
        ),
        "alchemical_valence": ["sulphur", "fixation", "sol", "dissolution"],
        "planetary": "Sol / Mars",
    },
    {
        "id": "hermaphrodite",
        "label": "Hermaphrodite / Androgyne / Rebis",
        "variants": ["hermaphrodite", "androgyne", "rebis", "hermaphroditus", "two-natured figure"],
        "description": (
            "The coniunctio made visible: a single body bearing the attributes of sun and moon, "
            "king and queen, red and white. The Rebis is the completed Stone."
        ),
        "alchemical_valence": ["coniunctio", "rubedo", "completion", "philosophical_stone"],
        "planetary": "Sol + Luna",
    },
    {
        "id": "king",
        "label": "King / Sol",
        "variants": ["king", "crowned king", "rex", "solar king"],
        "description": (
            "The solar, sulphurous, masculine principle. The king must die (mortificatio) and "
            "be resurrected, his body becoming the red tincture."
        ),
        "alchemical_valence": ["sol", "sulphur", "mortificatio", "rubedo"],
        "planetary": "Sol",
    },
    {
        "id": "queen",
        "label": "Queen / Luna",
        "variants": ["queen", "crowned queen", "regina", "lunar queen"],
        "description": (
            "The lunar, mercurial, feminine principle. As bride she receives the king's death; "
            "as resurrected queen she embodies the albedo and the white tincture."
        ),
        "alchemical_valence": ["luna", "mercury", "albedo", "white_tincture"],
        "planetary": "Luna",
    },
    {
        "id": "sun",
        "label": "Sun / Sol (disc or personified)",
        "variants": ["sun", "solar disc", "sol", "Helios", "Apollo"],
        "description": (
            "The solar disc, radiate crown, or personified Sol. Governs gold, fire, and the "
            "masculine principle throughout the alchemical tradition."
        ),
        "alchemical_valence": ["sol", "gold", "fire", "sulphur"],
        "planetary": "Sol",
    },
    {
        "id": "moon",
        "label": "Moon / Luna (crescent or personified)",
        "variants": ["moon", "crescent", "luna", "lunar crescent", "Diana"],
        "description": (
            "The lunar crescent or personified Luna. Governs silver, water, and the feminine principle."
        ),
        "alchemical_valence": ["luna", "silver", "water", "mercury"],
        "planetary": "Luna",
    },
    {
        "id": "vessel",
        "label": "Vessel / Philosophical Egg / Vase",
        "variants": ["vessel", "flask", "athanor", "alembic", "retort", "philosophical egg",
                     "vase", "amphora", "urn", "pot"],
        "description": (
            "The sealed container in which the Work proceeds: glass flask, clay vessel, "
            "philosophical egg (ovum philosophicum), alembic, or retort. "
            "The vessel is the microcosmic world in which the opus is performed."
        ),
        "alchemical_valence": ["opus", "containment", "philosophical_egg", "vessel"],
        "planetary": None,
    },
    {
        "id": "furnace",
        "label": "Furnace / Athanor / Fire",
        "variants": ["furnace", "athanor", "fire", "flames", "hearth"],
        "description": (
            "The source of alchemical heat: athanor, open furnace, or allegorical fire. "
            "Governs the timing of every stage; too much fire destroys the work."
        ),
        "alchemical_valence": ["fire", "calcinatio", "heat", "operation"],
        "planetary": "Mars / Sol",
    },
    {
        "id": "tree",
        "label": "Tree / Arbor Philosophica",
        "variants": ["tree", "arbor philosophica", "rose tree", "tree of knowledge"],
        "description": (
            "The philosophical tree (arbor philosophica) grows from the putrefied seed of the Stone. "
            "Bears sun and moon as fruit; may be a rose tree (Rosarium) or a golden tree (Aureum Vellus)."
        ),
        "alchemical_valence": ["growth", "maturation", "arbor_philosophica", "coniunctio"],
        "planetary": "Sol + Luna",
    },
    {
        "id": "bird",
        "label": "Bird / Phoenix / Eagle / Dove",
        "variants": ["bird", "phoenix", "eagle", "dove", "pelican", "raven", "white swan",
                     "black crow", "cauda_pavonis", "peacock"],
        "description": (
            "Alchemical birds mark the volatile principle and the stages of the Work: "
            "the black crow (nigredo), white swan (albedo), peacock tail (cauda pavonis, citrinitas), "
            "and phoenix or eagle (rubedo, sublimation)."
        ),
        "alchemical_valence": ["sublimation", "volatility", "stages", "spirit"],
        "planetary": "Mercury / Sol",
    },
    {
        "id": "serpent",
        "label": "Serpent (non-dragon)",
        "variants": ["serpent", "snake", "caduceus serpent", "Aesculapian snake"],
        "description": (
            "Distinguished from the winged dragon: the serpent without wings is the fixed mercury "
            "or the Hermetic caduceus. The bitten serpent (Nehushtan) represents the purified poison."
        ),
        "alchemical_valence": ["mercury", "fixation", "caduceus", "poison"],
        "planetary": "Mercury",
    },
    {
        "id": "mountain",
        "label": "Mountain / Cave / Grotto",
        "variants": ["mountain", "cave", "grotto", "rocky ground", "hill"],
        "description": (
            "The mountain is both prima materia (the raw earth) and the destination of VITRIOL: "
            "Visita Interiora Terrae Rectificando Invenies Occultum Lapidem. "
            "Grottos are thresholds between surface and interior work."
        ),
        "alchemical_valence": ["prima_materia", "earth", "descent", "vitriol"],
        "planetary": "Saturn",
    },
    {
        "id": "fountain",
        "label": "Fountain / Spring / Water",
        "variants": ["fountain", "spring", "stream", "water", "bath", "bain-marie"],
        "description": (
            "The mercurial fountain, the philosophical water, the bath of purification. "
            "The mercurial spring dissolves and purifies; the bain-marie (Maria's bath) gently heats."
        ),
        "alchemical_valence": ["mercury", "dissolution", "purification", "albedo"],
        "planetary": "Luna / Mercury",
    },
    {
        "id": "star",
        "label": "Star / Celestial Body",
        "variants": ["star", "stars", "celestial sphere", "zodiac", "planets"],
        "description": (
            "Celestial bodies govern alchemical timing and correspondence. Stars, planetary symbols, "
            "and zodiacal figures mark the macrocosmic scaffold that the Work mirrors below."
        ),
        "alchemical_valence": ["correspondence", "timing", "macrocosm", "celestial"],
        "planetary": "All",
    },
]


# ---------------------------------------------------------------------------
# EMBLEMS — Maier (Atalanta Fugiens)
# ---------------------------------------------------------------------------

def build_maier_emblems():
    manifest = load_json(SOURCES / "claudiens/data/emblem_manifest.json")
    site_data_raw = load_json(SOURCES / "claudiens/site/data.json")
    # site data.json entries may be nested lists
    site_entries_raw = site_data_raw.get("entries", [])
    site_flat = []
    for item in site_entries_raw:
        if isinstance(item, list):
            site_flat.extend(item)
        else:
            site_flat.append(item)
    site_by_num = {e["number"]: e for e in site_flat}

    theos_raw = load_json(
        SOURCES / "theosophical-alchemy-db/data/maier_atalanta_fugiens_emblems_metadata.json"
    )
    theos_by_num = {e["emblem_number"]: e for e in theos_raw["emblems"]}

    identity_seed = load_json(SOURCES / "claudiens/data/emblem_identity_seed.json")
    identity_by_num = {e["emblem_number"]: e for e in identity_seed}

    emblems = []
    for m in manifest:
        n = m["number"]
        site = site_by_num.get(n, {})
        theos = theos_by_num.get(n, {})
        ident = identity_by_num.get(n, {})

        image_path = f"sources/claudiens/site/images/emblems/{m['image_file']}"

        # Motif candidates: merge visual_elements from theosophical metadata
        motif_candidates = []
        if theos.get("visual_elements"):
            motif_candidates = [v.lower() for v in theos["visual_elements"]]

        emblem = {
            "id": f"AF_{n:02d}",
            "work_id": "atalanta_fugiens",
            "number": n,
            "roman": m.get("roman"),
            "label": m.get("label"),
            "latin_motto": m.get("latin_motto"),
            "english_motto": (m.get("english_motto") or "").strip() or None,
            "image_path": image_path,
            "image_source": m.get("image_source"),
            "furnace_fugue_url": m.get("furnace_fugue_url"),
            "furnace_fugue_image_url": m.get("furnace_fugue_image_url"),
            "provenance_url": ident.get("image_url"),
            "image_confidence": ident.get("alignment_confidence", "HIGH"),
            # Enriched from theosophical-alchemy-db (emblems 1–20)
            "alchemical_stage": theos.get("alchemical_stage"),
            "color_association": theos.get("color_association"),
            "planetary_association": theos.get("planetary_association"),
            "key_concepts": theos.get("key_concepts", []),
            "related_emblems": [f"AF_{r:02d}" for r in theos.get("related_emblems", [])],
            "de_jong_pages": theos.get("de_jong_pages"),
            # From claudiens site data
            "discourse_excerpt": (site.get("discourse") or "")[:400] or None,
            "stage": site.get("stage"),
            "confidence": site.get("confidence"),
            # Motif candidates
            "motif_candidates": motif_candidates,
            "review_status": "stub",
        }
        emblems.append(emblem)

    return emblems


# ---------------------------------------------------------------------------
# EMBLEMS — Hypnerotomachia woodcuts
# ---------------------------------------------------------------------------

# Inline the complete 1499 woodcut inventory extracted from seed_1499_woodcuts.py
WOODCUTS_1499 = [
    (4, "a2v", "Poliphilo in the Dark Forest", "Poliphilo wanders among tall trees in a dense forest. Small figure at center surrounded by towering trunks with detailed foliage.", "The opening scene of the HP. Poliphilo, having fallen asleep weeping for his beloved Polia, finds himself lost in a dark and terrifying forest — echoing Dante's selva oscura. This is the threshold between waking and dreaming.", "LANDSCAPE"),
    (8, "a4v", "Poliphilo at the Landscape with River", "Poliphilo rests in an open landscape with trees and a stream. Pastoral scene with classical elements.", "Having escaped the dark forest, Poliphilo enters a beautiful open landscape. He drinks from a stream and rests, transitioning from terror to wonder. The landscape represents the first stage of his allegorical journey.", "LANDSCAPE"),
    (10, "a5v", "Poliphilo Sleeping (Dream within Dream)", "Poliphilo lies sleeping on the ground in a wooded landscape. A second dream begins within the first.", "Poliphilo falls asleep again within his dream, initiating the dream-within-a-dream structure that is the HP's most distinctive narrative device. This second sleep takes him deeper into the allegorical realm.", "NARRATIVE"),
    (11, "a6r", "Poliphilo in a Garden with Palms", "Poliphilo stands in a garden setting with palm trees and classical vegetation.", "Poliphilo awakens in a beautiful garden with exotic plants. The palms and ordered vegetation signal his entry into a civilized, designed landscape — architecture replacing wilderness.", "LANDSCAPE"),
    (16, "b2v", "The Great Pyramid", "Full-page woodcut of a massive stepped pyramid topped by a tall obelisk surmounted by a figure. Colonnaded portico at the base. Inscription KITOMARNO visible.", "The centerpiece of Poliphilo's first architectural encounter. This impossible pyramid exceeds the Egyptian originals in Colonna's description — its dimensions are meticulously specified and internally consistent, demonstrating the author's architectural learning.", "ARCHITECTURAL"),
    (22, "b5r", "The Ruined Colossal Horse", "Fragments of a colossal bronze horse lying among ruins. One of the HP's most evocative images of ancient grandeur brought low.", "Poliphilo discovers the ruins of an immense bronze horse — a symbol of imperial ambition and the transience of human achievement.", "ARCHITECTURAL"),
    (23, "b5v", "Twin Inscribed Monuments (D.AMBIG.D.D.)", "Two rectangular stone pedestals with circular wreath inscriptions. Enigmatic Latin abbreviated text within each wreath.", "Poliphilo encounters paired funerary monuments with cryptic inscriptions. The enigmatic abbreviations have generated centuries of scholarly debate.", "HIEROGLYPHIC"),
    (24, "b6r", "Figures with TEMPVS", "Group of classical figures, one labeled TEMPVS (Time). Allegorical scene with personified abstractions.", "An allegorical group representing Time and associated concepts.", "NARRATIVE"),
    (25, "b6r", "Classical Figures in a Garden", "Group of figures in classical dress gathered in a garden or outdoor scene.", "Poliphilo encounters allegorical figures in an idealized setting.", "NARRATIVE"),
    (27, "b6v", "Inscription Monument (ΓΟΝΟΣ ΚΑΙ ΕΤΟΥΣΙΑ)", "Stone stele with Greek and pseudo-Arabic inscriptions in an arched niche.", "A multilingual monument displaying Greek, Arabic, and Hebrew-like characters. The inscription 'Offspring and Abundance' connects to fertility and generative power.", "HIEROGLYPHIC"),
    (28, "b6v", "The Elephant and Obelisk", "An elephant bearing an obelisk on a circular stepped pedestal. The obelisk is topped with a sphere and decorated with pseudo-hieroglyphic panels.", "The most famous image in the HP. This combination directly inspired Bernini's 1667 sculpture in Piazza della Minerva, Rome. Union of strength (elephant) and wisdom (obelisk).", "ARCHITECTURAL"),
    (29, "b7r", "Figure on Monument with Greek Inscription", "Standing figure atop a pedestal with Greek text. Classical architectural framing.", "A monument combining human figure and Greek inscription.", "HIEROGLYPHIC"),
    (30, "b7v", "Monument with Female Figure, Lamp, and Trilingual Inscriptions", "Tall monument with standing female figure holding a lamp. Below: three tiers of inscriptions in Hebrew, Greek, and Latin capitals.", "The most inscription-heavy page in the HP. Hebrew, Greek, and Latin texts encode warnings about a treasure.", "HIEROGLYPHIC"),
    (31, "b8r", "Hieroglyphic Frieze", "Two-register frieze with emblematic figures: chariots, winged beings, dolphins, anchors, vessels. Below: Latin majuscule inscription.", "The first of the HP's pseudo-hieroglyphic friezes — Colonna's invented 'Egyptian' symbolic language.", "HIEROGLYPHIC"),
    (38, "c3r", "Architectural Portal", "Grand classical portal with pediment, columns, and medallion busts. Monumental entrance architecture.", "A monumental doorway representing the threshold between different zones of Poliphilo's journey.", "ARCHITECTURAL"),
    (45, "c6v", "Ruins of the Temple", "Ruined classical temple with broken columns and fragments. Poliphilo contemplates ancient remains.", "Poliphilo encounters another ruin, continuing the theme of ancient grandeur.", "ARCHITECTURAL"),
    (52, "d2v", "Poliphilo at a Portal with Dragon", "Poliphilo recoils from a dragon or beast emerging from a portal. Dramatic confrontation scene.", "A moment of danger and wonder. The dragon guards a threshold — the beast connects to the 'bellua' alchemical annotations.", "NARRATIVE"),
    (59, "d6r", "Emblematic Medallions (PATIENTIA / Anchor-Dolphin)", "Two circular medallion emblems. Top: PATIENTIA EST ORNAMENTVM. Bottom: anchor-and-dolphin with Greek motto ΑΕΙ ΣΠΕΥΔΕ ΒΡΑΔΕΩΣ.", "Two of the HP's most influential emblems. The patience motto and anchor-dolphin (festina lente) connect directly to the Aldine Press device.", "HIEROGLYPHIC"),
    (63, "d8r", "Sleeping Nymph", "A sleeping nymph reclining in a classical aedicule with water flowing from the stone. One of the HP's most copied compositions.", "The sleeping nymph fountain is one of the most influential images in Renaissance art.", "NARRATIVE"),
    (66, "e1r", "Five Nymphs Meeting Poliphilo", "Five nymphs in classical dress approach Poliphilo in a garden. One extends a hand in greeting.", "Poliphilo meets the five senses personified as nymphs.", "NARRATIVE"),
    (71, "e3v", "Cupid on a Sphere", "Winged putto (Cupid) standing on a sphere atop a fountain. Water arcs from the base.", "Cupid/Eros presides over a fountain — love as the animating force of the natural world.", "ARCHITECTURAL"),
    (75, "e5v", "Three Figures in Aedicule", "Three figures in an architectural niche with pediment.", "An allegorical scene set within classical architecture.", "ARCHITECTURAL"),
    (80, "f2v", "The Great Fountain", "Full-page woodcut of an elaborate tiered fountain. Three levels: sea-horses at base, grotesque masks and sphinxes at middle, nude Venus figure under arching water jets at top.", "The most architecturally ambitious fountain in the HP. Its three tiers represent the three levels of being: marine, grotesque (transformation), and divine.", "ARCHITECTURAL"),
    (84, "f4v", "Queen Eleuterylida's Palace", "Interior of ornate palace hall with columned arcade. Seven compartments labeled with planetary names: MERCVRIVS, VENVS, SOL, MARS, LVNA, IVPITER, SATVRNVS.", "The palace of the seven planets — each compartment corresponds to a celestial body and its associated metal, gemstone, and virtue.", "ARCHITECTURAL"),
    (88, "f6v", "Palace Interior with Planetary Compartments", "Detailed view of the planetary palace interior showing ornate facades with arabesque panels.", "A second view of the planetary palace showing the decorative program in detail.", "ARCHITECTURAL"),
    (90, "f7v", "Court Scene with Queen Enthroned", "Queen seated on throne under canopy, attended by courtiers and nymphs. Formal court reception scene.", "Queen Eleuterylida receives Poliphilo. Her name means 'Freely-Given' — she represents generous hospitality.", "NARRATIVE"),
    (93, "g1r", "Ornamental Tripod Table", "Ornate classical tripod with decorative scrollwork and dolphin-form legs.", "An architectural study of a classical tripod.", "DECORATIVE"),
    (94, "g1v", "Covered Vessel on Wheeled Chariot", "Small ornamental urn or covered vessel mounted on a wheeled chariot.", "A ceremonial vessel, possibly for processions or ritual use.", "DECORATIVE"),
    (95, "g2r", "Caryatid Figures Supporting Basin", "Three female caryatid figures supporting a basin with harp-like decorative elements.", "Caryatid architecture — female figures serving as structural columns — is one of the HP's recurring motifs.", "ARCHITECTURAL"),
    (105, "g7r", "Nymph at Fountain Vessel", "Woman standing beside an elaborate fountain vessel on a wheeled platform.", "A nymph associated with a mobile fountain, combining figural and architectural elements.", "NARRATIVE"),
    (119, "h3v", "Obelisk with Three Figures", "Tall obelisk with three standing figures in niches at its base. Greek and Latin inscriptions. DIVINAE AENINITATI visible.", "A monument combining Egyptian (obelisk) and Greek elements.", "ARCHITECTURAL"),
    (123, "h5v", "Seated Scholar at Monument", "Seated figure at a desk within a classical architectural frame with pediment and columns.", "A scholar at work, housed within architecture.", "ARCHITECTURAL"),
    (124, "h6r", "Two Seated Figures at Pedestal with Medallion", "Two seated figures on either side of a pedestal, with a circular medallion portrait above.", "A scene of philosophical dialogue or instruction.", "NARRATIVE"),
    (125, "h6v", "The Three Doors", "Cave or grotto scene: figures before three inscribed doorways. Inscriptions: THEODOXIA, COSMODOXIA, EROTOTROPHOS.", "The central allegory of the HP. Poliphilo must choose between three doors — he chooses the path of Eros.", "NARRATIVE"),
    (126, "h7r", "Poliphilo at the Temple Entrance", "Group of figures approaching a small classical building or temple. Landscape with trees.", "Having chosen EROTOTROPHOS, Poliphilo enters the realm of love and beauty.", "NARRATIVE"),
    (129, "h8v", "Nymphs and Figures Among Trees", "Group of nymphs and figures standing among trees near a building or monument.", "Poliphilo in the company of nymphs in a sacred grove.", "NARRATIVE"),
    (130, "i1r", "Nymphs Walking Through a Grove", "Group of nymphs and a central figure walking through a grove of trees.", "A processional scene through a sacred landscape.", "NARRATIVE"),
    (139, "i5v", "Garden with Pergola", "Two figures standing in a garden with an arched pergola and trees.", "A garden scene showing designed horticultural architecture.", "LANDSCAPE"),
    (149, "k1r", "First Triumphal Chariot (PRIMA TABELLA)", "Two woodcut panels: PRIMA TABELLA showing a chariot with bulls and figures.", "The beginning of the HP's most sustained visual sequence — a triumphal procession celebrating the victory of love.", "PROCESSION"),
    (150, "k1v", "Second Triumphal Panel", "Two woodcut panels showing front and rear views of a triumphal chariot with classical figures.", "Continuation of the procession with views showing the chariot from multiple angles.", "PROCESSION"),
    (151, "k2r", "Triumphal Chariot (TRIVMPHVS TERTIVS)", "Large triumphal chariot drawn by centaurs with nymphs and musicians.", "The third triumph, drawn by centaurs — half-human, half-horse beings representing the dual nature of desire.", "PROCESSION"),
    (152, "k2v", "Triumphal Chariot with Soldiers", "Large triumphal chariot drawn by horses with soldiers, musicians, and banner-bearers.", "A military-themed triumph with martial figures, connecting the procession of love to Roman triumphal traditions.", "PROCESSION"),
    (153, "k3r", "Muses and Apollo Chariot", "Triumphal chariot with the Muses and Apollo, drawn by horses. Musical instruments and laurel wreaths visible.", "The triumph of the arts and music.", "PROCESSION"),
    (154, "k3v", "TABELLA DEXTRA Panels", "Two stacked panel woodcuts: TABELLA DEXTRA showing figures at a doorway and TABELLA SINISTRA showing an outdoor scene.", "Side panels of the procession — left and right views of a passing triumph.", "PROCESSION"),
    (155, "k4r", "PARS ANTERIOR ET POSTERIOR", "Two-panel woodcut showing front and rear views of figures in processional arrangement.", "Front and back views of another section of the procession.", "PROCESSION"),
    (156, "k4v", "TRIVMPHVS: Lovers' Chariot", "Large triumphal chariot bearing reclining lovers embraced among garlands and putti. The emotional climax of the procession.", "The central image of the procession — lovers entwined on a triumphal chariot, representing the ultimate victory of Eros.", "PROCESSION"),
    (158, "k5v", "TABELLA DEXTRA (Second Set)", "Two stacked panels showing processional scenes with figures at doorways and in landscapes.", "Additional processional panels.", "PROCESSION"),
    (159, "k6r", "PARS ANTERIOR ET POSTERIOR (Second)", "Small woodcut showing front and rear views of processional figures.", "Another paired-view panel in the procession sequence.", "PROCESSION"),
    (160, "k6v", "TRIVMPHVS with Triple Panels", "Large chariot woodcut at top plus two TABELLA DEXTRA/SINISTRA panels below.", "The most densely illustrated page in the procession.", "PROCESSION"),
    (161, "k7r", "TERTIVS: Ox Procession", "Two stacked panels showing a procession with oxen and figures carrying implements.", "An agricultural/sacrificial section of the procession, with oxen suggesting ritual sacrifice.", "PROCESSION"),
    (164, "k8v", "Nymphs Approaching Altar", "Procession of nymphs approaching an altar or sacrificial table with trees and architecture.", "A ritual scene marking the transition from procession to ceremony.", "PROCESSION"),
    (165, "l1r", "Festive Scene at Fountain", "Festive scene with figures gathered around a fountain in a garden setting.", "Post-processional celebration.", "PROCESSION"),
    (166, "l1v", "Bacchic Triumphal Chariot", "Large Bacchic triumphal chariot with Maenads, Satyrs, and Dionysiac figures.", "The Bacchic triumph — Dionysus as the complement to Apollo's ordered beauty.", "PROCESSION"),
    (167, "l2r", "QVARTVS: Feasting Chariot", "Chariot with reclining figures feasting among garlands, fruit, and flowing drapery.", "The fourth triumph: a feast on wheels.", "PROCESSION"),
    (185, "m5r", "Worship of Priapus", "Full-page woodcut: nineteen female and five male figures worshipping at a shrine of Priapus.", "The Priapus worship scene marks the transition from procession to temple ritual.", "NARRATIVE"),
    (195, "n2r", "Section and Ground-plan of Rotunda Temple", "Full-page architectural diagram: cross-section and floor plan of the circular Temple of Venus Physizoa.", "The HP's most elaborate architectural diagram.", "DIAGRAM"),
    (197, "n3r", "Winged Female Half-figure Ornament", "Nude winged female half-figure emerging from acanthus foliage. Decorative architectural element.", "A decorative motif from the temple interior.", "DECORATIVE"),
    (198, "n3v", "Globular Lamp Hung in Chains", "Ornate spherical lamp suspended by chains. Detailed metalwork design.", "A lighting fixture from the Temple of Venus.", "DECORATIVE"),
    (201, "n5r", "Crowning of Lantern in Cupola", "Architectural ornament: the lantern crowning the temple cupola, with bells and decorative finial.", "The crowning element of the temple dome.", "DECORATIVE"),
    (204, "n6v", "Inscribed Tablets in Temple", "Two inscribed cartouches with Greek and Latin text. Hieroglyphic devices in the Temple of Venus.", "Inscribed tablets within the temple.", "HIEROGLYPHIC"),
    (205, "n7r", "Procession of Seven Virgins to Altar", "Seven virgins in procession approaching the altar in the Temple of Venus. Ritual scene with priestess.", "The beginning of the Venus temple ceremony.", "NARRATIVE"),
    (207, "n8r", "Polia's Torch Extinguished in Altar-fountain", "Ceremony scene: Polia extinguishes a torch in the fountain at the altar. Priestess and attendants present.", "Polia's torch-extinguishing symbolizes the surrender of Diana's chastity to Venus's love.", "NARRATIVE"),
    (208, "n8v", "Temple Ceremony at Altar", "Figures gathered around the altar in the Temple of Venus. Ritual scene under classical portico.", "Continuation of the temple ceremony.", "NARRATIVE"),
    (210, "o1v", "Two Virgins Offering Swans and Doves", "Two virgins offering swans and doves for sacrifice at the temple altar. Priestess officiates.", "The sacrifice of birds sacred to Venus.", "NARRATIVE"),
    (212, "o2v", "The Altar in the Temple of Venus", "Detailed view of the altar/vessel on its pedestal in the Temple of Venus.", "The altar itself as an object of contemplation.", "ARCHITECTURAL"),
    (213, "o3r", "Temple Ceremony: Miracle of the Roses", "Ceremony scene in the temple. Figures gathered around altar as roses appear.", "The miracle of the roses: a rose-tree rises from the altar.", "NARRATIVE"),
    (219, "o6r", "Sacrifice Scene with Swans at Altar", "Ceremony at temple altar: priestess officiates as swans are sacrificed.", "The culminating sacrifice in the Temple of Venus.", "NARRATIVE"),
    (221, "o7r", "Poliphilus and Polia Receive Fruits", "Poliphilus and Polia receive fruits from the priestess at the altar. Completion of the temple ceremony.", "The lovers receive the fruits of their devotion.", "NARRATIVE"),
    (222, "o7v", "Miracle of the Roses (Full Scene)", "Rose-tree rising from altar. Priestess on ladder tending the miraculous tree. Figures kneel in worship below.", "The miracle of the roses is the climax of the temple ceremony.", "NARRATIVE"),
    (224, "o8v", "Poliphilus and Polia Receive Fruits from Priestess", "Poliphilus and Polia receive ceremonial fruits from the priestess under the temple portico.", "The final gift from the priestess seals the lovers' union.", "NARRATIVE"),
    (228, "p2v", "Ruins of Temple Polyandrion", "Full-page woodcut: ruined classical temple among trees. Obelisk visible. Fallen columns and arches.", "The Polyandrion (cemetery of lovers) — the HP's most romantic archaeological vision.", "ARCHITECTURAL"),
    (233, "p5r", "Obelisk with Hieroglyphic Devices", "Obelisk with hieroglyphic inscriptions plus circular medallion with Latin text.", "The Polyandrion begins with an obelisk covered in hieroglyphics.", "HIEROGLYPHIC"),
    (234, "p5v", "Hieroglyphic Device Strip and Julius Caesar Medallion", "Two woodcuts: strip of small hieroglyphic figures AND circular medallion with DIVO IVLIO CAESARI inscription.", "Julius Caesar medallion combines Roman imperial epigraphy with natural history.", "HIEROGLYPHIC"),
    (235, "p6r", "Two Hieroglyphic Medallion Reliefs", "Two circular medallions with figural scenes: MILITARIS PRVDENTIA and DIVVLII VICTORIAR.", "Paired medallions from the Polyandrion, combining military virtue with love's victory.", "HIEROGLYPHIC"),
    (236, "p6v", "Polyandrion Architrave Fragment", "Architrave fragment with inscription CADAVERIS AMORE FVRENTIVM MISERABVNDIS POLYANDRION.", "The naming inscription of the Polyandrion: a cemetery for those who died raving from love.", "ARCHITECTURAL"),
    (237, "p7r", "Cupola Above Entrance to the Crypt", "Domed cupola structure with columns marking the entrance to the underground crypt.", "The entrance to the crypt beneath the Polyandrion.", "ARCHITECTURAL"),
    (238, "p7v", "Sarcophagus: Interno Plotoni", "Sarcophagus with inscription INTERNO PLOTONI TRICORPORI. Classical funerary monument.", "A sarcophagus dedicated to Pluto, ruler of the underworld.", "ARCHITECTURAL"),
    (241, "q1r", "Mosaic of Hell on Crypt Ceiling", "Large arched scene: mosaic depicting Hell on the ceiling of the crypt. Figures in torment among flames and darkness.", "The Hell mosaic, after Dante.", "NARRATIVE"),
    (243, "q2r", "Sepulchral Monument: D.M. Annirae", "Architectural monument with urn and inscription D.M. ANNIRAE PVCILLAE. Cherub faces on pedestal.", "A funerary monument for a young girl.", "ARCHITECTURAL"),
    (245, "q3r", "Sacrifice Relief: Have Seria Obitum", "Relief panel with figures: old man, youth, faun, and dancers. Inscription HAVE SERIA OBITVM.", "A relief depicting a funerary sacrifice.", "NARRATIVE"),
    (247, "q4r", "Epitaph Fragments with Urn", "Two epitaph fragments: HEVS INSPECTO FACIO inscription and Greek inscription urn.", "Multiple epitaphs showcasing the HP's multilingual epigraphy.", "ARCHITECTURAL"),
    (249, "q5r", "Sepulchral Monument with Latin Inscription", "Tombstone on stepped pedestal with Latin epitaph.", "A classical Roman-style funerary monument.", "ARCHITECTURAL"),
    (250, "q5v", "Epitaphs: Greek Urn and D.M. Lyndia", "Two woodcuts: sepulchral urn with Greek inscription AND tombstone with epitaph D.M. LYNDIA.", "Paired epitaphs continuing the Polyandrion sequence.", "ARCHITECTURAL"),
    (251, "q6r", "Sarcophagus: P. Cornelia Annia", "Elaborate sarcophagus with inscription D.M. P.CORNELIA ANNIA NE INDESOLATA. Tiled roof detail.", "A grand sarcophagus with architectural frame suggesting a miniature temple.", "ARCHITECTURAL"),
    (252, "q6v", "Sarcophagus with Hieroglyphic Devices", "Sarcophagus decorated with hieroglyphic symbols and devices.", "An Egyptian-themed sarcophagus connecting funerary arts of Rome and Egypt.", "HIEROGLYPHIC"),
    (253, "q7r", "Large Epitaph: O Lector Infoelix", "Full-page epitaph within ornate architectural frame. Extended Latin inscription beginning O LECTOR INFOEL...", "The longest epitaph in the Polyandrion. The reader is directly addressed as 'unhappy reader'.", "ARCHITECTURAL"),
    (254, "q7v", "Sepulchral Monument with Laurel Wreath", "Large sepulchral monument crowned with laurel wreath.", "A monument crowned with the laurel of poetic glory.", "ARCHITECTURAL"),
    (257, "r1r", "Monument of Artemisia", "Full-page woodcut: elaborate architectural monument with Queen Artemisia enthroned in central niche.", "The monument of Artemisia, who drank the ashes of her husband Mausolus.", "NARRATIVE"),
    (258, "r1v", "Sepulchral Monument with Putti", "Elaborate sepulchral monument with two putti holding curtain. Arched niche with figure.", "A grand funerary monument combining classical framing with putti and drapery.", "ARCHITECTURAL"),
    (259, "r2r", "Epitaph with Busts of Youth and Woman", "Sepulchral monument with portrait busts. Latin epitaph: ASPICE VIATOR...", "A double portrait monument for two lovers.", "ARCHITECTURAL"),
    (261, "r3r", "Sepulchral Portal: Gates of Life and Death", "Full-page monument: architectural portal with eagle pediment, inscription D.DITI ET PROSER. Two gates below.", "The portal of Dis and Proserpina, with the narrow gates of life and death.", "ARCHITECTURAL"),
    (275, "s2r", "Standard of Cupid's Bark", "Decorative banner with AMOR VINCIT OMNIA inscription.", "The banner of Cupid's ship, proclaiming love conquers all.", "DECORATIVE"),
    (281, "s5r", "The Bark of the God of Love", "Small boat on waves with ornamental prow and stern. Cupid's vessel for the voyage to Cythera.", "Cupid's bark, carrying Poliphilo and Polia across the sea to Venus's island.", "NARRATIVE"),
    (291, "t2r", "Water-work Fountain with Hydra Heads", "Ornate fountain structure with multiple water spouts, hydra-headed decorations, and peristyle columns.", "A garden fountain on Venus's island, combining hydraulic engineering with mythological ornament.", "ARCHITECTURAL"),
    (295, "t4r", "Tree Clipped in Ring-shape", "Topiary: tree shaped into a ring on ornamental base with pedestal.", "The first of the HP's remarkable topiary illustrations.", "DECORATIVE"),
    (297, "t5r", "Box-tree Clipped as Mushroom", "Topiary: box-tree clipped into mushroom shape on stepped circular pedestal.", "Another topiary design from Venus's gardens.", "DECORATIVE"),
    (298, "t5v", "Peristyle Colonnade with Trellis", "Classical peristyle structure with trellis and garden setting.", "A garden architecture combining classical columns with horticultural trellis work.", "ARCHITECTURAL"),
    (301, "t7r", "Plan of the Island of Venus", "Full-page diagram: circular plan of Venus's island showing concentric garden zones and central temple.", "The plan of Venus's island, with concentric rings of gardens surrounding the central sanctuary.", "DIAGRAM"),
    (307, "x2r", "Ornamental Flower-bed Pattern (Circular)", "Circular ornamental flower-bed design with concentric rings of geometric patterns.", "One of the HP's garden-design diagrams.", "DECORATIVE"),
    (311, "x4r", "Ornamental Flower-bed Pattern (Square)", "Square flower-bed design with geometric interlocking patterns.", "A square flower-bed design complementing the circular pattern.", "DECORATIVE"),
    (312, "x4v", "Peacock Topiary on Pedestal", "Box-tree clipped as three peacocks standing on ornamental altar-vase pedestal.", "A topiary peacock, combining horticultural imagination with the symbolic associations of the peacock.", "DECORATIVE"),
    (313, "x5r", "Flower-bed in Shape of Eagle", "Flower-bed pattern shaped as an eagle with spread wings.", "An eagle-shaped parterre, combining heraldic imagery with horticultural design.", "DECORATIVE"),
    (314, "x5v", "Eagle and Urn Flower-bed Design", "Flower-bed pattern with eagle/urn motif. Latin inscription around border.", "An eagle-and-urn parterre design.", "DECORATIVE"),
    (317, "x7r", "Two Trophy Standards", "Two vertical trophy standards side by side: Roman arms trophies with ornamental designs.", "Garden trophies combining military and decorative motifs.", "DECORATIVE"),
    (318, "x7v", "Trophy Standards: QVIS EVADET and NEMO", "Two vertical trophy standards. Tablets inscribed QVIS EVADET and NEMO.", "Paired trophies posing the enigmatic question 'Who shall escape?' answered by 'No one.'", "DECORATIVE"),
    (319, "x8r", "Trophy Standards with NEMO Tablet", "Two more trophy standards with tablets inscribed NEMO.", "Trophies bearing the enigmatic inscription NEMO (no one).", "DECORATIVE"),
    (328, "y4v", "Vase with Dragon-handle Monsters", "Ornate two-handled vase with dragon-form handles. Detailed metalwork with mythological motifs.", "A remarkable vessel combining the HP's obsession with decorative arts and mythological fauna.", "DECORATIVE"),
    (330, "y5v", "Earthenware Amphora with Fumes", "Amphora with odoriferous fumes emerging from orifice. Greek inscription PANTA BAIA BIOY.", "An amphora emitting fragrant smoke, inscribed 'All of life is brief.' Perfume and mortality united.", "DECORATIVE"),
    (331, "y6r", "Precious Stone Vase with Fiery Sparks", "Small ornate vase of precious stone emitting fiery sparks or fumes.", "A remarkable vessel combining precious materials with alchemical imagery.", "DECORATIVE"),
    (334, "y7v", "Terminal Figure with Three Male Heads", "Classical herm/terminal figure on pedestal. Three male heads facing different directions.", "A garden herm, the three heads perhaps representing past, present, and future.", "DECORATIVE"),
    (335, "y8r", "Terminal Figure with Serpent", "Terminal figure/trophy with serpent and ornamental elements. Three heads of Cerberus visible.", "A terminal figure combining classical herm tradition with infernal imagery.", "DECORATIVE"),
    (336, "y8v", "Triumph of Cupid: Nymphs and Satyrs with Chariot", "Procession with nymphs and satyrs pulling chariot bearing Cupid. Captives and trophies.", "A second triumphal procession on Venus's island.", "PROCESSION"),
    (337, "z1r", "Triumph of Cupid", "Large procession: nymphs, satyrs, dragons, and captives in Cupid's triumphal procession.", "Cupid rides in triumph over all who love.", "PROCESSION"),
    (339, "z2r", "Column Base with Rams' Heads", "Architectural detail: column base with rams' heads and sacrifice medallion relief.", "A column base from the amphitheater.", "DECORATIVE"),
    (341, "z3r", "The Amphitheatre in Island of Venus", "Large architectural section: amphitheater structure with tiered seating, arches, and columns.", "The amphitheater on Venus's island.", "ARCHITECTURAL"),
    (349, "A3r", "Ground-plan of Fountain of Venus", "Geometric diagram: heptagonal/octagonal ground-plan of the fountain of Venus.", "The plan of Venus's central fountain.", "DIAGRAM"),
    (365, "B3r", "Poliphilus and Polia at Fountain of Venus", "Garden scene: Poliphilus and Polia with nymphs at the Fountain of Venus.", "The lovers arrive at the culminating fountain.", "NARRATIVE"),
    (386, "C5v", "Polia Drags Prostrate Poliphilus", "Interior scene: Polia drags the prostrate Poliphilus from the sanctuary of Diana. Classical temple columns.", "Polia's act of physical rescue precedes her spiritual surrender to love.", "NARRATIVE"),
    (387, "C6r", "Polia in Temple of Diana; Poliphilus Prostrate", "Temple interior: Poliphilus lies prostrate on the floor while Polia stands in the Temple of Diana.", "Poliphilus has collapsed at Polia's feet in Diana's temple.", "NARRATIVE"),
    (390, "C7v", "Cupid Brandishes Sword over Victims", "Cupid brandishes a sword over kneeling women bound to trees. Chariot visible at right.", "Cupid's punishment of those who resist love.", "NARRATIVE"),
    (391, "C8r", "Lion, Dog, Dragon Devour Victims", "Woodland scene: lion, dog, and dragon devour victims while Cupid flies above with torch and arrows.", "The most violent image in the HP: beasts destroy those who defy love.", "NARRATIVE"),
    (393, "D1r", "Dream of Polia: Cupid Punishes Two Women", "Two women punished by Cupid in a woodland setting. Figures tied to trees with beasts approaching.", "Polia's vision of Cupid's vengeance.", "NARRATIVE"),
    (411, "E2r", "Poliphilus Dead; Polia Kneels in Grief", "Interior scene: Poliphilus lies dead on tiled floor while Polia kneels beside him in grief.", "The central crisis of Book II.", "NARRATIVE"),
    (412, "E2v", "Poliphilus Revived in Polia's Lap", "Interior scene: Polia cradles the revived Poliphilus in her lap.", "Poliphilus revives in Polia's arms — a resurrection through love paralleling the alchemical solve et coagula.", "NARRATIVE"),
    (413, "E3r", "Priestesses Drive Lovers from Temple", "Figures being driven from a classical temple entrance. Priestesses expel the lovers from Diana's sanctuary.", "The priestesses of Diana expel Poliphilus and Polia.", "NARRATIVE"),
    (416, "E4v", "Polia's Bed-chamber Vision", "Two-scene woodcut: landscape with figures above, Polia in bed-chamber below. Diana vs Venus contest in sky.", "Polia's pivotal vision: Diana and Venus contend for her allegiance.", "NARRATIVE"),
]

# HP pages with local images (from cutout examples and known local files)
HP_LOCAL_IMAGES = {330, 392, 393}

def build_hp_emblems():
    emblems = []
    for (page, sig, title, desc, context, category) in WOODCUTS_1499:
        woodcut_id = f"HP_{page:04d}"
        ia_page = page + 5  # IA offset formula from seed script
        local_img = f"sources/hypnerotomachia-polyphili/site/images/woodcuts_1499/hp1499_p{page}.jpg"
        ia_url = f"https://archive.org/details/hypnerotomachiap00colo/page/n{ia_page}/mode/1up"

        # Quick motif candidates from title/description keywords
        motif_candidates = []
        text = (title + " " + desc).lower()
        kw_map = [
            ("dragon",       ["dragon"]),
            ("serpent",      ["serpent", "snake"]),
            ("lion",         ["lion"]),
            ("vessel",       ["vessel", "vase", "urn", "amphora", "flask", "pot", "lamp"]),
            ("fountain",     ["fountain", "water", "spring", "stream"]),
            ("tree",         ["tree", "topiary"]),
            ("bird",         ["bird", "peacock", "swan", "dove", "eagle", "phoenix"]),
            ("furnace",      ["furnace", "fire", "flames"]),
            ("star",         ["planet", "star", "zodiac", "saturn", "jupiter", "mars", "luna", "sol", "mercury", "venus"]),
            ("mountain",     ["mountain", "cave", "grotto", "rock"]),
            ("hermaphrodite",["hermaphrodite", "androgyne"]),
            ("king",         ["king", "crowned king"]),
            ("queen",        ["queen", "enthroned"]),
        ]
        for motif_id, keywords in kw_map:
            if any(kw in text for kw in keywords):
                motif_candidates.append(motif_id)

        emblem = {
            "id": woodcut_id,
            "work_id": "hypnerotomachia_poliphili",
            "page_1499": page,
            "signature_1499": sig,
            "label": title,
            "description": desc,
            "narrative_context": context,
            "subject_category": category,
            "image_path": local_img,
            "image_available_locally": page in HP_LOCAL_IMAGES,
            "ia_page": ia_page,
            "provenance_url": ia_url,
            "rights_note": "Public domain. Internet Archive scan.",
            "tradition": "alchemical_reception",
            "motif_candidates": motif_candidates,
            "review_status": "stub",
        }
        emblems.append(emblem)
    return emblems


# ---------------------------------------------------------------------------
# VISUAL ELEMENTS — seed from cutout manifest
# ---------------------------------------------------------------------------

def build_visual_elements():
    manifest_path = ROOT / "assets/cutout-examples/cutout_examples_manifest.json"
    manifest = load_json(manifest_path)

    elements = []
    for item in manifest:
        # Map source path to work_id and emblem_id
        src = item["source"].replace("\\", "/")
        if "claudiens" in src:
            work_id = "atalanta_fugiens"
            # extract emblem number from filename like emblem-25.jpg
            fname = src.split("/")[-1]  # emblem-25.jpg
            try:
                num = int(fname.replace("emblem-", "").replace(".jpg", ""))
                emblem_id = f"AF_{num:02d}"
            except ValueError:
                emblem_id = None
        elif "hypnerotomachia" in src:
            work_id = "hypnerotomachia_poliphili"
            # extract page from filename like hp1499_p393.jpg
            fname = src.split("/")[-1]
            try:
                page = int(fname.replace("hp1499_p", "").replace(".jpg", ""))
                emblem_id = f"HP_{page:04d}"
            except ValueError:
                emblem_id = None
        else:
            work_id = None
            emblem_id = None

        element = {
            "id": item["id"],
            "source_project": "cutout-examples",
            "work_id": work_id,
            "emblem_id": emblem_id,
            "label": item["label"],
            "motif_candidates": item["motifs"],
            "image_path": item["source"].replace("\\", "/"),
            "crop_path": item.get("crop_jpg", "").replace("\\", "/"),
            "transparent_png": item.get("transparent_png", "").replace("\\", "/"),
            "bbox": item.get("bbox"),
            "description": item.get("label"),
            "provenance_url": None,
            "rights_note": None,
            "method": item.get("method"),
            "confidence": "medium",
            "review_status": "stub",
        }
        elements.append(element)

    return elements


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("Building EmblemPrintShop data layer...")

    # works.json
    write_json(DATA_OUT / "works.json", WORKS)

    # motifs.json
    write_json(DATA_OUT / "motifs.json", MOTIFS)

    # emblems.json
    maier = build_maier_emblems()
    hp = build_hp_emblems()
    all_emblems = maier + hp
    write_json(DATA_OUT / "emblems.json", all_emblems)

    # visual_elements.json
    elements = build_visual_elements()
    write_json(DATA_OUT / "visual_elements.json", elements)

    print(f"\nDone.")
    print(f"  works:           {len(WORKS)}")
    print(f"  motifs:          {len(MOTIFS)}")
    print(f"  emblems (Maier): {len(maier)}")
    print(f"  emblems (HP):    {len(hp)}")
    print(f"  visual_elements: {len(elements)}")


if __name__ == "__main__":
    main()
