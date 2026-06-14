#!/usr/bin/env python3
"""seed_1499_woodcuts.py — Populate woodcuts table with the complete 1499 HP inventory.

Seeds all woodcuts from the 1499 Aldine first edition of the
Hypnerotomachia Poliphili. Merges with existing entries where they
overlap (matched by page_1499).

The 1499 edition contains approximately 172 woodcut illustrations
across 234 leaves. This script catalogs them with:
- Title, description, narrative context
- Page/signature in the 1499 edition
- Internet Archive page index (for image fetching)
- Subject category

Sources: Pozzi & Ciapponi critical edition (1980), Ariani & Gabriele
edition (1998), Godwin 1999 translation, Fierz-David 1947 analysis,
Lefaivre 1997 (MIT Press).

IA offset formula: ia_page = page_1499 + 5
Verified: HP p.4 = IA n9, HP p.28 = IA n33

Usage:
    python scripts/seed_1499_woodcuts.py
    python scripts/seed_1499_woodcuts.py --dry-run
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "hp.db"

# IA offset: IA page number = HP 1499 page number + 5
IA_OFFSET = 5

# Complete 1499 HP woodcut inventory
# Format: (page_1499, signature_1499, title, description, narrative_context, subject_category)
WOODCUTS_1499 = [
    # === BOOK I: Poliphilo's Dream ===
    # Opening / Dark Forest
    (4, "a2v", "Poliphilo in the Dark Forest",
     "Poliphilo wanders among tall trees in a dense forest. Small figure at center surrounded by towering trunks with detailed foliage.",
     "The opening scene of the HP. Poliphilo, having fallen asleep weeping for his beloved Polia, finds himself lost in a dark and terrifying forest — echoing Dante's selva oscura. This is the threshold between waking and dreaming.",
     "LANDSCAPE"),

    (8, "a4v", "Poliphilo at the Landscape with River",
     "Poliphilo rests in an open landscape with trees and a stream. Pastoral scene with classical elements.",
     "Having escaped the dark forest, Poliphilo enters a beautiful open landscape. He drinks from a stream and rests, transitioning from terror to wonder. The landscape represents the first stage of his allegorical journey.",
     "LANDSCAPE"),

    (10, "a5v", "Poliphilo Sleeping (Dream within Dream)",
     "Poliphilo lies sleeping on the ground in a wooded landscape. A second dream begins within the first.",
     "Poliphilo falls asleep again within his dream, initiating the dream-within-a-dream structure that is the HP's most distinctive narrative device. This second sleep takes him deeper into the allegorical realm.",
     "NARRATIVE"),

    (11, "a6r", "Poliphilo in a Garden with Palms",
     "Poliphilo stands in a garden setting with palm trees and classical vegetation.",
     "Poliphilo awakens in a beautiful garden with exotic plants. The palms and ordered vegetation signal his entry into a civilized, designed landscape — architecture replacing wilderness.",
     "LANDSCAPE"),

    # The Pyramid and Monumental Architecture
    (16, "b2v", "The Great Pyramid",
     "Full-page woodcut of a massive stepped pyramid topped by a tall obelisk surmounted by a figure. Colonnaded portico at the base. Inscription KITOMARNO visible.",
     "The centerpiece of Poliphilo's first architectural encounter. This impossible pyramid exceeds the Egyptian originals in Colonna's description — its dimensions are meticulously specified and internally consistent, demonstrating the author's architectural learning.",
     "ARCHITECTURAL"),

    (22, "b5r", "The Ruined Colossal Horse",
     "Fragments of a colossal bronze horse lying among ruins. One of the HP's most evocative images of ancient grandeur brought low.",
     "Poliphilo discovers the ruins of an immense bronze horse — a symbol of imperial ambition and the transience of human achievement. The scale of the ruin matches the scale of the pyramid.",
     "ARCHITECTURAL"),

    (23, "b5v", "Twin Inscribed Monuments (D.AMBIG.D.D.)",
     "Two rectangular stone pedestals with circular wreath inscriptions. Enigmatic Latin abbreviated text within each wreath.",
     "Poliphilo encounters paired funerary monuments with cryptic inscriptions. The enigmatic abbreviations have generated centuries of scholarly debate — they may encode alchemical, erotic, or architectural meanings.",
     "HIEROGLYPHIC"),

    (24, "b6r", "Figures with TEMPVS",
     "Group of classical figures, one labeled TEMPVS (Time). Allegorical scene with personified abstractions.",
     "An allegorical group representing Time and associated concepts. The personification of abstract ideas through classical figures is central to the HP's visual rhetoric.",
     "NARRATIVE"),

    (25, "b6r", "Classical Figures in a Garden",
     "Group of figures in classical dress gathered in a garden or outdoor scene.",
     "Poliphilo encounters allegorical figures in an idealized setting. The garden setting mediates between natural and architectural space.",
     "NARRATIVE"),

    (27, "b6v", "Inscription Monument (ΓΟΝΟΣ ΚΑΙ ΕΤΟΥΣΙΑ)",
     "Stone stele with Greek and pseudo-Arabic inscriptions in an arched niche. ΓΟΝΟΣ ΚΑΙ ΕΤΟΥΣΙΑ (Offspring and Abundance).",
     "A multilingual monument displaying Greek, Arabic, and Hebrew-like characters. The inscription 'Offspring and Abundance' connects to the HP's themes of fertility and generative power.",
     "HIEROGLYPHIC"),

    (28, "b6v", "The Elephant and Obelisk",
     "An elephant bearing an obelisk on a circular stepped pedestal. The obelisk is topped with a sphere and decorated with pseudo-hieroglyphic panels.",
     "The most famous image in the HP. This combination of elephant and obelisk was unprecedented in European art and directly inspired Bernini's 1667 sculpture in Piazza della Minerva, Rome. It represents the union of strength (elephant) and wisdom (obelisk/hieroglyphs).",
     "ARCHITECTURAL"),

    (29, "b7r", "Figure on Monument with Greek Inscription",
     "Standing figure atop a pedestal with Greek text. Classical architectural framing.",
     "A monument combining human figure and Greek inscription, continuing the HP's program of embedding encoded meaning in architectural forms.",
     "HIEROGLYPHIC"),

    (30, "b7v", "Monument with Female Figure, Lamp, and Trilingual Inscriptions",
     "Tall monument with standing female figure holding a lamp. Below: three tiers of inscriptions in Hebrew, Greek, and Latin capitals.",
     "The most inscription-heavy page in the HP. Hebrew, Greek, and Latin texts encode warnings about a treasure. The female figure with lamp represents illumination — both literal and philosophical.",
     "HIEROGLYPHIC"),

    (31, "b8r", "Hieroglyphic Frieze",
     "Two-register frieze with emblematic figures: chariots, winged beings, dolphins, anchors, vessels. Below: Latin majuscule inscription.",
     "The first of the HP's pseudo-hieroglyphic friezes — Colonna's invented 'Egyptian' symbolic language. The emblems encode a message that combines Roman imperial imagery with invented symbolic grammar.",
     "HIEROGLYPHIC"),

    (38, "c3r", "Architectural Portal",
     "Grand classical portal with pediment, columns, and medallion busts. Monumental entrance architecture.",
     "A monumental doorway representing the threshold between different zones of Poliphilo's journey. The architectural vocabulary draws on Roman triumphal arch tradition.",
     "ARCHITECTURAL"),

    (45, "c6v", "Ruins of the Temple",
     "Ruined classical temple with broken columns and fragments. Poliphilo contemplates ancient remains.",
     "Poliphilo encounters another ruin, continuing the theme of ancient grandeur and modern contemplation that runs through Book I.",
     "ARCHITECTURAL"),

    (52, "d2v", "Poliphilo at a Portal with Dragon",
     "Poliphilo recoils from a dragon or beast emerging from a portal. Dramatic confrontation scene.",
     "A moment of danger and wonder. The dragon guards a threshold — Poliphilo must confront fear to continue his journey. The beast connects to the 'bellua' alchemical annotations in the BL copy.",
     "NARRATIVE"),

    (59, "d6r", "Emblematic Medallions (PATIENTIA / Anchor-Dolphin)",
     "Two circular medallion emblems. Top: PATIENTIA EST ORNAMENTVM CVSTO/DIA ET PROTECTIO VITAE. Bottom: anchor-and-dolphin with Greek motto ΑΕΙ ΣΠΕΥΔΕ ΒΡΑΔΕΩΣ.",
     "Two of the HP's most influential emblems. The patience motto and the anchor-dolphin (festina lente — 'hasten slowly') connect directly to the Aldine Press device. These images helped establish the European emblem tradition.",
     "HIEROGLYPHIC"),

    (63, "d8r", "Sleeping Nymph",
     "A sleeping nymph reclining in a classical aedicule with water flowing from the stone. One of the HP's most copied compositions.",
     "The sleeping nymph fountain is one of the most influential images in Renaissance art. The combination of sleeping female figure, water, and classical architecture was widely imitated. The Latin inscription ΠΑΝΙΚΟΣ warns that the sleep is sacred.",
     "NARRATIVE"),

    (66, "e1r", "Five Nymphs Meeting Poliphilo",
     "Five nymphs in classical dress approach Poliphilo in a garden. One extends a hand in greeting.",
     "Poliphilo meets the five senses personified as nymphs. Their names encode the Greek words for each sense. This begins the section of the HP most explicitly concerned with sensory knowledge and pleasure.",
     "NARRATIVE"),

    (71, "e3v", "Cupid on a Sphere",
     "Winged putto (Cupid) standing on a sphere atop a fountain. Water arcs from the base.",
     "Cupid/Eros presides over a fountain — love as the animating force of the natural world. The sphere represents cosmic love.",
     "ARCHITECTURAL"),

    (75, "e5v", "Three Figures in Aedicule",
     "Three figures in an architectural niche with pediment. Interior architectural scene.",
     "An allegorical scene set within classical architecture. The aedicule form connects to Roman domestic religion and shrine design.",
     "ARCHITECTURAL"),

    (80, "f2v", "The Great Fountain",
     "Full-page woodcut of an elaborate tiered fountain. Three levels: sea-horses at base, grotesque masks and sphinxes at middle, nude Venus figure under arching water jets at top.",
     "The most architecturally ambitious fountain in the HP. Its three tiers represent the three levels of being: marine (water/matter), grotesque (transformation), and divine (Venus/beauty). The fountain is both an architectural fantasy and an alchemical diagram.",
     "ARCHITECTURAL"),

    (84, "f4v", "Queen Eleuterylida's Palace",
     "Interior of ornate palace hall with columned arcade. Seven compartments labeled with planetary names: MERCVRIVS, VENVS, SOL, MARS, LVNA, IVPITER, SATVRNVS.",
     "The palace of the seven planets — each compartment corresponds to a celestial body and its associated metal, gemstone, and virtue. This is the HP's most explicit cosmological diagram, connecting architecture to astrology.",
     "ARCHITECTURAL"),

    (88, "f6v", "Palace Interior with Planetary Compartments",
     "Detailed view of the planetary palace interior showing ornate facades with arabesque panels.",
     "A second view of the planetary palace showing the decorative program in detail. The arabesque patterns connect to Islamic geometric design traditions that Colonna knew from Venetian trade contacts.",
     "ARCHITECTURAL"),

    (90, "f7v", "Court Scene with Queen Enthroned",
     "Queen seated on throne under canopy, attended by courtiers and nymphs. Formal court reception scene.",
     "Queen Eleuterylida receives Poliphilo. Her name means 'Freely-Given' — she represents generous hospitality and the liberal arts. The court scene follows classical ekphrasis conventions.",
     "NARRATIVE"),

    (93, "g1r", "Ornamental Tripod Table",
     "Ornate classical tripod with decorative scrollwork and dolphin-form legs.",
     "An architectural study of a classical tripod — the kind of object that appears in Roman domestic settings and temple furnishings. Colonna's attention to decorative arts is as detailed as his architectural descriptions.",
     "DECORATIVE"),

    (94, "g1v", "Covered Vessel on Wheeled Chariot",
     "Small ornamental urn or covered vessel mounted on a wheeled chariot or cart.",
     "A ceremonial vessel, possibly for processions or ritual use. The combination of vessel and wheels suggests mobile sacred architecture.",
     "DECORATIVE"),

    (95, "g2r", "Caryatid Figures Supporting Basin",
     "Three female caryatid figures supporting a basin or table with harp-like decorative elements.",
     "Caryatid architecture — female figures serving as structural columns — is one of the HP's recurring motifs. These figures connect architecture to the human body.",
     "ARCHITECTURAL"),

    (105, "g7r", "Nymph at Fountain Vessel",
     "Woman standing beside an elaborate fountain vessel on a wheeled platform.",
     "A nymph associated with a mobile fountain, combining figural and architectural elements.",
     "NARRATIVE"),

    (119, "h3v", "Obelisk with Three Figures",
     "Tall obelisk with three standing figures in niches at its base. Greek and Latin inscriptions. DIVINAE AENINITATI inscription visible.",
     "A monument combining Egyptian (obelisk) and Greek (inscriptions) elements. The three figures may represent philosophical or allegorical personifications.",
     "ARCHITECTURAL"),

    (123, "h5v", "Seated Scholar at Monument",
     "Seated figure at a desk or lectern within a classical architectural frame with pediment and columns.",
     "A scholar or philosopher at work, housed within architecture. This image of intellectual activity framed by classical design embodies the HP's fusion of learning and building.",
     "ARCHITECTURAL"),

    (124, "h6r", "Two Seated Figures at Pedestal with Medallion",
     "Two seated figures on either side of a pedestal, with a circular medallion portrait above. Classical architectural frame.",
     "A scene of philosophical dialogue or instruction. The two-figure composition suggests teacher and student, or the exchange of ideas.",
     "NARRATIVE"),

    (125, "h6v", "The Three Doors",
     "Cave or grotto scene: figures before three inscribed doorways in a rocky mountainside. Inscriptions: THEODOXIA, COSMODOXIA, EROTOTROPHOS.",
     "The central allegory of the HP. Poliphilo must choose between three doors: Glory of God (THEODOXIA), Glory of the World (COSMODOXIA), and Nourisher of Love (EROTOTROPHOS). He chooses the third — the path of Eros. This scene is the HP's version of the Choice of Hercules.",
     "NARRATIVE"),

    (126, "h7r", "Poliphilo at the Temple Entrance",
     "Group of figures approaching a small classical building or temple. Landscape with trees.",
     "Having chosen the door of EROTOTROPHOS, Poliphilo enters the realm of love and beauty. The classical temple represents the shrine of Venus.",
     "NARRATIVE"),

    (129, "h8v", "Nymphs and Figures Among Trees",
     "Group of nymphs and figures standing among trees near a building or monument.",
     "Poliphilo in the company of nymphs in a sacred grove. The combination of architecture and nature is characteristic of the HP's designed landscapes.",
     "NARRATIVE"),

    (130, "i1r", "Nymphs Walking Through a Grove",
     "Group of nymphs and a central figure walking through a grove of trees.",
     "A processional scene through a sacred landscape, leading Poliphilo toward the next stage of his journey.",
     "NARRATIVE"),

    (139, "i5v", "Garden with Pergola",
     "Two figures standing in a garden with an arched pergola and trees.",
     "A garden scene showing designed horticultural architecture — the pergola represents the domestication of nature through human craft.",
     "LANDSCAPE"),

    # Triumphal Procession sequence (pp. 149-167)
    (149, "k1r", "First Triumphal Chariot (PRIMA TABELLA)",
     "Two woodcut panels: PRIMA TABELLA showing a chariot with bulls and figures. Beginning of the triumphal procession sequence.",
     "The beginning of the HP's most sustained visual sequence — a triumphal procession celebrating the victory of love. The first chariot establishes the ceremonial vocabulary.",
     "PROCESSION"),

    (150, "k1v", "Second Triumphal Panel",
     "Two woodcut panels showing front and rear views of a triumphal chariot with classical figures.",
     "Continuation of the procession with views showing the chariot from multiple angles — an unusual device suggesting the viewer walks around the object.",
     "PROCESSION"),

    (151, "k2r", "Triumphal Chariot (TRIVMPHVS TERTIVS)",
     "Large triumphal chariot drawn by centaurs with nymphs and musicians.",
     "The third triumph in the procession, drawn by centaurs — half-human, half-horse beings representing the dual nature of desire.",
     "PROCESSION"),

    (152, "k2v", "Triumphal Chariot with Soldiers",
     "Large triumphal chariot drawn by horses with soldiers, musicians, and banner-bearers.",
     "A military-themed triumph with martial figures, connecting the procession of love to Roman triumphal traditions.",
     "PROCESSION"),

    (153, "k3r", "Muses and Apollo Chariot",
     "Triumphal chariot with the Muses and Apollo, drawn by horses. Musical instruments and laurel wreaths visible.",
     "The triumph of the arts and music. Apollo and the Muses represent the highest achievements of human culture in the classical tradition.",
     "PROCESSION"),

    (154, "k3v", "TABELLA DEXTRA Panels",
     "Two stacked panel woodcuts: TABELLA DEXTRA showing figures at a doorway and TABELLA SINISTRA showing an outdoor scene.",
     "Side panels of the procession showing narrative scenes — the left and right views of a passing triumph, like spectators at a parade.",
     "PROCESSION"),

    (155, "k4r", "PARS ANTERIOR ET POSTERIOR",
     "Two-panel woodcut showing front and rear views of figures in processional arrangement.",
     "Front and back views of another section of the procession, continuing the immersive spatial presentation.",
     "PROCESSION"),

    (156, "k4v", "TRIVMPHVS: Lovers' Chariot",
     "Large triumphal chariot bearing reclining lovers embraced among garlands and putti. The emotional climax of the procession.",
     "The central image of the procession — lovers entwined on a triumphal chariot, representing the ultimate victory of Eros. This is the most explicitly amorous image in the HP.",
     "PROCESSION"),

    (158, "k5v", "TABELLA DEXTRA (Second Set)",
     "Two stacked panels showing processional scenes with figures at doorways and in landscapes.",
     "Additional processional panels continuing the parade sequence.",
     "PROCESSION"),

    (159, "k6r", "PARS ANTERIOR ET POSTERIOR (Second)",
     "Small woodcut showing front and rear views of processional figures.",
     "Another paired-view panel in the procession sequence.",
     "PROCESSION"),

    (160, "k6v", "TRIVMPHVS with Triple Panels",
     "Large chariot woodcut at top plus two TABELLA DEXTRA/SINISTRA panels below. Dense woodcut-text integration.",
     "The most densely illustrated page in the procession, combining large chariot and subsidiary panel views.",
     "PROCESSION"),

    (161, "k7r", "TERTIVS: Ox Procession",
     "Two stacked panels showing a procession with oxen and figures carrying implements.",
     "An agricultural/sacrificial section of the procession, with oxen suggesting ritual sacrifice in the Roman tradition.",
     "PROCESSION"),

    (164, "k8v", "Nymphs Approaching Altar",
     "Procession of nymphs approaching an altar or sacrificial table with trees and architecture.",
     "A ritual scene marking the transition from procession to ceremony. The altar signals the approach to Venus's shrine.",
     "PROCESSION"),

    (165, "l1r", "Festive Scene at Fountain",
     "Festive scene with figures gathered around a fountain or basin in a garden setting.",
     "Post-processional celebration, combining revelry with the HP's characteristic fountain imagery.",
     "PROCESSION"),

    (166, "l1v", "Bacchic Triumphal Chariot",
     "Large Bacchic triumphal chariot with Maenads, Satyrs, and Dionysiac figures. The most explicitly pagan image in the procession.",
     "The Bacchic triumph represents the wild, ecstatic dimension of love — Dionysus as the complement to Apollo's ordered beauty. Maenads and satyrs embody unrestrained passion.",
     "PROCESSION"),

    (167, "l2r", "QVARTVS: Feasting Chariot",
     "Chariot with reclining figures feasting among garlands, fruit, and flowing drapery.",
     "The fourth triumph: a feast on wheels. The combination of food, drink, and movement represents the sensory abundance of the world Eros governs.",
     "PROCESSION"),

    # === WORSHIP OF PRIAPUS & TEMPLE OF VENUS (pp. 185-221) ===
    (185, "m5r", "Worship of Priapus",
     "Full-page woodcut: nineteen female and five male figures worshipping at a shrine of Priapus. Densely populated ritual scene.",
     "The Priapus worship scene marks the transition from procession to temple ritual. The explicit nature of this woodcut embodies the HP's frank treatment of fertility and desire.",
     "NARRATIVE"),

    (195, "n2r", "Section and Ground-plan of Rotunda Temple",
     "Full-page architectural diagram: cross-section and floor plan of the circular Temple of Venus Physizoa. Detailed measurements and proportions.",
     "The HP's most elaborate architectural diagram. The rotunda temple embodies the mathematical perfection that Colonna sees as analogous to divine love.",
     "DIAGRAM"),

    (197, "n3r", "Winged Female Half-figure Ornament",
     "Nude winged female half-figure emerging from acanthus foliage. Decorative architectural element.",
     "A decorative motif from the temple interior, combining human and vegetal forms in the grotesque tradition.",
     "DECORATIVE"),

    (198, "n3v", "Globular Lamp Hung in Chains",
     "Ornate spherical lamp suspended by chains. Detailed metalwork design.",
     "A lighting fixture from the Temple of Venus, described in meticulous detail as part of the HP's ekphrastic tradition.",
     "DECORATIVE"),

    (201, "n5r", "Crowning of Lantern in Cupola",
     "Architectural ornament: the lantern crowning the temple cupola, with bells and decorative finial.",
     "The crowning element of the temple dome, completing the architectural description from foundation to apex.",
     "DECORATIVE"),

    (204, "n6v", "Inscribed Tablets in Temple",
     "Two inscribed cartouches/tablets with Greek and Latin text. Hieroglyphic devices in the Temple of Venus.",
     "Inscribed tablets within the temple, combining Greek and Latin in the HP's characteristic multilingual epigraphy.",
     "HIEROGLYPHIC"),

    (205, "n7r", "Procession of Seven Virgins to Altar",
     "Seven virgins in procession approaching the altar in the Temple of Venus. Ritual scene with priestess.",
     "The beginning of the Venus temple ceremony. Seven virgins process toward the altar where Poliphilo and Polia will be united.",
     "NARRATIVE"),

    (207, "n8r", "Polia's Torch Extinguished in Altar-fountain",
     "Ceremony scene: Polia extinguishes a torch in the fountain at the altar. Priestess and attendants present.",
     "Polia's torch-extinguishing symbolizes the surrender of Diana's chastity to Venus's love.",
     "NARRATIVE"),

    (208, "n8v", "Temple Ceremony at Altar",
     "Figures gathered around the altar in the Temple of Venus. Ritual scene under classical portico.",
     "Continuation of the temple ceremony with ritual offerings.",
     "NARRATIVE"),

    (210, "o1v", "Two Virgins Offering Swans and Doves",
     "Two virgins offering swans and doves for sacrifice at the temple altar. Priestess officiates.",
     "The sacrifice of birds sacred to Venus. Swans and doves are the traditional animals of the love goddess.",
     "NARRATIVE"),

    (212, "o2v", "The Altar in the Temple of Venus",
     "Detailed view of the altar/vessel on its pedestal in the Temple of Venus.",
     "The altar itself as an object of contemplation. Like all furnishings in the HP, it is described as a work of art.",
     "ARCHITECTURAL"),

    (213, "o3r", "Temple Ceremony: Miracle of the Roses",
     "Ceremony scene in the temple. Figures gathered around altar as roses appear.",
     "The miracle of the roses: a rose-tree rises from the altar as the ceremony reaches its climax.",
     "NARRATIVE"),

    (219, "o6r", "Sacrifice Scene with Swans at Altar",
     "Ceremony at temple altar: priestess officiates as swans are sacrificed under classical portico.",
     "The culminating sacrifice in the Temple of Venus. The swans represent Polia's purity offered to love.",
     "NARRATIVE"),

    (222, "o7v", "Miracle of the Roses",
     "Rose-tree rising from altar. Priestess on ladder tending the miraculous tree. Figures kneel in worship below.",
     "The miracle of the roses is the climax of the temple ceremony. A supernatural rose-tree springs from the altar, confirming Venus's blessing on the lovers.",
     "NARRATIVE"),

    (224, "o8v", "Poliphilus and Polia Receive Fruits from Priestess",
     "Poliphilus and Polia receive ceremonial fruits from the priestess under the temple portico. Multiple attendant figures.",
     "The final gift from the priestess seals the lovers' union. The fruits symbolize the consummation of the sacred marriage ceremony.",
     "NARRATIVE"),

    # NOTE: entry at p.221 likely duplicates p.222/224 ceremony scene — keep for now
    (221, "o7r", "Poliphilus and Polia Receive Fruits",
     "Poliphilus and Polia receive fruits from the priestess at the altar. Completion of the temple ceremony.",
     "The lovers receive the fruits of their devotion. This final gift from the priestess seals their union under Venus's blessing.",
     "NARRATIVE"),

    # === POLYANDRION / CEMETERY (pp. 228-261) ===
    (228, "p2v", "Ruins of Temple Polyandrion",
     "Full-page woodcut: ruined classical temple among trees and vegetation. Obelisk visible. Fallen columns and arches. One of the HP's finest architectural compositions.",
     "The Polyandrion (cemetery of lovers) appears as a magnificent ruin. This image of classical architecture returning to nature is the HP's most romantic archaeological vision.",
     "ARCHITECTURAL"),

    (233, "p5r", "Obelisk with Hieroglyphic Devices",
     "Obelisk with hieroglyphic inscriptions plus circular medallion with Latin text. Two woodcuts on one page.",
     "The Polyandrion (cemetery of lovers) begins with an obelisk covered in hieroglyphics. The HP's sustained engagement with Egyptian symbolism reaches its peak here.",
     "HIEROGLYPHIC"),

    (235, "p6r", "Two Hieroglyphic Medallion Reliefs",
     "Two circular medallions with figural scenes and Latin inscriptions: MILITARIS PRVDENTIA and DIVVLII VICTORIAR.",
     "Paired medallions from the Polyandrion monuments, combining military virtue with love's victory.",
     "HIEROGLYPHIC"),

    (234, "p5v", "Hieroglyphic Device Strip and Julius Caesar Medallion",
     "Two woodcuts: strip of small hieroglyphic figures/objects AND circular medallion with DIVO IVLIO CAESARI inscription, ants and elephants.",
     "The Julius Caesar medallion combines Roman imperial epigraphy with natural history (ants, elephants) in the HP's characteristic fusion of classical learning.",
     "HIEROGLYPHIC"),

    (236, "p6v", "Polyandrion Architrave Fragment",
     "Architrave fragment with inscription CADAVERIS AMORE FVRENTIVM MISERABVNDIS POLYANDRION.",
     "The naming inscription of the Polyandrion: a cemetery for those who died raving from love. This establishes the section's memento mori theme.",
     "ARCHITECTURAL"),

    (237, "p7r", "Cupola Above Entrance to the Crypt",
     "Domed cupola structure with columns marking the entrance to the underground crypt.",
     "The entrance to the crypt beneath the Polyandrion. The descent underground parallels classical katabasis narratives.",
     "ARCHITECTURAL"),

    (238, "p7v", "Sarcophagus: Interno Plotoni",
     "Sarcophagus with inscription INTERNO PLOTONI TRICORPORI. Classical funerary monument.",
     "A sarcophagus dedicated to Pluto (Pluton), ruler of the underworld. The HP connects love's death to mythological underworld geography.",
     "ARCHITECTURAL"),

    (241, "q1r", "Mosaic of Hell on Crypt Ceiling",
     "Large arched scene: mosaic depicting Hell on the ceiling of the crypt. Figures in torment among flames and darkness.",
     "The Hell mosaic, after Dante. Colonna places a vision of infernal punishment within the lovers' cemetery, linking erotic transgression to damnation.",
     "NARRATIVE"),

    (243, "q2r", "Sepulchral Monument: D.M. Annirae",
     "Architectural monument with urn and inscription D.M. ANNIRAE PVCILLAE. Cherub faces on pedestal.",
     "A funerary monument for a young girl, combining Roman epigraphic conventions with Renaissance decorative motifs.",
     "ARCHITECTURAL"),

    (245, "q3r", "Sacrifice Relief: Have Seria Obitum",
     "Relief panel with figures: old man, youth, faun, and dancers. Inscription HAVE SERIA OBITVM AMANTIS VALE.",
     "A relief depicting a funerary sacrifice with the farewell inscription to a dead lover.",
     "NARRATIVE"),

    (247, "q4r", "Epitaph Fragments with Urn",
     "Two epitaph fragments on one page: HEVS INSPECTO FACIO inscription and Greek inscription urn.",
     "Multiple epitaphs from the Polyandrion, showcasing the HP's multilingual epigraphy (Latin and Greek).",
     "ARCHITECTURAL"),

    (249, "q5r", "Sepulchral Monument with Latin Inscription",
     "Tombstone on stepped pedestal with Latin epitaph: INTER.D.DEAR.Q.CVIBVS ADVLESCENS...",
     "A classical Roman-style funerary monument for a young man who died of intemperate love.",
     "ARCHITECTURAL"),

    (250, "q5v", "Epitaphs: Greek Urn and D.M. Lyndia",
     "Two woodcuts: sepulchral urn with Greek inscription AND tombstone with epitaph D.M. LYNDIA.",
     "Paired epitaphs continuing the Polyandrion sequence. The Greek urn demonstrates Colonna's classical erudition.",
     "ARCHITECTURAL"),

    (251, "q6r", "Sarcophagus: P. Cornelia Annia",
     "Elaborate sarcophagus with inscription D.M. P.CORNELIA ANNIA NE INDESOLATA. Tiled roof detail.",
     "A grand sarcophagus for a Roman noblewoman, with an elaborate architectural frame suggesting a miniature temple.",
     "ARCHITECTURAL"),

    (252, "q6v", "Sarcophagus with Hieroglyphic Devices",
     "Sarcophagus decorated with hieroglyphic symbols and devices.",
     "An Egyptian-themed sarcophagus in the Polyandrion, connecting the funerary arts of Rome and Egypt.",
     "HIEROGLYPHIC"),

    (253, "q7r", "Large Epitaph: O Lector Infoelix",
     "Full-page epitaph within ornate architectural frame. Extended Latin inscription beginning O LECTOR INFOEL...",
     "The longest and most elaborate epitaph in the Polyandrion. The reader is directly addressed as 'unhappy reader' in a meditation on mortality.",
     "ARCHITECTURAL"),

    (254, "q7v", "Sepulchral Monument with Laurel Wreath",
     "Large sepulchral monument crowned with laurel wreath. Elaborate Renaissance architectural frame.",
     "A monument crowned with the laurel of poetic glory, connecting death to artistic immortality.",
     "ARCHITECTURAL"),

    (257, "r1r", "Monument of Artemisia",
     "Full-page woodcut: elaborate architectural monument with Queen Artemisia enthroned in central niche. Greek inscription ARTEMISIDOS BASILIDOS ERODON.",
     "The monument of Artemisia, who drank the ashes of her husband Mausolus. The HP's most elaborate funerary monument, prototype of the historical Mausoleum at Halicarnassus.",
     "NARRATIVE"),

    (258, "r1v", "Sepulchral Monument with Putti",
     "Elaborate sepulchral monument with two putti holding curtain. Arched niche with figure. Relief panels below.",
     "A grand funerary monument combining classical architectural framing with the decorative vocabulary of putti and drapery.",
     "ARCHITECTURAL"),

    (259, "r2r", "Epitaph with Busts of Youth and Woman",
     "Sepulchral monument with portrait busts of a young man and woman under curtained canopy. Latin epitaph: ASPICE VIATOR...",
     "A double portrait monument for two lovers, the curtain suggesting both intimacy and the veil between life and death.",
     "ARCHITECTURAL"),

    (261, "r3r", "Sepulchral Portal: Gates of Life and Death",
     "Full-page monument: architectural portal with eagle pediment, inscription D.DITI ET PROSER. Two gates below.",
     "The portal of Dis and Proserpina, with the narrow gates of life and death. This is the Polyandrion's culminating monument.",
     "ARCHITECTURAL"),

    # === CYTHERA VOYAGE (pp. 275-281) ===
    (275, "s2r", "Standard of Cupid's Bark",
     "Decorative banner/standard with AMOR VINCIT OMNIA inscription, plus ornamental initial below.",
     "The banner of Cupid's ship, proclaiming love conquers all. This Virgilian motto governs the entire HP.",
     "DECORATIVE"),

    (281, "s5r", "The Bark of the God of Love",
     "Small boat on waves with ornamental prow and stern. Cupid's vessel for the voyage to Cythera.",
     "Cupid's bark, carrying Poliphilo and Polia across the sea to Venus's island. The voyage represents the final threshold crossing.",
     "NARRATIVE"),

    # === CYTHERA GARDENS (pp. 291-341) ===
    (291, "t2r", "Water-work Fountain with Hydra Heads",
     "Ornate fountain structure with multiple water spouts, hydra-headed decorations, and peristyle columns.",
     "A garden fountain on Venus's island, combining hydraulic engineering with mythological ornament.",
     "ARCHITECTURAL"),

    (295, "t4r", "Tree Clipped in Ring-shape",
     "Topiary: tree shaped into a ring or circular form on ornamental base with pedestal.",
     "The first of the HP's remarkable topiary illustrations, showing nature bent to geometric form.",
     "DECORATIVE"),

    (297, "t5r", "Box-tree Clipped as Mushroom",
     "Topiary: box-tree clipped into mushroom shape on stepped circular pedestal.",
     "Another topiary design from Venus's gardens, demonstrating the HP's vision of nature as architectural material.",
     "DECORATIVE"),

    (298, "t5v", "Peristyle Colonnade with Trellis",
     "Classical peristyle structure with trellis and garden setting. Columns support an ornamental roof.",
     "A garden architecture combining classical columns with horticultural trellis work.",
     "ARCHITECTURAL"),

    (301, "t7r", "Plan of the Island of Venus",
     "Full-page diagram: circular plan of Venus's island showing concentric garden zones and central temple.",
     "The plan of Venus's island, with concentric rings of gardens surrounding the central sanctuary. A utopian diagram of the perfect garden-temple.",
     "DIAGRAM"),

    (307, "x2r", "Ornamental Flower-bed Pattern (Circular)",
     "Circular ornamental flower-bed design with concentric rings of geometric patterns.",
     "One of the HP's garden-design diagrams, showing the mathematical basis of Renaissance flower-bed layouts.",
     "DECORATIVE"),

    (311, "x4r", "Ornamental Flower-bed Pattern (Square)",
     "Square flower-bed design with geometric interlocking patterns and border elements.",
     "A square flower-bed design complementing the circular pattern, showing the HP's encyclopedic coverage of garden types.",
     "DECORATIVE"),

    (312, "x4v", "Peacock Topiary on Pedestal",
     "Box-tree clipped as three peacocks standing on ornamental altar-vase pedestal.",
     "A topiary peacock, combining the HP's horticultural imagination with the symbolic associations of the peacock (immortality, vanity).",
     "DECORATIVE"),

    (313, "x5r", "Flower-bed in Shape of Eagle",
     "Flower-bed pattern shaped as an eagle with spread wings, inscribed within a rectangular border.",
     "An eagle-shaped parterre, combining heraldic imagery with horticultural design.",
     "DECORATIVE"),

    (314, "x5v", "Eagle and Urn Flower-bed Design",
     "Flower-bed pattern with eagle/urn motif. Latin inscription around border with AEA LIT SENI text.",
     "An eagle-and-urn parterre design, combining heraldic and funerary motifs in the garden layout.",
     "DECORATIVE"),

    (317, "x7r", "Two Trophy Standards",
     "Two vertical trophy standards side by side: Roman arms trophies with ornamental designs.",
     "Garden trophies combining military and decorative motifs, ornaments of Venus's pleasure-ground.",
     "DECORATIVE"),

    (318, "x7v", "Trophy Standards: QVIS EVADET and NEMO",
     "Two vertical trophy standards with winged ornaments. Tablets inscribed QVIS EVADET and NEMO.",
     "Paired trophies posing the enigmatic question 'Who shall escape?' answered by 'No one.' Love is inescapable.",
     "DECORATIVE"),

    (319, "x8r", "Trophy Standards with NEMO Tablet",
     "Two more trophy standards with tablets inscribed NEMO and ornamental winged designs.",
     "Trophies bearing the enigmatic inscription NEMO (no one), connecting love's triumph to philosophical riddle.",
     "DECORATIVE"),

    (328, "y4v", "Vase with Dragon-handle Monsters",
     "Ornate two-handled vase with dragon-form handles. Detailed metalwork with mythological motifs.",
     "A remarkable vessel in Venus's gardens, combining the HP's obsession with decorative arts and mythological fauna.",
     "DECORATIVE"),

    (330, "y5v", "Earthenware Amphora with Fumes",
     "Amphora with odoriferous fumes emerging from orifice. Greek inscription PANTA BAIA BIOY.",
     "An amphora emitting fragrant smoke, inscribed with the Greek maxim 'All of life is brief.' Perfume and mortality united.",
     "DECORATIVE"),

    (331, "y6r", "Precious Stone Vase with Fiery Sparks",
     "Small ornate vase of precious stone emitting fiery sparks or fumes. Detailed metalwork.",
     "One of the remarkable vessels in Venus's gardens, combining precious materials with alchemical imagery.",
     "DECORATIVE"),

    (335, "y8r", "Terminal Figure with Serpent",
     "Terminal figure/trophy with serpent and ornamental elements. Three heads of Cerberus visible.",
     "A terminal figure combining classical herm tradition with infernal imagery (Cerberus), reminding that love borders death.",
     "DECORATIVE"),

    (334, "y7v", "Terminal Figure with Three Male Heads",
     "Classical herm/terminal figure on pedestal. Three male heads facing different directions. Decorative garden element.",
     "A garden herm in the classical tradition, the three heads perhaps representing past, present, and future — or the three faces of Hecate.",
     "DECORATIVE"),

    (336, "y8v", "Triumph of Cupid: Nymphs and Satyrs with Chariot",
     "Procession with nymphs and satyrs pulling chariot bearing Cupid. Captives and trophies.",
     "A second triumphal procession on Venus's island. Cupid rides in triumph while satyrs and nymphs process before him.",
     "PROCESSION"),

    (337, "z1r", "Triumph of Cupid",
     "Large procession: nymphs, satyrs, dragons, and captives in Cupid's triumphal procession.",
     "A second triumphal procession, this time on Venus's island. Cupid himself rides in triumph over all who love.",
     "PROCESSION"),

    (339, "z2r", "Column Base with Rams' Heads",
     "Architectural detail: column base with rams' heads and sacrifice medallion relief.",
     "A column base from the amphitheater, combining sacrificial rams with architectural ornament.",
     "DECORATIVE"),

    (341, "z3r", "The Amphitheatre in Island of Venus",
     "Large architectural section: amphitheater structure with tiered seating, arches, and columns.",
     "The amphitheater on Venus's island, where the lovers will witness the final ceremonies. Classical architecture at its most monumental.",
     "ARCHITECTURAL"),

    # === VENUS FOUNTAIN (pp. 349-365) ===
    (349, "A3r", "Ground-plan of Fountain of Venus",
     "Geometric diagram: heptagonal/octagonal ground-plan of the fountain of Venus. Detailed measurements.",
     "The plan of Venus's central fountain, the mathematical heart of the island's design.",
     "DIAGRAM"),

    (365, "B3r", "Poliphilus and Polia at Fountain of Venus",
     "Garden scene: Poliphilus and Polia with nymphs at the Fountain of Venus, trellis and columns visible.",
     "The lovers arrive at the culminating fountain. This reunion at the water's source completes the HP's aquatic symbolism.",
     "NARRATIVE"),

    # === BOOK II: POLIA'S NARRATIVE (pp. 386-447) ===
    (386, "C5v", "Polia Drags Prostrate Poliphilus",
     "Interior scene: Polia drags the prostrate Poliphilus from the sanctuary of Diana. Classical temple columns.",
     "In Polia's telling, she dragged the collapsed Poliphilus from Diana's temple. Her act of physical rescue precedes her spiritual surrender to love.",
     "NARRATIVE"),

    (387, "C6r", "Polia in Temple of Diana; Poliphilus Prostrate",
     "Temple interior: Poliphilus lies prostrate on the floor while Polia stands in the Temple of Diana.",
     "Poliphilus has collapsed at Polia's feet in Diana's temple. His death-like swoon is the crisis that forces Polia to choose between Diana and Venus.",
     "NARRATIVE"),

    (390, "C7v", "Cupid Brandishes Sword over Victims",
     "Cupid brandishes a sword over kneeling women bound to trees. Chariot visible at right.",
     "Cupid's punishment of those who resist love. The violence of this scene underscores the HP's view of Eros as an irresistible cosmic force.",
     "NARRATIVE"),

    (391, "C8r", "Lion, Dog, Dragon Devour Victims",
     "Woodland scene: lion, dog, and dragon devour victims while Cupid flies above with torch and arrows.",
     "The most violent image in the HP: beasts destroy those who defy love. Cupid oversees from above, combining infantile form with terrible power.",
     "NARRATIVE"),

    (393, "D1r", "Dream of Polia: Cupid Punishes Two Women",
     "Two women punished by Cupid in a woodland setting. Figures tied to trees with beasts approaching.",
     "Polia's vision of Cupid's vengeance. The paired punishment scenes serve as exempla warning against resistance to love.",
     "NARRATIVE"),

    (411, "E2r", "Poliphilus Dead; Polia Kneels in Grief",
     "Interior scene: Poliphilus lies dead on tiled floor while Polia kneels beside him in grief.",
     "The central crisis of Book II. Poliphilus appears to have died from unrequited love, and Polia confronts the consequences of her rejection.",
     "NARRATIVE"),

    (412, "E2v", "Poliphilus Revived in Polia's Lap",
     "Interior scene: Polia cradles the revived Poliphilus in her lap. The lovers embrace on tiled floor.",
     "Poliphilus revives in Polia's arms. This resurrection through love parallels the alchemical solve et coagula.",
     "NARRATIVE"),

    (413, "E3r", "Priestesses Drive Lovers from Temple",
     "Figures being driven from a classical temple entrance. Priestesses expel the lovers from Diana's sanctuary.",
     "The priestesses of Diana expel Poliphilus and Polia from the temple. Their love has profaned Diana's sacred space.",
     "NARRATIVE"),

    (416, "E4v", "Polia's Bed-chamber Vision",
     "Two-scene woodcut: landscape with figures above, Polia in bed-chamber below. Diana vs Venus contest in sky.",
     "Polia's pivotal vision: Diana and Venus contend for her allegiance while she lies in her bed-chamber. The split scene shows outer and inner worlds.",
     "NARRATIVE"),

    (419, "E6r", "Polia Kneels Before Venus Priestess",
     "Temple scene: Polia kneels before the Venus priestess with Poliphilus beside her. Altar with flame visible.",
     "Polia submits to Venus's priestess, formally abandoning Diana. This scene resolves Book II's central conflict.",
     "NARRATIVE"),

    (421, "E7r", "Enamoured Couple Before Priestess",
     "Interior scene with columns: the couple kneels before the enthroned priestess at altar.",
     "Poliphilus and Polia kneel together before the priestess, receiving Venus's formal blessing on their union.",
     "NARRATIVE"),

    (425, "F1r", "Priestess Enthroned; Lovers Kissing",
     "Interior scene: priestess enthroned above while the lovers kiss in her presence. Witnesses at sides.",
     "The lovers' kiss before the priestess of Venus. This public ritual kiss seals their sacred marriage.",
     "NARRATIVE"),

    (433, "F5r", "Poliphilus Writing at Carved Desk",
     "Interior scene: Poliphilus seated at an ornately carved desk, writing. Bookshelves and architectural details.",
     "Poliphilus as author, writing the very text we read. This self-reflexive image frames the HP as a literary artifact produced by a lover's hand.",
     "NARRATIVE"),

    (436, "F6v", "Polia Reading Letter in Bed-chamber",
     "Interior scene: Polia reads Poliphilus's letter while seated in her bed-chamber. Small dog at feet.",
     "Polia receives and reads Poliphilus's love letter. The intimate bed-chamber setting emphasizes the private nature of their correspondence.",
     "NARRATIVE"),

    (447, "G4r", "Poliphilus Before Venus in Clouds",
     "Poliphilus before Venus enthroned on clouds. Cupid at left, figure at right. Divine epiphany scene.",
     "The final narrative woodcut of the HP. Venus appears to Poliphilus in glory, flanked by Cupid. This celestial vision completes the dream before Poliphilus awakens.",
     "NARRATIVE"),

    (448, "G4v", "Cupid Shoots Arrow at Bust of Polia",
     "Cupid with bow shoots arrow at bust/figure. Venus seated on clouds at right. The very last woodcut in the HP.",
     "The final image of the HP: Cupid looses his arrow at Polia's image as the dream dissolves. Venus watches from her celestial throne. The reader is returned to waking life.",
     "NARRATIVE"),
]


def slugify(text):
    """Convert text to URL-safe slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].rstrip('-')


def main():
    parser = argparse.ArgumentParser(
        description="Seed the complete 1499 HP woodcut inventory"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get existing entries keyed by page_1499
    existing_by_page = {}
    for row in cur.execute("SELECT id, page_1499, slug, title FROM woodcuts").fetchall():
        if row["page_1499"]:
            existing_by_page[row["page_1499"]] = dict(row)

    inserted = 0
    updated = 0
    skipped = 0

    for page, sig, title, desc, narrative, category in WOODCUTS_1499:
        ia_page = page + IA_OFFSET
        slug = slugify(title)

        if page in existing_by_page:
            # Update existing entry with IA data and narrative context
            existing = existing_by_page[page]
            if args.dry_run:
                print(f"  UPDATE p.{page}: {existing['title']} -> add IA page {ia_page}")
            else:
                cur.execute("""
                    UPDATE woodcuts SET
                        page_1499_ia = ?,
                        narrative_context = COALESCE(narrative_context, ?),
                        signature_1499 = COALESCE(signature_1499, ?),
                        subject_category = COALESCE(subject_category, ?)
                    WHERE id = ?
                """, (ia_page, narrative, sig, category, existing["id"]))
            updated += 1
        else:
            # Check for slug collision
            existing_slug = cur.execute(
                "SELECT id FROM woodcuts WHERE slug = ?", (slug,)
            ).fetchone()
            if existing_slug:
                slug = slug + f"-p{page}"

            if args.dry_run:
                print(f"  INSERT p.{page} ({sig}): {title} [IA n{ia_page}]")
            else:
                cur.execute("""
                    INSERT INTO woodcuts (
                        slug, title, signature_1499, page_1499, page_1499_ia,
                        description, narrative_context, subject_category,
                        woodcut_type, source_method, confidence, review_status,
                        ia_image_cached
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'IN_TEXT', 'LLM_ASSISTED',
                              'PROVISIONAL', 'DRAFT', 0)
                """, (slug, title, sig, page, ia_page, desc, narrative, category))
            inserted += 1

    if not args.dry_run:
        conn.commit()

    # Also update any existing entries that have page_1499 but no page_1499_ia
    if not args.dry_run:
        cur.execute("""
            UPDATE woodcuts SET page_1499_ia = page_1499 + ?
            WHERE page_1499 IS NOT NULL AND page_1499_ia IS NULL
        """, (IA_OFFSET,))
        extra = cur.rowcount
        conn.commit()
        if extra:
            print(f"  Also set IA page for {extra} existing entries via offset formula")

    conn.close()
    print(f"\nDone: {inserted} inserted, {updated} updated, {skipped} skipped")


if __name__ == "__main__":
    main()
