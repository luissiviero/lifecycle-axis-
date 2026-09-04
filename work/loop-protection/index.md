---
type: sdlc/work-item
id: loop-protection
title: The agent must not be able to weaken the check on its own work
description: The verify loop, the test lock and the session settings are unprotected; a branch that guts verify.sh passes every gate, a fix item cannot write its failing test first, and a skipped check or a failing eval says nothing.
timestamp: 2026-09-04T21:53:54Z
---
# The agent must not be able to weaken the check on its own work

- [intent.md](intent.md) — status: in-review; approved-by: ; The verify loop, the test lock and the session settings are unprotected; a branch that guts verify.sh passes every gate, a fix item cannot write its failing test first, and a skipped check or a failing eval says nothing.
- [spec.md](spec.md) — status: in-review; approved-by: ; Protect the verify loop and the session settings as control plane, lock only existing tests under a fix, pre-approve the loop and deny egress in settings, and make a skipped check or a failing eval speak.
- [plan.md](plan.md) — status: in-review; approved-by: ; Files, order, proof and risks for protecting the verify loop and settings, the existing-only test lock, permissions in settings, and loud skipped checks and failing evals.

Last gate: - 2026-09-04T21:56:38Z | plan.md | (none) -> in-review | claude | 64bcb17 | same
