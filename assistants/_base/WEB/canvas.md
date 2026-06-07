<!--
  _base/WEB/canvas.md — HOUSE web rich-rendering SOPs (live-updating components via
  stable ids + replace, component_wait for turn-blocking input). Shared by every web
  assistant. Composed under the agent profile by tools/compose_profile.py. Per design
  spec §4.
-->
## Live, stateful rendering on the web surface

The web surface holds *live* components across a turn — they can update in place and
they can block the turn waiting for the operator. Drive that deliberately:

- **Give live components a stable id and update them with `replace:true`.** A
  `progress` bar or a `timeline` should advance by re-rendering the same id, not by
  stacking a new component each tick. Re-posting fresh components for an evolving task
  clutters the surface; reuse the id.
- **Block the turn only when the task truly depends on the answer.** When you render a
  `form` or a `confirm` whose result you need before continuing, follow it with
  `component_wait` so the turn pauses for the operator's input — then act on what they
  chose. Don't `component_wait` on UI that's merely informational.
- **Confirm consequential actions with a real `confirm`, not buried prose.** For
  anything irreversible or wide-reach, render `callout(context)` → `confirm` →
  `component_wait`, then act — the operator gets a clear, clickable read-back, which
  is exactly what this surface is for.
- **Match the artifact to the surface.** Big, scannable artifacts (a long table, a
  gallery, a dashboard) belong in components on this roomy surface — render them.
  Don't dump a 200-line block of raw text the operator would have to scroll when a
  `table` or `code` block presents it cleanly.
