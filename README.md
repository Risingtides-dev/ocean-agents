# ocean-agents

Provider-agnostic agent packages for the [Ocean OS](https://github.com/Risingtides-dev/ocean-os)
ecosystem. Each package pairs a deterministic **harness** (the hands — pure stdlib,
drivable by any runtime via the `bash` tool) with a `CLAUDE.md`/`AGENTS.md`
**protocol** (loaded by whatever model is the brain).

Ocean OS is provider-neutral by design — the agent loop runs under DeepSeek,
Anthropic, OpenAI, or Google interchangeably. These packages preserve that: all
transport/IO logic lives in the harness, so swapping the model never changes
behavior. This repo is intentionally **not** part of the `ocean-os` Rust
workspace (that repo stays pure Rust crates/containers); these agents *run on top
of* the Ocean runtime.

## Contents

| Group | What it is |
|---|---|
| [`couriers/`](couriers) | A class of agents that ship payloads to a destination over a shared route. Active route: Slack. Includes the shared `transport/` and species like `file-courier`. |

## Layout convention

```
ocean-agents/
├── couriers/                 # a class: same route, same workflow, different payloads
│   ├── README.md             # the class + the shared route concept
│   ├── transport/            # THE route — shared, stdlib, no per-agent dup
│   │   ├── slack.py          # active route
│   │   └── parked/           # retired routes (archived, off active path)
│   └── file-courier/         # a species
│       ├── CLAUDE.md         # operating protocol (provider-neutral)
│       ├── AGENTS.md         # short agent instructions
│       ├── harness/          # orchestration over the route
│       ├── bin/              # thin CLI wrapper
│       ├── dropbox/          # payload staging (gitignored)
│       └── courier.env.example
└── README.md
```

## Quick start (file-courier)

```bash
cd couriers/file-courier
cp courier.env.example courier.env     # add your Slack bot token (or use ~/.slack_token)
# drop files into dropbox/, then:
bin/courier resolve "https://workspace.slack.com/archives/C0123ABCD"
bin/courier send --channel C0123ABCD
bin/courier message --channel C0123ABCD "done ✅"
```
