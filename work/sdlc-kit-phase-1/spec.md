---
type: sdlc/spec
id: sdlc-kit-phase-1
title: Reusable AI-native SDLC kit for Claude + Gemini projects
description: Requirements and design for turning the scaffold into a plugin-distributed kit with an OKF knowledge layer and model-neutral gates.
stage: design
status: in-review
reads: intent.md
approved-by:
approved-on:
skills-applied: [security-standards]
skills-version: 76c05c8
prompt: "Plan-mode session; owner accepted every [recommended] row of decisions.md; draft breakdown by an Opus planner, reviewed and trimmed by the orchestrator."
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/1
tags: [sdlc, okf, claude, gemini, plugin]
timestamp: 2026-09-02T18:00:00Z
---
# Spec: reusable AI-native SDLC kit for Claude + Gemini projects

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) adopt in under an hour and run the loop by hand; (2) gates hold whichever model produced the change; (3) knowledge lives once, read by both models.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-T01 | Chain artifacts + hygiene | outcome 1–3 | see design §T01: its unit test / eval case; `scripts/verify.sh` green |
| R-T02 | Spike: plugin packaging | outcome 1–3 | see design §T02: its unit test / eval case; `scripts/verify.sh` green |
| R-T03 | Spike: Gemini CLI parity | outcome 1–3 | see design §T03: its unit test / eval case; `scripts/verify.sh` green |
| R-T04 | Spike: review action, identity, branch protection | outcome 1–3 | see design §T04: its unit test / eval case; `scripts/verify.sh` green |
| R-T05 | Config keys + self-registering checks | outcome 1–3 | see design §T05: its unit test / eval case; `scripts/verify.sh` green |
| R-T06 | Hook test harness + characterisation tests | outcome 1–3 | see design §T06: its unit test / eval case; `scripts/verify.sh` green |
| R-T07 | Approvers file + loader | outcome 1–3 | see design §T07: its unit test / eval case; `scripts/verify.sh` green |
| R-T08 | `log.md` gate ledger | outcome 1–3 | see design §T08: its unit test / eval case; `scripts/verify.sh` green |
| R-T09 | Eval runner selectors + tests for untested scripts | outcome 1–3 | see design §T09: its unit test / eval case; `scripts/verify.sh` green |
| R-T10 | Stop hook reads `PLAN_REQUIRED_PATHS` | outcome 1–3 | see design §T10: its unit test / eval case; `scripts/verify.sh` green |
| R-T12 | Control-plane guard extracted, tested, label exemption | outcome 1–3 | see design §T12: its unit test / eval case; `scripts/verify.sh` green |
| R-T13 | Chain check validates approver + log entry | outcome 1–3 | see design §T13: its unit test / eval case; `scripts/verify.sh` green |
| R-T14 | OKF conformance checker (warning by default) | outcome 1–3 | see design §T14: its unit test / eval case; `scripts/verify.sh` green |
| R-T15a | `knowledge/` bundle seeded | outcome 1–3 | see design §T15a: its unit test / eval case; `scripts/verify.sh` green |
| R-T15b | OKF front matter on `docs/sdlc/*.md` | outcome 1–3 | see design §T15b: its unit test / eval case; `scripts/verify.sh` green |
| R-T16 | Generated `work/index.md` + per-item `index.md` | outcome 1–3 | see design §T16: its unit test / eval case; `scripts/verify.sh` green |
| R-T17 | One rule source → `CLAUDE.md` / `GEMINI.md` / `AGENTS.md` | outcome 1–3 | see design §T17: its unit test / eval case; `scripts/verify.sh` green |
| R-T18 | GitHub-only metrics → detector | outcome 1–3 | see design §T18: its unit test / eval case; `scripts/verify.sh` green |
| R-T19 | Deploy only from CI via GitHub Environment | outcome 1–3 | see design §T19: its unit test / eval case; `scripts/verify.sh` green |
| R-T20 | PR review workflow + workflow-permissions check | outcome 1–3 | see design §T20: its unit test / eval case; `scripts/verify.sh` green |
| R-T21 | Plugin manifest + drift check | outcome 1–3 | see design §T21: its unit test / eval case; `scripts/verify.sh` green |
| R-T22 | `scripts/adopt.sh <target> [--force] [--dry-run] [--with-hooks]` | outcome 1–3 | see design §T22: its unit test / eval case; `scripts/verify.sh` green |
| R-T23 | Docs and memory refresh | outcome 1–3 | see design §T23: its unit test / eval case; `scripts/verify.sh` green |
| R-T11 | Close the Bash / MultiEdit write bypass | outcome 1–3 | see design §T11: its unit test / eval case; `scripts/verify.sh` green |
| R-T24 | Integration, verification, review | outcome 1–3 | see design §T24: its unit test / eval case; `scripts/verify.sh` green |

## Design
### Architecture / data flow
Artifact chain unchanged. New layers: `docs/sdlc/rules/` → generated `CLAUDE.md`/`GEMINI.md`/`AGENTS.md`; `knowledge/` OKF bundle read by both models; `work/<slug>/log.md` gate ledger read by the chain check; `scripts/checks/*.sh` self-registering into `verify.sh`; GitHub as metrics source → `detect_bands.py`; deploy only from CI via GitHub Environments; kit packaged as a plugin plus `adopt.sh`.

### Interfaces
- `scripts/approvers.py`: `load()`, `role_for(artifact)`, `is_valid(artifact, handle) -> (bool, reason)`, `normalize(handle)`.
- `scripts/log_ledger.py`: `parse(path) -> (entries, malformed)`, `approvals(entries, artifact)`, `render(entry)`; line format `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`.
- `scripts/check_control_plane.sh <base>`: env `SDLC_PR_AUTHOR_TYPE`, `SDLC_PR_HEAD_REF`, `SDLC_PR_LABELS`, `CONTROL_PLANE_LABEL`.
- `scripts/github_metrics.py <metric>`: one float per line, oldest first (input of `detect_bands.py --file`).
- `scripts/deploy.sh <env>`: refuses unless `RELEASE_APPROVAL == HEAD`, `CI` set, env in `environments.yaml`.
- Context-file markers: `<!-- BEGIN GENERATED: docs/sdlc/rules … -->` / `<!-- END GENERATED -->`.

### Data and migrations
None. New files only; `docs/sdlc/lessons.md` becomes a pointer to `knowledge/lessons/`.

### Failure modes and how they surface
Drift between generated and source files → `scripts/checks/context-drift.sh` and `index-drift.sh` fail verify. Unknown approver or missing ledger entry → `CHAIN: FAIL` with the exact line to paste. Bash write to a protected path → hook block with remediation. Control-plane change on an agent PR → CI fails until a human applies the label.

## Areas of concern (flagged)
- C1: hooks are Claude-only; Gemini sessions are governed by CI and branch protection only — policy: security-standards §8 — contradiction? no — owner: luissiviero — resolution: accepted (decision Q3), recorded in spike gemini-parity.md.
- C2: the kit's own control plane must be edited by agents during this work item, which rule 3 forbids in consumer repos — policy: CLAUDE.md rule 3 — contradiction? yes, for this repo only — owner: luissiviero — resolution: CI label `control-plane-approved` applied by the owner; Bash-write guard lands last; human unlock env var for future sessions.
- C3: `SDLC_CONTROL_PLANE_UNLOCK` is a human-set env var; an agent cannot set it for the hook process, but a human who exports it globally weakens the red line — owner: luissiviero — resolution: document as session-scoped, audit line on every allow.
- C4: single human approver means separation of duties is nominal — policy: security-standards §8 — resolution: agent identity in `never-approve`; revisit when a second human joins.

## Open questions carried from intent.md
- none; all ten answered (see intent.md and decisions.md).

## Decisions (ADR-style)
- D1: decisions go to `knowledge/decisions/*.md` as OKF concepts, not a separate ADR tree.
- D2: tests live in `scripts/test_*.py` (hooks dir is protected); hooks are tested via subprocess.
- D3: `scripts/checks/*.sh` self-register so parallel tasks never edit `VERIFY_CMDS`.
- D4: T11 (Bash-write guard) is the last control-plane edit because it would block this session's own edits.

## Gotchas found while reading the codebase
- `stop-verify-reminder.sh` hardcodes paths and mis-parenthesises `find -o`.
- `sdlc-gate.yml` control-plane job would fail PR #1 itself.
- `check_artifact_chain.py` accepts any `approved-by`; `--base HEAD` locally yields an empty diff.
- Edit-hooks do not see Bash heredocs; `.pyc` files were tracked.

## Not doing
- Jira/ServiceNow sync, vendor catalogs, cloud-specific deploy commands, managed settings, Claude Tag, Claude Security, Gemini hooks.

## Design detail per task (from the approved plan)
## Wave 0 — chain artifacts, config, spikes (parallel)

**T01 · Chain artifacts + hygiene — fable**
Files: `work/sdlc-kit-phase-1/{intent.md,spec.md,plan.md,log.md}`, `.sdlc/active` → `sdlc-kit-phase-1`, `.gitignore` (+`__pycache__/`, `*.pyc`), `git rm --cached scripts/__pycache__`.
Spec: fill the ten `A:` lines from decisions.md; `spec.md` with one requirement row per task (R-T05 … R-T24) naming its test; `plan.md` `## Files that change` listing every path in this plan (the chain check fails on unlisted files; `work/ docs/ evals/ monitoring/ knowledge/` are exempt, `.github/workflows/*` must be explicit); `kind: feature`, `risk-class: low`; all three set `status: in-review`. The owner sets `approved` (in chat is fine; Fable records it in `log.md` with the session URL).

**T02 · Spike: plugin packaging — opus** → `docs/sdlc/spikes/plugin-packaging.md`
Answer from current docs (Context7 / claude-code-guide agent; if the network blocks docs, say so and use defensive defaults): `.claude-plugin/plugin.json` schema; how skills/agents/hooks are contributed; `${CLAUDE_PLUGIN_ROOT}` vs `$CLAUDE_PROJECT_DIR` (hooks must find the *consumer's* `.sdlc/config.env`); `marketplace.json`; local loading for dogfooding. Decision: ship hooks in the plugin or repo-local via adopt. Fallback if unverifiable: plugin ships skills+agents+templates; hooks installed by `adopt.sh --with-hooks`.

**T03 · Spike: Gemini CLI parity — opus** → `docs/sdlc/spikes/gemini-parity.md`
Which context file(s) Gemini CLI loads (`GEMINI.md`, `AGENTS.md`, hierarchy, limits); any pre-tool interception comparable to hooks and its contract; committable per-repo settings. Output: two-column table of the eight hard rules → enforced locally for Gemini / CI-only. Decision: generate `AGENTS.md` too, or a pointer. No Gemini hook is written in this phase regardless.

**T04 · Spike: review action, identity, branch protection — opus** → `docs/sdlc/spikes/pr-review-identity.md`
Current `anthropics/claude-code-action` inputs and minimum `permissions:`; which identity the review runs under and whether it shows as `user.type == 'Bot'` (T12 relies on this); whether a bot review can satisfy "one approval"; the single-human workaround (CODEOWNERS + `require_last_push_approval`, or documented admin merge). Output includes a branch-protection checklist for the owner.

**T05 · Config keys + self-registering checks — sonnet**
Files: `.sdlc/config.env`, `.sdlc/README.md`, `scripts/verify.sh`, `scripts/checks/.gitkeep`, `scripts/test_verify.py`.
Spec: add keys with safe defaults `APPROVERS_FILE=".sdlc/approvers.yaml"`, `KNOWLEDGE_PATHS="knowledge docs/sdlc"`, `OKF_STRICT="0"`, `CONTEXT_FILES="CLAUDE.md GEMINI.md AGENTS.md"`, `RULES_SRC="docs/sdlc/rules"`, `CONTROL_PLANE_LABEL="control-plane-approved"`, `BASH_WRITE_GUARD="1"`, `MAX_CONTEXT_LINES="120"`. `verify.sh`: after `VERIFY_CMDS`, run every executable `scripts/checks/*.sh` in sorted order with the same `▶/✔/✘` reporting and fail flag; guard the unexpanded glob; skip non-executables. Test: temp repo → PASS; a failing check → `VERIFY: FAIL` rc 1; non-executable skipped; empty dir passes.

## Wave 1 — test scaffolding and data files (parallel)

**T06 · Hook test harness + characterisation tests — sonnet**
Files: `scripts/hooktest.py` (`fake_repo(**files)`, `run_hook(name, payload, root, env)`), `scripts/fixtures/hook_inputs/{edit,write,multiedit,bash}.json`, `scripts/test_hooks_baseline.py`.
Spec: one test per existing hook locking in today's behaviour (protect-paths blocks `.sdlc/x` and `id_rsa`, allows `src/a.ts`; block-secrets on `content` and `new_string`; require-plan states; protect-tests under `kind: fix`; production-gate block/ask/unattended/`RELEASE_APPROVAL`; post-edit-format no-op; stop hook clean tree). Record the real MultiEdit payload shape (`tool_input.edits[].new_string`) in the fixture; if unconfirmable, note it and T11 handles both shapes.

**T07 · Approvers file + loader — sonnet**
Files: `.sdlc/approvers.yaml` (roles product-owner/tech-lead/release-manager/service-owner → `[luissiviero]`; `artifacts:` map intent→product-owner, spec→product-owner, plan→tech-lead, incident→service-owner; `never-approve: ["claude[bot]","github-actions[bot]","claude"]`), `.github/CODEOWNERS` (`* @luissiviero` + explicit lines for PROTECTED and RELEASE_GATED paths), `scripts/approvers.py` (`load()`, `role_for()`, `is_valid() -> (bool, reason)`, `normalize()` strips `@`, quotes, casefolds, first token), `scripts/test_approvers.py`.
Edge: missing file fails closed; bot handle rejected with reason; unknown artifact rejected; malformed YAML raises with line number.

**T08 · `log.md` gate ledger — sonnet**
Files: `docs/sdlc/templates/log.md`, `work/_example/log.md`, `scripts/log_ledger.py`, `scripts/test_log_ledger.py`.
Format: front matter `type: sdlc/log`; entries `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`. API: `parse(path) -> (entries, malformed)`, `approvals(entries, artifact)`, `render(entry)` (exact line to paste, used in error messages). Malformed lines reported with line numbers, never a crash; missing file → empties.

**T09 · Eval runner selectors + tests for untested scripts — sonnet**
Files: `scripts/run_evals.sh` (`--only <glob>`, `--kind hook|skill|e2e`, `--list`; unknown flag → usage rc 2), `scripts/test_run_evals.py`, `scripts/test_sdlc_metrics.py` (missing plan → `None` not `TypeError`; `commits_after` never negative).

## Wave 2 — defects 1–3 and the OKF checker (parallel; Fable reviews T10, T12, T13 diffs)

**T10 · Stop hook reads `PLAN_REQUIRED_PATHS` — sonnet**
Files: `.claude/hooks/stop-verify-reminder.sh`, `scripts/test_stop_verify_reminder.py`, `evals/cases/hook-stop-uses-configured-paths.yaml`.
Spec: source `_lib.sh` (it already reads stdin and config); keep the `stop_hook_active` guard; build the porcelain regex from `PLAN_REQUIRED_PATHS`; replace the mis-precedenced `find -o` with a per-prefix `find "$ROOT/$p" -newer "$STAMP" -type f -print -quit`, skipping absent prefixes; empty list → no-op; output contract `{"decision":"block","reason":…}` unchanged. Regression test: dirty `src/` while `src` is not configured → no nudge.

**T12 · Control-plane guard extracted, tested, label exemption — sonnet, fable review**
Files: `scripts/check_control_plane.sh <base-ref>` (env `SDLC_PR_AUTHOR_TYPE`, `SDLC_PR_HEAD_REF`, `SDLC_PR_LABELS`, `CONTROL_PLANE_LABEL`; prefixes from `PROTECTED_PATHS`), `.github/workflows/sdlc-gate.yml` (add `labeled, unlabeled` triggers; call the script; always write touched files to `$GITHUB_STEP_SUMMARY`), `scripts/test_check_control_plane.py` (matrix: human+work branch → 0; `claude/*` no label → 1 with remediation; label present → 0 `EXEMPT`; casefolded label; empty diff → 0; missing base → non-zero), `evals/cases/ci-control-plane-label-exempts.yaml`, `knowledge/decisions/control-plane-label.md` (residual risk: label persists across pushes → mitigations: write-access only, dismiss stale approvals, label is a CI exemption not a merge permission, diff printed on every run).

**T13 · Chain check validates approver + log entry — sonnet, fable review**
Files: `scripts/check_artifact_chain.py`, `scripts/test_check_artifact_chain.py`, `evals/cases/chain-rejects-unknown-approver.yaml`, `evals/cases/chain-requires-log-entry.yaml`.
Spec: for each of intent/spec/plan: existing checks, then `approvers.is_valid(name, approved-by)`, then require a `log.md` entry with `artifact == name`, `to_status == approved`, actor matching after normalisation; error text includes `log_ledger.render(...)` template; malformed log lines are notes; missing `log.md` with any approved artifact is an error; add `knowledge/` to `EXEMPT`; `--no-approvers` flag (default off) for early adopters; docstring notes `--base HEAD` yields an empty diff locally.

**T14 · OKF conformance checker (warning by default) — sonnet**
Files: `scripts/check_okf.py [--strict] [paths]`, `scripts/test_check_okf.py`, `scripts/checks/okf.sh` (non-strict unless `OKF_STRICT=1`), `evals/cases/okf-warns-on-missing-type.yaml`.
Rules: front matter with non-empty `type` (required); `title`/`description`/`timestamp` (warn); RFC3339 timestamp; relative `.md`/dir links resolve (skip http/mailto/#); every dir with `.md` has `index.md`. Output `WARN <path> <rule> <detail>` sorted by path; last line `OKF: N docs, W warnings`; exit 1 only with `--strict` and W>0. Walks `KNOWLEDGE_PATHS` + `work/`.

## Wave 3 — knowledge layer, multi-model, CI (parallel; Fable reviews T19)

**T15a · `knowledge/` bundle seeded — sonnet**
Files: `knowledge/index.md`; `knowledge/{decisions,lessons,runbooks,metrics,services}/index.md`; `knowledge/runbooks/rollback-deploy.md` (referenced by `bands.yaml` 3σ and `environments.yaml`, currently missing); `knowledge/metrics/{ci-test-failure-rate,pr-cycle-time-hours,post-deploy-5xx-rate}.md`; `knowledge/decisions/{bash-write-guard,deploy-from-ci,one-rule-source,plugin-distribution}.md` stubs to be filled by their tasks; `docs/sdlc/lessons.md` → pointer to `knowledge/lessons/`.
Acceptance: `python3 scripts/check_okf.py --strict knowledge` exits 0 (`evals/cases/okf-knowledge-bundle-conforms.yaml`).

**T15b · OKF front matter on `docs/sdlc/*.md` — haiku**
Add `type: doc`, `title`, `description`, `tags`, `timestamp` to the five docs; add `docs/sdlc/index.md` and `docs/sdlc/templates/index.md`, `docs/sdlc/spikes/index.md`; fix the `check_okf.py` forward reference wording. Acceptance: `check_okf.py --strict docs/sdlc` exits 0.

**T16 · Generated `work/index.md` + per-item `index.md` — sonnet**
Files: `scripts/gen_index.py [--check]`, `scripts/test_gen_index.py`, `scripts/checks/index-drift.sh`, generated `work/index.md`, `work/*/index.md`, `evals/cases/index-drift-detected.yaml`.
Spec: per item, front matter of the four artifacts (`front_matter()`) + last ledger entry (`log_ledger`) → `index.md` with `type: sdlc/work-item`; top-level table `| slug | title | stage | intent | spec | plan | last gate |`. Byte-stable output (no generation timestamp); `--check` exits 1 naming drifted files. Tests: golden render; idempotence; missing intent handled.

**T17 · One rule source → `CLAUDE.md` / `GEMINI.md` / `AGENTS.md` — opus**
Files: `docs/sdlc/rules/{00-chain,10-hard-rules,20-verifying,30-conventions,40-claude-only,50-gemini-only}.md` (front matter `targets: [claude, gemini]`, `order`), `scripts/gen_context_files.py [--check]`, `scripts/test_gen_context_files.py`, `scripts/checks/context-drift.sh`, `CLAUDE.md` (content preserved, wrapped in `<!-- BEGIN GENERATED … -->` / `<!-- END GENERATED -->` markers; "Lessons learned" stays outside and hand-editable), `GEMINI.md`, `AGENTS.md` (per T03), `knowledge/decisions/one-rule-source.md`.
Spec: concatenate fragments by filename order filtered by target; write between markers, create whole if absent; reject malformed markers; enforce `MAX_CONTEXT_LINES` per file; the eight hard rules byte-identical across outputs (Gemini-only caveat sentence lives in `50-gemini-only.md`). Tests: golden render, target filtering, outside-marker preservation, idempotence, over-length rc 1, rule identity across files.

**T18 · GitHub-only metrics → detector — sonnet**
Files: `scripts/github_metrics.py <ci_test_failure_rate|pr_cycle_time_hours> [--repo] [--days] [--from-json]` (fetch via `gh api --paginate`; pure functions `ci_failure_series(runs, days)` omitting empty buckets and in-progress runs, `pr_cycle_series(prs)` merged only; one float per line, oldest first = `detect_bands.py --file` input), `scripts/fixtures/gh_{runs,prs}.json`, `scripts/test_github_metrics.py` (incl. end-to-end through `detect_bands`), `monitoring/bands.yaml` (`source:` = the producing command; `post_deploy_5xx_rate` marked inert until a store exists), `.github/workflows/bands.yml` (daily: collect → detect; on rc 3 with tier ≥ 2σ and a key present, `claude -p` read-only diagnosis with the tier's `tools`, output filed as a GitHub issue using the intent template; never opens a PR in this phase).

**T19 · Deploy only from CI via GitHub Environment — sonnet, fable review**
Files: `.github/workflows/deploy.yml` (`workflow_dispatch` inputs environment/sha + `release: published`; `environment: ${{ inputs.environment }}`; `permissions: {contents: read, id-token: write}`; concurrency per env; runs verify + chain check then `scripts/deploy.sh` with `RELEASE_APPROVAL=${{ github.sha }}`), `scripts/deploy.sh <env>` (guard + placeholder: refuse unless `RELEASE_APPROVAL == HEAD`, `CI` set, env exists in `environments.yaml`; then echo the command it would run, `# ADOPTERS:` marker), `scripts/test_deploy_guard.py`, `.sdlc/environments.yaml` (name the GitHub Environment per env; agents never invoke deploy), `evals/cases/deploy-refuses-without-approval.yaml`, `knowledge/decisions/deploy-from-ci.md`.

**T20 · PR review workflow + workflow-permissions check — sonnet (after T04)**
Files: `.github/workflows/pr-review.yml` (inputs per T04; prompt = follow `REVIEW.md` verbatim and run `/sdlc-review`; `allowed_tools` read-only + `Bash(scripts/verify.sh)` + chain check; `permissions: {contents: read, pull-requests: write, id-token: write}`; skip drafts), `scripts/check_workflow_permissions.py` (every workflow has top-level `permissions:`; no `contents: write` outside an empty allowlist; no `pull_request_target`; comments ignored; anchors rejected as unsupported), `scripts/test_check_workflow_permissions.py`, `scripts/checks/workflow-permissions.sh`, `evals/cases/review-workflow-is-read-only.yaml`.

## Wave 4 — packaging

**T21 · Plugin manifest + drift check — sonnet (after T02, T17)**
Files: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `scripts/check_plugin_manifest.py` (every `.claude/skills/*/SKILL.md` and `.claude/agents/*.md` listed and vice versa; hook paths exist and are executable; semver; `SKILL.md` `name` equals its directory), `scripts/test_check_plugin_manifest.py`, `scripts/checks/plugin-manifest.sh`, `evals/cases/plugin-manifest-lists-every-skill.yaml`, `knowledge/decisions/plugin-distribution.md`.

## Wave 5 — adoption, docs, and the last control-plane edit

**T22 · `scripts/adopt.sh <target> [--force] [--dry-run] [--with-hooks]` — sonnet (after T21)**
Copies without overwriting (lists skips): `.sdlc/*`, `.claude/{skills,agents,settings.json}` (+hooks with `--with-hooks` per T02), `docs/sdlc/{templates,rules}`, the scripts and `scripts/checks`, `evals/`, `work/_example`, `sdlc-gate.yml`, `agent-evals.yml`, `REVIEW.md`; renders context files into the target; leaves `VERIFY_CMDS` as a `# TODO(adopter)` line; prints next steps. Tests: file set present; second run changes nothing; `--force`; `--dry-run`; existing `CLAUDE.md` preserved; non-git target warns.

**T23 · Docs and memory refresh — sonnet**
Files: `README.md`, `docs/sdlc/README.md` (file map + three new enforcement rows: approver validated against a file; control-plane exemption is a human label; context files generated from one source), `docs/sdlc/phase-2-roadmap.md` (mark items 0 and 6 done), `evals/README.md` (`--kind/--only`, one case per gate), `docs/sdlc/rules/{20-verifying,30-conventions}.md` (new commands with healthy-output examples; `log.md` entry at every gate; `approved-by` from approvers file). Then regenerate context files; one-page limit must hold.

**T11 · Close the Bash / MultiEdit write bypass — opus, fable review (LAST control-plane edit)**
Files: `.claude/hooks/protect-paths.sh` (when `$FILE` empty and `$CMD` set and `BASH_WRITE_GUARD=1`: `bash_write_targets()` extracts targets of `>`/`>>`, `tee [-a]`, `dd of=`, `sed -i`/`perl -i`, `cp/mv/install/rsync` last arg, `truncate`, `git checkout -- <path>`, `patch`/`git apply` mentioning a protected prefix, `python -c … open(<p>,'w')`; ignore `2>&1`, `>&2`, `/dev/null`, variable targets; truncate `$CMD` at 16 KB; feed candidates through the existing `under_any`/secret-filename `case`), human unlock `SDLC_CONTROL_PLANE_UNLOCK=1` (allow + stderr audit line), `.claude/hooks/block-secrets.sh` (scan `edits[]?.new_string` and `command` too), `.claude/settings.json` (add both to the `Bash` matcher before `production-gate.sh`), `scripts/test_protect_paths_bash.py` (blocked: heredoc to `.sdlc/config.env`, `>>` into `_lib.sh`, `tee -a` workflow, `sed -i` on `.sdlc/active`, `cp` into hooks, `> deploy.key`; allowed: `ls > /tmp/out`, `2>&1`, `cat .sdlc/config.env`, `grep -r`; `BASH_WRITE_GUARD=0`; unlock var), `evals/cases/hook-blocks-bash-write-to-protected-path.yaml`, `evals/cases/hook-blocks-multiedit-secret.yaml`, `knowledge/decisions/bash-write-guard.md` (why both hook heuristic and CI job: the CI job never fires for an agent on a `work/*` branch under the owner's identity; false positives cost one stderr line and never prompt a human).

## Wave 6 — integration

**T24 · Integration, verification, review — fable**
1. `scripts/verify.sh` → `VERIFY: PASS (<sha>)` (unit tests, chain, evals, all `scripts/checks/*`).
2. `python3 scripts/check_artifact_chain.py --base origin/main --slug sdlc-kit-phase-1` → `CHAIN: PASS` (self-test of T13 against this work item; owner must have approved and `log.md` must carry the entries).
3. `scripts/run_evals.sh` → `EVALS: ≥17 pass, 0 fail, …`; `check_okf.py` → 0 warnings; `gen_index.py --check`, `gen_context_files.py --check` clean.
4. Hand checks: `adopt.sh` into a temp target is not blocked by the Bash guard (absolute path outside `$ROOT`); single-Edit hook latency < ~150 ms; `verify.sh` wall time reported.
5. `/sdlc-review` (security-reviewer + plan-reviewer subagents, both read-only) → findings in `REVIEW.md` format, fixed or answered.
6. Reconcile `plan.md` `## Files that change` with the real diff; append `## Deviations log` in the same commit; append gate entries to `log.md`; push; update PR #1 body with the verify/chain/evals last lines; ask the owner to apply `control-plane-approved` and confirm the branch-protection checklist from T04.
status: approved
approved-by: luissiviero
approved-on: 2026-09-02
