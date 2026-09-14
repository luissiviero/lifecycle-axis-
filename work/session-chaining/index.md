---
type: sdlc/work-item
id: session-chaining
title: The kit never says who manages session context, so the owner has been doing it by hand
description: "One session per work item is the protocol the owner chose, but nothing in the kit writes it down or acts on it: sdlc-run's advance step does not open the next session, the handoff carries no protocol, and two skills give instructions that are wrong or incomplete against the repository as it stands."
timestamp: 2026-09-13T22:40:00Z
---
# The kit never says who manages session context, so the owner has been doing it by hand

- [intent.md](intent.md) — status: superseded; approved-by: luissiviero; One session per work item is the protocol the owner chose, but nothing in the kit writes it down or acts on it: sdlc-run's advance step does not open the next session, the handoff carries no protocol, and two skills give instructions that are wrong or incomplete against the repository as it stands.
- [spec.md](spec.md) — status: superseded; approved-by: luissiviero; Names the one-session-per-work-item protocol in the handoff and in sdlc-run, makes the finishing session schedule the next one where its runtime can and say so where it cannot, and fixes three places where kit documentation instructs an act the repository's own checks refuse.
- [plan.md](plan.md) — status: superseded; approved-by: luissiviero; One pull request of instructions and documentation: the chaining act in sdlc-run, the protocol and seed prompt in the handoff, the two skill corrections, one rendered pointer line paid for by re-flow, and a hook-kind eval case that is red on main today.

Last gate: - 2026-09-14T00:00:00Z | plan.md | approved -> superseded | luissiviero | 623604e | retired with the intent
