---
type: sdlc/work-item
id: approve-by-dispatch
title: Give permission for the AI to change from one mode to the other when I request, without doing everything manually
description: "Make every approval and every delegation grant one tap in the Actions tab: a workflow_dispatch workflow that writes what approve.py writes, with GitHub's own record of who pressed Run as the human act, so the owner chooses supervised or delegated per item on request and never edits a file by hand."
timestamp: 2026-09-06T17:30:00Z
---
# Give permission for the AI to change from one mode to the other when I request, without doing everything manually

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; Make every approval and every delegation grant one tap in the Actions tab: a workflow_dispatch workflow that writes what approve.py writes, with GitHub's own record of who pressed Run as the human act, so the owner chooses supervised or delegated per item on request and never edits a file by hand.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; A workflow_dispatch workflow runs scripts/approve.py with the run's actor as the handle and commits the result, so every approval and every delegation grant is one tap; the commit carries the run id, and the chain check and the merge script verify a dispatch-made decision against the run's server-side record.
- [plan.md](plan.md) — status: delegated; approved-by: claude; Build approve.yml and approve_dispatch.py, teach approve.py --from-dispatch, and give the chain check and the merge script a trailer-verified route, so every approval and every delegation grant is one tap whose actor GitHub records server-side.

Last gate: - 2026-09-06T19:55:00Z | plan.md | delegated -> delegated | claude | 159b303 | deviation: docs/sdlc/rules/30-conventions.md gains a convention the spec does not ask for, at the owner's request -- a review runs on a different model from the writer, and the item's ledger records which model wrote and which reviewed; the owner writes the names. Triggered by this item's own three review rounds, two of whose findings were defects introduced by the previous round's fixes
