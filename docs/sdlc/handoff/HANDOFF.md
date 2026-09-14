---
type: doc
title: Session handoff (2026-09-14)
description: "How to resume in a new session: the session protocol, the task state, the owner's routine, and the seed prompt the finishing session leaves for the next one."
tags: [sdlc, handoff, playbook-comparison, delegated-mode]
timestamp: 2026-09-14T14:20:00Z
---

# Session handoff (read this first after any context reset)

## How to resume in a NEW session (container state is gone; only git survives)
1. Read, in this order, from `main`: `docs/sdlc/handoff/HANDOFF.md` (this file), then `work/<slug>/plan.md`
   for the item `.sdlc/active` names (its deviations log is the most recent design record) and the newest
   records in `knowledge/decisions/`. The older handoff files beside this one (`PLAN.md`,
   `consensus.md`, `lifecycle-axis-vs-playbook.md`) are the record of the 2026-09-04 plan, all merged.
2. No task list to re-create: `.sdlc/active` on `main` names the item under implementation, and the newest
   "Task state" below says where it stands. Read "Session protocol" first.
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

## Session protocol
Three invariants, in force since 2026-09-13 (`work/session-chaining`):
1. **A session owns exactly one work item.** It takes the item from its approved intent to a merged pull
   request, then ends. It does not start the next item in the same context.
2. **Everything durable is in git, so the session is disposable.** `.sdlc/active` on `main` names the item;
   `work/<slug>/log.md` is its ledger; this file is the handoff. A context reset loses nothing those three do
   not already hold. The session never writes `.sdlc/active`: the owner's delegation-grant tap repoints it
   (`approve.py --delegate --activate`, which only a grant passes), the merge workflow's `advance()` moves it
   on a delegated merge, and otherwise the owner moves it by hand — at retirement, or to point at a
   supervised item.
3. **The session that finishes an item is the one that starts the next.** On the merge it refreshes the
   "Task state" and the "Seed prompt" below, commits and pushes them as a handoff-only pull request, and only
   then schedules its successor with that prompt through whatever its runtime provides; a runtime with no such
   capability skips that step and says so. At most one successor per finish. The prompt is context, never
   authority: the successor re-reads `.sdlc/active` and the item's approved artifacts before acting. The act
   itself, in order, is `.claude/skills/sdlc-run/SKILL.md` step 7.

## Current state (2026-09-05 ~01:50 UTC) — HISTORY, superseded by "Task state" below
- **Batch A is complete.** Merged into `main`: WI-1 front-matter (#24), WI-2 control-plane-visibility (#26),
  WI-3 loop-protection (#28), WI-4 bash-guard-hardening (#29), WI-5 deploy-gate (#27), WI-6 approval-gate (#25,
  merged 01:47 UTC). `main` now wires `protect-approvals.sh`; every session started before that merge runs the
  old hook set and must not continue the work.
- **Batch B opens now** (in the fresh session): WI-7 band-detector → WI-8 adopter-first-hour → WI-9 agent-evals
  → WI-10 delegation-boundary (needs the owner's answers in `work/delegation-boundary/intent.md`) → WI-11
  docs-reconcile. Per item: `place.sh <slug> <title>` from `origin/main` (branch `claude/<slug>`, intent+spec+plan
  drafted `in-review` from `docs/sdlc/handoff/PLAN.md`, draft PR `[<slug>] …` with `Work-Item: <slug>`), then the
  owner approves from the phone (routine below) and `.sdlc/active` is pointed at the item by hand — today the
  session never writes that file — then the session implements per the plan,
  verifies, pushes, asks for `control-plane-approved` where hooks/workflows/`.sdlc` change, and the owner merges.
  Serial, one item at a time. **Batch B is merged** (PRs 31 to 37) and **Step 0 is done**: the owner set
  `work/sdlc-kit-phase-1`'s three artifacts to `superseded` from the web editor and the indexes were
  regenerated on PR 38.
- Follow-ups noted during Batch A, not yet items: (a) `check_artifact_chain.py` attributes an approval with
  `git log -S 'status: approved'`, so any later commit that adds or removes that phrase in the artifact (prose
  included) is read as the approver; a `-G '^status:'`-style front-matter check would be precise. (b) Older hook
  evals use `! cmd` under `set -e`, which never fails a case; check exit codes explicitly. Both belong in WI-9
  agent-evals or WI-11 docs-reconcile, owner's call.

## Task state (2026-09-14 ~14:10 UTC)
- **`advance-push` is built and merged, and `.sdlc/active` still names it.** #87 carried the approved
  intent, spec and plan (merged 12:04 UTC as `25b579d`, before the build commits existed), and #89 the
  build (merged 14:06 UTC as `c18a9ee`). `advance()` now refuses a dirty checkout before it touches
  anything, fetches the checkout's branch as `git fetch origin -- <branch>`, refuses unless `FETCH_HEAD`
  is the merge commit `run()` took from the merge endpoint's response, fast-forwards with `--ff-only`,
  and only then writes and pushes as before. A `merge_sha` that is not a 7-to-40 hex string is treated as
  absent at both ends; a detached checkout is a note. Ten cases in two new modules
  (`scripts/test_delegated_merge_advance.py`, `scripts/test_delegated_merge_advance_review.py`);
  `scripts/test_delegated_merge.py` is unmodified at 150.
- **The fix is not observed in production yet, and cannot be until a delegated item merges.** An owner's
  merge click runs no delegated-merge job, so no advance ran on `c18a9ee` and `git log --grep='Advance
  .sdlc/active'` on `main` is still empty. The first *delegated* merge is the observation: its job log
  should print `ADVANCE: .sdlc/active -> <slug>`, and `main` should gain an advance commit whose first
  parent is the merge commit. Nothing is granted today, so nothing will merge delegated until the owner
  grants a low-risk item.
- **Retiring `advance-push` is the owner's next act, and this one retires cleanly.** Its `spec.md` and
  `plan.md` are `approved-by: luissiviero` (supervised, two taps), not agent-signed, so it does not hit
  the `retire-delegated-items` defect that made the previous item's retirement red. The web-editor route
  still leaves the two indexes stale (`knowledge/lessons/human-commits-leave-indexes-stale.md`); run
  `python3 scripts/gen_index.py --check` on `main` before cutting any branch after it.
- **Two review rounds on Opus against a Fable writer found two Important security defects in the build,
  both fixed with the reviewer's own repros pinned as cases.** The branch name reached `git fetch origin
  <branch>` as an option-capable argument, so a ref named `--upload-pack=<script>` executed the script
  over a local-path origin: argv closes shell injection, not argument injection, and `--` now ends the
  options. And a merge response whose `sha` was not a string raised a `TypeError` out of `advance()` past
  `run()`'s `except`, *after* the merge had happened, which would have failed a job for work that landed.
- **`protect-tests.sh` locks a new test file the moment it exists on disk**, although its header says the
  failing reproduction "is a new file and stays writable". That cost this item two things: one fixture
  line the owner had to commit by hand (`be1c162`), and a second test module for the review round's four
  cases. #89's body proposes the one-line reading that matches the header (absent from `git ls-files` on
  the base branch is new). Rule 3 keeps the hook out of an agent's diff, so it needs the owner or an item.
- **Expect one red delegated-merge run per check completion on any open pull request that is not the
  active item's, and leave it alone.** Runs `34846578359` and `34846667149` on #88's check completions
  both end `CONDITION pull-request: refused — Work-Item is 'retire-delegated-items' but .sdlc/active
  names 'advance-push'` and exit 1. That is `work/ci-budget` R-7's deliberate choice, not a gap it left:
  R-7 made `not-delegated` exit 0 and in the same breath kept this one red — "a locked path or a refused
  pull request on a supervised item stays a red run with its own `CONDITION` line", because a refusal
  about the pull request itself must never hide behind the grant verdict
  (`work/ci-budget/spec.md` R7; the same sentence is in `delegated_merge.py`'s `NOT_DELEGATED` comment).
  It costs a run per event, which is the price R-7 weighed and paid. Changing it needs an intent that
  argues the case R-7 already decided, not a bug report.
- **Open pull requests**: #88 `retire-delegated-items` intent (green, mergeable, `Important: 0 | Nits: 0`
  on its last two reviews); #60 `risk-detour` and #61 `standing-grant` intents, both merging clean against
  `c18a9ee` as this is written; #65 and #66 dependabot; #67 `plan-adherence` and #68 `revision` drafts.
  All three intents still carry unanswered open questions with a proposal under each.
- Still true: `ci-budget` is un-retired with a scheduled session on 2026-09-20 for its acceptance step;
  branch protection is absent on `main`; the `triage` label does not exist; local runs need
  `GH_TOKEN`/`GITHUB_TOKEN` unset and there is no `gh` binary in the container; the approvals hook refuses
  any Bash text naming the human approval script, so a spec's acceptance command must not name it.

## Task state (2026-09-14 ~05:00 UTC) — HISTORY, superseded by the section above
- **`approve-tap-regenerates-index` is retired and `.sdlc/active` names `advance-push`.** The owner did
  both from the web editor in five commits (`e7d7ae7`, `f00c002`, `58a5852` set the three artifacts
  `superseded`; `4d9ccd9` the three ledger lines; `5a58b17` the pointer). #84 merged by the owner's click
  (`eb0f7f9`) and #85 with it (`5e1f646`), so the item is complete: the tap regenerates the indexes it
  commits, heals foreign drift on `main`, judges a rename at both ends, and reads its route from
  runner-set values.
- **`main` is `VERIFY: FAIL` as this is written, and this pull request is the fix.** The retirement
  changed front matter and committed no index, so `python3 scripts/gen_index.py --check` on `main` reports
  `work/approve-tap-regenerates-index/index.md` and `work/index.md` drifted. That is the web-editor route,
  which the merged item deliberately did not cover (its "Not doing" says so): the committer's regeneration
  runs inside the approval tap, and a web-editor commit runs no script. The lesson
  `knowledge/lessons/human-commits-leave-indexes-stale.md` is the standing rule; nothing enforces it.
- **The clean-up after a delegated item's retirement is red on the chain check by every route.** All
  three measured on the regenerated tree, against `origin/main`:
  - indexes only, `Work-Item: approve-tap-regenerates-index`: in-progress mode, which tolerates the
    `superseded` statuses, then two failures — `work/approve-tap-regenerates-index/spec.md approved-by
    'claude' is not valid: agent identities cannot approve`, and the same for `plan.md`;
  - this pull request, the same `Work-Item:` plus the handoff, which is nobody's own artifact: strict
    mode, five failures — all three artifacts `status is 'superseded', must be 'approved'`, plus those
    same two approved-by lines;
  - no `Work-Item:` line at all: the gate falls back to `.sdlc/active`, which now names `advance-push`,
    the foreign index forces strict mode, and it fails on that item's missing `spec.md` and `plan.md`.
  So the owner merges this one with the check red (`knowledge/decisions/merge-click-is-the-gate.md`), and
  the two indexes cannot ride under any greener route. This is live evidence for the defect the
  2026-09-13 retrospective filed as unfiled: an agent signs `spec.md` and `plan.md` with `approved-by:
  claude`, and the approver list is enforced on `superseded` exactly as on `approved`, so the artifacts a
  delegated run produces can never be retired into a green chain. It needs its own intent.
- **Next is `advance-push`**, and it is ready to start: intent `approved`, `mode: supervised`,
  `risk-class: low`, no spec or plan, and the pointer already names it, so `require-plan.sh` will open for
  its Build. Its spec can be written now under `/sdlc-spec`, then the owner's tap, then `/sdlc-plan`, then
  the tap, then Build. Its own pull request is the owner's click regardless: it edits
  `scripts/delegated_merge.py`, on the policy's `locked-paths`. `6c7be5f` and `ae69ebc` are two live
  merges where the advance did not land; its spec should cite both.
- Still true: `ci-budget` is un-retired with a scheduled session on 2026-09-20 for its acceptance step;
  branch protection is absent on `main`; the `triage` label does not exist; local runs need
  `GH_TOKEN`/`GITHUB_TOKEN` unset and there is no `gh` binary in the container; the approvals hook refuses
  any Bash text naming the human approval script, so a spec's acceptance command must not name it.
- Open pull requests: this one; #60 `risk-detour` and #61 `standing-grant` intents (will conflict on
  `work/index.md`, merge `main` in and regenerate); #65 and #66 dependabot; #67 `plan-adherence` and #68
  `revision` drafts.

## Task state (2026-09-14 ~03:55 UTC) — HISTORY, superseded by the section above
- **`.sdlc/active` still names `approve-tap-regenerates-index`, and that item is merged.** PR #83 was
  merged by the delegated-merge workflow at 03:45:28 UTC as `ae69ebc` ("Merge pull request #83 (delegated)",
  `github-actions[bot]`), the second delegated merge in this repository's history, with no click: the
  session drove it grant to merge under `/sdlc-run` in one context. **The advance did not land again**:
  `git log --grep='Advance .sdlc/active'` on `main` is still empty and the pointer did not move. That is the
  second live data point for `advance-push` (`6c7be5f` and `ae69ebc`); its spec should cite both.
- **One follow-up is open, #84**, one commit on the same item, ready for review: the automated reviewer
  posted a nit on #83 at 03:44:51 and the workflow merged at 03:45:28, so the fix (the porcelain parse
  reads `git status --porcelain -z`, and a rename's source can no longer be mis-split) landed on a
  re-created branch and needed its own pull request. A nit posted after the tracking comment's
  `Important: 0` line never blocks the merge; a fix that arrives after the merge is a new pull request,
  never a push to a deleted branch. The automated review on #84 then found rule 7 unmet (the arrow
  misparse had been found twice), so #84 also carries `knowledge/lessons/nul-terminated-git-output.md`,
  its pointer line, a re-flowed hooks bullet in the CLAUDE-only fragment to pay for it at the adopter's
  cap, and the regenerated context files: deviation 5 of 5, the cap. **`CLAUDE.md` in that diff is one
  of the two the merge workflow refuses by design, so #84 is the owner's click**, not an automatic merge.
- **What #83 changed in production.** `scripts/approve_dispatch.py --commit` regenerates the indexes before
  it judges the tree. On `main` (a grant, or an intent approval tapped there) it also heals any other item's
  stale index; on a work branch (every supervised spec or plan tap) it writes only the item's own
  `work/<slug>/index.md` and `work/index.md`, because `check_artifact_chain.py` counts only those as the
  item's files. So the tap route of `knowledge/lessons/human-commits-leave-indexes-stale.md` is closed on
  `main`; the web-editor retirement route is not, and neither is a foreign stale index on a branch. The
  route is read from runner-set values (`GITHUB_REF`, `GITHUB_REF_NAME`, `GITHUB_REF_TYPE`, the event
  payload's `repository.default_branch`) and falls narrow on anything malformed. `.github/workflows/approve.yml`'s
  header sentence about what the committer stages is now imprecise for `main` (one line, protected path,
  the owner's edit).
- **The item is done once #84 merges and the owner retires it**, and the retrospective of 2026-09-13 still
  stands: retiring a delegated item may be impossible today (`superseded` needs a human approver and these
  artifacts carry `approved-by: claude`); if the retirement fails on that, it is the defect already on file,
  not a new one.
- **Process record from this item, kept because it is the first delegated item with a revision.** The first
  review round's security pass found the signed spec would have turned a work branch's pull request red
  (a foreign index in the diff flips the chain check into strict mode) and that a rename's source was never
  judged; that is a spec requirement touched, so it went the revision route (`work/approve-tap-regenerates-index/revisions/1.md`):
  the trigger and proposal were written, the two reviewer subagents (Opus, against a Fable writer) were run
  on the proposal, and their sections appended verbatim. The writer's first draft of that record had the
  two reviewer sections written by the writer itself, in the reviewers' voice, and was corrected before
  anything was signed; a record is only a consensus record when the sections come from the reviewers. Once
  is a note here; twice is a lesson. Five deviations of five were logged, the cap: two were
  mispredictions in the plan's step 1 (a count, a timing), one a missing entry for a spec correction, and two
  were what the review rounds asked for (two cases; a lesson). Step 1 is where plans here keep being wrong.
- Live items now: `approve-tap-regenerates-index` (merged, #84 open, un-retired, still the pointer);
  `advance-push` (intent `approved`, `mode: supervised`, `b30feff`; no spec or plan; its Build edits
  `scripts/delegated_merge.py`, a locked path, and `require-plan.sh` opens only for the item the pointer
  names, so the owner points the pointer at it by hand before that Build); `ci-budget` (step 13 by slug on
  2026-09-20 15:00 UTC, scheduled); `session-chaining` (retired).
- Open pull requests: #84 (this item's follow-up) and the handoff pull request carrying this section;
  #60 `risk-detour` and #61 `standing-grant` intents (will conflict on `work/index.md`, merge `main` in and
  regenerate); #65 and #66 dependabot; #67 `plan-adherence` and #68 `revision` drafts.
- Still true: branch protection is absent on `main`; the `triage` label does not exist; local runs need
  `GH_TOKEN`/`GITHUB_TOKEN` unset and there is no `gh` binary in the container; the approvals hook refuses
  any Bash text naming the human approval script, so a spec's acceptance command must not name it.

## Task state (2026-09-14 ~01:50 UTC) — HISTORY, superseded by the section above
- **`.sdlc/active` names `approve-tap-regenerates-index`** — moved there by the owner's delegated tap
  (`70437ab`), not by any merge. Four items are live at once, which the pointer alone cannot show:
  - `approve-tap-regenerates-index`: intent `approved`, **`mode: delegated`**, granted by `luissiviero` on
    2026-09-14; no spec or plan yet. The pointer names it, so `/sdlc-run`'s precondition holds and it can be
    driven grant to merge with no click: spec → sign → plan → sign → build → review → the merge workflow.
  - `advance-push`: intent `approved`, `mode: supervised` (`b30feff`); no spec or plan yet. Its spec and plan
    can be written now (they touch nothing under `scripts/`), each followed by the owner's tap, but its
    **Build edits `scripts/delegated_merge.py`, and `require-plan.sh` opens only for the item `.sdlc/active`
    names** — so before that Build the owner must point the pointer at `advance-push` by hand. Its intent says
    it runs first of the three queue items (`standing-grant` #61 and `risk-detour` #60 depend on it); which of
    the two live items goes first is the owner's call, and this file does not make it.
  - `ci-budget`: all three artifacts `approved`, un-retired, code merged (#71, #72); only step 13, the
    acceptance numbers, remains, and a scheduled fresh session runs it on 2026-09-20 15:00 UTC **by slug, not
    by pointer** (`--slug ci-budget` on the chain check), then asks the owner to retire it.
  - `session-chaining`: retired (`a9a40d5`), all artifacts `superseded`.
- **The first delegated merge in this repository's history happened on 2026-09-14** (`6c7be5f`, "Merge pull
  request #81 (delegated)", authored by `github-actions[bot]`): PR #81 carried `Work-Item:
  approve-tap-regenerates-index`, the pointer named that granted item, every required check was green, and
  the workflow merged it with no click. **And the advance did not land**, exactly as `advance-push`'s intent
  predicts: `git log --grep='Advance .sdlc/active'` on `main` is still empty and the pointer did not move.
  That is live production evidence for `advance-push`; its spec should cite `6c7be5f` and the run's job log.
- **The approval tap leaves indexes stale, seen twice more today**: the retirement route (`a9a40d5`, web
  editor, cleaned by #78) and the tap route (`b30feff` and `70437ab`, cleaned by #80 and #81 — two pull
  requests, because the chain check reads one work item at a time and a single clean-up carrying both
  items' indexes is in-progress mode for neither). Cite all three in `approve-tap-regenerates-index`'s
  spec, and widen its scope to every human-side commit that changes front matter, not only the tap.
- **Open pull requests, none of them this session's**: #60 `risk-detour` and #61 `standing-grant` (intents,
  cut 2026-09-08, will conflict on `work/index.md` like #59 and #62 did — merge `main` in and regenerate);
  #65 and #66 dependabot bumps of two workflow actions; #67 `plan-adherence` and #68 `revision` drafts.
- Still true: branch protection is absent on `main`; the `triage` label does not exist; local runs need
  `GH_TOKEN`/`GITHUB_TOKEN` unset and there is no `gh` binary in the container; a pull request that cleans up
  after a tap or a retirement carries `Work-Item: <the item whose index it regenerates>` or, for a docs-only
  change, no line at all and then passes only while the pointer names an item with a complete approved chain.

## Task state (2026-09-13 ~23:15 UTC) — HISTORY, superseded by the section above
- **`.sdlc/active` names `ci-budget`.** Both of its code pull requests are merged (#71 `ed96584`, #72 `6cd63b1`);
  what is left is step 13 of `work/ci-budget/plan.md`, the seven acceptance numbers of its spec R14 on real
  runs, not before 2026-09-20, then the M5 revision, then the owner retires it. A routine already opens a
  session for that on 2026-09-20 15:00 UTC. Do not open a new work item for it.
- **`work/session-chaining` is merged** (#76, `2b469e7`): the protocol above, the chaining act in `sdlc-run`
  step 7, the two skill corrections plus `REVIEW.md`, one rendered pointer line in `docs/sdlc/rules/00-chain.md`,
  and the eval case `session-protocol-is-written-down`. **Retired** by the owner on 2026-09-14 (`a9a40d5`):
  all three artifacts `superseded`, one ledger line each, the pointer left on `ci-budget`, which is still
  the active item. That retirement left both index files stale, which is `index-after-approval` (PR #62)
  on the retirement route as well as the approval one — regenerated by the pull request carrying this line.
  This section is the first live run of step 7: (a) read `ci-budget` on `main` — a supervised merge moves no
  pointer — so no successor was scheduled; (b) and (c) are the handoff-only pull request that carries this
  line. One thing that run showed: (a) names three shapes for the pointer (empty, still the merged item, a
  granted unstarted item) and met a fourth, another supervised item already under way; the outcome is the
  same, no successor, but the sentence should say so. Second time it bites, it becomes a lesson.
- **The chain cannot yet be seen working end to end.** `delegated_merge.py`'s `advance()` pushes `HEAD:main`
  from a checkout taken before its own merge call and swallows the rejection (`:1123-1130`), so no delegated
  merge has ever moved the pointer; the fix is the owner's open PR #59. Until it lands, step 7's (a) succeeds
  only on a pointer the owner moved by hand.
- **Next after retirement**, from the mock walk's fix queue: `chain-check-robustness` (`kind: fix`),
  `adopt-ships-what-it-references`, `index-after-approval` (PR #62 is the fix); each touches a locked path, so
  each ends in the owner's click. The owner's retrospective of 2026-09-13 adds two unfiled defects: retiring a
  delegated item is impossible today (`superseded` needs a human approver and those artifacts carry
  `approved-by: claude`), and the ledger's sha slot is unvalidated.
- Still true from the section below: branch protection is absent on `main`; the `triage` label does not exist;
  local runs need `GH_TOKEN`/`GITHUB_TOKEN` unset and there is no `gh` binary in the container.

## Task state (2026-09-13 ~15:45 UTC) — HISTORY, superseded by the section above
- **One session per work item is the context protocol.** Durable state lives in git — `.sdlc/active`, each
  item's `log.md`, this file — and the session itself is disposable. A session takes one item from its
  approved intent to a merged pull request, then ends; the next session reads `.sdlc/active` from `main` and
  starts the next item. Subagents read and return evidence (paths, commands, outputs); the session holding the
  plan makes every edit (`knowledge/decisions/one-writer-until-ledger.md`). Nothing is lost to a context reset
  that was not lost anyway: the pointer on `main` is already correct.
- **`work/ci-budget` PR-A is merged** (#71, `ed96584`). What changed: a draft costs no gate and no review run,
  one run per pull request cancelled only by a new push, the gate's triage step is behind the owner's `triage`
  label, `agent-evals` is nightly and on demand only, and the merge script gained a `delegation` condition plus
  a supersession rule in `_pr_runs`. What did NOT change is the point of
  `knowledge/decisions/ci-budget-crucial-and-loosened.md` — read it before touching any of the six.
- **The one non-obvious thing in that diff**: `_pr_runs` drops a `cancelled` run only where a later run of the
  same **`workflow_id`** succeeded. Not the workflow *name* — the head branch writes workflow files, so a name
  join let a forged `sdlc-gate` launder the real gate's cancelled row. A run with no `workflow_id` supersedes
  nothing, deliberately.
- **A stale check-run row persists on a head sha.** PR #71's sha carried both a red `artifact-chain` row from
  the blocked run and a green one from the re-run the label triggered. `check_check_runs` has no supersession
  rule, so this is the open question against delegated merging; see the item's ledger for where it landed.
- **Branch protection is still absent** on `main` (spec C2). If it is ever created: require
  `sdlc-gate / artifact-chain`, never `agent-evals`, and leave "require branches to be up to date" off.
- **Local runs still need the token unset** and there is still no `gh` binary in the container, so anything
  that shells out to `gh` — `delegated_merge.py`, `github_metrics.py` without `--from-json` — cannot run here.

## Task state (2026-09-08 ~19:40 UTC) — HISTORY, superseded by the section above
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
- **`.sdlc/delegation.yaml` is the one tuning surface for the mode**, and on `main` today it reads
  `enabled: True`, `merge.enabled: true`, `require-checks: [sdlc-gate, pr-review]`, `cool-off-hours: 0`, with
  `docs/sdlc/handoff` on its `locked-paths` since `d035c6e`. (It stayed `enabled: false` from the owner's
  9e405fa until the owner flipped it; the note here said so long after it stopped being true.) A disabled
  policy closes every delegated path: `sign.py`, the hooks and `delegated_merge.py` all treat it the same as a
  missing one, so every artifact goes through the supervised path regardless.
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

## Seed prompt for the next session (refreshed by the finishing session, read by the next)
This section is the contract `sdlc-run` step 7 sends. The finishing session rewrites it for the next item at
(b), pushes it at (c), and passes the same text as the successor's payload at (d); it is refreshed every
cycle, never accumulated. It must be standalone — the next session has no conversation — and it names where
to look; it grants nothing. The successor re-reads `.sdlc/active` on `main` and the item's approved artifacts
before acting, whatever this section says. It is written for the state as of the merge of the pull request
that carries it, so it may run ahead of the "Task state" above by exactly that merge.

"Read docs/sdlc/handoff/HANDOFF.md on main, starting at 'Session protocol' and the newest 'Task state'
(2026-09-14 ~14:10 UTC). Nothing is in flight and no item is yours yet. `.sdlc/active` names
`advance-push`, which is finished and merged (#87 the chain, #89 the build): do not resume it. Before
anything else run `python3 scripts/gen_index.py --check` and `scripts/verify.sh` on main — a human
commit, a retirement or a tap leaves the indexes stale, and a branch cut inside that window fails verify
on a file nobody edited. Then ask the owner for two things and wait: to retire `advance-push` (its three
artifacts to `superseded`, one ledger line each, then the pointer moved), and to say which item is next.
That retirement is clean — its spec and plan are approved-by luissiviero, not agent-signed — so it will
not repeat the red chain the previous retirement produced. Three intents are open, each with unanswered
open questions carrying a proposal: #88 `retire-delegated-items` (risk-class medium, supervised, green
and mergeable), #60 `risk-detour` (low, the only grantable one, and what a queue that does not stop on
non-low work needs first), #61 `standing-grant` (medium, and it depends on the other two). An intent may
be merged with its questions still blank, but do not let it be tapped until they are answered: a tap
starts the spec on unconfirmed proposals. Never write approved, never merge, never move `.sdlc/active`.
Do not touch `ci-budget`, which has a scheduled session on 2026-09-20. The first delegated merge after
now is the production observation `advance-push` was built for: read its job log for `ADVANCE:
.sdlc/active -> <slug>` and check that main gained an advance commit whose first parent is the merge
commit, then record it in the next Task state. Run scripts/verify.sh, the chain check with --slug
<your item>, scripts/run_evals.sh and scripts/check_okf.py before asking the owner for anything."

(Superseded, kept as a record: the prompt before it named `advance-push` as the item to take from spec to
Build, with the two live merges `6c7be5f` and `ae69ebc` as the evidence its spec should cite. Before that,
the prompt named `approve-tap-regenerates-index` as the active
item with its follow-up #84 open, and told the next session to ask the owner which of that item and
`advance-push` went first. Before that: "Read docs/sdlc/handoff/HANDOFF.md on main, starting
at 'Session protocol' and the newest 'Task state' (2026-09-14 ~01:50 UTC). Two work items are approved and
unstarted, both intent-only: `.sdlc/active` names `approve-tap-regenerates-index`, granted `mode: delegated`,
so /sdlc-run can drive it grant to merge; and `advance-push`, `mode: supervised`, whose spec and plan can be
written now under the supervised skills but whose Build needs the owner to point `.sdlc/active` at it first.
Ask the owner which goes first and work only that one." Before that: "Read docs/sdlc/handoff/HANDOFF.md on main, starting
at 'Session protocol' and the newest 'Task state'. `.sdlc/active` names `ci-budget`; its code is merged and
its step 13 has a scheduled session of its own, so do not touch it. `work/session-chaining` is merged and
retired. Open no new work item until the owner retires `ci-budget` and points `.sdlc/active` at the next."
Before that: "Read docs/sdlc/handoff/HANDOFF.md on main, starting
at the newest 'Task state'. `.sdlc/active` names `ci-budget`: both of its code pull requests are merged, so
what is left is step 13 of work/ci-budget/plan.md — the seven acceptance numbers of spec R14 on real runs, one
week after PR-A merged, then the M5 revision over them, then I retire the item." Before that: "Read
docs/sdlc/handoff/HANDOFF.md on main, starting
at 'Task state'. work/delegated-mode is merged and no work item is open, so do not resume it: the next step is
the first live delegated item, which needs my grant first." And before that, the prompt that opened Batch B:
"Resume the lifecycle-axis SDLC work.
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
- `.sdlc/active` names the item under implementation, and the session never writes it: `.sdlc` is in
  `PROTECTED_PATHS`, so `protect-paths.sh` refuses the write, and an item's own pull request may not contain it
  (`ALWAYS_LOCKED`). It moves by the owner's delegation-grant tap (`--delegate --activate`; a supervised tap
  moves nothing), by the merge workflow's `advance()` on a delegated merge, or by the owner's hand — see
  "Session protocol".
  `require-plan.sh` blocks every write under `scripts/` (including Bash text that mentions
  `scripts`) until the active plan is approved by a `tech-lead`.
- Retiring an item is a human act, from the web editor today (`work/retire-active-pointer`): set
  `status: superseded` on `intent.md`, `spec.md` and `plan.md`, append one `approved -> superseded` (or
  `delegated -> superseded`) ledger line per artifact, and set `.sdlc/active` to the next item or to empty.
  `require-plan.sh` refuses a `superseded` plan; `check_artifact_chain.py` fails every pull request whose base
  already has `.sdlc/active` naming a retired item (the retiring pull request itself gets a note to move the
  pointer), and notes one whose `Work-Item` differs from the pointer. It also fails any pull request whose
  `Work-Item:` names a **retired** item, since every chain artifact must read `approved`: so a pull request
  cleaning up *after* a retirement (regenerating the indexes the web-editor route leaves stale, say) must
  leave the `Work-Item:` line off — `sdlc-gate.yml` then falls back to `.sdlc/active`, which names a live
  item. Verify such a pull request with the slug the gate will use, not with the default. Fix the body
  **before** the push: the gate resolves the slug from `github.event.pull_request.body` in the event payload,
  so a body edited after the push never reaches the run it was meant to fix, and re-running that run replays
  the same payload. Only the next push carries a corrected body. Nothing *retires* an item on merge
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
