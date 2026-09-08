---
type: sdlc/log
id: standing-grant-log
title: Gate ledger for standing-grant
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-08T20:31:19Z
---
# Log: standing-grant

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-08T20:31:19Z | intent.md | (none) -> in-review | claude | 5d6ae96 | drafted from the owner's statements (delegated as the default mode, supervised on request; no tap, just start writing) and an exploration of every reader of the grant; measured: the per-item grant and its five readers, intent.md never signable, the pointer's two writers, the parser that raises on an unknown policy key, verify failing on an empty pointer, risk-class unguarded by the hook despite decision 2; risk class proposed medium as the owner's call; six questions answered as proposals for the owner
