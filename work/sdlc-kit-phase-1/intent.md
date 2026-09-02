---
type: sdlc/intent
id: sdlc-kit-phase-1
title: Make lifecycle-axis a reusable AI-native SDLC kit for Claude + Gemini projects
description: Turn the scaffold into a drop-in kit with an OKF knowledge layer and model-neutral gates.
stage: plan
status: draft
author: Luis Siviero (repo owner), drafted with Claude
approved-by:
approved-on:
supersedes:
record:
resource: https://claude.com/blog/the-ai-native-sdlc-playbook
tags: [sdlc, okf, claude, gemini]
timestamp: 2026-09-02T00:00:00Z
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
  A:
- Q: Repo topology? (monorepo vs many repos; are `src lib app services packages` the right plan-required paths; where the intent home lives)
  A:
- Q: Which Gemini surface and for which stages? (Gemini CLI, Antigravity, Vertex agents; does it read GEMINI.md/AGENTS.md; does it support hooks)
  A:
- Q: Who approves what? (GitHub handles for product owner, tech lead, release manager; is the owner all three for now)
  A:
- Q: Deploy targets and environments? (commands to match in the production gate; dev/staging/prod; rollback command)
  A:
- Q: Legacy source of truth? (Jira/Linear/none; linkage or repo as source of truth)
  A:
- Q: Metrics store for bands and CI budget? (GitHub-only for now; Prometheus; is an ANTHROPIC_API_KEY available in CI for evals and triage)
  A:
- Q: Claude platform features in use? (Enterprise managed settings, Claude Tag in Slack, Claude Security, private plugin marketplace)
  A:
- Q: OKF today? (existing bundles or Knowledge Catalog; shared `knowledge/` bundle vs per-repo)
  A:
- Q: Distribution? (template repo, plugin, or both)
  A:
