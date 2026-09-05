---
type: decision
title: scripts/adopt.sh as the template half of plugin distribution
description: adopt.sh copies the kit's control plane, docs, scripts and hook-scoped evals into a target repo, never overwriting an existing file unless told to, merges an existing settings file, ships a placeholder handle and an in-review example item, and installs the deterministic hooks only when asked.
tags: [adopt, distribution, plugin, hooks, sdlc]
timestamp: 2026-09-05T03:00:57Z
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

The first-hour review of 2026-09-04 (consensus item 7, `work/adopter-first-hour`) found that a fresh
install broke ten times before the adopter could do anything: the approval script was not copied, the
kit owner's handle shipped in every role, an existing settings file was skipped silently, the placeholder
verify command reported a false pass, the example item shipped approved (plan gate open, install commit
uncovered), the rendered context file described a starter kit, the knowledge indexes linked to files that
were not copied, no GitHub-side checklist shipped, and `--force` reset the adopter's values. The bullets
below say what the script does now.

## Decision

`scripts/adopt.sh <target-dir> [--force] [--dry-run] [--with-hooks] [--no-create] [--help]` copies a fixed
list of paths from this repo (`KIT`, resolved via `git -C "$(dirname "$0")" rev-parse
--show-toplevel`, so the script works from any checkout) into `<target-dir>`, file by file:

- **Never overwrites** an existing file unless `--force` is given; every file gets a
  `copy: <path>` or `skip (exists): <path>` line, so a rerun is legible and idempotent
  (`evals/cases/adopt-is-idempotent.yaml` locks this in: the second run of two consecutive
  invocations emits no `copy:` lines at all). A skipped file whose content is not the kit's is reported
  as `skip (exists, differs from kit): <path>`, so an adopter sees drift without `--force`; the files the
  script itself rewrites after copying (`config.env`, `approvers.yaml`, `CODEOWNERS`, `00-chain.md`,
  `work/_example/*`) are excluded from that comparison.
- **`--force` is the upgrade path and keeps three things.** Before overwriting, the script remembers the
  adopter's `VERIFY_CMDS` and `PLAN_REQUIRED_PATHS` lines and the first `product-owner` handle in
  `approvers.yaml`; after the copy each is restored when it differs from both the kit's own value and the
  placeholder the script would otherwise write, with a `preserved: <key>` line. Everything else follows
  the plain meaning of "overwrite".
- **Hooks are opt-in.** `.claude/hooks/` and `.claude/settings.json` — the files that actually
  enforce the eight hard rules locally — are copied only with `--with-hooks` (the settings file
  comes from `docs/sdlc/templates/claude-settings.json`, never from the kit's own
  `.claude/settings.json`, which carries the control-plane unlock the kit needs to maintain
  itself — see `self-hooks-on.md`); otherwise the
  script prints a one-line note explaining that only CI enforces the rules until the flag is
  used. This mirrors `plugin-distribution.md`'s reasoning exactly: a governance mechanism that
  binds "everyone who trusts the folder" should be a deliberate, visible step, not a default a
  `git pull`-style adoption silently skips or silently grants.
- **An existing `.claude/settings.json` is merged, never skipped.** With `--with-hooks` and a settings
  file already in the target (anyone who has used Claude Code there has one), the kit's hook entries
  are appended under their event and matcher, keyed on the hook's `command` so a rerun adds nothing;
  `permissions.deny` and `permissions.allow` are added only when the key is absent; every other key
  is kept as the adopter wrote it; stdout says `merged: .claude/settings.json (<n> hook entries added)`.
  A file that is not JSON is left untouched and `WARNING: .claude/settings.json could not be parsed;
  hooks NOT installed` goes to both stdout and stderr. The merge is stdlib `python3` with `json`.
- **The kit owner's handle never ships.** A freshly copied `.sdlc/approvers.yaml` and `.github/CODEOWNERS`
  have every `luissiviero` replaced by `<your-github-handle>` (angle brackets: not a possible GitHub
  login, visibly a placeholder). Step 0 of the Next steps and `docs/sdlc/github-setup.md` say to replace
  it before approving anything. A pre-existing file is never touched.
- **`work/_example` ships in review, with an explicit plan.** In the target the three artifacts are set to
  `status: in-review` with empty `approved-by`/`approved-on`, `plan.md`'s `## Files that change` is one
  bullet per path this run wrote (plus the generated context files and indexes; no globs), and `log.md`
  records the three `(none) -> in-review` gates with actor `adopt.sh`. The plan gate is therefore closed
  until the adopter approves the item as themselves with the copied approval script from their own shell
  (the target must be a git repository); once they commit that as themselves, the install pull request is
  covered by that plan and passes the chain check. The kit's own `work/_example` stays approved. An
  exemption in the chain check for "the install commit" was considered and rejected: a hole every later
  PR could dress up as.
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
  hand-written `CLAUDE.md`; adopt.sh relies on that contract instead of re-implementing it. When
  `CLAUDE.md` does not exist yet, the script first seeds it with `# <repo>`, `## Commands`,
  `## Architecture` and `## Lessons learned` stubs, so the adopter's project content sits above the
  generated block from day one; and the copied `docs/sdlc/rules/00-chain.md` gets a first paragraph that
  describes the adopter's repository rather than this starter kit.
- **`VERIFY_CMDS` is a placeholder that fails**, not a guess: `.sdlc/config.env` is copied verbatim
  from the kit, then (unless the file pre-existed and `--force` was not given, i.e. an adopter's
  own prior edits are never clobbered) its `VERIFY_CMDS=` line is replaced with
  `echo 'TODO(adopter): …' && false`, so `scripts/verify.sh` prints the TODO and ends `VERIFY: FAIL`
  until a real command is set. A silently-wrong default (e.g. `npm test`) would let `verify.sh` report a
  false `VERIFY: PASS`; so would an `echo` alone, which is what the first version shipped. (`verify.sh`
  splits `VERIFY_CMDS` on `;`, which is why the placeholder uses `&&`.)
- **`knowledge/*/index.md` are written, not copied.** The kit's indexes link to this repo's decisions,
  runbooks and metrics, none of which travel; the target gets six minimal indexes (front matter, one
  paragraph, no links to absent files), so its OKF check is honest from the first run.
- **`.sdlc/active` is set to `_example`** only when absent, so the freshly adopted repo has a
  valid active work item (the copied `work/_example/`) without ever overwriting an adopter who
  has already started their own.
- `--dry-run` performs every check that decides copy vs. skip and prints the same lines, but
  writes nothing — no directory is created, no file is copied, `VERIFY_CMDS` is not touched, and
  `gen_context_files.py` is not invoked. `--help`/`-h` prints the usage and exits 0.
- A missing target directory is created unless `--no-create` (then the script exits 1); a target
  that exists but is not a git repository gets a warning on stderr and adoption proceeds anyway,
  since the kit's own hooks and scripts degrade gracefully outside git (`verify.sh` already falls
  back from `git rev-parse --show-toplevel` to `pwd`).

## Consequences

- **What is copied**: `.sdlc/{config.env,README.md,approvers.yaml,environments.yaml}`; the whole
  `.claude/skills/` and `.claude/agents/` trees; `docs/sdlc/{templates,rules}`, `docs/sdlc/README.md`,
  `docs/sdlc/okf-pairing.md`, `docs/sdlc/github-setup.md`; the seventeen orchestration scripts
  (`verify.sh`, `check_artifact_chain.py`, `check_okf.py`, `gen_index.py`, `gen_context_files.py`,
  `log_ledger.py`, `approvers.py`, `approve.py`, `hooktest.py`, `run_evals.sh`, `detect_bands.py`,
  `github_metrics.py`, `bands_config.py`, `sdlc_metrics.py`, `deploy.sh`, `check_control_plane.sh`,
  `check_workflow_permissions.py`) and all of `scripts/checks/`; `evals/README.md` and the
  hook/gate/deploy eval cases; `work/_example/` (rewritten to in-review, see above); the five CI workflows
  (`sdlc-gate.yml`, `agent-evals.yml`, `pr-review.yml`, `deploy.yml`, `bands.yml`), `.github/CODEOWNERS`
  (handle rewritten) and `.gitignore`; `REVIEW.md`; `monitoring/bands.yaml`.
- **What is written rather than copied**: `knowledge/index.md` plus its five subdirectory `index.md`
  stubs; `.sdlc/active`; the `CLAUDE.md` seed; the rendered `CLAUDE.md`/`GEMINI.md`/`AGENTS.md`;
  `work/index.md` and `work/_example/index.md`.
- **What is not copied**: `.claude/hooks/` and `.claude/settings.json` without `--with-hooks`;
  eval cases that assert this repo's own content (`chain-*`, `plugin-*`, `index-*`, `okf-*`,
  `ci-*`, `review-*`, `skill-*`); `scripts/check_plugin_manifest.py`, `scripts/run_tests.py`, the kit's
  `scripts/test_*.py` and `.claude-plugin/` (an adopter is not this repo's plugin build, and its tests are
  its own; Q10's plugin channel — not adopt.sh — is how the plugin reaches a consumer that wants it);
  the kit's own `work/<slug>/` chain artifacts and `knowledge/` documents (they describe this repo);
  `.sdlc/release-authorizations/` (recreated fresh); and `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` as literal
  files (rendered instead, so an adopter's own content survives).
  `scripts/checks/plugin-manifest.sh` *is* copied along with the rest of `scripts/checks/`, even
  though its target `check_plugin_manifest.py` is not — in a repo with no `.claude-plugin/` manifest
  the check prints `PLUGIN: no manifest (not a plugin repo); skipped` and passes. The contract this
  script guarantees is the `VERIFY:`/`CHAIN:` last line and a red placeholder run, not a green run out
  of the box (`scripts/test_adopt.py` asserts both).
- **The first hour is approve-first.** Replace the handle, set `VERIFY_CMDS`, approve `_example` from
  your own shell, commit as yourself, open the install PR; `docs/sdlc/github-setup.md` has the order and
  the GitHub settings (label, branch protection, secrets, App). Until the approval, `verify.sh` and the
  chain check are red with the stage-order message, on purpose.
- **Why hooks are opt-in**: an adopter who runs `adopt.sh` without `--with-hooks` gets working
  skills, agents, docs and CI checks, but none of the local red lines — `protect-paths.sh`,
  `block-secrets.sh`, `require-plan.sh`, `production-gate.sh` are simply absent from
  `.claude/settings.json` and `.claude/hooks/`. `sdlc-gate.yml` in CI is the backstop for that gap
  once the target's remote CI runs; locally, nothing stops an agent from editing `.sdlc/` in a
  hooks-less adoption. `README.md` and `docs/sdlc/README.md` §3 should point new adopters at
  `--with-hooks` as the default recommendation, per `plugin-distribution.md`'s consequences.
- **A placeholder handle satisfies every role until edited** (`work/adopter-first-hour` spec C1). The
  chain check's commit-author test still refuses an agent-authored approval, and the brackets make a
  forgotten replacement obvious in any review; a `never-approve` entry for the placeholder is noted for
  `docs-reconcile`.

## Links

- `scripts/adopt.sh`
- `scripts/test_adopt.py`
- `evals/cases/adopt-is-idempotent.yaml`
- `docs/sdlc/github-setup.md`
- `scripts/gen_context_files.py`
- `knowledge/decisions/plugin-distribution.md`
- `docs/sdlc/README.md` §3
- `work/sdlc-kit-phase-1/decisions.md`
- `work/adopter-first-hour/`
