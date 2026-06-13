// music.js — procedural "fugue" engine in the spirit of Maier's Atalanta Fugiens.
//
// Every Atalanta Fugiens emblem carries a three-voice canon: a fixed cantus
// firmus ("the golden apple") and two voices in chase — Atalanta (the fuga, the
// fleeing voice) and Hippomenes (the comes, entering a beat later in imitation).
// We reproduce that FORM: each theme is one melody played as an octave canon
// (lead + delayed comes) over a slow cantus firmus. Themes are grouped into
// per-area playlists and cycle every couple of loops.
//
// No audio files: everything is synthesised with WebAudio oscillators, sharing
// the game's AudioContext (passed in via getCtx()).

const LOOKAHEAD = 0.12;   // schedule this far ahead (s)
const TICK = 25;          // scheduler interval (ms)

// theme: { bpm, wave, delay (beats the comes lags), mel:[[midi,beats]], cf:[[midi,beats]] }
// midi 0 = rest. The comes voice replays `mel` an octave down, `delay` beats late.
const THEMES = {
  // --- title / court ---
  hymn: { bpm: 96, wave: 'triangle', delay: 2, vol: 0.07,
    mel: [[67,1],[64,1],[65,1],[67,2],[72,1],[71,1],[67,2],[69,1],[67,1],[65,1],[64,2],[60,2]],
    cf:  [[48,4],[43,4],[53,4],[48,4]] },

  // --- overworld (pastoral, cycles through three) ---
  past_a: { bpm: 116, wave: 'triangle', delay: 2, vol: 0.06,
    mel: [[67,1],[69,1],[71,1],[67,1],[72,2],[71,1],[69,1],[67,2],[62,1],[64,1],[65,2]],
    cf:  [[43,4],[50,4],[48,4],[43,4]] },
  past_b: { bpm: 124, wave: 'triangle', delay: 1.5, vol: 0.06,
    mel: [[62,1],[65,1],[67,1],[69,1],[67,1],[65,1],[64,2],[62,1],[60,1],[62,2]],
    cf:  [[50,4],[45,4],[48,4],[50,4]] },
  past_c: { bpm: 108, wave: 'triangle', delay: 2, vol: 0.06,
    mel: [[65,1],[67,1],[69,2],[71,1],[69,1],[67,2],[65,1],[64,1],[65,2],[60,2]],
    cf:  [[41,4],[48,4],[43,4],[41,4]] },

  // --- Nigredo (dark, slow, low) ---
  nig_a: { bpm: 80, wave: 'sine', delay: 3, vol: 0.07,
    mel: [[57,2],[60,1],[59,1],[57,2],[55,2],[57,1],[58,1],[57,3]],
    cf:  [[33,4],[40,4],[34,4],[33,4]] },
  nig_b: { bpm: 76, wave: 'sine', delay: 2, vol: 0.07,
    mel: [[62,2],[63,1],[62,1],[60,2],[58,2],[60,1],[62,1],[58,3]],
    cf:  [[38,4],[34,4],[36,4],[38,4]] },

  // --- Albedo (clear, bright) ---
  alb_a: { bpm: 116, wave: 'triangle', delay: 1.5, vol: 0.06,
    mel: [[70,1],[72,1],[74,1],[72,1],[70,2],[69,1],[70,1],[72,2],[67,2]],
    cf:  [[46,4],[53,4],[51,4],[46,4]] },
  alb_b: { bpm: 122, wave: 'triangle', delay: 2, vol: 0.06,
    mel: [[65,1],[69,1],[72,1],[69,1],[71,1],[69,1],[67,2],[65,2]],
    cf:  [[41,4],[48,4],[43,4],[41,4]] },

  // --- Citrinitas (warm, golden) ---
  cit_a: { bpm: 120, wave: 'triangle', delay: 2, vol: 0.06,
    mel: [[67,1],[71,1],[72,1],[74,2],[72,1],[71,1],[69,1],[67,2],[71,2]],
    cf:  [[43,4],[50,4],[48,4],[43,4]] },
  cit_b: { bpm: 126, wave: 'triangle', delay: 1.5, vol: 0.06,
    mel: [[72,1],[74,1],[76,1],[74,1],[72,1],[71,1],[72,2],[67,2]],
    cf:  [[48,4],[55,4],[53,4],[48,4]] },

  // --- Rubedo (intense, driving minor) ---
  rub_a: { bpm: 132, wave: 'sawtooth', delay: 1, vol: 0.05,
    mel: [[62,1],[65,1],[69,1],[65,1],[67,1],[64,1],[62,2],[61,1],[62,1]],
    cf:  [[38,2],[36,2],[33,2],[38,2]] },
  rub_b: { bpm: 140, wave: 'sawtooth', delay: 1, vol: 0.05,
    mel: [[69,1],[72,1],[71,1],[69,1],[67,1],[65,1],[64,1],[69,1]],
    cf:  [[45,2],[41,2],[43,2],[45,2]] },

  // --- battle ---
  bat_a: { bpm: 152, wave: 'square', delay: 1, vol: 0.045,
    mel: [[64,1],[64,0.5],[67,0.5],[64,1],[62,1],[60,1],[62,1],[64,2]],
    cf:  [[40,2],[40,2],[38,2],[36,2]] },
  bat_b: { bpm: 160, wave: 'square', delay: 1, vol: 0.045,
    mel: [[69,0.5],[71,0.5],[72,1],[69,1],[67,1],[65,1],[64,1],[69,1]],
    cf:  [[45,2],[43,2],[41,2],[45,2]] },

  // --- stingers ---
  triumph: { bpm: 120, wave: 'triangle', delay: 1, vol: 0.07,
    mel: [[60,1],[64,1],[67,1],[72,2],[71,1],[72,3]],
    cf:  [[48,4],[55,4]] },
  dirge: { bpm: 60, wave: 'sine', delay: 0, vol: 0.07,
    mel: [[57,3],[56,1],[55,4],[53,4]],
    cf:  [[33,4],[31,4]] },
};

const PLAYLISTS = {
  title:      ['hymn'],
  overworld:  ['past_a', 'past_b', 'past_c'],
  battle:     ['bat_a', 'bat_b'],
  victory:    ['triumph'],
  gameover:   ['dirge'],
  nigredo:    ['nig_a', 'nig_b'],
  albedo:     ['alb_a', 'alb_b'],
  citrinitas: ['cit_a', 'cit_b'],
  rubedo:     ['rub_a', 'rub_b'],
};

function midiToFreq(m) { return 440 * Math.pow(2, (m - 69) / 12); }

export class Music {
  constructor(getCtx) {
    this.getCtx = getCtx;
    this.area = null;
    this.playlist = [];
    this.pIdx = 0;
    this.loops = 0;
    this.loopsPerTheme = 2;
    this.muted = false;
    this.timer = null;
    this.master = null;
    this.voices = [];     // {seq, i, next, shift, gain, wave}
    this.beat = 0.5;
    this.themeVol = 0.06;
  }

  start() { if (!this.timer) this.timer = setInterval(() => this._tick(), TICK); }
  stop() { if (this.timer) { clearInterval(this.timer); this.timer = null; } }
  toggleMute() { this.muted = !this.muted; if (this.master) this.master.gain.value = this.muted ? 0 : 1; return this.muted; }

  setArea(key) {
    if (key === this.area) return;
    this.area = key;
    this.playlist = PLAYLISTS[key] || [];
    this.pIdx = 0; this.loops = 0;
    this._load(this.playlist[0]);
  }

  _ensureMaster(ctx) {
    if (this.master && this.master.context === ctx) return;
    this.master = ctx.createGain();
    this.master.gain.value = this.muted ? 0 : 1;
    this.master.connect(ctx.destination);
  }

  _load(themeId) {
    const ctx = this.getCtx && this.getCtx();
    const t = THEMES[themeId];
    if (!t) { this.voices = []; return; }
    this.beat = 60 / t.bpm;
    this.themeVol = t.vol || 0.06;
    this.wave = t.wave;
    const start = ctx ? ctx.currentTime + 0.08 : 0;
    // three voices: Atalanta (lead), Hippomenes (comes, delayed octave-down),
    // and the cantus firmus ("the apple").
    this.voices = [
      { seq: t.mel, i: 0, next: start, shift: 0, gain: this.themeVol, wave: t.wave, isLead: true },
      { seq: t.mel, i: 0, next: start + t.delay * this.beat, shift: -12, gain: this.themeVol * 0.6, wave: t.wave },
      { seq: t.cf, i: 0, next: start, shift: 0, gain: this.themeVol * 0.5, wave: 'sine' },
    ];
  }

  _silence() { this.voices = []; }

  _tick() {
    if (this.muted) return;
    const ctx = this.getCtx && this.getCtx();
    if (!ctx || ctx.state !== 'running') return;
    this._ensureMaster(ctx);
    if (!this.voices.length && this.playlist.length) this._load(this.playlist[this.pIdx]);
    const horizon = ctx.currentTime + LOOKAHEAD;
    for (const v of this.voices) {
      while (v.next < horizon) {
        const [midi, beats] = v.seq[v.i];
        const dur = beats * this.beat;
        if (midi > 0) this._note(ctx, midiToFreq(midi + v.shift), v.next, dur, v.gain, v.wave);
        v.i++;
        if (v.i >= v.seq.length) {
          v.i = 0;
          if (v.isLead) {            // a full pass of the fuga = one loop
            this.loops++;
            if (this.loops >= this.loopsPerTheme && this.playlist.length > 1) {
              this.loops = 0;
              this.pIdx = (this.pIdx + 1) % this.playlist.length;
              this._load(this.playlist[this.pIdx]);
              return;                // voices replaced; resume next tick
            }
          }
        }
        v.next += dur;
      }
    }
  }

  _note(ctx, freq, t, dur, vol, wave) {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = wave; o.frequency.value = freq;
    o.connect(g); g.connect(this.master);
    const a = 0.02, rel = Math.min(0.18, dur * 0.4);
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(vol, t + a);
    g.gain.setValueAtTime(vol, t + Math.max(a, dur - rel));
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.start(t); o.stop(t + dur + 0.02);
  }
}
