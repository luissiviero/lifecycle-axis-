---
type: index
title: Knowledge bundle
description: Entry point to the model-neutral OKF knowledge bundle — institutional knowledge that CLAUDE.md and GEMINI.md point into instead of restating.
tags: [okf, index, knowledge]
timestamp: 2026-09-02T16:18:39Z
---

# Knowledge bundle

This directory is an [Open Knowledge Format](../docs/sdlc/okf-pairing.md) bundle: one concept per file, front matter
with a required `type`, path as identity, Markdown links as the graph. Both Claude Code and Gemini CLI read this
bundle — `CLAUDE.md` and `GEMINI.md` stay one page each and link into it rather than restating what lives here, per
`docs/sdlc/okf-pairing.md`. Conformance is checked by `scripts/check_okf.py` (warning by default; strict in CI once
promoted, see `.sdlc/config.env`'s `OKF_STRICT`).

## Subdirectories

- [`decisions/`](decisions/index.md) — architecture/process decisions with accepted alternatives and consequences.
  Read when you need to know *why* something is built the way it is, or before proposing a change that would
  contradict a standing decision.
- [`lessons/`](lessons/index.md) — post-mortem lessons linked to the incident that produced them. Read during
  `/sdlc-incident` and `/sdlc-review` to check whether a mistake has happened before.
- [`runbooks/`](runbooks/index.md) — pre-approved operational procedures an agent may *propose* but never run
  unattended. Read when a control band breaches or an incident needs a known-safe recovery path.
- [`metrics/`](metrics/index.md) — one definition per metric named in `monitoring/bands.yaml`: what it measures, its
  source command, baseline window, and tiers. Read when interpreting a band breach or wiring up a new metric.
- [`services/`](services/index.md) — one concept file per service/table once this project has more than one service.
  Read when working across a service boundary. Empty today.

## Work items vs. knowledge

`work/<slug>/` is the artifact chain for one change (intent → spec → plan → diff → review → incident) and is also an
OKF bundle, but it is time-bound to that change. `knowledge/` is durable: it outlives any single work item and is
where a decision, lesson, runbook, or metric definition goes once it applies beyond the item that produced it.
