---
type: sdlc/rule-fragment
title: Gemini CLI specifics
description: Tool names, the first-run trust warning, exit_plan_mode, and .gemini as protected.
targets: [gemini]
order: 50
tags: [rules, gemini-cli, hooks, plan-mode]
timestamp: 2026-09-02T00:00:00Z
---
## Gemini CLI notes
- Hooks are `BeforeTool` entries in `.gemini/settings.json` and match Gemini tool names
  (`write_file`, `replace`, `run_shell_command`), not `Edit|Write|MultiEdit`.
- A project hook that is new or whose command changed warns before it runs, so a local
  block can be skipped on first run. The CI gate (`sdlc-gate`) is the authoritative red line.
- Leaving plan mode with `exit_plan_mode` is **not** an approved `plan.md`. Rule 1 is
  satisfied only by `work/<slug>/plan.md` with `status: approved` set by a human.
- Treat `.gemini/` (settings, agents, policies) as protected exactly like `.claude/hooks/`
  in rule 3: propose the change in the PR description instead of editing it.
