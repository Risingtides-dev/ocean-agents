#!/usr/bin/env python3
"""
Slack reply path — daemon output → Slack (design spec §3, §4 bridge/reply.py).

Takes the Ocean daemon's assistant output for a turn and posts it back via the
EXISTING outbound transport (couriers/transport/slack.py) — message in-thread / DM,
or a canvas create/update for rich content. The bridge does NOT re-implement Slack
I/O; the transport owns rate limits, retries, file upload, and canvas ops (spec §3
"Reuse"). This module is the thin adapter from daemon output → transport calls.

STATUS: SCAFFOLD. The routing decision (inline message vs. canvas, thread vs. DM)
and the transport handoff are real; the wiring to the daemon's streamed output
shape is DEFERRED to build-order step 3 (spec §11). `deliver()` documents the
contract and routes to the transport; the canvas-vs-message heuristic is a stub the
agent's SOPs (content-agent/SLACK/sops/) ultimately drive.

Pure stdlib + the repo's transport. No new Slack I/O.
"""
import sys
from pathlib import Path

# Import the EXISTING outbound transport — never re-implement Slack calls (spec §3).
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "couriers" / "transport"))
try:
    from slack import Slack  # type: ignore  # couriers/transport/slack.py
except Exception:  # pragma: no cover - transport optional at scaffold time
    Slack = None  # type: ignore


def should_canvas(output: dict) -> bool:
    """Heuristic stub: render to a canvas when the agent flagged the output as a
    gallery/status board or it's large/structured (house canvas SOP). The real
    decision is made by content-agent's SOPs; this is the bridge-side fallback."""
    if output.get("render") == "canvas":
        return True
    text = output.get("text", "") or ""
    # Big/tabular output → canvas; a short reply stays inline.
    return len(text) > 1500 or text.count("\n") > 25


def deliver(reply_target: dict, output: dict, token: str | None = None) -> dict:
    """Post the daemon's `output` back to Slack at `reply_target`.

    reply_target = {channel, thread_ts, is_dm}  (from socket_listener.build_turn _reply)
    output       = {text, render?, files?, canvas?}  (the daemon's assistant turn)

    DEFERRED wiring: the exact `output` shape comes from the daemon's streamed
    AgentTurnEvent → final text/artifacts (build-order step 3). Here we route to the
    transport: thread/DM message, file upload, or canvas create — the real calls,
    behind a graceful guard so the scaffold imports without a token.
    """
    if Slack is None:
        return {"ok": False, "status": "scaffold",
                "note": "transport not importable here; wire in build-order step 3"}

    channel = reply_target.get("channel", "")
    # In-thread reply keeps threaded convos threaded; DMs post to the DM channel.
    thread_ts = None if reply_target.get("is_dm") else reply_target.get("thread_ts")
    client = Slack(token=token)

    if should_canvas(output):
        # Rich content → canvas + a one-line in-thread pointer (house canvas SOP).
        canvas = output.get("canvas") or {"title": "content-agent", "markdown": output.get("text", "")}
        res = client.create_canvas(title=canvas["title"], markdown=canvas["markdown"], channel=channel)
        client.post_message(channel, text=output.get("pointer", "Posted a canvas 👆"), thread_ts=thread_ts)
        return {"ok": True, "mode": "canvas", "result": res}

    # Plain in-thread / DM message.
    res = client.post_message(channel, text=output.get("text", ""), thread_ts=thread_ts)
    return {"ok": True, "mode": "message", "result": res}


if __name__ == "__main__":
    # Scaffold self-describe: no token needed, no live send.
    import json
    print(json.dumps({
        "ok": False,
        "status": "scaffold",
        "deferred": "wire daemon streamed output → deliver() — build-order step 3 (spec §11)",
        "routes": ["message (thread/DM)", "canvas (create + in-thread pointer)", "file upload (transport)"],
        "reuses": "couriers/transport/slack.py (post_message / upload_file / create_canvas)",
    }, indent=2))
