# couriers

A **class** of agents that all run the same route with the same workflow, and
differ only in *what they ship*. A courier:

1. **resolves** a destination the operator names at run time (a Slack channel link),
2. **confirms** it in human terms (bot identity / channel name) before sending into
   a shared channel,
3. **ships** its payload over the shared route — paced, rate-limit-aware, retried,
   ledgered for clean resume.

Because every courier rides the **same route**, that route is extracted once and
shared. Couriers are thin orchestration on top of it.

## The route

[`transport/slack.py`](transport/slack.py) — the shared Slack transport. Pure
stdlib (no `slack_sdk`/`requests`/curl). Owns: token resolution, link parsing
(`/archives/C…`, `?thread_ts=…&cid=…`, raw id), `auth.test`/`conversations.info`,
message posting, the modern 3-step file upload
(`getUploadURLExternal` → PUT bytes → `completeUploadExternal`), rate-limit +
transient retry, channel threading, and an experimental canvas create. Every
courier species imports this; none reimplements Slack.

> Prior route: Telegram. Parked under [`transport/parked/`](transport/parked) —
> the transport shape is identical if it ever needs to come back.

## Species

| Courier | Ships | Entry |
|---|---|---|
| [`file-courier`](file-courier) | files from a dropbox folder + text messages; deletes files on confirmed upload | `file-courier/bin/courier` |

## Adding a courier species

1. Create `couriers/<name>/` with its own `CLAUDE.md` (operating protocol) +
   entry point.
2. `import slack` from `../transport` — use `Slack.post_message` / `upload_file`
   / `call`. Do not hand-roll API calls.
3. Keep the species focused on *what* to ship and *how to confirm*; the route
   handles *how to send*.

## Config / secrets

Token resolution (first hit wins): `$OCEAN_SLACK_BOT_TOKEN` → `$SLACK_BOT_TOKEN`
→ file at `$OCEAN_SLACK_TOKEN_FILE` (default `~/.slack_token`). Bot token
(`xoxb-…`) needs `chat:write`, `files:write`, and a channel read scope. Put
shared config in `couriers/courier.env` (gitignored); a species may override in
its own `courier.env`.
