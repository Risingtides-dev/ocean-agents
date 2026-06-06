#!/usr/bin/env python3
"""
Slack inbound bridge — Socket Mode listener SCAFFOLD (design spec §3, §4, §9).

The NEW inbound plumbing for the assistants class. Couriers/transport already
handles OUTBOUND Slack I/O; nothing in the repo receives Slack *events* today.
This is the front door: open an `xapp-` Socket Mode WebSocket, receive Slack
events (app_mention / message.im), dedupe Slack's retries, resolve thread/DM
context, and dispatch each turn to the Ocean daemon scoped to the agent's dir.

STATUS: SCAFFOLD. The dedupe + context-resolution + daemon-dispatch logic is real
and unit-testable (pure stdlib, no token). The live WebSocket open/receive loop is
DEFERRED to build-order step 3 (spec §11) — `run()` is intentionally a stub that
documents the contract rather than opening a live socket here. Wiring the real
socket needs the `slack_sdk` Socket Mode client (or a raw WS over the apps.connections
.open url) + the app token, and is gated on a real Slack app existing (spec §12).

Pure stdlib. tomllib (Python 3.11+) for manifest read.

Usage (scaffold):
  socket_listener.py resolve <manifest.toml>   # show the turn-scoping contract (JSON)
  socket_listener.py run                        # NOT LIVE — prints the deferred contract
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    print(json.dumps({"ok": False, "error": "needs Python 3.11+ (tomllib)"}), file=sys.stderr)
    sys.exit(1)

ASSISTANTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ASSISTANTS_ROOT.parent
DAEMON_URL = os.environ.get("OCEAN_DAEMON_URL", "http://127.0.0.1:4780")


class EventDeduper:
    """Slack re-delivers events when the app doesn't ack in time (spec §9). Drop a
    repeat by Slack event id so a turn never double-fires. Bounded memory: keep the
    last N ids. Pure, testable, no I/O."""

    def __init__(self, capacity: int = 4096):
        self.capacity = capacity
        self._seen: dict[str, None] = {}

    def is_duplicate(self, event_id: str) -> bool:
        if not event_id:
            return False
        if event_id in self._seen:
            return True
        self._seen[event_id] = None
        if len(self._seen) > self.capacity:
            # FIFO evict oldest (dict preserves insertion order in 3.7+).
            oldest = next(iter(self._seen))
            del self._seen[oldest]
        return False


def session_key(agent: str, channel_id: str, thread_or_dm: str) -> str:
    """Bind a Slack session to (agent, channel/DM, thread) so threads stay isolated
    and resumable (spec §5). Mirrors content-agent.toml `session_key`."""
    return f"slack:{agent}:{channel_id}:{thread_or_dm}"


def resolve_context(event: dict) -> dict:
    """Turn a raw Slack event into the daemon-turn context. Pure: no I/O.

    Handles app_mention (channel/thread) and message.im (DM). The reply target is
    the thread_ts when present (keep threaded replies in-thread, spec §comms),
    else the message ts (start a thread), else the DM channel.
    """
    channel = event.get("channel", "")
    user = event.get("user", "")
    text = event.get("text", "")
    # In-thread reply target: existing thread_ts wins, else this message's ts.
    thread_ts = event.get("thread_ts") or event.get("ts") or ""
    is_dm = event.get("channel_type") == "im" or str(channel).startswith("D")
    thread_or_dm = "dm" if is_dm else thread_ts
    return {
        "channel": channel,
        "user": user,
        "prompt": text,
        "thread_ts": thread_ts,
        "is_dm": is_dm,
        "thread_or_dm": thread_or_dm,
    }


def build_turn(manifest_path: Path, event: dict) -> dict:
    """Compose the POST /v1/prompt body for a Slack event, scoped to the agent dir.

    The daemon maps client_type=surface-slack → [SLACK] + the Slack surface profile
    (ocean-os surface_dir), and load_project_prompt ancestor-walks the scoped cwd to
    pick up the agent's CLAUDE.md/AGENTS.md identity (spec §3 key seam).
    """
    with manifest_path.open("rb") as fh:
        m = tomllib.load(fh)
    surface = m.get("surface", {}).get("SLACK", {})
    agent = m.get("name", manifest_path.parent.name)
    ctx = resolve_context(event)
    cwd = surface.get("cwd") or str(manifest_path.parent.relative_to(REPO_ROOT))
    return {
        "cwd": str((REPO_ROOT / cwd)),
        "prompt": ctx["prompt"],
        "client_type": surface.get("client_type", "surface-slack"),
        "session_id": session_key(agent, ctx["channel"], ctx["thread_or_dm"]),
        # carried for the reply path (not part of the daemon contract, used by reply.py)
        "_reply": {"channel": ctx["channel"], "thread_ts": ctx["thread_ts"], "is_dm": ctx["is_dm"]},
    }


def dispatch_to_daemon(turn: dict) -> dict:
    """POST the turn to the Ocean daemon. The `_reply` block is stripped — it is
    bridge-side routing, not part of the /v1/prompt contract."""
    body = {k: v for k, v in turn.items() if not k.startswith("_")}
    req = urllib.request.Request(
        f"{DAEMON_URL}/v1/prompt",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def cmd_resolve(args):
    """Show the turn-scoping contract for a manifest against a sample event."""
    if not args:
        _die("usage: socket_listener.py resolve <manifest.toml>")
    manifest = Path(args[0]).resolve()
    if not manifest.exists():
        _die(f"manifest not found: {manifest}")
    sample = {"type": "app_mention", "channel": "C123", "user": "U1",
              "text": "make me a clip", "ts": "1700000000.000100", "event_id": "Ev1"}
    turn = build_turn(manifest, sample)
    print(json.dumps({"ok": True, "sample_event": sample, "turn": turn}, indent=2))


def run():
    """DEFERRED (spec §11 step 3): open the live Socket Mode WebSocket and pump
    events through dedupe → resolve_context → build_turn → dispatch_to_daemon →
    reply.deliver. Not opened here — needs a real Slack app + app token (spec §12)
    and reconnect/backoff around a `slack_sdk` SocketModeClient (or raw WS via
    apps.connections.open). This scaffold provides every pure piece that loop needs."""
    print(json.dumps({
        "ok": False,
        "status": "scaffold",
        "deferred": "live Socket Mode loop — build-order step 3 (spec §11)",
        "ready": ["EventDeduper", "resolve_context", "build_turn",
                  "session_key", "dispatch_to_daemon", "reply.deliver"],
        "needs": ["SLACK_APP_TOKEN (xapp-)", "a real Slack app w/ Socket Mode",
                  "reconnect/backoff around the WS receive loop"],
    }, indent=2))


def _die(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}), file=sys.stderr)
    sys.exit(code)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "resolve":
        cmd_resolve(rest)
    elif cmd == "run":
        run()
    else:
        _die(f"unknown command '{cmd}' (try: resolve | run)")


if __name__ == "__main__":
    main()
