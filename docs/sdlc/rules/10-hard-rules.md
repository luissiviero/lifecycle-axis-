---
type: sdlc/rule-fragment
title: The eight hard rules
description: The eight hard rules; byte-identical in CLAUDE.md, GEMINI.md and AGENTS.md.
targets: [claude, gemini, agents]
order: 10
tags: [rules, hooks, ci, enforcement]
timestamp: 2026-09-05T20:00:00Z
---
## Hard rules (enforced by hooks and CI, not by good intentions)
1. No code edits under the paths in `.sdlc/config.env` (`PLAN_REQUIRED_PATHS`)
   unless the active work item has an **approved** `plan.md`. A plan with `kind: fix`
   also locks test files: reproduce the bug as a failing test first, then fix the code.
2. If implementation deviates from `plan.md`, update `plan.md` in the same commit.
   CI fails a PR whose diff touches files not listed in the plan.
3. Never edit `.claude/hooks/`, `.gemini/`, `.github/workflows/`, `.sdlc/`, `.claude/settings.json`,
   `scripts/verify.sh`, `scripts/run_tests.py`, `scripts/run_evals.sh`, `scripts/checks/`, or secret
   files. Propose the change in the PR description instead. Never set `status: approved`, `approved-by` or
   `approved-on` on a chain artifact and never run `scripts/approve.py`: `protect-approvals.sh` refuses both.
   Under a grant (`mode: delegated` on an approved intent, policy in `.sdlc/delegation.yaml`) an agent may
   sign `delegated` with `scripts/sign.py` under its own handle; `approved` stays a word only a human writes.
   That human act may be one tap: a `workflow_dispatch` run of `.github/workflows/approve.yml` writes what the
   approval script writes, with the run's actor as the deciding handle. Ask for the tap and wait; the production
   gate catches every route an agent has to press it.
4. Never deploy, publish, or push to a protected branch. The production gate hook
   stops you; a human authorizes releases.
5. Run `scripts/verify.sh` before asking for review. Paste its last line in the PR.
6. Review findings cite `file:line` and evidence. Max five minor comments per review.
7. A mistake made twice becomes a line in this file or a skill, in the same PR.
8. Subagents have a named role in the agent directory (`.claude/agents/`,
   `.gemini/agents/`), bounded tools, and must return evidence (paths, commands,
   outputs), not opinions.
