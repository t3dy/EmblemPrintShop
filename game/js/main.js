// main.js — entry point, state machine, input, game loop, persistence, audio.
import { Assets } from './assets.js';
import { World, tileType } from './world.js';
import { Battle } from './battle.js';
import { Dungeon } from './dungeon.js';
import { Music } from './music.js';
import { newHero, CLASSES, STAGES, stageForFloor, FINAL_FLOOR, QUESTS, OPUS_LINE, questsByGiver, ITEMS, MONSTERS, recomputeStats } from './data.js';
import { MessageBox, window9, parchmentCard, text, menu, COLORS } from './ui.js';

const QUEST_BY_ID = Object.fromEntries(QUESTS.map(q => [q.id, q]));

const SAVE_KEY = 'emblem_knight_save_v1';
const SCORE_KEY = 'emblem_knight_score_v1';

class Game {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.W = canvas.width; this.H = canvas.height;
    this.state = 'title';        // title|charselect|overworld|dungeon|battle|dialog|gameover|victory
    this.msg = new MessageBox();
    this.hero = null;
    this.world = null;
    this.dungeon = null;
    this.battle = null;
    this._dungeonEnemy = null;   // enemy ref when a battle was started from the dungeon
    this.titleSel = 0;
    this.classSel = 0;
    this.titleT = 0;
    this.deathDepth = 0;
    this.questOffer = null;      // { who, quest } when a King/Queen is consulted
    this.returnState = 'dungeon';
    this.input = { up: false, down: false, left: false, right: false };
    this.afterDialog = null;
    this.audio = makeAudio();
    this.music = new Music(() => this.audio.ctx());
    this._bindKeys();
  }

  // map current state -> music area key
  _musicArea() {
    switch (this.state) {
      case 'title': case 'charselect': return 'title';
      case 'gameover': return 'gameover';
      case 'victory': return 'victory';
      case 'battle': return 'battle';
      case 'dungeon': return this.dungeon ? this.dungeon.stage.key : 'nigredo';
      case 'quest':
        return this.returnState === 'overworld' ? 'overworld'
             : (this.dungeon ? this.dungeon.stage.key : 'overworld');
      default: return 'overworld';   // overworld, dialog
    }
  }

  // ---- persistence ----
  save() {
    if (!this.hero) return;
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(this.hero)); } catch (e) {}
  }
  hasSave() { try { return !!localStorage.getItem(SAVE_KEY); } catch (e) { return false; } }
  load() {
    try { return JSON.parse(localStorage.getItem(SAVE_KEY)); } catch (e) { return null; }
  }
  wipeSave() { try { localStorage.removeItem(SAVE_KEY); } catch (e) {} }
  bestDepth() { try { return parseInt(localStorage.getItem(SCORE_KEY) || '0', 10) || 0; } catch (e) { return 0; } }
  recordDepth(d) { try { if (d > this.bestDepth()) localStorage.setItem(SCORE_KEY, String(d)); } catch (e) {} }

  sfx(name) { this.audio.play(name); }

  // ---- flow ----
  goCharSelect() { this.classSel = 0; this.state = 'charselect'; this.audio.unlock(); }

  newGame(classId) {
    this.hero = newHero(classId);
    this.world = new World(this);
    this.state = 'overworld';
    this.msg.queue = []; this.msg.done = true;
    this.audio.unlock();
    this.msg.push('Above lies the world of Atalanta; below, the Opus awaits. Seek the King, then descend the eastern stair.');
  }
  continueGame() {
    const s = this.load();
    if (!s) { this.goCharSelect(); return; }
    this.hero = s;
    if (this.hero.depth == null) { this.hero.depth = 0; this.hero.maxDepth = 0; }
    this.world = new World(this);
    this.state = 'overworld';
    this.audio.unlock();
  }

  // ---- the Opus (roguelike descent) ----
  startDungeon(depth, stageChanged = true) {
    this.hero.depth = depth;
    if (depth > (this.hero.maxDepth || 0)) this.hero.maxDepth = depth;
    this.dungeon = new Dungeon(this, depth);
    this.state = 'dungeon';
    this.msg.queue = []; this.msg.done = true;
    const st = stageForFloor(depth);
    if (stageChanged) this.msg.push(`${st.name} — ${st.sub}.`, st.motto);
    else this.msg.push(`Floor ${depth}.`);
    if (depth === FINAL_FLOOR) this.msg.push('At the foot of the Work, the Dragon stirs...');
    this.questProgress('reach', { depth });
    this.save();
  }
  descend() {
    const prev = stageForFloor(this.hero.depth);
    const next = this.hero.depth + 1;
    const changed = stageForFloor(next).key !== prev.key;
    this.startDungeon(next, changed);
  }

  startBattle(monsterId) {                 // overworld wild encounter
    this._dungeonEnemy = null;
    this.battle = new Battle(this, monsterId);
    this.state = 'battle';
    this.audio.play('encounter');
  }
  startDungeonBattle(monsterId, enemyRef, scale) {
    this._dungeonEnemy = enemyRef;
    this.battle = new Battle(this, monsterId, scale);
    this.state = 'battle';
    this.audio.play('encounter');
  }
  endBattle(result) {
    const fromDungeon = !!this._dungeonEnemy;
    const enemy = this._dungeonEnemy;
    const slainId = this.battle ? this.battle.mon.id : null;
    this.battle = null; this._dungeonEnemy = null;

    if (result === 'lose') { this._die(); return; }

    if (fromDungeon) {
      if (result === 'win') {
        if (enemy.boss) { this._win(); return; }
        this.dungeon.removeEnemy(enemy);
        this.questProgress('slay', { monId: slainId });
      }
      // win or flee -> back to the dungeon floor
      this.state = 'dungeon';
      this.save();
      return;
    }
    // overworld encounter
    if (result === 'win') this.questProgress('slay', { monId: slainId });
    if (this.hero.flags.dragonSlain) { this._win(); return; }
    this.state = 'overworld';
    this.save();
  }

  // ---- quests (random calls-to-action from King/Queen) ----
  offerQuest(who) {
    this.returnState = (this.state === 'overworld' || this.state === 'dialog') ? 'overworld' : 'dungeon';
    const held = new Set((this.hero.quests || []).map(q => q.id));
    // priority: offer the next step of the Great Work (either royal may give it)
    const nextOpus = OPUS_LINE[this.hero.opusStep || 0];
    let quest = null;
    if (nextOpus && !held.has(nextOpus.id) && (this.hero.opusStep < OPUS_LINE.length) &&
        (Math.random() < 0.6 || this.returnState === 'overworld')) {
      quest = nextOpus;
    } else {
      const done = new Set(this.hero._questsSeen || []);
      let pool = questsByGiver(who).filter(q => !held.has(q.id) && !done.has(q.id));
      if (pool.length === 0) pool = questsByGiver(who).filter(q => !held.has(q.id));
      if (pool.length) quest = pool[Math.floor(Math.random() * pool.length)];
      else if (nextOpus && !held.has(nextOpus.id)) quest = nextOpus;   // fall back to the Work
    }
    if (!quest) { this.msg.push(`${who === 'king' ? 'The King' : 'The Queen'} has no charge for thee now.`); this.state = this.returnState; return; }
    this.questOffer = { who, quest };
    this.state = 'quest';
    this.audio.play('magic');
  }
  acceptQuest() {
    const q = this.questOffer.quest;
    if (!this.hero.quests) this.hero.quests = [];
    this.hero.quests.push({ id: q.id, count: 0, baseGold: this.hero.gold, acceptDepth: this.hero.depth || 0 });
    (this.hero._questsSeen = this.hero._questsSeen || []).push(q.id);
    this.questOffer = null;
    this.state = this.returnState;
    this.msg.push(`Charge taken: “${q.title}.”`);
    this.save();
  }
  declineQuest() { this.questOffer = null; this.state = this.returnState; }

  questProgress(event, payload = {}) {
    const h = this.hero;
    if (!h.quests || !h.quests.length) return;
    for (const active of [...h.quests]) {
      const def = QUEST_BY_ID[active.id]; if (!def) continue;
      const o = def.objective;
      let done = false;
      if (event === 'slay' && (o.kind === 'slay' || o.kind === 'slayType')) {
        const hit = o.kind === 'slay' || payload.monId === o.monId || payload.monId === o.alt;
        if (hit) { active.count++; if (active.count >= o.target) done = true; }
      } else if (event === 'collect' && o.kind === 'collect') {
        active.count++; if (active.count >= o.target) done = true;
      } else if (event === 'reach' && o.kind === 'reach') {
        if (o.stage) { if (stageForFloor(payload.depth).key === o.stage) done = true; }
        else if (o.deeper) { if (payload.depth - active.acceptDepth >= o.deeper) done = true; }
      } else if (event === 'gold' && o.kind === 'gold') {
        if (h.gold - active.baseGold >= o.target) done = true;
      }
      if (done) this._completeQuest(active, def);
    }
  }

  _completeQuest(active, def) {
    const h = this.hero;
    h.quests = h.quests.filter(a => a !== active);
    h.questsDone = (h.questsDone || 0) + 1;
    const r = def.reward, gains = [];
    if (r.gold) { h.gold += r.gold; gains.push(`${r.gold} gold`); }
    if (r.xp) { h.xp += r.xp; gains.push(`${r.xp} EXP`); }
    if (r.maxhp) { h.maxHp += r.maxhp; h.hp += r.maxhp; gains.push(`+${r.maxhp} max HP`); }
    if (r.item) { const [k, n] = r.item; h.items[k] = (h.items[k] || 0) + n; gains.push(`${n}× ${ITEMS[k].name}`); }
    if (r.boon === 'crowned' && !h.flags.crowned) {
      h.flags.crowned = true; h.atk += 5; h.def += 4; gains.push('the Crown (+5 atk, +4 def)');
    }
    this.audio.play('level');
    this.msg.push(`Charge fulfilled — “${def.title}”!`, `Reward: ${gains.join(', ')}.`);
    // advance the Great Work
    if (def.line === 'opus') {
      h.opusStep = Math.max(h.opusStep || 0, def.step);
      if (def.step >= OPUS_LINE.length) this.msg.push('The Great Work is all but accomplished — descend, and face the Dragon!');
      else this.msg.push('The Great Work advances. Seek the next royal charge.');
    }
    this.save();
  }

  _die() {
    this.deathDepth = this.hero.depth || 0;
    this.recordDepth(this.deathDepth);
    this.wipeSave();                        // permadeath
    this.state = 'gameover';
  }
  _win() {
    this.hero.flags.dragonSlain = true;
    this.recordDepth(this.hero.depth || FINAL_FLOOR);
    this.wipeSave();                        // a finished run is spent
    this.state = 'victory';
  }

  // landmark events
  dialog(lines, after = null) {
    this.afterDialog = after;
    this.state = 'dialog';
    this.msg.push(...lines);
    this.msg.onEmpty = () => {
      this.state = 'overworld';
      const f = this.afterDialog; this.afterDialog = null;
      if (f) f();
    };
  }
  enterCastle() {
    if (!this.hero.flags.metKing) {
      this.hero.flags.metKing = true;
      this.dialog([
        'KING: Adept, the Work descends through four stages — Nigredo, Albedo, Citrinitas, Rubedo.',
        'KING: At the foot of the Opus coils the Alchemical Dragon. Slay it to win the Stone.',
        'KING: Take these Golden Apples — cast one down to flee any foe, as Atalanta did.',
        'KING: Return to my throne, or my Queen at her bower, for charges of the Work.',
        'Received 30 gold and 2 Golden Apples.'
      ], () => { this.hero.gold += 30; this.hero.items.apple = (this.hero.items.apple || 0) + 2; this.save(); });
    } else {
      this.offerQuest('king');     // the King sets a charge from his throne
    }
  }
  enterQueenCourt() {
    if (!this.hero.flags.metQueen) {
      this.hero.flags.metQueen = true;
      this.dialog([
        'QUEEN: I am Luna, sister and bride to the Sun. The volatile is mine to rule.',
        'QUEEN: Come to my bower for charges of the whitening and the gathering.'
      ], () => this.save());
    } else {
      this.offerQuest('queen');    // the Queen sets a charge from her bower
    }
  }
  enterTown() {
    const cost = 0;
    this.dialog([
      'INNKEEPER: Rest here, weary one. Thy wounds are mended.',
      'HP and MP fully restored.'
    ], () => { this.hero.hp = this.hero.maxHp; this.hero.mp = this.hero.maxMp; this.sfx('heal'); this.save(); });
  }
  enterDungeon() {
    if (this.hero.flags.dragonSlain) {
      this.dialog(['The Opus is complete. The Stone is yours.']);
      return;
    }
    this.dialog(
      ['You descend into the prima materia. Festina lente — make haste slowly.'],
      () => this.startDungeon(1)
    );
  }

  // ---- input ----
  _bindKeys() {
    const down = (e) => {
      const k = e.key;
      if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(k)) e.preventDefault();
      this._key(k, true);
    };
    const up = (e) => this._key(e.key, false);
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    // on-screen dpad / buttons
    document.querySelectorAll('[data-key]').forEach(el => {
      const send = (v) => (ev) => { ev.preventDefault(); this._key(el.dataset.key, v); };
      el.addEventListener('touchstart', send(true), {passive:false});
      el.addEventListener('touchend', send(false), {passive:false});
      el.addEventListener('mousedown', send(true));
      el.addEventListener('mouseup', send(false));
      el.addEventListener('mouseleave', send(false));
    });
  }
  _mapKey(k) {
    switch (k) {
      case 'ArrowUp': case 'w': case 'W': return 'up';
      case 'ArrowDown': case 's': case 'S': return 'down';
      case 'ArrowLeft': case 'a': case 'A': return 'left';
      case 'ArrowRight': case 'd': case 'D': return 'right';
      case ' ': case 'Enter': case 'z': case 'Z': return 'confirm';
      case 'Escape': case 'x': case 'X': case 'Backspace': return 'cancel';
      case 'm': case 'M': return 'mute';
    }
    return null;
  }
  _key(rawKey, isDown) {
    const k = this._mapKey(rawKey);
    if (!k) return;
    this.audio.unlock();
    this.music.start();
    if (k === 'mute') { if (isDown) this.music.toggleMute(); return; }
    // continuous movement flags for overworld
    if (['up','down','left','right'].includes(k)) this.input[k] = isDown;
    if (!isDown) return;            // discrete actions on press only
    this._press(k);
  }
  _press(k) {
    if (this.state === 'title') {
      const opts = this.titleOptions();
      if (k === 'up') this.titleSel = (this.titleSel - 1 + opts.length) % opts.length;
      if (k === 'down') this.titleSel = (this.titleSel + 1) % opts.length;
      if (k === 'confirm') {
        const choice = opts[this.titleSel];
        if (choice === 'New Quest') this.goCharSelect();
        else if (choice === 'Continue') this.continueGame();
      }
      return;
    }
    if (this.state === 'charselect') {
      if (k === 'left')  this.classSel = (this.classSel - 1 + CLASSES.length) % CLASSES.length;
      if (k === 'right') this.classSel = (this.classSel + 1) % CLASSES.length;
      if (k === 'up')    this.classSel = (this.classSel - 1 + CLASSES.length) % CLASSES.length;
      if (k === 'down')  this.classSel = (this.classSel + 1) % CLASSES.length;
      if (k === 'confirm') this.newGame(CLASSES[this.classSel].id);
      if (k === 'cancel') { this.state = 'title'; this.titleSel = 0; }
      return;
    }
    if (this.state === 'dialog') {
      if (k === 'confirm') this.msg.advance();
      return;
    }
    if (this.state === 'battle' && this.battle) {
      this.battle.input(k);
      return;
    }
    if (this.state === 'gameover' || this.state === 'victory') {
      if (k === 'confirm') { this.state = 'title'; this.titleSel = 0; }
      return;
    }
    if (this.state === 'quest') {
      if (k === 'confirm') this.acceptQuest();
      else if (k === 'cancel') this.declineQuest();
      return;
    }
    if (this.state === 'dungeon') {
      if (!this.msg.empty) { if (k === 'confirm') this.msg.advance(); return; }
      if (k === 'up')    this.dungeon.step(-1, -1);
      else if (k === 'down')  this.dungeon.step(1, 1);
      else if (k === 'left')  this.dungeon.step(-1, 1);
      else if (k === 'right') this.dungeon.step(1, -1);
      return;
    }
    if (this.state === 'overworld') {
      if (k === 'confirm' && !this.msg.empty) this.msg.advance();
      if (k === 'cancel') this.save();
    }
  }

  titleOptions() { return this.hasSave() ? ['Continue', 'New Quest'] : ['New Quest']; }

  // ---- loop ----
  update(dt) {
    this.msg.update(dt);
    this.titleT += dt;
    this.music.setArea(this._musicArea());
    if (this.state === 'overworld') {
      this.world.update(dt, this.input);
    } else if (this.state === 'dungeon' && this.dungeon) {
      this.dungeon.update(dt, this.input);
    } else if (this.state === 'battle' && this.battle) {
      this.battle.update(dt);
    }
  }

  render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.W, this.H);
    if (this.state === 'title') return this._renderTitle(ctx);
    if (this.state === 'charselect') return this._renderCharSelect(ctx);
    if (this.state === 'gameover') {
      return this._renderEnd(ctx, 'NIGREDO', '#1a0808',
        `${this.hero ? this.hero.name : 'The adept'} dissolves into the blackness.\n` +
        `Reached floor ${this.deathDepth}.   Deepest descent: ${this.bestDepth()}.`);
    }
    if (this.state === 'victory') return this._renderEnd(ctx, 'RUBEDO — THE STONE', '#2a0d0d',
      'The Dragon is undone and the Lapis is achieved.\nThe Great Work is complete.');

    if (this.state === 'overworld' || this.state === 'dialog') {
      this.world.render(ctx);
      this._hud(ctx);
      if (!this.msg.empty) this.msg.render(ctx, 14, this.H - 116, this.W - 28, 104);
    } else if (this.state === 'dungeon' && this.dungeon) {
      this.dungeon.render(ctx);
      if (!this.msg.empty) this.msg.render(ctx, 14, this.H - 116, this.W - 28, 104);
    } else if (this.state === 'quest' && this.questOffer) {
      if (this.returnState === 'overworld' && this.world) { this.world.render(ctx); this._hud(ctx); }
      else if (this.dungeon) this.dungeon.render(ctx);
      this._renderQuest(ctx);
    } else if (this.state === 'battle' && this.battle) {
      this.battle.render(ctx);
    }
  }

  _objectiveText(o) {
    if (o.kind === 'slay') return `Slay ${o.target} creatures of the Work.`;
    if (o.kind === 'slayType') {
      const nm = (MONSTERS[o.monId] || {}).name || o.monId;
      const alt = o.alt ? ` or ${(MONSTERS[o.alt] || {}).name || o.alt}` : '';
      return `Slay ${o.target} ${nm}${alt}.`;
    }
    if (o.kind === 'collect') return `Gather ${o.target} relics from the floors.`;
    if (o.kind === 'gold') return `Gather ${o.target} gold.`;
    if (o.kind === 'reach' && o.stage) return `Reach the ${o.stage.toUpperCase()} stage.`;
    if (o.kind === 'reach' && o.deeper) return `Descend ${o.deeper} floors deeper.`;
    return 'Complete the Work.';
  }
  _rewardText(r) {
    const p = [];
    if (r.gold) p.push(`${r.gold} gold`);
    if (r.xp) p.push(`${r.xp} EXP`);
    if (r.maxhp) p.push(`+${r.maxhp} max HP`);
    if (r.item) p.push(`${r.item[1]}× ${ITEMS[r.item[0]].name}`);
    return p.join(', ');
  }

  _renderQuest(ctx) {
    const { who, quest } = this.questOffer;
    ctx.fillStyle = 'rgba(8,6,14,0.72)'; ctx.fillRect(0, 0, this.W, this.H);
    const pw = 560, ph = 360, px = this.W / 2 - pw / 2, py = this.H / 2 - ph / 2;
    parchmentCard(ctx, px, py, pw, ph);
    // giver portrait
    const img = Assets.img(who === 'king' ? 'q_king' : 'q_queen');
    if (img) {
      const sc = (ph - 90) / img.height, dw = img.width * sc, dh = img.height * sc;
      ctx.drawImage(img, px + 28, py + ph - 30 - dh, dw, dh);
    }
    const tx = px + 200, tw = pw - 224;
    const royal = who === 'king' ? 'THE KING — Sol' : 'THE QUEEN — Luna';
    text(ctx, quest.line === 'opus' ? `✦ THE GREAT WORK — Stage ${quest.step}/4` : royal,
      tx, py + 22, { size: 14, color: quest.line === 'opus' ? '#7a2010' : '#5b4226', shadow: false });
    text(ctx, `${quest.title}`, tx, py + 44, { size: 17, color: '#7a2010', shadow: false });
    text(ctx, `Emblem ${quest.roman}`, tx, py + 66, { size: 12, color: '#5b4226', shadow: false });
    // the motto (authentic quote)
    let yy = this._wrapInk(ctx, `“${quest.call}”`, tx, py + 88, tw, 18);
    // the emblem-poem couplet (recited verse)
    if (quest.poem) {
      yy += 8;
      quest.poem.forEach(ln => { text(ctx, ln, tx, yy, { size: 13, color: '#4a3a6a', shadow: false }); yy += 17; });
    }
    const oy = py + 224;
    text(ctx, 'CHARGE:', tx, oy, { size: 13, color: '#5b4226', shadow: false });
    this._wrapInk(ctx, this._objectiveText(quest.objective), tx, oy + 19, tw, 17);
    text(ctx, 'REWARD:', tx, oy + 56, { size: 13, color: '#5b4226', shadow: false });
    this._wrapInk(ctx, this._rewardText(quest.reward), tx, oy + 75, tw, 17);
    if (Math.floor(this.titleT * 1.5) % 2 === 0)
      text(ctx, 'Z — accept the charge      X — decline', this.W / 2, py + ph - 22, { align: 'center', size: 14, color: '#3a2a18', shadow: false });
  }
  _wrapInk(ctx, str, x, y, maxW, lh) {
    ctx.font = '15px "Courier New", monospace';
    const words = str.split(' '); let line = '', yy = y;
    for (const w of words) {
      const t = line ? line + ' ' + w : w;
      if (ctx.measureText(t).width > maxW && line) { text(ctx, line, x, yy, { size: 15, color: '#2a2118', shadow: false }); line = w; yy += lh; }
      else line = t;
    }
    if (line) { text(ctx, line, x, yy, { size: 15, color: '#2a2118', shadow: false }); yy += lh; }
    return yy;
  }

  _hud(ctx) {
    const h = this.hero;
    const w = 188, x = this.W - w - 12, y = 12;
    window9(ctx, x, y, w, 70);
    text(ctx, `${h.name}  Lv ${h.level}`, x + 12, y + 8, { size: 14, color: COLORS.hi });
    text(ctx, `HP ${h.hp}/${h.maxHp}`, x + 12, y + 26, { size: 13, color: COLORS.hpGreen });
    text(ctx, `MP ${h.mp}/${h.maxMp}`, x + 12, y + 44, { size: 13, color: COLORS.mpBlue });
    text(ctx, `G ${h.gold}`, x + 112, y + 26, { size: 13, color: COLORS.hi });
  }

  _renderTitle(ctx) {
    const g = ctx.createLinearGradient(0, 0, 0, this.H);
    g.addColorStop(0, '#10101f'); g.addColorStop(1, '#291a36');
    ctx.fillStyle = g; ctx.fillRect(0, 0, this.W, this.H);
    // sun emblem
    const sun = Assets.img('d_sun');
    if (sun) {
      const s = 1.1 + Math.sin(this.titleT) * 0.03;
      const dw = sun.width * s, dh = sun.height * s;
      ctx.save(); ctx.globalAlpha = 0.85;
      ctx.drawImage(sun, this.W/2 - dw/2, 70, dw, dh);
      ctx.restore();
    }
    text(ctx, 'EMBLEM  KNIGHT', this.W/2, 280, { align: 'center', size: 40, color: COLORS.hi });
    text(ctx, 'and the Alchemical Dragon', this.W/2, 326, { align: 'center', size: 18, color: COLORS.text });

    const opts = this.titleOptions();
    const ox = this.W/2 - 70, oy = 392;
    window9(ctx, ox - 20, oy - 14, 200, opts.length * 30 + 26);
    menu(ctx, opts, ox + 12, oy + 4, this.titleSel, { lh: 30 });
    const best = this.bestDepth();
    if (best > 0) text(ctx, `Deepest descent: floor ${best} / ${FINAL_FLOOR}`, this.W/2, oy + opts.length*30 + 24, { align: 'center', size: 13, color: COLORS.textDim });
    if (Math.floor(this.titleT * 1.5) % 2 === 0)
      text(ctx, 'Arrows / WASD  •  Z or Space = confirm', this.W/2, this.H - 36, { align: 'center', size: 13, color: COLORS.textDim });
  }

  _renderCharSelect(ctx) {
    const g = ctx.createLinearGradient(0, 0, 0, this.H);
    g.addColorStop(0, '#13101e'); g.addColorStop(1, '#241830');
    ctx.fillStyle = g; ctx.fillRect(0, 0, this.W, this.H);
    text(ctx, 'CHOOSE THY VESSEL', this.W/2, 30, { align: 'center', size: 26, color: COLORS.hi });

    const n = CLASSES.length, cw = this.W / n;
    for (let i = 0; i < n; i++) {
      const c = CLASSES[i], cx = i * cw + cw / 2, sel = i === this.classSel;
      // portrait card
      const cardW = cw - 28, cardH = 300, cardX = cx - cardW / 2, cardY = 70;
      parchmentCard(ctx, cardX, cardY, cardW, cardH);
      const img = Assets.img(c.sprite);
      if (img) {
        const sc = Math.min((cardW - 50) / img.width, (cardH - 60) / img.height);
        const dw = img.width * sc, dh = img.height * sc;
        ctx.drawImage(img, cx - dw / 2, cardY + cardH - 26 - dh, dw, dh);
      }
      if (sel) {
        ctx.lineWidth = 4; ctx.strokeStyle = COLORS.hi;
        ctx.strokeRect(cardX - 3, cardY - 3, cardW + 6, cardH + 6);
      }
      text(ctx, c.name, cx, cardY + cardH + 8, { align: 'center', size: 16, color: sel ? COLORS.hi : COLORS.text });
    }

    // detail panel for the selected class
    const c = CLASSES[this.classSel];
    const py = 408, pw = this.W - 80;
    window9(ctx, 40, py, pw, 120);
    text(ctx, c.name, 60, py + 14, { size: 18, color: COLORS.hi });
    this._wrap(ctx, c.blurb, 60, py + 40, pw - 40, 16);
    text(ctx, c.passive, 60, py + 88, { size: 14, color: COLORS.mpBlue });

    if (Math.floor(this.titleT * 1.5) % 2 === 0)
      text(ctx, '← → choose   •   Z confirm   •   X back', this.W/2, this.H - 26, { align: 'center', size: 13, color: COLORS.textDim });
  }

  _wrap(ctx, str, x, y, maxW, lh) {
    ctx.font = '15px "Courier New", monospace';
    const words = str.split(' ');
    let line = '', yy = y;
    for (const w of words) {
      const t = line ? line + ' ' + w : w;
      if (ctx.measureText(t).width > maxW && line) { text(ctx, line, x, yy, { size: 15 }); line = w; yy += lh; }
      else line = t;
    }
    if (line) text(ctx, line, x, yy, { size: 15 });
  }

  _renderEnd(ctx, title, bg, sub) {
    ctx.fillStyle = bg; ctx.fillRect(0, 0, this.W, this.H);
    text(ctx, title, this.W/2, this.H/2 - 60, { align: 'center', size: 46, color: COLORS.hi });
    sub.split('\n').forEach((ln, i) =>
      text(ctx, ln, this.W/2, this.H/2 + 10 + i*26, { align: 'center', size: 17, color: COLORS.text }));
    if (Math.floor(this.titleT * 1.5) % 2 === 0)
      text(ctx, 'Press Z to return', this.W/2, this.H - 60, { align: 'center', size: 15, color: COLORS.textDim });
  }
}

// ---- tiny WebAudio blip engine (no asset files needed) ---------------------
function makeAudio() {
  let ctx = null, unlocked = false;
  const ensure = () => { if (!ctx) { try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} } };
  const blip = (freq, dur, type = 'square', vol = 0.06) => {
    if (!ctx) return;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.value = freq;
    g.gain.value = vol;
    o.connect(g); g.connect(ctx.destination);
    const t = ctx.currentTime;
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.start(t); o.stop(t + dur);
  };
  const seq = (notes) => { let t = 0; notes.forEach(([f, d, ty]) => { setTimeout(() => blip(f, d, ty || 'square'), t * 1000); t += d * 0.85; }); };
  return {
    unlock() { ensure(); if (ctx && ctx.state === 'suspended') ctx.resume(); unlocked = true; },
    ctx() { return ctx; },
    play(name) {
      ensure(); if (!ctx) return;
      switch (name) {
        case 'hit': blip(140, 0.12, 'square', 0.08); break;
        case 'magic': seq([[660,0.06],[880,0.06],[1180,0.1]]); break;
        case 'heal': seq([[520,0.07],[700,0.07],[920,0.1,'triangle']]); break;
        case 'encounter': seq([[200,0.08],[160,0.08],[120,0.14,'sawtooth']]); break;
        case 'win': seq([[523,0.1],[659,0.1],[784,0.16]]); break;
        case 'level': seq([[523,0.09],[659,0.09],[784,0.09],[1046,0.2]]); break;
        case 'lose': seq([[300,0.15,'sawtooth'],[200,0.2,'sawtooth'],[120,0.35,'sawtooth']]); break;
      }
    }
  };
}

// ---- boot ------------------------------------------------------------------
async function boot() {
  const canvas = document.getElementById('game');
  const game = new Game(canvas);
  await Assets.load();
  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    game.update(dt);
    game.render();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  window.__game = game; // debug handle
}
boot();
