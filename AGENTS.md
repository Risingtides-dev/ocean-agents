# ocean-agents — public package index

This repository owns provider-agnostic surface profiles and reusable agent
package conventions for Ocean OS. It is public and organization-neutral.

## Boundary

Public content may define reusable mechanisms, schemas, profiles, transports,
and examples. It must not contain organization-specific assistants, campaigns,
artists, destinations, operational workflows, private repository paths, or
company knowledge.

Credentials and destinations are always runtime configuration and are never
committed.

## Licensing posture

Project code, reusable profiles, package manifests, documentation, and
project-authored non-brand assets are available under `MIT OR Apache-2.0` at the
recipient's option (`LICENSE`). Ocean names, logos, wordmarks, and distinctive
brand assets are excluded from those grants (`TRADEMARKS.md`). The per-file
source/license/hash inventory is `docs/provenance.json`; `docs/PROVENANCE.md`
summarizes it. Run `python3 scripts/check_release_readiness.py` as the launch
gate. No license-pending or unknown classification is launch-ready.

## Assistants

Ocean loads a generated `assistants/<SURFACE>/system.md` profile according to
the turn's client type. Authored sources live under `_shared/` and
`_base/<SURFACE>/`.

| Surface | Public package | Purpose |
| --- | --- | --- |
| `[ACP]` `[BRWSR]` `[CLI]` `[CNVS]` `[GUI]` `[MOBL]` `[SLACK]` `[TUI]` `[VOX]` `[WEB]` | house profiles | Surface-aware interaction and rendering behavior |
| `[BONZAI]` | `bonzai` | Generic Git branch/worktree hygiene specialist |

Never hand-edit generated house profiles. Run `make assistants-compose`, then
`make assistants-check`.

## Couriers

The router discovers `courier.toml` manifests dynamically.

| Command | Package | Mode | Purpose |
| --- | --- | --- | --- |
| `/ship` | `file-courier` | deterministic | Upload files to a confirmed Slack destination |
| `/say` | `file-courier` | deterministic | Send a message to a confirmed Slack destination |
| `/resolve` | `file-courier` | deterministic | Resolve and verify a destination |

The manifest registry is authoritative:

```bash
python3 couriers/hub/router.py list
```

## Repository contracts

- Read the nearest child `AGENTS.md` before editing.
- Generated profiles must match their `_base` and `_shared` sources.
- Add packages through manifests, not router conditionals.
- Confirm destinations before delivery; do not bypass package harnesses.
- Keep provider credentials and daemon authority outside package content.
- After meaningful changes, append a concise entry to `events.md` including the
  worktree and verification performed.

## Verification

- `make assistants-check`
- `python3 couriers/hub/router.py list`
- `python3 scripts/check_release_readiness.py`
- `python3 -m py_compile` for changed Python files
- validate changed Markdown links
- run a secret scan before public release

## Child index

- `assistants/` — composed surface profiles and named public specialists →
  `assistants/AGENTS.md`
- `couriers/` — manifest router, transport, and reference package →
  `couriers/AGENTS.md`
- `docs/` — public architecture and daemon contracts → `docs/AGENTS.md`
