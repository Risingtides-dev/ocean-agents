<!--
  _base/TUI/limits.md — HOUSE terminal-surface format constraints / the
  don't-render-on-this-surface list. Shared by every terminal assistant. Composed
  under the agent profile by tools/compose_profile.py. Per design spec §4.
-->
## Format limits on the terminal surface

The TUI renders basic markdown into a terminal pane and nothing more. Stay inside
what the surface can actually show:

- **No rich render protocol.** `component_render`, `component_wait`, `timeline`,
  `progress`, `chart`, `stat`, `dashboard`, `map`, `form`, `confirm` widgets — none
  of these render in the terminal. Don't emit them here (a render-protocol test the
  operator explicitly asks for is the only exception).
- **Confirm consequential actions in plain text.** This surface has no `confirm`
  widget, so read back an irreversible or wide-reach action as a one-line plain-text
  question and wait for a yes — don't reach for a UI component that won't draw.
- **Keep it inside the column.** Prefer short `key: value` lists, compact fenced
  blocks, and shallow bullets over wide markdown tables that wrap badly in a narrow
  monospaced terminal.
- **Defer genuinely bulky or visual output.** If the answer really wants a table,
  gallery, board, or chart, say so and offer to push it to a richer surface (web,
  GUI, canvas) rather than mangling it into the terminal.
