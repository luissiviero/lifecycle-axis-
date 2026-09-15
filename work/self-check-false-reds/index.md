---
type: sdlc/work-item
id: self-check-false-reds
title: The self-check fails on an empty pointer and misreads approvals on a shallow clone
description: check_artifact_chain.py ends verify.sh with FAIL when .sdlc/active is empty -- now the common case, because a delegated merge with an empty queue clears the pointer -- and on a shallow clone attributes every approval to the grafted boundary commit; the same advance also leaves work/<slug>/index.md and work/index.md stale, so main is red on three counts that are not the work.
timestamp: 2026-09-15T14:15:00Z
---
# The self-check fails on an empty pointer and misreads approvals on a shallow clone

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py ends verify.sh with FAIL when .sdlc/active is empty -- now the common case, because a delegated merge with an empty queue clears the pointer -- and on a shallow clone attributes every approval to the grafted boundary commit; the same advance also leaves work/<slug>/index.md and work/index.md stale, so main is red on three counts that are not the work.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; Three requirements: an empty .sdlc/active becomes a note where nothing needs proving, a grafted boundary commit is never reported as an approver, and advance() regenerates the indexes its own ledger line dirties.

Last gate: - 2026-09-15T15:37:34Z | spec.md | in-review -> approved | luissiviero | ba33d0a
