---
type: sdlc/intent
id: adopter-first-hour
title: A fresh install of the kit breaks in the first hour; the adopter path must work end to end
description: The install omits the approval script, ships the owner's handle in every role, silently skips an existing settings file, reports a false VERIFY PASS on a placeholder, leaves the plan gate open, and gives the adopter no GitHub-side checklist.
stage: plan
status: approved
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 consensus list (item 7)
approved-by: luissiviero
approved-on: 2026-09-05
supersedes:
record:
resource: https://claude.ai/code/session_01Te8oN2GdvRupSixH4kjR8Y
tags: [adopt, distribution, first-hour, hooks, settings, approvals, consensus-item-7]
timestamp: 2026-09-05T02:33:32Z
---
# Intent: a fresh install of the kit breaks in the first hour; the adopter path must work end to end

## Problem
`scripts/adopt.sh` is the kit's stated way into another repository (`README.md:15`, `docs/sdlc/README.md:130`).
Installing into a throwaway repo with `--with-hooks` and following the printed Next steps hits ten problems,
each verified against the working tree (consensus item 7, report B9):

1. `adopt.sh:294` and the rendered `CLAUDE.md` tell the adopter to run `scripts/approve.py`; the copy list
   (`adopt.sh:195-199`) omits it, along with `hooktest.py`, `github_metrics.py`, `bands_config.py` and
   `deploy.sh`, and `:207` omits `deploy.yml` and `bands.yml`. The first human act fails with "no such file".
2. The install commit fails the chain check: `work/_example/plan.md` lists `docs/**` and `work/_example/**`
   only, so every other copied path is "not listed in plan", and nothing explains why.
3. `.sdlc/approvers.yaml` and `.github/CODEOWNERS` land with `luissiviero` in every role. Fixing that means
   editing `.sdlc/`, which the hooks block from an agent, and until then `_example` is approved by a stranger.
4. A pre-existing `.claude/settings.json` (anyone who has used Claude Code in the repo) is skipped with one
   `skip (exists)` line among ninety-five (`adopt.sh:180`, `copy_file`), and every hook is silently inert.
   `test_adopt.py` covers only the empty target.
5. `adopt.sh:241` sets `VERIFY_CMDS` to an `echo`, so `scripts/verify.sh` prints `VERIFY: PASS` on a repo
   whose only verify command is a TODO. `knowledge/decisions/adopt-script.md:56-60` claims the opposite.
6. The plan gate is open on day one: `.sdlc/active` is `_example`, whose plan is already `approved`, and
   `require-plan.sh` checks status and approver role, both satisfied by the copied file.
7. The rendered `CLAUDE.md` opens "This repo is a starter kit for the AI-native SDLC" inside the adopter's
   product repo (`docs/sdlc/rules/00-chain.md:10-13`), spends the generated block before any project content,
   and Next steps step 2 tells the adopter to "cut it to one page" while the drift check forbids editing inside
   the markers.
8. `adopt.sh:215-218` copies the kit's `knowledge/*/index.md`, which link to files that were not copied:
   `OKF: N docs, 14 warnings` on every verify from day one.
9. No GitHub-side checklist ships (required checks, the `control-plane-approved` label, secrets, the App
   install); it exists only in `docs/sdlc/spikes/pr-review-identity.md:71-86`, which is not copied.
   `sdlc-gate.yml` triggers on `pull_request` only, so a direct push to `main` sees no gate.
10. `--force` (`adopt.sh:235`), the documented upgrade path, resets `VERIFY_CMDS` and `PLAN_REQUIRED_PATHS` to
    placeholders; without `--force` there is no signal that an existing file differs from the kit. There is no
    `--help` (`:46` treats it as an unknown flag, exit 2).

## Proposed outcome
1. Every script and workflow the Next steps or the rendered rules name is copied; `.gitignore` and a new
   `docs/sdlc/github-setup.md` travel with them.
2. An existing `.claude/settings.json` is merged (the kit's hook entries and missing permission keys added, the
   adopter's own content kept) and reported as `merged:`; an unparsable one produces a loud warning and the
   hooks are reported as not installed. Never silent.
3. `scripts/verify.sh` in a fresh target ends `VERIFY: FAIL` until the adopter sets `VERIFY_CMDS`; the
   placeholder prints the TODO line.
4. The copied `.sdlc/approvers.yaml` and `.github/CODEOWNERS` carry `<your-github-handle>`, never the kit
   owner's handle; Next steps says to replace it first.
5. The target's `work/_example` is `in-review` with no approver, its plan lists exactly the paths `adopt.sh`
   wrote (no globs), and its ledger records the three `(none) -> in-review` gates; so the plan gate is closed
   until the adopter approves, and once they approve from their own shell with the copied script and commit as
   themselves, the install PR passes the chain check.
6. A fresh target's `CLAUDE.md` opens with `## Commands` and `## Architecture` sections the adopter owns
   (outside the generated markers), and the generated block's first paragraph describes the adopter's repo,
   not a starter kit.
7. `knowledge/*/index.md` in the target link only to files that exist there.
8. `--force` preserves the adopter's `VERIFY_CMDS`, `PLAN_REQUIRED_PATHS` and handle; a skipped file that
   differs from the kit is reported as such; `--help` prints usage and exits 0.
9. Docs say what the code does; tests cover each of the above; the suite, evals and OKF check are green.

## Affected users and systems
- Users: anyone adopting the kit into another repository; the owner, whose handle no longer ships as a default.
- Services / repos / data: `scripts/adopt.sh`, `scripts/test_adopt.py`, `docs/sdlc/github-setup.md` (new),
  `docs/sdlc/spikes/pr-review-identity.md`, `knowledge/decisions/adopt-script.md`, `docs/sdlc/README.md`,
  `evals/cases/adopt-is-idempotent.yaml`.

## Constraints
- Must: keep `adopt.sh` idempotent (a second run prints only skips and rewrites nothing, pinned by the eval);
  never overwrite an adopter's file without `--force`; stay stdlib (`python3 -c` with `json`, no PyYAML); keep
  the kit's own `work/_example` approved; keep every existing `test_adopt.py` assertion.
- Must not: copy the kit's own `.claude/settings.json` (it carries the control-plane unlock); copy
  `work/<kit item>/`, `.claude-plugin/` or `check_plugin_manifest.py`; approve anything on the adopter's behalf.
- Out of scope: the plugin channel (`plugin-distribution.md`); branch protection on this repo; `scripts/checks/
  plugin-manifest.sh` failing in a target that is not a plugin (documented, unchanged); Windows-specific
  behaviour beyond what the existing tests already pin.

## Risk class
low — `adopt.sh` writes only into a target directory the caller names and refuses the kit itself; every change
is exercised by `test_adopt.py` scenarios in temp directories; nothing in this repo's own control plane changes
except `.sdlc/active`.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Placeholder handle spelled `<your-github-handle>` (angle brackets, so it can never collide with a real
  GitHub login and is visibly a placeholder)?
  A: (proposed yes)
- Q: The install flow is approve-first: the adopter replaces the handle, approves `_example` with the copied
  script, commits as themselves, and only then opens the install PR; until then `verify.sh` and the chain
  check are red with the stage-order message. Accept that order rather than an exemption in the chain check?
  A: (proposed yes; an exemption would be a hole every later PR could use)
- Q: `--force` keeps an adopter's `VERIFY_CMDS`, `PLAN_REQUIRED_PATHS` and handle only when they differ from
  the kit's own values and from the placeholders; everything else is overwritten as today?
  A: (proposed yes)
- Q: Seed only `CLAUDE.md` with the project sections (`GEMINI.md` and `AGENTS.md` stay generated-only)?
  A: (proposed yes; the renderer preserves text outside the markers in all three, so an adopter can add
  sections there later)
