"""
Local HTTP server for the Emblem Print Shop.

Serves the prototype directory with the project root as the file root,
so that relative paths like ../assets/extracted/... resolve correctly.

Also handles POST /api/save-edit            — saves edited PNG and edit log JSON.
         POST /api/save-review          — saves review decisions JSON.
         POST /api/save-new-extraction  — manual lasso/wand cutout -> a new
                                           element written straight into
                                           assets/extracted_all/, same shape
                                           as the automated pipeline's output.
         POST /api/rebuild-catalog      — reruns build_catalog.py so a new
                                           manual extraction shows up in the
                                           gallery immediately.

Usage:
    python prototype/serve.py
    # Then open: http://localhost:8765/prototype/gallery.html
"""
import http.server
import json
import os
import re
import subprocess
import sys
import base64
from pathlib import Path
from datetime import datetime, timezone

PORT = 8765
ROOT = str(Path(__file__).parent.parent)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        if args[1] not in ('200', '304'):
            super().log_message(fmt, *args)

    # ── POST handler ──────────────────────────────────────────────────────────
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            self._respond(400, {'error': 'bad JSON'})
            return

        if self.path == '/api/save-edit':
            self._handle_save_edit(data)
        elif self.path == '/api/save-review':
            self._handle_save_review(data)
        elif self.path == '/api/save-new-extraction':
            self._handle_save_new_extraction(data)
        elif self.path == '/api/rebuild-catalog':
            self._handle_rebuild_catalog(data)
        else:
            self._respond(404, {'error': 'unknown endpoint'})

    def _handle_save_edit(self, data):
        """
        Save an edited extraction PNG alongside the original, and append to its
        edit log JSON.

        Expected body:
          original_path  — relative path from project root, e.g.
                           "assets/extracted/emblem-16_ouroboros_transparent.png"
          edited_data    — data-URL: "data:image/png;base64,iVBORw..."
          edit_events    — list of edit event dicts
          quality_note   — optional free-text note
        """
        original_rel = data.get('original_path', '')
        if not original_rel:
            self._respond(400, {'error': 'missing original_path'})
            return

        original_abs = Path(ROOT) / original_rel
        if not original_abs.exists():
            self._respond(404, {'error': f'original not found: {original_rel}'})
            return

        # Decode PNG
        data_url = data.get('edited_data', '')
        if not data_url.startswith('data:image/png;base64,'):
            self._respond(400, {'error': 'edited_data must be data:image/png;base64,...'})
            return
        png_bytes = base64.b64decode(data_url.split(',', 1)[1])

        # Save edited PNG: original_transparent.png → original_transparent_edited.png
        edited_abs = original_abs.with_name(
            original_abs.stem.replace('_transparent', '') + '_edited.png'
        )
        edited_abs.write_bytes(png_bytes)

        # Load or create the edit log
        log_abs = original_abs.with_name(
            original_abs.stem.replace('_transparent', '') + '_edits.json'
        )
        if log_abs.exists():
            with open(log_abs, encoding='utf-8') as f:
                log = json.load(f)
        else:
            log = {
                'image_id': original_abs.stem,
                'original_png': original_rel,
                'edited_png': str(edited_abs.relative_to(ROOT)).replace('\\', '/'),
                'edits': [],
            }

        # Append new events
        ts = datetime.now(timezone.utc).isoformat()
        new_events = data.get('edit_events', [])
        quality_note = data.get('quality_note', '')
        if new_events or quality_note:
            log['edits'].append({
                'saved_at': ts,
                'quality_note': quality_note,
                'events': new_events,
            })
        log['last_edited'] = ts
        log['total_sessions'] = len(log['edits'])

        with open(log_abs, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)

        self._respond(200, {
            'saved': str(edited_abs.relative_to(ROOT)).replace('\\', '/'),
            'log': str(log_abs.relative_to(ROOT)).replace('\\', '/'),
        })

    def _handle_save_review(self, data):
        """
        Save review decisions to prototype/review_decisions.json.

        The client sends its complete in-memory decisions map on every save
        (review.html keeps REVIEWS as the single source of truth and this
        mirrors it verbatim), so this replaces the file rather than merging —
        a merge-only write can never represent "this key was reset to
        pending," since a removed key looks identical to an absent one.
        """
        decisions = data.get('decisions', {})
        dest = Path(ROOT) / 'prototype' / 'review_decisions.json'
        with open(dest, 'w', encoding='utf-8') as f:
            json.dump(decisions, f, indent=2)
        self._respond(200, {'saved': len(decisions)})

    def _handle_save_new_extraction(self, data):
        """
        Turn a manual lasso/wand selection made directly on a source plate
        into a new extracted element, written in exactly the shape the
        automated pipeline (extract_all_objects.py) writes so build_catalog.py
        picks it up with no special-casing -- it just globs *_meta.json in
        each emblem's individual/ directory.

        Expected body:
          source_image  — relative path to the full source plate (project root)
          emblem_id     — e.g. "emblem-00" (the individual/ subdir to write into)
          label         — human-entered label (required)
          category      — one of the six extraction categories
          mask_data     — data:image/png;base64,... — an RGBA PNG the SAME
                          PIXEL SIZE as source_image, alpha=255 inside the
                          hand-drawn selection and 0 outside. This endpoint
                          composites it against the actual source pixels
                          itself -- it does not trust any RGB the client sent
                          for the selected area, only the alpha mask, so the
                          new cutout's pixels are always genuine plate ink,
                          never a browser's re-encoded copy.
        """
        from PIL import Image
        import io

        source_rel = data.get('source_image', '')
        emblem_id = data.get('emblem_id', '')
        label = (data.get('label') or '').strip()
        category = data.get('category') or 'objects'
        mask_data_url = data.get('mask_data', '')

        if not source_rel or not emblem_id or not label or not mask_data_url.startswith('data:image/png;base64,'):
            self._respond(400, {'error': 'missing source_image, emblem_id, label, or mask_data'})
            return

        source_abs = Path(ROOT) / source_rel
        if not source_abs.exists():
            self._respond(404, {'error': f'source image not found: {source_rel}'})
            return

        source_im = Image.open(source_abs).convert('RGB')
        mask_bytes = base64.b64decode(mask_data_url.split(',', 1)[1])
        mask_im = Image.open(io.BytesIO(mask_bytes)).convert('RGBA')

        if mask_im.size != source_im.size:
            self._respond(400, {
                'error': f'mask_data size {mask_im.size} does not match source_image size {source_im.size}',
            })
            return

        alpha = mask_im.split()[3]
        bbox = alpha.getbbox()
        if bbox is None:
            self._respond(400, {'error': 'selection mask is empty -- nothing was selected'})
            return

        # Composite REAL source pixels (never the client's) with the drawn alpha.
        full_rgba = source_im.convert('RGBA')
        full_rgba.putalpha(alpha)
        cutout = full_rgba.crop(bbox)
        crop_rgb = source_im.crop(bbox)  # opaque reference crop, matches pipeline convention

        indiv_dir = Path(ROOT) / 'assets' / 'extracted_all' / emblem_id / 'individual'
        indiv_dir.mkdir(parents=True, exist_ok=True)

        slug = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')[:40] or 'manual_element'
        stem = f"{slug}_manual"
        n = 2
        while (indiv_dir / f"{stem}_meta.json").exists():
            stem = f"{slug}_manual_{n}"
            n += 1

        transparent_path = indiv_dir / f"{stem}_transparent.png"
        crop_path = indiv_dir / f"{stem}_crop.jpg"
        meta_path = indiv_dir / f"{stem}_meta.json"

        cutout.save(transparent_path)
        crop_rgb.save(crop_path, quality=92)

        x0, y0, x1, y1 = bbox
        meta = {
            'source_image': str(source_abs),
            'transparent_png': str(transparent_path),
            'crop_jpg': str(crop_path),
            'mask_pixel_count': int((alpha.point(lambda a: 255 if a > 127 else 0)).histogram()[255]),
            'tight_bbox': [x0, y0, x1 - x0, y1 - y0],
            'det_bbox': [x0, y0, x1 - x0, y1 - y0],
            'extracted_at': datetime.now(timezone.utc).isoformat(),
            'label': label,
            'category': category,
            'score': None,
            'type': 'individual',
            'extraction_method': 'manual-lasso-wand',
            'human_drawn': True,
        }
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')

        self._respond(200, {
            'saved_stem': stem,
            'transparent_png': str(transparent_path.relative_to(ROOT)).replace('\\', '/'),
            'crop_jpg': str(crop_path.relative_to(ROOT)).replace('\\', '/'),
        })

    def _handle_rebuild_catalog(self, data):
        """Rerun scripts/build_catalog.py so new/edited elements show up in the gallery."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'scripts.build_catalog'],
                cwd=ROOT, capture_output=True, text=True, timeout=180,
            )
        except Exception as exc:
            self._respond(500, {'error': f'rebuild failed to start: {exc}'})
            return
        if result.returncode != 0:
            self._respond(500, {'error': result.stderr[-2000:] or 'build_catalog.py failed'})
            return
        self._respond(200, {'output': result.stdout[-2000:]})

    def _respond(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(payload))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


if __name__ == "__main__":
    os.chdir(ROOT)
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        print(f"Emblem Print Shop")
        print(f"  Gallery:        http://localhost:{PORT}/prototype/gallery.html")
        print(f"  Emblem Catalog: http://localhost:{PORT}/prototype/emblems.html")
        print(f"  Review Queue:   http://localhost:{PORT}/prototype/review.html")
        print(f"  Image Editor:   http://localhost:{PORT}/prototype/editor.html")
        print(f"  (POST) /api/save-edit           — save edited extraction PNG + log")
        print(f"  (POST) /api/save-review         — persist review decisions to disk")
        print(f"  (POST) /api/save-new-extraction — write a manual lasso/wand cutout")
        print(f"  (POST) /api/rebuild-catalog     — rerun build_catalog.py")
        print(f"Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
