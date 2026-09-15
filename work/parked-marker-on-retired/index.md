---
type: sdlc/work-item
id: parked-marker-on-retired
title: A retired item still reads `parked` in the generated index
description: "gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement."
timestamp: 2026-09-15T02:20:28Z
---
# A retired item still reads `parked` in the generated index

- [intent.md](intent.md) — status: in-review; approved-by: ; gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement.

Last gate: - 2026-09-15T02:20:28Z | intent.md | (none) -> in-review | claude | fd39dd0 | drafted in the session that closed risk-detour, at the owner's choice of a separate low item: a retired item's row and index still read parked because gen_index.py reads only the latest parked:/resumed: ledger line; one condition and a regression test in a new module (kind fix); one open question with a proposal (the marker only for an approved intent)
