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

