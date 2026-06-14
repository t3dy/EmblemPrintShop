# Animal Recognition System

A diagnostic method for identifying *what kind of animal* an extracted cutout
actually depicts — **by looking at the image**, not by trusting the detector's
label.

## Why this exists

The extraction pipeline uses GroundingDINO to *find* objects (bounding boxes)
and to *name* them. The boxes are usually good; the **names are not**. Observed
failure modes on the `animals` category:

- **Garbled compound labels** — the detector emits several candidate terms
  concatenated: `"wolf lambtoise frog"`, `"dog wolf lamb frog fox"`,
  `"eagle peacock butterfly"`.
- **Wrong species** — a hare labelled `wolf`; a lion labelled `horse` or `dog`;
  a coiled serpent labelled `lamb frog`.
- **Category errors** — a winged human (angel) and a flaming heart both filed
  under `animals`.
- **Dirty crops** — the mask sometimes grabs a second subject (e.g. a lion crop
  that also contains the spearman behind it).

So a label of `peacock` on a record means *the detector guessed peacock* — it is
**not** evidence the image shows a peacock. Re-identification must start from the
pixels.

## The controlled vocabulary

Identifications map onto the 24 animal motifs in [`data/motifs.json`](../data/motifs.json):

`dragon · lion · serpent · bird · phoenix · pelican · raven · dove · peacock ·
swan · horse · dog · wolf · deer · ox · lamb · fish · tortoise · crab · bee ·
butterfly · fox · hare · bear`

Plus four escape hatches for when a crop is not a clean single animal:

- `not_an_animal` — the crop is a human figure, object, plant, architecture, or
  decoration that the detector miscategorised.
- `unknown_creature` — clearly an animal/beast but not in the vocabulary, or too
  fantastical/ambiguous to pin down (record the closest description).
- `multiple` — the crop contains more than one distinct subject (flag for
  re-segmentation; still record the dominant one).
- `unidentifiable` — too cropped, degraded, or abstract to call.

## The diagnostic key — read features in this order

Don't pattern-match a whole silhouette to a remembered label. Read the
**discriminating features** one at a time. Early-modern intaglio/woodcut style
(heavy hatching, paper tone, stylised anatomy) means surface texture is
unreliable; rely on **structure** (limbs, wings, tail, head furniture).

### 1. Count the body plan first

- **Wings present?** → go to §2 (birds / winged things).
- **Legless, long sinuous body?** → `serpent` (one body) — but check for a
  shell (→ `tortoise`) or fins (→ `fish`).
- **Four legs?** → §3 (quadrupeds).
- **Many legs / pincers / segmented?** → `crab` (pincers, carapace) or `bee` /
  `butterfly` (six legs + wings, insect body).
- **Two legs + reptilian/serpentine + wings?** → `dragon`.

### 2. Winged things

- **Feathered wings + a human head/torso** → this is an **angel or genius, not a
  bird** → `not_an_animal`. (Common false positive — winged humans abound in
  alchemical plates.)
- **Spread fan-shaped tail with eye-spots (ocelli)** → `peacock`.
- **Bird rising from / standing in flames** → `phoenix`.
- **Solid-black bird, corvid beak** → `raven`. **Small white bird, often with
  olive branch / in pairs** → `dove`. **Long curved neck, waterbird** → `swan`.
  **Pouched bill, often piercing its own breast** → `pelican`.
- **Membranous (bat-like) wings, scaly body** → `dragon`, not bird.
- **Patterned symmetrical insect wings** → `butterfly`; **striped fuzzy body
  near hive/flowers** → `bee`.
- Otherwise a generic large bird → `bird`.

### 3. Four-legged animals — use head furniture and proportions

- **Branching antlers** → `deer` (stag); a slender hooved animal without antlers
  may still be `deer` (hind) — check muzzle and tail.
- **Horns**: short curved horns + heavy body → `ox`; small woolly recumbent
  animal → `lamb`.
- **Mane + heavy paws + tufted tail** → `lion`. (A lion's mane is the single most
  reliable cue; don't be misled by a rider on its back.)
- **Long ears + leaping/crouched + short tail** → `hare` (the classic
  long-eared leaper — *not* a wolf).
- **Canine build**: lean, long-legged, often collared → `dog`; heavy fur, open
  snarling jaws, wild → `wolf`; slim, pointed muzzle, bushy tail → `fox`.
- **Equine**: long muzzle, hooves, flowing mane/tail, often rearing → `horse`.
- **Massive, shaggy, small round ears, plantigrade** → `bear`.

### 4. Sanity checks before committing

- **Is it actually an animal at all?** Vessels, suns/stars with faces, hearts,
  trees, fountains, and human figures are routinely miscategorised. If the
  dominant subject is not a creature → `not_an_animal`.
- **One subject or several?** If two distinct creatures (or a creature + a
  person) share the crop → `multiple`, and name the dominant one.
- **Confidence**: `high` when ≥2 discriminating features agree; `medium` when one
  cue carries it; `low` when guessing from silhouette alone.

## How the system is applied

The script [`scripts/reidentify_objects.py`](../scripts/reidentify_objects.py)
operationalises this key: it sends each cropped cutout image to a Claude vision
model (`claude-opus-4-8`) with this rubric and the controlled vocabulary, and
records a structured verdict (label, category, confidence, the distinguishing
features that drove the call, and a multi-subject flag) back into each emblem's
`summary.json` — **preserving the original detector label** for audit. See that
script's header for usage.
