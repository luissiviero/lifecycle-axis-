---
type: sdlc/log
id: self-check-false-reds-log
title: Gate ledger for self-check-false-reds
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-15T03:30:00Z
---
# Log: self-check-false-reds

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-15T03:30:00Z | intent.md | (none) -> in-review | claude | 5bf9573 | drafted as defect 1, the item the 2026-09-15 ~03:10 Task state named next. Three faults, all reproduced in the evidence window 4eb8383..e8ec522 on main: (a) an empty .sdlc/active ends the chain check FAIL at check_artifact_chain.py:528, now the common case because advance() clears the pointer on an empty queue; (b) on a shallow clone the -G lookups at :386 and :833 attribute the approval to the grafted boundary commit, so the same commit 4eb8383 is CHAIN: FAIL shallow and CHAIN: PASS full; (c) advance() appends a ledger line without regenerating, so INDEX: 2 file(s) drifted, folded in per the 03:10 section for the owner to accept or split. risk-class medium (the fixes are inside the approval gate's own judgement and inside an unattended push to main; the policy delegates low only, so medium keeps this supervised), mode supervised. DETOUR: needed (5) -- check_artifact_chain.py, delegated_merge.py and next_item.py are on locked-paths, verify.sh and .sdlc/active on PROTECTED_PATHS/ALWAYS_LOCKED -- so the code lands by the owner's click, not a delegated merge; no detour record filed, this intent seeks no grant. Six open questions, each with a proposed answer
