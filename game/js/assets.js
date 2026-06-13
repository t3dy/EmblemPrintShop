// assets.js — load the sprite manifest + images.
export const Assets = {
  manifest: [],
  byName: {},
  images: {},
  async load() {
    const res = await fetch('assets/manifest.json');
    this.manifest = await res.json();
    await Promise.all(this.manifest.map(rec => new Promise((resolve) => {
      const img = new Image();
      img.onload = () => { this.images[rec.name] = img; resolve(); };
      img.onerror = () => { console.warn('missing sprite', rec.file); resolve(); };
      img.src = rec.file;
      this.byName[rec.name] = rec;
    })));
    return this;
  },
  img(name) { return this.images[name]; },
  meta(name) { return this.byName[name]; },
};
