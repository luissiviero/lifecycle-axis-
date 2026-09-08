---
type: sdlc/rule-fragment
title: The artifact chain
description: Header and artifact-chain rules rendered into every context file.
targets: [claude, gemini, agents]
order: 0
tags: [rules, context-files, chain]
timestamp: 2026-09-05T01:26:09Z
---
# Repository memory (keep to ~1 page)

This repo is a starter kit for the AI-native SDLC: six non-linear stages
(Plan → Design → Build → Test → Deploy → Maintain) connected by committed
Markdown artifacts. Read `docs/sdlc/README.md` once; then follow the rules below.

## The artifact chain (never skip a link)
intent.md → spec.md → plan.md → diff + tests → PR + review findings → incident record → new intent.md

Each work item lives in `work/<slug>/` and holds `intent.md`, `spec.md`, `plan.md` (and later `incident.md`).
Every artifact has YAML front matter with `status` (`draft` | `in-review` | `approved` | `delegated` |
`superseded`) and `approved-by`. Only a human sets `status: approved`; a hook refuses it from an agent. An
agent may set `delegated` only under a human's delegation grant on the intent (`.sdlc/delegation.yaml`). The
active work item is named in `.sdlc/active`; when an item completes, a human retires it (`superseded` on its
artifacts, a ledger line each, the pointer cleared or moved to the next item) and a retired plan closes the gate.
