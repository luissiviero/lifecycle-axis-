---
type: sdlc/work-item
id: retire-delegated-items
title: A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale
description: "An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes."
timestamp: 2026-09-14T16:40:00Z
---
# A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py stops validating approved-by against the approver list on a superseded artifact and reads who retired it from the -> superseded ledger line and the commit that set the status (the author rule, or the Approved-Actor trailer when a tap did it); approve.py gains --retire and --next, approve_dispatch.py and approve.yml gain mode: retire with a next input, so a retirement is one tap whose commit goes through the committer that already regenerates the indexes. Nothing an agent can do becomes wider: superseded stays a word the hook, sign.py and the chain check refuse from an agent.

Last gate: - 2026-09-14T16:52:17Z | spec.md | in-review -> approved | luissiviero | cb3f7cc
