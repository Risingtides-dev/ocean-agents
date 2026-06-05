#!/usr/bin/env python3
"""
Courier hub router — the spine of the courier system.

Discovers every `courier.toml` under couriers/, builds the slash-command →
courier table, and dispatches an invocation:

  • deterministic courier → exec its harness entry directly (no LLM)
  • agentic courier        → POST /v1/prompt to the Ocean daemon, scoped to the
                             courier's dir (the daemon auto-loads its CLAUDE.md)

This is the routing layer of the hub described in ../ARCHITECTURE.md. Slack
slash-command intake (the front door) is a separate, outward-facing layer that
calls into this router; it is intentionally not built here.

Pure stdlib. TOML via tomllib (Python 3.11+).

Usage:
  router.py list                       # show all couriers + commands
  router.py resolve <slash>            # which courier handles a command (JSON)
  router.py run [--dry-run] <slash> [args...]
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    print(json.dumps({"ok": False, "error": "needs Python 3.11+ (tomllib)"}), file=sys.stderr)
    sys.exit(1)

COURIERS_ROOT = Path(__file__).resolve().parents[1]
DAEMON_URL = os.environ.get("OCEAN_DAEMON_URL", "http://127.0.0.1:4780")


def load_registry() -> dict:
    """slash-command -> {courier, dir, mode, entry, command}."""
    table = {}
    for manifest in sorted(COURIERS_ROOT.glob("*/courier.toml")):
        with manifest.open("rb") as fh:
            m = tomllib.load(fh)
        cdir = manifest.parent
        for cmd in m.get("commands", []):
            slash = cmd.get("slash")
            if not slash:
                continue
            table[slash] = {
                "courier": m.get("name", cdir.name),
                "dir": str(cdir),
                "mode": m.get("mode", "deterministic"),
                "entry": m.get("entry", "bin/courier"),
                "command": cmd,
            }
    return table


def cmd_list(_args):
    table = load_registry()
    if not table:
        print("(no courier.toml manifests found under couriers/)")
        return
    width = max(len(s) for s in table)
    for slash in sorted(table):
        e = table[slash]
        c = e["command"]
        print(f"{slash:<{width}}  [{e['mode']:^13}] {e['courier']:<14} {c.get('summary','')}")
        if c.get("usage"):
            print(f"{'':<{width}}  {'':15} {'':14} ↳ {c['usage']}")


def cmd_resolve(args):
    if not args:
        die("usage: router.py resolve <slash>")
    table = load_registry()
    hit = table.get(args[0])
    if not hit:
        die(f"no courier handles '{args[0]}'  (known: {', '.join(sorted(table)) or 'none'})")
    print(json.dumps({"ok": True, **hit}, indent=2))


def cmd_run(args):
    dry = False
    if args and args[0] == "--dry-run":
        dry, args = True, args[1:]
    if not args:
        die("usage: router.py run [--dry-run] <slash> [args...]")
    slash, rest = args[0], args[1:]
    table = load_registry()
    hit = table.get(slash)
    if not hit:
        die(f"no courier handles '{slash}'  (known: {', '.join(sorted(table)) or 'none'})")

    if hit["mode"] == "deterministic":
        entry = str(Path(hit["dir"]) / hit["entry"])
        sub = hit["command"].get("subcommand")
        argv = [entry] + ([sub] if sub else []) + rest
        if dry:
            print(json.dumps({"ok": True, "mode": "deterministic", "exec": argv}, indent=2))
            return
        sys.exit(subprocess.call(argv))

    # agentic: hand off to the daemon, scoped to the courier's dir.
    prompt = hit["command"].get("prompt", "").strip()
    if rest:
        prompt = (prompt + "\n\nOperator args: " + " ".join(rest)).strip()
    payload = {
        "cwd": hit["dir"],
        "prompt": prompt or f"Run {slash} with the given args.",
        "client_type": "surface-slack",
    }
    if dry:
        print(json.dumps({"ok": True, "mode": "agentic",
                          "POST": f"{DAEMON_URL}/v1/prompt", "body": payload}, indent=2))
        return
    req = urllib.request.Request(
        f"{DAEMON_URL}/v1/prompt",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            print(r.read().decode())
    except Exception as e:  # noqa: BLE001
        die(f"daemon POST failed ({DAEMON_URL}): {e}")


def die(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}), file=sys.stderr)
    sys.exit(code)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd, rest = sys.argv[1], sys.argv[2:]
    {"list": cmd_list, "resolve": cmd_resolve, "run": cmd_run}.get(cmd, lambda _a: die(
        f"unknown command '{cmd}' (try: list | resolve | run)"))(rest)


if __name__ == "__main__":
    main()
