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
