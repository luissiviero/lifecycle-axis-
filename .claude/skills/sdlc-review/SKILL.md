---
name: sdlc-review
description: Deploy stage. Review a diff or PR against plan.md, spec.md, REVIEW.md and the security standards; run the security-reviewer subagent; produce findings in REVIEW.md format. Use before requesting human review or when asked to review.
---
# /sdlc-review — layered agentic review

1. Determine the work item (`.sdlc/active` or `Work-Item:` in the PR body). Read plan.md, spec.md, REVIEW.md.
2. Run `python3 scripts/check_artifact_chain.py` and `scripts/verify.sh`. Quote both final lines.
3. Review in the order REVIEW.md prescribes. Delegate the security pass to the `security-reviewer` subagent and the plan-conformance pass to the `plan-reviewer` subagent; merge their evidence-backed findings, drop anything without `file:line`.
4. Output findings exactly in REVIEW.md's format. Max five minor comments.
5. If the change touches `RELEASE_GATED_PATHS`, state the named human owner who must approve. Never approve those yourself.
6. If the same class of mistake appeared in a previous review of this repo, add a line to CLAUDE.md "Lessons learned" in this PR.
