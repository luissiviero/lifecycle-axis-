---
type: sdlc/log
id: parked-marker-on-retired-log
title: Gate ledger for parked-marker-on-retired
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-15T02:20:28Z
---
# Log: parked-marker-on-retired

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-15T02:20:28Z | intent.md | (none) -> in-review | claude | fd39dd0 | drafted in the session that closed risk-detour, at the owner's choice of a separate low item: a retired item's row and index still read parked because gen_index.py reads only the latest parked:/resumed: ledger line; one condition and a regression test in a new module (kind fix); one open question with a proposal (the marker only for an approved intent)
- 2026-09-15T02:23:10Z | intent.md | in-review -> in-review | claude | 0c02fbf | open question answered by the owner: the proposal accepted as written, the parked marker reads only for status approved
- 2026-09-15T02:25:33Z | intent.md | in-review -> approved | luissiviero | 0a6d336 | mode: delegated
- 2026-09-15T02:34:11Z | spec.md | in-review -> delegated | claude | bad2b14 | designed from the owner's answer on the intent: build_item asks parked_note only for an approved intent, so a retired item renders like any other; one regression case in a new module composing test_gen_index's fixtures, seen red first; the helper, the queue and every judging script untouched
- 2026-09-15T02:35:14Z | plan.md | in-review -> delegated | claude | b860746 | one code file and one new test module beside the item's own artifacts and the two regenerated indexes; two cases to be watched red before the condition; kind fix so every existing test file stays locked
- 2026-09-15T02:38:31Z | plan.md | delegated -> delegated | claude | 8e99321 | deviation: two acceptance-test sentences in the signed spec corrected after measurement: R-1's quoted golden row read as a Markdown link to a missing file by check_okf.py (1 warning), now described in words; R-4's insertion count on work/index.md was the count against the pre-fix commit, now the three lines against origin/main that its prose already excepts. No requirement or test changed. 1 of 5
- 2026-09-15T02:49:06Z | plan.md | delegated -> delegated | claude | 3792ba4 | deviation: the review round changed the code by three nits (resumers stays outside the condition so a malformed approvers file still fails loudly; the comparison reads status == approved with no dead strip, the queue's spelling; the import comment says the index adds a condition); spec design step 3 and the plan's first risk line rewritten to match. No requirement or test changed. 2 of 5
- 2026-09-15T02:49:06Z | PR #100 | draft -> in-review | claude | 3792ba4 | build_item reads the parked marker only from an approved intent; two cases in a new module seen red in c63ac83 and green since 8e99321; the risk-detour row reads plan and its index loses the Parked: line, nothing else regenerated. Review: plan-reviewer and security-reviewer on Opus 5 against a Fable 5.1 writer, Important: 0, Nits: 6, three carried into the code. VERIFY: PASS, CHAIN: PASS, EVALS: 49 pass 0 fail, OKF: 0 warnings, DETOUR: none. No locked or protected path, so the delegated-merge workflow merges on its printed conditions
