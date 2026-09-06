---
type: sdlc/work-item
id: approve-by-dispatch
title: Give permission for the AI to change from one mode to the other when I request, without doing everything manually
description: "Make every approval and every delegation grant one tap in the Actions tab: a workflow_dispatch workflow that writes what approve.py writes, with GitHub's own record of who pressed Run as the human act, so the owner chooses supervised or delegated per item on request and never edits a file by hand."
timestamp: 2026-09-06T15:45:00Z
---
# Give permission for the AI to change from one mode to the other when I request, without doing everything manually

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; Make every approval and every delegation grant one tap in the Actions tab: a workflow_dispatch workflow that writes what approve.py writes, with GitHub's own record of who pressed Run as the human act, so the owner chooses supervised or delegated per item on request and never edits a file by hand.
- [spec.md](spec.md) — status: in-review; approved-by: ; A workflow_dispatch workflow runs scripts/approve.py with the run's actor as the handle and commits the result, so every approval and every delegation grant is one tap; the commit carries the run id, and the chain check and the merge script verify a dispatch-made decision against the run's server-side record.

Last gate: - 2026-09-06T15:41:47Z | spec.md | (none) -> in-review | claude | 47be4b7 | twelve requirements with oracles, from the approved intent and an explorer pass over approve.py, the chain check, the merge script, the workflows and the production gate; six decisions, five concerns, the trailer design that makes a dispatch verifiable
