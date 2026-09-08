---
type: sdlc/log
id: run-queue-log
title: Gate ledger for run-queue
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-08T15:35:00Z
---
# Log: run-queue

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-08T15:35:00Z | intent.md | (none) -> in-review | claude | d1efd89 | drafted from the owner's statement of the objective (two distinct modes; delegated means hours away with every input at the start) and the lifecycle facts measured while shipping work/retire-active-pointer: a run ends at one ready pull request, the merge writes nothing back, every grant tap repoints .sdlc/active at one item, so one tap buys one item; four questions answered as proposals for the owner to edit or accept
- 2026-09-08T16:46:50Z | intent.md | in-review -> approved | luissiviero | 79e9a30 | mode: delegated
- 2026-09-08T16:54:10Z | spec.md | in-review -> delegated | claude | 3da8bb6 | six requirements from the delegated intent and an explorer pass; the advance is a write-back in delegated_merge.py after the merge, on main's checkout, because an item's own pull request may never contain .sdlc/active (ALWAYS_LOCKED) and the merge workflow already checks out main with contents write; next_item.py fixes a total order; the loop's wake is a skill instruction, flagged as C1; ten gotchas, three concerns
- 2026-09-08T16:55:23Z | plan.md | in-review -> delegated | claude | 5ff9f5d | fourteen files, six steps, tests first for R-1 and R-2; the advance is additive and runs after the merge call so it cannot cause a wrong merge; run() gains root as a keyword with a default so the 111 existing cases keep working; no PROTECTED_PATHS touched, so no control-plane label -- the owner's merge click only
- 2026-09-08T17:20:00Z | plan.md | delegated -> delegated | claude | b144c55 | deviation: step 4's eval reported a pass while testing nothing -- run_evals.sh ends a block-scalar key at the first unindented line and a blank line is unindented, so every assertion below the first blank was dead text. Second oracle in this repository written so it could not fail, so rule 7 applies: the lesson, its pointer line, and CaseBlocksAreWhole in test_run_evals.py are in the same diff; the eval is mutation-tested three ways
- 2026-09-08T17:22:00Z | plan.md | delegated -> delegated | claude | b144c55 | deviation: two files added to the list after the plan-conformance pass found them unlisted -- docs/sdlc/rules/30-conventions.md, one paragraph re-flowed six lines to five because the new lesson pointer put the adopter's CLAUDE.md at 121 of 120, and work/retire-active-pointer/revisions/index.md, an OKF warning this session left on main in pull request 53
- 2026-09-08T17:25:01Z | spec.md | delegated -> delegated | claude | b144c55 | revision 1: R-3's ledger actor and the Interfaces shape corrected to github-actions[bot], the identity that makes the commit; the failure-modes paragraph now credits the non-forced push rather than a pointer re-read that cannot fire through run(); the oracle asserts the literal string instead of the code's own constant
