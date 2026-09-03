---
type: index
title: SDLC Spikes
description: Design spikes and investigation documents for SDLC enhancements.
tags: [sdlc, spikes, design]
timestamp: 2026-09-02T20:00:00Z
---

Every spike carries `status:` in its front matter, one of three words:
`open` (written up, no owner decision yet) | `accepted` (the owner accepted the design; implementation is a
separate, unscheduled decision) | `decided` (settled, and the consequence is built or recorded in
`knowledge/decisions/`). Before 2026-09-03 this field also held `proposed` and `in-review`; both meant `open`
and were folded into it.

[build-stage-from-claude-agents.md](build-stage-from-claude-agents.md) — What to borrow from the retired claude-agents repo for the Build stage (/sdlc-build skill, plan-template lines, review caps, hand-off file) and what to leave behind.

[gemini-parity.md](gemini-parity.md) — Investigation into achieving parity between Claude and Gemini SDLC enforcement.

[plugin-packaging.md](plugin-packaging.md) — Design spike for plugin packaging and distribution.

[pr-review-identity.md](pr-review-identity.md) — Analysis of PR review identity and approval mechanisms.

[prompt-surfaces.md](prompt-surfaces.md) — How the Claude platform prompting and guardrail docs become one standard, a lint, templates, evals and a review pass; alternatives discarded, deferred and ruled out of scope at the end.

[red-team-pass.md](red-team-pass.md) — Evaluation of an adversarial red-team pass as an opt-in step in `/sdlc-spec`; open, nothing implemented.
