---
type: sdlc/work-item
id: parked-marker-on-retired
title: A retired item still reads `parked` in the generated index
description: "gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement."
timestamp: 2026-09-15T02:20:28Z
---
# A retired item still reads `parked` in the generated index

- [intent.md](intent.md) — status: in-review; approved-by: ; gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement.

Last gate: - 2026-09-15T02:23:10Z | intent.md | in-review -> in-review | claude | 0c02fbf | open question answered by the owner: the proposal accepted as written, the parked marker reads only for status approved
