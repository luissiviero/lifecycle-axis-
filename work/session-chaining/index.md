---
type: sdlc/work-item
id: session-chaining
title: The kit never says who manages session context, so the owner has been doing it by hand
description: "One session per work item is the protocol the owner chose, but nothing in the kit writes it down or acts on it: sdlc-run's advance step does not open the next session, the handoff carries no protocol, and two skills give instructions that are wrong or incomplete against the repository as it stands."
timestamp: 2026-09-13T22:40:00Z
---
# The kit never says who manages session context, so the owner has been doing it by hand

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; One session per work item is the protocol the owner chose, but nothing in the kit writes it down or acts on it: sdlc-run's advance step does not open the next session, the handoff carries no protocol, and two skills give instructions that are wrong or incomplete against the repository as it stands.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; Names the one-session-per-work-item protocol in the handoff and in sdlc-run, makes the finishing session schedule the next one where its runtime can and say so where it cannot, and fixes three places where kit documentation instructs an act the repository's own checks refuse.
- [plan.md](plan.md) — status: approved; approved-by: luissiviero; One pull request of instructions and documentation: the chaining act in sdlc-run, the protocol and seed prompt in the handoff, the two skill corrections, one rendered pointer line paid for by re-flow, and a hook-kind eval case that is red on main today.

Last gate: - 2026-09-13T23:30:00Z | PR #76 | draft -> in-review | claude | 21ecfa8 | two reviews on sonnet over the Build diff. Security: no blocking, major or minor finding; R9 reproduced empty, no sentence in the new text grants an act the hooks or the merge script refuse, the cap reads as at-finish-never-at-start in both files, and R10's context-never-authority clause is present everywhere the prompt appears. Conformance: clean on all ten rows, every today-baseline re-run against origin/main and matching, the three negated eval assertions shown to be exercised rather than vacuous; three nits, one taken: step 3's one-pull-request rule now names the handoff-only pull request of step 7(c) beside the intent-only one, so the skill agrees with itself. Not taken: the re-flowed approval bullet is judged terser but whole, and the PR #59 and #62 claims in the Task state are unverifiable from a container without gh, which is the state the handoff already records. Marked ready; the owner's click is the merge, and no pointer moves. Writer fable, reviewers sonnet
