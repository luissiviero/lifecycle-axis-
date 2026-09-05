---
type: doc
title: The AI-native SDLC loop, built into this repo
description: A digest of the AI-native SDLC playbook mapped to enforcement mechanisms in this repo.
tags: [sdlc, process, playbook]
timestamp: 2026-09-05T21:00:00Z
---

# The AI-native SDLC loop, built into this repo

> Source: Louis Claxton, *The AI-Native SDLC playbook*, claude.com/blog, 21 Aug 2026 (verified against the full text).
> This document digests the playbook and maps every play to what this repo enforces.

## 1. The playbook in one page

**Thesis.** Code is no longer the bottleneck. Plan, review/test, and deploy still run at human speed; per-line human
review cannot keep up with agent-written diffs; governance-by-committee gets more expensive. Keep the old *control
objectives* (someone decided, someone checked, someone approved, it can be audited) and change the *enforcement*.

**The loop.** Six non-linear stages. A stage ends by committing an artifact; the commit starts the next stage.
An accepted `intent.md` triggers the requirements-and-design pass, an approved `spec.md` triggers plan mode, a merged
PR triggers the pipeline, and a breached control band writes the next `intent.md`. Human attention concentrates at the gates.

| Stage | Play | Artifact / mechanism | Gate |
|---|---|---|---|
| 1 Plan | Capture as intent.md | originator brainstorms with Claude; template as a skill; committed to the intent home | product owner accepts (merge) |
| 2 Design | Requirements and design | one session, org skills as constraints, **flagged areas of concern**; `spec.md` beside `intent.md`; can run headless on intent merge (not automated in this repo; see step 6 of Using it) | product owner (tech lead for higher risk) |
| 3 Build | Plan mode as the default start | interview the engineer; `plan.md`: files that change, order of work, risks, proof; update in the same commit when deviating | engineer (tech lead/architect for higher risk) |
| 3 Build | The CLAUDE.md | `/init`, cut to one page, mistake-twice rule | code owners review changes |
| 3 Build | Skills as institutional knowledge | `.claude/skills/<name>/SKILL.md`, policy owner signs off, advisory control backed by a hook | policy owner |
| 3 Build | Hooks as build-time guardrails | protected paths, formatter after edits, credentials out of the diff; fast, file-scoped; no approval prompts in build | — |
| 3 Build | Parallel sessions and subagents | worktrees, 2–3 sessions, `.claude/agents/*.md` with bounded tools (simplifier, verifier, researcher) | controls come from repo config |
| 4 Test | Give Claude a feedback loop | one verify command, healthy-output examples in CLAUDE.md, failing test first for fixes, **hook blocks test edits during a fix**, visual check for UI, verification is part of "done" | code owner reads attached evidence |
| 4 Test | Continuous evals in CI | 20–50 real tasks (`skill-*` cases; six today) beside the deterministic gate tests; runs on any change to CLAUDE.md, its rule and template sources, skills, hooks, agents, evals or the control plane, and nightly with `--require-claude` so an expired credential is a red run; every incident adds an eval | config-owning team |
| 5 Deploy | AI in the PR review loop | `REVIEW.md` passes (bugs, security, compliance vs spec/plan), Important vs Nit, five-nit cap, `@claude` comment re-runs the review (the reviewer has no write tools; the fix is the author's), findings feed CLAUDE.md, monthly tuning | code owner at the merge click (protected-branch rules where the plan allows them) |
| 5 Deploy | Hooks as approval gates | allow / ask / block; team hooks in `.claude/settings.json`, non-negotiable ones in managed settings; a block explains the route to approval | release manager; change board |
| 5 Deploy | CI/CD integration | `claude -p` read-only judgment first (triage), write steps behind gates, sandboxed with scoped tokens, deploy/rollback as MCP tools, autonomy tiered per environment, rollback is a manual `workflow_dispatch` of the previous SHA (`knowledge/runbooks/rollback-deploy.md`); nothing rehearses it | production gate hook |
| 6 Maintain | Closing the loop | deterministic detector (trailing mean/σ, all four Western Electric rules) + `bands.yaml` tiers: 1σ log, 2σ diagnose read-only, 3σ propose via PR or pre-approved runbook (declared; in this phase 3σ is diagnosed like 2σ and filed as an issue); diagnosis written as `intent.md` | service owner triages |
| 6 Maintain | Recurring codebase scans | scheduled scans (Claude Security); fixes via the review gate; larger findings become `intent.md`; eval per vulnerability class | security lead |
| 6 Maintain | Claude on call (Claude Tag) | first responder in the incident channel under its own identity; verifies recovery over MCP; writes the post-mortem to a version-controlled lessons file | channel is the audit trail |

**Adoption order.** Start with the "clay" plays that nothing points into: intent.md, CLAUDE.md, feedback loop, build-time
hooks, plan mode. Then skills, subagents, evals. Then requirements-and-design, PR review. Then approval gates and CI/CD.
Last, the monitoring loop, scans, and on-call.

**Source of truth sidebar.** For every artifact name one system as the source of truth: the repo, the legacy tool
(Jira/ServiceNow via MCP), or at minimum linkage (record id in the artifact, commit SHA in the record). This repo's
front matter carries a `record:` field for that link.

**Enforcement has three layers.** Advisory (CLAUDE.md, skills) makes the right behaviour likely. Deterministic (hooks,
CI, branch protection, managed settings, sandbox) makes the wrong behaviour close to impossible. Human judgment stays at
the gates. The commit chain is the audit trail.

## 2. How this repo implements each play

```
CLAUDE.md                        one page: rules, commands, conventions, lessons learned; generated, see docs/sdlc/rules/
REVIEW.md                        review passes, Important vs Nit, five-nit cap, do-not-report
.sdlc/                           control plane (agents cannot edit; this repo unlocks it for its own sessions, logged: `knowledge/decisions/self-hooks-on.md`): config.env, active, environments.yaml, release-authorizations/, approvers.yaml, delegation.yaml
work/<slug>/                     intent.md → spec.md → plan.md → incident.md (YAML status, approved-by, record, kind) + log.md gate ledger
docs/sdlc/templates/             the four artifact templates plus log.md, sections named as in the playbook
docs/sdlc/rules/                 one rule source: fragments rendered into CLAUDE.md / GEMINI.md / AGENTS.md by gen_context_files.py
docs/sdlc/spikes/                design spikes that back a decision (plugin packaging, Gemini parity, PR review identity, prompt surfaces and model routing)
docs/sdlc/managed-settings.example.json   the playbook's regulated-enterprise settings, to tailor
docs/sdlc/metrics.md             leading/lagging indicator per play and where to read it
docs/sdlc/lessons.md             pointer file: lessons now live in knowledge/lessons/, one OKF doc per incident
docs/sdlc/okf-pairing.md         how the artifact chain becomes an Open Knowledge Format bundle (multi-model)
knowledge/                       model-neutral OKF bundle: decisions/, lessons/, runbooks/, metrics/, services/
.claude-plugin/                  plugin.json + marketplace.json; ships skills, agents, templates, scripts as a plugin
scripts/adopt.sh                 installs this kit into another repo without overwriting; --with-hooks for .claude/hooks
.claude/skills/sdlc-*            /sdlc-intent /sdlc-spec /sdlc-plan /sdlc-review /sdlc-incident /sdlc-run
.claude/skills/security-standards        policy-as-skill, backed by hooks and the review pass
.claude/agents/                  explorer, plan-reviewer, security-reviewer, verifier (all read-only)
.claude/hooks/                   protect-paths, block-secrets, require-plan, protect-tests, production-gate, post-edit-format, stop-verify-reminder
docs/sdlc/templates/claude-settings.json   the hook wiring adopters get as .claude/settings.json (this repo wires the same hooks on itself, plus the control-plane unlock: knowledge/decisions/self-hooks-on.md)
.gemini/settings.json            the same hook scripts wired for Gemini CLI (BeforeTool / AfterAgent); .gemini/agents/ mirrors .claude/agents/ read-only (knowledge/decisions/gemini-hooks.md)
scripts/verify.sh                the single pass/fail signal; also runs every scripts/checks/*.sh
scripts/checks/                  self-registering verify.sh checks: okf, index-drift, context-drift, workflow-permissions, plugin-manifest
scripts/run_tests.py             the unit suite (scripts/test_*.py), one subprocess per module, modules run concurrently; -j 1 for serial
scripts/check_artifact_chain.py  artifacts approved by a valid approver with a log.md entry; diff ⊆ "Files that change"; release-gated paths have an owner; a diff touching only work/ is checked as far as the chain exists (one stage per PR)
scripts/check_okf.py             OKF conformance over knowledge/ and docs/sdlc/ (warning by default, OKF_STRICT=1 to fail)
scripts/run_evals.sh + evals/    hook cases run anywhere; prompt cases run with `claude -p` when a key exists; --kind/--only/--list select cases
scripts/detect_bands.py          deterministic Western Electric detector (trailing baseline, four rules, full-series scan), unit-tested; monitoring/bands.yaml tiers and `window:`, read into the workflow matrix by scripts/bands_config.py
.github/workflows/sdlc-gate.yml  chain check, verify, control-plane guard, triage-on-failure judgment step
.github/workflows/agent-evals.yml runs on CLAUDE.md / .claude/** / evals changes and nightly
.github/workflows/bands.yml      daily: matrix from bands.yaml, collect GitHub metrics (kept as a run artifact), run the band detector, file an issue on a breach or comment on the open one
.github/workflows/deploy.yml     workflow_dispatch behind a GitHub Environment; the only place scripts/deploy.sh runs
.github/workflows/pr-review.yml  reviews against REVIEW.md on PR open with no Bash; quotes Chain/Verify from the gate run; posts via the action's tracking comment
```

### Enforcement matrix

| Behaviour | Advisory | Deterministic | Human |
|---|---|---|---|
| Nothing implemented without an accepted plan | rule 1, `/sdlc-plan`, plan mode | `require-plan.sh` blocks code edits unless `work/<active>/plan.md` is `approved` by a handle holding the plan's role in `.sdlc/approvers.yaml` | approves plan |
| Diff matches plan; deviations in the same commit | rule 2 | chain check fails PR on files outside "Files that change" | reads deviations log |
| Agent never edits control plane or secrets | rule 3 | `protect-paths.sh` over `PROTECTED_PATHS` (hooks, workflows, `.sdlc`, `.gemini`, `.claude/settings.json`, `scripts/verify.sh`, the two runners, `scripts/checks/`); CI rejects agent PRs touching them | applies via PR |
| Credentials never enter the diff | security-standards §1 | `block-secrets.sh` | — |
| Agent cannot weaken the check on its own fix | Test play step 7 | `protect-tests.sh` when plan `kind: fix`: an existing test file or eval case is locked, a new failing test is allowed | changes a wrong test |
| Formatting never drifts | — | `post-edit-format.sh` (PostToolUse, one file) | — |
| Verified before "done" | rule 5, CLAUDE.md verification block | Stop hook; CI runs `verify.sh`, which reports and fails a non-executable check (`VERIFY_ALLOW_SKIPPED_CHECKS=1` to tolerate); `run_evals.sh` prints a failing oracle's output; `VERIFY_CMDS` runs the chain check against `HEAD` (structure only), the diff-in-plan check is `--base origin/main`, which CI runs | reads the pasted line |
| Agent stops at the production gate | rule 4, environments.yaml | `production-gate.sh`: destructive → block; deploy (incl. `gh release create`, `gh workflow run`, `gh pr merge`) → ask, or block when unattended, unless `.sdlc/release-authorizations/<sha>` names a `release-manager` or `RELEASE_APPROVAL=<sha>` | release manager |
| Review has evidence, ≤5 nits, no self-approval | REVIEW.md, `/sdlc-review` | reviewer subagents have no write tools; the merge click on this plan (`knowledge/decisions/merge-click-is-the-gate.md`), protected-branch rules where the plan allows them | code owner |
| Config that steers the agent is regression-tested | Test play | `agent-evals.yml` on every change to `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `REVIEW.md`, `.claude/**`, `.gemini/**`, `.claude-plugin/**`, `docs/sdlc/rules/**`, `docs/sdlc/templates/**`, `evals/**`, `.sdlc/**`, `scripts/**`; nightly `--require-claude`; `eval-cases.sh` refuses a case that cannot fail | config owner |
| Mistake twice → memory | rule 7, REVIEW.md Memory pass | — | reviewer insists |
| Detection stays deterministic; tier bounds the agent | — | `detect_bands.py` (no model) + `bands.yaml` tier `tools:` passed to `claude -p` by `bands.yml`; the 3σ `routes:` are declared, not yet acted on | service owner triages |
| `approved-by` is a real human role, backed by a ledger entry | rule 8, `docs/sdlc/rules/30-conventions.md` | `protect-approvals.sh` refuses an agent-side `status: approved|superseded`, `approved-by`, `approved-on` or `approve.py` call (no unlock); `check_artifact_chain.py` validates against `.sdlc/approvers.yaml` and requires a matching `work/<slug>/log.md` entry | approver named in the file |
| An agent signs `delegated` only under a human grant | `knowledge/decisions/delegated-mode.md`, `/sdlc-run` | `require-plan.sh` and the chain check accept a signed artifact only when the intent's `mode` is `delegated`, the risk class is in policy, and the handle is in `.sdlc/delegation.yaml`'s `agents`; `scripts/sign.py` is the only writer | grants delegated mode on intent.md |
| A plan revision needs a deviation cap and a consensus record | `docs/sdlc/templates/revision.md`, `/sdlc-run`'s revision rule | `check_artifact_chain.py` counts `deviation:` ledger lines against the policy's `max-deviations` and reads `work/<slug>/revisions/<n>.md` for a unanimous `verdict: revise` before accepting a re-signed artifact | reads `revisions/` |
| A delegated pull request merges without a click | `knowledge/decisions/delegated-mode.md` | `.github/workflows/delegated-merge.yml` and `scripts/delegated_merge.py` merge only when every printed condition holds — two waits fail closed by design: no Claude credential, or a diff touching `.claude/skills/`, `.claude/agents/` or `CLAUDE.md`; `github-actions[bot]` performs the merge | the grant is the click, for delegated items only |
| Control-plane diff on an agent PR needs explicit human sign-off | rule 3 | CI blocks any agent-authored PR (head branch in `AGENT_BRANCH_PREFIXES`, a Bot author, or a Claude commit trailer) touching `PROTECTED_PATHS`; a human applying `control-plane-approved` is the only exemption | applies the label after reading the diff |
| Context files stay one source, never hand-drift | CLAUDE.md play | `context-drift.sh` fails `verify.sh` when `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` don't match `docs/sdlc/rules/*.md` | edits a fragment, not the generated file |
| Workflows stay read-only and unprivileged | — | `workflow-permissions.sh`: every workflow declares `permissions:`, none grants `contents: write` outside the allowlist (`delegated-merge.yml` only, for the merge endpoint), none uses `pull_request_target` | reviews workflow diffs |
| Plugin manifest matches what's actually on disk | — | `plugin-manifest.sh`: every skill/agent listed and vice versa, hook paths exist and are executable, semver valid | — |
| Deploys run only from CI, never from an agent session | rule 4 | `deploy.yml` behind a GitHub Environment's required reviewers (not enforceable on the Free plan: `knowledge/decisions/merge-click-is-the-gate.md`); `deploy.sh` refuses without `CI` set and a release manager's binding of `HEAD`: the `RELEASE_APPROVAL` secret or a committed `.sdlc/release-authorizations/<sha>` | approves the Environment's deployment |

### Design choices worth knowing
- **`work/<slug>/` instead of a bare `intent/` folder.** The playbook commits `spec.md` beside `intent.md`; keeping the
  whole chain of one change in one directory makes the chain check and the git log trivial. A separate intent repo only
  pays off when intent spans many repos.
- **`ask` lives only in the production gate.** The playbook is explicit: approval prompts during build put a person back
  on the critical path of every parallel session. Build hooks allow or block; only the release gate asks.
- **Strong gates are in CI and branch protection, not only in local hooks.** Gemini CLI's `BeforeTool` hook has the
  same exit-2 block contract as Claude's `PreToolUse`, so `.gemini/settings.json` runs the scripts in `.claude/hooks/`
  unchanged (`docs/sdlc/spikes/gemini-parity.md`, `knowledge/decisions/gemini-hooks.md`). A local hook can still be
  skipped — Gemini warns before running a new or changed project hook, and a missing `jq` used to allow blindly — so
  CI (the chain check, verify, branch protection) remains the gate that holds for any model or human, model-neutral
  by construction. See `okf-pairing.md` for the multi-model argument.
- **Evals cover the workflow.** Hook cases need no model and run in seconds; prompt cases run with `claude -p` and
  bounded tools, exactly as the playbook's `agent-evals.yml` does.
- **One file tunes delegated mode.** `.sdlc/delegation.yaml` is the single human-only surface for the whole feature:
  which handles may sign, which artifacts, which risk classes, the deviation cap, the revision rule, and the merge
  conditions; a missing file or `enabled: false` leaves every artifact on the supervised, human-approved path.

## 3. Using it in a project
1. Run `scripts/adopt.sh <target>` (add `--with-hooks` to also install `.claude/hooks/` and, from
   `docs/sdlc/templates/claude-settings.json`, the target's `.claude/settings.json`, merged into one that already exists;
   it copies without overwriting and lists what it skipped and what differs from the kit). Or install as a Claude Code
   plugin — `claude --plugin-dir .` from this repo, or add it to a marketplace via `.claude-plugin/marketplace.json` — for
   the skills, agents, and templates without the repo-local hooks. Then follow `docs/sdlc/github-setup.md` (copied into
   the target): replace `<your-github-handle>` in `.sdlc/approvers.yaml` and `.github/CODEOWNERS`, set `VERIFY_CMDS`
   (the placeholder fails on purpose), `FORMAT_CMD` and the path classes in `.sdlc/config.env`, approve `work/_example`
   as yourself from your own shell with the copied approval script, commit as yourself, open the install PR.
   `--with-hooks` also installs `.gemini/settings.json` and `.gemini/agents/` for Gemini CLI; the hooks need `bash`
   and `jq` on PATH. Antigravity reads `GEMINI.md` but not those hooks (roadmap Phase 1.5).
2. Fill the `## Commands` and `## Architecture` sections `adopt.sh` seeded at the top of `CLAUDE.md`: commands with
   healthy output, architecture in ten lines, the mistakes the team sees most. One page; the generated block below is
   rendered from `docs/sdlc/rules/`.
3. Add standards as skills (security is included; add UX, API conventions, data classification) and list them in `/sdlc-spec`.
4. Protect `main`: require `sdlc-gate` and `agent-evals`; CODEOWNERS for `RELEASE_GATED_PATHS`.
5. Run the loop by hand once. Then automate the spec pass on intent merge and the review pass on PR open.
6. Collect 20–50 real tasks into `evals/cases/`. Add an `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` secret to CI so prompt cases run.
7. Add your own metrics beside the two GitHub ones `bands.yaml` already reads; `bands.yml` diagnoses at 2σ and 3σ and files an issue with a drafted intent (`/sdlc-incident` is the manual follow-up).
