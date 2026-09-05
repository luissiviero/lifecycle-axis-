---
type: lesson
title: The ledger's from/to slot holds status values only
description: "Two items logged the build gate as 'plan.md | build -> in-review', which reads as a regression of an approved plan; log the build gate on the PR ('PR #n | draft -> in-review') and leave plan.md at approved."
tags: [lesson, ledger, log]
resource: ../../docs/sdlc/templates/log.md
timestamp: 2026-09-05T04:45:00Z
---
# The ledger's from/to slot holds status values only

## What happened
The `<from> -> <to>` slot of a `log.md` line holds `status` values (`draft | in-review | approved | superseded`),
never a `stage` word. Two items logged the build gate as `plan.md | build -> in-review`, which a reader (and
`scripts/log_ledger.py`) takes as an approved plan regressing to review.

## Rule
Log the build gate on the pull request, `PR #<n> | draft -> in-review`, and leave `plan.md` at `approved`.

## Where it is enforced
`scripts/log_ledger.py` parses the slot; `docs/sdlc/templates/log.md` states the format. Prose beyond that.
