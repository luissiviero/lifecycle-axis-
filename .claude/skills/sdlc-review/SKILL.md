---
name: sdlc-review
description: Deploy stage. Review a diff or PR against plan.md, spec.md, REVIEW.md and the security standards; run the security-reviewer subagent; produce findings in REVIEW.md format. Use before requesting human review or when asked to review.
---
# /sdlc-review — layered agentic review

1. Determine the work item (`.sdlc/active` or `Work-Item:` in the PR body). Read plan.md, spec.md, REVIEW.md.
2. Run `python3 scripts/check_artifact_chain.py` and `scripts/verify.sh`. Quote both final lines.
3. Review in the order REVIEW.md prescribes. Delegate the security pass to the `security-reviewer` subagent and the plan-conformance pass to the `plan-reviewer` subagent; merge their evidence-backed findings, drop anything without `file:line`.
4. Output findings exactly in REVIEW.md's format, ending with the summary line `Important: <n> | Nits: <m>`. Max
   five minor comments. Mark the pull request ready (`gh pr ready`) and log `PR #<n> | draft -> in-review` in
   log.md on every item; this is the click that buys the gate and the review run, so it comes after the local
   checks are green. When the item is delegated, also post the findings as a PR comment.
   If the ready gate goes red for a reason you cannot diagnose from its log, ask the owner to apply the
   `triage` label and wait. Never apply it yourself: the label spends model time on a judgment step, and that
   spend is the owner's decision. A green re-run on the same sha does not clear the red one for
   `scripts/delegated_merge.py`: it keeps every failed run of a required workflow on that sha, so the merge
   waits on a push, not on a re-run. Fix the cause and push.
5. If the change touches `RELEASE_GATED_PATHS`, state the named human owner who must approve. Never approve those yourself.
6. If the same class of mistake appeared in a previous review of this repo, add a line to CLAUDE.md "Lessons learned" in this PR.
