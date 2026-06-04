# ocean-agents — agent index

> Loaded automatically by the Ocean runtime: `ocean-agent` walks the working
> directory's ancestors and concatenates every `AGENTS.md` / `CLAUDE.md` it
> finds into the system prompt. This file orients any agent working anywhere in
> this repo. A courier's own `CLAUDE.md` (loaded alongside this) is the detailed
> protocol for that courier.

This repo holds **provider-agnostic agent packages** that run *on top of* the
Ocean runtime. It is intentionally separate from `ocean-os` (which stays pure
Rust). Two families so far: **couriers** (ship payloads outbound over a route)
and **assistants** (brain-in-the-loop specialists that operate on a surface).

## Assistants — surface specialists

Brain-in-the-loop agents an operator *unlocks* by choosing them; each loads a
**surface profile** (`assistants/<SURFACE>/system.md`) that Ocean OS prefers over
its compiled seed prompt — editable, hot-reconfigurable, no rebuild. The surface
*is* the program. Index: [`assistants/README.md`](assistants/README.md).

| Surface | Assistant | Domain |
|---|---|---|
| `[BONZAI]` | bonzai | git hygiene — prune branch sprawl safely, HTML triage board, enforce merge→main→delete |

More surfaces to come (content tab, campaign-booking tab, finances section — each
a surface an agent specializes into).

## Couriers — a hub of single-purpose delivery agents

Narrow agents that ship a payload to a destination over a shared route, invoked
by command. Architecture: [`couriers/ARCHITECTURE.md`](couriers/ARCHITECTURE.md).

**Registry (source of truth = each `courier.toml`):**

| Slash | Courier | Mode | Does |
|---|---|---|---|
| `/ship` | file-courier | deterministic | upload `dropbox/` files to a Slack channel |
| `/say` | file-courier | deterministic | post a message to a Slack channel |
| `/resolve` | file-courier | deterministic | verify a Slack destination |

Run `python3 couriers/hub/router.py list` for the live table (it reads the
manifests, so this prose may lag — the router is authoritative).

## How to invoke a courier

- **Via the router:** `python3 couriers/hub/router.py run <slash> [args]`
  (deterministic → runs the harness; agentic → POSTs a scoped prompt to the
  daemon at `$OCEAN_DAEMON_URL`, default `:4780`).
- **Directly:** `cd couriers/<courier> && bin/courier …` (see its `CLAUDE.md`).

## Invariants (apply to every courier)

- **Confirm the destination before sending** into a shared channel — resolve it
  and read the name back to the operator first.
- **Never hardcode tokens or destinations.** Secrets come from env / a token
  file (Ocean convention: `OCEAN_<X>_…` first); destinations are supplied at run
  time. Nothing sensitive is committed.
- **Don't bypass a courier's harness.** The harness owns transport (auth, upload
  flow, rate limits, retries, ledger). Agents orchestrate + confirm.
- **Adding a courier = drop a folder with a `courier.toml`.** No router edits.
