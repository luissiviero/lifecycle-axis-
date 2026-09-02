# Phase 2+ roadmap: what the playbook leaves out

The playbook is a process skeleton. Running it on a complex project exposes gaps in seven areas. Items are ordered by
how soon a real project hits them. Each names the concrete addition to this repo.

## Phase 2 — make the loop measurable and safe to run unattended

1. **Measurement layer.** The playbook says to allocate "verification attention" and "agent budget" but defines neither.
   Add: per-work-item cost and time ledger (`work/<slug>/ledger.jsonl`: tokens, tool calls, retries, human review minutes,
   gate wait time), a `cost_per_merged_pr` band, and a weekly report. Without this, "faster" is a feeling.
2. **Risk tiering that drives automation.** "Low blast radius auto-merges, high risk needs humans" needs a computed tier,
   not a field the agent fills in. Add: `scripts/risk_tier.py` that derives the tier from touched paths, dependency graph,
   data classification, and diff size; CI attaches it to the PR; branch protection rules key off it.
3. **Database and schema safety.** Tests pass while a migration locks a table or drops a column. Add: a migration linter in
   `verify.sh` (destructive-op detection, lock analysis, reversibility check), `migrations/` in `RELEASE_GATED_PATHS`,
   and a `data-migration` standards skill.
4. **Runtime and environment visibility.** None of the artifacts let the agent see the system as it actually runs
   (staging schema, queue depth, what an upstream returns). Add: read-only MCP servers for logs, metrics, and DB schema;
   a `spec.md` section "Observed state" that must be filled from them, not from memory.
5. **Identity separation.** One agent identity creating, reviewing, and pushing defeats the gates. Add: distinct GitHub App
   identities for author and reviewer sessions, signed commits, and CI that refuses a PR approved by its own author identity.
6. **Hard checks on the soft links.** Intent → spec → plan is only checked by front matter today. Add: traceability check
   that every spec requirement cites an intent criterion and every plan step cites a spec requirement (IDs in tables),
   and an agentic "spec conformance" reviewer that fails when a requirement has no test.

## Phase 3 — scale across many agents and repos

7. **Multi-agent and multi-repo orchestration.** The playbook is single-repo, mostly single-session. Add: worktree-per-work-item
   convention, an orchestration skill that fans out `plan.md` steps to subagents with per-step verification, and a
   cross-repo intent (one `intent.md`, several `plan.md`).
8. **Ownership and routing.** "The right reviewer" is left to memory. Add: CODEOWNERS generated from a service catalog,
   reviewer auto-assignment by risk tier, and escalation paths when a gate sits idle beyond a band.
9. **Architecture control.** Intent, tests, and security are controlled; structure is not. Add: architecture fitness
   functions in `verify.sh` (dependency direction, module boundaries, public API diff) and an `architecture-standards` skill.
10. **Secrets, supply chain, and provenance.** Add: SBOM and provenance attestations per release, dependency policy as a
    hook (new dependency requires a plan entry), and secret-scanning as a required check, not only a hook.
11. **Environment and infra as artifacts.** Add: ephemeral preview environments per PR that the `verifier` subagent can hit,
    and infra changes following the same chain with `terraform plan` output attached to `plan.md`.

## Phase 4 — the loop learns

12. **Eval-driven improvement of the agents themselves.** Add: a regression suite for `CLAUDE.md`/skills/hooks with scoring,
    run on every change to them; prompt and skill versioning with changelogs; A/B of skill variants on the eval set.
13. **Maintain that is actually autonomous.** Bands and Claude Tag first-response are named, not built. Add: the detector
    service, runbooks as skills, automated rollback proposals with the authorization file pre-filled for a human to sign,
    and incident → eval → intent enforced by CI (an incident record without an eval fails).
14. **Knowledge decay management.** `CLAUDE.md` and skills go stale. Add: a periodic "memory audit" routine that checks
    every rule against the last N PRs and proposes deletions; hooks replace rules where possible (rule becomes code).
15. **Compliance evidence packs.** Regulated teams need the audit trail exported. Add: a script that assembles, per release,
    the intent/spec/plan/review/authorization chain plus verify and eval outputs into a signed bundle.
16. **Human factors.** Gate fatigue and rubber-stamping. Add: bands on approval latency and approval-without-comment rate,
    reviewer rotation, and a rule that a human must write one sentence of rationale in `approved-by` for high-tier items.

## Explicitly out of scope for this repo
Vendor-specific platform integrations (Jira/ServiceNow sync, IDP catalogs) are pluggable via MCP and left to each project.
