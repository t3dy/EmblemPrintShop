// ui.js — canvas drawing helpers: Dragon-Warrior style windows, parchment cards,
// menus, and a typewriter message box.

export const COLORS = {
  windowBg: '#0b0b27',
  windowEdge: '#ffffff',
  windowEdge2: '#5a6bd8',
  text: '#f6f0d8',
  textDim: '#b9b39a',
  hi: '#ffe08a',
  parchment: '#e7d4a8',
  parchmentDk: '#c8ad79',
  ink: '#2a2118',
  hpGreen: '#5fd16b',
  hpRed: '#e0584b',
  mpBlue: '#6aa8ff',
};

// classic DW double-border window
export function window9(ctx, x, y, w, h, bg = COLORS.windowBg) {
  ctx.fillStyle = bg;
  ctx.fillRect(x, y, w, h);
  ctx.lineWidth = 3;
  ctx.strokeStyle = COLORS.windowEdge;
  ctx.strokeRect(x + 2.5, y + 2.5, w - 5, h - 5);
  ctx.lineWidth = 1;
  ctx.strokeStyle = COLORS.windowEdge2;
  ctx.strokeRect(x + 5.5, y + 5.5, w - 11, h - 11);
}

// aged parchment card (for the bestiary monster portrait)
export function parchmentCard(ctx, x, y, w, h) {
  const g = ctx.createLinearGradient(x, y, x, y + h);
  g.addColorStop(0, '#efe0bb');
  g.addColorStop(0.5, COLORS.parchment);
  g.addColorStop(1, COLORS.parchmentDk);
  ctx.fillStyle = g;
  ctx.fillRect(x, y, w, h);
  // vignette
  const v = ctx.createRadialGradient(x + w/2, y + h/2, h*0.2, x + w/2, y + h/2, h*0.75);
  v.addColorStop(0, 'rgba(0,0,0,0)');
  v.addColorStop(1, 'rgba(60,40,15,0.35)');
  ctx.fillStyle = v;
  ctx.fillRect(x, y, w, h);
  // double frame
  ctx.lineWidth = 4; ctx.strokeStyle = '#5b4226';
  ctx.strokeRect(x + 3, y + 3, w - 6, h - 6);
  ctx.lineWidth = 1; ctx.strokeStyle = '#8a6a3c';
  ctx.strokeRect(x + 8, y + 8, w - 16, h - 16);
}

export function text(ctx, str, x, y, opts = {}) {
  ctx.font = (opts.size || 16) + 'px "Courier New", monospace';
  ctx.textBaseline = 'top';
  ctx.textAlign = opts.align || 'left';
  if (opts.shadow !== false) {
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillText(str, x + 2, y + 2);
  }
  ctx.fillStyle = opts.color || COLORS.text;
  ctx.fillText(str, x, y);
}

// menu of commands, returns nothing; caller tracks selected index
export function menu(ctx, items, x, y, selected, opts = {}) {
  const lh = opts.lh || 26;
  const colW = opts.colW || 0; // if >0, two-column layout
  items.forEach((it, i) => {
    let ix = x, iy = y + i * lh;
    if (colW) { ix = x + (i % 2) * colW; iy = y + Math.floor(i / 2) * lh; }
    const sel = i === selected;
    if (sel) text(ctx, '▶', ix - 20, iy, { color: COLORS.hi });
    text(ctx, it, ix, iy, { color: sel ? COLORS.hi : COLORS.text });
  });
}

// a stat bar
export function bar(ctx, x, y, w, h, frac, color) {
  ctx.fillStyle = '#000'; ctx.fillRect(x - 1, y - 1, w + 2, h + 2);
  ctx.fillStyle = '#333'; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = color; ctx.fillRect(x, y, Math.max(0, Math.min(1, frac)) * w, h);
}

// Typewriter message box state machine
export class MessageBox {
  constructor() { this.queue = []; this.shown = ''; this.full = ''; this.t = 0; this.done = true; this.onEmpty = null; }
  push(...lines) { this.queue.push(...lines); if (this.done) this._next(); }
  _next() {
    if (this.queue.length === 0) { this.done = true; this.full = this.shown = ''; if (this.onEmpty) { const f = this.onEmpty; this.onEmpty = null; f(); } return; }
    this.full = this.queue.shift(); this.shown = ''; this.t = 0; this.done = false;
  }
  // advance: called on confirm key. if still typing -> reveal all; else next line.
  advance() {
    if (!this.done && this.shown.length < this.full.length) { this.shown = this.full; return false; }
    this._next();
    return this.done;
  }
  update(dt) {
    if (this.done) return;
    if (this.shown.length < this.full.length) {
      this.t += dt;
      const cps = 45; // chars per second
      const n = Math.floor(this.t * cps);
      this.shown = this.full.slice(0, Math.min(this.full.length, n));
    }
  }
  get typing() { return !this.done && this.shown.length < this.full.length; }
  get empty() { return this.done && this.queue.length === 0; }
  render(ctx, x, y, w, h) {
    window9(ctx, x, y, w, h);
    const words = this.shown.split('\n');
    words.forEach((ln, i) => text(ctx, ln, x + 18, y + 16 + i * 22, { size: 16 }));
    if (this.done === false && !this.typing) {
      text(ctx, '▼', x + w - 26, y + h - 26, { color: COLORS.hi });
    }
  }
}
