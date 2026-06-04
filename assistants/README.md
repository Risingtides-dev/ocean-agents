# assistants — surface-specialist agents

A class of **brain-in-the-loop** agents that *operate on a surface*. Where a
**courier** ships a payload outbound over a route, an **assistant** is a
specialist an operator *unlocks* by choosing it — and it loads a **surface
profile** that changes how the agent behaves while it's on that surface.

This is the consumer side of the Ocean OS **surface taxonomy**. Ocean OS stamps
every turn with a surface flag (`[BONZAI]`, `[SLACK]`, `[BRWSR]`, `[GUI]`, …) and,
via `build_system_prompt → load_surface_profile`, prefers an on-disk
`assistants/<SURFACE>/system.md` over its compiled-in seed prompt. So a surface
profile is **editable data, hot-reconfigurable without a daemon rebuild** — the
Software-2.0 idea: the surface *is* the program.

## Layout convention

```
assistants/
├── _shared/                  # surface-agnostic core identity for assistants
└── <assistant>/              # one specialist = one surface
    ├── system.md             # THE surface profile Ocean OS loads (per surface)
    ├── CLAUDE.md             # full operating protocol (provider-neutral)
    ├── AGENTS.md             # short agent instructions
    ├── harness/              # deterministic hands (pure stdlib, bash-drivable)
    ├── bin/                  # thin CLI wrapper
    └── artifacts/            # tools the assistant produces/uses (e.g. HTML boards)
```

## Registry

| Surface flag | Assistant | Domain | Does |
|---|---|---|---|
| `[BONZAI]` | **bonzai** | git hygiene / worktree | Prune branch sprawl safely; produce an HTML triage board (restore/cherry/delete); enforce merge→main→delete. |

**More surfaces to come.** Each tab/section of the operator's world is its own
surface an agent can specialize into:
- a **content agent** loads its profile in the content tab (generate/clip/post
  workflow, the content-posting-lab pipeline),
- a **campaign-booking agent** loads its profile in the campaign tab (creator
  outreach, booking, the campaign-hub),
- a **finance agent** loads its profile in the finances section (reconciliation,
  reporting — read-mostly, high-confirmation),
- **bonzai** loads its profile when it's time to prune the worktree.

Same runtime and model; the *loaded surface* decides the role, the allowed tools,
the SOPs, and the comms style. Adding an assistant = drop a folder with a
`system.md`. No router edits.
