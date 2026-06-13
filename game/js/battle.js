// battle.js — Dragon Warrior style first-person battle.
import { Assets } from './assets.js';
import { MONSTERS, SPELLS, ITEMS, LEVELS, statsForLevel, spellsForLevel, recomputeStats } from './data.js';
import { window9, parchmentCard, text, menu, bar, COLORS } from './ui.js';

const PHASE = {
  INTRO: 'intro', MENU: 'menu', SUBMENU: 'submenu',
  ANIM: 'anim', RESULT: 'result', DONE: 'done'
};

export class Battle {
  constructor(game, monsterId, scale = 1) {
    this.game = game;
    this.hero = game.hero;
    const base = MONSTERS[monsterId];
    const sc = base.boss ? 1 : scale;   // bosses keep their authored stats
    const hp = Math.round(base.hp * sc);
    this.mon = {
      ...base, hp, maxHp: hp,
      atk: Math.round(base.atk * sc), def: Math.round(base.def * sc),
      xp: Math.round(base.xp * sc), gold: Math.round(base.gold * sc),
    };
    this.phase = PHASE.INTRO;
    this.cmd = 0;                 // top menu selection
    this.commands = ['FIGHT', 'SPELL', 'ITEM', 'RUN'];
    this.sub = 0;                 // submenu selection
    this.subType = null;          // 'spell' | 'item'
    this.subList = [];
    this.flash = 0;               // enemy hit flash
    this.shake = 0;               // screen shake timer
    this.heroFlash = 0;
    this.monAlpha = 1;            // fade out on death
    this.result = null;           // 'win'|'lose'|'run'
    this.pendingResolve = null;   // fn run after message empties during ANIM
    const m = game.msg;
    m.push(`A ${this.mon.name} draws near!`);
    m.onEmpty = () => { this.phase = PHASE.MENU; };
  }

  // ---- input -----------------------------------------------------------------
  input(key) {
    const m = this.game.msg;
    if (!m.empty) { // message showing
      if (key === 'confirm') {
        m.advance();
        if (m.empty && this.pendingResolve) { const f = this.pendingResolve; this.pendingResolve = null; f(); }
      }
      return;
    }
    if (this.phase === PHASE.MENU) {
      if (key === 'up')    this.cmd = (this.cmd + 2) % 4;
      if (key === 'down')  this.cmd = (this.cmd + 2) % 4;
      if (key === 'left')  this.cmd = (this.cmd + 3) % 4;
      if (key === 'right') this.cmd = (this.cmd + 1) % 4;
      if (key === 'confirm') this._choose(this.commands[this.cmd]);
    } else if (this.phase === PHASE.SUBMENU) {
      if (key === 'up')   this.sub = (this.sub - 1 + this.subList.length) % this.subList.length;
      if (key === 'down') this.sub = (this.sub + 1) % this.subList.length;
      if (key === 'cancel') { this.phase = PHASE.MENU; }
      if (key === 'confirm') this._pickSub();
    }
  }

  _choose(cmd) {
    if (cmd === 'FIGHT') { this._heroAttack(); }
    else if (cmd === 'RUN') { this._tryRun(); }
    else if (cmd === 'SPELL') {
      this.subType = 'spell';
      this.subList = this.hero.spells.map(k => ({ key: k, label: `${SPELLS[k].name}  ${SPELLS[k].cost}MP` }));
      if (this.subList.length === 0) { this.game.msg.push('No spells known.'); return; }
      this.sub = 0; this.phase = PHASE.SUBMENU;
    } else if (cmd === 'ITEM') {
      this.subType = 'item';
      this.subList = Object.keys(this.hero.items).filter(k => this.hero.items[k] > 0)
        .map(k => ({ key: k, label: `${ITEMS[k].name} x${this.hero.items[k]}` }));
      if (this.subList.length === 0) { this.game.msg.push('No items.'); return; }
      this.sub = 0; this.phase = PHASE.SUBMENU;
    }
  }

  _pickSub() {
    const entry = this.subList[this.sub];
    if (this.subType === 'spell') this._castSpell(entry.key);
    else this._useItem(entry.key);
  }

  // ---- player actions --------------------------------------------------------
  _dmg(atk, def) {
    const base = Math.max(1, atk - Math.floor(def / 2));
    const v = Math.floor(base * (0.8 + Math.random() * 0.4));
    const crit = Math.random() < 0.07;
    return { value: crit ? Math.floor(v * 1.8) : v, crit };
  }

  _heroAttack() {
    this.phase = PHASE.ANIM;
    const d = this._dmg(this.hero.atk, this.mon.def);
    if (this.hero.passiveKey === 'pursuer') d.value = Math.ceil(d.value * 1.15);
    this.mon.hp -= d.value;
    this.flash = 0.35; this.shake = 0.3;
    this.game.sfx('hit');
    this.game.msg.push(`${this.hero.name} attacks!`, d.crit ? `A mighty blow! ${d.value} damage.` : `${this.mon.name} takes ${d.value} damage.`);
    this.pendingResolve = () => this._afterHeroAction();
  }

  _castSpell(key) {
    const sp = SPELLS[key];
    if (this.hero.mp < sp.cost) { this.phase = PHASE.MENU; this.game.msg.push('Not enough MP!'); return; }
    this.hero.mp -= sp.cost;
    this.phase = PHASE.ANIM;
    if (sp.type === 'heal') {
      const amt = sp.power + Math.floor(Math.random() * 8);
      this.hero.hp = Math.min(this.hero.maxHp, this.hero.hp + amt);
      this.game.sfx('heal');
      this.game.msg.push(`${this.hero.name} casts ${sp.name}!`, `HP restored by ${amt}.`);
      this.pendingResolve = () => this._afterHeroAction(false);
    } else {
      const d = this._dmg(sp.power + 6, this.mon.def);
      this.mon.hp -= d.value;
      this.flash = 0.4; this.shake = 0.35;
      this.game.sfx('magic');
      this.game.msg.push(`${this.hero.name} casts ${sp.name}!`, `${this.mon.name} takes ${d.value} damage.`);
      this.pendingResolve = () => this._afterHeroAction();
    }
  }

  _useItem(key) {
    const it = ITEMS[key];
    this.hero.items[key]--;
    this.phase = PHASE.ANIM;
    if (it.type === 'heal') {
      const amt = it.power + Math.floor(Math.random() * 8);
      this.hero.hp = Math.min(this.hero.maxHp, this.hero.hp + amt);
      this.game.sfx('heal');
      this.game.msg.push(`Used ${it.name}.`, `HP restored by ${amt}.`);
      this.pendingResolve = () => this._afterHeroAction(false);
    } else if (it.type === 'mp') {
      this.hero.mp = Math.min(this.hero.maxMp, this.hero.mp + it.power);
      this.game.sfx('heal');
      this.game.msg.push(`Used ${it.name}.`, `MP restored by ${it.power}.`);
      this.pendingResolve = () => this._afterHeroAction(false);
    } else if (it.type === 'full') {
      this.hero.hp = this.hero.maxHp; this.hero.mp = this.hero.maxMp;
      this.game.sfx('heal');
      this.game.msg.push(`Quaffed the ${it.name}!`, 'HP and MP fully restored.');
      this.pendingResolve = () => this._afterHeroAction(false);
    } else if (it.type === 'flee') {
      // Golden Apple — Atalanta's trick: escape any battle, even a boss.
      this.game.sfx('heal');
      this.game.msg.push('A Golden Apple is cast down!', `${this.mon.name} is distracted — ${this.hero.name} slips away!`);
      this.result = 'run';
      this.pendingResolve = () => this._finish();
    }
  }

  _tryRun() {
    this.phase = PHASE.ANIM;
    // Atalanta's volatility: she always escapes
    if (this.hero.passiveKey === 'volatile') {
      this.game.msg.push(`${this.hero.name} is too swift to catch — fled!`);
      this.result = 'run'; this.pendingResolve = () => this._finish(); return;
    }
    if (this.mon.boss) { this.game.msg.push('The Dragon blocks your escape!'); this.pendingResolve = () => this._enemyTurn(); return; }
    const ok = Math.random() < 0.6;
    if (ok) { this.game.msg.push('The Knight fled!'); this.result = 'run'; this.pendingResolve = () => this._finish(); }
    else { this.game.msg.push('Could not escape!'); this.pendingResolve = () => this._enemyTurn(); }
  }

  _afterHeroAction(checkDeath = true) {
    if (checkDeath && this.mon.hp <= 0) { this._enemyDefeated(); return; }
    this._enemyTurn();
  }

  // ---- enemy turn ------------------------------------------------------------
  _enemyTurn() {
    // enemy may cast its spell occasionally
    const canSpell = this.mon.spell && this.mon.mp !== 0;
    if (canSpell && Math.random() < 0.3) {
      const sp = SPELLS[this.mon.spell];
      const d = this._dmg(sp.power + this.mon.atk * 0.4, this.hero.def);
      this.hero.hp -= d.value; this.heroFlash = 0.4; this.shake = 0.3;
      this.game.sfx('magic');
      this.game.msg.push(`${this.mon.name} breathes ${sp.name}!`, `${this.hero.name} takes ${d.value} damage.`);
    } else {
      const d = this._dmg(this.mon.atk, this.hero.def);
      this.hero.hp -= d.value; this.heroFlash = 0.4; this.shake = 0.25;
      this.game.sfx('hit');
      this.game.msg.push(`${this.mon.name} attacks!`, d.crit ? `A savage hit! ${d.value} damage.` : `${this.hero.name} takes ${d.value} damage.`);
    }
    this.pendingResolve = () => {
      if (this.hero.hp <= 0) { this.hero.hp = 0; this._heroDefeated(); }
      else this.phase = PHASE.MENU;
    };
  }

  // ---- resolution ------------------------------------------------------------
  _enemyDefeated() {
    this.monAlpha = 0; // fade handled in render via timer
    this.result = 'win';
    this.game.sfx('win');
    const xp = this.mon.xp, gold = this.mon.gold;
    this.hero.xp += xp; this.hero.gold += gold;
    this.game.msg.push(`${this.mon.name} is vanquished!`, `${xp} EXP and ${gold} gold gained.`);
    const ups = this._applyLevelUps();
    ups.forEach(line => this.game.msg.push(line));
    if (this.mon.boss) {
      this.hero.flags.dragonSlain = true;
      this.game.msg.push('The land is freed from the Dragon!');
    }
    this.pendingResolve = () => this._finish();
  }

  _applyLevelUps() {
    const lines = [];
    let leveled = false;
    while (this.hero.level < LEVELS.length && this.hero.xp >= LEVELS[this.hero.level]) {
      this.hero.level++;
      leveled = true;
      recomputeStats(this.hero);
      this.hero.hp = this.hero.maxHp; this.hero.mp = this.hero.maxMp;
      lines.push(`${this.hero.name} is now level ${this.hero.level}!`);
      const newSpells = spellsForLevel(this.hero.level).filter(k => !this.hero.spells.includes(k));
      newSpells.forEach(k => { this.hero.spells.push(k); lines.push(`Learned ${SPELLS[k].name}!`); });
    }
    if (leveled) this.game.sfx('level');
    return lines;
  }

  _heroDefeated() {
    this.result = 'lose';
    this.game.sfx('lose');
    this.game.msg.push(`${this.hero.name} has fallen...`);
    this.pendingResolve = () => this._finish();
  }

  _finish() {
    this.phase = PHASE.DONE;
    this.game.endBattle(this.result);
  }

  // ---- update / render -------------------------------------------------------
  update(dt) {
    if (this.flash > 0) this.flash -= dt;
    if (this.heroFlash > 0) this.heroFlash -= dt;
    if (this.shake > 0) this.shake -= dt;
  }

  render(ctx) {
    const W = this.game.W, H = this.game.H;
    let sx = 0, sy = 0;
    if (this.shake > 0) { sx = (Math.random() - 0.5) * 8; sy = (Math.random() - 0.5) * 8; }
    ctx.save();
    ctx.translate(sx, sy);

    // battle backdrop: dim sky gradient
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#1b1430'); g.addColorStop(1, '#0a0712');
    ctx.fillStyle = g; ctx.fillRect(-10, -10, W + 20, H + 20);

    // parchment monster card
    const cardW = 360, cardH = 300, cardX = W / 2 - cardW / 2, cardY = 70;
    parchmentCard(ctx, cardX, cardY, cardW, cardH);

    // monster sprite on card
    if (this.result !== 'win' || this.monAlpha > 0) {
      const img = Assets.img(this.mon.sprite);
      if (img) {
        const maxW = cardW - 60, maxH = cardH - 70;
        let scale = Math.min(maxW / img.width, maxH / img.height) * (this.mon.scale || 1);
        const dw = img.width * scale, dh = img.height * scale;
        ctx.save();
        ctx.globalAlpha = (this.result === 'win') ? Math.max(0, this.monAlpha) : 1;
        if (this.flash > 0 && Math.floor(this.flash * 20) % 2 === 0) ctx.globalAlpha *= 0.35;
        ctx.drawImage(img, cardX + cardW / 2 - dw / 2, cardY + cardH - 30 - dh, dw, dh);
        ctx.restore();
      }
    }
    // monster name plate
    text(ctx, this.mon.name, W / 2, cardY - 30, { align: 'center', size: 18, color: COLORS.hi });
    // enemy hp pips
    bar(ctx, cardX + 40, cardY + cardH + 6, cardW - 80, 8, this.mon.hp / this.mon.maxHp, COLORS.hpRed);

    // ---- hero status window (top-left) ----
    this._statusWindow(ctx, 14, 12);

    // ---- command / message area (bottom) ----
    const boxY = H - 132, boxH = 120;
    if (this.game.msg.empty && (this.phase === PHASE.MENU || this.phase === PHASE.SUBMENU)) {
      // command window
      const cw = 220;
      window9(ctx, 14, boxY, cw, boxH);
      menu(ctx, this.commands, 50, boxY + 18, this.cmd, { colW: 95, lh: 30 });
      if (this.phase === PHASE.SUBMENU) {
        const subW = W - cw - 44;
        window9(ctx, cw + 30, boxY, subW, boxH);
        menu(ctx, this.subList.map(s => s.label), cw + 66, boxY + 16, this.sub, { lh: 24 });
      } else {
        // prompt
        const subW = W - cw - 44;
        window9(ctx, cw + 30, boxY, subW, boxH);
        text(ctx, 'Command?', cw + 52, boxY + 16, { size: 16 });
      }
    } else {
      this.game.msg.render(ctx, 14, boxY, W - 28, boxH);
    }

    // hero hit flash overlay
    if (this.heroFlash > 0 && Math.floor(this.heroFlash * 20) % 2 === 0) {
      ctx.fillStyle = 'rgba(200,40,40,0.18)'; ctx.fillRect(0, 0, W, H);
    }
    ctx.restore();
  }

  _statusWindow(ctx, x, y) {
    const w = 200, h = 96;
    window9(ctx, x, y, w, h);
    const h0 = this.hero;
    text(ctx, `${h0.name}  Lv ${h0.level}`, x + 14, y + 10, { size: 15, color: COLORS.hi });
    text(ctx, `HP ${h0.hp}/${h0.maxHp}`, x + 14, y + 32, { size: 14 });
    bar(ctx, x + 14, y + 50, w - 28, 6, h0.hp / h0.maxHp, COLORS.hpGreen);
    text(ctx, `MP ${h0.mp}/${h0.maxMp}`, x + 14, y + 60, { size: 14 });
    bar(ctx, x + 14, y + 78, w - 28, 6, h0.maxMp ? h0.mp / h0.maxMp : 0, COLORS.mpBlue);
  }
}
