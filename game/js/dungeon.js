// dungeon.js — the Opus: a procedurally generated, fog-of-war roguelike descent.
// Reuses the isometric projection. Floors are themed by the four colour stages
// of the Great Work (Nigredo → Albedo → Citrinitas → Rubedo).
import { Assets } from './assets.js';
import { ITEMS, stageForFloor, FINAL_FLOOR, QUESTS } from './data.js';
import { window9, text, COLORS } from './ui.js';

const QUESTS_LOOKUP = Object.fromEntries(QUESTS.map(q => [q.id, q]));

const TILE_W = 64, TILE_H = 32, WALL_H = 26;
const GW = 26, GH = 26;            // floor grid size
const SIGHT = 4;                   // fog-of-war radius
const WALL = 1, FLOOR = 0, STAIRS = 2;

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  let r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  r = Math.round(r * f); g = Math.round(g * f); b = Math.round(b * f);
  return `rgb(${r},${g},${b})`;
}

export class Dungeon {
  constructor(game, depth) {
    this.game = game;
    this.hero = game.hero;
    this.depth = depth;
    this.stage = stageForFloor(depth);
    this.cam = { x: 0, y: 0 };
    this.bob = 0;
    this.generate();
    this._snapCamera();
  }

  // ---- generation ------------------------------------------------------------
  generate() {
    const g = [];
    for (let y = 0; y < GH; y++) g.push(new Array(GW).fill(WALL));
    this.grid = g;
    this.seen = []; this.vis = [];
    for (let y = 0; y < GH; y++) { this.seen.push(new Array(GW).fill(false)); this.vis.push(new Array(GW).fill(false)); }

    // carve rooms
    const rooms = [];
    const tries = 60, count = 6 + Math.min(5, Math.floor(this.depth / 2));
    for (let i = 0; i < tries && rooms.length < count; i++) {
      const w = 3 + this._ri(4), h = 3 + this._ri(4);
      const x = 1 + this._ri(GW - w - 2), y = 1 + this._ri(GH - h - 2);
      const room = { x, y, w, h, cx: x + (w >> 1), cy: y + (h >> 1) };
      for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) g[yy][xx] = FLOOR;
      rooms.push(room);
    }
    // connect room centres with L corridors
    for (let i = 1; i < rooms.length; i++) {
      const a = rooms[i - 1], b = rooms[i];
      this._hCorr(a.cx, b.cx, a.cy);
      this._vCorr(a.cy, b.cy, b.cx);
    }
    this.rooms = rooms;

    // player start = first room
    const start = rooms[0];
    this.hero.gx = start.cx; this.hero.gy = start.cy;

    // entities
    this.enemies = [];
    this.items = [];
    this.boss = null;
    this.stairs = null;

    const last = rooms[rooms.length - 1];
    if (this.depth >= FINAL_FLOOR) {
      // the Dragon guards the foot of the Work; no stairs beyond
      this.boss = { gx: last.cx, gy: last.cy, monId: 'dragon', boss: true };
      this.enemies.push(this.boss);
    } else {
      this.grid[last.cy][last.cx] = STAIRS;
      this.stairs = { gx: last.cx, gy: last.cy };
    }

    // wandering monsters
    const nEnemies = 3 + Math.min(7, this.depth);
    for (let i = 0; i < nEnemies; i++) {
      const p = this._freeFloor(2);
      if (!p) break;
      const monId = this.stage.pool[this._ri(this.stage.pool.length)];
      this.enemies.push({ gx: p.x, gy: p.y, monId });
    }

    // loot
    const lootTable = ['herb', 'herb', 'potion', 'apple', 'elixir', 'gold', 'salt'];
    const nItems = 3 + this._ri(3);
    for (let i = 0; i < nItems; i++) {
      const p = this._freeFloor(1);
      if (!p) break;
      const kind = lootTable[this._ri(lootTable.length)];
      this.items.push({ gx: p.x, gy: p.y, kind });
    }
    // a King or Queen may hold court on this floor (random calls to action)
    this.giver = null;
    if (this.depth < FINAL_FLOOR && Math.random() < 0.55) {
      const p = this._freeFloor(2);
      if (p) this.giver = { gx: p.x, gy: p.y, who: Math.random() < 0.5 ? 'king' : 'queen' };
    }

    this._computeFov();
  }

  _ri(n) { return Math.floor(Math.random() * n); }
  _hCorr(x0, x1, y) { for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++) if (this.grid[y][x] === WALL) this.grid[y][x] = FLOOR; }
  _vCorr(y0, y1, x) { for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++) if (this.grid[y][x] === WALL) this.grid[y][x] = FLOOR; }
  _occupied(x, y) {
    if (this.hero.gx === x && this.hero.gy === y) return true;
    return this.enemies.some(e => e.gx === x && e.gy === y) || this.items.some(it => it.gx === x && it.gy === y);
  }
  _freeFloor(minDistFromStart) {
    for (let t = 0; t < 200; t++) {
      const x = this._ri(GW), y = this._ri(GH);
      if (this.grid[y][x] !== FLOOR) continue;
      if (this._occupied(x, y)) continue;
      if (minDistFromStart) {
        const d = Math.abs(x - this.hero.gx) + Math.abs(y - this.hero.gy);
        if (d < minDistFromStart + 1) continue;
      }
      return { x, y };
    }
    return null;
  }

  // ---- fog of war ------------------------------------------------------------
  _computeFov() {
    for (let y = 0; y < GH; y++) for (let x = 0; x < GW; x++) this.vis[y][x] = false;
    const px = this.hero.gx, py = this.hero.gy;
    for (let y = py - SIGHT; y <= py + SIGHT; y++) {
      for (let x = px - SIGHT; x <= px + SIGHT; x++) {
        if (x < 0 || y < 0 || x >= GW || y >= GH) continue;
        if ((x - px) * (x - px) + (y - py) * (y - py) <= SIGHT * SIGHT) {
          this.vis[y][x] = true; this.seen[y][x] = true;
        }
      }
    }
  }

  // ---- iso helpers -----------------------------------------------------------
  iso(gx, gy) { return { x: (gx - gy) * TILE_W / 2, y: (gx + gy) * TILE_H / 2 }; }
  _snapCamera() { const p = this.iso(this.hero.gx, this.hero.gy); this.cam.x = p.x - this.game.W / 2; this.cam.y = p.y - this.game.H / 2 + 20; }

  passable(x, y) {
    if (x < 0 || y < 0 || x >= GW || y >= GH) return false;
    return this.grid[y][x] !== WALL;
  }

  // ---- turn logic ------------------------------------------------------------
  update(dt, input) {
    this.bob += dt * 6;
    const p = this.iso(this.hero.gx, this.hero.gy);
    const tx = p.x - this.game.W / 2, ty = p.y - this.game.H / 2 + 20;
    this.cam.x += (tx - this.cam.x) * Math.min(1, dt * 12);
    this.cam.y += (ty - this.cam.y) * Math.min(1, dt * 12);
  }

  // called by main on a movement keypress
  step(dgx, dgy) {
    if (!this.game.msg.empty) return;
    const nx = this.hero.gx + dgx, ny = this.hero.gy + dgy;
    // King or Queen in target tile? -> hold an audience (random quest)
    if (this.giver && this.giver.gx === nx && this.giver.gy === ny) {
      const who = this.giver.who; this.giver = null;
      this.game.offerQuest(who); return;
    }
    // enemy in target tile? -> fight it
    const foe = this.enemies.find(e => e.gx === nx && e.gy === ny);
    if (foe) { this._fight(foe); return; }
    if (!this.passable(nx, ny)) return;        // wall, no turn taken
    this.hero.gx = nx; this.hero.gy = ny;
    this._pickup();
    this._computeFov();
    if (this.grid[ny][nx] === STAIRS) { this._descend(); return; }
    this._enemyTurn();
  }

  _pickup() {
    const i = this.items.findIndex(it => it.gx === this.hero.gx && it.gy === this.hero.gy);
    if (i < 0) return;
    const it = this.items.splice(i, 1)[0];
    const h = this.hero;
    if (it.kind === 'gold') {
      const amt = 8 + this._ri(14 + this.depth * 2);
      h.gold += amt; this.game.sfx('heal');
      this.game.msg.push(`Found ${amt} gold.`);
      this.game.questProgress('gold', {});
    } else if (it.kind === 'salt') {
      h.maxHp += 4; h.hp += 4; this.game.sfx('level');
      this.game.msg.push('Philosophic Salt — max HP +4.');
      this.game.questProgress('collect', {});
    } else {
      h.items[it.kind] = (h.items[it.kind] || 0) + 1;
      this.game.sfx('heal');
      this.game.msg.push(`Found a ${ITEMS[it.kind].name}.`);
      this.game.questProgress('collect', {});
    }
  }

  _descend() {
    this.game.sfx('encounter');
    this.game.descend();
  }

  _fight(enemy) {
    const scale = 1 + (this.depth - 1) * 0.12;
    this.game.startDungeonBattle(enemy.monId, enemy, enemy.boss ? 1 : scale);
  }

  // remove a defeated enemy (called by main after a won battle)
  removeEnemy(enemy) {
    const i = this.enemies.indexOf(enemy);
    if (i >= 0) this.enemies.splice(i, 1);
  }

  _enemyTurn() {
    let bumped = null;
    for (const e of this.enemies) {
      const d = Math.abs(e.gx - this.hero.gx) + Math.abs(e.gy - this.hero.gy);
      let dx = 0, dy = 0;
      if (d <= 6) {                         // chase
        if (Math.abs(this.hero.gx - e.gx) > Math.abs(this.hero.gy - e.gy)) dx = Math.sign(this.hero.gx - e.gx);
        else dy = Math.sign(this.hero.gy - e.gy);
      } else if (Math.random() < 0.5) {     // wander
        const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
        const dd = dirs[this._ri(4)]; dx = dd[0]; dy = dd[1];
      }
      if (dx === 0 && dy === 0) continue;
      const tx = e.gx + dx, ty = e.gy + dy;
      if (tx === this.hero.gx && ty === this.hero.gy) { bumped = e; continue; }
      if (this.passable(tx, ty) && !this._occupied(tx, ty)) { e.gx = tx; e.gy = ty; }
    }
    if (bumped) this._fight(bumped);
  }

  // ---- render ----------------------------------------------------------------
  render(ctx) {
    const W = this.game.W, H = this.game.H;
    ctx.fillStyle = this.stage.tint; ctx.fillRect(0, 0, W, H);
    const ox = -this.cam.x, oy = -this.cam.y;

    for (let s = 0; s < GW + GH; s++) {
      for (let gx = 0; gx < GW; gx++) {
        const gy = s - gx;
        if (gy < 0 || gy >= GH) continue;
        if (!this.seen[gy][gx]) continue;
        const t = this.grid[gy][gx];
        const p = this.iso(gx, gy);
        const sx = p.x + ox, sy = p.y + oy;
        if (sx < -TILE_W || sx > W + TILE_W || sy < -80 || sy > H + 80) continue;
        const lit = this.vis[gy][gx];
        const f = lit ? 1 : 0.5;
        if (t === WALL) this._wall(ctx, sx, sy, f);
        else this._floor(ctx, sx, sy, t, f);

        // entities only when currently visible
        if (lit) {
          const it = this.items.find(o => o.gx === gx && o.gy === gy);
          if (it) this._item(ctx, sx, sy, it);
          const en = this.enemies.find(o => o.gx === gx && o.gy === gy);
          if (en) this._enemy(ctx, sx, sy, en);
          if (this.giver && this.giver.gx === gx && this.giver.gy === gy) this._giver(ctx, sx, sy, this.giver);
        }
        if (gx === this.hero.gx && gy === this.hero.gy) this._player(ctx, sx, sy);
      }
    }
    this._hud(ctx);
  }

  _diamond(ctx, sx, sy, c) {
    ctx.beginPath();
    ctx.moveTo(sx, sy - TILE_H / 2); ctx.lineTo(sx + TILE_W / 2, sy);
    ctx.lineTo(sx, sy + TILE_H / 2); ctx.lineTo(sx - TILE_W / 2, sy);
    ctx.closePath(); ctx.fillStyle = c; ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.25)'; ctx.lineWidth = 1; ctx.stroke();
  }

  _floor(ctx, sx, sy, t, f) {
    this._diamond(ctx, sx, sy, shade(this.stage.floor, f));
    if (t === STAIRS) {
      ctx.fillStyle = shade('#1a1410', f);
      ctx.beginPath();
      ctx.moveTo(sx, sy - 10); ctx.lineTo(sx + 18, sy); ctx.lineTo(sx, sy + 10); ctx.lineTo(sx - 18, sy);
      ctx.closePath(); ctx.fill();
      text(ctx, '▼', sx, sy - 9, { align: 'center', size: 14, color: f > 0.7 ? COLORS.hi : '#8a7a3a' });
    }
  }

  _wall(ctx, sx, sy, f) {
    const top = shade(this.stage.wall, f);
    const left = shade(this.stage.wall, f * 0.7);
    const right = shade(this.stage.wall, f * 0.55);
    // left face
    ctx.fillStyle = left;
    ctx.beginPath();
    ctx.moveTo(sx - TILE_W / 2, sy); ctx.lineTo(sx, sy + TILE_H / 2);
    ctx.lineTo(sx, sy + TILE_H / 2 - WALL_H); ctx.lineTo(sx - TILE_W / 2, sy - WALL_H);
    ctx.closePath(); ctx.fill();
    // right face
    ctx.fillStyle = right;
    ctx.beginPath();
    ctx.moveTo(sx + TILE_W / 2, sy); ctx.lineTo(sx, sy + TILE_H / 2);
    ctx.lineTo(sx, sy + TILE_H / 2 - WALL_H); ctx.lineTo(sx + TILE_W / 2, sy - WALL_H);
    ctx.closePath(); ctx.fill();
    // top
    ctx.beginPath();
    ctx.moveTo(sx, sy - TILE_H / 2 - WALL_H); ctx.lineTo(sx + TILE_W / 2, sy - WALL_H);
    ctx.lineTo(sx, sy + TILE_H / 2 - WALL_H); ctx.lineTo(sx - TILE_W / 2, sy - WALL_H);
    ctx.closePath(); ctx.fillStyle = top; ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.3)'; ctx.lineWidth = 1; ctx.stroke();
  }

  _sprite(ctx, name, sx, sy, maxH, f) {
    const img = Assets.img(name); if (!img) return;
    const scale = maxH / img.height;
    const dw = img.width * scale, dh = img.height * scale;
    ctx.save();
    if (f < 0.9) ctx.globalAlpha = 0.85;
    ctx.drawImage(img, sx - dw / 2, sy + TILE_H / 2 - dh, dw, dh);
    ctx.restore();
  }

  _player(ctx, sx, sy) {
    ctx.save(); ctx.fillStyle = 'rgba(0,0,0,0.3)';
    ctx.beginPath(); ctx.ellipse(sx, sy + 2, 14, 6, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    this._sprite(ctx, this.hero.sprite || 'hero', sx, sy, 46, 1);
  }

  _enemy(ctx, sx, sy, e) {
    ctx.save(); ctx.fillStyle = 'rgba(0,0,0,0.28)';
    ctx.beginPath(); ctx.ellipse(sx, sy + 2, 14, 6, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    const sprite = 'm_' + e.monId;
    this._sprite(ctx, sprite, sx, sy, e.boss ? 64 : 40, 1);
  }

  _giver(ctx, sx, sy, gv) {
    // golden audience glow under the royal figure
    ctx.save();
    ctx.fillStyle = 'rgba(255,210,90,0.16)';
    ctx.beginPath(); ctx.ellipse(sx, sy + 2, 22, 10, 0, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
    this._sprite(ctx, gv.who === 'king' ? 'q_king' : 'q_queen', sx, sy, 50, 1);
    text(ctx, gv.who === 'king' ? '♔' : '♕', sx, sy - 56, { align: 'center', size: 16, color: COLORS.hi });
  }

  _item(ctx, sx, sy, it) {
    const col = { gold: '#ffd54a', herb: '#6fd06f', potion: '#6aa8ff', elixir: '#e0584b', apple: '#ffcf3a', salt: '#eaeaea' }[it.kind] || '#fff';
    const yy = sy - 6 + Math.sin(this.bob + sx) * 2;
    ctx.save();
    ctx.shadowColor = col; ctx.shadowBlur = 8;
    ctx.fillStyle = col;
    ctx.beginPath(); ctx.arc(sx, yy, 5, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

  _hud(ctx) {
    const W = this.game.W, h = this.hero;
    // depth / stage banner (top-centre)
    window9(ctx, W / 2 - 150, 8, 300, 44);
    text(ctx, `${this.stage.name} — ${this.stage.sub}`, W / 2, 14, { align: 'center', size: 15, color: COLORS.hi });
    text(ctx, `Floor ${this.depth} / ${FINAL_FLOOR}`, W / 2, 32, { align: 'center', size: 13, color: COLORS.textDim });
    // hero status (top-left)
    window9(ctx, 12, 8, 196, 64);
    text(ctx, `${h.name}  Lv ${h.level}`, 24, 14, { size: 14, color: COLORS.hi });
    text(ctx, `HP ${h.hp}/${h.maxHp}`, 24, 32, { size: 13, color: COLORS.hpGreen });
    text(ctx, `MP ${h.mp}/${h.maxMp}`, 24, 50, { size: 13, color: COLORS.mpBlue });
    text(ctx, `G ${h.gold}`, 132, 32, { size: 13, color: COLORS.hi });
    text(ctx, `Apples ${h.items.apple || 0}`, 132, 50, { size: 12, color: COLORS.textDim });
    // active quest log (left side)
    const quests = h.quests || [];
    if (quests.length) {
      const qy = 80;
      window9(ctx, 12, qy, 220, 22 + quests.length * 18);
      text(ctx, 'CHARGES', 24, qy + 6, { size: 12, color: COLORS.hi });
      quests.forEach((a, i) => {
        const def = QUESTS_LOOKUP[a.id]; if (!def) return;
        const o = def.objective;
        let prog = '';
        if (o.kind === 'slay' || o.kind === 'slayType' || o.kind === 'collect') prog = ` ${a.count}/${o.target}`;
        else if (o.kind === 'gold') prog = ` ${Math.min(o.target, h.gold - a.baseGold)}/${o.target}`;
        else if (o.kind === 'reach' && o.deeper) prog = ` ${Math.min(o.deeper, this.depth - a.acceptDepth)}/${o.deeper}`;
        text(ctx, `• ${def.title}${prog}`, 24, qy + 24 + i * 18, { size: 12, color: COLORS.text });
      });
    }
  }
}
