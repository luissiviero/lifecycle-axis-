---
type: sdlc/log
id: approve-tap-regenerates-index-log
title: Gate ledger for approve-tap-regenerates-index
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-08T21:50:00Z
---
# Log: approve-tap-regenerates-index

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-08T21:50:00Z | intent.md | (none) -> in-review | claude | d5da45f | drafted from the owner's report and the three tap commits on main (a903a91, 3da8bb6, c0aa58c), each of which committed the artifact, log.md and .sdlc/active and no index; gen_index.py --check on c0aa58c reports work/run-queue-followups/index.md and work/index.md drifted, and approve_dispatch.py's allowlist documents a regeneration nothing runs. Two questions for the owner, answered as proposals: where the regeneration lives, and what the tap does about drift it may not commit. This pull request cannot carry work/run-queue-followups/index.md without leaving in-progress mode, so that drift stays on main until that item's next commit or the owner regenerates
- 2026-09-08T22:35:00Z | intent.md | in-review -> in-review | claude | 3ad6788 | the owner answered both questions, choosing a run that goes as long as possible without their input: the regeneration lives inside approve_dispatch.py --commit, not in the workflow, so the item touches no protected or locked path and a delegated run can carry it from grant to merge; and a tap commits every index it regenerates, other items' included, with the allowlist widened to work/*/index.md and work/index.md under its own test, so a tap heals drift on main instead of refusing on it or leaving it there. Affected systems, constraints and the risk class rewritten to match; nothing else in the intent changed

- 2026-09-14T01:33:20Z | intent.md | in-review -> approved | luissiviero | b30feff | mode: delegated
- 2026-09-14T02:43:57Z | spec.md | in-review -> delegated | claude | 864923e | designed from the owner's two answers in the intent: regeneration inside --commit via gen_index.render_all, every regenerated index committed, allowlist widened to the generated paths under six new committer cases; sign.py and the grant untouched
- 2026-09-14T02:46:42Z | plan.md | in-review -> delegated | claude | e5ec667 | two code files and the item's own artifacts; six new committer cases, three to be seen red before the code; kind feature so the existing test file stays editable
- 2026-09-14T02:52:00Z | plan.md | delegated -> delegated | claude | e11300c | deviation: step 1 predicted three red cases before the code and found four; test_index_only_changes_do_not_make_a_commit is red too because the spec's R-8 stdout assertion sits inside it and nothing prints before the code exists. Plan miscount, spec unchanged, no case edited, one more case proven to exercise the change. 1 of 5
- 2026-09-14T03:05:00Z | plan.md | delegated -> delegated | claude | f8b0e1d | deviation: the build commit 98daa7c corrected the signed spec's design step 4 (the index-only refusal stages nothing, as R-5's acceptance test requires) and the deviation entry written beside it said the spec did not change; logged now as the plan pass asked. 2 of 5
