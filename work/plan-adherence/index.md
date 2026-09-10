---
type: sdlc/work-item
id: plan-adherence
title: A plan executed in a new session is forgotten mid-run, and the agent deviates from it
description: The plan is read once and summarised away at compaction, nothing in the repository re-surfaces it, and the plan's file-list contract is checked only when the pull request opens. This item keeps the plan in front of the agent for the whole session and refuses a deviation at the edit that makes it, with every check tested from a payload and no manual step.
timestamp: 2026-09-10T10:48:42Z
---
# A plan executed in a new session is forgotten mid-run, and the agent deviates from it

- [intent.md](intent.md) — status: in-review; approved-by: ; The plan is read once and summarised away at compaction, nothing in the repository re-surfaces it, and the plan's file-list contract is checked only when the pull request opens. This item keeps the plan in front of the agent for the whole session and refuses a deviation at the edit that makes it, with every check tested from a payload and no manual step.

Last gate: - 2026-09-10T10:48:42Z | intent.md | (none) -> in-review | claude | 7532564 | drafted from the owner's statements in the session of 2026-09-10 (a traced plan executed in a fresh session is forgotten mid-run; make the agent keep it and make output less verbose without forgetting that mid-way) and an exploration of the hooks, the chain check, the templates and the agent directory; measured: no SessionStart or UserPromptSubmit hook, a plan gate that reads status only, the file-list contract judged at the pull request, no step state on disk, no Input line on six of eight agents, no style rule in any fragment; the owner accepted every proposal in the session (no compaction rule, no second pointer, no output style, no caveman, no subagent writer, nothing manual); four questions left for the tap; written and fact-checked by two models
