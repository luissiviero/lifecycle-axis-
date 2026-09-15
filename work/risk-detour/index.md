---
type: sdlc/work-item
id: risk-detour
title: A delegated item that meets non-low work looks for a low-only route by reviewer consensus, and parks instead of stopping the queue
description: Delegated mode stays low-only. Today non-low work is refused at admission or stops the whole queue mid-item; the only consensus record asks for the smallest change that clears a trigger, never for a route that stays low. Let the run convene reviewers at every gate for a route that reaches the intent's outcome touching only low-risk surface, adopt it on a unanimous verdict, and otherwise park the item and continue.
timestamp: 2026-09-15T00:50:24Z
---
# A delegated item that meets non-low work looks for a low-only route by reviewer consensus, and parks instead of stopping the queue

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; Delegated mode stays low-only. Today non-low work is refused at admission or stops the whole queue mid-item; the only consensus record asks for the smallest change that clears a trigger, never for a route that stays low. Let the run convene reviewers at every gate for a route that reaches the intent's outcome touching only low-risk surface, adopt it on a unanimous verdict, and otherwise park the item and continue.
- [spec.md](spec.md) — status: delegated; approved-by: claude; The run meets non-low work as a DETOUR: needed line from a new path check that reuses the merge script's own locked-path matcher; a revision record of kind detour carries the route and reviewers judge the route, not the trigger; a unanimous revise amends and re-signs the artifact, two split records at one gate park the item as a parked: ledger line on intent.md that next_item.py and the index both read; the park lands as the item's own delegated pull request so the merge's advance moves the pointer, and the non-low remainder is a supervised intent with a detour-of key in its own pull request.

Last gate: - 2026-09-15T00:53:27Z | spec.md | in-review -> delegated | claude | 3ce6eae
