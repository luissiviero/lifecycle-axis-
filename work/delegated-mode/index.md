---
type: sdlc/work-item
id: delegated-mode
title: A second way to run a work item, where I approve the start and the AI signs the rest under its own name
description: "Add a delegated mode beside the current supervised one: the owner approves the intent and grants delegation once, the agent signs spec, plan, review and merge under its own handle with every act in the ledger, plan changes are a recorded last resort, and everything tunable lives in one human-edited policy file."
timestamp: 2026-09-05T11:28:24Z
---
# A second way to run a work item, where I approve the start and the AI signs the rest under its own name

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; Add a delegated mode beside the current supervised one: the owner approves the intent and grants delegation once, the agent signs spec, plan, review and merge under its own handle with every act in the ledger, plan changes are a recorded last resort, and everything tunable lives in one human-edited policy file.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; Requirements and design for delegated mode: the policy file, the grant on the intent, the delegated status and the agent signing script, the hook and chain-check rules that accept it, the revision gate, and the CI merge workflow.
- [plan.md](plan.md) — status: approved; approved-by: luissiviero; Files, order, proof and risks for delegated mode across four pull requests: vocabulary and chain check, hooks and signing script, prose and skills, and the CI merge workflow.

Last gate: - 2026-09-06T01:18:56Z | PR #45 | in-review -> in-review | claude | 1851edd | merged by the owner as 1851edd (pull request 44 as 924f5c0); every pull request of this item is on main; plan step 6, the first live delegated item, waits on the owner's grant; the session ended here
