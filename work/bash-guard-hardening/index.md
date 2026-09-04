---
type: sdlc/work-item
id: bash-guard-hardening
title: The Bash write guard silently allows deletes, glued commands, stderr redirects and two-step cd into the control plane
description: bash_write_targets misses eleven command shapes that write to or remove protected paths, the hooks ignore the cwd field, and NotebookEdit bypasses every edit hook; harden within a stated bound and document the residuals.
timestamp: 2026-09-04T21:48:41Z
---
# The Bash write guard silently allows deletes, glued commands, stderr redirects and two-step cd into the control plane

- [intent.md](intent.md) — status: in-review; approved-by: ; bash_write_targets misses eleven command shapes that write to or remove protected paths, the hooks ignore the cwd field, and NotebookEdit bypasses every edit hook; harden within a stated bound and document the residuals.
- [spec.md](spec.md) — status: in-review; approved-by: ; Requirements and design for closing the verified silent-allow shapes of the Bash write guard within a 140-line bound, reading the hook input's cwd, covering NotebookEdit, and recording the accepted residuals.
- [plan.md](plan.md) — status: in-review; approved-by: ; Files, order of work, proof and risks for closing the verified Bash write-guard gaps within a 140-line bound; design and test strings live in spec.md.

Last gate: - 2026-09-04T21:57:52Z | plan.md | (none) -> in-review | claude | 64bcb17 | same
