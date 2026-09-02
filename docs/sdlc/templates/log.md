---
type: sdlc/log
id: <slug>-log
title: Gate ledger for <slug>
description: Chronological record of stage transitions and approvals for this work item.
timestamp: <RFC3339>
---
# Log: <slug>

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-01-01T00:00:00Z | intent.md | (none) -> draft | <actor> | <sha> | drafted from the interview
- 2026-01-01T01:00:00Z | intent.md | draft -> approved | <actor> | <sha> | approved by the role named for `intent` in `.sdlc/approvers.yaml`
