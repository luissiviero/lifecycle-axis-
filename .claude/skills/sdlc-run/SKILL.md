---
name: sdlc-run
description: Drive every granted work item from an approved, delegated intent to a merged pull request without stopping, advancing to the next queued item on each merge. Use when at least one intent has a delegation grant.
---
# /sdlc-run — the delegated loop

Precondition: `.sdlc/delegation.yaml` exists with `enabled: true`; `work/<slug>/intent.md` has `status: approved`
and `mode: delegated` with a `risk-class` the policy lists; `.sdlc/active` names the slug. If any fails, stop at
the first gate and say which.

Missing the grant is the common failure, and it is one tap to fix: ask the owner to run
**Actions -> approve -> Run workflow** (`.github/workflows/approve.yml`) with `slug` = the item, `artifact` = `intent.md`, `mode` = `delegated`,
from the default branch (the workflow refuses a grant on any other ref). Then wait. Naming the inputs is not
approving; the run records who pressed Run, and that record is what the chain check and the merge script verify.

**The queue.** The owner grants N intents up front, one tap each, and this runs them in order without
coming back for anything. Before starting, print the queue so the owner knows what will happen before
they leave: `python3 scripts/next_item.py --list` — earliest `delegated-on` first, ties by slug. Steps
1-6 are one item; step 7 is what makes it a queue.

1. `/sdlc-spec`, then `python3 scripts/sign.py <slug> spec.md`.
2. `/sdlc-plan`, then `python3 scripts/sign.py <slug> plan.md` (the plan gate opens on a signed plan under the grant).
3. Implement on the session's own branch, whose prefix is in `AGENT_BRANCH_PREFIXES` (`.sdlc/config.env`, for
   example `claude/`): the merge workflow refuses any other head, and `work/<slug>` stays the human's branch. Log
   a file-list or order deviation as a ledger line in the same commit, capped by the policy's `max-deviations`.
4. Run `scripts/verify.sh`, `python3 scripts/check_artifact_chain.py --base origin/main`, `scripts/run_evals.sh`,
   `python3 scripts/check_okf.py`.
5. `/sdlc-review`, with reviewer subagents run on a different model from the writer where possible. On a
   delegated item that skill posts the findings with the summary line `Important: <n> | Nits: <m>`, runs
   `gh pr ready` and logs `PR #<n> | draft -> in-review`; do not repeat those here.
6. The ready pull request is the callback when the policy has `merge.enabled: false`; otherwise the
   delegated-merge workflow merges when its printed conditions hold.
7. **Advance.** Subscribe to the pull request you opened (`subscribe_pr_activity`) and stay on it: answer its
   review findings and CI until it merges. On the merge, the workflow has already moved `.sdlc/active` to the
   next queued item and written a ledger line on both items — you do not move the pointer, and an item's own
   pull request may never contain `.sdlc/active` (`ALWAYS_LOCKED`). Re-read `.sdlc/active` from `main`: when it
   names a different granted, unstarted item, reset your branch onto `main` and go to step 1 for that item,
   without asking the owner for anything. When it is empty, the queue is done — say so once and stop.
   If the session ends mid-queue, nothing is lost: the pointer on `main` is already correct, so the next
   session resumes at the right item with no repair.

## The revision rule
A plan revision is the last resort. A file-list or order deviation is logged as today plus a ledger line, capped
by the policy's `max-deviations`. Anything else (a step dropped or added, an acceptance test changed, a different
approach, a spec requirement touched) needs a critical, blocking error or finding as its trigger and a committed
consensus record `work/<slug>/revisions/<n>.md`: the trigger with evidence, the proposal, and one
`## Reviewer: <role> (<model>)` section per `min-reviewers` from the policy (`plan-reviewer` and
`security-reviewer`, run on a different model from the writer where possible), each ending `verdict: revise`.
Only a unanimous `revise` allows the agent to edit the artifact and re-sign it with `scripts/sign.py --revision`.
Any `keep`, too few reviewers, or a blocked plan with no consensus means stop and call the owner back with the
record.

## Stop and call the owner back
Each of these stops the **whole queue**, not just the item: say which item and why, once, and do not start the
next one. The deviation cap is reached; a `keep` verdict, or a blocking error with no consensus; a path under
`PROTECTED_PATHS`, `RELEASE_GATED_PATHS` or the policy's `locked-paths` is needed; a red check the item cannot
fix inside its plan; a hook refusal you do not understand. Two more end the queue quietly rather than badly:
the queue is empty (`next_item.py` exits 3), and a pull request that needs the owner's merge click — a
locked-path item never merges on its own, so no advance follows it and the queue ends there. Tell the owner to
grant such items last.

## Never
Write `approved`; touch the grant keys (`mode`, `delegated-by`, `delegated-on`, `risk-class`); sign `intent.md`;
run `scripts/approve.py`; merge with `gh pr merge`; squash; write `.sdlc/active` yourself — the merge workflow
moves it, and a queue of N items is N human grants, never one grant for N.
