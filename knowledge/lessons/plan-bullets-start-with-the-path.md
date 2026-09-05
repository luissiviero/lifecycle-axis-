---
type: lesson
title: A plan's file bullet starts with the bare path
description: "The chain check reads a '## Files that change' bullet up to the first ' — ' as the path, so 'scripts/x.py (new) — note' fails as the path 'scripts/x.py (new)'; write 'scripts/x.py — new; note'. The template's empty deviation bullet is '- ' with a trailing space."
tags: [lesson, plan, chain-check]
resource: ../../work/front-matter/
timestamp: 2026-09-05T04:45:00Z
---
# A plan's file bullet starts with the bare path

## What happened
`scripts/check_artifact_chain.py` reads each `## Files that change` bullet up to the first ` — ` as the path.
`scripts/x.py (new) — note` therefore fails the chain check as the path `scripts/x.py (new)`. The template's empty
deviation bullet is `- ` with a trailing space, which an edit anchored on `-` alone misses. Both tripped on
`work/front-matter` and `work/control-plane-visibility`.

## Rule
Write `scripts/x.py — new; note`: the bare path, then ` — `, then the note. Anchor edits of the deviations log on
the trailing-space bullet.

## Where it is enforced
`scripts/check_artifact_chain.py` (the path is what it matches); `scripts/test_check_artifact_chain.py`.
