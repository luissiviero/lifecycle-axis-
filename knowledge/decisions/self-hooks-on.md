---
type: decision
title: The kit repo wires its own hooks, with the control-plane unlock
description: .claude/settings.json is back, as the adopter template plus env.SDLC_CONTROL_PLANE_UNLOCK=1; the unlock now covers Edit/Write as well as Bash and never lifts the secret-material check; require-plan.sh and protect-tests.sh gained the Bash branch protect-paths.sh already had. Supersedes self-enforcement-off.md.
tags: [hooks, control-plane, dogfooding, sdlc]
timestamp: 2026-09-04T23:42:26Z
---

# The kit repo wires its own hooks, with the control-plane unlock

Supersedes [`self-enforcement-off.md`](self-enforcement-off.md), decided earlier the same day.

## Context

`self-enforcement-off.md` removed `.claude/settings.json` from this repo because the kit's own
guards had stalled its maintenance. Reading the eight hook scripts again shows what actually
stalled it: `protect-paths.sh` refuses every write under `PROTECTED_PATHS` (`.claude/hooks`,
`.github/workflows`, `.sdlc`), and this repo's product lives there. Nothing in the hooks touches
`gh`, `git commit`, `git merge` or a pull-request merge; the only git commands they act on are a
force push, a hard reset to origin, and a direct push to `main` or a release branch, which
`production-gate.sh` turns into a permission prompt. The owner's two requirements, "my hooks
working" and "the project handles GitHub by itself", were therefore never in conflict.

Two gaps stood in the way of simply putting the wiring back:

1. The human unlock (`SDLC_CONTROL_PLANE_UNLOCK=1`) was checked only on the Bash branch of
   `protect-paths.sh`. An unlocked session could `cat >` into `.sdlc/` but not `Edit` a hook.
2. `require-plan.sh` and `protect-tests.sh` were registered on the edit tools only and exited 0 on
   an empty `file_path`, so a heredoc into `src/` needed no approved plan (roadmap item 17, and the
   "not covered" list in `bash-write-guard.md`).

## Decision

- **`.claude/settings.json` returns** with exactly the template's `hooks` block plus
  `"env": {"SDLC_CONTROL_PLANE_UNLOCK": "1"}`. Claude Code exports settings `env` to every
  subprocess, including hooks, and `_lib.sh` captures the switch from the process environment
  before sourcing `.sdlc/config.env`, so the existing "planted in config" defence is unchanged.
- **The unlock applies per protected path on both branches.** `check_target` in `protect-paths.sh`
  prints `SDLC: control plane unlocked by human env (SDLC_CONTROL_PLANE_UNLOCK=1): writing '<path>'`
  to stderr and continues, instead of exiting the whole Bash branch early. The secret-material
  check (`.env`, `*.pem`, `*.key`, `id_rsa`, ...) runs regardless of the unlock, on both branches.
- **`bash_write_targets()` and a new `bash_write_candidates()` live in `_lib.sh`.** The second
  yields canonical repo-relative candidates, each also resolved against every `cd`/`pushd` target
  in the command. `protect-paths.sh`, `require-plan.sh` and `protect-tests.sh` all walk that list
  when `file_path` is empty; `BASH_WRITE_GUARD=0` switches the branch off for all three. The
  template registers the two plan hooks on the `Bash` matcher, so adopters get the closure too.
- **`scripts/run_evals.sh` unsets `SDLC_CONTROL_PLANE_UNLOCK`** before running cases, as
  `scripts/hooktest.py` already strips `SDLC_*`: every oracle sees the guards locked, the way an
  adopter's session does. Without this, running the evals inside a session in this repo would
  report false failures on every "expect block" case.

## Consequences

- The guards are live again in this repo: no credential-shaped content in any write, no writes to
  secret-looking files, plan required for code under `PLAN_REQUIRED_PATHS` (`scripts`, the kit's own product code),
  test files locked during a `kind: fix` item, force pushes and hard resets refused, a push to
  `main` prompts the owner, and a turn that changed plan-required code without a verify run is
  sent back.
- Rule 3 in `CLAUDE.md` stays advisory in this repo, now with evidence: every control-plane write
  by an agent is appended to `.sdlc/hook-decisions.log` (git-ignored; one tab-separated line per
  block, ask or unlock, with the session id) and reported to the session as a `systemMessage`. The
  stderr audit line is kept for the tests, but an exit-0 hook's stderr never reaches the transcript,
  so the log is the record (`work/control-plane-visibility`). The unlock never covers
  `.sdlc/release-authorizations/`, `.sdlc/approvers.yaml` or the log itself. CI's
  `check_control_plane.sh` (which now treats `kit/`, `spike/` and `claude/` branches and Claude
  commit trailers as agent-authored) and CODEOWNERS routing to the owner remain the deterministic
  gate, as before.
- `.claude/settings.json` is not itself under `PROTECTED_PATHS`. An agent in any adopter repo could
  already delete the `hooks` block; adding an `env` unlock is the same class of act and the same
  answer applies: the hook stops the accident, review and CI stop the intent.
- Hook wiring is read at session start. After this lands, the owner restarts the Claude Code
  session in this folder; nothing else changes for adopters, whose `adopt.sh --with-hooks` still
  installs the template (now with five hooks on the `Bash` matcher) and never this repo's file.
- Local evals and hook tests behave as before in CI; on the owner's Windows PC the hook tests still
  cannot exec `.sh` files (see the Windows-portability notes in the roadmap).

## Alternatives considered

| Alternative | Pros / cons |
|---|---|
| **Template + `env` unlock in `.claude/settings.json`; unlock on both branches; Bash branch for the plan hooks [chosen]** | + every guard live, one audit line per control-plane write; + closes roadmap item 17 for adopters as well; − the unlock is a committed file an agent could in principle edit (same as deleting the hooks block) |
| Keep the repo hook-free (status quo) | − none of the eight guards run while the kit is maintained; − the owner asked for the opposite |
| Wire the hooks and set the unlock in the shell that launches Claude Code | − every new environment (desktop app, cloud session, another PC) forgets it; − the unlock still missed Edit/Write until fixed |
| Empty `PROTECTED_PATHS` in this repo's `config.env` | − `adopt.sh` copies that file to adopters; − the hook and CI tests copy the live config as their fixture |

## Links

- `.claude/settings.json`, `docs/sdlc/templates/claude-settings.json`
- `.claude/hooks/_lib.sh`, `protect-paths.sh`, `require-plan.sh`, `protect-tests.sh`
- `scripts/test_bash_plan_gates.py`, `scripts/run_evals.sh`
- `evals/cases/hook-requires-plan-for-bash-write.yaml`, `evals/cases/hook-unlock-covers-edit-branch.yaml`
- `knowledge/decisions/bash-write-guard.md`, `knowledge/decisions/self-enforcement-off.md`
- `work/sdlc-kit-phase-1/plan.md` (deviations log)
