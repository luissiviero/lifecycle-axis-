---
type: sdlc/plan
id: sdlc-kit-phase-1
title: Reusable AI-native SDLC kit for Claude + Gemini projects
description: Files, order of work, proof and risks for the phase-1 kit build; detailed task specs live in spec.md.
stage: build
status: approved
kind: feature
reads: spec.md
approved-by: luissiviero
approved-on: 2026-09-02
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/1
tags: [sdlc, okf, claude, gemini, plugin]
timestamp: 2026-09-02T18:00:00Z
---
# Plan: reusable AI-native SDLC kit (from intent.md 2026-09-02)

Detailed per-task specs, tests and model tiers: `spec.md` § "Design detail per task". This file is the contract the chain check enforces.

## Files that change
- .gitignore — ignore __pycache__ and .pyc; drop tracked .pyc
- .gitattributes — force LF for *.sh so hooks run from a Windows checkout (roadmap item 19e)
- .sdlc/active — point at this work item
- .sdlc/config.env — new keys (T05)
- .sdlc/README.md — document keys (T05)
- .sdlc/approvers.yaml — roles and never-approve list (T07)
- .sdlc/environments.yaml — GitHub Environment mapping (T19)
- .github/CODEOWNERS — owner for everything, explicit control-plane and release-gated lines (T07)
- .github/workflows/sdlc-gate.yml — call check_control_plane.sh, label triggers (T12)
- .github/workflows/agent-evals.yml — pass --kind if needed (T09)
- .github/workflows/bands.yml — daily metrics → detector → read-only diagnosis (T18)
- .github/workflows/deploy.yml — deploy only from CI via Environment (T19)
- .github/workflows/pr-review.yml — claude-code-action review from REVIEW.md (T20)
- .github/dependabot.yml — weekly SHA bumps for the pinned actions (security review nit, roadmap item 18)
- .claude/hooks/stop-verify-reminder.sh — read PLAN_REQUIRED_PATHS (T10)
- .claude/hooks/_lib.sh — canonical paths; human-only switches captured from the process env (security hardening)
- .claude/hooks/protect-paths.sh — Bash write guard + human unlock (T11)
- .claude/hooks/require-plan.sh — Bash branch via bash_write_candidates (roadmap item 17)
- .claude/hooks/block-secrets.sh — scan edits[] and command (T11)
- .claude/settings.json — Bash matcher gains the two hooks (T11)
- .claude/hooks/post-edit-format.sh — added by the alignment commit that precedes this work item in PR #1; listed so the PR-level chain check covers the whole diff
- .claude/hooks/production-gate.sh — same
- .claude/hooks/protect-tests.sh — same
- .gemini/** — settings.json (BeforeTool/AfterAgent wiring of the same hook scripts) and agents/ (read-only mirrors of .claude/agents/); roadmap Phase 1.5, knowledge/decisions/gemini-hooks.md
- REVIEW.md — rewritten to the four-pass format by the alignment commit that precedes this work item in PR #1; T20's review prompt depends on it
- .claude-plugin/** — plugin.json, marketplace.json (T21)
- scripts/** — verify.sh, checks/*, hooktest.py, fixtures/*, approvers.py, log_ledger.py, run_evals.sh, check_artifact_chain.py, check_okf.py, gen_index.py, gen_context_files.py, github_metrics.py, deploy.sh, check_control_plane.sh, check_workflow_permissions.py, check_plugin_manifest.py, adopt.sh, and one test_*.py per script
- knowledge/** — OKF bundle (T15a, decisions, runbook, metrics)
- docs/** — rules/, spikes/, templates/log.md, index files, front matter, README/roadmap/metrics refresh
- work/** — this work item's artifacts, generated index.md files, _example/log.md
- evals/** — one case per new deterministic gate; README
- monitoring/bands.yaml — concrete sources (T18)
- CLAUDE.md — generated block between markers; lessons stay hand-edited (T17)
- GEMINI.md — generated (T17)
- AGENTS.md — generated or pointer per spike (T17)
- README.md — links (T23)

## Release-gated
(none)

## Order of work
1. Wave 0: T01 chain artifacts + hygiene (fable); T02–T04 spikes (opus); T05 config keys + self-registering checks (sonnet).
2. Wave 1: T06 hook test harness, T07 approvers, T08 log ledger, T09 eval runner selectors (sonnet).
3. Wave 2: T10 stop hook, T12 control-plane label, T13 chain check approver + ledger, T14 OKF checker (sonnet; fable reviews T10/T12/T13).
4. Wave 3: T15a knowledge bundle, T15b docs front matter (haiku), T16 index generator, T17 rule source + renderer (opus), T18 GitHub metrics + bands workflow, T19 deploy from CI (fable review), T20 PR review workflow + permissions check.
5. Wave 4: T21 plugin manifest + drift check.
6. Wave 5: T22 adopt.sh, T23 docs and memory refresh, then T11 Bash-write guard (opus; last control-plane edit; fable review).
7. Wave 6: T24 integration, /sdlc-review, push, PR update (fable).
Commit once per wave after `scripts/verify.sh` is green.

## Risks
- Hooks are live in this session → a Bash-write guard landing early would block the kit's own control-plane edits → mitigation: T11 last; human unlock env var for later sessions.
- Spikes may be unverifiable offline (egress-restricted sandbox) → mitigation: spikes record UNVERIFIED items; T20/T21 use defensive defaults; owner validates locally.
- Parallel subagents in one tree could collide → mitigation: each wave's tasks touch disjoint files; one commit per wave.
- What this could break: nothing in production; `verify.sh` contract lines must stay byte-identical (CLAUDE.md quotes them).
- Options not taken: worktree-per-task (merge overhead for a solo owner); PyYAML dependency (stdlib only); making OKF conformance a hard gate now.

## Proof
- `scripts/verify.sh` → `VERIFY: PASS (<sha>)` (unit tests, chain check, evals, all `scripts/checks/*.sh`)
- `python3 scripts/check_artifact_chain.py --base origin/main --slug sdlc-kit-phase-1` → `CHAIN: PASS`
- `scripts/run_evals.sh` → `EVALS: ≥17 pass, 0 fail, …`; `python3 scripts/check_okf.py` → 0 warnings
- `python3 scripts/gen_index.py --check` and `python3 scripts/gen_context_files.py --check` → clean
- Spec rows → tests: R-T05 → test_verify.py; R-T06 → test_hooks_baseline.py; R-T07 → test_approvers.py; R-T08 → test_log_ledger.py; R-T09 → test_run_evals.py; R-T10 → test_stop_verify_reminder.py; R-T11 → test_protect_paths_bash.py; R-T12 → test_check_control_plane.py; R-T13 → test_check_artifact_chain.py; R-T14 → test_check_okf.py; R-T15a/b → check_okf --strict; R-T16 → test_gen_index.py; R-T17 → test_gen_context_files.py; R-T18 → test_github_metrics.py; R-T19 → test_deploy_guard.py; R-T20 → test_check_workflow_permissions.py; R-T21 → test_check_plugin_manifest.py; R-T22 → test_adopt.py
- Manual: adopt into a temp dir and run its verify.sh; a Bash heredoc into `.sdlc/x` is blocked; CI green on PR #1 after the owner applies `control-plane-approved`.

## Control-plane changes for the owner (rule 3: agents propose, a human applies)
The Bash-write guard (T11) now blocks the agent from editing `.claude/hooks/`, `.claude/settings.json`,
`.github/workflows/` and `.sdlc/` by any route, including the Bash heredocs used earlier in this work item.
The security review of the PR found five Important issues in those files; the fixes are in
`work/sdlc-kit-phase-1/control-plane.patch`, validated in a throwaway clone (59 hook tests, full verify green).
1. `git apply work/sdlc-kit-phase-1/control-plane.patch` on this branch, then `scripts/verify.sh`. It touches:
   `_lib.sh` (canonical paths; switches read from the process env before the config is sourced),
   `protect-paths.sh` (canonicalised candidates, `cd`/`pushd`-relative targets, `ln`), `production-gate.sh`
   (comment only; relies on `_lib.sh`), `settings.json` (`NotebookEdit` in both matchers), `sdlc-gate.yml`
   (slug and refs via env, sanitised fallback, key scoped to the triage step only), `agent-evals.yml` (PR job
   runs hook cases without the key; nightly job runs everything with it), `pr-review.yml` (commenter must be
   owner/member/collaborator; PR-head checkout on both triggers; reviewer has no Bash at all), and adds
   `scripts/test_control_plane_hardening.py`.
2. In `.sdlc/config.env` set `GENERATED_PATHS="src/gen CLAUDE.md GEMINI.md AGENTS.md work/index.md work/*/index.md"`
   (plan review finding; REVIEW.md's do-not-report list depends on it).
3. Apply the `control-plane-approved` label to PR #1 after reading its control-plane diff (the gate re-runs on label).

## Rollback
- Revert the wave's commit; nothing outside this repo is affected.

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-02: `.sdlc/active` stays `_example` until the owner approves intent/spec/plan, so `scripts/verify.sh` (which runs the chain check on the active item) stays green during the build; CI resolves the slug from the PR body and correctly fails until approval.
- 2026-09-02: template files carry an example RFC3339 timestamp instead of a `<RFC3339>` placeholder, because the OKF checker scans docs/sdlc and must parse it (T15b).
- 2026-09-02: `scripts/gen_context_files.py` skips `index.md` in the rules directory; `docs/sdlc/rules/index.md` is an OKF index, not a fragment (found in T23 review).
- 2026-09-02: `docs/sdlc/lessons.md` kept its path as a pointer and gained front matter so the strict OKF check is clean across docs/sdlc and knowledge.
- 2026-09-02: `RELEASE_APPROVAL` in deploy.yml is bound to the checked-out commit (`inputs.sha || github.sha`), not always `github.sha` (found in T19 review).
- 2026-09-02: every workflow hoists `ANTHROPIC_API_KEY` to job-level env so step `if:` expressions can test it; the control-plane step uses `shell: bash` for pipefail (found in T12/T18 review).
- 2026-09-02: `knowledge/decisions/adopt-script.md` added by T22 (covered by `knowledge/**`).
- 2026-09-02: plan review found `GENERATED_PATHS` in `.sdlc/config.env` still reads `src/gen` while the kit now generates `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `work/index.md` and `work/*/index.md`. The Bash-write guard (T11) now blocks the agent from editing `.sdlc/`, so per rule 3 the change is proposed in the PR body for the owner to apply.
- 2026-09-02: security review (five Important findings) → fixes delivered as `control-plane.patch` for the owner to apply (see the section above); `evals/` removed from the chain check's exempt list so a new eval case needs a plan entry; `check_control_plane.sh` compares whole labels. The review's other nits (unpinned action refs; the plan's wildcard file list) are accepted for phase 1 and noted in the roadmap.
- 2026-09-02: owner chose option C for approvals: `scripts/approve.py` (flips front matter, appends the ledger line, refuses inside a Claude Code session via `CLAUDECODE`), with `scripts/test_approve.py` and an eval case. Not in the original task list; covered by `scripts/**` and `evals/**`.
- 2026-09-02: an environment variable is not a gate, so the chain check now also rejects an approval whose committing author is an agent identity (never-approve handle or agent email). That exposed the example item: its approval had been committed by the agent, so `work/_example` is back to `in-review` (ledger updated) and `scripts/verify.sh` stays red on the chain step until the owner runs `scripts/approve.py _example intent.md spec.md plan.md` and commits. `adopt.sh` tells adopters the same.
- 2026-09-02: found after the owner's approvals: `sdlc-gate.yml` never ran on any push because line 17's step name (`"Work-Item: <slug>"` inside an unquoted scalar) is invalid YAML; GitHub showed a failed run with no jobs, listed by file path. Fixed in `control-plane.patch` (quoted step name) and guarded by `scripts/checks/workflow-yaml.sh`. The owner can also fix the live file with one web edit on line 17.
- 2026-09-02: on the owner's explicit instruction, the control-plane hardening and the `GENERATED_PATHS` change were pushed through the owner's GitHub connector (commit fff489a, under the owner's identity) because the local guard blocks the agent from those paths by any route; the owner had also applied the `control-plane-approved` label via the same connector. The chain check then flagged `_lib.sh` as unlisted; added above.
- 2026-09-02: the connector push had also dropped the executable bit on `_lib.sh`, `protect-paths.sh` and `production-gate.sh` (37 hook tests red in CI); restored from the owner's desktop (99b0541, mode-only change).
- 2026-09-02: owner decision after PR #1 went green: the kit no longer wires its own hooks on this repo. The `hooks` block moves from `.claude/settings.json` to `docs/sdlc/templates/claude-settings.json`, which `adopt.sh --with-hooks` installs as the target's `.claude/settings.json`; hook scripts, tests, evals and CI are unchanged. Rationale and consequences: `knowledge/decisions/self-enforcement-off.md`.
- 2026-09-02: security review nit closed after merge: every `uses:` in `.github/workflows/` is pinned to a full commit SHA (`actions/checkout` v4.4.0, `anthropics/claude-code-action` v1) with the version as a trailing comment, the `claude-code` npm install names an exact version, and `.github/dependabot.yml` keeps the SHAs current via weekly PRs. Roadmap item 18 updated; the wildcard file lists stay open.
- 2026-09-02: the owner is on a Claude Max plan and has no API key, so every CI credential check now accepts `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`) alongside `ANTHROPIC_API_KEY`: the four workflows gate on either secret, pass both to `claude-code-action` and to `claude -p`, `scripts/run_evals.sh` treats either as "Claude available", `scripts/test_run_evals.py` strips both, and the docs and `adopt.sh` next steps name both.
- 2026-09-02: owner decision, reversing the same-day self-enforcement-off decision: the kit runs its own hooks again. `.claude/settings.json` is the template plus `env.SDLC_CONTROL_PLANE_UNLOCK=1`; `protect-paths.sh` honours the unlock on the Edit/Write branch too (never for secret material); `bash_write_targets()`/`bash_write_candidates()` moved to `_lib.sh` and `require-plan.sh`/`protect-tests.sh` gained a Bash branch (roadmap item 17), registered on the Bash matcher in the template; `run_evals.sh` unsets the unlock so hook oracles see locked guards. Tests: `scripts/test_bash_plan_gates.py`; evals: `hook-requires-plan-for-bash-write`, `hook-unlock-covers-edit-branch`. Record: `knowledge/decisions/self-hooks-on.md`.
- 2026-09-02: first live run of `pr-review.yml` (PR #6, OAuth token): Claude finished in 4 turns with one permission denial and posted nothing, because the workflow forbids Bash (finding 4) and offered no other posting route. Fixed with `track_progress: true` (the action opens a tracking comment and Claude replaces it via `mcp__github_comment__update_claude_comment`) plus `mcp__github_inline_comment__create_inline_comment` for file:line findings; Bash stays disallowed. The prompt names the tools and forbids `gh`.
- 2026-09-02: session wrap-up after the owner's decisions: `knowledge/decisions/merge-click-is-the-gate.md` records that the private Free-plan repo has no branch protection and the owner's merge click (or an instructed agent merge) is the gate; the spike checklist, `adopt.sh` next steps and the README row for `pr-review.yml` say the same; roadmap item 19 lists the Windows-portability findings and `.gitattributes` fixes the CRLF one.
- 2026-09-02: Gemini CLI wiring (roadmap Phase 1.5): `.gemini/settings.json` runs the same hook scripts on `BeforeTool`/`AfterAgent`, `.gemini/agents/` mirrors the four read-only agents, `.gemini` joins `PROTECTED_PATHS` and hard rule 3. Smoke-testing it on the owner's Windows PC showed the hooks had been silently off there: `canon()` took `C:\...` paths as relative (every guard allowed), and a missing `jq` parsed every field to empty (allow). `_lib.sh` now folds backslashes, treats drive-letter paths as absolute, normalises through `cygpath`, and fails closed without `jq`; `production-gate.sh` blocks instead of asking under Gemini (`GEMINI_SESSION_ID`), which cannot render an ask. Tests: `scripts/test_gemini_wiring.py`; evals: `hook-blocks-drive-letter-path`, `gate-blocks-deploy-under-gemini`. Record: `knowledge/decisions/gemini-hooks.md`.
- 2026-09-03: wrap-up after PR #9: `adopt.sh --with-hooks` also copies `.gemini/` (test in `scripts/test_adopt.py`); the docs record that Gemini CLI v0.58 refuses personal accounts and that Antigravity, the surface actually in use, has a different hook contract (left as the next roadmap item); the root README's stale "draft work item" line is gone and `okf-pairing.md`'s open question on the Gemini surface is answered.
- 2026-09-03: review of PR #11 on `production-gate.sh`: the deploy regex's boundary was `(^|[;&| ])` with a literal space (a tab-indented or parenthesised deploy started no command), and its `git push` clause matched only a bare `main`-shaped word, so `git push origin HEAD:main`, `git push origin :main`, `refs/heads/main`, `--all`, `--mirror` and a bare `git push` onto a main upstream all passed. It also asked on read-only calls, because `aws cloudformation|lambda|ecs` and `az webapp` matched any subcommand. The boundary is now `(^|[;&|(){}!]|[[:space:]])`, each cloud clause names its mutating subcommands, and `git push` left the regex for `push_reaches_protected()`, which reads the refspecs, the whole-repo flags and — for a bare push — the current branch and its upstream, failing closed on a HEAD it cannot resolve. The gate stays a nudge (ask, or block when unattended); authority stays in CI and branch protection per `docs/sdlc/README.md`. Tests: six cases in `scripts/test_hooks_baseline.py` (`ProductionGateHook`); eval: `gate-blocks-refspec-push-to-main`. Files: `.claude/hooks/production-gate.sh`, `scripts/test_hooks_baseline.py`, `scripts/hooktest.py`, `evals/cases/gate-blocks-refspec-push-to-main.yaml`.
- 2026-09-03: roadmap item 19b closed for the hook harness: `scripts/hooktest.py` ran `[hook_path]` directly, which is `WinError 193` on Windows, so all 24 baseline hook tests errored on the owner's PC and the cases above could not be verified where they were written. `run_hook` now invokes `["bash", hook_path]` when `os.name == "nt"`; Linux CI is unchanged. `test_run_evals.py` and the eval oracles still exec `.sh` directly (item 19b's other half).
- 2026-09-03: roadmap item 19 (Windows portability of the kit's own tooling) closed except for the parts that need an OS setting. Six causes, five of them platform artefacts and one a real defect: (1) **`adopt.sh` ran `claude setup-token`** — its `Next steps` heredoc delimiter was unquoted, so the backticks around `` `claude setup-token` `` in step 4 were a command substitution and every `adopt.sh` run started an interactive OAuth flow that never returns. This is not Windows-specific and hits any adopter with Claude Code installed; CI never saw it because `claude` is not on PATH there. Delimiter quoted, regression test asserts the backticks reach stdout as literal text. (2) `adopt.sh` treated `C:\...` as relative (19c), writing a `C:`-named tree into the kit; drive-letter paths now handled as in `_lib.sh`, and a target inside the kit is refused outright, because `copy_tree` walks the kit with `find` and each copy discovers the last one. (3) `test_run_evals.py` forced `PATH=/usr/bin:/bin`, which has no `git` under Git Bash, so all 10 tests failed on empty output; on Windows it now keeps the real PATH minus any directory holding a `claude` binary, which is what the sanitised value was for. (4) `check_artifact_chain.py` built the git pathspec with `os.path.join`, so `git show HEAD:work\<slug>\<file>` failed and the approval-author guard silently reported "not committed yet" instead of running (19d) — the one fix here that closes an enforcement gap rather than noise. (5) `check_plugin_manifest.py` reported skill paths with `os.sep`; repo paths shown to humans are forward-slash on every platform now. (6) NTFS has no POSIX executable bit, so three exec-bit assertions could not be produced on Windows: `test_adopt` asserts the bit only where it exists, `test_verify` and `test_check_plugin_manifest` skip theirs with the reason. Files: `scripts/adopt.sh`, `scripts/check_artifact_chain.py`, `scripts/check_plugin_manifest.py`, `scripts/test_adopt.py`, `scripts/test_run_evals.py`, `scripts/test_verify.py`, `scripts/test_check_plugin_manifest.py`, `evals/cases/plugin-manifest-lists-every-skill.yaml`. Still open: `test_control_plane_hardening`'s symlink test needs Windows Developer Mode (an OS setting, not a code fix).
- 2026-09-03: the owner enabled Windows Developer Mode, the symlink test in `scripts/test_control_plane_hardening.py` ran for the first time on Windows — and **failed**, exposing a real hole in `.claude/hooks/_lib.sh`. `winpath()` only converted POSIX paths matching `/[a-z]/*`, but MSYS resolves a symlink into its own namespace using the shortest mount, so `realpath` returns `/tmp/x/.sdlc/config.env` for a repo under a named mount rather than `/c/users/.../.sdlc/config.env`. That form did not match, the candidate stayed POSIX while `ROOT` was `C:/...`, the prefix test concluded "outside the repo", and a write through a symlink into `.sdlc` was **allowed**. The pattern is now `/*`, which covers every absolute POSIX path (`cygpath` is still absent elsewhere, so Linux is unchanged). Regression: the existing Bash-command test now runs instead of erroring, plus a new `test_symlink_into_control_plane_is_blocked_for_the_write_tool` for the `file_path` branch. This is the third time a Windows path form has made a guard silently allow (`knowledge/decisions/gemini-hooks.md` was the first two); the lesson is that a skipped guard test is not a passing one.
- 2026-09-03: two of the three Windows skips claimed as unavoidable were re-examined and one was wrong. `test_verify`'s non-executable fixture is producible after all: Git Bash ignores the mode and decides `[ -x ]` from the shebang, so `_write_check(..., executable=False)` now drops the `#!` line as well as the mode and the test runs on both platforms. The `test_check_plugin_manifest` one is genuinely unproducible: the checker asks `os.access(path, os.X_OK)`, which on Windows returns True for every existing path — `chmod 0o000`, read-only and directories included — and False only when the path is missing; reading `st_mode` instead would flag every `.sh` (0o666 on NTFS) as non-executable, so the product check stays as it is. `test_adopt` asserts the bit only where the filesystem has one, which is a narrowed assertion rather than a skip.
