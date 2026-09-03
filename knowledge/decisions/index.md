---
type: index
title: Decisions
description: Architecture and process decisions for the SDLC kit, one file per decision with accepted alternatives and consequences.
tags: [okf, index, decisions]
timestamp: 2026-09-02T20:00:00Z
---

# Decisions

One file per decision (`type: decision`): the alternatives considered, what was decided, and the consequences. New
decisions land here as their task ships; this index is regenerated to add each one as it appears on disk.

<!-- regenerate links when new decisions land -->

- [Control-plane exemption is a human-applied PR label](control-plane-label.md)
- [Deploy only from CI via GitHub Environments](deploy-from-ci.md)
- [One rule source renders CLAUDE.md, GEMINI.md and AGENTS.md](one-rule-source.md)
- [Plugin distribution for the SDLC kit](plugin-distribution.md)
- [bash-write-guard.md](bash-write-guard.md) — hook heuristic and CI job together close the Bash heredoc bypass; human unlock env var
- [The kit repo does not wire its own hooks](self-enforcement-off.md) — superseded by self-hooks-on.md the same day; kept for the record
- [CI is informational; the merge click is the gate](merge-click-is-the-gate.md) — private repo on the GitHub Free plan: no branch protection, rulesets or environment rules; the owner reads the checks and clicks, or tells the agent to
- [The kit repo wires its own hooks, with the control-plane unlock](self-hooks-on.md) — .claude/settings.json restored with SDLC_CONTROL_PLANE_UNLOCK=1; the unlock covers Edit/Write too; require-plan and protect-tests gain a Bash branch
- [Gemini CLI runs the same hook scripts through .gemini/settings.json](gemini-hooks.md) — BeforeTool/AfterAgent wiring, release gate fails closed under Gemini, hooks handle Windows drive-letter paths and refuse to run without jq
