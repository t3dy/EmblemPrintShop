# Emblem Knight — and the Alchemical Dragon

A *Dragon Warrior*–style RPG **and roguelike** whose entire art set is built from
the Emblem Print Shop's extracted alchemical engravings, themed on Michael Maier's
*Atalanta Fugiens* (1617). An isometric, NES/SNES-era overworld hub; a first-person,
command-menu battle screen where every monster is a woodcut creature from a real
emblem plate; and a procedurally-generated, fog-of-war **descent through the four
stages of the Great Work** with permadeath.

> Choose your vessel — Knight, Alchemist, Atalanta, or Hippomenes — in the world
> above. Meet the King, then descend the eastern stair into the Opus: twelve
> procedurally-built floors that pass through **Nigredo → Albedo → Citrinitas →
> Rubedo**, each announced with a genuine Maier motto, until the **Alchemical
> Dragon** is slain and the Philosopher's Stone is won. Die and the save is gone.

### The Atalanta Fugiens framing

The story is grounded in the project's own alchemy databases (`C:\Dev\Claudiens`,
`C:\Dev\ALCHEMYTIMELINEMAP`, `C:\Dev\TheosophicalAlchemyDB`):

- The **four colour stages** of the *magnum opus* structure the descent, each with
  a real motto, e.g. Albedo's *"Go to the woman who washes the sheets, and do as
  she does"* (Emblem III) and Rubedo's *"Make a circle of man and woman… and thou
  shalt have the Stone"* (Emblem XXI).
- **Atalanta** = the volatile/Mercury (the fleeing principle), **Hippomenes** =
  the fixed/Sulphur (the pursuer), and the **three golden apples** are her trick —
  in-game the *Golden Apple* item lets you flee any battle, even the boss.
- The goal is the **Lapis / Philosopher's Stone**; *festina lente* ("make haste
  slowly") is the recurring watchword.

## Run it

A static server is registered in `.claude/launch.json` as **emblem-knight**
(serves this `game/` folder on port 7431):

```
python -m http.server 7431 --directory game
# then open http://localhost:7431/
```

ES modules require http(s) — opening `index.html` from `file://` will not load.

## Controls

| Action               | Keys                          |
|----------------------|-------------------------------|
| Move (overworld)     | Arrow keys / WASD (held)      |
| Move (dungeon, turn) | Arrow keys / WASD (per press) |
| Choose character     | ← → then Z                    |
| Confirm / talk       | Z / Space / Enter             |
| Cancel / save / back | X / Esc / Backspace           |
| Music on/off         | M                             |
| (Touch)              | On-screen D-pad + A/B buttons |

Movement is screen-aligned: ▲ walks "up" the isometric grid, etc. The overworld
moves smoothly; the dungeon is **turn-based** (one tile per press; enemies act
after you do).

## The game loop

```
TITLE ─New Quest─▶ CHOOSE VESSEL ─▶ OVERWORLD(hub) ─enter eastern stair─▶ THE OPUS
  ▲                                   │   │   │                              │
  │                                 castle town wilds              floors 1→12 descend
  │                                 quest heal  battle      Nigredo▸Albedo▸Citrinitas▸Rubedo
  │                                                                          │
GAME OVER ◀──hero HP 0 (permadeath, save wiped)──────────── Dragon slain ─▶ VICTORY (the Stone)
```

- **Character select** (`_renderCharSelect` in `js/main.js`): pick one of four
  emblem-drawn vessels; each re-skins the hero and tweaks stats / kit / a passive.
- **Overworld** (`js/world.js`): isometric diamond-tile renderer (64×32 tiles), the
  safe hub — Sun-Castle (quest + Golden Apples), Town (free rest), wild encounters,
  and the eastern stair into the Opus.
- **The Opus** (`js/dungeon.js`): procedurally-generated floors (rooms + corridors),
  isometric walls, **fog of war**, turn-based movement, enemies that wander and
  chase (contact → battle), floor loot, stairs down. Floor depth → colour-stage
  theming (palette + monster pool + enemy stat-scaling) + a real Maier motto. The
  Dragon waits on floor 12; beating it wins the Stone. **Permadeath**: a battle
  lost anywhere wipes the save; the title tracks your deepest descent.
- **Quests** (`QUESTS` in `js/data.js`): the **King (Sol)** and **Queen (Luna)**
  set *charges* — random "calls to action," each quoting a genuine *Atalanta
  Fugiens* motto plus a recited **emblem-poem couplet**. They appear two ways:
  - In the **overworld court**: the King at his castle, the **Queen at her bower**
    (the `Q` tile beside the castle) — visit before a run to stock charges.
  - In the **Opus**: a King or Queen may hold court on a random floor (~55%).

  Charges set an objective (slay N of a creature, gather relics/gold, descend N
  floors, reach a stage) and pay out gold / items / EXP / +max HP. Active charges
  show in the dungeon HUD; the givers are the `q_king` / `q_queen` emblem figures.
  Sol's charges lean martial (fire, slaying, descent, the Stone); Luna's lean lunar
  (washing, gathering, the woman, flight).
- **The Great Work questline** (`OPUS_LINE`): a 4-step chain the royals offer **in
  order**, one per colour stage — *Nigredo* (slay the blackness) → *Albedo* (wash
  the matter) → *Citrinitas* (raise the Lion) → *Rubedo* (reach the red and face
  the Dragon). Each step quotes its emblem; finishing the chain bestows **the
  Crown** (+5 atk, +4 def) and points you at the Dragon. Tracked via `hero.opusStep`.
- **Battle** (`js/battle.js`): turn-based FIGHT / SPELL / ITEM / RUN. Damage =
  `max(1, atk − def/2) × rand(0.8–1.2)` with 7% crits. Enemies may breathe fire.
  Win → EXP + gold + automatic level-ups (HP/MP/atk/def grow, spells learned).
- **Persistence**: hero state saved to `localStorage` after battles, town rests,
  and on the cancel/save key. The title shows **Continue** when a save exists.
- **Audio**: procedural WebAudio blips (no sound files) for hits, magic, heals,
  encounters, level-ups, victory and defeat.
- **Music** (`js/music.js`): procedural "fugues" in the spirit of *Atalanta
  Fugiens*. Maier gave every emblem a **three-voice canon** — a fixed cantus
  firmus ("the golden apple") and two voices in chase, *Atalanta* (the fleeing
  fuga) and *Hippomenes* (the *comes*, entering a beat later in imitation). Each
  theme reproduces that form (lead + octave-delayed comes + slow cantus firmus),
  synthesised live — no audio files. Themes are grouped into per-area playlists and
  **cycle** every couple of loops: a court hymn on the title, three pastoral airs
  in the overworld, a distinct mood for each colour stage of the Opus (dark/low
  Nigredo, bright Albedo, golden Citrinitas, driving Rubedo), battle themes, and
  victory/defeat stingers. **M** toggles music. (The actual Maier scores aren't in
  the repo — only a recordings bibliography in `Claudiens/AFMUSIC.txt` — so these
  are original modal canons built on his three-voice *form*, not transcriptions.)

## Characters (choose your vessel)

Defined in `CLASSES` (`js/data.js`); each is a real human figure from the emblems.

| Class       | Sprite (source)                    | Playstyle / passive                              |
|-------------|------------------------------------|--------------------------------------------------|
| Knight      | `hero` (Stolcius 13)               | Balanced; *Stout* +10% max HP                     |
| Alchemist   | `c_alchemist` (Atalanta Emblem XXI)| Frail caster; starts with Heal+Blaze, +MP/level  |
| Atalanta    | `c_atalanta` (Stolcius 2)          | Volatile; **always** flees, extra Golden Apples  |
| Hippomenes  | `c_hippomenes` (Splendor Solis)    | Aggressive; *Pursuer* +15% attack damage         |

## The descent — stages of the Great Work

`STAGES` (`js/data.js`) maps floor depth to the four colour stages; each sets the
palette, the enemy pool, and a genuine *Atalanta Fugiens* motto shown on entry.

| Floors | Stage      | Motto (Maier)                                              |
|--------|------------|-----------------------------------------------------------|
| 1–3    | Nigredo    | "Putrefaction is the beginning of generation."            |
| 4–6    | Albedo     | "Go to the woman who washes the sheets, and do as she does." |
| 7–9    | Citrinitas | "Nature teaches Nature; Nature conquers Nature."          |
| 10–12  | Rubedo     | "Make a circle of man and woman… and thou shalt have the Stone." |

Floor 12 (Rubedo) holds the **Dragon**; defeat it to achieve the **Lapis**.

### Items

`herb` (heal), `potion`/Aqua Vitae (MP), `elixir`/Red Elixir (full restore),
**`apple`/Golden Apple** (flee any battle, even bosses — Atalanta's trick), plus
floor-only finds: gold piles and *Philosophic Salt* (+4 max HP).

## Landmarks & progression

| Tile           | Sprite                    | Effect                                       |
|----------------|---------------------------|----------------------------------------------|
| Castle         | `s_castle`                | King gives the quest + 30 gold (first visit) |
| Town           | `s_town`                  | Full HP/MP rest                              |
| Dungeon        | `s_door`                  | Entrance to the Opus (the roguelike descent) |
| Forest / Woods | `t_forest` / `t_forest2`  | Tier-2 encounters (bears, stags, boars…)     |
| Cliff          | `t_cliff`                 | Tier-2 encounters (harpies, stags)           |
| Badlands       | —  (reddish ground)       | Tier-3 encounters (lions, wyrms, ouroboros)  |
| Cave           | `t_cave`                  | Tier-3 encounters; gateway terrain to dungeon|
| Mountain/Peaks | `t_mountain`/`t_mountain2`| Impassable                                   |
| Water          | —                         | Impassable                                   |

The continent runs west→east in difficulty: home **Sun-Castle** and gentle grass
in the west, **Town** (free rest) in the centre, then the eastern **badlands**,
caves and cliffs — tier-3 country — funnelling to the **Dungeon** in the far east.

Encounter pools by region live in `js/data.js` (`REGION_POOLS`). The monster
roster, stats, spells, items and the level curve are all data-driven there.

## Assets — from emblem to sprite

35 curated extractions become game sprites via `tools/build_assets.py`:

1. optional manual crop — many creatures live *inside* a full plate, so dragons
   are cut straight from the Atalanta Fugiens engravings (emblem-25 coiled dragon,
   emblem-14 ouroboros, emblem-50 coiling wyrm; the boar from emblem-41),
2. paper/background removal (bright engraving paper → transparent),
3. alpha-bbox crop + resize (nearest/Lanczos) for an NES-ish read,
4. light 4-bit posterize.

Output goes to `assets/sprites/*.png` plus `assets/manifest.json` (consumed at
runtime by `js/assets.js`). To re-curate or swap art, edit the `MANIFEST` list in
`tools/build_assets.py` and re-run it.

> Note on labels: GroundingDINO's extraction vocabulary had no "lion", so lions
> are filed under `dog`/`bear` in the catalog (e.g. the in-game Lion and Winged
> Lion are both `dog`-tagged Stolcius plates). Dragons are mostly only findable by
> hand-cropping the source plates — the `dragon`-tagged catalog records are largely
> mislabelled full pages.

### The 35 sprites

| Role        | Sprite(s)                                   | Source corpus                |
|-------------|---------------------------------------------|------------------------------|
| Player classes | `hero`, `c_alchemist`, `c_atalanta`, `c_hippomenes` | Stolcius, Atalanta XXI, Splendor Solis |
| NPCs        | `king`, `sage`, `villager`                   | Stolcius                     |
| Quest givers| `q_king` (Sol), `q_queen` (Luna)             | Stolcius plates 33 & 44      |
| Dragons     | `m_dragon` (boss), `m_ouroboros`, `m_wyrm`, `m_serpent` | Atalanta Fugiens 25/14/50, Stolcius |
| Beasts      | `m_lion`, `m_wlion`, `m_bear`, `m_wolf`, `m_boar`, `m_stag`, `m_salamander`, `m_harpy`, `m_swan`, `m_toad` | Stolcius, Atalanta, Splendor Solis, McLean |
| Structures  | `s_castle`, `s_tower`, `s_town`, `s_gate`, `s_door` | Stolcius, Cramer, Atalanta, McLean |
| Terrain     | `t_forest`, `t_forest2`, `t_mountain`, `t_mountain2`, `t_cave`, `t_cliff` | Stolcius, Atalanta, McLean, Maier Arcana |
| Decor       | `d_sun` (title Sol)                          | Atalanta Fugiens emblem-45   |

## File map

```
game/
  index.html            shell + canvas + touch controls
  css/style.css
  js/
    main.js             state machine, input, loop, save, permadeath, char-select, audio
    data.js             map, monsters, CLASSES, STAGES, regions, spells, items, level curve
    world.js            isometric overworld (hub)
    dungeon.js          procedural roguelike descent (the Opus): gen, fog-of-war, turns
    battle.js           Dragon-Warrior battle (depth-scaled enemies)
    ui.js               windows, parchment cards, menus, typewriter message box
    assets.js           manifest + image loader
  tools/build_assets.py asset pipeline (emblem extractions → sprites)
  assets/
    manifest.json
    sprites/*.png
  _curation/            contact sheets + verification frames (build artifacts)
```

## Prototype scope / next steps

Playable end-to-end: title → explore → fight → level → boss → victory/defeat.
Natural extensions: directional hero sprites, a shop economy with the gold,
inn cost, more map regions, status effects, a small story beyond the single quest,
and battle sprite-entry animations.
