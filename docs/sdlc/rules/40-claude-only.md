---
type: sdlc/rule-fragment
title: Claude Code specifics
description: Skill entry points, hook events and subagent location for Claude Code only.
targets: [claude]
order: 40
tags: [rules, claude-code, skills, hooks]
timestamp: 2026-09-05T20:00:00Z
---
## Workflow entry points (skills)
`/sdlc-intent` → `/sdlc-spec` → `/sdlc-plan` → implement → `/sdlc-review` → `/sdlc-incident`
- Hooks in `.claude/hooks/` enforce rules 1, 3 and 4 as `PreToolUse` matchers on
  `Edit|Write|MultiEdit|Bash`, plus a `Stop` reminder for rule 5. They read
  `.sdlc/config.env` under `$CLAUDE_PROJECT_DIR`; a block is `exit 2` with the reason on stderr.
- Subagents live in `.claude/agents/` with a named role and a bounded `tools:` list. Keep one writer per work item:
  subagents read and return evidence, the session holding the plan makes every edit
  (`knowledge/decisions/one-writer-until-ledger.md`, provisional, with an expiry).
- `/sdlc-run` drives every granted item end to end (grant to merged pull request, then the next queued item on
  each merge, no human in between); a plan revision is the last resort and needs the consensus record.
