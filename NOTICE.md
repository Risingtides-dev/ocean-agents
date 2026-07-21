Ocean Agents
Copyright © 2026 Rising Tides

Ocean Agents source code, reusable profiles, package manifests, documentation,
and project-authored non-brand artifacts are available under either the MIT
License or the Apache License, Version 2.0, at your option. See LICENSE,
LICENSE-MIT, and LICENSE-APACHE.

Ocean names, logos, wordmarks, and other distinctive brand assets are excluded
from those grants. See TRADEMARKS.md.

The current release tree contains no vendored third-party libraries, fonts,
icons, audio, video, or other third-party visual assets. Its Python programs use
only the Python standard library plus repository-local modules. Git is invoked
as an external command, and Slack Web API endpoints are used as an external
service integration; neither Git, Python, Slack software, nor a Slack SDK is
bundled or relicensed here.

Repository automation references these GitHub-maintained actions:

- actions/checkout@v4
- actions/setup-python@v5

Those actions execute in GitHub-hosted CI and remain governed by their upstream
repositories and licenses. Slack, GitHub, Python, Git, and any other third-party
names or marks belong to their respective owners.

The generated `assistants/<SURFACE>/system.md` files are deterministic
compositions of repository-authored `_shared` and `_base` sources. They remain
under the Ocean Agents project license; generation does not create a separate
third-party license boundary.

Detailed provenance and verification evidence is recorded in
`docs/PROVENANCE.md` and `docs/provenance.json`.
