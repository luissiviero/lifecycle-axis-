---
type: sdlc/rule-fragment
title: Gemini CLI specifics
description: Where the hooks are wired for Gemini CLI, the first-run trust warning, the release gate, exit_plan_mode, and .gemini as protected.
targets: [gemini]
order: 50
tags: [rules, gemini-cli, hooks, plan-mode]
timestamp: 2026-09-02T00:00:00Z
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
