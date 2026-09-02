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
   Gemini hook wiring remains — see the item below.
   - **New: Gemini `BeforeTool` hook wiring.** Wire `.gemini/settings.json` reusing the same hook scripts, after
     verifying Gemini's `tool_input` keys (see the UNVERIFIED notes in
     [`docs/sdlc/spikes/gemini-parity.md`](spikes/gemini-parity.md)).

## Phase 2 — measurable, safe to run unattended
1. **Cost and budget attribution.** The playbook names "agent budget" and reads timings from git and OTel but never
   attributes spend. Add a per-work-item ledger (tokens, tool calls, retries, human review minutes, gate wait) and a
   `cost_per_merged_pr` control band.
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

17. **Bash writes to plan-required and test paths.** `require-plan.sh` and `protect-tests.sh` still match only
    Edit/Write/MultiEdit; a Bash redirection into `src/` skips the plan requirement locally (the chain check catches it
    at PR time). Reuse `bash_write_targets()` from `protect-paths.sh` in both hooks.

18. **Pin CI dependencies and tighten the file contract.** Pin `actions/checkout`, `claude-code-action` and the
    `claude-code` npm install to exact versions or SHAs; replace the wildcard entries in `plan.md` file lists with
    explicit paths once the kit is stable (security review nits on PR #1).

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
