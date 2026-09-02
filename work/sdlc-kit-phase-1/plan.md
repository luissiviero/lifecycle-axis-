---
type: sdlc/plan
id: sdlc-kit-phase-1
title: Reusable AI-native SDLC kit for Claude + Gemini projects
description: Files, order of work, proof and risks for the phase-1 kit build; detailed task specs live in spec.md.
stage: build
status: in-review
kind: feature
reads: spec.md
approved-by:
approved-on:
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
- .claude/hooks/stop-verify-reminder.sh — read PLAN_REQUIRED_PATHS (T10)
- .claude/hooks/protect-paths.sh — Bash write guard + human unlock (T11)
- .claude/hooks/block-secrets.sh — scan edits[] and command (T11)
- .claude/settings.json — Bash matcher gains the two hooks (T11)
- .claude/hooks/post-edit-format.sh — added by the alignment commit that precedes this work item in PR #1; listed so the PR-level chain check covers the whole diff
- .claude/hooks/production-gate.sh — same
- .claude/hooks/protect-tests.sh — same
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
