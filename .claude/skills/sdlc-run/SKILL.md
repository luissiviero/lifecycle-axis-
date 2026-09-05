---
name: sdlc-run
description: Drive a delegated work item from an approved, delegated intent to a ready pull request without stopping. Use when the intent has a delegation grant.
---
# /sdlc-run — the delegated loop

Precondition: `.sdlc/delegation.yaml` exists with `enabled: true`; `work/<slug>/intent.md` has `status: approved`
and `mode: delegated` with a `risk-class` the policy lists; `.sdlc/active` names the slug. If any fails, stop at
the first gate and say which.

1. `/sdlc-spec`, then `python3 scripts/sign.py <slug> spec.md`.
2. `/sdlc-plan`, then `python3 scripts/sign.py <slug> plan.md` (the plan gate opens on a signed plan under the grant).
3. Implement on the session's own branch, whose prefix is in `AGENT_BRANCH_PREFIXES` (`.sdlc/config.env`, for
   example `claude/`): the merge workflow refuses any other head, and `work/<slug>` stays the human's branch. Log
   a file-list or order deviation as a ledger line in the same commit, capped by the policy's `max-deviations`.
4. Run `scripts/verify.sh`, `python3 scripts/check_artifact_chain.py --base origin/main`, `scripts/run_evals.sh`,
   `python3 scripts/check_okf.py`.
5. `/sdlc-review`, with reviewer subagents run on a different model from the writer where possible. Post the
   findings as a PR comment, ending with the summary line `Important: <n> | Nits: <m>`.
6. `gh pr ready`; log `PR #<n> | draft -> in-review`. With `merge.enabled: false` in the policy this is the
   callback; otherwise the delegated-merge workflow merges when its printed conditions hold.

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
The deviation cap is reached; a `keep` verdict, or a blocking error with no consensus; a path under
`PROTECTED_PATHS`, `RELEASE_GATED_PATHS` or the policy's `locked-paths` is needed; a red check the item cannot
fix inside its plan; a hook refusal you do not understand.

## Never
Write `approved`; touch the grant keys (`mode`, `delegated-by`, `delegated-on`, `risk-class`); sign `intent.md`;
run `scripts/approve.py`; merge with `gh pr merge`; squash.
