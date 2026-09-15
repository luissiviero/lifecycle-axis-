---
type: sdlc/work-item
id: parked-marker-on-retired
title: A retired item still reads `parked` in the generated index
description: "gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement."
timestamp: 2026-09-15T02:20:28Z
---
# A retired item still reads `parked` in the generated index

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; gen_index.py marks an item parked from its ledger's latest parked:/resumed: line alone, so a retired item whose last such line is a park keeps the parked stage cell and the Parked: line after its intent is superseded; the marker should yield to the retirement.

Last gate: - 2026-09-15T02:25:33Z | intent.md | in-review -> approved | luissiviero | 0a6d336 | mode: delegated
