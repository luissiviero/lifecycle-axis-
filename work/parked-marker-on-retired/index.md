---
type: sdlc/work-item
id: parked-marker-on-retired
title: A retired item still reads `parked` in the generated index
description: "gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement."
timestamp: 2026-09-15T02:36:00Z
---
# A retired item still reads `parked` in the generated index

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement.
- [spec.md](spec.md) — status: delegated; approved-by: claude; gen_index.build_item asks next_item.parked_note for a park only when the item's intent.md has status: approved; on any other status the stage cell comes from _stage and the item index carries no Parked: line, so a retired item renders like every other retired item. The helper, the queue and every judging script are untouched; one regression case in a new module is seen red first.
- [plan.md](plan.md) — status: delegated; approved-by: claude; scripts/test_gen_index_retired.py (new, two cases composing test_gen_index's fixtures, both watched red first), then build_item in scripts/gen_index.py gates the parked_note call on the intent reading status: approved, then python3 scripts/gen_index.py heals the risk-detour row and index on main; kind fix, so no existing test file is touched.

Last gate: - 2026-09-15T02:38:31Z | plan.md | delegated -> delegated | claude | 8e99321 | deviation: two acceptance-test sentences in the signed spec corrected after measurement: R-1's quoted golden row read as a Markdown link to a missing file by check_okf.py (1 warning), now described in words; R-4's insertion count on work/index.md was the count against the pre-fix commit, now the three lines against origin/main that its prose already excepts. No requirement or test changed. 1 of 5
