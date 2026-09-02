---
type: decision
title: scripts/adopt.sh as the template half of plugin distribution
description: adopt.sh copies the kit's control plane, docs, scripts and hook-scoped evals into a target repo, never overwriting an existing file unless told to, and installs the deterministic hooks only when asked.
tags: [adopt, distribution, plugin, hooks, sdlc]
timestamp: 2026-09-02T00:00:00Z
---

# scripts/adopt.sh as the template half of plugin distribution

## Context

`work/sdlc-kit-phase-1/decisions.md` Q10 accepted **plugin + thin template repo**:
`knowledge/decisions/plugin-distribution.md` (T21) covers the plugin half — `.claude-plugin/plugin.json`
ships skills, agents, commands, templates and scripts, but deliberately *not* hooks, because a red
line must not be a per-user plugin toggle. That leaves a gap: something still has to put the
control plane (`.sdlc/`), the deterministic hooks, and the CI workflows into a new repository,
since none of those travel with the plugin. `scripts/adopt.sh` is that something — the template
half of the same Q10 decision, run once per adopting repo rather than installed and auto-updated
like the plugin.

`docs/sdlc/README.md` §3 ("Using it in a project") already promised this as step 1 ("Copy the
tree (or install it as a plugin, see roadmap)"); this script is what makes that step a single
command instead of a manual file-by-file copy.

## Decision

`scripts/adopt.sh <target-dir> [--force] [--dry-run] [--with-hooks] [--no-create]` copies a fixed
list of paths from this repo (`KIT`, resolved via `git -C "$(dirname "$0")" rev-parse
--show-toplevel`, so the script works from any checkout) into `<target-dir>`, file by file:

- **Never overwrites** an existing file unless `--force` is given; every file gets a
  `copy: <path>` or `skip (exists): <path>` line, so a rerun is legible and idempotent
  (`evals/cases/adopt-is-idempotent.yaml` locks this in: the second run of two consecutive
  invocations emits no `copy:` lines at all).
- **Hooks are opt-in.** `.claude/hooks/` and `.claude/settings.json` — the files that actually
  enforce the eight hard rules locally — are copied only with `--with-hooks` (the settings file
  comes from `docs/sdlc/templates/claude-settings.json`, never from the kit's own
  `.claude/settings.json`, which carries the control-plane unlock the kit needs to maintain
  itself — see `self-hooks-on.md`); otherwise the
  script prints a one-line note explaining that only CI enforces the rules until the flag is
  used. This mirrors `plugin-distribution.md`'s reasoning exactly: a governance mechanism that
  binds "everyone who trusts the folder" should be a deliberate, visible step, not a default a
  `git pull`-style adoption silently skips or silently grants.
- **Eval cases are filtered.** Only `evals/cases/{hook,gate,deploy}-*.yaml` are copied — the
  cases that exercise the hooks and scripts adopt.sh actually installs. Cases like
  `chain-rejects-unknown-approver.yaml`, `plugin-manifest-lists-every-skill.yaml`,
  `index-drift-detected.yaml` or the `okf-*`/`ci-*` cases assert against this repo's own content
  (its `work/` items, its plugin manifest, its knowledge bundle) and would simply fail — or
  worse, silently pass for the wrong reason — in a fresh adopter's tree.
- **`CLAUDE.md`/`GEMINI.md`/`AGENTS.md` are never copied directly.** They are *rendered*, via
  `scripts/gen_context_files.py --root <target-dir>` run once after every other file lands. The
  renderer's own contract — append a generated block to an existing markerless file rather than
  replace it — is exactly the preservation adopt.sh needs for a target that already has a
  hand-written `CLAUDE.md`; adopt.sh relies on that contract instead of re-implementing it.
- **`VERIFY_CMDS` is left as a visible TODO**, not a guess: `.sdlc/config.env` is copied verbatim
  from the kit, then (unless the file pre-existed and `--force` was not given, i.e. an adopter's
  own prior edits are never clobbered) its `VERIFY_CMDS=` line is replaced with a single `echo`
  command naming the placeholder. A silently-wrong default (e.g. `npm test`) would let
  `scripts/verify.sh` report a false `VERIFY: PASS`; a loud placeholder cannot.
- **`.sdlc/active` is set to `_example`** only when absent, so the freshly adopted repo has a
  valid active work item (the copied `work/_example/`) without ever overwriting an adopter who
  has already started their own.
- `--dry-run` performs every check that decides copy vs. skip and prints the same lines, but
  writes nothing — no directory is created, no file is copied, `VERIFY_CMDS` is not touched, and
  `gen_context_files.py` is not invoked.
- A missing target directory is created unless `--no-create` (then the script exits 1); a target
  that exists but is not a git repository gets a warning on stderr and adoption proceeds anyway,
  since the kit's own hooks and scripts degrade gracefully outside git (`verify.sh` already falls
  back from `git rev-parse --show-toplevel` to `pwd`).

## Consequences

- **What is copied**: `.sdlc/{config.env,README.md,approvers.yaml,environments.yaml}`; the whole
  `.claude/skills/` and `.claude/agents/` trees; `docs/sdlc/{templates,rules}`, `docs/sdlc/README.md`,
  `docs/sdlc/okf-pairing.md`; the twelve orchestration scripts (`verify.sh`,
  `check_artifact_chain.py`, `check_okf.py`, `gen_index.py`, `gen_context_files.py`,
  `log_ledger.py`, `approvers.py`, `run_evals.sh`, `detect_bands.py`, `sdlc_metrics.py`,
  `check_control_plane.sh`, `check_workflow_permissions.py`) and all of `scripts/checks/`;
  `evals/README.md` and the hook/gate/deploy eval cases; `work/_example/`; the three CI workflows
  (`sdlc-gate.yml`, `agent-evals.yml`, `pr-review.yml`) and `.github/CODEOWNERS`; `REVIEW.md`;
  `monitoring/bands.yaml`; and `knowledge/index.md` plus its five subdirectory `index.md` stubs.
- **What is not copied**: `.claude/hooks/` and `.claude/settings.json` without `--with-hooks`;
  eval cases that assert this repo's own content (`chain-*`, `plugin-*`, `index-*`, `okf-*`,
  `ci-*`, `review-*`, `skill-*`); `scripts/check_plugin_manifest.py`, `scripts/github_metrics.py`,
  `scripts/deploy.sh`, `scripts/hooktest.py` and `.claude-plugin/` (an adopter is not this repo's
  plugin build, and Q10's plugin channel — not adopt.sh — is how those reach a consumer that
  wants the plugin); `work/sdlc-kit-phase-1/` (this kit's own chain artifacts); the `.sdlc/active`
  and `.sdlc/release-authorizations/` runtime files (recreated fresh); and `CLAUDE.md`/`GEMINI.md`/
  `AGENTS.md` as literal files (rendered instead, so an adopter's own content survives).
  `scripts/checks/plugin-manifest.sh` *is* copied along with the rest of `scripts/checks/`, even
  though its target `check_plugin_manifest.py` is not — an adopted repo that never becomes its own
  plugin will see that one check fail until the adopter deletes it or the manifest catches up; the
  contract this script guarantees is the `VERIFY:`/`CHAIN:` last line, not a green run out of the
  box (`scripts/test_adopt.py` asserts only the former).
- **Why hooks are opt-in**: an adopter who runs `adopt.sh` without `--with-hooks` gets working
  skills, agents, docs and CI checks, but none of the local red lines — `protect-paths.sh`,
  `block-secrets.sh`, `require-plan.sh`, `production-gate.sh` are simply absent from
  `.claude/settings.json` and `.claude/hooks/`. `sdlc-gate.yml` in CI is the backstop for that gap
  once the target's remote CI runs; locally, nothing stops an agent from editing `.sdlc/` in a
  hooks-less adoption. `README.md` and `docs/sdlc/README.md` §3 should point new adopters at
  `--with-hooks` as the default recommendation, per `plugin-distribution.md`'s consequences.

## Links

- `scripts/adopt.sh`
- `scripts/test_adopt.py`
- `evals/cases/adopt-is-idempotent.yaml`
- `scripts/gen_context_files.py`
- `knowledge/decisions/plugin-distribution.md`
- `docs/sdlc/README.md` §3
- `work/sdlc-kit-phase-1/decisions.md`
