"""
seed_registers.py — Populate the `registers` JSON column on dictionary_terms.

De Jong's key insight: alchemical terms operate simultaneously across 4 registers:
  - alchemical (material/laboratory)
  - medical (humoral/healing)
  - spiritual (soul/psyche)
  - cosmological (planetary/macrocosm)

Populates registers for PROCESS, SUBSTANCE, qualifying FIGURE, and qualifying CONCEPT terms.
Skips SOURCE_TEXT terms (book titles) and non-polysemous entries.

Idempotent: overwrites existing registers data on re-run.
"""

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "atalanta.db"


# ── Register definitions ─────────────────────────────────────────────────────
# Each entry: slug -> {alchemical, medical, spiritual, cosmological}
# Voice: scholarly but concise, 1-2 sentences per register.
# Grounded in De Jong's analysis of Maier's Atalanta Fugiens.

REGISTERS = {
    # ═══════════════════════════════════════════════════════════════════════════
    # PROCESS TERMS (18)
    # ═══════════════════════════════════════════════════════════════════════════
    "nigredo": {
        "alchemical": "The blackening stage: putrefaction and decomposition of matter in the sealed vessel, producing a foul-smelling black mass that signals the work has begun.",
        "medical": "Corresponds to melancholia and black bile in humoral theory; the saturnine temperament whose leaden darkness must be purged before healing.",
        "spiritual": "The dark night of the soul: ego-death and psychological dissolution that precedes spiritual rebirth and illumination.",
        "cosmological": "Saturn's dominion over the prima materia; the chaos and formlessness from which cosmic order must be extracted, associated with winter and the nadir."
    },
    "albedo": {
        "alchemical": "The whitening: purification of the black mass through washing and sublimation, yielding a pure white earth or powder—the stage of purificatio.",
        "medical": "Restoration of phlegmatic balance; the cleansing of corrupt humors and return to a state of bodily purity, analogous to convalescence.",
        "spiritual": "Illumination after the dark night: the purified soul perceives spiritual light, achieving clarity and the dawn of higher consciousness.",
        "cosmological": "The Moon's dominion; the reflective feminine principle that receives and transmits celestial light, associated with silver and nocturnal dew."
    },
    "citrinitas": {
        "alchemical": "The yellowing: a transitional phase between albedo and rubedo where the white matter takes on a golden hue, signaling the approach of perfection.",
        "medical": "Associated with yellow bile and the choleric temperament in its constructive aspect—vital heat that drives metabolism and bodily vigor.",
        "spiritual": "The dawning of solar consciousness; wisdom emerging between the passive receptivity of albedo and the full realization of rubedo.",
        "cosmological": "The dawn and the rising sun; the transitional moment when lunar silver yields to solar gold in the celestial cycle."
    },
    "rubedo": {
        "alchemical": "The reddening: final stage where the white stone is tinged to red through fermentation with gold, producing the Philosopher's Stone or Red Tincture.",
        "medical": "The sanguine temperament perfected; full vitality, robust health, and the balanced circulation of life-giving blood through the body.",
        "spiritual": "The sacred marriage of soul and body achieved; full individuation, wholeness, and the philosopher's union with the divine ground.",
        "cosmological": "The Sun's dominion and the completion of the cosmic cycle; gold as the perfected metal reflecting the eternal and immutable light of the fixed stars."
    },
    "calcination": {
        "alchemical": "Heating the base matter to extreme temperatures to reduce it to powder or calx, driving off volatile components and exposing the fixed salt.",
        "medical": "The burning away of disease and corrupt matter; cauterization and the application of intense remedial heat to purge infection.",
        "spiritual": "The burning away of ego-attachments and worldly illusions; the trial by fire that strips the soul down to its essential, incombustible core.",
        "cosmological": "The action of celestial fire on terrestrial matter; the solar principle's consuming power that reduces gross forms to their elemental substrate."
    },
    "coniunctio": {
        "alchemical": "The chemical wedding of Sulphur and Mercury—the union of the red king and white queen in the sealed vessel to produce the hermaphroditic Rebis.",
        "medical": "The rebalancing of contrary humors into harmonious proportion; the therapeutic union of hot and cold, moist and dry principles within the body.",
        "spiritual": "The sacred marriage of opposites within the psyche—conscious and unconscious, masculine and feminine—producing wholeness and inner unity.",
        "cosmological": "The conjunction of Sol and Luna, the great celestial marriage whose earthly reflection governs generation and the harmony of macrocosm and microcosm."
    },
    "dissolution": {
        "alchemical": "Dissolving the calcined matter in the mercurial water; the body is liquefied so that its hidden seed may be released from the fixed matrix.",
        "medical": "The therapeutic dissolving of calcified obstructions and hardened humoral deposits; restoring fluidity to the body's circulatory economy.",
        "spiritual": "The dissolution of rigid psychic structures; the letting go of fixed identities and beliefs that obstruct the flow of inner transformation.",
        "cosmological": "Water's primordial action on earth; the lunar solvent that returns differentiated forms to the undifferentiated ocean of potentiality."
    },
    "sublimatio": {
        "alchemical": "Raising volatile spirits from gross matter through heat; the purified essence ascends and condenses on the upper walls of the vessel.",
        "medical": "The refinement of crude bodily spirits into subtle vital pneuma; the upward movement of healing vapors in steam baths and fumigations.",
        "spiritual": "The elevation of consciousness from base material concerns to refined spiritual perception; the ascent of the soul toward the divine.",
        "cosmological": "The ascent of earthly vapors to become celestial dew and rain; the vertical axis connecting earth to heaven in the cosmic circulatory system."
    },
    "putrefaction": {
        "alchemical": "Controlled decomposition of sealed matter producing the characteristic black color of nigredo; the death that is prerequisite to all alchemical generation.",
        "medical": "Analogous to the suppuration of wounds and the crisis of fever—the body's purgative destruction of corrupt matter that must precede healing.",
        "spiritual": "The mortification of the old self; the necessary rotting away of prior identity so that the seed of the new spiritual life may germinate.",
        "cosmological": "The universal law that generation proceeds from corruption, as in the Aristotelian cycle of growth and decay governing all sublunary nature."
    },
    "coagulation": {
        "alchemical": "The fixing and solidifying of volatile matter into stable form; the dissolved components reunite into a new, permanent body—the Stone.",
        "medical": "The restoration of firm bodily substance from dissolved or weakened states; the clotting and consolidation that restores structural integrity.",
        "spiritual": "The embodiment of spiritual insight in stable, lived practice; the crystallization of illumination into enduring character and wisdom.",
        "cosmological": "The cosmic principle by which formless potentiality congeals into manifest creation; the earth-principle that gives permanence to celestial influences."
    },
    "solutio": {
        "alchemical": "The dissolving of solid matter into liquid form using the philosophical mercury; the body must be reduced to its primordial water before reconstitution.",
        "medical": "The liquefaction of hardened deposits and obstructions in the body; restoring the natural flow of humors through dissolution of morbid concretions.",
        "spiritual": "The melting of the hardened heart; emotional release and the surrender of rigid ego-structures to the transformative waters of the unconscious.",
        "cosmological": "The universal solvent principle, the action of the primordial waters from which all forms originally emerged and to which they cyclically return."
    },
    "circulatio": {
        "alchemical": "The repeated distillation and recombination of volatile and fixed components in a sealed vessel, refining the matter through iterative cycles.",
        "medical": "The circulation of blood and vital spirits through the body; the continuous cycle of nourishment, purification, and renewal that sustains life.",
        "spiritual": "The iterative deepening of self-knowledge through repeated cycles of dissolution and reintegration; the spiral path of spiritual maturation.",
        "cosmological": "The great circulation of celestial influences from heaven to earth and back; the Hermetic cycle linking macrocosm and microcosm in perpetual exchange."
    },
    "distillatio": {
        "alchemical": "Separation of volatile essence from gross residue through heating and condensation; the collection of purified spirit in the receiving vessel.",
        "medical": "The extraction of medicinal essences and tinctures from raw plant or mineral matter; the preparation of refined remedies from crude substances.",
        "spiritual": "The careful extraction of essential meaning from the mass of life experience; the distillation of wisdom from the raw material of suffering.",
        "cosmological": "The celestial distillation by which solar heat draws moisture upward to form clouds, returning it as purified rain—nature's alembic."
    },
    "fermentatio": {
        "alchemical": "The leavening of the white stone with a small quantity of gold or its ferment, initiating the final transformation toward the Red Tincture.",
        "medical": "Analogous to the digestive ferment that transforms food into nourishment; the vital leaven that activates the body's regenerative processes.",
        "spiritual": "The catalytic encounter with a living spiritual tradition or teacher that activates latent potential; the yeast of grace working in the soul.",
        "cosmological": "The generative ferment implanted by the Creator in all of nature; the seminal principle that drives cosmic becoming and the multiplication of forms."
    },
    "fixatio": {
        "alchemical": "Rendering volatile matter stable and resistant to fire; the spirit is permanently bound to the body so it can no longer escape through heating.",
        "medical": "The stabilization of volatile symptoms and humoral imbalances; making a cure permanent rather than merely suppressing recurring disease.",
        "spiritual": "The permanent anchoring of spiritual realization in embodied life; ensuring that transcendent insight does not evaporate when the adept returns to daily existence.",
        "cosmological": "The principle of cosmic fixity: the immovable center around which the celestial spheres rotate, the axis mundi that grounds the turning heavens."
    },
    "mortificatio": {
        "alchemical": "The killing of the metal: stripping the base substance of its original form and properties through corrosion, so that it may receive a higher nature.",
        "medical": "The destruction of diseased tissue through caustic remedies; the surgeon's necessary violence that removes corruption to save the patient.",
        "spiritual": "The mortification of the flesh and ego; the ascetic killing of worldly desires that the soul may be liberated from its bondage to matter.",
        "cosmological": "The death phase in the cosmic cycle of death and rebirth; winter's killing frost that is the necessary precondition for spring's regeneration."
    },
    "multiplicatio": {
        "alchemical": "The augmentation of the Stone's potency through repeated cycles of dissolution and coagulation, increasing its power to transmute ever greater quantities of base metal.",
        "medical": "The amplification of a remedy's efficacy through careful preparation and potentiation; a small quantity of perfected medicine healing many patients.",
        "spiritual": "The multiplication of spiritual gifts: as the adept's realization deepens, its transformative influence radiates outward to benefit others.",
        "cosmological": "The principle of cosmic abundance: from the One proceed the many; the fecundity of nature that generates infinite diversity from a single divine seed."
    },
    "projectio": {
        "alchemical": "The final act: casting a small quantity of the perfected Stone onto molten base metal, transmuting it instantly into gold or silver.",
        "medical": "The application of the perfected elixir to the sick body, effecting immediate and complete cure—the projection of health onto disease.",
        "spiritual": "The moment of realized action: projecting inner transformation outward into the world, where the philosopher's perfected nature transmutes all it touches.",
        "cosmological": "The emanation of divine creative power into the material world; the projection of celestial form onto terrestrial matter that sustains all generation."
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # SUBSTANCE TERMS (12)
    # ═══════════════════════════════════════════════════════════════════════════
    "mercurius": {
        "alchemical": "The philosophical Mercury: not common quicksilver but the universal solvent and volatile principle—the moist, cold, feminine component of the metallic dyad.",
        "medical": "The vital spirit or pneuma that circulates through the body; the mercurial principle governing nerve function, respiration, and the subtle fluids.",
        "spiritual": "The anima or world-soul; the mediating spirit that connects body and soul, matter and intellect—Hermes as psychopomp guiding transformation.",
        "cosmological": "The planet Mercury as cosmic messenger between Sun and Moon; the principle of mediation and communication linking all levels of the great chain of being."
    },
    "sulphur": {
        "alchemical": "The philosophical Sulphur: the hot, dry, masculine, combustible principle in metals—the active seed that gives form and color to the metallic body.",
        "medical": "The vital heat or innate calor that drives digestion, growth, and generation; the choleric fire that, in proper measure, sustains bodily life.",
        "spiritual": "The soul's desire and will; the active, formative principle of consciousness that shapes raw experience into meaning and purpose.",
        "cosmological": "The solar and fiery principle; Sulphur corresponds to the Sun's generative heat that activates all earthly matter through its formative rays."
    },
    "sol": {
        "alchemical": "Gold in its philosophical sense: the perfect, incorruptible metal whose seed must be extracted and multiplied to produce the Philosopher's Stone.",
        "medical": "The heart as the body's sun; the vital center radiating life-giving warmth and sanguine vitality to every organ through arterial circulation.",
        "spiritual": "The illuminated consciousness; the divine spark or inner gold that the Great Work seeks to reveal beneath the dross of unrefined nature.",
        "cosmological": "The Sun as sovereign of the planetary hierarchy; source of all light, heat, and generative power in the macrocosm, father of the alchemical dyad."
    },
    "luna": {
        "alchemical": "Silver in its philosophical sense: the receptive, reflective metal that must be conjoined with Sol to achieve the complete work.",
        "medical": "The brain and lymphatic system; the cool, moist, phlegmatic principle governing the body's receptive and reflective capacities.",
        "spiritual": "The receptive, contemplative faculty of the soul; the mirror that reflects divine light without generating it—imagination and intuition.",
        "cosmological": "The Moon as cosmic mediator between celestial fire and terrestrial water; governess of tides, menstruation, and all cyclical change in the sublunary world."
    },
    "prima-materia": {
        "alchemical": "The undifferentiated base substance from which the Stone is made; paradoxically described as worthless and everywhere available, yet unrecognized by the ignorant.",
        "medical": "The radical moisture or fundamental bodily substrate that precedes differentiation into the four humors; the basic vitality underlying all physiological processes.",
        "spiritual": "The raw, unformed psyche before the work of individuation begins; the chaotic prima materia of the unconscious from which the Self must be extracted.",
        "cosmological": "The primordial chaos or hyle from which God fashioned the cosmos; the formless substrate underlying all manifest creation, coeval with the Creator."
    },
    "rebis": {
        "alchemical": "The 'two-thing': the hermaphroditic product of the coniunctio, uniting Sulphur and Mercury, Sol and Luna, into a single perfected substance.",
        "medical": "The perfected balance of all contrary qualities in the body; the androgynous ideal of complete humoral equilibrium transcending any single temperament.",
        "spiritual": "The integrated self in which all opposites—masculine and feminine, conscious and unconscious—are reconciled into a unified wholeness.",
        "cosmological": "The cosmic androgyne; the primordial unity that preceded the differentiation of the elements, and to which the perfected cosmos returns."
    },
    "aqua-regia": {
        "alchemical": "The royal water: a mixture of nitric and hydrochloric acids capable of dissolving gold—the only solvent powerful enough to attack the noblest metal.",
        "medical": "A corrosive remedy of extreme potency, used in minute doses to dissolve calcified obstructions that milder treatments cannot address.",
        "spiritual": "The supreme solvent of ego: a crisis or ordeal so powerful it dissolves even the most fixed and defended aspects of the personality.",
        "cosmological": "The primordial deluge or universal solvent; the catastrophic dissolution that reduces even the most permanent cosmic structures to their elements."
    },
    "aqua-vitae": {
        "alchemical": "The water of life: a purified distillate—often the philosophical mercury in its most refined form—capable of reviving dead metals and perfecting the Stone.",
        "medical": "The quintessence extracted from wine or herbs; a life-giving elixir believed to restore vitality, extend life, and cure otherwise fatal diseases.",
        "spiritual": "The living water of divine grace; the spiritual nourishment that sustains the soul through the arid phases of the Great Work.",
        "cosmological": "The celestial dew or astral moisture that descends from the stars to vivify all terrestrial life; the subtle medium through which cosmic influences operate."
    },
    "aurum-philosophicum": {
        "alchemical": "Philosophical gold: not common bullion but the perfected seed of gold freed from material impurity—the active principle of the completed Stone.",
        "medical": "The perfected vital essence; potable gold as the supreme medicine that restores perfect health by harmonizing all bodily processes to their ideal state.",
        "spiritual": "The incorruptible core of the self; the imperishable spiritual gold that survives every trial and constitutes the philosopher's true attainment.",
        "cosmological": "The solar substance in its purest form; the celestial gold that corresponds to the Sun's essence rather than its mere terrestrial reflection in mineral veins."
    },
    "elixir": {
        "alchemical": "The perfected tincture in liquid form: identical in substance to the Philosopher's Stone but prepared as a drinkable solution for medicinal projection.",
        "medical": "The universal medicine capable of curing all diseases, restoring youth, and prolonging life indefinitely—the supreme goal of iatrochemistry.",
        "spiritual": "The draught of immortality; the concentrated essence of spiritual realization that, once imbibed, permanently transforms the aspirant's nature.",
        "cosmological": "The quintessence or fifth element: the celestial substance free from corruption that permeates and sustains the four mundane elements."
    },
    "tinctura": {
        "alchemical": "The coloring power of the Stone: the capacity to permanently alter the nature of base metals by imparting gold's essential quality through superficial contact.",
        "medical": "A concentrated medicinal extract prepared by dissolving a substance's active principle in alcohol or acid; the coloring and curative essence of a remedy.",
        "spiritual": "The transformative influence of realized wisdom; the capacity of an awakened being to alter the character of those they encounter.",
        "cosmological": "The formative power by which celestial influences imprint their qualities on terrestrial matter; the coloring of earthly substance by stellar virtues."
    },
    "white-lead": {
        "alchemical": "Plumbum album or cerussa: the whitened form of lead, an intermediate product signaling partial purification on the way from Saturn's darkness to lunar silver.",
        "medical": "Used in traditional pharmacopoeia as a desiccant and cooling agent for inflamed wounds, despite its known toxicity—a dangerous remedy requiring careful dosage.",
        "spiritual": "The partially purified soul: no longer in the blackness of nigredo but not yet fully illuminated; the intermediate stage of spiritual convalescence.",
        "cosmological": "The transition from Saturn (lead) toward Luna (silver); the liminal zone between planetary influences where base matter begins to receive celestial whiteness."
    },
    "aurum-potabile": {
        "alchemical": "Drinkable gold: the perfected metal rendered into a liquid tincture, often by repeated dissolution in mercurial water; the convertible form of the Stone for ingestion.",
        "medical": "The supreme Paracelsian remedy, claimed by iatrochemists from Paracelsus to Maier as a panacea capable of restoring radical heat, prolonging life, and curing the most refractory diseases.",
        "spiritual": "The internalized solar principle: golden insight that, having been swallowed, transmutes the inner constitution from base reactivity to the radiant equanimity of the realized soul.",
        "cosmological": "The Sun condensed into liquid form; the celestial gold drawn down through alchemical art so the heavens' incorruptible virtue may circulate through the sublunary body."
    },
    "green-lion": {
        "alchemical": "The vitriolic mineral acid (often green vitriol or its derivatives) figured as a green lion that 'devours the sun': the corrosive solvent that dissolves gold to begin the work.",
        "medical": "The aggressive purgative whose corrosive virtue scours obstructed humors from the body; the violent remedy whose green color signals its derivation from copper-bearing minerals.",
        "spiritual": "The hungry, untamed vitality of the unintegrated psyche; the wild green of unprocessed life-force that consumes the sun-king of consciousness before it can be tempered.",
        "cosmological": "Venus and Mars commixed: the copper-iron complex whose vegetal green marks the earth's productive force, the chthonic appetite at the root of all generation."
    },
    "quintessence": {
        "alchemical": "The fifth essence: the incorruptible substrate distilled out of the four elements, equated by adepts with the Stone's purest form and the perfected matter that grounds all transmutation.",
        "medical": "The vital pneuma or radical moisture that animates the body; the subtle medium whose extraction and re-administration constitutes the spagyrist's universal medicine.",
        "spiritual": "The incorruptible kernel of the soul that survives every dissolution; the imperishable witness whose recovery is the goal of contemplative work in the Hermetic tradition.",
        "cosmological": "Aristotle's aether: the supralunary substance of the celestial spheres, weightless and unchanging, whose downward refraction into terrestrial matter is what alchemy strives to capture."
    },
    "vitriol": {
        "alchemical": "The hydrated metal sulphates (especially copper and iron) whose acronymic motto V.I.T.R.I.O.L.—visita interiora terrae rectificando invenies occultum lapidem—encodes the descent into hidden interior matter.",
        "medical": "Iatrochemistry's powerful astringent and corrosive: vitriolic preparations were used to cauterize ulcers, dry rheums, and (cautiously) as internal purgatives in Paracelsian dosage.",
        "spiritual": "The injunction to interiority: 'visit the inner parts of the earth' as the imperative to descend into the unconscious, where rectification of the shadow uncovers the hidden Stone.",
        "cosmological": "The mineral residue of celestial influence stored in the earth's crystalline depths; the chthonic concentration of solar and venusian virtues solidified into colored salts."
    },
    "lac-virginis": {
        "alchemical": "The Virgin's Milk: a name for the pure, white, mercurial water of the philosophers—the lactescent solvent that nourishes the embryonic Stone within the philosophical egg.",
        "medical": "Whitened milk-tinctures and lactic preparations used as gentle nutritives for invalids and infants; the fluidum vitae whose purity restores depleted radical moisture.",
        "spiritual": "The sustaining grace that feeds the newborn spiritual life; the pure, untainted nourishment given by the Sophianic feminine to the soul reborn after nigredo.",
        "cosmological": "The lunar dew that descends as silver-white moisture in the cool of dawn; the maternal milk of the Moon that fertilizes terrestrial generation in classical natural philosophy."
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # FIGURE TERMS (qualifying — those with alchemical symbolism)
    # ═══════════════════════════════════════════════════════════════════════════
    "hermaphrodite": {
        "alchemical": "The Rebis or two-headed figure: product of the chemical wedding of Sol and Luna, depicted in Emblem XXXIV lying on a tomb—the perfected union of Sulphur and Mercury.",
        "medical": "The ideal of complete bodily equilibrium in which masculine and feminine humoral qualities are perfectly balanced, transcending the dominance of any single temperament.",
        "spiritual": "The integrated psyche: the union of animus and anima, conscious and unconscious, that Jung identified as the goal of individuation—drawing directly on alchemical imagery.",
        "cosmological": "The primordial androgyne of Platonic and Hermetic cosmology; the undivided unity that existed before the separation of heaven and earth, male and female."
    },
    "dragon": {
        "alchemical": "The devouring mercurial serpent: raw, unrefined prima materia in its most dangerous and volatile state, which must be slain and reborn as the philosophical mercury.",
        "medical": "The virulent disease or toxic agent that must be conquered and transmuted into medicine; poison as potential remedy when properly mastered.",
        "spiritual": "The guardian of the threshold: the terrifying psychic forces that must be confronted and integrated before the treasure of self-knowledge can be won.",
        "cosmological": "The ouroboros or world-serpent encircling the cosmos; the self-devouring cycle of creation and destruction that sustains the eternal return of all things."
    },
    "rex": {
        "alchemical": "The Red King: philosophical Sulphur, the solar-masculine principle that must be united with the White Queen (Mercury) to produce the Stone. In Emblem XXIV, the king is cured of melancholy.",
        "medical": "The dominant vital principle or ruling humor; in Maier's allegory, King Duenech's melancholic sickness represents the imbalance that the art must cure.",
        "spiritual": "The conscious will and ruling ego whose saturnine fixity must be dissolved before it can be reborn in a higher, more integrated form.",
        "cosmological": "The Sun as cosmic sovereign; the kingly principle of order, authority, and formative power that governs the celestial hierarchy."
    },
    "regina": {
        "alchemical": "The White Queen: philosophical Mercury, the lunar-feminine principle whose volatile, moist nature must be fixed and united with the Red King to complete the work.",
        "medical": "The receptive, nourishing aspect of the body's economy; the phlegmatic-sanguine balance that sustains fertility, moisture, and regenerative capacity.",
        "spiritual": "The soul's receptive wisdom; the feminine principle of intuition and contemplation that complements and completes the active masculine will.",
        "cosmological": "The Moon as cosmic consort; the reflective, generative, and cyclical principle that receives solar light and transmits it to the sublunary world."
    },
    "latona": {
        "alchemical": "An imperfect body composed of Sol and Luna, as Bonus describes: she must be whitened (dealbate Latonem) by washing with Mercury to reveal the hidden gold and silver within.",
        "medical": "The diseased or impure body harboring latent health; the patient whose mixed condition contains the seeds of both sickness and cure.",
        "spiritual": "The soul burdened by unresolved contraries; the mother of Apollo and Diana who suffers persecution until her divine children—light and reflection—are born.",
        "cosmological": "The material world pregnant with celestial potential; the earthly matrix from which solar and lunar principles must be separated and purified by the art."
    },
    "sphinx": {
        "alchemical": "The riddle of the Stone: the enigmatic nature of the prima materia, which is described in contradictory terms and can only be identified by the wise who solve her riddle.",
        "medical": "The diagnostic puzzle: the hidden cause of disease that presents contradictory symptoms and can only be identified by the physician who reads nature's signs correctly.",
        "spiritual": "The guardian of esoteric knowledge who devours those unworthy of initiation; only the philosopher who knows himself (as Oedipus) can pass safely.",
        "cosmological": "The composite creature uniting human, animal, and avian natures—a microcosmic emblem of the three kingdoms (mineral, vegetable, animal) united under a single enigma."
    },
    "osiris": {
        "alchemical": "The dismembered king whose body is scattered and must be reassembled by Isis: an allegory of the dissolution and reconstitution of matter in the Great Work. Maier connects Typhon's putrefaction of Osiris directly to the alchemical process.",
        "medical": "The diseased body fragmented by illness whose scattered parts (organs, humors) must be gathered and reintegrated by the healing art.",
        "spiritual": "The divine self torn apart by the forces of chaos (Typhon) and reassembled through love and devotion (Isis); death and resurrection as spiritual paradigm.",
        "cosmological": "The solar deity whose annual death and resurrection mirrors the agricultural cycle of seed, growth, harvest, and renewal—the cosmic rhythm of dying and rising gods."
    },
    "typhon": {
        "alchemical": "The destructive force of putrefaction personified: Typhon dismembers Osiris, representing the necessary corruption and dissolution that precedes alchemical regeneration.",
        "medical": "The acute crisis of disease; the violent fever or toxic eruption that breaks down the body's order but, if survived, leads to purgation and recovery.",
        "spiritual": "The shadow and destructive impulse that attacks the integrity of the self; the chaotic force that must be acknowledged and overcome in the process of individuation.",
        "cosmological": "The principle of cosmic disorder and entropy; the serpentine chaos-monster whose periodic eruptions disrupt celestial harmony but ultimately serve the cycle of renewal."
    },
    "isis": {
        "alchemical": "The reassembler: Isis gathers Osiris's scattered members and restores them to wholeness, representing the careful recombination of separated alchemical components after dissolution.",
        "medical": "The healing art personified: the patient, systematic work of gathering scattered vital forces and reintegrating them into a functioning bodily whole.",
        "spiritual": "The devoted seeker who through love, persistence, and wisdom reconstitutes what chaos has fragmented; the feminine principle of restorative wholeness.",
        "cosmological": "The veiled goddess of nature whose secrets are hidden from the profane; she governs the regenerative cycles of the natural world and the Nile's fertile inundation."
    },
    "venus": {
        "alchemical": "Copper in the planetary-metallic correspondence; the impure but promising metal whose green color and malleability connect it to organic growth and early-stage transformation.",
        "medical": "The principle of desire and attraction in the body; the generative and reproductive forces governed by warmth, moisture, and the sanguine humor.",
        "spiritual": "The power of love and beauty as transformative agents; the attractive force that draws opposites together and makes the coniunctio possible.",
        "cosmological": "The planet Venus as morning and evening star; the celestial embodiment of harmony, proportion, and the attractive power that binds the cosmos together."
    },
    "adonis": {
        "alchemical": "The beautiful youth slain by the boar: an allegory of the precious substance destroyed in the violent phase of the work, whose blood (tincture) colors the white rose red.",
        "medical": "The principle of youthful vitality cut short by violence or disease; the transience of bodily beauty that must be preserved through the physician's art.",
        "spiritual": "The dying and rising god of desire; the soul's attachment to sensory beauty that must be sacrificed before resurrection into a higher, imperishable form.",
        "cosmological": "The annual vegetation cycle embodied: Adonis's death in autumn and rebirth in spring mirrors the cosmic rhythm of solar withdrawal and return."
    },
    "king-duenech": {
        "alchemical": "The melancholic king of the Turba Philosophorum who must be cured in the steam bath: an allegory of the base metal requiring dissolution and purification to yield its hidden gold.",
        "medical": "The paradigmatic melancholic patient: his saturnine excess of black bile must be treated with moist heat (the steam bath) to restore humoral equilibrium.",
        "spiritual": "The soul imprisoned by saturnine depression; the leaden weight of acedia that can only be lifted through the warmth of spiritual practice and purgative ordeal.",
        "cosmological": "Saturn's influence made flesh: the heavy, cold, dry principle that must be warmed and moistened by solar and lunar forces to participate in cosmic harmony."
    },
    "atalanta": {
        "alchemical": "The fugitive virgin of Maier's title: cipher of the volatile philosophical mercury that must be arrested in the sealed vessel before it escapes through heating.",
        "medical": "The hyperactive vital spirit that exhausts the body when it cannot be fixed; the runaway pulse and febrile heat that the physician must slow without quenching.",
        "spiritual": "The swift, untamable soul whose flight from contemplation must be redirected by the golden apples of insight; the seeker pursued and pursuing in the same instant.",
        "cosmological": "The Moon in her swift rotation, outpacing the Sun until the conjunction; the lunar principle whose flight defines the rhythm in which solar gold can finally overtake her."
    },
    "hercules": {
        "alchemical": "The hero whose twelve labors Maier (in Arcana Arcanissima) reads as encoded operations of the opus: each monstrous adversary a stage of matter, each victory a chemical accomplishment.",
        "medical": "The exemplar of robust sanguine vigor; his strength figures the ideal physiological constitution that has subdued the disordered humors and tamed the body's monsters.",
        "spiritual": "The labor-bound soul: the heroic ego that must complete a sequence of trials, each one purgative, before earning apotheosis among the stars.",
        "cosmological": "The solar hero whose twelve labors track the zodiacal year; his cycle of trials is the Sun's annual passage through the houses, mapping the cosmos onto biographical time."
    },
    "hermes-trismegistus": {
        "alchemical": "The thrice-greatest patron of the art and putative author of the Tabula Smaragdina, whose 'as above, so below' is alchemy's foundational axiom and the warrant for every operation.",
        "medical": "The legendary first physician of the Hermetic tradition; the source from which Galenic and Paracelsian medicine alike claimed pharmacological authority for the mineral arcana.",
        "spiritual": "The mediator between divine and human realms; the messenger whose Corpus Hermeticum supplied Renaissance Christian Hermetism with its model of the soul's ascent.",
        "cosmological": "Mercury thrice over—planet, principle, and god; the cosmic intermediary whose triple greatness encompasses the heavens, earth, and underworld unified by the caduceus's intertwined serpents."
    },
    "ouroboros": {
        "alchemical": "The serpent biting its tail: figure of the closed circulatory work in the sealed vessel, where dissolution and coagulation continually feed each other until perfection.",
        "medical": "The body's self-renewing economy: the cycle of digestion, assimilation, and excretion in which what is consumed becomes substance and what is substance is consumed.",
        "spiritual": "The eternal return of self-knowledge; the recognition that every ending is also a beginning, that the soul's work is circular rather than linear and admits no final terminus.",
        "cosmological": "The cosmos as self-contained whole: the great circle of the heavens enclosing all generation and corruption, the All-and-One whose Greek emblem (hen to pan) it inscribes."
    },
    "paracelsus": {
        "alchemical": "Theophrastus von Hohenheim (1493–1541): the iatrochemical reformer whose Tria Prima (Sulphur, Mercury, Salt) restructured alchemical theory and whose authority Maier repeatedly invokes.",
        "medical": "The founder of iatrochemistry: replacing Galenic humoralism with chemical pharmacology, he prescribed mineral and metallic arcana whose preparation depended on alchemical operations.",
        "spiritual": "The astrum or inner star: Paracelsus held that each soul carries an inner heaven whose recognition and cultivation is the true work, and Maier extends this to the meditating reader.",
        "cosmological": "The doctrine of signatures and of macrocosm-microcosm correspondence: Paracelsus's insistence that every terrestrial body bears the signature of its celestial counterpart underwrites Maier's emblematic method."
    },
    "boreas": {
        "alchemical": "The North Wind of Emblem I who carries the swaddled infant in his belly: figure of the volatile aerial principle (philosophical air or spirit) that transports the embryonic Stone through gestation in the sealed vessel.",
        "medical": "The cold, dry north wind of Hippocratic meteorology: bracing and astringent, it figures the constitutional cooling necessary to balance phlegmatic excess and to fix unstable spirits in the body.",
        "spiritual": "The pneumatic carrier of the nascent soul; the bracing inrush of inspiration whose chill must be endured before its life-giving cargo can be brought to term within the contemplative.",
        "cosmological": "The Hyperborean wind issuing from the cosmic North Pole: the celestial axis-direction whose cold spiritus, carrying the seed of generation, descends to fertilize the sublunary world."
    },
    "hippomenes": {
        "alchemical": "The suitor of Maier's title who arrests Atalanta with three golden apples: figure of the operative artist who fixes volatile mercury through the timely interposition of solar gold.",
        "medical": "The therapeutic intelligence that slows runaway vital spirit by interposing nourishing substances at the right intervals; the physician's art of cadence and dosage.",
        "spiritual": "The contemplative who paces the soul's pursuit of wisdom by deploying compelling images at the right moments; the reader of Atalanta Fugiens as Maier scripts him.",
        "cosmological": "The Sun overtaking the swift Moon at the conjunction; the solar principle whose three apples (gold) successively brake the lunar flight until they meet at the same celestial degree."
    },
    "jason": {
        "alchemical": "The Argonaut whose Colchian quest De Jong and Maier read as a complete alchemical voyage: the dragon-guarded Fleece is the Stone, the Argo the vessel, Medea's drugs the necessary preparations.",
        "medical": "The physician-hero who undertakes the long therapeutic journey, mastering exotic remedies and obstacles to retrieve the supreme medicament that ordinary practice cannot reach.",
        "spiritual": "The disciplined ego embarking on a guided voyage through unconscious waters; the heroic seeker whose success requires both personal courage and a counsellor's secret knowledge.",
        "cosmological": "The solar hero traversing the eastern horizon to seize the celestial fleece in the dawn of Aries; the annual itinerary of the Sun reread as quest narrative."
    },
    "medea": {
        "alchemical": "The Colchian sorceress whose pharmaka enable Jason to seize the Fleece: figure of the chemical knowledge—the secret tinctures and washes—without which the operative artist accomplishes nothing.",
        "medical": "The herbalist of dangerous arcana: her ointments anaesthetize the dragon and renew aged Aeson's blood, archetypes of the powerful, ambivalent remedies that iatrochemistry inherits.",
        "spiritual": "The dark feminine wisdom whose knowledge the seeker must accept on her terms; the unconscious counsellor whose drugs both enable transformation and exact a tragic price.",
        "cosmological": "The sublunary lunar feminine whose magical waters embody the moon's influence over plants, blood, and tides; the mediating Hecatean intelligence at the threshold of three worlds."
    },
    "kronos-saturn": {
        "alchemical": "The aged king who devours his children: figure of the heavy, cold, fixed lead-principle that must itself be dissolved (castrated, in the myth) before generation can yield purer metals.",
        "medical": "The patron of the melancholic temperament: black bile, cold and dry, whose excess produces depression, retention, and the saturnine diseases that humoral medicine sought to relieve.",
        "spiritual": "The weight of acedia and limit-experience; the contemplative descent into depressive interiority whose gravity, properly endured, becomes the foundation for all subsequent uplift.",
        "cosmological": "The outermost planet of the traditional spheres: slow, cold, and ringed; the chronological boundary between sublunary becoming and the unchanging stars beyond."
    },
    "ulysses-odysseus": {
        "alchemical": "The cunning navigator of Maier's frontispiece: cipher for the wily artist whose homeward voyage—through Circean transformations and Sirenic temptations—models the long return-journey of the opus.",
        "medical": "The patient who endures protracted convalescence with cunning rather than force; the long regimen whose success depends on intelligent improvisation against shifting symptoms.",
        "spiritual": "The polytropos soul, much-turning and adaptive; the seeker whose homecoming requires recognizing transformations of self and other, and refusing premature arrivals.",
        "cosmological": "The wandering planet (planos) personified: the celestial body whose long, looped motions through the zodiac chart a journey home that can be read as both literal and allegorical."
    },
    "oedipus": {
        "alchemical": "The interpreter of the Sphinx's riddle whom Maier (especially in his Arcana Arcanissima) treats as paradigm of the alchemical reader: the one whose decipherment of veiled language is itself the operation.",
        "medical": "The diagnostician whose riddle-solving epitomizes Hippocratic semiotics: reading occult signs in surface symptoms to name the hidden cause, so that the physician's word itself begins the cure.",
        "spiritual": "The seeker confronting the riddle of his own being; the soul whose self-recognition is both liberation and tragic burden, anticipating the modern hermeneutic of the unconscious.",
        "cosmological": "The figure positioned at a cosmological crossroads where the human, the bestial, and the divine meet; the riddle of being-in-the-world that the four-elementary cosmos poses to its inhabitants."
    },
    "ceres": {
        "alchemical": "The grain-goddess Demeter whose fruits Maier invokes for the vegetative fixation of Mercury: the maternal earth-principle that nourishes the embryonic Stone through coagulating humidity.",
        "medical": "The patroness of nutrition: bread and grain as the staple of bodily renewal; her cult of the Eleusinian Mysteries explicitly linked to the renewal of life through ingestion.",
        "spiritual": "The Eleusinian initiatrix whose mysteries enacted death and rebirth in the grain; the cyclical mother whose loss and recovery of Persephone models the soul's descent and return.",
        "cosmological": "The earth-element personified: the receptive feminine ground in which celestial seed is sown, whose fertility tracks the solar year and the cycle of seasons."
    },
    "naaman": {
        "alchemical": "The Syrian commander whose sevenfold immersion in the Jordan cleanses his leprosy: a biblical analogue Maier and earlier adepts read for the seven washings (ablutions) that purify the matter.",
        "medical": "The paradigmatic case of cure-by-bathing: the therapeutic immersion that humoral and Paracelsian medicine alike inherited from biblical and classical balneology.",
        "spiritual": "The pride-stricken seeker who must accept a humble remedy; the soul whose healing depends on relinquishing its own scheme and submitting to the prescribed sevenfold work.",
        "cosmological": "The seven planetary spheres traversed by the soul in its purification, each ablution corresponding to the soul's stripping of one planetary garment in the Hermetic ascent."
    },
    "alchemical-eagle": {
        "alchemical": "The volatile principle in its ascending phase: the eagle that flies up the alembic, distilled spirit rising from the calcined body—paired iconographically with the toad or lion of fixity.",
        "medical": "The sublimated vital spirit (spiritus animalis) raised from the gross humors; the refined pneuma that medicine seeks to extract and re-administer as quintessential remedy.",
        "spiritual": "The soul's upward flight in contemplation; the visionary capacity that, lifted on hot drafts, perceives from above what the earthbound understanding cannot.",
        "cosmological": "The sign of Jupiter's bird and of the air-element; the celestial messenger whose ascent and descent figure the vertical traffic between heaven and earth."
    },
    "alchemical-lion": {
        "alchemical": "The fixed solar Sulphur in animal form: the red lion (perfected gold) and green lion (vitriolic solvent) of the iconographic tradition, marking opposite poles of the work.",
        "medical": "The sanguine-choleric vigor in its noble form; the fierce vital heat that, properly governed, expresses itself as constitutional strength rather than febrile rage.",
        "spiritual": "The royal spiritedness of the awakened ego; the sovereign self that has subdued lesser passions and bears its solar nature with dignity rather than violence.",
        "cosmological": "The zodiacal Leo as the Sun's domicile; the celestial sign whose midsummer fire concentrates solar virtue at its peak terrestrial manifestation."
    },
    "salamander": {
        "alchemical": "The creature reputed to live in fire: figure of the incombustible Sulphur or fixed essence that thrives where common matter is consumed; the irreducible kernel revealed by calcination.",
        "medical": "The constitutional principle of innate heat (calor innatus) whose flame must be sustained without exhausting it; the radical fire whose preservation is the physician's central task.",
        "spiritual": "The soul's incombustible witness that survives every purgative ordeal; the inner essence that the trial by fire does not destroy but rather discloses.",
        "cosmological": "The element fire personified in elemental zoology; the fiery salamander as antitype of the watery undine, marking the active principle of the four-elementary cosmos."
    },
    "raven-crow": {
        "alchemical": "The black bird of nigredo: the corvine sign, often depicted as a crow's head on the dying king, that announces the work's onset and the matter's putrefaction in the sealed vessel.",
        "medical": "The sign of black bile and saturnine corruption: the corvine prognosis appearing in the patient whose humors have darkened and whose treatment must begin with controlled putrefaction.",
        "spiritual": "The soul's dark night marked unmistakably; the corvine omen at the entrance of the underworld journey, when ego-light fails and the deeper work begins.",
        "cosmological": "Saturn's bird in the zodiac of beasts; the black-feathered emissary of the outermost planet whose appearance signals the moment for descent rather than ascent."
    },
    "philosophical-bird": {
        "alchemical": "Generic name for any volatile aerial spirit raised in the alembic: the philosophical bird is whatever rises and must be brought back down—mercury, spirit, or ascending vapor.",
        "medical": "The body's volatile spirits (spiritus naturalis, vitalis, animalis) whose flight and return in the vessels constitute the very rhythm of life; the breath-soul of physiology.",
        "spiritual": "The ascending and descending aspect of every spiritual gift: insight that flies up must come down again into embodied life, or it remains a sterile exhalation.",
        "cosmological": "The aerial messenger between sublunary and supralunary realms; the avian intermediary that classical and Renaissance cosmology placed in the air-element between earth and fire."
    },
    "alchemical-wolf": {
        "alchemical": "The grey wolf of antimony (lupus metallorum) who 'devours the king': the antimonial sulphide used to purge gold of its impurities, after which the wolf itself is consumed in the cupelling fire.",
        "medical": "The aggressive purgative (antimony preparations were central to Paracelsian medicine) whose violent action removes diseased matter at the cost of considerable risk to the patient.",
        "spiritual": "The shadow-aspect that consumes the inflated solar ego before being itself dissolved; the dark agent of necessary destruction in the work of integration.",
        "cosmological": "Mars's bestial avatar: the predatory principle whose role in cosmic economy is to clear the way for renewal by devouring what has overstayed its season."
    },
    "alchemical-dog": {
        "alchemical": "The Khorasan dog and Armenian bitch of the Turba and the Rosarium, whose biting union (often paired with the wolf) figures the controlled hostility of two mercurial principles fixing each other in the vessel.",
        "medical": "The faithful, fierce vigilance of innate heat guarding the body's threshold; the watchdog principle that recognizes corruption and bites it off before infection spreads.",
        "spiritual": "The threshold-guardian of the inner work; the loyal but biting capacity of self-discipline that defends the contemplative space against the wolf of dispersion.",
        "cosmological": "Anubis at the underworld gate; the Sirius-dog whose heliacal rising marks seasonal thresholds and whose celestial counterpart guards the boundary between worlds."
    },
    "alchemical-toad": {
        "alchemical": "The earthly counter-pole to the airy eagle: the terra damnata or fixed faecal residue at the bottom of the alembic, whose stubborn weight is what the volatile spirit must return to and animate.",
        "medical": "The melancholic deposit of the body—black bile sediment, sluggish humor—that resists circulation; the toad-like residue medicine must dissolve and reincorporate rather than discard.",
        "spiritual": "The repulsive but indispensable shadow-matter of the psyche; the ugly, low, unwanted material that contemplation must befriend, since the eagle without the toad cannot fly home.",
        "cosmological": "The earth-element in its densest aspect: the chthonic principle whose toad-emblem signals the deep, cool, moist substrate from which all generation proceeds."
    },
    "apocalyptic-woman": {
        "alchemical": "The 'woman clothed with the sun, with the moon under her feet' (Revelation 12) repurposed by alchemy as the perfected matter pregnant with the Stone, encompassing solar and lunar principles in a single radiant figure.",
        "medical": "The supreme medicine personified as celestial bride: the panacea whose conception and bringing-to-birth requires the conjunction of Sol and Luna within the Paracelsian vessel-as-womb.",
        "spiritual": "The Sophianic feminine of Christian Hermetism; the wisdom-figure whose appearance signals the soul's apocalyptic transformation and the breaking-in of the new aeon.",
        "cosmological": "The cosmos as a single luminous bride: sun-clothed, moon-footed, star-crowned—the mediating world-soul whose imminent delivery is the cosmic counterpart of the alchemical work."
    },
    "cybele": {
        "alchemical": "The Phrygian Magna Mater whose lion-drawn chariot and tympanum-rites figure the maternal-vegetative power that gestates the Stone within the sealed vessel.",
        "medical": "The patroness of fertility-medicine whose ecstatic cult preserved an ancient pharmacology of mineral and herbal remedies tied to the great mother's seasonal rites.",
        "spiritual": "The terrible Mother whose galli-priests' self-castration figures the radical sacrifice of generative power that the spiritual work demands; the dark counterpart to Sophia.",
        "cosmological": "Earth as enthroned goddess: the personified terrestrial sphere from which all metals are mined as her milk, attended by the lions of solar fixity and the keys of celestial influx."
    },
    "dryad": {
        "alchemical": "The tree-spirit of the philosophical wood: the indwelling vital principle of the alchemical tree (arbor philosophica) whose fruits are the metals and whose sap is the universal solvent.",
        "medical": "The vegetal soul (anima vegetativa) whose sap circulates as the body's nutritive principle; the dryadic life-force that herbal medicine extracts from living plants at the right hour.",
        "spiritual": "The animating presence within nature whose recognition transforms the contemplative's relation to the world; the soul of the world made visible in particular living forms.",
        "cosmological": "The localized anima mundi resident in each tree as in each star; the principle by which classical and Renaissance natural philosophy populated the cosmos with intermediate intelligences."
    },
    "geryon": {
        "alchemical": "The three-bodied giant of Hercules' tenth labor: figure of the triple matter (or the Tria Prima) that the operative hero must overcome and unify in a single mastered substance.",
        "medical": "The morbid triplication of one principle—triple imbalance in body, spirit, and soul—that Paracelsian diagnosis would address by restoring proportion among Sulphur, Mercury, and Salt.",
        "spiritual": "The fragmented self that presents three contradictory faces to the world; the disunified ego that must be slain at the threshold before the integrated personality can be born.",
        "cosmological": "The far-western boundary of the inhabited world (Geryon dwelt at Erytheia); the threshold-monster guarding the Pillars of Hercules where the cosmos opens onto the unknown."
    },
    "screech-owl": {
        "alchemical": "The night-bird of Saturn whose cry punctuates nigredo: emblematic companion of the dying king and of melancholy contemplation, signaling the long darkness from which the work begins.",
        "medical": "The prognostic of saturnine illness: the owl as omen of black-bile crisis, the diagnostic sign that the patient has entered the depressive phase requiring patience rather than intervention.",
        "spiritual": "The wisdom of the dark; the contemplative who, like the owl, sees in night what the daylit mind cannot perceive—a wisdom acquired only by enduring the long sojourn in obscurity.",
        "cosmological": "Athena's bird in its saturnine aspect: the celestial creature whose habits map onto the cold, slow, outermost planet, perceiving from that elevation what nearer luminaries miss."
    },
    "lusus-serius": {
        "alchemical": "The serious game: Maier's term (and book title, 1616) for the alchemical work understood as ludic discipline—rule-bound, playful, rigorous, where the operations are moves in a long game.",
        "medical": "The therapeutic regimen as game: the patient and physician as players whose moves (diet, dose, rest, exercise) follow rules and produce outcomes only through sustained, attentive play.",
        "spiritual": "The contemplative life as serious play; the Renaissance Christian-humanist insistence that joyful engagement with image, riddle, and song is the real work, not its preface.",
        "cosmological": "The cosmos itself as ludus—a divine play-space whose ordered rules generate the spectacle of becoming; an idea Maier and Andreae share with the broader humanist tradition."
    },
    "prisca-sapientia": {
        "alchemical": "The 'ancient wisdom' Maier and his predecessors locate in Egypt, Greece, and the Hebrew patriarchs: a unified primordial knowledge of nature, broken by time and recoverable only through the alchemical recovery of forgotten meaning.",
        "medical": "The lost original medicine—Hermetic, Mosaic, or Aesculapian—of which Galenic, Arabic, and Paracelsian medicines are partial heirs; the tradition iatrochemists claimed to be reassembling.",
        "spiritual": "The single original revelation diffused through diverse traditions; the Renaissance Hermetist's conviction that Plato, Hermes, Zoroaster, and Moses transmit a common interior wisdom.",
        "cosmological": "The original cosmology before its dispersion into rival systems; the unified knowledge of the macrocosm-microcosm correspondence that Renaissance natural philosophy seeks to restore."
    },
    "mytho-alchemy": {
        "alchemical": "Peter Forshaw's term for Maier's distinctive method (Arcana Arcanissima, Atalanta Fugiens) of reading classical mythology as encoded chemical instruction—every god, hero, and monster a stage of the work.",
        "medical": "The diagnostic application of myth: reading the mythological grammar of the body's processes (Saturn's heaviness, Mars's heat, Mercury's volatility) as a language for naming and treating illness.",
        "spiritual": "The hermeneutic posture in which mythological narrative becomes the mirror of inner transformation; reading the labors and journeys of heroes as a script for the soul's work.",
        "cosmological": "The conviction that ancient myth and natural philosophy describe the same cosmos under different registers; the Renaissance practice of unifying poetic and scientific knowledge through allegorical reading."
    },
    "rosicrucian-brotherhood": {
        "alchemical": "The fraternity announced in the manifestos (1614–1616) and defended by Maier in Silentium post Clamores and Themis Aurea; the imagined community of adepts whose existence underwrites the alchemical-spiritual reform of the age.",
        "medical": "The brotherhood's promised programme of free healing for the poor: an explicitly iatrochemical mission tying medical practice to spiritual reformation in the Paracelsian lineage.",
        "spiritual": "The invisible college of the spiritually awakened, defined by interior commitment rather than visible membership; the prototype of the modern esoteric brotherhood as community of inner work.",
        "cosmological": "The eschatological community gathered for the imminent renewal of the world; the brotherhood understood within a cosmological narrative of decline, restoration, and the return of prisca sapientia."
    },
    "cantus-firmus": {
        "alchemical": "The 'fixed song' of the soprano voice in Maier's three-voice fugues: the unchanging melodic line representing the fixed principle (philosophical Sulphur or the King) around which the volatile voices weave.",
        "medical": "The body's steady underlying rhythm—pulse, breath, circadian cycle—on which fluctuating symptoms play; the diagnostic baseline against which deviation is measured.",
        "spiritual": "The unchanging contemplative ground beneath the fluctuations of psychic life; the still center whose constancy enables the seeker to register and integrate the soul's mobile voices.",
        "cosmological": "The fixed stars of the eighth sphere whose unchanging position anchors the whirling motions of the planets below; the celestial cantus firmus on which the cosmic polyphony sings."
    },
    "fugue": {
        "alchemical": "The contrapuntal form of Maier's fifty musical settings: three voices (Atalanta fleeing, Hippomenes pursuing, golden apple intervening) enact in sound the alchemical chase the emblems narrate visually.",
        "medical": "The Ficinian therapy of polyphonic music: the sustained imitative voices treat the listener's spirit by entraining its rhythms into healthful proportion across multiple registers simultaneously.",
        "spiritual": "The disciplined imitation of a single subject across difference; the pattern of contemplative practice in which the same insight returns transposed through varied life-circumstances until fully integrated.",
        "cosmological": "The three voices as Sun, Moon, and the rotating Earth between them; the cosmos as great fugue in which celestial motions follow imitative rules across distinct registers."
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CONCEPT TERMS (qualifying)
    # ═══════════════════════════════════════════════════════════════════════════
    "philosopher-s-stone": {
        "alchemical": "The Lapis Philosophorum: the perfected red powder or tincture capable of transmuting base metals into gold and serving as the universal medicine—the opus's ultimate product.",
        "medical": "The panacea or universal medicine that cures all diseases, restores youth, and grants extraordinary longevity—the supreme aim of iatrochemical practice.",
        "spiritual": "The fully realized self; the incorruptible inner gold achieved through the complete integration of all psychic opposites—the goal of the soul's Great Work.",
        "cosmological": "The quintessence crystallized: the fifth element that transcends and perfects the four mundane elements, embodying the perfection of cosmic order in material form."
    },
    "philosophical-egg": {
        "alchemical": "The sealed vessel (often egg-shaped) containing the prima materia, maintained at gentle heat to incubate the Stone—the alchemical equivalent of the womb or nest.",
        "medical": "The protected healing environment; the carefully controlled conditions of temperature, moisture, and rest that allow the body's natural restorative powers to operate.",
        "spiritual": "The enclosed space of contemplation and inner work; the hermetically sealed container of the psyche in which transformation gestates before hatching into new life.",
        "cosmological": "The cosmic egg of Orphic and Hermetic cosmogony: the primordial vessel from which the differentiated cosmos emerges, containing all potentialities in compressed form."
    },
    "solve-et-coagula": {
        "alchemical": "The fundamental axiom: dissolve the fixed and coagulate the volatile. All alchemical operations reduce to this rhythm of breaking down and reconstituting matter at a higher level.",
        "medical": "The therapeutic cycle of breaking down diseased structures and rebuilding healthy tissue; the alternation of catabolism and anabolism that sustains bodily renewal.",
        "spiritual": "The universal rhythm of spiritual growth: dismantling old beliefs and identities (solve) and crystallizing new understanding into lived wisdom (coagula).",
        "cosmological": "The cosmic pulse of creation: the eternal alternation between dissolution into chaos and reconstitution into order that drives the cyclical life of the universe."
    },
    "tria-prima": {
        "alchemical": "Paracelsus's three principles—Sulphur, Mercury, and Salt—replacing the Aristotelian four elements as the fundamental components of all matter and the basis of spagyric analysis.",
        "medical": "The three physiological principles: Sulphur as vital heat and combustibility, Mercury as fluidity and volatility, Salt as structure and solidity—the Paracelsian diagnostic triad.",
        "spiritual": "Spirit, soul, and body: the tripartite anthropology in which Mercury mediates between the fiery will (Sulphur) and the material vessel (Salt).",
        "cosmological": "The three cosmic principles reflecting the Trinity: the active formative fire (Sulphur), the receptive universal medium (Mercury), and the crystallized manifest world (Salt)."
    },
    "vas-hermeticum": {
        "alchemical": "The hermetically sealed vessel in which the entire opus takes place; it must be perfectly sealed so that no spirit escapes—Maier's glass house that must be well closed.",
        "medical": "The body itself as the vessel of healing: the patient's constitution that must be sealed against external corruption while internal transformative processes complete their work.",
        "spiritual": "The contemplative enclosure of the soul; the disciplined inner space of meditation and practice in which psychic transformation can proceed without dissipation.",
        "cosmological": "The cosmos itself as God's sealed vessel: the bounded universe within which all celestial and terrestrial processes unfold according to the divine plan."
    },
    "opus-magnum": {
        "alchemical": "The Great Work itself: the entire sequence of operations from prima materia to Philosopher's Stone, encompassing nigredo, albedo, citrinitas, and rubedo.",
        "medical": "The complete course of treatment from diagnosis through crisis to cure; the physician's magnum opus of restoring the patient from sickness to perfected health.",
        "spiritual": "The lifelong work of self-transformation; the soul's journey from unconscious chaos through successive purifications to the gold of realized wisdom.",
        "cosmological": "The divine creative act mirrored in human artifice; the alchemist's work as a microcosmic recapitulation of God's original creation of order from chaos."
    },
    "lapis": {
        "alchemical": "The Stone: shorthand for the Philosopher's Stone in its most general sense—the goal and product of the alchemical art, whether conceived as powder, tincture, or elixir.",
        "medical": "The perfected medicine in solid form; the Stone as universal remedy whose mere proximity or touch is sufficient to transmute disease into health.",
        "spiritual": "The cornerstone rejected by the builders; the despised and hidden treasure of self-knowledge that the world overlooks but the wise recognize as supremely precious.",
        "cosmological": "The cosmic keystone; the perfected microcosmic substance that, as the Turba states, gives access to all the secrets of macrocosm and microcosm."
    },
    "catena-aurea": {
        "alchemical": "The golden chain: the unbroken sequence of transmissions linking ancient sages to present practitioners, guaranteeing the authenticity of alchemical knowledge.",
        "medical": "The chain of medical authority from Hippocrates through Galen to Paracelsus; the lineage of healing wisdom transmitted from master to student across centuries.",
        "spiritual": "The unbroken chain of initiatic transmission; the living lineage connecting the seeker to the original source of esoteric knowledge through teacher-student succession.",
        "cosmological": "Homer's golden chain linking heaven to earth: the vertical axis of emanation by which divine influence descends through the planetary spheres to terrestrial matter."
    },
    "cauda-pavonis": {
        "alchemical": "The peacock's tail: the iridescent display of colors appearing in the vessel during the transitional phase between nigredo and albedo, signaling that the matter is alive and progressing.",
        "medical": "The crisis of fever showing many-colored symptoms—a sign that the body is actively fighting disease and that the humoral disturbance is moving toward resolution.",
        "spiritual": "The dazzling but transient visions and psychic phenomena that arise during spiritual transformation; beautiful but not yet the stable light of true illumination.",
        "cosmological": "The rainbow as bridge between heaven and earth; the spectrum of planetary colors reflected in the alchemical vessel, recapitulating the diversity of celestial influences."
    },
    "pelicanus": {
        "alchemical": "The pelican vessel: a circulatory flask in which distillate flows back onto the residue, named for the legendary bird that feeds its young with blood from its own breast.",
        "medical": "The self-sacrificing physician who gives of their own vitality to heal the patient; the therapeutic principle that cure requires the healer's personal expenditure of life-force.",
        "spiritual": "Christ-like self-sacrifice: the soul that nourishes its own transformation through willing suffering, feeding the nascent spiritual life with the blood of the old self.",
        "cosmological": "The Sun nourishing the planets with its own substance; the cosmic principle of self-giving that sustains all dependent beings through continuous emanation of vital light."
    },
    "sapientia": {
        "alchemical": "Wisdom as the true prerequisite of the art: without philosophical understanding of nature's principles, mere laboratory technique produces nothing—knowledge precedes operation.",
        "medical": "The physician's diagnostic wisdom; the capacity to read the body's signs correctly and prescribe the right remedy at the right time in the right measure.",
        "spiritual": "Divine Sophia: the feminine personification of wisdom who guides the seeker through the labyrinth of the Great Work and reveals the hidden meaning of nature's symbols.",
        "cosmological": "The ordering intelligence pervading the cosmos; the Logos or world-reason that structures the universe according to number, proportion, and harmony."
    },
    "alembic": {
        "alchemical": "The distillation apparatus proper: the head or capital fitted onto the cucurbit through which volatile vapors rise and condense into the receiving vessel—the instrument of separation par excellence.",
        "medical": "The Paracelsian still by which the spagyrist extracts pure tinctures from gross plant or mineral bodies; the iatrochemical workshop where crude matter becomes refined remedy.",
        "spiritual": "The contemplative discipline that distills essential meaning from the welter of experience; the inner alembic in which spiritual heat lifts pure understanding from the residue of attachment.",
        "cosmological": "The sky itself as cosmic still: solar heat raises terrestrial moisture, condenses it on the celestial vault, and returns it as purified rain—nature's universal alembic."
    },
    "athanor": {
        "alchemical": "The slow furnace whose constant, gentle heat incubates the sealed vessel through the long phases of the opus; its name (from Arabic al-tannūr) marks alchemy's debt to Islamic adepts.",
        "medical": "The body's innate heat (calor innatus) that drives digestion, generation, and the slow maturation of vital spirits; physiological warmth as the engine of cure.",
        "spiritual": "The sustained inner fire of devotion and discipline; the steady, unwavering attention that allows transformation to mature without being scorched by zeal or quenched by neglect.",
        "cosmological": "The Sun as cosmic athanor: the central hearth whose patient, perpetual fire warms the planetary spheres and sustains generation throughout the sublunary world."
    },
    "four-elements": {
        "alchemical": "Earth, water, air, and fire: the qualitative substrates whose proportions and transmutations underlie every alchemical operation, as Maier's emblems repeatedly stage their interplay.",
        "medical": "The Galenic basis of humoral physiology: blood (air), phlegm (water), yellow bile (fire), and black bile (earth)—health as their balanced commixture, disease as their disorder.",
        "spiritual": "The fourfold structure of the soul or psyche; the elemental temperaments through which spiritual aspiration must be tempered into a balanced and integrated character.",
        "cosmological": "The sublunary cosmos's material constituents arranged in concentric spheres beneath the heavens; the framework through which celestial influences act upon terrestrial bodies."
    },
    "mercury-sulphur-theory": {
        "alchemical": "The medieval Arabic-derived doctrine that all metals are composed of philosophical Mercury (volatile, feminine, lunar) and Sulphur (fixed, masculine, solar) in varying purity and proportion.",
        "medical": "The basis of iatrochemical pharmacology: medicines understood as rebalancing the patient's mercurial and sulphurous principles; the diagnostic frame Paracelsus extended into Tria Prima.",
        "spiritual": "The polarity of receptivity and active will within the soul; the inner marriage of feminine reflective intelligence and masculine generative power that the Work brings to perfection.",
        "cosmological": "The Sun and Moon as the celestial archetypes of Sulphur and Mercury; their conjunction governs generation throughout nature, mirrored in every metal's hidden parentage."
    },
    "garden-of-hesperides": {
        "alchemical": "The hidden orchard guarded by a dragon where the golden apples ripen: a topos for the secret laboratory and the Stone itself, ringed by the protective serpent of mercurial matter.",
        "medical": "The locus of restored health and longevity; the legendary garden whose fruit confers the vitality the iatrochemist seeks to bottle in the universal medicine.",
        "spiritual": "The paradisal interior of the awakened soul; the inner garden whose fruits—wisdom, virtue, integration—ripen only when the dragon of unconscious resistance has been overcome.",
        "cosmological": "The far western edge of the world where the sun sets into the ocean of unmanifest potentiality; the threshold between manifest cosmos and the hidden source from which it issues."
    },
    "golden-apple": {
        "alchemical": "The fruit of Hesperides that Hippomenes drops to slow Atalanta: cipher of the perfected gold or Stone whose apparition arrests the volatile flight of mercurial matter.",
        "medical": "The aurum potabile in fruit form; the perfected medicinal essence whose ingestion restores incorruptible health, figured as the food of the gods in classical legend.",
        "spiritual": "The lure that draws the soul out of unconscious flight into conscious encounter; the precious insight whose appearance, though fleeting, redirects the seeker toward the goal.",
        "cosmological": "The solar fruit ripened by celestial fire at the world's western boundary; the round perfection in which the heavens condense their virtue into edible, bounded form."
    },
    "golden-fleece": {
        "alchemical": "The prize won by Jason from the dragon-guarded grove of Colchis: Maier and his predecessors read it as cipher for the Philosopher's Stone, with the Argonauts' voyage as the opus.",
        "medical": "The supreme medicament whose acquisition demands a heroic regimen; the panacea hidden behind the dragon of disease, recoverable only by sustained therapeutic discipline.",
        "spiritual": "The radiant authentic self recovered after the soul's perilous voyage through unfamiliar waters; the integrated personality won from the unconscious by trial and patient cunning.",
        "cosmological": "The solar ram itself, fixed in the zodiac as Aries: the celestial fleece whose recovery marks the spring equinox, the cosmos's annual rebirth from the dragon of winter darkness."
    },
    "eucharist-alchemical": {
        "alchemical": "The sacramental analogy adepts drew between the consecrated species and the Stone: both are humble matter into which a higher principle has been substantially infused without altering the appearance.",
        "medical": "The supreme medicine of the soul reread as physical panacea: just as the host nourishes the spiritual body, the alchemical Eucharist nourishes the bodily life with its own concentrated virtue.",
        "spiritual": "The interiorized sacrament: communion as the daily recapitulation of conjunctio—the union of human and divine substance that the alchemical work models in matter.",
        "cosmological": "The cosmos as universal Eucharist: the doctrine that all matter participates in divine substance through the descent of celestial influence, making every transformation a sacred ingestion."
    },
    "musica-speculativa": {
        "alchemical": "Speculative music: the Pythagorean–Boethian science of harmonic ratio that grounds Maier's fifty fugues in the same proportional theory that orders matter in the alchemical vessel.",
        "medical": "Music as therapy in the Ficinian tradition: the audible proportions that retune the listener's spirit and restore humoral balance through resonance with celestial harmony.",
        "spiritual": "The contemplative ascent through harmonic ratio toward the divine ground; music heard not as pleasant sound but as the audible trace of cosmic order, training the soul in proportion.",
        "cosmological": "The Boethian music of the spheres: the planetary motions understood as inaudible harmony, of which earthly music (musica instrumentalis) and human harmony (musica humana) are reflections."
    },
    "quadrivium": {
        "alchemical": "The fourfold mathematical curriculum (arithmetic, geometry, music, astronomy) that grounds alchemical proportion: weights, vessel geometry, fugal ratios, and timing of operations all draw on it.",
        "medical": "The numerical bases of regimen: dosage proportion, geometric models of the body, musical pulse-theory, and astrological timing of treatments—medieval medicine was explicitly quadrivial.",
        "spiritual": "The disciplined ascent of the mind through the four mathematical sciences toward contemplation of pure intelligible form; the medieval pedagogical path from sensible to spiritual.",
        "cosmological": "The architecture of the cosmos read as number: the four sciences disclose successively the unities, magnitudes, harmonies, and motions through which God ordered creation."
    },
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    updated = 0
    skipped = 0
    missing = 0

    for slug, registers in REGISTERS.items():
        json_str = json.dumps(registers, ensure_ascii=False)
        result = conn.execute(
            "UPDATE dictionary_terms SET registers = ? WHERE slug = ?",
            (json_str, slug)
        )
        if result.rowcount > 0:
            updated += 1
        else:
            print(f"  WARNING: slug '{slug}' not found in dictionary_terms")
            missing += 1

    # Report what was skipped
    cursor = conn.execute(
        "SELECT slug, category FROM dictionary_terms WHERE registers IS NULL ORDER BY category, slug"
    )
    null_rows = cursor.fetchall()
    for slug, cat in null_rows:
        skipped += 1

    conn.commit()
    conn.close()

    print(f"\nRegisters populated: {updated}")
    print(f"Slugs not found:    {missing}")
    print(f"Terms left NULL:    {skipped}")
    if null_rows:
        print("\nTerms without registers (by design or omission):")
        for slug, cat in null_rows:
            print(f"  [{cat}] {slug}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
