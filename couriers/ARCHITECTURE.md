# Courier Hub — Architecture

The courier system is a **hub** over the Ocean OS daemon: narrow, single-purpose
courier agents that get invoked by command, do one job, and report back. Slack is
both the **control plane** (slash commands in) and a **delivery plane** (results
out, over the shared Slack route).

```
  Slack  ──/command──▶  intake adapter  ──▶  hub router  ──┬─▶  deterministic: run harness
 (operator)            (HTTPS, signed)    (this layer)     │
      ▲                                                     └─▶  agentic: POST /v1/prompt
      └────────────── results (chat.postMessage) ◀──────────────  to ocean-daemon (cwd=courier dir)
```

## Layers

| Layer | What | Where | Status |
|---|---|---|---|
| **Intake** | Slack slash-command front door: verify signature, 3-sec ack, async reply | _(separate, outward-facing — not built)_ | planned |
| **Router** | `slash → courier` table from manifests; dispatch deterministic vs agentic | [`hub/router.py`](hub/router.py) | ✅ built |
| **Couriers** | single-purpose agents; each a manifest + protocol + harness | `<courier>/` | file-courier ✅ |
| **Route** | shared transport the couriers ship over | [`transport/slack.py`](transport/slack.py) | ✅ built |
| **Daemon** | always-on Ocean runtime; spawns agentic couriers | `ocean-daemon` (`:4780`) | ✅ exists |

## How a courier is spawned (grounded in ocean-os)

The daemon already supports everything the agentic path needs — no new runtime
work:

- `POST /v1/prompt` accepts a `PromptRequest` with a **`cwd`**
  (`ocean-core/src/lib.rs:77`); the daemon resolves the workspace from it
  (`ocean-daemon/src/main.rs:597`).
- The agent then loads `AGENTS.md` / `CLAUDE.md` from that dir and its ancestors
  as its instructions (`ocean-agent/src/lib.rs:1229`, `load_project_prompt`).
- Tool calls (incl. the courier's `bash`-driven harness) run under the daemon's
  permission gate (`/v1/permissions`), and actions stream on `/v1/agent/events`.

So **spawning a courier = POST a scoped prompt**; the daemon does the rest.

## Deterministic vs agentic

Declared per courier in its `courier.toml`:

- **deterministic** — the router execs the harness directly (no LLM). For pure
  mechanical jobs like `file-courier /ship`. Fast, cheap, bulletproof.
- **agentic** — the router POSTs a scoped prompt; a daemon agent applies judgment
  (e.g. a Slingshot-style discover → rank → format → deliver), driving its harness.

## Manifest schema (`<courier>/courier.toml`)

```toml
name = "file-courier"
description = "…"
mode = "deterministic"        # or "agentic"
entry = "bin/courier"         # deterministic: harness to exec

[[commands]]
slash = "/ship"
subcommand = "send"           # deterministic: harness subcommand
summary = "…"
usage = "/ship --channel <id>"
# agentic variant uses `prompt = "…"` instead of `subcommand`.
```

The router (`hub/router.py`) discovers all manifests, so adding a courier =
drop a folder with a `courier.toml`; no router edits.

## Secrets

Tokens follow Ocean's own convention (`OCEAN_<X>_…` first, bare fallback, then a
file) — see `ocean-providers` `credential_env_names`. The Slack route uses
`OCEAN_SLACK_BOT_TOKEN` → `SLACK_BOT_TOKEN` → `~/.slack_token`. Nothing hardcoded.

## Not yet built (deliberately)

- **Slack intake adapter** — needs a Slack app, signing secret, and public
  ingress (reuse the existing `cloudflared` tunnels). Outward-facing; set up
  deliberately, not spun up unannounced.
- **Forward-compat with the planned ocean-os plugin runtime** (`ROADMAP.md`:
  *Subprocess plugins*, *Skill/prompt packs*) — manifests are designed to map
  onto it when it lands.
