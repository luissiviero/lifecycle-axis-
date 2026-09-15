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

Last gate: - 2026-09-15T14:32:00Z | spec.md | in-review -> in-review | claude | d39df85 | review finding carried into the design (pull request 104, Important: 1). R7's acceptance test read "the commit's --name-only list equals the allowlist exactly", which is unsatisfiable against gen_index.render_all (gen_index.py:254): it is repo-wide, returning 29 paths today while a full run changes 0, so git add no-ops on the unchanged ones and staged is a strict subset of written. The reviewer offered either scoping the write or relaxing the test to a subset assertion; the stricter option is taken, because relaxing it would have let the allowlist widen from 3 paths to 29 unnoticed, which is exactly what C2 promises does not happen. render_all is still reused for the content (one spelling of the rendering rule), the write is filtered to {merged, next, top}, gen_index.py is untouched and gains no new seam, and R7 gains a guard that a deliberately stale third item's index is left alone. New D6 records it; C3 rewritten from "the seam may not exist" to "the seam is repo-wide"
