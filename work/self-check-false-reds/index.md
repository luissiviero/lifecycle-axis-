---
type: sdlc/work-item
id: self-check-false-reds
title: The self-check fails on an empty pointer and misreads approvals on a shallow clone
description: check_artifact_chain.py ends verify.sh with FAIL when .sdlc/active is empty -- now the common case, because a delegated merge with an empty queue clears the pointer -- and on a shallow clone attributes every approval to the grafted boundary commit; the same advance also leaves work/<slug>/index.md and work/index.md stale, so main is red on three counts that are not the work.
timestamp: 2026-09-15T03:30:00Z
---
# The self-check fails on an empty pointer and misreads approvals on a shallow clone

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py ends verify.sh with FAIL when .sdlc/active is empty -- now the common case, because a delegated merge with an empty queue clears the pointer -- and on a shallow clone attributes every approval to the grafted boundary commit; the same advance also leaves work/<slug>/index.md and work/index.md stale, so main is red on three counts that are not the work.

Last gate: - 2026-09-15T04:05:00Z | intent.md | approved -> approved | claude | d3bd674 | open questions answered by the owner: all six proposals accepted as written. Q1 empty pointer splits by mode (note in in-progress, FAIL in strict, explicit --slug naming nothing still FAIL); Q2 shallow clone degrades to a loud note and never fetches; Q3 all three faults stay in this one item, no split; Q4 the regeneration goes inside advance() with the written allowlist extended by exactly the index paths; Q5 no detour record at this gate; Q6 risk-class medium, confirmed by the approval tap itself (the delegated run failed at approve.py:347 and recorded nothing, the supervised run succeeded). Front matter untouched: the approval stays luissiviero's on d3bd674
