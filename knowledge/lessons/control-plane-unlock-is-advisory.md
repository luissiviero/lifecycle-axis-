---
type: lesson
title: The control-plane unlock makes rule 3 advisory in this repository
description: "This repo runs its own hooks with SDLC_CONTROL_PLANE_UNLOCK=1, so a control-plane write passes with an audit line and a systemMessage; CI and the owner's review guard the control plane, not the hook."
tags: [lesson, hooks, control-plane, self-hosting]
resource: ../../work/control-plane-visibility/
timestamp: 2026-09-05T04:45:00Z
---
# The control-plane unlock makes rule 3 advisory in this repository

## What happened
The kit dogfoods its own hooks with `SDLC_CONTROL_PLANE_UNLOCK=1` set in `.claude/settings.json`
([self-hooks-on](../decisions/self-hooks-on.md)). A write under `PROTECTED_PATHS` therefore passes; the hook
appends a line to `.sdlc/hook-decisions.log` and reports a `systemMessage`. Before `work/control-plane-visibility`
the only trace was a stderr line, and an exit-0 hook's stderr never reaches the transcript, so the sessions believed
the hook had blocked what it had let through.

## Rule
Treat rule 3 as advisory here: CI's control-plane job (the `control-plane-approved` label) and the owner's review are
the gate. Restart the session after changing hook wiring; the running session keeps the old hooks.

## Where it is enforced
`scripts/check_control_plane.sh` in `sdlc-gate`; the decision log; `knowledge/decisions/self-hooks-on.md`.
