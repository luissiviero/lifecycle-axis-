---
type: sdlc/work-item
id: retire-delegated-items
title: A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale
description: "An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes."
timestamp: 2026-09-14T05:35:00Z
---
# A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale

- [intent.md](intent.md) — status: in-review; approved-by: ; An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes.

Last gate: - 2026-09-14T05:35:00Z | intent.md | (none) -> in-review | claude | 7513ff5 | drafted on the owner's direction after the first delegated item was retired from the web editor and both halves of the 2026-09-13 retrospective's prediction landed: the chain check validates superseded against the approver list like approved, so the retired item's agent-signed spec and plan fail every route (five failures in strict mode, two in in-progress mode, measured on pull request 86), and the retirement committed no index, so main was VERIFY: FAIL until #86 merged with the check red. Three questions answered as proposals for the owner
