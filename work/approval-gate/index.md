---
type: sdlc/work-item
id: approval-gate
title: Only a human can flip an artifact to approved
description: No hook covers work/, so an agent can set status approved and approved-by itself or run approve.py with CLAUDECODE stripped, and the chain check does not catch a local agent; approval is a record, not a gate.
timestamp: 2026-09-04T21:49:27Z
---
# Only a human can flip an artifact to approved

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; No hook covers work/, so an agent can set status approved and approved-by itself or run approve.py with CLAUDECODE stripped, and the chain check does not catch a local agent; approval is a record, not a gate.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; A PreToolUse hook that refuses agent writes to the approval fields of chain artifacts and agent invocations of approve.py, plus an approver check in require-plan.sh.
- [plan.md](plan.md) — status: approved; approved-by: luissiviero; New protect-approvals.sh hook, approver check in require-plan.sh, wiring in three settings files, tests, eval and decision record.

Last gate: - 2026-09-05T01:25:23Z | PR #25 | draft -> in-review | claude | 7dcc8fc | implementation of steps 1-8 complete; five deviations recorded in plan.md; needs control-plane-approved (new hook, require-plan.sh, three settings files, .sdlc/active); restart sessions after merge
