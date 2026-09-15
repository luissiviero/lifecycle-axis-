---
type: sdlc/work-item
id: risk-detour
title: A delegated item that meets non-low work looks for a low-only route by reviewer consensus, and parks instead of stopping the queue
description: Delegated mode stays low-only. Today non-low work is refused at admission or stops the whole queue mid-item; the only consensus record asks for the smallest change that clears a trigger, never for a route that stays low. Let the run convene reviewers at every gate for a route that reaches the intent's outcome touching only low-risk surface, adopt it on a unanimous verdict, and otherwise park the item and continue.
timestamp: 2026-09-15T00:58:00Z
---
# A delegated item that meets non-low work looks for a low-only route by reviewer consensus, and parks instead of stopping the queue

- [intent.md](intent.md) — status: superseded; approved-by: luissiviero; Delegated mode stays low-only. Today non-low work is refused at admission or stops the whole queue mid-item; the only consensus record asks for the smallest change that clears a trigger, never for a route that stays low. Let the run convene reviewers at every gate for a route that reaches the intent's outcome touching only low-risk surface, adopt it on a unanimous verdict, and otherwise park the item and continue.
- [spec.md](spec.md) — status: superseded; approved-by: claude; The run meets non-low work as a DETOUR: needed line from a new path check that reuses the merge script's own locked-path matcher; a revision record of kind detour carries the route and reviewers judge the route, not the trigger; a unanimous revise amends and re-signs the artifact, two split records at one gate park the item as a parked: ledger line on intent.md that next_item.py and the index both read; the park lands as the item's own delegated pull request so the merge's advance moves the pointer, and the non-low remainder is a supervised intent with a detour-of key in its own pull request.
- [plan.md](plan.md) — status: superseded; approved-by: claude; Thirty-two files in one claude/ branch: eight under scripts/ (a new check_detour.py and its test module, a parked_note helper in next_item.py with four cases, a parked marker in gen_index.py with a golden case, a detour-record guard in test_sign.py, a new test_park_advance.py composing the merge tests' Advance fixture), three templates, four skills, two rule fragments with the three context files regenerated, three eval cases, a decision record with an amendment note and an index line, and the item's own artifacts; every new case is watched red before its code, the adopter's render is measured at the cap, and the last commit parks the item as `parked: ready PR #<n>; click needed (<path>)` because every skill, template and rule path sits on the merge script's ALWAYS_LOCKED floor.

Parked: parked: ready PR #96; click needed (.claude/skills/sdlc-run/SKILL.md)

Last gate: - 2026-09-15T02:14:12Z | plan.md | delegated -> superseded | luissiviero | b15bacb
