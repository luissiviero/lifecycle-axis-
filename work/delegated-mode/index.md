---
type: sdlc/work-item
id: delegated-mode
title: A second way to run a work item, where I approve the start and the AI signs the rest under its own name
description: Add a delegated mode beside the current supervised one: the owner approves the intent and grants delegation once, the agent signs spec, plan, review and merge under its own handle with every act in the ledger, plan changes are a recorded last resort, and everything tunable lives in one human-edited policy file.
timestamp: 2026-09-05T11:28:24Z
---
# A second way to run a work item, where I approve the start and the AI signs the rest under its own name

- [intent.md](intent.md) — status: in-review; approved-by: ; Add a delegated mode beside the current supervised one: the owner approves the intent and grants delegation once, the agent signs spec, plan, review and merge under its own handle with every act in the ledger, plan changes are a recorded last resort, and everything tunable lives in one human-edited policy file.
- [spec.md](spec.md) — status: in-review; approved-by: ; Requirements and design for delegated mode: the policy file, the grant on the intent, the delegated status and the agent signing script, the hook and chain-check rules that accept it, the revision gate, and the CI merge workflow.
- [plan.md](plan.md) — status: in-review; approved-by: ; Files, order, proof and risks for delegated mode across four pull requests: vocabulary and chain check, hooks and signing script, prose and skills, and the CI merge workflow.

Last gate: - 2026-09-05T11:28:24Z | plan.md | (none) -> in-review | claude | 38ba396 | four pull requests on one chain; every file listed; the owner sets .sdlc/active on main with the approvals
