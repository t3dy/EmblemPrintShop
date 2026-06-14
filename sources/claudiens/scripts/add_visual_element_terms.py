"""Add 12 dictionary terms for recurring visual elements depicted across Maier's
emblem plates that lacked dedicated entries.

Idempotent: INSERT OR IGNORE.
"""
import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "atalanta.db")


def reg(alch, med, spir, cosm):
    return json.dumps({
        "alchemical": alch,
        "medical": med,
        "spiritual": spir,
        "cosmological": cosm,
    }, ensure_ascii=False)


TERMS = [
    {
        "slug": "hesperides",
        "label": "Hesperides",
        "category": "FIGURE",
        "label_latin": "Hesperides",
        "definition_short": "The three nymphs—Aegle, Arethusa, and Hespertusa—who guard the tree of golden apples in the far western garden.",
        "definition_long": (
            "The Hesperides are the three nymphs of the evening light, daughters of Atlas (in some genealogies, "
            "of Night), who tend the tree of golden apples in a paradisal garden at the western edge of the world. "
            "Their names vary across classical sources; the tradition Maier draws on names them Aegle (Brightness), "
            "Arethusa (Watering), and Hespertusa (Evening). The garden is guarded by the dragon Ladon, whom Hercules "
            "slays in his eleventh labor to obtain the apples. Renaissance mytho-alchemy reads the three nymphs as "
            "personifications of complementary phases or principles in the work, the dragon as the volatile mercury "
            "that must be subdued, and the golden apples as the perfected Stone."
        ),
        "significance_to_af": (
            "The Hesperides appear on the AF frontispiece (Emblem 0) above the foot-race scene, where Hercules "
            "approaches their tree to take the golden fruit. Their inclusion alongside the Atalanta-Hippomenes race "
            "tells the reader that the apples thrown by Hippomenes are the same kind of apples Hercules retrieves: "
            "both myths encode the same alchemical operation under different narrative covers. The garden of the "
            "Hesperides functions as a topos for the alchemical laboratory itself—a hidden, dragon-guarded enclosure "
            "in which the gold ripens."
        ),
        "registers": reg(
            "The three guardians of the golden apples at the world's western edge: figures of the alchemical phases that ripen the Stone in the dragon-guarded vessel.",
            "The threefold custodians of the supreme medicament; the watchful nymphs who tend the tree whose fruit is the panacea, recoverable only through the heroic labor of the physician.",
            "The interior keepers of evening wisdom whose triple name—brightness, watering, evening—maps onto stages of contemplative ripening: illumination, nourishment, and the long patient dusk before harvest.",
            "The vespertine triad of the western horizon; the celestial nymphs whose station at the sunset boundary marks the cosmological place where solar gold concentrates before its nightly disappearance."
        ),
        "emblem_links": [0],
    },
    {
        "slug": "earth-mother",
        "label": "Earth-Mother / Terra",
        "category": "FIGURE",
        "label_latin": "Terra Mater",
        "definition_short": "The massive globular female earth-figure depicted reclining on the landscape in Emblems I and II as nurse of the philosophical infant.",
        "definition_long": (
            "The earth-mother (Terra Mater) is the personified globe of the world depicted in Emblems I and II as a "
            "vast reclining female body whose flesh merges with the landscape itself. Her exposed breasts nurse a "
            "small child—the philosophical infant carried in Boreas's belly—and animals graze at her feet. The image "
            "draws on the classical traditions of Tellus (Roman), Gaia (Greek), and the medieval Mater Terra "
            "iconography seen in works like Albertus Magnus's Philosophia pauperum and Mylius's Philosophia "
            "reformata. Walter Pagel notes the figure as a 'nurse of the tender child of the Philosophers,' a "
            "pregnant earth whose womb-substance gestates the alchemical work."
        ),
        "significance_to_af": (
            "The earth-mother establishes the maternal-vegetative pole of the AF cosmology that complements the "
            "paternal-aerial pole of Boreas (Emblem I). De Jong reads the pairing as the Emerald Tablet's 'pater eius "
            "est Sol, mater eius Luna; portavit eum ventus in ventre suo'—the Sun is its father, the Moon its mother, "
            "the wind carried it in its belly: the wind (Boreas) and the earth (Terra) together gestate and nurse the "
            "Stone. Her recurrence in Emblem II underscores that the work's substrate is the body of nature itself, "
            "and that alchemical operations are continuous with terrestrial generation."
        ),
        "registers": reg(
            "The maternal substrate that nurses the philosophical infant: the body of nature whose globular flesh provides the matrix in which the alchemical work proceeds.",
            "The fundamental nutritive principle: the great nurse whose milk and produce sustain bodily life, archetype of every dietetic and humoral therapy that draws on terrestrial substances.",
            "The Magna Mater as feminine ground of being; the maternal presence whose acceptance of the seeker's vulnerability allows spiritual nourishment to occur where personal effort cannot reach.",
            "The terrestrial sphere personified as living being; the cosmos's central mother-body that receives celestial seed (rain, dew, solar heat) and converts it into manifest generation."
        ),
        "emblem_links": [1, 2],
    },
    {
        "slug": "arbor-philosophica",
        "label": "Arbor Philosophica / Philosophical Tree",
        "category": "CONCEPT",
        "label_latin": "Arbor Philosophica",
        "definition_short": "The alchemical tree of metals or tree of life whose branches bear the seven planetary metals and whose fruit is the Stone.",
        "definition_long": (
            "The arbor philosophica is one of alchemy's most persistent images: a tree (often metallic, often bearing "
            "celestial fruit) whose roots draw on the prima materia and whose branches yield the seven planetary "
            "metals or the philosophical fruit. The figure descends from Senior's Tabula Chimica, the Aurora "
            "Consurgens, and the Rosarium Philosophorum, and threads through the Splendor Solis and the Pretiosa "
            "Margarita Novella. The tree functions as a vegetative model of the work in contradistinction to the "
            "mineral or animal models: alchemy is gardening as well as smithing, and the Stone is grown and ripened "
            "as much as it is forged."
        ),
        "significance_to_af": (
            "The philosophical tree appears in multiple AF emblems: the tree of the Hesperides on the frontispiece "
            "(Emblem 0), the tree to which the old man is bound while celestial dew falls on him (Emblem IX), and "
            "the Tree of Life beside which Lady Sapientia stands in Emblem XXVI. The recurrence signals that the AF "
            "is shaped by the vegetative paradigm—Maier's emphasis on play, music, and ripening fits the tree-of-"
            "metals tradition more than the laboratory-furnace tradition. The reader is invited to see the work as "
            "a garden to be tended, not merely a process to be executed."
        ),
        "registers": reg(
            "The vegetative model of the opus: the tree whose branches bear the seven metals and whose fruit is the perfected Stone, ripened by patience rather than forced by heat alone.",
            "The Tree of Life of medieval medicine: the iconography of the body as a tree whose humoral sap must circulate freely if the canopy of health is to flourish.",
            "The interior tree of the soul, planted in the heart and watered by contemplation; the figure of the integrated self whose roots reach the unconscious and whose crown reaches divine light.",
            "The cosmic axis (axis mundi) figured as world-tree, linking underworld, earth, and heavens; the vertical scaffold of correspondence on which Renaissance natural philosophy hung its system."
        ),
        "emblem_links": [0, 9, 26],
    },
    {
        "slug": "philosophical-child",
        "label": "Philosophical Child / Puer Philosophicus",
        "category": "FIGURE",
        "label_latin": "Puer Philosophicus",
        "definition_short": "The infant figure—newborn, swaddled, or growing—who appears throughout the AF as the nascent Stone in personified form.",
        "definition_long": (
            "The puer philosophicus is the infant or child who recurs across alchemical iconography as the nascent "
            "Stone or as the work's product in personified form. He is born in the philosophical egg, gestates in "
            "the earth-mother, is carried by the wind, must be nursed, washed, and tempered in fire. The image "
            "appears in the Rosarium Philosophorum (the king's son), the Aurora Consurgens (the divine child), and "
            "throughout the Splendor Solis tradition. Sometimes the child is the perfected Mercury; sometimes the "
            "Rebis-hermaphrodite in early form; sometimes the homunculus of Paracelsian theory."
        ),
        "significance_to_af": (
            "The philosophical child appears across the AF: Boreas carries him in his belly (Emblem I), the earth-"
            "mother nurses him (Emblems I and II), he is concealed in the egg pierced by the flaming sword (Emblem "
            "VIII), Ceres or Thetis tempers him in fire as Triptolemus or Achilles (Emblem XXXV), and he stands "
            "between his three fathers (Emblem XLIX). The recurring infant unifies the AF's narrative spine: the "
            "work is the conception, gestation, birth, washing, feeding, tempering, and growing-up of a single "
            "philosophical being."
        ),
        "registers": reg(
            "The nascent Stone in personified form: the infant whose conception, gestation, and tempering in the sealed vessel are the operations the alchemist performs at each stage of the work.",
            "The infant patient whose care models radical pediatric medicine: the one who must be received, nourished, washed, warmed, and protected with sustained attention before becoming the agent of cure.",
            "The new self born from the soul's labor; the inner child whose appearance signals successful integration after the long descent through nigredo, requiring tender care to mature into adult wisdom.",
            "The cosmic puer of Hermetic and Christian tradition: the divine child who descends into matter to redeem it, whose biographical span recapitulates the cosmos's own journey from conception to fulfillment."
        ),
        "emblem_links": [1, 2, 8, 35, 49],
    },
    {
        "slug": "balneum",
        "label": "Balneum / Alchemical Bath",
        "category": "CONCEPT",
        "label_latin": "Balneum",
        "definition_short": "The alchemical bath—balneum mariae or steam bath—in which the king is immersed for cure or the matter is gently heated.",
        "definition_long": (
            "The balneum is the alchemical bath, both as practical apparatus and as iconographic motif. The "
            "balneum mariae (Mary's bath) is the water-bath used for gentle, indirect heating: the vessel containing "
            "the matter is immersed in a larger pot of water rather than placed directly on flame, which keeps the "
            "temperature even and below water's boiling point. The balneum vaporis is the steam bath, used for "
            "treating bodies medical or alchemical with controlled humid heat. As iconography, the bath in which "
            "the king is immersed (Emblem XXVIII) draws on the Turba Philosophorum's narrative of King Duenech, who "
            "must be cured of melancholic excess by sustained immersion in warm water."
        ),
        "significance_to_af": (
            "The balneum dominates Emblem XXVIII, where the crowned king sits in the steaming bath while attendants "
            "regulate the temperature and dark fluids drain from his body. De Jong identifies the source as the "
            "Turba's King Duenech episode. Pagel emphasizes the medical resonance: Galenic and Paracelsian medicine "
            "alike inherited bath-therapy from biblical (Naaman in the Jordan, Emblem XIII) and classical sources. "
            "The bath is alchemy's gentle counterpart to the violence of calcination: matter is purified by patient "
            "immersion rather than by burning."
        ),
        "registers": reg(
            "The balneum mariae and steam bath: the gentle, indirect heating apparatus by which volatile matter is purified without scorching, preferred for the long phases of the opus.",
            "The therapeutic bath of humoral medicine: warm water as the vehicle of cure for melancholic, leprous, and febrile conditions; the technique inherited from biblical and Hippocratic balneology.",
            "The contemplative immersion that dissolves rigid ego-structures without violent confrontation; the warm, sustained holding-environment in which transformation can ripen at its own pace.",
            "The cosmic bath of dawn dew and seasonal rain in which the earth is daily and yearly cleansed; the macrocosmic counterpart of the alchemical vessel in which sublunary matter is renewed."
        ),
        "emblem_links": [13, 28],
    },
    {
        "slug": "celestial-dew",
        "label": "Celestial Dew / Ros Coelestis",
        "category": "SUBSTANCE",
        "label_latin": "Ros Coelestis",
        "definition_short": "The dew that falls from heaven, gathered as a privileged solvent and nourishing principle for the alchemical work.",
        "definition_long": (
            "Ros coelestis—celestial or May dew—occupies a privileged place in the alchemical pharmacopoeia. Adepts "
            "gathered dew with linen cloths in the early hours of spring mornings, believing it to carry distilled "
            "celestial influence in concentrated form. It functions in the literature both as a literal substance "
            "(used in spagyric preparation of plant tinctures) and as a symbol of the descent of philosophical "
            "Mercury or divine grace. The Tabula Smaragdina states that 'its mother is the Moon... the wind carried "
            "it in its belly; its nurse is the earth'; the descending mother-substance, distilled out of the air "
            "onto cool morning grass, is the dew."
        ),
        "significance_to_af": (
            "Celestial dew descends visibly in Emblem IX, where the old man is bound to the tree and the dew falls "
            "on his body—an image of the matter's revivification by celestial influence after fixation. The same "
            "downward-descending principle reappears as the golden rain on Rhodes in Emblem XXIII (paired with "
            "Pallas Athena's birth) and as the celestial fire descending on the conceiving figure in Emblem XXXIV. "
            "Across these emblems, descent from above carries the active principle that completes what terrestrial "
            "operations alone cannot."
        ),
        "registers": reg(
            "The privileged philosophical solvent gathered from cool morning grass: condensed celestial moisture whose virtue exceeds ordinary water in spagyric preparation.",
            "The pure water of life used as base for delicate medicines and infant remedies; the gentlest of solvents for extracting subtle active principles from plant matter.",
            "The descending grace that revives what human effort has prepared but cannot animate; the gift from above that completes the soul's work without erasing it.",
            "The visible token of celestial influence's daily descent into terrestrial matter; the cosmos's ongoing infusion of the sublunary world with subtle astral substance."
        ),
        "emblem_links": [9, 23, 34],
    },
    {
        "slug": "alchemical-rose",
        "label": "Alchemical Rose / Rosa Philosophorum",
        "category": "CONCEPT",
        "label_latin": "Rosa Philosophorum",
        "definition_short": "The philosophical rose—white and red—central to the iconography of the Rosarium Philosophorum and the alchemical garden.",
        "definition_long": (
            "The rosa philosophorum is the rose of the philosophers, named in the title of one of alchemy's "
            "foundational texts (the Rosarium Philosophorum, c. 1550) and depicted throughout the iconographic "
            "tradition. The white rose figures the perfected matter at the albedo stage; the red rose figures the "
            "rubedo or the completed Stone. The two roses paired (white and red on a single stem) are the alchemical "
            "marriage in floral form. The rose is also the central motif of the Rosicrucian Brotherhood whose "
            "manifestos appeared in 1614–1616, contemporary with the AF, and whose name (Rosae Crucis—Rose-Cross) "
            "Maier defended in print."
        ),
        "significance_to_af": (
            "The walled rose-garden appears in Emblem XXVII, where the figure stands locked out of the rosarium—the "
            "key to entry being the secret knowledge the work demands. The white-to-red transformation appears "
            "vividly in Emblem XLI, where Adonis's blood stains white roses red at the moment of his death. The rose "
            "thus visualizes both the perfected matter (white-and-red) and the bloody sacrifice required to produce "
            "it. Maier's defense of Rosicrucianism in Silentium post Clamores and Themis Aurea is iconographically "
            "continuous with the AF's rose imagery."
        ),
        "registers": reg(
            "The white-and-red flower whose two phases (albedo and rubedo) summarize the work; the rose-stem on which the philosophical marriage opens into completion.",
            "The Galenic and Paracelsian rose used in pharmacy: rose-water, rose oil, and conserve of roses as cordials and astringents whose color marks their humoral properties.",
            "The opened heart of the awakened soul; the inner flower whose unfolding signifies receptive readiness to the descent of grace, the symbol shared by Rosicrucian and Sufi traditions.",
            "The rose-mandala of the cosmos in its perfected form; the pattern of celestial ordering that geometric and mystical traditions alike read as the universe's signature shape."
        ),
        "emblem_links": [27, 41],
    },
    {
        "slug": "hierogamy",
        "label": "Hierogamy / Sacred Marriage",
        "category": "CONCEPT",
        "label_latin": "Hieros Gamos",
        "definition_short": "The sacred marriage of opposites—Sol and Luna, king and queen, heaven and earth—central to alchemical and Hermetic transformation.",
        "definition_long": (
            "Hierogamy (from Greek hieros gamos, 'sacred marriage') names the union of opposites that lies at the "
            "core of alchemical doctrine and Hermetic cosmology. The marriage is staged at multiple registers: as "
            "the chemical wedding of Sulphur and Mercury, as the union of Sol (king) and Luna (queen), as the "
            "celestial marriage of heaven and earth, and as the inner conjunction of contraries within the "
            "psyche. The Rosarium Philosophorum's woodcuts narrate the marriage in detail; the Chemical Wedding "
            "of Christian Rosenkreutz (1616) presents it as Rosicrucian initiation. The marriage produces the "
            "Rebis-hermaphrodite (the two-natured product), which in turn yields the Philosopher's Stone."
        ),
        "significance_to_af": (
            "Hierogamy organizes much of the AF: the union of brother and sister (Emblem IV), the dragon's killing "
            "by Sol and Luna (Emblem XXV), the celestial conception (Emblem XXXIV), the resulting hermaphrodite "
            "lying in darkness (Emblems XXX and XXXIII), the standing hermaphrodite between the mountains of "
            "Mercury and Venus (Emblem XXXVIII), and the dragon-and-woman mortal embrace (Emblem L). De Jong traces "
            "this nuptial spine across at least 14 emblems, identifying it as the structural backbone of Maier's "
            "emblem program."
        ),
        "registers": reg(
            "The chemical wedding of philosophical Sulphur and Mercury: the central nuptial operation whose product (the Rebis) is the precursor of the Stone, staged repeatedly through the work.",
            "The therapeutic union of opposed humoral qualities: the cure-by-conjunction in which contrary principles (hot and cold, moist and dry) are brought into balanced wedlock within the patient.",
            "The interior marriage of conscious and unconscious, masculine and feminine, that yields psychic wholeness; Jung's individuation drew its name and structure directly from alchemical hierogamy.",
            "The cosmic wedding of heaven and earth, Sol and Luna; the great conjunction whose terrestrial reflection orders generation throughout sublunary nature."
        ),
        "emblem_links": [4, 25, 30, 33, 34, 38, 50],
    },
    {
        "slug": "wild-boar",
        "label": "Wild Boar / Aper",
        "category": "FIGURE",
        "label_latin": "Aper",
        "definition_short": "The wild boar that gores Adonis to death in classical myth, recast by Maier as a destructive principle whose violence catalyzes transformation.",
        "definition_long": (
            "The wild boar (aper) of classical mythology is the beast that kills Adonis, the youth beloved of Venus, "
            "during a hunt. The blood from Adonis's wound stains the white roses growing nearby, transforming them "
            "into the red roses of grief. The boar is also the third labor of Hercules (the Erymanthian boar). In "
            "alchemical mytho-reading, the boar embodies the violent, destructive principle that breaks open the "
            "vessel or wounds the king: the corrosive sulphur, the antimonial wolf-action, or the death required "
            "before resurrection. Maier and his predecessors invoke the boar as a recurrent agent of necessary "
            "destruction in the work."
        ),
        "significance_to_af": (
            "The wild boar appears in Emblem XLI, where it gores Adonis in the woodland setting and Venus rushes to "
            "the dying youth. The blood-staining of the white roses—central to the alchemical color sequence "
            "albedo→rubedo—is precipitated by the boar's violence. Without the boar's killing stroke, the roses "
            "remain white; the rubedo demands the boar's intervention. The image stages an alchemical truth: the "
            "passage from white to red is not a gentle ripening but a sacrificial wound."
        ),
        "registers": reg(
            "The destructive principle whose violence wounds the matter so that its red essence may flow; the corrosive agent (sulphur, antimony) that catalyzes the passage from albedo to rubedo.",
            "The acute, wounding crisis whose intervention forces the body's hidden reserves into active engagement; the violent symptom that paradoxically initiates the cure.",
            "The shadow eruption that destroys naive innocence and opens the soul to deeper feeling; the necessary loss whose blood paints the world with vivid color the protected life cannot know.",
            "The chthonic boar of the Erymanthian wilds: the wild, untamed face of nature that resists civilization and whose violence is integral to the cosmos's economy of generation and decay."
        ),
        "emblem_links": [41],
    },
    {
        "slug": "pallas-athena",
        "label": "Pallas Athena",
        "category": "FIGURE",
        "label_latin": "Pallas Athena",
        "definition_short": "The Greek goddess of wisdom, born fully armed from the head of Zeus; in the AF, she emerges with the descent of golden rain.",
        "definition_long": (
            "Pallas Athena is the Greek goddess of wisdom, war, and craft, born fully armed from the head of Zeus "
            "after he swallowed her pregnant mother Metis. She is one of the few Olympians without a mortal mother, "
            "and her birth from the head rather than the womb makes her an emblem of intelligence proceeding "
            "directly from divine mind. As tutelary deity of Athens, she patronizes the techne of artisans, "
            "weavers, and—by extension—alchemists. Her birth is iconographically linked to the descent of golden "
            "rain (Danae and Zeus, Rhodes and Zeus, etc.) in Renaissance mytho-alchemical reading."
        ),
        "significance_to_af": (
            "Pallas appears in Emblem XXIII, where she emerges fully formed alongside the descent of golden rain on "
            "Rhodes. The simultaneity of golden precipitation and goddess-birth links the descent of philosophical "
            "gold from above to the emergence of wisdom: the work's product is not only matter but understanding. "
            "Sapientia (Emblem XXVI) stands as her Latin cousin, and the AF's whole pedagogical program—the ludus "
            "serius of looking, reading, listening, singing—falls under her patronage as goddess of techne and "
            "philosophical craft."
        ),
        "registers": reg(
            "The wisdom that completes the operative work: alchemy is not gold-making alone but knowledge-making, and Pallas's birth from divine mind names the cognitive yield of the opus.",
            "The patron of medical techne whose insight guides the physician's hand; the goddess of the well-considered remedy applied at the right moment with the right craft.",
            "The wisdom-figure of integrated psyche: the inner intelligence born fully armed from the depths of contemplation, ready to defend and to weave at once.",
            "The Athenian goddess whose celestial descent into civic life models how heavenly wisdom enters the sublunary world; the cosmos's intelligence personified at a particular polis."
        ),
        "emblem_links": [23],
    },
    {
        "slug": "triptolemus",
        "label": "Triptolemus / Achilles in the Fire",
        "category": "FIGURE",
        "label_latin": "Triptolemus",
        "definition_short": "The infant held over flames by Ceres (or Thetis) to make him immortal—a mythic figure of the philosophical child tempered in fire.",
        "definition_long": (
            "Triptolemus is the Eleusinian prince whom Demeter/Ceres held in her fire each night to render him "
            "immortal, abandoning the rite when the prince's mother witnessed it in horror. The parallel myth of "
            "Thetis and Achilles repeats the structure: the goddess attempts to make the mortal infant invulnerable "
            "by passing him through fire, with Peleus's intervention preventing completion. Both myths encode the "
            "alchemical operation of tempering—the controlled application of heat to the matter—as a maternal rite "
            "in which the child is partially deified through fire."
        ),
        "significance_to_af": (
            "Triptolemus (or Achilles, in some readings) appears in Emblem XXXV, where Ceres (or Thetis) holds the "
            "infant over the flames while a second figure registers alarm. The image stages the philosophical child's "
            "tempering in fire as both nurturing and dangerous—the maternal-fire that hardens the Stone is the same "
            "fire that destroys what cannot endure it. Maier's frequent return to mother-and-child imagery "
            "(Emblems I, II, V, XXXV, XLI) reads this myth alongside the others as a single sustained meditation on "
            "the costs and conditions of philosophical generation."
        ),
        "registers": reg(
            "The controlled tempering of the embryonic Stone in measured fire: the infant matter held in the flame just long enough to fix its virtue, withdrawn before destruction.",
            "The pediatric fever-cure that strengthens the constitution by carefully calibrated heat exposure; the homeopathic principle of using fire to harden against fire.",
            "The trials by fire that the spiritual infant must endure to acquire immortal substance; the costly grace by which the soul is rendered invulnerable to ordinary suffering.",
            "The cosmic principle of selective combustion: the fire that purifies and preserves the worthy while consuming the unworthy, governing the differential survivals of cosmic and biographical time."
        ),
        "emblem_links": [35],
    },
    {
        "slug": "flaming-sword",
        "label": "Flaming Sword",
        "category": "CONCEPT",
        "label_latin": "Gladius Igneus",
        "definition_short": "The fiery sword that pierces the philosophical egg, introducing controlled heat into the sealed vessel of the work.",
        "definition_long": (
            "The flaming sword (gladius igneus) carries multiple iconographic resonances: it is the cherubic sword "
            "guarding Eden after the Fall (Genesis 3:24), the apocalyptic sword issuing from the mouth of the Son "
            "of Man (Revelation 1:16), and the operative blade by which the alchemist introduces controlled heat "
            "into the sealed vessel. As the fiery weapon, it figures the active masculine principle of separation "
            "and judgment, distinguishing what must be preserved from what must be consumed. Its application to the "
            "philosophical egg is one of alchemy's most pointed iconographic statements: the closed vessel is not "
            "violated but purposefully opened by a precise, fiery instrument."
        ),
        "significance_to_af": (
            "The flaming sword pierces the philosophical egg in Emblem VIII, with vapors and flames escaping from "
            "the breach. The image visualizes the introduction of fire into the philosophical egg—the sealed work-"
            "space—as a violent but precise act. De Jong reads the sword as the operative principle that begins "
            "the work, its fire being the same fire that resurfaces as athanor heat (Emblem XVIII), as the four-"
            "fold sphere of fires (Emblem XVII), and as the salamander's element (Emblem XXIX). The sword unifies "
            "the AF's repeated meditations on fire as the artist's fundamental tool."
        ),
        "registers": reg(
            "The operative heat introduced into the sealed vessel: the precise, measured fire that initiates the work without destroying its enclosure; the artist's chief instrument.",
            "The cauterizing blade of surgery: the heated steel that opens, drains, and seals the diseased body in a single stroke; the principle of curative violence in iatrochemical practice.",
            "The discriminating intelligence that separates spirit from matter, soul from body, true from false; the inner sword by which the contemplative cleaves through illusion.",
            "The cosmic principle of fiery judgment: the apocalyptic sword whose descent from heaven separates the wheat from the chaff in eschatological time and the elements from each other in cosmic genesis."
        ),
        "emblem_links": [8],
    },
]


def main():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return 1
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    inserted = 0
    skipped = 0
    linked = 0
    for term in TERMS:
        c.execute(
            """INSERT OR IGNORE INTO dictionary_terms
               (slug, label, category, label_latin, definition_short, definition_long,
                significance_to_af, registers, review_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT')""",
            (
                term["slug"], term["label"], term["category"], term["label_latin"],
                term["definition_short"], term["definition_long"],
                term["significance_to_af"], term["registers"],
            ),
        )
        if c.rowcount:
            inserted += 1
        else:
            skipped += 1
        c.execute("SELECT id FROM dictionary_terms WHERE slug = ?", (term["slug"],))
        row = c.fetchone()
        if not row:
            continue
        term_id = row[0]
        for emblem_num in term.get("emblem_links", []):
            c.execute("SELECT id FROM emblems WHERE number = ?", (emblem_num,))
            emblem_row = c.fetchone()
            if not emblem_row:
                continue
            c.execute(
                "INSERT OR IGNORE INTO term_emblem_refs (term_id, emblem_id, context) VALUES (?, ?, ?)",
                (term_id, emblem_row[0], "visual element depicted in the plate"),
            )
            if c.rowcount:
                linked += 1
    conn.commit()
    conn.close()
    print(f"Terms inserted: {inserted}")
    print(f"Already present: {skipped}")
    print(f"Term-emblem links added: {linked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
