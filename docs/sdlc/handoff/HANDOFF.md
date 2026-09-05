---
type: doc
title: Session handoff (2026-09-05)
description: How to resume the playbook-comparison work: constraints, PR state, task state, resume steps.
tags: [sdlc, handoff, playbook-comparison]
timestamp: 2026-09-05T01:30:00Z
---

# Session handoff (read this first after any context reset)

## How to resume in a NEW session (container state is gone; only git survives)
1. Read, in this order, from branch `claude/session-handoff` (also PR'd): `docs/sdlc/handoff/HANDOFF.md`
   (this file), `docs/sdlc/handoff/PLAN.md` (the approved implementation plan), and only if a
   finding needs re-checking, `docs/sdlc/handoff/consensus.md` and `docs/sdlc/handoff/lifecycle-axis-vs-playbook.md`.
2. Re-create the task list (12 items, statuses in "Task state" below).
3. Re-subscribe to the open Batch A/B PRs (`subscribe_pr_activity`) and re-arm an hourly
   `send_later` check-in. A previous session unsubscribes and deletes its trigger on handoff so
   two sessions never act on the same PR.
4. Continue at "Current state" below.
5. Helper scripts (copies in `docs/sdlc/handoff/`): `place.sh <slug> <title>` opens a chain
   branch from `origin/main`; `check_artifacts.py <dir>` checks template conformance. Copy them to
   the new session's scratchpad before use (they must not run from inside `docs/`).
6. Git identity in a new remote session is again an agent identity; never approve anything.

## Current state (2026-09-05 ~01:30 UTC)
- Merged into `main` (09fac5c): WI-1 front-matter (#24), WI-2 control-plane-visibility (#26),
  WI-3 loop-protection (#28), WI-4 bash-guard-hardening (#29), WI-5 deploy-gate (#27).
- WI-6 approval-gate: PR #25, branch `claude/approval-gate`, head 55cf5f5, ready for review. All three
  artifacts approved by the owner (84783bf, 3c52254, 7dcc8fc). Implemented per `work/approval-gate/plan.md`
  (five deviations logged). Local: VERIFY PASS, 443 tests, EVALS 32 pass / 0 fail, OKF 0 warnings, CHAIN PASS.
  Waiting on the owner's `control-plane-approved` label and merge.
- After #25 merges, `protect-approvals.sh` is wired: **restart the session** before any further work (settings
  are read at session start). In the new session, the first check is that an Edit setting `status: approved`
  on a chain artifact is refused.
- Batch B (WI-7..WI-11) opens when WI-6 merges: WI-7 band-detector → WI-8 adopter-first-hour → WI-9 agent-evals
  → WI-10 delegation-boundary (needs the owner's answers in `work/delegation-boundary/intent.md`) → WI-11
  docs-reconcile. Each opens as a chain (intent+spec+plan in-review) on `claude/<slug>` with a draft PR, then the
  owner approves from the phone and the session implements. Step 0 (owner: supersede `work/sdlc-kit-phase-1`)
  is still pending.

## Task state (2026-09-05 ~01:30 UTC)
- #1 Step 0 (owner): pending. #2..#6 WI-1..WI-5: completed. #7 WI-6: implemented, awaiting label + merge.
  #8..#12 (WI-7..WI-11): pending, Batch B.

## Owner routine (the owner works from a phone; keep every ask to taps)
- Approvals: send GitHub web-editor links (`https://github.com/luissiviero/lifecycle-axis-/edit/<branch>/work/<slug>/<artifact>.md`)
  with the line numbers and exact replacement text for `status:`, `approved-by:`, `approved-on:`, and
  the three ledger lines to append to `work/<slug>/log.md` in a fenced block (never as bullets: a pasted
  bullet arrives as `- - <ts>`; run `python3 scripts/log_ledger.py work/<slug>/log.md` after the commit).
- Label: PR page → "..." (top right) → Edit → Labels → `control-plane-approved`.
- Merge: the owner clicks merge on the PR page after CI is green; never merge from the session.
- Every request to the owner ends with the phone steps. Do not restate a decision already made; the owner
  reads only the last message.

## Suggested first prompt for the new session
"Resume the lifecycle-axis SDLC work. Read docs/sdlc/handoff/HANDOFF.md on branch claude/session-handoff
first, then follow its resume steps. Continue from the Current state section."

## What the earlier sessions did
1. Compared the repo (`main` @ `64bcb17`) against Anthropic's AI-native SDLC playbook with eight read-only
   analysts. Report: `lifecycle-axis-vs-playbook.md` (this dir). Bash-guard bypass table: `bypass_table.md`.
2. Reconciled with the owner's earlier row-by-row artifact
   (https://claude.ai/code/artifact/2034001b-d402-47f4-a9c7-22b8d486137a). Consensus: `consensus.md`.
3. Wrote the implementation plan (11 work items + Step 0; appendix has verified hook/gate code): `PLAN.md`.
4. Owner decisions: several per-change work items; keep the unlock and make it visible; all twelve
   consensus items, phased; bounded Bash-guard hardening with documented residuals.
5. Opened Batch A (six chains, PRs #24-#29), then implemented WI-1..WI-6 serially as the owner approved.

## Hard facts that govern implementation
- The session's git identity is `Claude <noreply@anthropic.com>`: `check_artifact_chain.py`
  classifies it as an agent, so an approval committed here FAILS the chain check. Only the owner
  (`luissiviero`) can approve intent/spec/plan. Never set `status: approved` or `approved-by` yourself;
  never run the approval helper script. After WI-6, `protect-approvals.sh` refuses all of it anyway, and
  refuses any Bash command text naming that script or unsetting `CLAUDECODE`.
- Branches `claude/<slug>`: the prefix makes `scripts/check_control_plane.sh` treat PRs as agent-authored,
  so control-plane diffs need the owner's `control-plane-approved` label. PR body carries
  `Work-Item: <slug>`; title `[<slug>] …`.
- `.sdlc/active` names the item under implementation; the session sets it after merging `main` into the
  next branch (the owner cannot run the approval script from a phone) and lists it in the plan's file list
  with a deviation. `require-plan.sh` blocks every write under `scripts/` (including Bash text that mentions
  `scripts`) until the active plan is approved by a `tech-lead`.
- `SDLC_CONTROL_PLANE_UNLOCK=1` (`.claude/settings.json`): writes to hooks, workflows, `.sdlc` pass with
  an audit line. The never-unlock files (`.sdlc/release-authorizations*`, `.sdlc/approvers.yaml`,
  `.sdlc/hook-decisions.log`) block any Bash command whose text names them, including `git rm --cached`;
  the session's policy classifier also refuses disguised spellings. Ask the owner instead (a
  `https://github.com/<owner>/<repo>/delete/<branch>/<path>` link is one tap).
- Hook edits are atomic: stage in the scratchpad, `bash -n`, `cp` into place, run the full
  `python3 scripts/run_tests.py`, `git checkout --` the hook back on failure, all in one Bash call.
  `scripts/run_tests.py -p a -p b` runs only the last pattern: one module per call.
- `production-gate.sh` asks on any Bash text containing the deploy script's name, `gh pr merge`,
  `gh release create`, `gh workflow run`, or `deploy` next to `prod`; keep those out of commit messages
  and command text.
- Merging `main` into a chain branch conflicts on generated `work/index.md`: take either side, run
  `python3 scripts/gen_index.py`, `git add`, commit. Regenerate (`gen_index.py`, `gen_context_files.py`)
  after every ledger edit; verify fails on drift.
- Plan `## Files that change` bullets start with the bare path (`path — note`); the template's empty
  deviation bullet is `- ` with a trailing space. The ledger's status slot holds status values only: log
  the build gate as `PR #<n> | draft -> in-review`, never `plan.md | build -> ...`.
- Verification per PR: `scripts/verify.sh` → `VERIFY: PASS (<sha>)`;
  `python3 scripts/check_artifact_chain.py --base origin/main --slug <slug>` → `CHAIN: PASS`;
  `scripts/run_evals.sh` → `0 fail`; `python3 scripts/check_okf.py` → `0 warnings`.
- The automated reviewer in `review.yml` restores `.claude/` and `CLAUDE.md` from base before running, so
  its "missing implementation" findings on hook files are sandbox artifacts: answer with branch-head
  evidence (grep + CI hook-cases pass) and resolve the thread. Other bot findings are bug reports: verify, fix.
- The repo's secrets hook refuses any write whose text looks like a credential assignment with a quoted
  value of eight or more characters; keep such examples out of docs, tests and the scratchpad.

## Work-item order (from the plan)
Step 0 (owner): supersede `work/sdlc-kit-phase-1/*` artifacts + ledger lines, regen index.
WI-1 front-matter → WI-2 control-plane-visibility → WI-3 loop-protection → WI-4 bash-guard-hardening →
WI-5 deploy-gate → WI-6 approval-gate → WI-7 band-detector → WI-8 adopter-first-hour →
WI-9 agent-evals → WI-10 delegation-boundary → WI-11 docs-reconcile. Hooks change serially, never in
parallel worktrees.

## Where the evidence is
- Analyst conclusions are folded into `lifecycle-axis-vs-playbook.md` and the plan.
- Playbook text: `playbook.txt`. Preamble given to analysts: `PREAMBLE.md`.
