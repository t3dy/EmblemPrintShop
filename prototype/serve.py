"""
Local HTTP server for the Emblem Print Shop.

Serves the prototype directory with the project root as the file root,
so that relative paths like ../assets/extracted/... resolve correctly.

Also handles POST /api/save-edit  — saves edited PNG and edit log JSON.
         POST /api/save-review   — saves review decisions JSON.

Usage:
    python prototype/serve.py
    # Then open: http://localhost:8765/prototype/gallery.html
"""
import http.server
import json
import os
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
        print(f"  (POST) /api/save-edit   — save edited extraction PNG + log")
        print(f"  (POST) /api/save-review — persist review decisions to disk")
        print(f"Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
