---
type: sdlc/work-item
id: retire-delegated-items
title: A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale
description: "An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes."
timestamp: 2026-09-14T05:35:00Z
---
# A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes.

Last gate: - 2026-09-14T16:12:34Z | intent.md | in-review -> approved | luissiviero | c864c0f
