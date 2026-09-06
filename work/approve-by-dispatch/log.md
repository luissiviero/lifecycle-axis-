---
type: sdlc/log
id: approve-by-dispatch-log
title: Gate ledger for approve-by-dispatch
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-06T02:05:00Z
---
# Log: approve-by-dispatch

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | 72bf0ef | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-06T02:05:00Z | intent.md | (none) -> in-review | claude | 15424e0 | drafted from the owner's request in the session that closed work/delegated-mode ("give permission for the AI to change from one mode to the other when I request, without doing everything manually, for both modes"); five questions answered as proposals for the owner to edit or accept
- 2026-09-06T02:30:00Z | intent.md | in-review -> approved | luissiviero | 4ee5ffc | approved from the GitHub web editor
- 2026-09-06T15:41:47Z | spec.md | (none) -> in-review | claude | 47be4b7 | twelve requirements with oracles, from the approved intent and an explorer pass over approve.py, the chain check, the merge script, the workflows and the production gate; six decisions, five concerns, the trailer design that makes a dispatch verifiable
- 2026-09-06T16:10:00Z | spec.md | in-review -> in-review | claude | 47dbbe8 | revised for the reviewer's two findings on pull request 48: R-7 restructured into two grant routes, the signature gate moved inside route A where its own early return had made a dispatch-made commit unreachable, and R-13 added for the actions read scope and token sdlc-gate.yml needs; now thirteen requirements, seven decisions, six concerns
- 2026-09-06T16:20:00Z | spec.md | in-review -> approved | luissiviero | 82537ce | approved from the GitHub web editor
- 2026-09-06T17:00:00Z | intent.md | approved -> approved | luissiviero | 72bf0ef | mode: delegated
- 2026-09-06T17:49:06Z | plan.md | in-review -> delegated | claude | bf15030 | file list and eleven steps from the approved spec; step 1's D7 measurement done first from this repository's own history (%G? E on the GitHub-made 72bf0ef/bf15030, N on the git-pushed 82537ce/47dbbe8/c62bfe1), so mechanism 1 is forced and route B drops the signature condition, closing C6
- 2026-09-06T19:05:00Z | plan.md | delegated -> delegated | claude | ba4227f | deviation: step 1 measured D7 from this repository's own history rather than by the throwaway dispatch spec.md's D7 names; that dispatch is not performable before approve.yml is on a ref, and R-9 forbids this session pressing Run. Conclusion unchanged and independently re-verified in the pull request 51 plan-conformance pass; the owner may want to amend D7, which is a spec edit only they can make
- 2026-09-06T19:20:00Z | PR #51 | draft -> in-review | claude | ddac58a | review posted: six Important findings from the security and plan-conformance passes, all fixed with a regression test each; VERIFY: PASS (ddac58a), CHAIN: PASS, EVALS: 42 pass 0 fail, OKF: 0 warnings
- 2026-09-06T19:45:00Z | plan.md | delegated -> delegated | claude | 7fab063 | deviation: file list gains knowledge/lessons/tests-carry-their-own-environment.md, knowledge/lessons/index.md and docs/sdlc/rules/60-lessons.md under rule 7, after the same class of mistake (a test reading the ambient environment) appeared twice in this pull request: a bare git commit with no identity, red in CI on ddac58a, and an unnormalised header timestamp found by the review
