---
type: sdlc/work-item
id: ci-budget
title: Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest
description: "The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own."
timestamp: 2026-09-09T09:10:00Z
---
# Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest

- [intent.md](intent.md) — status: in-review; approved-by: ; The repository ran 1,124 workflow runs in six days on a private repo, exhausted the account's 2,000 free Actions minutes on 2026-09-08 21:43 UTC, and has been unable to run a single job since, including the owner's approval tap; most of those minutes, and the tokens and waiting behind them, went to work nobody used: superseded runs, a duplicate eval job, and a six-minute model triage of failures that were not the pull request's own.

Last gate: - 2026-09-09T14:30:00Z | intent.md | in-review -> in-review | claude | 4c6be66 | second session, on fable, reviewing the plan before execution: the repository went public first (owner, nothing else changed; gate green on this head at 12:36 UTC), so the fork pull-request pass is the first item of the control-plane pull request and the settings the flip skipped are Phase 0 clicks, each with its link; the history scan ran read-only, nothing found. Owner's revisions recorded as answered questions: opus writes and calls sonnet subagents, fable revises in full at each of five milestones; the skipped-run rule shrinks to one clause in _pr_runs and cancelled still refuses; the gate's `edited` trigger skips Bot senders (Sourcery's body edit doubled the gate run on 3abef21); a supervised item's merge run ends green `not-delegated` instead of red; the measure counts runs by event, since workflow_run wakes carry head_branch main; the owner retires run-queue-followups and moves .sdlc/active before any scripts/ edit; the `triage` label is still to be created; Sourcery uninstalled; failure e-mails off on the owner's side
