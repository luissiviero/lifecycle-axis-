---
type: index
title: Decisions
description: Architecture and process decisions for the SDLC kit, one file per decision with accepted alternatives and consequences.
tags: [okf, index, decisions]
timestamp: 2026-09-05T04:00:24Z
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
- [Only a human can flip an artifact to approved](human-only-approvals.md) — protect-approvals.sh refuses agent-side approval edits and approve.py calls, the unlock never applies; require-plan.sh checks the approver's role
- [scripts/adopt.sh as the template half of plugin distribution](adopt-script.md) — what the installer copies, merges, rewrites and writes; hooks opt-in; the first hour is approve-first
- [One writer per work item until the cost ledger exists](one-writer-until-ledger.md) — provisional: subagents read, the lead writes; expires with the first cost_per_merged_pr reading or on 2027-03-05; names the measurement that reopens it
- [Gemini CLI runs the same hook scripts through .gemini/settings.json](gemini-hooks.md) — BeforeTool/AfterAgent wiring, release gate fails closed under Gemini, hooks handle Windows drive-letter paths and refuse to run without jq
- [A second, delegated mode where an agent signs under its own handle and CI merges](delegated-mode.md) — amends human-only-approvals.md for a new status word, delegated, signed under a human's grant on the intent; supersedes merge-click-is-the-gate.md for delegated items only; one policy file, .sdlc/delegation.yaml
