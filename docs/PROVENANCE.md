# Ocean Agents Provenance

Status: current release-tree audit complete; no unresolved provenance or license
classifications remain.

This document records the public-source boundary for Ocean Agents. The compact
machine-readable companion is [`provenance.json`](provenance.json), and the
launch gate is:

```sh
python3 scripts/check_release_readiness.py
```

## Audit scope

The 2026-07-21 audit covered:

- authored surface-profile sources under `assistants/_shared/` and
  `assistants/_base/`;
- all ten generated `assistants/<SURFACE>/system.md` outputs;
- Bonzai profile, Python harness, shell entry point, and HTML triage template;
- profile composition, courier routing, Slack transport, and file-courier Python
  and shell code;
- TOML manifests, GitHub Actions configuration, repository contracts, and all
  Markdown documentation;
- copied/adapted-code indicators, copyright/license markers, imports,
  dependencies, executable files, external URLs, and tracked asset/media types;
- both commits in the repository's fresh public history at audit time;
- exact-byte comparison against the authorized predecessor package snapshot to
  distinguish transferred Ocean project work from unknown third-party material.

The audit found no vendored third-party source, dependency lockfile, package
manager manifest, font, icon, image, audio, video, or PDF in the current tree.
All executable Python imports resolve to the standard library or the local
`couriers/transport/slack.py` module. No Slack SDK is bundled.

## Authorship and generated files

The repository was initialized in commit `8ea01aa` as a clean public snapshot of
reusable Ocean package work authored for Rising Tides. Private operational Git
history was intentionally not imported. Exact-byte overlap with the authorized
predecessor snapshot establishes internal project provenance; it does not grant
or expose private production content.

Generated house profiles are assembled by
`assistants/tools/compose_profile.py` from the repository-authored shared and
surface-specific Markdown sources. `make assistants-check` proves the committed
outputs match those sources. Generated output carries the same
`MIT OR Apache-2.0` project license as its authored inputs.

## Public-boundary correction

The audit found snapshot-specific branch counts, a provider-specific handoff,
and production-subject deletion heuristics in Bonzai's public triage template
and harness. They were removed rather than documented as reusable behavior.
Bonzai now classifies only unique commits with no changed files as `noise`; every
content-bearing branch remains `work` unless the operator decides otherwise.
This makes deletion safer and restores the public repository's
organization-neutral boundary.

This correction removes the material from the current release tree. It does not
claim that already-public Git history has been recalled or rewritten.

## External tools and services

Ocean Agents interoperates with, but does not vendor or relicense:

- Python and its standard library;
- Git, invoked as an external command by Bonzai;
- Slack's Web API, called directly with operator-supplied runtime credentials;
- GitHub-hosted CI and the referenced `actions/checkout@v4` and
  `actions/setup-python@v5` actions;
- Ocean OS and Ocean Surface public runtime/client contracts.

Their names, software, services, and marks remain under their respective terms.
See [`../NOTICE.md`](../NOTICE.md).

## Tracked asset

The only tracked file in the audited image/icon/font/media/PDF/HTML extension set
is `assistants/bonzai/artifacts/triage-board.template.html`. Its inline HTML,
CSS, and JavaScript are project-authored, contain no external assets, and are
available under `MIT OR Apache-2.0`. Its exact byte count and SHA-256 are pinned
in `provenance.json`.

## Ongoing rule

Before adding or changing copied, adapted, generated, or vendored material:

1. establish its source, author/owner, license, and redistribution terms;
2. preserve required notices in the repository;
3. update this document and `provenance.json`;
4. add every new image, icon, font, media file, PDF, or HTML artifact to the
   machine-readable asset inventory with exact bytes and SHA-256;
5. run `python3 scripts/check_release_readiness.py`, `make assistants-check`, and
   the nearest package checks;
6. record meaningful changes in `events.md`.

Unknown provenance is a release blocker. Do not infer project authorship merely
from presence in Git history.
