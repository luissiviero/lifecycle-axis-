---
type: sdlc/rule-fragment
title: Gemini CLI specifics
description: Where the hooks are wired for Gemini CLI, the first-run trust warning, the release gate, exit_plan_mode, and .gemini as protected.
targets: [gemini]
order: 50
tags: [rules, gemini-cli, hooks, plan-mode]
timestamp: 2026-09-05T20:00:00Z
---
## Gemini CLI notes
- `.gemini/settings.json` wires the same scripts as Claude: `BeforeTool` on
  `write_file|replace|run_shell_command` runs `.claude/hooks/` protect-paths, block-secrets,
  require-plan, protect-tests, and production-gate; `AfterAgent` runs the verify reminder.
- A project hook that is new or whose command changed warns before it runs, so a local
  block can be skipped on first run. The CI gate (`sdlc-gate`) is the authoritative red line.
- The release gate cannot ask you under Gemini; a deploy or push to a protected branch
  without `.sdlc/release-authorizations/<sha>` is blocked outright.
- Leaving plan mode with `exit_plan_mode` is **not** an approved `plan.md`. Rule 1 is
  satisfied only by `work/<slug>/plan.md` with `status: approved` set by a human.
- Subagents live in `.gemini/agents/` (read-only mirrors of `.claude/agents/`); the
  `/sdlc-*` procedures are the SKILL.md files under `.claude/skills/`: read and follow them.
  Keep one writer per work item: subagents read and return evidence, the session holding the plan
  makes every edit (`knowledge/decisions/one-writer-until-ledger.md`, provisional, with an expiry).
- `/sdlc-run` drives every granted item end to end (grant to merged pull request, then the next queued item on
  each merge), the same way: read and follow `.claude/skills/sdlc-run/SKILL.md`; a plan revision is the last
  resort and needs the consensus record.
- Antigravity (IDE and `agy`) reads this file but ignores `.gemini/settings.json`, so there
  the rules above are advisory only and `sdlc-gate` plus the merge click are the gates.
