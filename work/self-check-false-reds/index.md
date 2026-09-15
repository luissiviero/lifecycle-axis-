---
type: sdlc/work-item
id: self-check-false-reds
title: The self-check fails on an empty pointer and misreads approvals on a shallow clone
description: check_artifact_chain.py ends verify.sh with FAIL when .sdlc/active is empty -- now the common case, because a delegated merge with an empty queue clears the pointer -- and on a shallow clone attributes every approval to the grafted boundary commit; the same advance also leaves work/<slug>/index.md and work/index.md stale, so main is red on three counts that are not the work.
timestamp: 2026-09-15T14:15:00Z
---
# The self-check fails on an empty pointer and misreads approvals on a shallow clone

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py ends verify.sh with FAIL when .sdlc/active is empty -- now the common case, because a delegated merge with an empty queue clears the pointer -- and on a shallow clone attributes every approval to the grafted boundary commit; the same advance also leaves work/<slug>/index.md and work/index.md stale, so main is red on three counts that are not the work.
- [spec.md](spec.md) — status: in-review; approved-by: ; Three requirements: an empty .sdlc/active becomes a note where nothing needs proving, a grafted boundary commit is never reported as an approver, and advance() regenerates the indexes its own ledger line dirties.

Last gate: - 2026-09-15T14:20:00Z | spec.md | (none) -> in-review | claude | 6f303af | designed from the approved intent and the owner's six answers. Eight requirements: R1-R3 the empty pointer (note and exit 0 when every changed path is EXEMPT, FAIL otherwise, an explicit --slug naming nothing still FAIL), R4-R6 the graft (membership in git's own shallow file, the existing author-check-skipped note branch reused, and a test that no fetch ever runs), R7-R8 the advance (gen_index regenerates inside advance(), the written allowlist extended by what it reports writing, the :1169 refusal pinned). Five ADRs; D1 resolves the detail the intent flagged: in_progress needs a slug, so with none the mode question becomes "is every changed path EXEMPT?". Four areas of concern, C1 and C2 the two that touch the control plane. DETOUR: needed (5), named under C4 per the skill's step 5, no record filed: supervised, no grant. Gotcha of record: the docstring at check_artifact_chain.py:23 claims evals/ is exempt and EXEMPT at :55 has no such entry, deliberately per the comment at :53 -- the docstring is stale, not the code; left for defect 2, owner's call
