---
type: sdlc/log
id: _example-log
title: Gate ledger for _example
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-02T12:00:00Z
---
# Log: _example

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>` (append-only; parsed by scripts/log_ledger.py).

- 2026-09-02T12:00:00Z | intent.md | (none) -> draft | luissiviero | 372801f | drafted so the example item always has one to exercise the hooks and CI against
- 2026-09-02T12:05:00Z | intent.md | draft -> approved | luissiviero | 372801f | approved as product-owner per .sdlc/approvers.yaml
- 2026-09-02T12:10:00Z | spec.md | (none) -> draft | luissiviero | 372801f | requirements table drafted from the approved intent
- 2026-09-02T12:15:00Z | spec.md | draft -> approved | luissiviero | 372801f | approved as product-owner per .sdlc/approvers.yaml
- 2026-09-02T12:20:00Z | plan.md | (none) -> draft | luissiviero | 372801f | file list and steps drafted from the approved spec
- 2026-09-02T12:25:00Z | plan.md | draft -> approved | luissiviero | 372801f | approved as tech-lead per .sdlc/approvers.yaml
