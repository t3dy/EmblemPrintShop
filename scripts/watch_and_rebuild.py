#!/usr/bin/env python3
"""
Watch for extraction job completion and automatically rebuild catalogs.

Monitors assets/extracted_all/ for new extractions and triggers catalog rebuild
when the job appears to be complete (no new files for N seconds).

Usage:
    python scripts/watch_and_rebuild.py [--interval=5] [--idle-wait=120]

Options:
    --interval      Check every N seconds (default: 5)
    --idle-wait     Rebuild when idle for N seconds (default: 120)
    --dry-run       Print what would be done, don't rebuild
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
EXTRACTED = ROOT / "assets" / "extracted_all"


def count_extractions() -> int:
    """Count total extraction directories."""
    return len(list(EXTRACTED.glob("*/individual/*.json")))


def get_latest_mtime() -> float:
    """Get the most recent file modification time in extracted_all/."""
    times = []
    for f in EXTRACTED.glob("*/individual/*"):
        try:
            times.append(f.stat().st_mtime)
        except OSError:
            pass
    return max(times) if times else 0


def rebuild_catalogs() -> bool:
    """Run the catalog rebuild scripts."""
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Rebuilding catalogs...")

        # Try build_object_catalog if it exists
        try:
            result = subprocess.run(
                [sys.executable, "-m", "scripts.build_object_catalog"],
                cwd=ROOT, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                print(f"build_object_catalog stderr: {result.stderr[:500]}")
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pass  # Optional script, skip if missing

        # build_catalog.py (required)
        result = subprocess.run(
            [sys.executable, "scripts/build_catalog.py"],
            cwd=ROOT, capture_output=True, text=True, timeout=300
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr[:500]}")
            return False

        # build_emblem_catalog.py
        result = subprocess.run(
            [sys.executable, "scripts/build_emblem_catalog.py"],
            cwd=ROOT, capture_output=True, text=True, timeout=300
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr[:500]}")
            return False

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Catalogs rebuilt successfully!")
        return True
    except Exception as e:
        print(f"Rebuild failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=5, help="Check interval (seconds)")
    parser.add_argument("--idle-wait", type=int, default=120, help="Idle wait before rebuild (seconds)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually rebuild")
    args = parser.parse_args()

    if not EXTRACTED.exists():
        print(f"ERROR: {EXTRACTED} not found")
        return 1

    print(f"Watching {EXTRACTED} for extraction completion...")
    print(f"Check interval: {args.interval}s, rebuild on idle for {args.idle_wait}s")

    last_mtime = get_latest_mtime()
    idle_since = None
    last_count = count_extractions()

    while True:
        time.sleep(args.interval)

        current_mtime = get_latest_mtime()
        current_count = count_extractions()

        # Check if there's been activity
        if current_mtime > last_mtime:
            # Activity detected
            idle_since = None
            last_mtime = current_mtime
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Activity: {current_count} extractions", end="\r")
        else:
            # No activity
            if idle_since is None:
                idle_since = time.time()

            idle_seconds = time.time() - idle_since
            if idle_seconds >= args.idle_wait:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Idle for {idle_seconds:.0f}s → starting rebuild")
                if not args.dry_run:
                    success = rebuild_catalogs()
                    if success:
                        # Reset and continue watching
                        idle_since = None
                        last_count = current_count
                        last_mtime = current_mtime
                    else:
                        print("Rebuild failed; continuing to watch...")
                else:
                    print("[DRY RUN] Would rebuild catalogs now")
                    break


if __name__ == "__main__":
    sys.exit(main() or 0)
