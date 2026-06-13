// world.js — isometric overworld: render, hero movement, encounters, landmarks.
import { MAP, MAP_LEGEND, BLOCKED, NO_ENCOUNTER, REGION_POOLS, MONSTERS } from './data.js';
import { Assets } from './assets.js';

const TILE_W = 64, TILE_H = 32;          // diamond tile footprint
const COLS = MAP[0].length, ROWS = MAP.length;

// per-tile-type base color (top face of the diamond)
const TILE_COLOR = {
  grass:   ['#5b8a3a', '#4f7d32'],
  plains:  ['#8aa24a', '#7d9540'],
  forest:  ['#3f6f2e', '#356126'],
  woods:   ['#3a6630', '#2f5526'],
  mountain:['#7d7468', '#6b6359'],
  peaks:   ['#8c8377', '#736a5e'],
  water:   ['#356a9e', '#2d5d8c'],
  path:    ['#b89b63', '#a98d57'],
  castle:  ['#9a8f7a', '#8a8068'],
  town:    ['#a89a78', '#988a6a'],
  queencourt: ['#9a8aa0', '#897a90'],
  dungeon: ['#5a4a55', '#4c3e48'],
  badlands:['#9c6b46', '#86593a'],
  cave:    ['#6f6354', '#5c5145'],
  cliff:   ['#9b9384', '#867e6f'],
};
// structures placed on a tile, anchored bottom-center
const TILE_DECOR = {
  forest: 't_forest', woods: 't_forest2',
  mountain: 't_mountain', peaks: 't_mountain2',
  cave: 't_cave', cliff: 't_cliff',
  castle: 's_castle', town: 's_town', dungeon: 's_door',
  queencourt: 'q_queen',
};

export function tileType(gx, gy) {
  if (gx < 0 || gy < 0 || gx >= COLS || gy >= ROWS) return 'water';
  return MAP_LEGEND[MAP[gy][gx]] || 'grass';
}

export class World {
  constructor(game) {
    this.game = game;
    this.hero = game.hero;
    this.move = null;        // active tween {fx,fy,tx,ty,t,dur,dgx,dgy}
    this.stepsToEnc = this._rollSteps();
    this.bob = 0;
    // snap camera to centre on the hero immediately
    const hs0 = this.iso(this.hero.gx, this.hero.gy);
    this.cam = { x: hs0.x - game.W / 2, y: hs0.y - game.H / 2 + 40 };
  }

  _rollSteps() { return 5 + Math.floor(Math.random() * 9); }

  // grid -> screen (un-cameraed)
  iso(gx, gy) {
    return {
      x: (gx - gy) * TILE_W / 2,
      y: (gx + gy) * TILE_H / 2,
    };
  }

  tryMove(dgx, dgy, facing) {
    if (this.move) return;
    const h = this.hero;
    h.facing = facing;
    const nx = h.gx + dgx, ny = h.gy + dgy;
    const tt = tileType(nx, ny);
    if (BLOCKED.has(tt)) { return; }
    this.move = { fx: h.gx, fy: h.gy, dgx, dgy, t: 0, dur: 0.16 };
  }

  update(dt, input) {
    this.bob += dt * 6;
    // input -> movement (screen-aligned diagonal grid steps), only when idle
    if (!this.move && this.game.msg.empty) {
      if (input.up)    this.tryMove(-1, -1, 'up');
      else if (input.down)  this.tryMove(1, 1, 'down');
      else if (input.left)  this.tryMove(-1, 1, 'left');
      else if (input.right) this.tryMove(1, -1, 'right');
    }

    if (this.move) {
      this.move.t += dt;
      const k = Math.min(1, this.move.t / this.move.dur);
      if (k >= 1) {
        // commit
        const h = this.hero;
        h.gx += this.move.dgx; h.gy += this.move.dgy;
        this.move = null;
        this._onArrive();
      }
    }
    this._updateCamera(dt);
  }

  _onArrive() {
    const h = this.hero;
    const tt = tileType(h.gx, h.gy);
    // landmarks
    if (tt === 'castle') { this.game.enterCastle(); return; }
    if (tt === 'queencourt') { this.game.enterQueenCourt(); return; }
    if (tt === 'town')   { this.game.enterTown(); return; }
    if (tt === 'dungeon'){ this.game.enterDungeon(); return; }
    // encounters
    if (!NO_ENCOUNTER.has(tt)) {
      this.stepsToEnc--;
      if (this.stepsToEnc <= 0) {
        this.stepsToEnc = this._rollSteps();
        const pool = REGION_POOLS[tt] || REGION_POOLS.grass;
        const id = pool[Math.floor(Math.random() * pool.length)];
        this.game.startBattle(id);
      }
    }
  }

  heroScreen() {
    // interpolate during move
    const h = this.hero;
    let gx = h.gx, gy = h.gy;
    if (this.move) {
      const k = Math.min(1, this.move.t / this.move.dur);
      gx = this.move.fx + this.move.dgx * k;
      gy = this.move.fy + this.move.dgy * k;
    }
    return this.iso(gx, gy);
  }

  _updateCamera(dt) {
    const hs = this.heroScreen();
    const tx = hs.x - this.game.W / 2;
    const ty = hs.y - this.game.H / 2 + 40;
    // smooth follow
    this.cam.x += (tx - this.cam.x) * Math.min(1, dt * 8);
    this.cam.y += (ty - this.cam.y) * Math.min(1, dt * 8);
  }

  _diamond(ctx, sx, sy, c1, c2) {
    ctx.beginPath();
    ctx.moveTo(sx, sy - TILE_H / 2);
    ctx.lineTo(sx + TILE_W / 2, sy);
    ctx.lineTo(sx, sy + TILE_H / 2);
    ctx.lineTo(sx - TILE_W / 2, sy);
    ctx.closePath();
    const g = ctx.createLinearGradient(sx, sy - TILE_H/2, sx, sy + TILE_H/2);
    g.addColorStop(0, c1); g.addColorStop(1, c2);
    ctx.fillStyle = g; ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.18)'; ctx.lineWidth = 1; ctx.stroke();
  }

  render(ctx) {
    const W = this.game.W, H = this.game.H;
    // sky / sea backdrop
    ctx.fillStyle = '#1d3b57'; ctx.fillRect(0, 0, W, H);

    const ox = -this.cam.x, oy = -this.cam.y;
    const hs = this.heroScreen();
    // draw tiles back-to-front
    for (let s = 0; s < COLS + ROWS; s++) {
      for (let gx = 0; gx < COLS; gx++) {
        const gy = s - gx;
        if (gy < 0 || gy >= ROWS) continue;
        const tt = tileType(gx, gy);
        const p = this.iso(gx, gy);
        const sx = p.x + ox, sy = p.y + oy;
        if (sx < -TILE_W || sx > W + TILE_W || sy < -TILE_H || sy > H + 120) continue;
        const col = TILE_COLOR[tt] || TILE_COLOR.grass;
        // decor sits on a ground-tinted diamond rather than its own colour
        const GROUND_BASE = {
          castle: 'plains', town: 'plains', dungeon: 'badlands', queencourt: 'plains',
          forest: 'grass', woods: 'grass', mountain: 'grass', peaks: 'grass',
          cave: 'badlands', cliff: 'plains',
        };
        const bcol = TILE_COLOR[GROUND_BASE[tt] || tt] || col;
        this._diamond(ctx, sx, sy, bcol[0], bcol[1]);

        // decor sprite on top
        const decoName = TILE_DECOR[tt];
        if (decoName) {
          const img = Assets.img(decoName);
          if (img) {
            const DECO_SCALE = {
              castle: 0.95, town: 0.8, dungeon: 0.7, queencourt: 0.62,
              mountain: 0.9, peaks: 0.95, forest: 0.7, woods: 0.7,
              cave: 0.8, cliff: 0.85,
            };
            const scale = DECO_SCALE[tt] || 0.7;
            const dw = img.width * scale, dh = img.height * scale;
            ctx.drawImage(img, sx - dw / 2, sy + TILE_H / 2 - dh, dw, dh);
          }
        }

        // draw hero when his tile is reached in paint order
        if (gx === Math.round(this.heroGX()) && gy === Math.round(this.heroGY())) {
          this._drawHero(ctx, hs.x + ox, hs.y + oy);
        }
      }
    }
  }

  heroGX() { const h = this.hero; return this.move ? this.move.fx + this.move.dgx * Math.min(1, this.move.t/this.move.dur) : h.gx; }
  heroGY() { const h = this.hero; return this.move ? this.move.fy + this.move.dgy * Math.min(1, this.move.t/this.move.dur) : h.gy; }

  _drawHero(ctx, sx, sy) {
    const img = Assets.img('hero');
    if (!img) return;
    const scale = 0.62;
    const dw = img.width * scale, dh = img.height * scale;
    const bobY = this.move ? Math.abs(Math.sin(this.bob * 1.6)) * -4 : 0;
    // shadow
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.28)';
    ctx.beginPath();
    ctx.ellipse(sx, sy + 4, 16, 7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    // flip for left/right facing
    const flip = h_facing_flip(this.hero.facing);
    ctx.save();
    if (flip) {
      ctx.translate(sx, 0); ctx.scale(-1, 1);
      ctx.drawImage(img, -dw / 2, sy - dh + bobY, dw, dh);
    } else {
      ctx.drawImage(img, sx - dw / 2, sy - dh + bobY, dw, dh);
    }
    ctx.restore();
  }
}

function h_facing_flip(f) { return f === 'left'; }
