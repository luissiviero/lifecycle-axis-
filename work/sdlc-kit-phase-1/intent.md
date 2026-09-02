---
type: sdlc/intent
id: sdlc-kit-phase-1
title: Make lifecycle-axis a reusable AI-native SDLC kit for Claude + Gemini projects
description: Turn the scaffold into a drop-in kit with an OKF knowledge layer and model-neutral gates.
stage: plan
status: in-review
author: Luis Siviero (repo owner), drafted with Claude
approved-by:
approved-on:
supersedes:
record:
resource: https://claude.com/blog/the-ai-native-sdlc-playbook
tags: [sdlc, okf, claude, gemini]
timestamp: 2026-09-02T18:00:00Z
---
# Intent: make lifecycle-axis a reusable AI-native SDLC kit for Claude + Gemini projects

## Problem
Complex projects use both Claude and Gemini. Process controls (plan-before-code, review evidence, release gates) are
re-invented per project and enforced by habit, and institutional knowledge drifts between CLAUDE.md and GEMINI.md.

## Proposed outcome
- A new project can adopt the kit in under an hour and the loop runs by hand end to end.
- The deterministic gates hold regardless of which model produced the change (CI and branch protection, not only hooks).
- Institutional knowledge lives once, in an OKF bundle, read by both models.

## Affected users and systems
- Users: the owner; future collaborators; Claude Code and Gemini sessions.
- Services / repos / data: this repo; each product repo that adopts it; CI (GitHub Actions).

## Constraints
- Must: keep the playbook's eight hard rules; keep CLAUDE.md and GEMINI.md to one page each; no secrets in the repo.
- Must not: require a paid platform for the core loop; make OKF conformance a hard gate before its spec stabilises.
- Out of scope: Jira/ServiceNow sync; vendor catalogs; production deploy tooling for specific clouds.

## Risk class
low — process and documentation, plus scripts with unit tests. No production systems.

## Open questions (answered by the owner before spec)
- Q: Which stacks and commands? (languages; build/test/lint commands per repo; test-file naming; formatter)
  A: Per repo, one `scripts/verify.sh` reading `VERIFY_CMDS`/`FORMAT_CMD`/`TEST_FILE_GLOBS` from `.sdlc/config.env`; the adopt script leaves `VERIFY_CMDS` as a TODO for the adopter rather than guessing.
- Q: Repo topology? (monorepo vs many repos; are `src lib app services packages` the right plan-required paths; where the intent home lives)
  A: `work/<slug>/` inside each product repo; the plan-required paths default stays and is edited per repo; intent home is `work/`.
- Q: Which Gemini surface and for which stages? (Gemini CLI, Antigravity, Vertex agents; does it read GEMINI.md/AGENTS.md; does it support hooks)
  A: Gemini CLI for interactive work, reading `GEMINI.md` generated from the same rule source as `CLAUDE.md`; enforcement parity is not assumed, CI is the hard gate (see spike docs/sdlc/spikes/gemini-parity.md).
- Q: Who approves what? (GitHub handles for product owner, tech lead, release manager; is the owner all three for now)
  A: luissiviero holds product-owner, tech-lead, release-manager and service-owner (`.sdlc/approvers.yaml`); agents act under a separate bot/App identity that can never approve; branch protection requires one human review.
- Q: Deploy targets and environments? (commands to match in the production gate; dev/staging/prod; rollback command)
  A: Deploy only from CI via GitHub Environments with required reviewers (`deploy.yml`); agents never run deploy commands; the production-gate hook stays as defence in depth; rollback is the pre-approved runbook `knowledge/runbooks/rollback-deploy.md`.
- Q: Legacy source of truth? (Jira/Linear/none; linkage or repo as source of truth)
  A: The repo. No ticket tool in the loop; `record:` stays optional.
- Q: Metrics store for bands and CI budget? (GitHub-only for now; Prometheus; is an ANTHROPIC_API_KEY available in CI for evals and triage)
  A: GitHub only (Actions API, PR metadata) via `scripts/github_metrics.py`; an `ANTHROPIC_API_KEY` with a console spend limit is added to CI so prompt evals and triage run.
- Q: Claude platform features in use? (Enterprise managed settings, Claude Tag in Slack, Claude Security, private plugin marketplace)
  A: Team/Pro: repo-level hooks, `claude-code-action` for PR review driven by `REVIEW.md`; no managed settings, Claude Tag or Claude Security in this phase.
- Q: OKF today? (existing bundles or Knowledge Catalog; shared `knowledge/` bundle vs per-repo)
  A: None yet. Start a `knowledge/` bundle per repo, conformance check as a warning, both models read it.
- Q: Distribution? (template repo, plugin, or both)
  A: Both: a Claude Code plugin (skills, agents, hooks, templates) plus this repo as the thin template with `scripts/adopt.sh`.
status: approved
approved-by: luissiviero
approved-on: 2026-09-02
