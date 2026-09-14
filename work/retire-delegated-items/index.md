---
type: sdlc/work-item
id: retire-delegated-items
title: A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale
description: "An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes."
timestamp: 2026-09-14T05:35:00Z
---
# A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale

- [intent.md](intent.md) — status: in-review; approved-by: ; An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes.

Last gate: - 2026-09-14T05:30:09Z | intent.md | in-review -> in-review | claude | 1490106 | the automated review on #88 left one nit: the third open question pointed at check_grant_commit, which lives in delegated_merge.py and judges grant commits; the sentence now names the chain check's own trailer-versus-author split for approved-by, the two routes a retirement would reuse. Nothing else in the intent changed. The first line above was dated 05:35 by hand, ahead of the clock; it now carries the time of the commit that landed it, 05:22:37Z
