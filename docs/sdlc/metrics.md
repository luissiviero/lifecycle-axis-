---
type: doc
title: Metrics: one leading and one lagging indicator per play
description: Leading and lagging indicators for each SDLC play from the AI-native playbook.
tags: [sdlc, metrics, measurement]
timestamp: 2026-09-02T20:00:00Z
---

# Metrics: one leading and one lagging indicator per play

All taken from the playbook. Where to read each one in this repo's setup is in the last column. `scripts/sdlc_metrics.py`
prints the git-derived ones; `scripts/github_metrics.py` prints the GitHub-derived ones the band detector reads.

| Play | Leading | Lagging | Where |
|---|---|---|---|
| Capture intent | time from first conversation to committed intent.md | survival rate (intents accepted into Design); intent edits after first spec commit | git log on `work/*/intent.md` |
| Requirements and design | elapsed time intent.md → spec.md | spec.md commits dated after the first plan.md commit | git timestamps |
| Plan mode | share of changes merged from the first pass; plan approval → merged PR | rework cycles per change; merged diff still matches plan.md | PR metadata; chain check |
| CLAUDE.md | how often a mistake CLAUDE.md should have caught repeats | time to first merged PR for a new team member | review findings; PR history |
| Skills | policy change approved → updated skill merged | review findings citing the policy (should fall to zero) | PRs on `.claude/skills` |
| Parallel sessions | concurrent sessions per engineer while review quality holds; share of day steering vs waiting | changes merged per engineer per week alongside rework rate | OpenTelemetry export; PR history |
| Feedback loop | first-pass CI success rate for agent changes | review time per PR; change failure rate | CI; incident tracker |
| Continuous evals | eval pass rate over time; time for an incident to become an eval | regressions caught in CI vs found in production | `agent-evals` runs |
| PR review | time to first review; share of comments resolved without a human touching the branch | defects caught before merge vs escaped | PR history; incidents |
| Approval gates | time waiting at each gate (hook decisions with timestamps) | gate violations reaching production before/after hooks | `.sdlc/hook-decisions.log` (timestamped block/ask/unlock lines per session); incidents |
| CI/CD | share of pipeline failures triaged without paging a human | DORA measures | CI logs |
| Closing the loop | band breach → intent.md in the triage queue | share of findings that become merged fixes; repeat incidents of the same class | `[band] …` issues and the `bands-series-*` run artifacts of `bands.yml`; PRs |
| Codebase scans | share of repos on a schedule; finding → patch in review gate | scan findings vs production/external reports; findings per scan trend | scan history |

Not defined by the playbook, added in the roadmap: cost per completed task (tokens, tool calls, retries, human minutes)
attributed to a work item and owner.
