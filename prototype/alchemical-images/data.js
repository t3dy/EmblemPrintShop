// Complete Alchemical Images — Data
// Generated 2026-06-06. ~28 works from ancient through early modern.
// PART 1: Ancient + Medieval

const WORKS = [

// ═══════════════════════ PART I — ANCIENT ═══════════════════════

{
  id: "codex-marcianus",
  title: "Codex Marcianus gr. Z. 299",
  subtitle: "Chrysopoeia of Cleopatra — Ouroboros & Zosimos Diagrams",
  period: "ancient",
  date_display: "c. 3rd–4th century AD (10th–11th c. Byzantine copy)",
  date_sort: 350,
  author: "Cleopatra the Alchemist; Zosimos of Panopolis; Stephanus of Alexandria",
  medium: "Illuminated manuscript (parchment)",
  repository: "Biblioteca Nazionale Marciana, Venice",
  shelfmark: "MS Marciana gr. Z. 299 (coll. 584)",
  status: "needs_sourcing",
  priority: "critical",
  symbol: "♾",
  card_description: "The oldest known image of the ouroboros — a serpent biting its own tail encircling the text 'hen to pan' (the All is One) — appears on fol. 188v of this 10th-century Byzantine manuscript compendium. Alongside Zosimos's apparatus drawings, it is the founding visual document of Western alchemy, preserving images composed in Greek Egypt around 300 AD.",
  related: ["leiden-stockholm","aurora-consurgens","rosarium-1550"],
  images: [
    { id: "ouroboros-chrysopoeia", label: "Chrysopoeia of Cleopatra — Ouroboros", folio_or_plate: "fol. 188v", thumb_description: "Serpent biting its own tail encircling 'hen to pan' (the All is One). The earliest known ouroboros in the Western tradition, attributed to Cleopatra the Alchemist." },
    { id: "zosimos-kerotakis", label: "Zosimos — Kerotakis Apparatus", folio_or_plate: "fol. 21v", thumb_description: "Technical diagram of the kerotakis, a reflux apparatus for sulphuration of metals. Among the earliest surviving scientific illustrations in Western history." },
    { id: "zosimos-tribikos", label: "Zosimos — Tribikos Still", folio_or_plate: "fol. 22r", thumb_description: "The tribikos: a three-armed distillation still attributed in the text to Maria the Jewess, the legendary female alchemist." },
    { id: "zosimos-visions", label: "Zosimos — Vision of the Priest", folio_or_plate: "various folios", thumb_description: "Diagrammatic imagery accompanying Zosimos's visionary accounts of priests tortured and transformed — the earliest allegorical alchemical literature." }
  ],
  essay: {
    visual_description: `<p>The ouroboros on fol. 188v of the Codex Marcianus is drawn in a circular form: a serpent whose body forms a perfect ring, biting its own tail. Within the ring, the Greek inscription reads <em>ἓν τὸ πᾶν</em> (<em>hen to pan</em>, "the All is One") — the central maxim of Hellenistic alchemical philosophy. The serpent's body is divided by a horizontal line, the upper half dark, the lower light, encoding the dual nature of matter. Above the circle a second inscription identifies the serpent: "one is the serpent who has the poison." The composition is simple but charged: containment, cyclicity, and the unity of opposites made visible in a single line drawing.</p>
<p>The apparatus diagrams on surrounding folios are of a different character entirely: not symbolic but technical. The kerotakis is drawn as a vertical vessel with a perforated internal shelf, annotated with Greek labels for each component. Metals placed on the shelf are exposed to ascending vapors of sulphur or arsenic rising from heated material in the base compartment; the vapors condense on the metals and alter their surface color. The tribikos — three-armed still attributed to Maria the Jewess — appears as a cucurbit with three delivery tubes leading to three receiving vessels, a fundamental configuration in the history of distillation. These are working drawings, not decorations: they encode laboratory knowledge in the same manuscript that encodes metaphysical doctrine.</p>`,
    historical_context: `<p>The Codex Marcianus gr. Z. 299 is the single most important surviving compendium of Greek alchemical writing. It was compiled in Byzantium in the 10th or 11th century from texts composed between the 1st and 7th centuries AD, preserving authors otherwise known only in fragments: pseudo-Democritus (1st century AD), Zosimos of Panopolis (fl. c. 300 AD), Stephanus of Alexandria (early 7th century), Olympiodorus, Synesius, and the female alchemist Cleopatra. Without this manuscript, the Chrysopoeia attributed to Cleopatra would be entirely unknown.</p>
<p>Zosimos of Panopolis is the most significant author preserved in the manuscript. Writing in Greek Egypt around 300 AD, he was the first alchemist to produce systematic theoretical accounts of the art alongside practical recipes. His visionary texts — the "authentic memoirs" in which he dreams of priests being tortured, boiled, and transformed — establish the allegorical, spiritualizing reading of alchemical operations that would shape the entire subsequent tradition, Arabic and Latin as well as Greek. The apparatus diagrams embedded in his texts represent a remarkable double vision: they document real laboratory practice while insisting on the pneumatic (spiritual) significance of physical operations.</p>`,
    provenance: `<p>The manuscript was donated to the Republic of Venice in 1468 by Cardinal Bessarion (1403–1472), the Greek Byzantine scholar who fled Constantinople after its fall in 1453. Bessarion's gift of his entire library — the largest private collection of Greek manuscripts in the West at the time — to Venice established the Biblioteca Marciana as a major European scholarly institution. The Codex Marcianus gr. Z. 299 has remained in Venice since 1468. It was catalogued by early modern humanists interested in Hermeticism and was a source for some Renaissance natural philosophers, though it remained largely inaccessible to the broader scholarly world until modern critical editions. The manuscript is now available through the Biblissima IIIF portal.</p>`,
    alchemical_processes: `<p>The ouroboros encapsulates the alchemical doctrine of <em>solve et coagula</em> — the endless cycle of dissolution and reconstitution by which matter is purified toward perfection. The serpent consuming itself represents both the prima materia (which contains within itself the seed of its own transformation) and the cyclic character of the alchemical Work (which returns always to its starting point at a higher level). "The All is One" encodes the Stoic and Neoplatonic conviction that a single substance underlies apparent material multiplicity, and that alchemical operations reveal this unity by reducing things to their prima materia.</p>
<p>The apparatus diagrams address the physical mechanics of transformation. The kerotakis procedure — exposing metals to ascending sulphurous vapors — is the paradigmatic operation of early Greek alchemy: it produces a surface film on copper or lead that mimics the appearance of gold or silver. Zosimos frames this in terms of pneumatic transformation: the "spirit" (pneuma) or "tincture" of sulphur penetrates and alters the metal's nature, just as the divine spirit transforms the soul. Physical and spiritual registers are aspects of a single process, not separate domains.</p>`,
    scholarly_discussion: `<p>The foundational edition of the Marcianus texts is Marcellin Berthelot and Charles-Émile Ruelle, <em>Collection des anciens alchimistes grecs</em> (3 vols., 1887–1888), which provides Greek text, French translation, and reproductions of the apparatus diagrams. Michèle Mertens's critical edition in the Budé series (<em>Les alchimistes grecs</em>, vol. IV, 1995) provides the authoritative text and translation of the Zosimos "Authentic Memoirs." Jack Lindsay's <em>The Origins of Alchemy in Graeco-Roman Egypt</em> (1970) provides a literary and historical reading of the visionary texts. More recently, Karin Figala's work on alchemical symbolism and Matteo Martelli's studies of Greek alchemical recipes have advanced understanding of the practical and symbolic dimensions of these texts.</p>
<p>The attribution of the Chrysopoeia to "Cleopatra" has been debated: the scholarly consensus is that "Cleopatra" is a learned pseudonym (following the Hellenistic convention of attributing philosophical texts to famous women or divine figures) rather than the historical Cleopatra VII. Nonetheless, Adriana Turpin and others have argued for the existence of genuine female practitioners in the Hellenistic alchemical tradition, making the attribution historically suggestive even if literally false.</p>`
  },
  bibliography: [
    { citation: "Berthelot, Marcellin, and Charles-Émile Ruelle. <em>Collection des anciens alchimistes grecs</em>. 3 vols. Paris: Georges Steinheil, 1887–1888.", url: "" },
    { citation: "Mertens, Michèle. <em>Les alchimistes grecs</em>, vol. IV, pt. 1: Zosime de Panopolis, Mémoires authentiques. Paris: Les Belles Lettres, 1995.", url: "" },
    { citation: "Lindsay, Jack. <em>The Origins of Alchemy in Graeco-Roman Egypt</em>. London: Muller, 1970.", url: "" },
    { citation: "Principe, Lawrence M. <em>The Secrets of Alchemy</em>. Chicago: University of Chicago Press, 2013.", url: "" },
    { citation: "Obrist, Barbara. <em>Les débuts de l'imagerie alchimique (IXe–XVe siècles)</em>. Paris: Le Sycomore, 1982.", url: "" }
  ],
  links: [
    { label: "Biblissima IIIF Viewer — Marciana gr. Z. 299", url: "https://portail.biblissima.fr/ark:/43093/mdataf361a5cb77a866280bc1a1e50cf143dd8416e045", description: "Full manuscript viewer — all folios including fol. 188v" },
    { label: "Princeton Byzantine Sources — MS description", url: "https://byzantine.lib.princeton.edu/byzantine/manuscripts/30390", description: "Scholarly catalog entry with bibliography" },
    { label: "Cleopatra the Alchemist — Wikipedia", url: "https://en.wikipedia.org/wiki/Cleopatra_the_Alchemist", description: "Biographical and bibliographic summary" },
    { label: "Zosimos of Panopolis — Wikipedia", url: "https://en.wikipedia.org/wiki/Zosimos_of_Panopolis", description: "Overview of the most important Greek alchemical author" }
  ]
},

{
  id: "leiden-stockholm",
  title: "Leiden Papyrus X & Stockholm Papyrus",
  subtitle: "The Oldest Surviving Alchemical Workshop Texts",
  period: "ancient",
  date_display: "Late 3rd – early 4th century AD",
  date_sort: 300,
  author: "Anonymous (Greek, Theban provenance)",
  medium: "Papyrus (no images — workshop text documents)",
  repository: "Rijksmuseum van Oudheden, Leiden (P. Leid. I 397); Kungliga Biblioteket, Stockholm (P. Gr. Holm.)",
  shelfmark: "P. Leid. I 397; Papyrus Graecus Holmiensis",
  status: "needs_sourcing",
  priority: "medium",
  symbol: "☿",
  card_description: "The oldest surviving alchemical texts in the Western tradition: 111 Greek recipes for imitating gold and silver (Leiden) and 154 recipes for dyeing textiles and imitating gems (Stockholm). Discovered together near Thebes c. 1828. Both are workshop manuals without illustrations — but they document the practical metallurgical foundation from which all later symbolic alchemy grew, showing what alchemists actually did before the allegorical tradition obscured laboratory practice.",
  related: ["codex-marcianus"],
  images: [
    { id: "leiden-photo", label: "Leiden Papyrus X — Physical Document", folio_or_plate: "P. Leid. I 397", thumb_description: "Photograph of the papyrus scroll showing Greek uncial script with numbered recipes for metallurgical imitation of gold and silver." }
  ],
  essay: {
    visual_description: `<p>The Leiden Papyrus X and Stockholm Papyrus contain no alchemical images — no diagrams, symbols, or pictorial content of any kind. They are workshop manuals: columns of Greek text, with recipes numbered in sequence on papyrus sheets joined end to end. Any visual record is a photograph of the physical artifact itself, which is the documentary object of interest. The Leiden papyrus (approximately 23 × 29 cm) is in good preservation relative to its age, with legible text throughout. The Stockholm papyrus is similarly preserved.</p>
<p>Their inclusion here is as historical foundation: they represent the practical, material base of alchemical practice before the allegorical and symbolic apparatus of the Hellenistic philosophical tradition had developed. To understand what the ouroboros of the Codex Marcianus <em>means</em> — the philosophical claims it encodes — requires understanding the laboratory practices that the Leiden papyrus documents directly.</p>`,
    historical_context: `<p>The two papyri were discovered together near Thebes (Luxor) around 1828, part of a cache of documents sold by the Swedish-Norwegian diplomat Johan d'Anastasy to European institutions. The Leiden papyrus went to the Rijksmuseum van Oudheden; the Stockholm to the Royal Library of Sweden. They are twin documents from the same provenance and period, possibly from the same workshop or practitioner's estate.</p>
<p>The Leiden papyrus contains 111 recipes: procedures for purifying gold and silver alloys, producing surface coatings on base metals that imitate gold or silver, testing metal purity with touchstone or fire, producing colored glass imitating gems, and various dyeing operations. The Stockholm papyrus focuses more heavily on textile dyeing and gem imitation (154 recipes). Together they reveal a sophisticated metallurgical and chemical practice in late Roman Egypt — practical rather than mystical, but employing the same mercury-sulphur manipulations that later alchemical philosophy would theorize.</p>`,
    provenance: `<p>The Leiden papyrus entered the Rijksmuseum van Oudheden in 1829 and was first edited and translated by Conrad Leemans in 1885. The Stockholm papyrus was edited by Otto Lagercrantz in 1913. Both are now catalogued in the Trismegistos database (Leiden: TM 61300). The Rijksmuseum has made collection photographs available online. Neither papyrus is illustrated, but artifact photographs document the physical objects.</p>`,
    alchemical_processes: `<p>The Leiden papyrus is significant precisely because it documents alchemy before philosophical elaboration. Recipe 8, for example, describes producing a tin-mercury amalgam that resembles silver on the surface; Recipe 51 describes gilding bronze with copper sulfate, alum, salt, and vinegar. These are real chemical procedures producing real (if temporary) effects. The later allegorical tradition — the "marriage of Sol and Luna" in the Rosarium Philosophorum, the "coniunctio" of the Aurora Consurgens — is, at one level of reading, a symbolic encoding of procedures like these. The Leiden papyrus shows us the laboratory substrate before the symbolic superstructure was built.</p>`,
    scholarly_discussion: `<p>Robert Halleux's <em>Les alchimistes grecs</em>, vol. I (1981) provides the authoritative modern edition of the Leiden papyrus with French translation. Halleux argues that practical metallurgy of the Leiden type is the material base from which Greek alchemical philosophy subsequently developed — not a corruption of an originally pure spiritual tradition, but the root from which the philosophical tree grew. Lawrence Principe's <em>The Secrets of Alchemy</em> (2013) makes the analogous argument for the early modern period, showing that even the most elaborate symbolic alchemical texts of the 17th century encode real laboratory operations.</p>`
  },
  bibliography: [
    { citation: "Halleux, Robert. <em>Les alchimistes grecs</em>, vol. I: Papyrus de Leyde, Papyrus de Stockholm. Paris: Les Belles Lettres, 1981.", url: "" },
    { citation: "Leemans, Conrad. <em>Papyrus Graecus Leidensis</em>. Leiden: Brill, 1885.", url: "" },
    { citation: "Lagercrantz, Otto. <em>Papyrus Graecus Holmiensis</em>. Uppsala: Almqvist & Wiksell, 1913.", url: "" },
    { citation: "Principe, Lawrence M. <em>The Secrets of Alchemy</em>. Chicago: University of Chicago Press, 2013.", url: "" }
  ],
  links: [
    { label: "Leiden Papyrus X — Trismegistos database (TM 61300)", url: "https://www.trismegistos.org/text/61300", description: "Catalog record with full bibliography" },
    { label: "Rijksmuseum van Oudheden collection search", url: "https://www.rmo.nl/en/collection/", description: "National Museum of Antiquities, Leiden — artifact photographs" }
  ]
},

// ═══════════════════════ PART II — MEDIEVAL ═══════════════════════

{
  id: "aurora-consurgens",
  title: "Aurora Consurgens",
  subtitle: "Zürich Zentralbibliothek Ms. Rh. 172 — 38 Miniatures",
  period: "medieval",
  date_display: "c. 1420 (Zürich MS); other copies through late 15th century",
  date_sort: 1420,
  author: "Attributed to Thomas Aquinas (pseudepigraphal); actual author unknown",
  medium: "Illuminated manuscript on parchment; 100 folios, 38 miniatures",
  repository: "Zentralbibliothek Zürich",
  shelfmark: "Ms. Rh. 172",
  status: "partial",
  priority: "critical",
  symbol: "☀",
  card_image: "https://www.e-codices.unifr.ch/loris/zbz/zbz-Ms-Rh-0172/zbz-Ms-Rh-0172_005.jp2/full/400,/0/default.jpg",
  card_description: "Thirty-eight historiated miniatures illuminate this 15th-century alchemical treatise framed as a dialogue between the soul and divine Wisdom drawn from the Song of Songs. The images — Sapientia in her bath, Sol and Luna in conjunction, the philosophical tree, the dragon consuming itself — form the most ambitious illuminated image cycle in all of medieval alchemy. Fully digitized on e-codices.unifr.ch via IIIF.",
  related: ["rosarium-1550","splendor-solis-bl","donum-dei","buch-dreifaltigkeit"],
  images: [
    { id: "aurora-sapientia-bath", label: "Sapientia in the Bath", folio_or_plate: "fol. 2r",
      src: "https://www.e-codices.unifr.ch/loris/zbz/zbz-Ms-Rh-0172/zbz-Ms-Rh-0172_005.jp2/full/400,/0/default.jpg",
      attribution: "e-codices / ZBZ — CC BY-NC 4.0",
      thumb_description: "A crowned woman immersed in a circular bath, attended by handmaidens — Wisdom (Sapientia) as the prima materia, the opening image of the Aurora Consurgens cycle." },
    { id: "aurora-conjunction", label: "Sol and Luna Conjunction", folio_or_plate: "fol. 13r",
      src: "https://www.e-codices.unifr.ch/loris/zbz/zbz-Ms-Rh-0172/zbz-Ms-Rh-0172_027.jp2/full/400,/0/default.jpg",
      attribution: "e-codices / ZBZ — CC BY-NC 4.0",
      thumb_description: "The sun and moon personified as crowned monarchs, their hands joined — the coniunctio oppositorum at the heart of the alchemical Work." },
    { id: "aurora-red-king-white-queen", label: "Red King & White Queen", folio_or_plate: "fol. 19v",
      src: "https://www.e-codices.unifr.ch/loris/zbz/zbz-Ms-Rh-0172/zbz-Ms-Rh-0172_040.jp2/full/400,/0/default.jpg",
      attribution: "e-codices / ZBZ — CC BY-NC 4.0",
      thumb_description: "Red king and white queen facing each other with orb and sceptre — the royal marriage of sulphur and mercury before final conjunction." },
    { id: "aurora-dragon", label: "Dragon Consuming Itself", folio_or_plate: "fol. 30v", thumb_description: "A dragon consuming its own tail — the self-consuming prima materia, a variant of the ouroboros motif representing the nigredo." },
    { id: "aurora-seven-women", label: "The Seven Wise Women", folio_or_plate: "fol. 36r", thumb_description: "Seven female figures personifying the seven stages of the alchemical Work, each associated with a planet and its metal." },
    { id: "aurora-resurrection", label: "Resurrection Figure", folio_or_plate: "fol. 44r", thumb_description: "A figure rising from a tomb or vessel — the final resurrection of the Stone, the rubedo completing the Work." }
  ],
  essay: {
    visual_description: `<p>The thirty-eight miniatures of the Zürich Aurora Consurgens represent the most coherent and visually sophisticated illuminated program in medieval alchemical manuscripts. The opening image shows a crowned woman — Sapientia, divine Wisdom — immersed in a circular bath, attended by handmaidens. The bath is simultaneously a vessel of dissolution (the prima materia placed in the alchemical flask), a ritual bath of purification, and the sacred fountain of the Song of Songs. The woman's crown marks her as royal and divine; the circular form of the bath mirrors the circular alchemical vessel.</p>
<p>The conjunction miniatures show Sol and Luna as crowned monarchs facing one another, their hands joined in a gesture that simultaneously evokes the secular marriage handclasp and the liturgical gesture of the mass. In other miniatures, the sun and moon appear as golden and silver discs carried by winged figures, or as radiant eyes within a human face. The philosophical tree, rooted in a circular alembic, bears flowers of gold and silver simultaneously — the two perfections united in a single growth. Throughout, the illuminator works with a concentrated palette — deep blue, vermillion, ochre, and gold leaf — to produce images of intense symbolic compression. The dragon consuming itself on fol. 30v is one of the finest medieval renderings of the ouroboros motif.</p>`,
    historical_context: `<p>The <em>Aurora Consurgens</em> ("The Rising Dawn") takes its title from its opening words, drawn from the Song of Songs: <em>Aurora consurgens in montibus sicut columna fumi</em> ("The dawn rising in the mountains like a pillar of smoke"). The entire text is a prolonged allegorical reading of the Song of Songs in alchemical terms: the beloved calling to her lover in the night is Sapientia/Alchemical Wisdom, and the search for her is the search for the Philosopher's Stone. This fusion of biblical erotic poetry with alchemical allegory represents a distinctive medieval synthesis with no direct precedent in the Greek tradition.</p>
<p>The attribution to Thomas Aquinas (1225–1274) is certainly pseudepigraphal — the text was composed considerably later, probably in the late 14th or early 15th century, and Aquinas's genuine philosophical writings show no interest in alchemy. The attribution served to give the work unimpeachable theological authority. The Zürich manuscript (Ms. Rh. 172) dates to approximately 1420 and is the oldest and most lavishly illuminated of nine known manuscripts. It was produced in the region of St. Gallen and came to the Zentralbibliothek Zürich from Rheinau Abbey.</p>`,
    provenance: `<p>Ms. Rh. 172 was held at Rheinau Abbey on the Rhine near Schaffhausen for several centuries as part of the monastic library. The Rheinau collection was secularized and transferred to the Zentralbibliothek Zürich in the early 19th century following the dissolution of Swiss monasteries in the revolutionary period. The manuscript is now among the crown jewels of the ZBZ's medieval holdings. It has been fully digitized through the e-codices project and is available through IIIF with a complete Mirador viewer at e-codices.unifr.ch.</p>`,
    alchemical_processes: `<p>The Aurora Consurgens encodes the full sequence of the alchemical <em>opus</em> in the language of mystical eros drawn from the Song of Songs. The prima materia is the "sleeping beloved" — unformed, dark, chaotic, yet containing within herself the seed of perfection. The nigredo (blackening, putrefaction) is her descent into the bath of dissolution. The albedo (whitening, purification) is her emergence transformed and clarified. The rubedo (reddening, perfection) is the marriage: the union of purified solar and lunar principles producing the red Stone, called here the "beloved who has found her rest." Each miniature marks a stage in this sequence, providing a visual guide to the <em>opus</em> that can be followed even without reading the Latin text.</p>`,
    scholarly_discussion: `<p>The standard modern study is Marie-Louise von Franz, <em>Aurora Consurgens: A Document Attributed to Thomas Aquinas on the Problem of Opposites in Alchemy</em> (1966), which provides translation, commentary, and Jungian psychological interpretation — reading the text as a symbolic representation of psychological individuation. Barbara Obrist's <em>Les débuts de l'imagerie alchimique</em> (1982) provides the most rigorous art-historical analysis of the miniatures in their medieval context. Leah DeVun's <em>Prophecy, Alchemy, and the End of Time</em> (2009) examines the theological dimensions and the relationship to apocalyptic traditions. Stanton Linden's survey of alchemical imagery provides useful comparative material.</p>`
  },
  bibliography: [
    { citation: "Von Franz, Marie-Louise. <em>Aurora Consurgens: A Document Attributed to Thomas Aquinas on the Problem of Opposites in Alchemy</em>. New York: Pantheon, 1966.", url: "" },
    { citation: "Obrist, Barbara. <em>Les débuts de l'imagerie alchimique (IXe–XVe siècles)</em>. Paris: Le Sycomore, 1982.", url: "" },
    { citation: "DeVun, Leah. <em>Prophecy, Alchemy, and the End of Time</em>. New York: Columbia University Press, 2009.", url: "" },
    { citation: "Jung, C.G. <em>Mysterium Coniunctionis</em>. Collected Works, vol. 14. Princeton: Princeton University Press, 1963.", url: "" },
    { citation: "Abraham, Lyndy. <em>A Dictionary of Alchemical Imagery</em>. Cambridge: Cambridge University Press, 1998.", url: "" }
  ],
  links: [
    { label: "e-codices — Full digital facsimile (IIIF)", url: "https://www.e-codices.unifr.ch/en/searchresult/list/one/zbz/Ms-Rh-0172", description: "Complete high-resolution scan — all 100 folios with 38 miniatures" },
    { label: "Europeana record", url: "https://www.europeana.eu/en/item/9200211/en_list_one_zbz_Ms_Rh_0172", description: "Aggregated metadata and image access" },
    { label: "Internet Archive facsimile edition", url: "https://archive.org/details/AuroraConsurgens", description: "Facsimile publication" },
    { label: "Aurora consurgens — Wikipedia", url: "https://en.wikipedia.org/wiki/Aurora_consurgens", description: "Overview with MS census and bibliography" }
  ]
},

{
  id: "ripley-scroll",
  title: "The Ripley Scroll",
  subtitle: "A Continuous Visual Narrative of the Alchemical Work",
  period: "medieval",
  date_display: "Attributed c. 1490 (Ripley); surviving copies late 16th – early 17th century",
  date_sort: 1490,
  author: "Attributed to George Ripley (c. 1415–1490), Canon of Bridlington",
  medium: "Manuscript scroll (parchment or vellum), up to 6 meters × 50 cm",
  repository: "Bodleian Library, Oxford (MS. Bodl. Rolls 1); British Library (Add. MS 5025 — 4 copies); Wellcome Collection (2 copies)",
  shelfmark: "MS. Bodl. Rolls 1 (Bodleian); Add. MS 5025 (BL)",
  status: "partial",
  priority: "critical",
  symbol: "🜂",
  card_image: "https://cdm16003.contentdm.oclc.org/iiif/2/p15150coll7:30526/0,0,2978,4000/400,/0/default.jpg",
  card_description: "A single continuous scroll, up to six meters long, depicting the entire alchemical Work as an unbroken visual narrative: a crowned toad bled by three serpents, the Green Lion swallowing the sun, the pelican feeding her young with her own blood, the ouroboros containing a king, and the phoenix rising in flames. Twenty-three to twenty-eight copies survive in major libraries. No other alchemical work uses the continuous scroll format.",
  related: ["aurora-consurgens","rosarium-1550","flamel-figures","buch-dreifaltigkeit"],
  images: [
    { id: "ripley-top-section", label: "Opening Section — Toad, Serpents, Ouroboros", folio_or_plate: "Top of scroll",
      src: "https://cdm16003.contentdm.oclc.org/iiif/2/p15150coll7:30526/0,0,2978,4000/400,/0/default.jpg",
      attribution: "Huntington Library, HM 30313 — Public domain",
      thumb_description: "The opening section of the Huntington copy: crowned toad at top, flanked by serpents; circular medallions with the ouroboros and other symbols below." },
    { id: "ripley-mid-section", label: "Middle Section — Green Lion, Pelican, King", folio_or_plate: "Mid-scroll",
      src: "https://cdm16003.contentdm.oclc.org/iiif/2/p15150coll7:30526/0,7000,2978,4000/400,/0/default.jpg",
      attribution: "Huntington Library, HM 30313 — Public domain",
      thumb_description: "The middle section: the green lion devouring the sun, the pelican vessel, and the crowned king within the work." },
    { id: "ripley-lower-section", label: "Lower Section — Phoenix, Completion", folio_or_plate: "Lower scroll",
      src: "https://cdm16003.contentdm.oclc.org/iiif/2/p15150coll7:30526/0,14000,2978,4000/400,/0/default.jpg",
      attribution: "Huntington Library, HM 30313 — Public domain",
      thumb_description: "The lower section approaching the completion: the phoenix rising from flames and the final emblematic figures of the red stone." },
    { id: "ripley-full-scroll", label: "Full Scroll (reduced)", folio_or_plate: "Complete",
      src: "https://cdm16003.contentdm.oclc.org/iiif/2/p15150coll7:30526/full/80,/0/default.jpg",
      attribution: "Huntington Library, HM 30313 — Public domain",
      thumb_description: "The complete scroll reduced to thumbnail scale — an elongated vertical composition showing the full arc of the alchemical work from prima materia to completion." }
  ],
  essay: {
    visual_description: `<p>The Ripley Scroll is unique in alchemical visual culture: a single continuous sheet of parchment or vellum, typically between four and six meters in length and approximately fifty centimeters wide, on which the entire alchemical Work is depicted as an unbroken visual sequence running from top to bottom. There are no chapter divisions, no text panels interrupting the image flow — only the images themselves, arranged in a sustained visual logic that must be read as a journey. In the finest copies, the color is vivid: the crowned toad is purple-black against an earthy ground; the green lion blazes in emerald; the phoenix burns in crimson and gold against a stippled background of architectural framing.</p>
<p>The consistent visual program moves through five major image zones: (1) the crowned toad bled by three serpents at the head of the scroll; (2) a sequence of roundels containing vessels in various stages of heating over furnaces; (3) the green lion swallowing the solar disc; (4) the pelican bird with the pelican-vessel; (5) a sequence of ouroboros formations containing various figures; and (6) at the scroll's base, the phoenix. Flanking the images are verses — either Ripley's own "Compound of Alchymie" or variant texts — that gloss each stage. The physical act of unrolling the scroll to reveal the next stage enacts the temporal progress of the Work itself.</p>`,
    historical_context: `<p>George Ripley (c. 1415–1490) was an Augustinian canon at Bridlington Priory in Yorkshire, the most celebrated English alchemist of the 15th century. His major written work, the <em>Compound of Alchymie</em> (1471, dedicated to King Edward IV), presented the alchemical <em>opus</em> in twelve "gates." None of the surviving scrolls is contemporaneous with Ripley; all known copies date from the late 16th or early 17th century, when Elizabethan and Jacobean England saw an intensification of interest in the native English alchemical tradition. The association of the scroll with Ripley's name gave it authority, but the visual program may have developed independently of the written <em>Compound</em>.</p>
<p>The scroll format — unique to English alchemical manuscripts — may reflect specifically English illuminated manuscript traditions: the genealogical roll, the chronicle scroll. Adapted to alchemical purposes, it allows the Work to be experienced as a literal unfolding: the practitioner unrolls the scroll as the Work proceeds, using the images as a temporal guide. The British Library holds seven copies; the Bodleian five; the Wellcome two; others are at Edinburgh, Cambridge, and in private collections.</p>`,
    provenance: `<p>The Bodleian's MS. Bodl. Rolls 1 is among the finest surviving copies, with vivid coloring and careful execution, acquired by the Bodleian in the 17th century. The British Library's Add. MS 5025 contains four copies acquired at various dates. Both institutions have digitized their holdings: Digital Bodleian provides a full IIIF viewer for MS. Bodl. Rolls 1; the British Library announced digitization of Add. MS 5025 in 2014. The Wellcome Collection holds two partially digitized copies. Conservation challenges are significant: the vellum curls when unrolled, and joins between sections are vulnerable to water damage.</p>`,
    alchemical_processes: `<p>The Ripley Scroll encodes the operations of the Work in a systematic visual vocabulary unique to the English tradition. The crowned toad represents the prima materia in its most debased, earthly state — a creature of earth and water (toad) with nonetheless royal potential (crown). The three serpents bleeding it correspond to the three Paracelsian principles — sulphur, mercury, and salt — whose separation and purification begin the Work. The green lion swallowing the sun is the dissolution of gold in vitriol (sulfuric acid), producing the green color signaling the first stage. The pelican-vessel, named after the bird's self-wounding gesture, is the alembic in which distillate is fed back into the flask for redistillation — the "circulation" essential to purification. The phoenix represents the principle that matter must be utterly destroyed before reconstituting in a higher form: destruction is not failure but prerequisite.</p>`,
    scholarly_discussion: `<p>Jennifer Rampling's <em>The Experimental Fire: Inventing English Alchemy, 1300–1700</em> (2020) is the most recent and rigorous scholarly treatment, situating the scroll within English laboratory practice and showing that its imagery encodes specific procedures being actively practiced in the Elizabethan period. Stanton Linden's <em>Darke Hierogliphicks</em> (1996) provides the broader literary-historical context of English alchemy. Lawrence Principe's work on alchemical practice and Barbara Obrist's iconographic analyses provide the comparative material needed to assess the scroll's relationship to continental traditions.</p>`
  },
  bibliography: [
    { citation: "Rampling, Jennifer M. <em>The Experimental Fire: Inventing English Alchemy, 1300–1700</em>. Chicago: University of Chicago Press, 2020.", url: "" },
    { citation: "Linden, Stanton J. <em>Darke Hierogliphicks: Alchemy in English Literature from Chaucer to the Restoration</em>. Lexington: University Press of Kentucky, 1996.", url: "" },
    { citation: "Jung, C.G. <em>Psychology and Alchemy</em>. Collected Works, vol. 12. Princeton: Princeton University Press, 1953.", url: "" },
    { citation: "Obrist, Barbara. <em>Les débuts de l'imagerie alchimique</em>. Paris: Le Sycomore, 1982.", url: "" },
    { citation: "Roob, Alexander. <em>Alchemy and Mysticism</em>. Cologne: Taschen, 1997.", url: "" }
  ],
  links: [
    { label: "Digital Bodleian — MS. Bodl. Rolls 1 (IIIF)", url: "https://digital.bodleian.ox.ac.uk/objects/a7764355-8fe8-4e6b-af28-ce6e5e225c70/", description: "Full IIIF facsimile of the Bodleian copy" },
    { label: "British Library — 'Art and Alchemy' blog post", url: "https://blogs.bl.uk/digitisedmanuscripts/2014/06/art-and-alchemy.html", description: "Announcing digitization of Add MS 5025" },
    { label: "George Ripley — Wikipedia", url: "https://en.wikipedia.org/wiki/George_Ripley_(alchemist)", description: "Biographical overview with bibliography" }
  ]
},

{
  id: "buch-dreifaltigkeit",
  title: "Buch der Heiligen Dreifaltigkeit",
  subtitle: "Book of the Holy Trinity — The First German Alchemical Manuscript",
  period: "medieval",
  date_display: "c. 1410–1419 (archetype); copies through c. 1492",
  date_sort: 1415,
  author: "Frater Ulmannus (Franciscan friar, active c. 1410–1420)",
  medium: "Illuminated manuscript; Middle High German (paper and parchment)",
  repository: "Bayerische Staatsbibliothek, Munich (Cgm 598 — DIGITIZED); SLUB Dresden (Mscr.Dresd.N.110); Universitätsbibliothek Heidelberg (Cpg 843)",
  shelfmark: "Cgm 598 (BSB Munich); Mscr.Dresd.N.110 (SLUB); Cpg 843 (Heidelberg)",
  status: "partial",
  priority: "high",
  symbol: "✦",
  card_image: "https://api.digitale-sammlungen.de/iiif/image/v2/bsb00016775_00008/full/400,/0/default.jpg",
  card_description: "The earliest German alchemical manuscript, composed c. 1410–1419 by a Franciscan friar who systematically mapped the alchemical Work onto Christ's Passion: the nigredo is the Crucifixion, the albedo the Resurrection, the rubedo the Second Coming. Its images — hermaphroditic Christ-figures, alchemical Trinity diagrams, symbolic trees — are without parallel in the entire tradition. The BSB Munich Cgm 598 copy is fully digitized (377 pages).",
  related: ["aurora-consurgens","donum-dei","rosarium-1550"],
  images: [
    { id: "dreifaltigkeit-trinity", label: "Alchemical Trinity Diagram", folio_or_plate: "Cgm 598, fol. 1r",
      src: "https://api.digitale-sammlungen.de/iiif/image/v2/bsb00016775_00008/full/400,/0/default.jpg",
      attribution: "BSB Munich, Cgm 598 — CC BY-NC-SA 4.0",
      thumb_description: "A diagrammatic image equating the Christian Trinity (Father, Son, Holy Spirit) with the alchemical triad of sulphur, mercury, and salt." },
    { id: "dreifaltigkeit-rebis", label: "The Rebis — Christ as Hermaphrodite", folio_or_plate: "Cgm 598, fol. 8v",
      src: "https://api.digitale-sammlungen.de/iiif/image/v2/bsb00016775_00022/full/400,/0/default.jpg",
      attribution: "BSB Munich, Cgm 598 — CC BY-NC-SA 4.0",
      thumb_description: "A hermaphroditic figure combining male and female elements, identified simultaneously with the resurrected Christ and the perfected Philosopher's Stone." },
    { id: "dreifaltigkeit-crucifixion", label: "Alchemical Crucifixion", folio_or_plate: "Cgm 598, fol. 15r",
      src: "https://api.digitale-sammlungen.de/iiif/image/v2/bsb00016775_00036/full/400,/0/default.jpg",
      attribution: "BSB Munich, Cgm 598 — CC BY-NC-SA 4.0",
      thumb_description: "Christ on the cross, with blood from the wounds flowing into an alchemical vessel — the Passion as the nigredo, the beginning of the Work." },
    { id: "dreifaltigkeit-tree", label: "Philosophical Tree of Metals", folio_or_plate: "Cgm 598, fol. 22v",
      src: "https://api.digitale-sammlungen.de/iiif/image/v2/bsb00016775_00051/full/400,/0/default.jpg",
      attribution: "BSB Munich, Cgm 598 — CC BY-NC-SA 4.0",
      thumb_description: "A symbolic tree whose roots are the four elements and whose branches bear the seven metals, a cosmological diagram unique to this text." }
  ],
  essay: {
    visual_description: `<p>The Buch der Heiligen Dreifaltigkeit is the most theologically daring work in the entire alchemical visual tradition. Its images do not merely use Christian iconography as decoration but identify alchemical operations with the central events of Christian salvation history. A central image shows Christ crucified, with blood from his wounds flowing directly into an alchemical vessel placed at the foot of the cross: the Passion becomes literally the nigredo — the blackening and dissolution of the prima materia. The vessel receives divine blood as the alchemist's flask receives the dissolved metal.</p>
<p>In another key image, the resurrected Christ stands in the posture of the Rebis — the hermaphroditic figure that combines male and female, solar and lunar, gold and silver principles in a single perfected body. The Christ-Rebis carries both the solar nimbus and the lunar crescent; the wounds of the Passion have become the rubedo's red marks. The Trinity diagram renders the three divine persons as geometric forms whose intersection produces the lapis philosophorum. These images require the viewer to hold two interpretive registers simultaneously: Christian theology and alchemical philosophy are not merely analogous but identical.</p>`,
    historical_context: `<p>Frater Ulmannus composed the Buch der Heiligen Dreifaltigkeit around 1410–1419, making it the earliest known German alchemical text. The context was the Council of Constance (1414–1418), at which the Franciscan order was deeply embroiled in debates about poverty and apostolic life. Ulmannus may have hoped to present his synthesis at the Council as a demonstration that alchemy was not a pagan or demonic art but a divinely ordained process mirroring God's redemptive work in creation. By mapping the Work onto the Passion, he gave alchemy a theological legitimacy it would thereafter claim throughout the early modern period.</p>`,
    provenance: `<p>The archetype manuscript (Kupferstichkabinett Berlin, Cod. 78 A 11, c. 1410–1419) has not been confirmed as publicly digitized. The BSB Munich Cgm 598 (after 1467, Franconian; 377 pages) is the primary digitized source and is available in full at digitale-sammlungen.de. The SLUB Dresden copy (Mscr.Dresd.N.110, 1492) and the Heidelberg copy (Cpg 843) are also digitized. The Handschriftencensus provides a complete census of all known manuscripts.</p>`,
    alchemical_processes: `<p>Ulmannus's schema maps the full alchemical <em>opus</em> onto the Passion narrative: the arrest and trial of Christ correspond to the preparation and purification of the prima materia; the Crucifixion and entombment correspond to the nigredo (putrefaction, blackening); the Harrowing of Hell corresponds to the separation and clarification of the dissolved material; the Resurrection corresponds to the albedo (whitening, first perfection); and the Second Coming corresponds to the rubedo (reddening), the completed red Stone. This gives alchemy an explicitly soteriological character: the alchemist participates in the ongoing redemption of matter, completing at the physical level what Christ accomplished at the spiritual.</p>`,
    scholarly_discussion: `<p>Barbara Obrist's <em>Les débuts de l'imagerie alchimique</em> (1982) provides the most thorough analysis of the Buch der Heiligen Dreifaltigkeit images in their medieval iconographic context. Leah DeVun's <em>Prophecy, Alchemy, and the End of Time</em> (2009) examines the apocalyptic dimension — the mapping of the alchemical Work onto eschatological history. The Handschriftencensus entry (handschriftencensus.de/6184) maintains the authoritative census of all MSS. Lawrence Principe's and William Newman's broader work on the history of alchemy provides context for understanding the social and institutional position of Ulmannus's theological synthesis.</p>`
  },
  bibliography: [
    { citation: "Obrist, Barbara. <em>Les débuts de l'imagerie alchimique</em>. Paris: Le Sycomore, 1982.", url: "" },
    { citation: "DeVun, Leah. <em>Prophecy, Alchemy, and the End of Time</em>. New York: Columbia University Press, 2009.", url: "" },
    { citation: "Priesner, Claus, and Karin Figala, eds. <em>Alchemie: Lexikon einer hermetischen Wissenschaft</em>. Munich: C.H. Beck, 1998.", url: "" },
    { citation: "Linden, Stanton J. <em>Darke Hierogliphicks</em>. Lexington: University Press of Kentucky, 1996.", url: "" }
  ],
  links: [
    { label: "BSB Munich Cgm 598 — Full digitization (377 pages)", url: "https://www.digitale-sammlungen.de/en/view/bsb00016775", description: "Complete digital facsimile — the primary accessible copy" },
    { label: "SLUB Dresden — Mscr.Dresd.N.110 (1492)", url: "https://digital.slub-dresden.de/en/workview/dlf/5987/1", description: "1492 copy, fully digitized" },
    { label: "Heidelberg — Cpg 843", url: "https://digi.ub.uni-heidelberg.de/diglit/cpg843", description: "Heidelberg digitized copy" },
    { label: "Handschriftencensus — complete MS census", url: "https://handschriftencensus.de/6184", description: "All known manuscripts listed with location and bibliography" }
  ]
},

{
  id: "donum-dei",
  title: "Donum Dei",
  subtitle: "The Gift of God — The Twelve-Flask Sequence",
  period: "medieval",
  date_display: "c. 1475–1500 (earliest MSS); over 60 copies in 5 languages",
  date_sort: 1480,
  author: "Attributed to 'Georgius Aurach de Argentina' (1475); actual authorship unknown",
  medium: "Illuminated manuscript; Latin, German, French, Italian, English copies",
  repository: "British Library (Sloane MS 2560); Leiden University Library (VCF 15); BnF Paris (btv1b105380640)",
  shelfmark: "Sloane MS 2560 (BL); VCF 15 (Leiden)",
  status: "needs_sourcing",
  priority: "high",
  symbol: "🜔",
  card_description: "More than sixty manuscript copies of this short illustrated treatise survive across five languages — the most widely distributed illustrated alchemical text of the medieval period. Twelve roundels, each showing a glass flask containing matter at a different stage of transformation, trace the Work from initial blackness through the white and red stones. The standardized twelve-flask vocabulary directly influenced the later emblem tradition.",
  related: ["rosarium-1550","aurora-consurgens","turba-philosophorum"],
  images: [
    { id: "donum-flask-1", label: "Flask I — Nigredo (Blackening)", folio_or_plate: "Roundel 1", thumb_description: "The first flask: black material — the prima materia in its initial state of putrefaction, the necessary beginning of the Work." },
    { id: "donum-flask-4", label: "Flask IV — Albedo (Whitening)", folio_or_plate: "Roundel 4", thumb_description: "The fourth flask: white material — the albedo stage, the first perfection, the White Queen." },
    { id: "donum-flask-8", label: "Flask VIII — Coniunctio", folio_or_plate: "Roundel 8", thumb_description: "The eighth flask: red and white combined — Sol and Luna in conjunction within the vessel, approaching the final Stone." },
    { id: "donum-flask-12", label: "Flask XII — Rubedo (Red Stone)", folio_or_plate: "Roundel 12", thumb_description: "The twelfth flask: the perfected red Philosopher's Stone — the culmination of the twelve-stage Work." }
  ],
  essay: {
    visual_description: `<p>The twelve roundels of the Donum Dei present a strikingly systematic visual program: each is a circular composition enclosing a glass vessel on a stand, the vessel's contents changing color through the sequence. The first roundel shows the flask filled with black material — the nigredo of putrefaction. Subsequent roundels pass through grey, white, yellow, and progressively deeper red stages. Some copies show figures within the flasks: a small homunculus; a crowned king and queen in conjunction; or the fiery red stone in its final form. The roundels are surrounded by ornamental borders whose elaboration varies from copy to copy, but the circular format and the sequential color logic remain constant across all sixty-plus manuscripts.</p>
<p>The Donum Dei's visual strategy is concentrated and diagnostic: it reduces the complex allegorical apparatus of other alchemical traditions to a single object, the glass vessel, and a single observable phenomenon, the color change of its contents. Transparency is the point — the alchemist can see the progress of the Work. This emphasis on visibility and sequential color change reflects genuine laboratory practice: in certain sulphur-mercury preparations, the color sequence black → grey → white → yellow → red is actually observable.</p>`,
    historical_context: `<p>The Donum Dei was composed in the late 15th century — the attribution to "Georgius Aurach de Argentina" with a date of 1475 is conventional rather than confirmed by independent evidence. Its extraordinary popularity (sixty-plus manuscripts in five languages over two centuries) reflects the practical utility of the twelve-flask schema as a teaching tool and practitioner's guide. The standardization of the color-stage vocabulary across this many copies suggests that the Donum Dei functioned as a reference standard — a visual glossary of alchemical color changes that any practitioner would recognize.</p>`,
    provenance: `<p>The British Library's Sloane MS 2560 (15th century, German or Austrian) is the most accessible digitized copy for the English-speaking reader. Leiden University Library's VCF 15 (1575–1600) is openly digitized at Leiden's Digital Manuscripts in the Classroom project. The BnF copy (Gallica btv1b105380640), bound with an illustrated Turba Philosophorum, provides another important witness and is freely accessible through Gallica. The multiplicity of copies attests to the text's sustained practical utility over more than two centuries.</p>`,
    alchemical_processes: `<p>The twelve-stage color sequence maps onto the standard color theory of medieval alchemy: black (nigredo, putrefaction), various intermediate grey stages, white (albedo, first purification), yellow (citrinitas, intermediate between white and red), and red (rubedo, the perfected stone). The Donum Dei does not theorize extensively about the mechanisms behind these changes — it is a practitioner's guide, presenting observable stages in sequence. This pragmatic orientation, combined with its visual clarity, explains its adoption across the full range of medieval alchemical practice.</p>`,
    scholarly_discussion: `<p>Barbara Obrist's <em>Les débuts de l'imagerie alchimique</em> provides the authoritative analysis of the Donum Dei image tradition, tracing the relationship between the twelve-flask sequence and the broader tradition of alchemical color-stage theory. Lawrence Principe's experimental recreation of period alchemical procedures has confirmed that the color sequences depicted in the Donum Dei roundels correspond to real chemical phenomena observable in sulphur-mercury and other traditional preparations, grounding the visual program in laboratory reality rather than purely symbolic convention.</p>`
  },
  bibliography: [
    { citation: "Obrist, Barbara. <em>Les débuts de l'imagerie alchimique</em>. Paris: Le Sycomore, 1982.", url: "" },
    { citation: "Principe, Lawrence M. <em>The Secrets of Alchemy</em>. Chicago: University of Chicago Press, 2013.", url: "" },
    { citation: "Abraham, Lyndy. <em>A Dictionary of Alchemical Imagery</em>. Cambridge: Cambridge University Press, 1998.", url: "" },
    { citation: "Priesner, Claus, and Karin Figala, eds. <em>Alchemie: Lexikon einer hermetischen Wissenschaft</em>. Munich: C.H. Beck, 1998.", url: "" }
  ],
  links: [
    { label: "BL Sloane MS 2560 — images at Alchemy Website", url: "https://www.alchemywebsite.com/Emblems_manuscripts_Donum_Dei_Sloane_2560.html", description: "Reproductions from the British Library copy" },
    { label: "Leiden VCF 15 — Digital Manuscripts in the Classroom", url: "https://digmanclass.universiteitleiden.nl/manuscripts/vcf-15/", description: "Fully digitized Leiden copy" },
    { label: "BnF Gallica — Turba + Donum Dei illustrated MS", url: "https://gallica.bnf.fr/ark:/12148/btv1b105380640", description: "Paris copy with both texts, fully digitized" }
  ]
},

{
  id: "turba-philosophorum",
  title: "Turba Philosophorum",
  subtitle: "Assembly of the Philosophers — Illustrated MS Tradition",
  period: "medieval",
  date_display: "9th–10th c. AD (Arabic original); 16th c. illustrated Latin MSS",
  date_sort: 1100,
  author: "Anonymous (Arabic original attributed to various ancient sages; Latin tr. 12th c.)",
  medium: "Manuscript (Latin); 16th-century illustrated copies",
  repository: "BnF, Paris (MS btv1b105380640 — illustrated, with Donum Dei)",
  shelfmark: "BnF Gallica ARK btv1b105380640",
  status: "needs_sourcing",
  priority: "medium",
  symbol: "☿",
  card_description: "The oldest alchemical text to survive in Latin translation, the Turba Philosophorum presents alchemical doctrine as a series of speeches by ancient Greek sages — Pythagoras, Anaxagoras, Democritus, Plato — at a philosophical convocation. Most copies are unillustrated, but a 16th-century BnF manuscript preserves the text with figures, bound with an illustrated Donum Dei.",
  related: ["donum-dei","leiden-stockholm","aurora-consurgens"],
  images: [
    { id: "turba-assembly", label: "The Assembly of Philosophers", folio_or_plate: "Frontispiece", thumb_description: "Robed figures in philosophical disputation — the ancient sages whose speeches compose the Turba Philosophorum, assembled as at a conference." },
    { id: "turba-diagrams", label: "Alchemical Diagrams", folio_or_plate: "Various folios", thumb_description: "Symbolic figures and diagrams from the BnF illustrated copy, accompanying the text of the philosophical speeches on alchemical prima materia." }
  ],
  essay: {
    visual_description: `<p>The illustrated BnF copy of the Turba Philosophorum (Gallica ARK btv1b105380640) is one of very few MSS of this text with visual content. Most copies of the Turba are purely textual. The frontispiece of the illustrated copy shows a group of robed scholars in philosophical disputation — the assembly of ancient sages whose speeches constitute the text — rendered in the conventions of late medieval scholarly manuscript illustration. Additional figures within the manuscript follow the iconographic conventions of the Donum Dei tradition, to which this MS is physically bound.</p>`,
    historical_context: `<p>The Turba Philosophorum is the oldest alchemical text to survive in Latin, translated from Arabic — itself derived from a Hellenistic Greek original — probably in the 12th century as part of the great wave of Arabic-to-Latin translations in Spain and Sicily. It presents alchemical doctrine as a philosophical symposium: Pythagoras convenes a gathering of ancient sages (Anaxagoras, Democritus, Plato, Socrates, Aristotle, among others) who debate the nature of the prima materia and the operations of the Work. This framing device — giving alchemical doctrine the authority of ancient philosophical names — guaranteed the text's prestige throughout the medieval and early modern periods. Gratarolo published the standard early modern edition in Frankfurt in 1572.</p>`,
    provenance: `<p>The BnF illustrated MS (Gallica btv1b105380640) is a 16th-century Latin codex holding both the Turba with figures and an illustrated Donum Dei. It has been fully digitized through Gallica and is freely accessible. The 1572 Gratarolo printed edition (text only, no illustrations) is available on Internet Archive.</p>`,
    alchemical_processes: `<p>The Turba's primary theoretical contribution is the articulation of prima materia doctrine: all metals derive from a single original substance (water or moist earth for most speakers; alternatively, a combination of the four elements). The speeches of the assembled sages represent different schools of thought on how this prima materia is to be extracted, purified, and brought to perfection as the Philosopher's Stone. The Turba thus functions as a compendium of early alchemical theory — a survey of the tradition's foundational debates in dramatic form.</p>`,
    scholarly_discussion: `<p>Julius Ruska's <em>Turba Philosophorum</em> (1931) remains the critical edition with German translation. Arthur Edward Waite produced an English translation in 1896. Charles Burnett and others working on the Arabic-to-Latin translation movement have placed the Turba in the broader context of 12th-century knowledge transfer. The Turba's influence on subsequent alchemical literature — particularly on the Rosarium Philosophorum and related texts — is substantial.</p>`
  },
  bibliography: [
    { citation: "Ruska, Julius. <em>Turba Philosophorum</em>. Berlin: Springer, 1931.", url: "" },
    { citation: "Waite, Arthur Edward. <em>The Turba Philosophorum</em>. London: George Redway, 1896.", url: "" },
    { citation: "Halleux, Robert. <em>Les alchimistes grecs</em>, vol. I. Paris: Les Belles Lettres, 1981.", url: "" }
  ],
  links: [
    { label: "BnF Gallica — Turba + Donum Dei illustrated MS", url: "https://gallica.bnf.fr/ark:/12148/btv1b105380640", description: "16th-century illustrated MS, fully digitized" },
    { label: "Internet Archive — Gratarolo 1572 edition (text)", url: "https://archive.org/details/cu31924012366088", description: "The standard early printed edition" },
    { label: "Turba Philosophorum — Wikipedia", url: "https://en.wikipedia.org/wiki/Turba_Philosophorum", description: "Overview with bibliography" }
  ]
},

{
  id: "flamel-figures",
  title: "Livre des Figures Hiéroglyphiques",
  subtitle: "Nicolas Flamel — Twenty-Two Hieroglyphic Figures",
  period: "medieval",
  date_display: "First printed 1612 (purporting to describe c. 1399 paintings)",
  date_sort: 1399,
  author: "Pseudo-Nicolas Flamel (historical Flamel: c. 1330–1418; text pseudepigraphal, composed 16th c.)",
  medium: "Manuscript (BnF MS Fr. 14765, painted vellum); printed editions from 1612",
  repository: "Bibliothèque nationale de France, Paris",
  shelfmark: "BnF MS Français 14765",
  status: "partial",
  priority: "high",
  symbol: "☽",
  card_image: "https://gallica.bnf.fr/iiif/ark:/12148/btv1b90613395/f1/full/400,/0/native.jpg",
  card_description: "Twenty-two 'hieroglyphic figures' purportedly painted by Nicolas Flamel on the arches of Paris's Cemetery of the Innocents around 1399 — images of descending angels, dragons devouring each other, a king commanding the massacre of children (an alchemical allegory of Herod), and winged Mercury. The original paintings no longer survive (the cemetery was demolished in 1786), but the BnF manuscript preserves the image cycle that generated the entire 'Flamel legend' of alchemical transmission.",
  related: ["turba-philosophorum","aurora-consurgens","rosarium-1550"],
  images: [
    { id: "flamel-angel", label: "Figure 1 — The Angel with the Book", folio_or_plate: "Figure 1",
      src: "https://gallica.bnf.fr/iiif/ark:/12148/btv1b90613395/f1/full/400,/0/native.jpg",
      attribution: "BnF Gallica — domaine public",
      thumb_description: "An angel descending with an open book of divine alchemical wisdom — the opening figure framing the entire sequence as revealed knowledge." },
    { id: "flamel-early-figure", label: "Early Hieroglyphic Figure", folio_or_plate: "Figure 3–4",
      src: "https://gallica.bnf.fr/iiif/ark:/12148/btv1b90613395/f5/full/400,/0/native.jpg",
      attribution: "BnF Gallica — domaine public",
      thumb_description: "An early figure in the sequence — dragons, Mercury, or related symbolic imagery from the opening of the hieroglyphic cycle." },
    { id: "flamel-mid-figure", label: "Mid-Sequence Hieroglyphic Figure", folio_or_plate: "Figure 7–10",
      src: "https://gallica.bnf.fr/iiif/ark:/12148/btv1b90613395/f10/full/400,/0/native.jpg",
      attribution: "BnF Gallica — domaine public",
      thumb_description: "A mid-sequence figure — possibly the Massacre of the Innocents or related imagery from the central portion of Flamel's twenty-two figure cycle." },
    { id: "flamel-resurrection", label: "Final Figure — Resurrection", folio_or_plate: "Figure 22",
      thumb_description: "The final figure: resurrection of the perfected Stone from the materials of the Work, completing the soteriological narrative." }
  ],
  essay: {
    visual_description: `<p>The twenty-two hieroglyphic figures of the pseudo-Flamel tradition present a visual program of extraordinary violence and theological complexity. The opening figure shows an angel descending with an open book — a vision narrative that frames the entire sequence as divinely revealed knowledge rather than human discovery. Subsequent figures include: a garden with a great oak from which hang golden and silver fruits; two dragons consuming each other simultaneously (a double ouroboros, representing the reciprocal dissolution that begins the Work); the god Mercury with caduceus and winged feet; and — most memorably — King Herod commanding soldiers to massacre children before a weeping woman while an angel watches with horror.</p>
<p>This last image, the Massacre of the Innocents, is the most disturbing in the alchemical canon. Flamel's explanation: the "children" are the base metals; the "soldiers" are mercury, which destroys them; the "king" is the principle of purification that commands this destruction; the woman's tears are water, the solvent. The violence of the image is the point — the destruction of the impure is not a regrettable accident of the Work but its necessary condition. In the BnF MS Français 14765, the figures are rendered as miniatures on vellum with full color and gold, embedded within Flamel's explanatory text.</p>`,
    historical_context: `<p>The historical Nicolas Flamel (c. 1330–1418) was a Paris scrivener and manuscript dealer who became, posthumously, the most famous alleged adept in the French alchemical tradition. The legend — that he discovered the Philosopher's Stone in 1382 using a mysterious book obtained from a Jewish scholar in Spain — first appeared in the <em>Livre des Figures Hiéroglyphiques</em>, published in Paris in 1612, nearly two centuries after Flamel's death. Flamel's actual prosperity in historical records derives from a successful scribal and notarial business, not from gold-making. The alchemical texts attributed to him are essentially 16th-century compositions attached to his name for authority.</p>
<p>The first print edition (Paris, 1612) established the hieroglyphic figure cycle in print; subsequent editions in French and in translation spread the images across Europe. By the 17th century, "Flamel" was a byword for the successfully realized alchemical project — an example to aspire to and a source of images to interpret. The legend grew further in the 18th and 19th centuries and retains cultural vitality in the 21st (Flamel appears as a character in several popular fantasy novels).</p>`,
    provenance: `<p>The Cemetery of the Innocents, where Flamel allegedly painted the hieroglyphic figures on the charnel house arches, was demolished in 1786 and the bones removed to the Paris catacombs. No contemporary record of any such paintings exists. The BnF MS Français 14765 is the primary MS source for the image cycle; the Albert Poisson scholarly edition of 1893 reproduces all twenty-two figures in engraving and is freely accessible on Gallica (ARK bpt6k900780r). The BnF compendium MS (btv1b9062177g) contains Flamel texts with related material.</p>`,
    alchemical_processes: `<p>Flamel's commentary on the twenty-two figures provides a systematic allegorical reading of the entire <em>opus</em>. The double dragons represent the initial state of the mercury-sulphur matrix: each principle destroys and is destroyed by the other, producing the prima materia through mutual annihilation. The Massacre of the Innocents represents the nigredo: the base metals (the "innocent children") are killed by the dissolving mercury (the "soldiers"), their forms destroyed so their essential substance can be freed. The garden with golden and silver fruits represents the albedo: the matter purified to two perfections simultaneously. The final resurrection figure represents the completion of the Work. The sequence is thus a visual catechism of the alchemical <em>opus</em> structured as narrative allegory.</p>`,
    scholarly_discussion: `<p>William Newman and Lawrence Principe's <em>Alchemy Tried in the Fire</em> (2002) examines the construction of the Flamel legend in the early 17th century, demonstrating the pseudepigraphal character of all the "Flamel" alchemical texts. Antoine Faivre's work on Western esotericism provides the broader framework: the Flamel legend exemplifies the "transmission narrative" — a story guaranteeing the authenticity of secret knowledge by attributing it to a historical figure of recognized virtue, dating that figure's discovery to a specific moment of divine revelation, and tracing the chain of transmission to the present. This narrative structure is common to many alchemical, Rosicrucian, and Masonic traditions.</p>`
  },
  bibliography: [
    { citation: "Newman, William R., and Lawrence M. Principe. <em>Alchemy Tried in the Fire</em>. Chicago: University of Chicago Press, 2002.", url: "" },
    { citation: "Poisson, Albert. <em>Nicolas Flamel: sa vie, ses fondations, ses oeuvres</em>. Paris: Chacornac, 1893.", url: "" },
    { citation: "Faivre, Antoine. <em>Access to Western Esotericism</em>. Albany: SUNY Press, 1994.", url: "" },
    { citation: "Abraham, Lyndy. <em>A Dictionary of Alchemical Imagery</em>. Cambridge: Cambridge University Press, 1998.", url: "" }
  ],
  links: [
    { label: "BnF Gallica — MS Français 14765 (vellum miniatures)", url: "https://gallica.bnf.fr/ark:/12148/btv1b52515783p", description: "Primary MS source for the hieroglyphic figures" },
    { label: "Gallica — Poisson 1893 edition (all 22 figures engraved)", url: "https://gallica.bnf.fr/ark:/12148/bpt6k900780r.texteImage", description: "Scholarly edition with reproductions of all figures" },
    { label: "BnF Gallica — Flamel alchemical compendium", url: "https://gallica.bnf.fr/ark:/12148/btv1b9062177g", description: "Flamel texts with Bernard le Trevisan and Zacaire" },
    { label: "Nicolas Flamel — Wikipedia", url: "https://en.wikipedia.org/wiki/Nicolas_Flamel", description: "Historical and legendary biography" }
  ]
},

{
  id: "rosarium-1550",
  title: "Rosarium Philosophorum",
  subtitle: "The Rosary of the Philosophers — 20 Woodcuts of the Royal Marriage",
  period: "medieval",
  date_display: "First printed 1550 (Frankfurt: Cyriacus Jacobi); image tradition earlier",
  date_sort: 1550,
  author: "Anonymous",
  medium: "Printed book with 20 woodcuts; also manuscript copies",
  repository: "Internet Archive (primary scan); BnF (MS copies); National Library of Israel (MS copy)",
  shelfmark: "IA identifier: RosariumPhilosophorum",
  status: "partial",
  priority: "high",
  symbol: "♀",
  card_description: "Twenty woodcut illustrations of the Sol-Luna coniunctio — the 'royal marriage' moving from the first meeting of crowned king and queen through their naked union in a bath, shared death and putrefaction, and resurrection as the androgynous Rebis — form the most influential image sequence in the entire Western alchemical tradition. Already partially in corpus; higher-resolution versions of the original 1550 woodcuts are sought.",
  related: ["aurora-consurgens","splendor-solis-bl","donum-dei"],
  images: [
    { id: "rosarium-01-meeting", label: "Plate 1 — The Meeting", folio_or_plate: "Woodcut 1", thumb_description: "Sol and Luna, crowned, face one another extending flowers — the beginning of the royal coniunctio." },
    { id: "rosarium-02-mercury", label: "Plate 2 — Mercury as Guide", folio_or_plate: "Woodcut 2", thumb_description: "Mercury between the king and queen — the mercurial principle as intermediary in the alchemical conjunction." },
    { id: "rosarium-03-bath", label: "Plate 3 — The Bath", folio_or_plate: "Woodcut 3", thumb_description: "The crowned couple naked together in a circular bath — their cohabitation, the beginning of dissolution into one another." },
    { id: "rosarium-05-conjunction", label: "Plate 5 — The Conjunction", folio_or_plate: "Woodcut 5", thumb_description: "The king and queen in full sexual union — the coniunctio in its most literal form, encoding the union of sulphur and mercury." },
    { id: "rosarium-06-death", label: "Plate 6 — The Death", folio_or_plate: "Woodcut 6", thumb_description: "The couple lying dead together — the nigredo: the two principles dissolved into each other, their individual forms destroyed." },
    { id: "rosarium-10-resurrection", label: "Plate 10 — The Rebis Resurrection", folio_or_plate: "Woodcut 10", thumb_description: "The androgynous Rebis rising from the coffin with solar crown and lunar crescent — the completed Stone, male and female unified in one perfected form." }
  ],
  essay: {
    visual_description: `<p>The twenty woodcuts of the 1550 Rosarium Philosophorum present a visual narrative of striking directness. The king, identified by his solar disc and crown, and the queen, identified by her lunar crescent, approach one another in the first woodcut holding flowering branches. Mercury — the god, depicted with caduceus and winged feet — stands between them as intermediary and guide. In subsequent woodcuts, they exchange flowers; they are ushered together into a shared circular bath. The bath scenes are the most frankly erotic images in the mainstream alchemical tradition: the two figures are shown naked together, immersed to the waist, the circle of the bath enclosing them as the alchemical flask encloses its contents.</p>
<p>Their union produces death. In the sixth woodcut, the king and queen lie naked and apparently dead across one another, their bodies in the first stages of putrefaction. Over subsequent plates, the decomposition reverses: a winged soul-figure rises from the bodies; rain falls on the corpses (the dew of purification); new life begins to form. In the tenth and final woodcut, the Rebis rises from a coffin or vessel, a single androgynous body bearing both the solar crown and the lunar crescent, male and female features unified — the perfected Stone, the culmination of the coniunctio.</p>`,
    historical_context: `<p>The Rosarium Philosophorum was first printed in Frankfurt in 1550 as Part II of the anthology <em>De Alchimia Opuscula</em>, published by Cyriacus Jacobi. The 20-woodcut cycle appears for the first time in print here; no earlier manuscript with the full illustrated program is known, though the text has earlier textual witnesses. The images became the most reproduced sequence in early modern alchemical publishing — cited, copied, and plagiarized by dozens of subsequent works. C.G. Jung's <em>Psychology of the Transference</em> (1946), which devoted its entirety to the ten central plates, gave the Rosarium extraordinary visibility in the 20th century.</p>`,
    provenance: `<p>The Internet Archive holds a scan of the Rosarium (IA: RosariumPhilosophorum). The current EmblemPrintShop corpus includes 19 extracted pages from this scan. The National Library of Israel holds a manuscript copy (NLI catalog: NNL_ALEPH990035056340205171). The Frankfurt University's Merian-Alchemie exhibition project provides contextual material on the 1550 printing within the Frankfurt alchemical publishing tradition.</p>`,
    alchemical_processes: `<p>The Rosarium sequence encodes the <em>coniunctio</em> — the union of opposites — as both the central operation and the central mystery of alchemy. Sol (sulphur, the fixed principle, gold, the masculine) and Luna (mercury, the volatile principle, silver, the feminine) must be united in a common vessel. Their union first destroys them both — the nigredo of death and putrefaction — before generating the unified Stone (the Rebis, the androgynous perfection). The sequence models the principle that all higher synthesis requires the dissolution of its components: the Stone cannot be created without the destruction of both Sol and Luna as separate entities. This philosophical principle was read by later interpreters as encoding actual laboratory procedure (the union of gold with mercury to produce an amalgam, which is then heated until the mercury is driven off), theological allegory (the death and resurrection of Christ), and psychological process (the dissolution of ego in the unconscious and the emergence of the integrated Self).</p>`,
    scholarly_discussion: `<p>C.G. Jung's <em>Psychology of the Transference</em> (1946) reads the ten central Rosarium plates as a symbolic map of the transference relationship in psychoanalysis, giving this medieval image sequence a 20th-century psychological interpretation that has been enormously influential. More rigorous historical scholarship — particularly by Barbara Obrist, Jennifer Rampling, and Lawrence Principe — situates the images in their proper historical context of laboratory practice and the visual culture of late medieval and early modern alchemy. Adam McLean's edition and commentary (<em>The Rosary of the Philosophers</em>, 1980) provides a practitioner's perspective on the sequence.</p>`
  },
  bibliography: [
    { citation: "Jung, C.G. <em>The Psychology of the Transference</em>. Collected Works, vol. 16. Princeton: Princeton University Press, 1954.", url: "" },
    { citation: "McLean, Adam, ed. <em>The Rosary of the Philosophers</em>. Edinburgh: Magnum Opus Hermetic Sourceworks, 1980.", url: "" },
    { citation: "Obrist, Barbara. <em>Les débuts de l'imagerie alchimique</em>. Paris: Le Sycomore, 1982.", url: "" },
    { citation: "Principe, Lawrence M. <em>The Secrets of Alchemy</em>. Chicago: University of Chicago Press, 2013.", url: "" },
    { citation: "Abraham, Lyndy. <em>A Dictionary of Alchemical Imagery</em>. Cambridge: Cambridge University Press, 1998.", url: "" }
  ],
  links: [
    { label: "Internet Archive — Rosarium Philosophorum", url: "https://archive.org/details/RosariumPhilosophorum", description: "Primary digitized source" },
    { label: "Frankfurt Merian-Alchemie — De Alchimia 1550 context", url: "https://merian-alchemie.ub.uni-frankfurt.de/ausstellung/i-merian-und-die-tradition-der-alchemica-illustrata-in-frankfurt/de-alchimia-mit-rosarium-philosophorum-1550/", description: "Exhibition on the 1550 Frankfurt edition" },
    { label: "Rosary of the Philosophers — Wikipedia", url: "https://en.wikipedia.org/wiki/Rosary_of_the_Philosophers", description: "Overview and image links" }
  ]
},

// ─── EARLY MODERN SECTION CONTINUES IN data-em.js ───
// The remainder of WORKS is appended below by the build process.
];

const WORKS_BY_ID = Object.fromEntries(WORKS.map(w => [w.id, w]));
