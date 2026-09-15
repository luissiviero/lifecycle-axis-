---
type: sdlc/log
id: risk-detour-log
title: Gate ledger for risk-detour
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-08T20:31:02Z
---
# Log: risk-detour

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-08T20:31:02Z | intent.md | (none) -> in-review | claude | 52ffb04 | drafted from the owner's statement (delegated stays low-only; on non-low work look for a low-only route by reviewer consensus instead of stopping) and the owner's three decisions in the same session (two items, the detour at every gate including mid-build, park and continue); measured: five terminal admission checks, the run skill's stop-the-queue rule, a revision record that asks the wrong question, a queue rule that would re-offer a parked item; five questions answered as proposals for the owner
- 2026-09-08T21:35:56Z | intent.md | in-review -> in-review | claude | 81c2f0e | open questions answered by the owner: every proposal accepted as written
- 2026-09-14T05:26:38Z | intent.md | in-review -> in-review | claude | fd31fd4 | the automated review on pull request 60 held one Important finding across three passes: the detour is decided to fire at intent drafting, but the adoption mechanism is sign.py --revision and intent.md is never signable, a sign.py change the Must-not list forbids. Carried into the open questions with a proposal (nothing is re-signed at that gate; the route is drafted into the in-review intent and the owner tap is the sign-off) for the owner to accept or turn around; nothing else in the intent changed
- 2026-09-15T00:22:15Z | intent.md | in-review -> in-review | claude | 0e7eb1a | sixth open question answered by the owner: the proposal accepted as written, the intent-drafting gate re-signs nothing and the tap is the sign-off; branch merged up to main with work/index.md regenerated
- 2026-09-15T00:27:48Z | intent.md | in-review -> approved | luissiviero | ae35caf | mode: delegated
- 2026-09-15T00:53:17Z | spec.md | (none) -> in-review | claude | 3ce6eae | drafted under the grant from the six answered questions: the trigger is a new scripts/check_detour.py that calls the merge script's own locked-path matcher per path (DETOUR: none / needed, exit 0 / 3); a detour is a revision record of kind detour with a Route section reviewers judge; a park is a parked: ledger line on intent.md that next_item.py skips and gen_index.py marks, landing as the item's own delegated pull request so advance() moves the pointer; the remainder is a supervised intent with detour-of in its own pull request; two rule fragments rewritten with no net line at the adopter's cap
- 2026-09-15T00:53:27Z | spec.md | in-review -> delegated | claude | 3ce6eae
- 2026-09-15T00:56:31Z | spec.md | delegated -> delegated | claude | 001b20e | deviation: R-1 acceptance reworded before Build: the detour-record test is a guard predicted green and mutation-checked with a keep verdict, not a test that fails today; the signature itself untouched
- 2026-09-15T00:56:31Z | plan.md | (none) -> in-review | claude | 001b20e | kind feature; twenty-nine files: eight under scripts (check_detour.py and its tests, parked_note in next_item.py with four cases, the index marker with a golden case, a detour-record guard in test_sign.py, test_park_advance.py on the Advance fixture), three templates, four skills, two rule fragments with the render, three evals, the decision record; tests first and watched red; the pull request is the owner click because every skill, template and rule path is ALWAYS_LOCKED, and the last commit parks the item as the intent first answer says
- 2026-09-15T00:56:31Z | plan.md | in-review -> delegated | claude | 001b20e
