# hub

The courier hub's **router** — the `slash-command → courier` dispatch layer.
See [`../ARCHITECTURE.md`](../ARCHITECTURE.md) for the full picture.

```bash
python3 router.py list                          # all couriers + commands
python3 router.py resolve /ship                 # who handles a command (JSON)
python3 router.py run --dry-run /ship --channel C0123ABCD
python3 router.py run /ship --channel C0123ABCD
```

- Discovers every `../*/courier.toml` — adding a courier needs no router edit.
- **deterministic** couriers → execs the harness directly.
- **agentic** couriers → `POST /v1/prompt` to the Ocean daemon
  (`$OCEAN_DAEMON_URL`, default `http://127.0.0.1:4780`), scoped to the courier's
  dir so the daemon auto-loads its `CLAUDE.md`.

The Slack slash-command intake (the front door that calls this router) is a
separate, outward-facing layer and is not built here.
