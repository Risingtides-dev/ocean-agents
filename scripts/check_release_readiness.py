#!/usr/bin/env python3
"""
check_release_readiness.py — launch gate for the ocean-agents public tree.

Verifies the provenance inventory in docs/provenance.json against the actual
tracked files. Fails when:
  - a tracked asset-like file is missing from the inventory
  - a listed file is no longer tracked
  - a byte count or SHA-256 has drifted
  - any record uses a non-accepted status
  - the inventory claims third-party assets not permitted in the public tree

Usage:
  python3 scripts/check_release_readiness.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "docs" / "provenance.json"
ASSET_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".pdf",
    ".html", ".htm",
    ".mp3", ".mp4", ".webm", ".webp", ".bmp",
}
ACCEPTED_STATUSES = {"project_dual_licensed", "protected_brand", "cleared"}

errors = []


def fail(msg):
    print(f"FAIL: {msg}")
    errors.append(msg)


def git_tracked():
    out = subprocess.check_output(["git", "-C", str(REPO), "ls-files"], text=True)
    return [f for f in out.strip().split("\n") if f]


def main():
    if not MANIFEST.exists():
        fail(f"{MANIFEST} not found")
        _report()
        return 1

    doc = json.loads(MANIFEST.read_text())
    assets = doc.get("assets", [])
    tracked = set(git_tracked())

    # Check third_party count
    if doc.get("third_party_assets_in_tree", 0) != 0:
        fail("third_party_assets_in_tree must be 0 for this public repository")

    # Build a set of tracked asset-like files
    tracked_asset_paths = {
        f for f in tracked
        if Path(f).suffix.lower() in ASSET_EXTS
    }
    manifest_paths = {a["path"] for a in assets}

    # Missing from manifest
    for p in sorted(tracked_asset_paths - manifest_paths):
        fail(f"tracked asset not in inventory: {p}")

    # Stale entries
    for p in sorted(manifest_paths - tracked_asset_paths):
        fail(f"inventory lists removed file: {p}")

    # Verify each record
    for a in assets:
        p = REPO / a["path"]
        if not p.exists():
            fail(f"{a['path']}: file missing")
            continue
        data = p.read_bytes()
        if a["bytes"] != len(data):
            fail(f"{a['path']}: byte count drift (manifest={a['bytes']}, actual={len(data)})")
        actual_hash = hashlib.sha256(data).hexdigest()
        if a["sha256"] != actual_hash:
            fail(f"{a['path']}: SHA-256 drift")
        if a["status"] not in ACCEPTED_STATUSES:
            fail(f"{a['path']}: status '{a['status']}' not accepted; pending is a release blocker")

    # Confirm no third-party assets are silently introduced
    third_party = [a for a in assets if a["status"] == "cleared"]
    if third_party and doc.get("third_party_assets_in_tree", 0) != len(third_party):
        fail(f"third_party_assets_in_tree says {doc.get('third_party_assets_in_tree')} but {len(third_party)} cleared records exist")

    _report()
    return 1 if errors else 0


def _report():
    if not errors:
        print(json.dumps({
            "ok": True,
            "trackedAssets": len(json.loads(MANIFEST.read_text()).get("assets", [])),
        }, indent=2))
    else:
        print(f"\n{len(errors)} error(s)")


if __name__ == "__main__":
    sys.exit(main())
