---
type: doc
title: Session handoff (2026-09-06)
description: "How to resume after the delegated-mode work: constraints, task state, the owner's grant routine, resume steps."
tags: [sdlc, handoff, playbook-comparison, delegated-mode]
timestamp: 2026-09-06T01:20:00Z
---

# Session handoff (read this first after any context reset)

## How to resume in a NEW session (container state is gone; only git survives)
1. Read, in this order, from `main`: `docs/sdlc/handoff/HANDOFF.md` (this file), then
   `work/delegated-mode/plan.md` (the last item's plan; its deviations log is the most recent design record)
   and `knowledge/decisions/delegated-mode.md`. The older handoff files beside this one (`PLAN.md`,
   `consensus.md`, `lifecycle-axis-vs-playbook.md`) are the record of the 2026-09-04 plan, all merged.
2. No task list to re-create: no work item is open. The next act is a human grant (see "Task state").
3. Re-arm an hourly `send_later` check-in and subscribe to each PR you open (`subscribe_pr_activity`).
   Every earlier session deleted its trigger on handoff so two sessions never act on the same PR.
4. Continue at "Task state" below. ("Current state" is history from 2026-09-05 ~01:50 UTC and
   describes Batch B as still to open; it is kept as a record, not as instructions.)
5. Helper scripts (copies in `docs/sdlc/handoff/`): `place.sh <slug> <title>` opens a chain
   branch from `origin/main`; `check_artifacts.py <dir>` checks template conformance. Copy them to
   the new session's scratchpad before use (they must not run from inside `docs/`).
6. Git identity in a new remote session is again an agent identity; never approve anything.
7. First check in the new session: the new `protect-approvals.sh` is wired on `main`. An Edit that sets
   `status: approved` on any `work/<slug>/*.md` must be refused (exit 2). If it is not, stop and tell the owner.

## Current state (2026-09-05 ~01:50 UTC) — HISTORY, superseded by "Task state" below
- **Batch A is complete.** Merged into `main`: WI-1 front-matter (#24), WI-2 control-plane-visibility (#26),
  WI-3 loop-protection (#28), WI-4 bash-guard-hardening (#29), WI-5 deploy-gate (#27), WI-6 approval-gate (#25,
  merged 01:47 UTC). `main` now wires `protect-approvals.sh`; every session started before that merge runs the
  old hook set and must not continue the work.
- **Batch B opens now** (in the fresh session): WI-7 band-detector → WI-8 adopter-first-hour → WI-9 agent-evals
  → WI-10 delegation-boundary (needs the owner's answers in `work/delegation-boundary/intent.md`) → WI-11
  docs-reconcile. Per item: `place.sh <slug> <title>` from `origin/main` (branch `claude/<slug>`, intent+spec+plan
  drafted `in-review` from `docs/sdlc/handoff/PLAN.md`, draft PR `[<slug>] …` with `Work-Item: <slug>`), then the
  owner approves from the phone (routine below), then the session sets `.sdlc/active`, implements per the plan,
  verifies, pushes, asks for `control-plane-approved` where hooks/workflows/`.sdlc` change, and the owner merges.
  Serial, one item at a time. **Batch B is merged** (PRs 31 to 37) and **Step 0 is done**: the owner set
  `work/sdlc-kit-phase-1`'s three artifacts to `superseded` from the web editor and the indexes were
  regenerated on PR 38.
- Follow-ups noted during Batch A, not yet items: (a) `check_artifact_chain.py` attributes an approval with
  `git log -S 'status: approved'`, so any later commit that adds or removes that phrase in the artifact (prose
  included) is read as the approver; a `-G '^status:'`-style front-matter check would be precise. (b) Older hook
  evals use `! cmd` under `set -e`, which never fails a case; check exit codes explicitly. Both belong in WI-9
  agent-evals or WI-11 docs-reconcile, owner's call.

## Task state (2026-09-08 ~19:40 UTC)
- **Delegated mode has run a full item end to end.** `work/approve-by-dispatch` (#51), `work/retire-active-pointer`
  (#53), `work/run-queue` (#55, #57) and `work/run-queue-followups` (#56 intent, #58 implementation) are the
  record. The queue machinery works: `scripts/next_item.py` orders it, `delegated_merge.py` advances
  `.sdlc/active` after a merge, and `/sdlc-run` loops on its own pull request.
- **Local runs need the token unset**, in a container with no `gh` binary: `GH_TOKEN= GITHUB_TOKEN= scripts/verify.sh`
  and the same prefix on `check_artifact_chain.py`. Without it the dispatch-trailer check crashes. This bit two
  sessions before it was written down.
- **Run the chain check after committing, never before.** Since `work/run-queue-followups` the check refuses an
  empty diff on a dirty tree rather than reporting `CHAIN: PASS` on work it never saw; `verify.sh`'s `--base HEAD`
  self-check is deliberately exempt, so a green verify still says nothing about whether your commit is complete.
- Known follow-ups, not yet items: `work/run-queue/log.md:21` cites the wrong sha (the base it was written
  against, not the commit carrying the change); the `gh`-absent crash in `check_artifact_chain.py` is still
  unfixed and is why the token prefix is needed.

## Task state (2026-09-06 ~01:20 UTC) — HISTORY, superseded by the section above
- **`work/delegated-mode` is merged, in four pull requests**: #42 (1a, the vocabulary — `delegation.py`, the
  chain check's `delegated` branch, the decision record; fce28c0), #43 (1b, the act — the hooks,
  `scripts/sign.py`, `approve.py --delegate`; 2e01c12), #44 (1c, the prose — skills, rule fragments, this doc
  set; 924f5c0) and #45 (2, the merge — `delegated-merge.yml`, `scripts/delegated_merge.py`; 1851edd). The
  session that built it ended after #45; nothing of the item is open, and the plan's step 6 below is the next
  act. #45's merge script carries the security pass's seven fixes (the grant read from the base branch, the
  committer as well as the author checked, the review verdict bound to a `pr-review` run, `pull_request`-only
  required runs, renames and a locked-path floor, the slug bound to `.sdlc/active`): `plan.md`'s deviations
  log and the decision record's residuals are the record. The repo now runs two modes side by side: supervised, where a human writes the `approved` status
  as `human-only-approvals.md` always required; and delegated, where an agent signs the `delegated` status
  under a grant and `.github/workflows/delegated-merge.yml` merges the pull request once every printed
  condition holds, no click needed.
- **`.sdlc/delegation.yaml` is the one tuning surface for the mode**, and it stays `enabled: false` on
  `main` — the owner's own commit, 9e405fa — until the owner flips it back. Until then every delegated path
  stays closed: `sign.py`, the hooks and `delegated_merge.py` all treat the disabled policy the same as a
  missing one, so every artifact goes through the supervised path regardless. When the owner flips it, the
  same edit sets `require-checks: [sdlc-gate, pr-review]`: the live file still lists `agent-evals`, whose
  `paths:` filter means a docs-only pull request has no run for it, and the merge script refuses a missing
  required run (the template already carries the trimmed list).
- **The owner's routine for a grant**, once the policy is on: `python3 scripts/approve.py <slug> intent.md
  --delegate --activate --as <handle>` from a shell, or the same four keys (`risk-class`, `mode`,
  `delegated-by`, `delegated-on`) plus the ledger note edited in the GitHub web editor — either way, on
  `main`, as a human commit. `docs/sdlc/github-setup.md`, "Delegated mode (optional)", has the full routine
  and the two waits that fail closed by design (no Claude credential; a diff touching `.claude/skills/`,
  `.claude/agents/` or `CLAUDE.md`).
- **The first live delegated item is next** (plan step 6): a `scripts/`- or docs-only follow-up — the
  NUL-byte check and the flaky eval `skill-spec-flags-concerns` are the two candidates already on file below
  — granted by the owner and run end to end with `/sdlc-run`. Not the control-plane tiering item:
  `delegated_merge.py` refuses any diff under a locked or protected path by design, so that item stays
  supervised regardless of a grant.
- **Open follow-ups this work did not touch**, carried over from the previous task state, plus one new one:
  control-plane tiering; the stale-active-slug retirement (both halves — retire the slug when an item
  completes, and make the chain check handle an unset slug); the flaky eval (`skill-spec-flags-concerns`);
  the NUL-byte check (control bytes in tracked text); the B13 list in `lifecycle-axis-vs-playbook.md`; the
  Phase 2 roadmap. New from this work: `check_control_plane.sh` reported "clean" on pull request 42's diff,
  which changed `.sdlc/active` — `check_artifact_chain.py` treats that line as this item's own file, but
  `check_control_plane.sh` does not (deviation 1 in `work/delegated-mode/plan.md`), so the two checkers
  disagree on the same diff; worth a look, and likely the same fix as the stale-slug item above. Issue 40
  (the `pr-review-bottleneck` intent the band detector filed) is still open for the owner to answer or
  close; this work neither read nor answered it.

## Owner routine (the owner works from a phone; keep every ask to taps)
- **Approvals and grants, preferred route: the tap.** *Actions → approve → Run workflow*
  (`.github/workflows/approve.yml`). Send the owner four values and nothing else: the **branch** for the
  selector, `artifact`, `mode` (`supervised`, or `delegated` for a grant) and `slug` (blank means the branch's
  `.sdlc/active`). It runs the approval script as the run's actor and commits the result, so the owner never
  edits front matter or pastes a ledger line. A grant must be dispatched from `main`; the run refuses on any
  other ref. It also refuses, before writing anything, if the actor does not hold the artifact's role, so a
  mistaken tap changes nothing and shows one line in the step summary. GitHub records who pressed Run, and
  the chain check and the merge script verify the commit's trailers against that record.
- Approvals, the older route (still valid, and the one to use for a demotion, which the workflow does not do):
  send GitHub web-editor links (`https://github.com/luissiviero/lifecycle-axis-/edit/<branch>/work/<slug>/<artifact>.md`)
  with the line numbers and exact replacement text for `status:`, `approved-by:`, `approved-on:`, and
  the three ledger lines to append to `work/<slug>/log.md` in a fenced block (never as bullets: a pasted
  bullet arrives as `- - <ts>`; run `python3 scripts/log_ledger.py work/<slug>/log.md` after the commit).
- Label: PR page → "..." (top right) → Edit → Labels → `control-plane-approved`.
- Merge: the owner clicks merge on the PR page; never merge from the session. CI is informational here
  (`knowledge/decisions/merge-click-is-the-gate.md`): the owner merged #25 with the chain check still red on the
  pickaxe misattribution above, having read the explanation.
- Grant (delegated mode, once `.sdlc/delegation.yaml` is `enabled: true`): one tap, as above — `artifact`
  `intent.md`, `mode` `delegated`, branch `main`, which also points `.sdlc/active` at the item. Or the older
  routes: the web-editor link for `intent.md`'s four keys (`risk-class`, `mode`, `delegated-by`,
  `delegated-on`) plus the ledger note, on `main`; or `approve.py --delegate --activate` from the owner's own
  shell. Every route lands as a human-caused commit — after that, `/sdlc-run` calls the owner back only at a
  deviation cap, a stalled revision, a locked path, or a red check it cannot fix.
- Every request to the owner ends with the phone steps. Send one clear list; do not restate a decision already
  made, and do not answer automated stop-hook prompts in the chat (the owner reads only the last message).

## Suggested first prompt for the new session
"Read docs/sdlc/handoff/HANDOFF.md on main, starting at 'Task state'. work/delegated-mode is merged and no
work item is open, so do not resume it: the next step is the first live delegated item, which needs my grant
first; until then pick up whichever follow-up that section lists, or wait for me."

(Superseded, kept as a record: the prompt that opened Batch B read "Resume the lifecycle-axis SDLC work.
Read docs/sdlc/handoff/HANDOFF.md on branch claude/session-handoff first, then follow its resume steps.
Batch A is merged; open Batch B starting with WI-7 band-detector.")

## What the earlier sessions did
1. Compared the repo (`main` @ `64bcb17`) against Anthropic's AI-native SDLC playbook with eight read-only
   analysts. Report: `lifecycle-axis-vs-playbook.md` (this dir). Bash-guard bypass table: `bypass_table.md`.
2. Reconciled with the owner's earlier row-by-row artifact
   (https://claude.ai/code/artifact/2034001b-d402-47f4-a9c7-22b8d486137a). Consensus: `consensus.md`.
3. Wrote the implementation plan (11 work items + Step 0; appendix has verified hook/gate code): `PLAN.md`.
4. Owner decisions: several per-change work items; keep the unlock and make it visible; all twelve
   consensus items, phased; bounded Bash-guard hardening with documented residuals.
5. Opened Batch A (six chains, PRs #24-#29) and implemented WI-1..WI-6 serially as the owner approved; each PR's
   automated-review findings were verified, fixed and resolved in-thread.

## Hard facts that govern implementation
- The session's git identity is `Claude <noreply@anthropic.com>`: `check_artifact_chain.py`
  classifies it as an agent, so an approval committed here FAILS the chain check. Only the owner
  (`luissiviero`) can approve intent/spec/plan. Never set `status: approved` or `approved-by` yourself;
  never run the approval helper script. `protect-approvals.sh` now refuses all of it: it judges the front
  matter that would result from an Edit/Write, refuses any Bash write to an already-approved artifact, and
  refuses Bash text naming that script or unsetting `CLAUDECODE`. Edit an approved plan's body (deviations
  log) with the Edit tool only.
- A post-approval edit to an approved artifact must not add or remove the literal phrase `status:` +
  ` approved` anywhere in that file (prose included), or CI attributes the approval to the agent's commit.
- Branches `claude/<slug>`: the prefix makes `scripts/check_control_plane.sh` treat PRs as agent-authored,
  so control-plane diffs need the owner's `control-plane-approved` label. PR body carries
  `Work-Item: <slug>`; title `[<slug>] …`.
- `.sdlc/active` names the item under implementation; the session sets it after merging `main` into the
  next branch (the owner cannot run the approval script from a phone) and lists it in the plan's file list
  with a deviation. `require-plan.sh` blocks every write under `scripts/` (including Bash text that mentions
  `scripts`) until the active plan is approved by a `tech-lead`.
- Retiring an item is a human act, from the web editor today (`work/retire-active-pointer`): set
  `status: superseded` on `intent.md`, `spec.md` and `plan.md`, append one `approved -> superseded` (or
  `delegated -> superseded`) ledger line per artifact, and set `.sdlc/active` to the next item or to empty.
  `require-plan.sh` refuses a `superseded` plan; `check_artifact_chain.py` fails every pull request whose base
  already has `.sdlc/active` naming a retired item (the retiring pull request itself gets a note to move the
  pointer), and notes one whose `Work-Item` differs from the pointer. Nothing *retires* an item on merge
  (`superseded` stays the owner's act; one tap for it is a follow-up item), but since `work/run-queue` the
  merge does *move the pointer*: `delegated_merge.py` advances `.sdlc/active` to the next granted, unstarted
  item (`scripts/next_item.py`: earliest `delegated-on`, ties by slug) and writes a ledger line on both items,
  committed to `main` as `github-actions[bot]`. An owner's merge click runs no workflow, so it does not advance.
- The queue's first item is whatever `.sdlc/active` names, and every grant tap repoints it — so **the last
  tap runs first**, then the rest in date/slug order. Tap the item you want first, last.
- No `gh` binary in the remote container: with `GH_TOKEN` set, the chain check's trailer verification raises
  `FileNotFoundError` (`check_artifact_chain.py:192`, a follow-up). Locally, prefix `GH_TOKEN= GITHUB_TOKEN=`
  on `scripts/verify.sh` and on the chain check; that takes the documented author-rule fallback. CI has `gh`.
- `SDLC_CONTROL_PLANE_UNLOCK=1` (`.claude/settings.json`): writes to hooks, workflows, `.sdlc` pass with
  an audit line. The never-unlock files (`.sdlc/release-authorizations*`, `.sdlc/approvers.yaml`,
  `.sdlc/hook-decisions.log`) block any Bash command whose text names them, including `git rm --cached`;
  the session's policy classifier also refuses disguised spellings. Ask the owner instead (a
  `https://github.com/<owner>/<repo>/delete/<branch>/<path>` link is one tap).
- Hook edits are atomic: stage in the scratchpad, `bash -n`, `cp` into place, run the full
  `python3 scripts/run_tests.py`, `git checkout --` the hook back on failure, all in one Bash call.
  `scripts/run_tests.py -p a -p b` runs only the last pattern: one module per call. The Write tool turns a
  `\0` escape inside a heredoc-free file into a raw NUL byte; write such jq programs with `printf`.
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
  evidence (grep + CI hook-cases pass) and resolve the thread. Its other findings have all been real so far:
  reproduce, fix, add a test, log a deviation, reply with evidence, resolve.
- The repo's secrets hook refuses any write whose text looks like a credential assignment with a quoted
  value of eight or more characters; keep such examples out of docs, tests and the scratchpad.

## Work-item order (from the plan; all of it is merged, see Task state)
Step 0 (owner): supersede `work/sdlc-kit-phase-1/*` artifacts + ledger lines, regen index.
WI-1 front-matter → WI-2 control-plane-visibility → WI-3 loop-protection → WI-4 bash-guard-hardening →
WI-5 deploy-gate → WI-6 approval-gate → WI-7 band-detector → WI-8 adopter-first-hour →
WI-9 agent-evals → WI-10 delegation-boundary → WI-11 docs-reconcile. Hooks change serially, never in
parallel worktrees.

## Where the evidence is
- Analyst conclusions are folded into `lifecycle-axis-vs-playbook.md` and the plan.
- Playbook text: `playbook.txt`. Preamble given to analysts: `PREAMBLE.md`.
