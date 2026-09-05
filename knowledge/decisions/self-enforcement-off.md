---
type: decision
title: The kit repo does not wire its own hooks
description: The hook wiring lives in docs/sdlc/templates/claude-settings.json and is installed by adopt.sh --with-hooks; this repo has no .claude/settings.json, so an agent maintaining the kit can edit, commit, push and merge without the kit's own red lines blocking it. Hook scripts, tests, evals and CI are unchanged.
tags: [hooks, control-plane, dogfooding, sdlc]
timestamp: 2026-09-02T22:35:09Z
---

# The kit repo does not wire its own hooks

> **Superseded on 2026-09-02 by [`self-hooks-on.md`](self-hooks-on.md).** The owner reinstated the hooks on
> this repo with the control-plane unlock set in `.claude/settings.json`; the template and `adopt.sh`
> behaviour described below still hold for adopters.

## Context

Until PR #1 this repo dogfooded its own hooks: `.claude/settings.json` registered every script in
`.claude/hooks/` as a `PreToolUse`/`PostToolUse`/`Stop` hook, so the same red lines an adopter gets
also bound the agent working on the kit. That is where the kit's own maintenance stalled: the
Bash-write guard (rule 3) blocks any edit under `.claude/hooks`, `.github/workflows` and `.sdlc`,
so the security hardening of those very files had to go through the owner's GitHub connector,
which wrote the hooks without their executable bit (fff489a), which turned CI red, which the agent
could not fix locally because the same guard, plus the harness's own safety classifier, refused
every route. The owner then decided the kit must not police its own repository.

## Decision

- The `hooks` block moves out of `.claude/settings.json` into
  `docs/sdlc/templates/claude-settings.json`. The kit repo carries no `.claude/settings.json`.
- `scripts/adopt.sh --with-hooks` installs the template as `<target>/.claude/settings.json`
  (`copy_file` takes an optional destination for this one case). Adopters get exactly the
  wiring they had before; `scripts/test_adopt.py` asserts the installed file equals the template
  and names every hook.
- Nothing else changes: the hook scripts, their tests (`scripts/test_hooks_baseline.py`,
  `test_protect_paths_bash.py`, `test_control_plane_hardening.py`, ...), the eval cases, and the
  CI jobs (`sdlc-gate`, `agent-evals`) all invoke the scripts directly and keep guarding the
  product.

## Consequences

- An agent session in this repo can edit any path, including the control plane, and run any git
  or `gh` command. Responsibility moves to review: CODEOWNERS routes every control-plane diff to
  the owner, and `check_control_plane.sh` in CI still blocks a `claude/*` PR that touches
  `PROTECTED_PATHS` until a human applies `control-plane-approved`.
- The human unlock (`SDLC_CONTROL_PLANE_UNLOCK=1`) is no longer needed in this repo. It stays in
  `protect-paths.sh` for adopters. Known gap kept for a later fix: the unlock is checked only on
  the Bash branch, so an Edit/Write to a protected path is still blocked even with the variable
  set.
- Rule 3 in `CLAUDE.md` still reads "never edit `.claude/hooks/` ..." because the context files
  are rendered from the shared rule source adopters also receive. In this repo it is advisory;
  the deterministic gate for the kit's own control plane is CI plus the owner's review.
- `plugin-distribution.md`'s reason for keeping hooks repo-local ("bind everyone who trusts the
  folder") is unchanged for adopters; it simply no longer applies to the kit's own folder.

## Alternatives considered

| Alternative | Pros / cons |
|---|---|
| **Move the wiring to a template; the kit repo has no `.claude/settings.json` [chosen]** | + one file moves, scripts and tests untouched; + adopters unaffected; − the kit no longer exercises its own hooks live (the test suite and evals do) |
| Keep the wiring and set the unlock variable in every environment | − the unlock does not cover Edit/Write; − every new environment needs the variable; − does not clear the harness classifier, which reacts to the pattern of an agent working around a guard |
| Empty `PROTECTED_PATHS` in `.sdlc/config.env` | − the hook and CI tests copy the live config and would all need their own fixture; − `adopt.sh` copies the same file, so adopters would inherit the loosened default |
| Delete the hook scripts | − removes the product the kit exists to ship, along with 60+ tests and the eval cases |

## Links

- `docs/sdlc/templates/claude-settings.json`
- `scripts/adopt.sh`, `scripts/test_adopt.py`
- `knowledge/decisions/bash-write-guard.md`, `knowledge/decisions/plugin-distribution.md`
- `work/sdlc-kit-phase-1/plan.md` (deviations log)
