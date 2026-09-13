---
type: sdlc/work-item
id: session-chaining
title: The kit never says who manages session context, so the owner has been doing it by hand
description: "One session per work item is the protocol the owner chose, but nothing in the kit writes it down or acts on it: sdlc-run's advance step does not open the next session, the handoff carries no protocol, and two skills give instructions that are wrong or incomplete against the repository as it stands."
timestamp: 2026-09-13T16:30:00Z
---
# The kit never says who manages session context, so the owner has been doing it by hand

- [intent.md](intent.md) — status: in-review; approved-by: ; One session per work item is the protocol the owner chose, but nothing in the kit writes it down or acts on it: sdlc-run's advance step does not open the next session, the handoff carries no protocol, and two skills give instructions that are wrong or incomplete against the repository as it stands.

Last gate: - 2026-09-13T16:30:00Z | intent.md | (none) -> in-review | claude | 6cd63b1 | drafted from the owner's two questions during the ci-budget execution session, quoted verbatim, and from the three defects the mock walk of 2026-09-11 found, each re-verified against main at 6cd63b1 before being written down. Defect 2 is worse than the mock walk recorded: sdlc-review does not merely name a CLAUDE.md section that no longer exists, it tells the agent to edit CLAUDE.md at all, which is a generated file whose hand-edit context-drift.sh fails. Defect 3 confirmed by count: sdlc-intent carries zero mentions of log.md or gen_index.py, so an item created by following it literally has no ledger and drifts the index. Three open questions carried for the owner, the first of which decides whether this stays a documentation item at risk-class low or becomes a mechanism and is re-examined. This ledger and the index regeneration are themselves the behaviour defect 3 is about, done here by hand because the skill does not yet ask for them. Writer opus
