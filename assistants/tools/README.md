# assistants/tools — the base-profile composer

## `compose_profile.py` — base-profile injection, made real here

The design spec (§4) wants the house Slack rules to live **once** in
`_base/SLACK/` and a named agent's `<agent>/SLACK/` to hold **only** its deltas.
But the Ocean daemon does **not** compose multiple files — verified in ocean-os
(`crates/ocean-agent/src/lib.rs`):

- `build_system_prompt` = `BASE_SYSTEM_PROMPT` + `load_project_prompt(cwd)`
  (ancestor-walks `AGENTS.md`/`CLAUDE.md` only) + `append_client_type`.
- `append_client_type` → `load_surface_profile_from` reads **exactly one** file:
  `assistants/<SURFACE>/system.md`. No `_shared/`, no `_base/<SURFACE>/` concat.
  The daemon's own `surface_dir` doc comment says the symlink-vs-resolver
  composition is *"Still parked for John"* — i.e. not implemented runtime-side.

So the daemon-composed layering is **flat**. To keep the house rules DRY without
waiting on a Rust change, ocean-agents assembles the base itself — this composer —
into the single `system.md` the daemon actually loads. This is **option (b)** from
spec §4/§13 (path-resolve + concatenate; no symlink sprawl; base stays read-only),
done in agents-space.

### Composition order

1. `_shared/system.md` — cross-surface house core
2. `_base/<SURFACE>/system.md` — per-surface house role
3. `_base/<SURFACE>/{comms,canvas,limits,…}.md` — house SOP split
4. (optional) `<agent>/<SURFACE>/system.md` — agent-specific overrides

### Usage

```bash
# Print the composed house profile for a surface
python3 assistants/tools/compose_profile.py SLACK

# Compose with a named agent's overrides
python3 assistants/tools/compose_profile.py SLACK --agent content-agent

# Publish the daemon-loaded house profile (assistants/SLACK/system.md)
python3 assistants/tools/compose_profile.py SLACK --write

# Verify a published file is current with its sources (CI gate)
python3 assistants/tools/compose_profile.py --check SLACK
```

`assistants/SLACK/system.md` is a **composed artifact** — do not hand-edit it. Edit
the sources (`_shared/system.md`, `_base/SLACK/*.md`) and re-run with `--write`.

> **When ocean-os ships runtime composition** (the parked symlink-vs-resolver), the
> daemon will compose `_shared` + `_base/<SURFACE>` + `<agent>/<SURFACE>` itself and
> this composer is retired. Until then it makes the DRY pattern real today.
