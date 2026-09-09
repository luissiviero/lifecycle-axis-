---
type: sdlc/log
id: ci-budget-log
title: Gate ledger for ci-budget
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-09T09:10:00Z
---
# Log: ci-budget

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-09T09:10:00Z | intent.md | (none) -> in-review | claude | 603695b | drafted from the owner's three goals (fewer GitHub minutes, less waiting, fewer wasted tokens; keep the crucial procedures, loosen the rest) and the Actions run history: the quota block at 2026-09-08 21:43 UTC after 1,124 runs, the approve tap that died in 3 seconds behind it, a 5m54s claude -p triage on every red gate (pull requests 59-61 each paid it for a drift already on main), the agent-evals PR job repeating what verify.sh ran, delegated-merge waking on a workflow the policy no longer requires, and 89 of 96 gate runs superseded by a later push; six questions answered as proposals for the owner to edit or accept
- 2026-09-09T09:40:00Z | intent.md | in-review -> in-review | claude | 3cdf708 | open questions answered by the owner: skip the gate on drafts entirely; triage behind a `triage` label; "require branches to be up to date" off with "one agent code pull request open at a time" as the compensating control; the reviewer's model unchanged until measured; the review-comment question closed by reading the code (check_review already binds to the newest successful run, delegated_merge.py:605-610); the measure is a series named actions_minutes_per_pr. Two questions added and answered: the superseded-run rule in delegated_merge.py (a skipped or cancelled run is ignored only when a later run of the same workflow on the same head sha succeeded — without it every pull request that was ever a draft is unmergeable at its ready sha), and the four delivery answers (repository goes public after a fork pull-request pass and a history scan; two pull requests, control plane first; sonnet writes, opus reviews, fable checks divergence; the agent writes the workflow diff under the unlock and the owner labels). Exploration on sonnet (three read-only scouts), design pass on opus; implementation-plan.md carries the exact diffs, the verification commands and the acceptance numbers
