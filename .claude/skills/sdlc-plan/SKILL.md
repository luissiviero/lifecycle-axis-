---
name: sdlc-plan
description: Build stage, step 1. In plan mode, read an approved spec.md and produce work/<slug>/plan.md with the exact file list, steps, verification, and risks. Use before any implementation.
---
# /sdlc-plan — implementation plan

Precondition: `work/<slug>/spec.md` is approved. Work in plan mode; do not edit code.

1. Read spec.md and the files it touches. Interview the engineer about the repository: conventions, known traps, what must not break.
2. Fill `docs/sdlc/templates/plan.md`. The `## Files that change` list is a contract: CI fails the PR if the diff touches anything not listed. Prefer explicit paths; use globs only for generated files.
3. Any path under `RELEASE_GATED_PATHS` (see `.sdlc/config.env`) goes under `## Release-gated` with a human owner.
4. Map each spec requirement to the test that will prove it under `## Proof`.
5. Write with `status: in-review`. When the intent has `mode: delegated`, run `python3 scripts/sign.py <slug> plan.md`
   and continue implementing — the plan gate opens on a signed plan under the grant. Otherwise stop: implementation
   hooks stay closed until a human sets `status: approved`.

During implementation: if you must deviate, edit `## Files that change` and
`## Deviations log (append during implementation; same commit as the deviation)` in the same commit as the code
change; under a delegation grant, a file-list or order deviation also gets a ledger line, capped by the
policy's `max-deviations`. Anything larger (a step dropped or added, an acceptance test changed, a different
approach, a spec requirement touched) is a plan revision, the last resort: see `/sdlc-run` for the full rule and
`docs/sdlc/templates/revision.md` for the record it requires.
