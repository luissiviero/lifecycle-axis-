---
type: sdlc/work-item
id: parked-marker-on-retired
title: A retired item still reads `parked` in the generated index
description: "gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement."
timestamp: 2026-09-15T02:33:00Z
---
# A retired item still reads `parked` in the generated index

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement.
- [spec.md](spec.md) — status: delegated; approved-by: claude; gen_index.build_item asks next_item.parked_note for a park only when the item's intent.md has status: approved; on any other status the stage cell comes from _stage and the item index carries no Parked: line, so a retired item renders like every other retired item. The helper, the queue and every judging script are untouched; one regression case in a new module is seen red first.

Last gate: - 2026-09-15T02:34:11Z | spec.md | in-review -> delegated | claude | bad2b14 | designed from the owner's answer on the intent: build_item asks parked_note only for an approved intent, so a retired item renders like any other; one regression case in a new module composing test_gen_index's fixtures, seen red first; the helper, the queue and every judging script untouched
