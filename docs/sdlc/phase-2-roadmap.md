---
type: doc
title: Phase 2+ roadmap: what the playbook leaves out
description: Future phases and gaps beyond Phase 1 of the AI-native SDLC implementation.
tags: [sdlc, roadmap, future]
timestamp: 2026-09-02T20:00:00Z
---

# Phase 2+ roadmap: what the playbook leaves out

Checked against the full article. The playbook does cover more than early summaries suggested: it defines a leading and
lagging indicator per play, separates duties (agent identity in CI, branch protection, no self-approval), rehearses
rollback, gives a managed-settings and sandbox worked example, and adds security scanning and on-call. The gaps below
are what remains once all of that is built. Ordered by how soon a complex project hits them.

## Phase 1.5 — multi-model knowledge layer (see `okf-pairing.md`)
0. **OKF bundle and Gemini parity.** Artifact chain as an OKF bundle, `knowledge/` for institutional knowledge,
   `log.md` gate ledger, `GEMINI.md`/`AGENTS.md` generated from the same rule source, conformance check as a warning.
   **Done in phase 1:** the [`knowledge/`](../../knowledge/index.md) bundle, the
   [`docs/sdlc/rules/`](rules/index.md) fragments rendered by
   [`scripts/gen_context_files.py`](../../scripts/gen_context_files.py), the `log.md` ledger (see
   `docs/sdlc/templates/log.md`), and [`scripts/check_okf.py`](../../scripts/check_okf.py) as a warning-only check.
   **Done (Gemini hook wiring):** `.gemini/settings.json` runs the same hook scripts on `BeforeTool` /
   `AfterAgent`, `.gemini/agents/` mirrors the read-only agents, the release gate fails closed under Gemini, and the
   `tool_input` keys are verified against the installed CLI
   ([`knowledge/decisions/gemini-hooks.md`](../../knowledge/decisions/gemini-hooks.md)).
   **Open:** Gemini CLI v0.58 refuses personal Google accounts ("migrate to Antigravity"), and Antigravity reads
   `GEMINI.md` but not `.gemini/settings.json`: its hooks live in `.agents/hooks.json`, receive `toolCall.name` /
   `toolCall.args` (`write_to_file`: `TargetFile`, `CodeContent`; `run_command`: `CommandLine`) and answer with a JSON
   `decision` on stdout. Next step: an adapter under `.agents/` that maps that payload onto the existing scripts and
   turns their exit 2 into `{"decision":"deny"}`, with `.agents` joining `PROTECTED_PATHS`. Also open: an end-to-end
   check that PowerShell forwards Gemini CLI's stdin to `bash` on Windows (verified by simulation only).

## Phase 2 — measurable, safe to run unattended
1. **Cost and budget attribution.** The playbook names "agent budget" and reads timings from git and OTel but never
   attributes spend. Add a per-work-item ledger (tokens, tool calls, retries, human review minutes, gate wait) and a
   `cost_per_merged_pr` control band. The per-role model routing in
   [`spikes/prompt-surfaces.md`](spikes/prompt-surfaces.md) §2.6 is judged by this ledger; until it exists, that
   spike's Phase C uses a per-work-item token count in `log.md` as the stand-in.
1b. **Prompt surfaces and model routing.** The Claude platform prompting, guardrail and eval docs encoded where they
   run: canonical prompt blocks, a `prompting-standards` skill, a prompt-surface lint in `verify.sh`, templates, a
   conditional review pass, per-role model and effort pins with a delegation policy and caps, and evals for each.
   **Designed, not scheduled:** [`spikes/prompt-surfaces.md`](spikes/prompt-surfaces.md) (accepted 2026-09-03; the
   set-aside alternatives are listed at its end). Becomes work item `prompt-surfaces` when scheduled.
2. **Computed risk tiers.** "Routine vs higher risk" and "small blast radius" decide who approves and what auto-merges,
   yet the class is a field a human fills in. Derive it from touched paths, dependency graph, data classification, and
   diff size; CI attaches it; branch protection and `environments.yaml` key off it.
3. **Database and schema safety.** The playbook only says hooks can block migration edits without a change ticket.
   Add a migration linter in `verify.sh` (destructive ops, lock analysis, reversibility), migrations in
   `RELEASE_GATED_PATHS`, and a data-migration standards skill.
4. **Runtime visibility during Design and Build.** MCP is used for deploy tools and for Claude Tag's recovery check,
   not for seeing live state while writing a spec. Add read-only MCP servers for logs, metrics, and schema, and a
   required "observed state" section in `spec.md`.
5. **Traceability across the soft links.** Intent → spec → plan is checked by front matter only. Require IDs
   (outcome → requirement → step → test) and an agentic spec-conformance reviewer that fails a requirement without a test.
6. **Distribution as a plugin.** The playbook distributes skills and hooks through a private marketplace. Package this
   repo as a plugin (skills, agents, hooks, templates) plus a thin template repo, so projects update centrally.
   **Done in phase 1:** [`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json) +
   [`marketplace.json`](../../.claude-plugin/marketplace.json),
   [`scripts/check_plugin_manifest.py`](../../scripts/check_plugin_manifest.py) as a drift check, and
   [`knowledge/decisions/plugin-distribution.md`](../../knowledge/decisions/plugin-distribution.md). Hooks stay
   repo-local, installed via `scripts/adopt.sh --with-hooks` rather than shipped inside the plugin.

17. **Bash writes to plan-required and test paths.** `require-plan.sh` and `protect-tests.sh` used to match only
    Edit/Write/MultiEdit; a Bash redirection into `src/` skipped the plan requirement locally (the chain check caught it
    at PR time). **Done:** `bash_write_targets()` and `bash_write_candidates()` moved into `_lib.sh`; both hooks walk
    the candidates on the `Bash` matcher (`knowledge/decisions/self-hooks-on.md`, `scripts/test_bash_plan_gates.py`).

18. **Pin CI dependencies and tighten the file contract.** Pin `actions/checkout`, `claude-code-action` and the
    `claude-code` npm install to exact versions or SHAs; replace the wildcard entries in `plan.md` file lists with
    explicit paths once the kit is stable (security review nits on PR #1).
    **Done (pins):** every `uses:` line carries a full commit SHA with the version as a trailing comment, the
    npm install names an exact version, and `.github/dependabot.yml` (ecosystem `github-actions`, weekly)
    proposes SHA bumps as PRs for a human to merge. **Open:** the wildcard file lists; new work items list
    exact paths, and the phase-1 plan keeps its wildcards as a record of what shipped.

19. **Windows portability of the kit's own tooling.** Found on the owner's Windows 10 PC (Git Bash, Python 3.12/3.13,
    `core.autocrlf=true`); CI on Linux is green throughout, so none of these are product defects, but a Windows
    developer cannot run the suite locally: (a) every script calls `python3`, which resolves to the Microsoft Store
    stub — use `sys.executable`/`python` fallbacks or document the shim; (b) `hooktest.py`, `test_run_evals.py` and
    the eval oracles exec `.sh` files directly and force `PATH=/usr/bin:/bin` — invoke them through `bash`;
    (c) `adopt.sh` treats `C:\...` as a relative path and writes a junk tree into the repo root; (d)
    `check_artifact_chain.py` builds `HEAD:work\<slug>\<file>` with `os.path.join`, so `git show` fails and the
    approval-author check is silently skipped locally ("approval not committed yet"); (e) the autocrlf checkout
    turned the hook scripts into CRLF files that bash cannot run — **done:** `.gitattributes` now forces LF for
    `*.sh`; (f) the hooks took `C:\...` paths as relative and allowed everything, and a missing `jq` made them allow
    blindly — **done:** `_lib.sh` handles drive-letter paths and fails closed without `jq`
    (`knowledge/decisions/gemini-hooks.md`). **Done 2026-09-03:** (b) `hooktest.py` and `test_run_evals.py` — hooks run
    through `bash`, and the sanitised PATH keeps `git` on Windows; (c) `adopt.sh` handles drive letters and refuses a
    target inside the kit, and its `Next steps` heredoc no longer executed `claude setup-token` through unquoted
    backticks (a hang on any machine with Claude Code installed, not a Windows bug); (d) the git pathspec is
    forward-slash, so the approval-author guard runs locally instead of silently skipping. `scripts/verify.sh` now ends
    with `VERIFY: PASS` on Windows. Enabling Developer Mode then made the symlink test run and **fail**, exposing a real
    bypass: `winpath()` matched only `/[a-z]/*`, so a path MSYS resolved under a named mount stayed POSIX and the guard
    read it as outside the repo — fixed to `/*`. Still open: (a) bare `python3` (moot where it resolves, a shim
    elsewhere), and one test that cannot run on Windows at all because `os.access(path, os.X_OK)` is True for every
    existing path there.

## Phase 3 — scale across agents and repos
7. **Multi-repo intent and orchestration.** One `intent.md` fanning out to several `plan.md`; worktree-per-work-item
   convention; an orchestration skill that assigns plan steps to subagents with per-step verification.
8. **Ownership and routing.** CODEOWNERS generated from a service catalog; reviewer assignment by risk tier;
   escalation when a gate sits idle beyond a band.
9. **Architecture control.** Fitness functions in `verify.sh` (dependency direction, module boundaries, public API diff)
   and an architecture-standards skill. Intent, tests, and security are controlled today; structure is not.
10. **Supply chain and provenance.** SBOM and attestations per release; a hook that requires a plan entry for any new dependency.
11. **Preview environments.** Ephemeral environment per PR that the verifier subagent can exercise, with `terraform plan`
    output attached to `plan.md` for infra changes.

## Phase 4 — the loop learns
12. **Eval-scored configuration changes.** Scoring, not only pass/fail; skill and prompt versioning with changelogs;
    A/B of skill variants on the suite.
13. **Autonomous Maintain end to end.** Detector service wired to real metrics, runbooks as skills, rollback proposals
    with the authorization file pre-filled for a human to sign, and CI that refuses an incident record without an eval.
14. **Memory decay management.** Periodic audit of `CLAUDE.md`, `GEMINI.md`, and skills against the last N PRs;
    proposes deletions; rules become hooks where possible.
15. **Compliance evidence packs.** Per release, assemble intent/spec/plan/review/authorization plus verify and eval
    outputs into a signed bundle (the Compliance API covers activity, not this chain).
16. **Human factors.** Bands on approval latency and approve-without-comment rate; reviewer rotation; one sentence of
    rationale required in `approved-by` for medium/high risk.

## Explicitly out of scope for this repo
Vendor-specific platform integrations (Jira/ServiceNow sync, IDP catalogs) are pluggable via MCP and left to each project.
