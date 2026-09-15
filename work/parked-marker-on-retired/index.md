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

Last gate: - 2026-09-15T02:49:06Z | PR #100 | draft -> in-review | claude | 3792ba4 | build_item reads the parked marker only from an approved intent; two cases in a new module seen red in c63ac83 and green since 8e99321; the risk-detour row reads plan and its index loses the Parked: line, nothing else regenerated. Review: plan-reviewer and security-reviewer on Opus 5 against a Fable 5.1 writer, Important: 0, Nits: 6, three carried into the code. VERIFY: PASS, CHAIN: PASS, EVALS: 49 pass 0 fail, OKF: 0 warnings, DETOUR: none. No locked or protected path, so the delegated-merge workflow merges on its printed conditions
