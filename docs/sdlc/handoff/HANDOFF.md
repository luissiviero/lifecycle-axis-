---
type: doc
title: Session handoff (2026-09-18)
description: "How to resume in a new session: the session protocol, the task state, the owner's routine, and the seed prompt the finishing session leaves for the next one."
tags: [sdlc, handoff, playbook-comparison, delegated-mode]
timestamp: 2026-09-18T20:50:00Z
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
8. Deepening the clone is optional since 2026-09-17 (`work/self-check-false-reds`, defect 1): on a shallow
   clone the chain check now prints `history is shallow at <sha>` and skips the author check instead of
   attributing the approval to the boundary commit, so `verify.sh` stays green either way. `git fetch
   --unshallow origin` is still worth running when you want an author check that can actually run; a shallow
   clone can only decline to guess. Since 2026-09-18 (`work/chain-check-without-gh`, defect 3) the checks run
   bare: a token with no `gh` on `PATH` takes the same skipped path a missing token takes, so the
   `env -u GH_TOKEN -u GITHUB_TOKEN` prefix every session carried since 2026-09-08 is retired. If a command
   still ends `FileNotFoundError: 'gh'`, that is a regression, not the old workaround being forgotten.

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

## Task state (2026-09-18 ~20:50 UTC)
- **`chain-check-without-gh` (defect 3) is merged; the token workaround is dead on `main`; the retire tap
  is owed.** #111 merged by the owner's click as `c96184d` at 20:40 UTC. On `c96184d` **with the container's
  token set and no `gh` binary**: `VERIFY: PASS (c96184d)`, `INDEX: up to date`, `.sdlc/active` empty. This
  section is the first written without the `env -u` prefix; resume step 8 and "Hard facts" say so. The
  item's artifacts are still `approved` / `delegated` / `delegated`: the retire tap (`mode` `retire`, `slug`
  `chain-check-without-gh`, `next` blank) comes **after** this handoff pull request merges, because this pull
  request carries `Work-Item: chain-check-without-gh` and the gate's chain check on a retired slug is `FAIL`
  (the 22:45 section measured that order on defect 1).
- **What the item landed** (`work/chain-check-without-gh/spec.md` R1 to R7): `verify_dispatch_run`'s one
  `gh api` call is wrapped in `try`/`except FileNotFoundError` and returns `(None, NO_GH_NOTE)`, the tuple a
  missing token returns, so the caller's author rule still runs beneath it and an agent-authored trailer
  commit still ends `FAIL` (R2, the pull-request-51 property). A present binary that exits non-zero stays
  `False` (R4). Nothing runs before the call: the locked suite's `DispatchAttestation._verify` stubs
  `subprocess.run` at the `["gh", "api"]` boundary and never has a real `gh`, so the `shutil.which` guard the
  intent proposed would have turned five of its cases red on every machine without `gh`; spec gotcha 1,
  D3, and R6's pin. Six cases in the new `scripts/test_chain_no_gh.py`, three seen red in `ba86169` and green
  since `b9d38b4` with the module byte-identical; `test_check_artifact_chain.py` 94 green unmodified. Both
  real items that crashed on `17004b4` measured `CHAIN: PASS` with the token set before the ready flip.
- **Firsts, all measured in production.** (1) The first item driven under a grant through the detour rule:
  `revisions/1.md` and `revisions/2.md` are the repository's first `kind: detour` records, one per gate,
  each with two reviewers on models other than the writer (plan-reviewer on claude-sonnet-5,
  security-reviewer on claude-opus-5), each unanimous `revise`; the ledger names the writer
  (claude-fable-5-1) on every signing line at the security reviewer's ask. (2) The first park with `click
  needed`: #112, ledger-only, merged by the delegated merge at 17:24 UTC; its advance cleared the pointer on
  the empty queue **and regenerated the indexes it dirtied**, which is defect 1's fix (c) running for the
  first time on a real merge, with `INDEX: up to date` on the resulting `4d0ccbc`. (3) The first bare
  `VERIFY: PASS` on an item with a tapped approval since 2026-09-06 (`b9d38b4`, then `c96184d` on `main`).
  (4) Two pull requests open and ready at once for one item, as `check_pull_request` filters by head sha:
  the delegated merge took #112 and never saw #111.
- **The owner's acts this cycle, for the record.** Intent tap (supervised) at 11:38 UTC; the five answers
  pasted at 14:15 UTC; a second tap that found nothing to write; the pointer set by hand at 16:20 UTC; a
  **retire tap by mistake** at 16:21 UTC (`mode` `retire` instead of the pointer edit), which superseded the
  intent and cleared the pointer; `risk-class` edited to `low` and the answer to question 3 revised; one
  `delegated` tap at 16:49 UTC that re-approved the intent, wrote the grant and set the pointer in one run;
  the click on #111 at 20:40 UTC. The ledger shows `approved -> superseded -> approved` honestly. `approve.py`
  accepts a superseded artifact back to `approved`, which is what made the recovery one tap.
- **Reviews.** Three automated reviews on #111 (`9afe0f6`, `2143b32`, `fc93e98`), `Important: 0` each,
  and one on #112, `Important: 0 | Nits: 0`. Taken: two plan-bullet nits (`35edf62`), the docstring naming
  both causes of the caught exception (`3982151`), and the plan bullet re-quoted with deviation 1 logged
  (`fc93e98`). Left for a human, because `protect-tests.sh` locks the new module the moment it exists: in
  `scripts/test_chain_no_gh.py`, `_env` keeps the ambient `HOME` and `shutil.which("git")` (add
  `GIT_CONFIG_GLOBAL=/dev/null` and skip when `REAL_GIT` is `None`), and the `cac.subprocess.run = fake`
  rebinding wants a scope comment. Both threads are resolved with that answer.
- **Gotchas of record, each a first occurrence, none a lesson yet.** A ledger note may not contain `|`: it
  is the field delimiter, and `log_ledger.py` reports the line `MALFORMED` (the park line was rewritten
  with "Important 0 and Nits 3"). A code commit whose plan bullet quotes its text must carry the plan edit in
  the same commit; `3982151` did not and the re-review caught it. A reviewer subagent ended a report that
  found no fault with the word `keep`, which the template defines as a rejection; asked once which meaning it
  intended, it corrected to `revise`, and `revisions/2.md` holds the original word, the question and the
  answer verbatim. `sign.py --revision` on a first signature warns and proceeds, and `check_revisions`
  validates re-signatures only, so a detour record at a first signature is validated by its reviewers and
  the ledger note's shape, not by the chain check. `protect-approvals.sh` refuses any Bash line naming
  `approve.py`, a `grep` included: read that script with the file tools.
- **Still open for the owner, in no order.** The retire tap for `chain-check-without-gh` after this pull
  request merges; `standing-grant` (`main`, `in-review`, `mode: supervised`, `risk-class: medium`);
  **defect 2** (`EXEMPT` in the chain check lists `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`), which can
  absorb the stale `evals/` sentence in `check_artifact_chain.py`'s module docstring at `:23`; the two red
  `delegated-merge` runs `34908767884` and `34909007398`, still unread; the two nits on
  `scripts/test_chain_no_gh.py` above; step 7(c)'s wording (a handoff pull request after a retire tap cannot
  carry the retired slug), still the one-line doc fix the 22:45 section named. `ci-budget` keeps its own
  session on 2026-09-20 15:00 UTC.
- **How this session ended.** Step 7(a) read an empty pointer on `main`: the queue is done. 7(b) is this
  section and the seed prompt below. 7(c) is this pull request, ready with `Work-Item:
  chain-check-without-gh`, whose chain check is in-progress mode on a slug still `approved`, so it passes;
  the owner merges it by click (`docs/sdlc/handoff` is a `locked-paths` entry). 7(d): no successor, the
  queue is empty and (a) found no item. Both of this session's check-in triggers were deleted once #111
  merged; the only routine left is `ci-budget`'s. Nothing was approved or superseded by this session;
  spec.md and plan.md were signed `delegated` under the grant; no grant key was touched; `.sdlc/active` was
  written by the owner's taps and the merge workflow's advance only.

## Task state (2026-09-17 ~22:45 UTC) — HISTORY, superseded by the section above
- **`self-check-false-reds` (defect 1) is retired; `.sdlc/active` is empty; `main` is green with the empty
  pointer, which is the first production confirmation of fix (a).** After the 19:00 section: #108, the
  handoff refresh, merged by click as `4766f1c` (19:11 UTC); then the owner's retire tap landed as `17004b4`
  (22:30:25Z, `mode` `retire`, `slug` `self-check-false-reds`, `next` blank): three artifacts `superseded`,
  three retiring ledger lines by `luissiviero`, `.sdlc/active` emptied, `work/self-check-false-reds/index.md`
  and `work/index.md` regenerated in the same commit. On `17004b4` with the token unset: `note: no active work
  item (.sdlc/active is empty); the diff touches no code, so there is no chain to prove`, `CHAIN: PASS`,
  `EVALS: 49 pass, 0 fail, 6 skipped`, `INDEX: up to date`, `OKF: 232 docs, 0 warnings`, `VERIFY: PASS
  (17004b4)`; `python3 scripts/next_item.py --list` prints nothing. The same state on 2026-09-15 (`4eb8383`)
  was `VERIFY: FAIL` on both lines, and the 01:50-to-03:10 sections' placeholder `next` is no longer needed:
  this is the first retirement with `next` blank, and nothing had to be healed afterwards.
- **The owner named the next item: defect 3.** Reproduced on `17004b4` before writing this: with the
  container's token set and no `gh` binary, `scripts/verify.sh` ends in `FileNotFoundError: [Errno 2] No such
  file or directory: 'gh'` and `VERIFY: FAIL`. The cause is two lines apart in `scripts/check_artifact_chain.py`:
  `:233` returns `None` with a skipped-attestation note when *no* token is set, and `:237` then runs
  `subprocess.run(["gh", "api", ...])` unconditionally, so a container with a token and no binary — every
  remote session this repository has run in — raises instead of returning. The guard exists; it guards the
  wrong condition. The successor's task is that item's `/sdlc-intent` only, stopping at the owner's tap;
  expect `risk-class: medium` (it changes the gate script, as defect 1 did), so `mode` `supervised` and a tap
  at every gate; the code merge is the owner's click whatever the class, because `check_artifact_chain.py` is
  a `locked-paths` entry. Merge each artifact's pull request before tapping it: `approve.yml` checks out the
  dispatched ref and `work/<slug>/` must exist on `main`.
- **Still open for the owner, in no order.** `standing-grant` (`main`, `in-review`, `mode: supervised`,
  `risk-class: medium`); **defect 2** (`EXEMPT` in the chain check lists `CLAUDE.md` but not
  `GEMINI.md`/`AGENTS.md`), which can absorb the stale `evals/` sentence in `check_artifact_chain.py`'s module
  docstring at `:23`; the two red `delegated-merge` runs `34908767884` and `34909007398`, still unread.
  `ci-budget` keeps its own session on 2026-09-20 15:00 UTC.
- **How this session ended.** This handoff pull request carries no `Work-Item:` line, against the letter of
  `sdlc-run` step 7(c) ("the slug just merged"), because that slug is now retired and the gate's chain check
  on it is `FAIL: work/self-check-false-reds/intent.md status is 'superseded', must be 'approved'` (measured
  on this branch with the gate's own invocation, `--base origin/main --slug self-check-false-reds`); the
  successor's slug has no intent yet, so it fails too, as 7(c) itself says. With no line the gate falls back
  to `.sdlc/active`, which is empty, and the chain check takes fix (a)'s path: `note: no active work item
  ...`, `CHAIN: PASS` — its first run in CI on a real pull request. Step 7(c)'s wording assumes the merged
  slug is still `approved`, which stops being true once the retire tap lands first; a one-line doc fix for
  the owner, not made here. Step 7(a) read an empty pointer, which by the letter of (d) means no successor;
  the owner asked for one by word, as on 2026-09-15, so one successor was scheduled with the seed prompt
  below and nothing else. Both of this session's check-in triggers were deleted once #106 and #108
  merged; the only routine left is `ci-budget`'s. Nothing was signed, approved or superseded by this session,
  no grant key was touched, and `.sdlc/active` was written only by the owner's tap.

## Task state (2026-09-17 ~19:00 UTC) — HISTORY, superseded by the section above
- **`self-check-false-reds` (defect 1) is merged; all three faults are dead on `main`; `main` is green.**
  #106 merged by click as `4194263` at 18:57 UTC — the owner's own click, because the diff touches two
  `locked-paths` scripts. On `4194263`: `VERIFY: PASS`, `INDEX: up to date`, `EVALS: 49 pass, 0 fail`,
  `OKF: 232 docs, 0 warnings`. The item ran the full four-gate chain, every gate a human tap:
  intent `d3bd674` (#103), spec `ba6c885` (#104), plan `0d8598d` (#105), code #106.
- **What the item landed** (`work/self-check-false-reds/spec.md` R1 to R8), each fault proven by a test
  module committed red on its own before its fix, with the other two staying red across it:
  (a) `check_artifact_chain.py` — the diff and its two fail-closed guards moved into `_changed_paths(base)`,
  computed before the slug is read, and the no-slug decision is made on it: every changed path under an
  `EXEMPT` prefix is `note: no active work item ...` and `CHAIN: PASS` exit 0; anything outside `EXEMPT`
  keeps today's `FAIL` (R1, R2, R3; D1 substitutes `EXEMPT` for `own_artifact`, which closes over the slug;
  D2 keeps the base-ref and dirty-tree guards ahead of the pointer). (b) `_is_graft(sha)` reads the file
  `git rev-parse --git-path shallow` names and answers by membership; both `-G` lookups take their existing
  "author check skipped" note branch when the commit they found is the graft, and nothing ever fetches
  (R4, R5, R6; D3, D4). (c) `advance()` imports `gen_index` and, after its ledger appends, renders through
  `render_all` but writes only `work/<merged>/index.md`, `work/<next>/index.md` and `work/index.md`,
  appending exactly those to the `written` allowlist, whose refusal at `:1169` is untouched (R7, R8; D6 —
  `render_all` is repo-wide, 29 paths today, and feeding all of them in would have widened the allowlist).
- **Both production shapes are measured on `main` itself, not only in fixtures.** A depth-1 clone of
  `4194263` ends `CHAIN: PASS` with three `history is shallow at 419426329810` notes; its boundary is
  *human*-authored, so before the fix that clone would have **silently passed** by attributing all three
  approvals to the merge commit — the false pass is closed along with the false fail. And `4eb8383`'s shape
  rebuilt on `main` (pointer emptied by a `github-actions[bot]` commit, then a docs-only commit) ends
  `note: no active work item (.sdlc/active is empty); the diff touches no code, so there is no chain to
  prove` / `CHAIN: PASS`, with `INDEX: up to date`; add one `scripts/` path to the same diff and it is
  `CHAIN: FAIL` again, which is R2 doing its job. **The next delegated merge with an empty queue leaves
  `main` green with no tap.**
- **One thing only a human could do, and the hook said so.** Fix (a) turns `ActiveSlugRequired`'s two cases
  red: they pin the exact `FAIL` line R1 replaces. `.claude/hooks/protect-tests.sh` locks every existing
  test file under `kind: fix` and its message directs the agent to "say so and stop; a human changes it" —
  so the session stopped, stated the case, and held fix (a) as a patch for 24 hours while (b) and (c)
  proceeded. The owner edited both cases by hand (`5dc6c0c`, `6b24c62`); `work/delegated-mode` R-6's intent
  (one clear line, not a cascade) survives as one clear note. **This is the loop-protection hook working as
  designed on a real item, and the first time it has blocked this repository's own work.** Three deviations
  logged of five: the fixture base-class name, the step order, and the test file joining the file list.
- **Two automated reviews, `Important: 0` both times**, on Opus 5. The second caught that the pull request's
  title and body still read "fix (a) held" after `35834c5` landed — stale prose, not a defect; corrected
  before the merge. The first item's review (#104) had earlier caught a real design fault: R7's acceptance
  test was unsatisfiable against `render_all`, which produced D6.
- **Still open for the owner, in no order.** `standing-grant` (`main`, `in-review`, `mode: supervised`,
  `risk-class: medium`); **defect 2** (`EXEMPT` in the chain check lists `CLAUDE.md` but not
  `GEMINI.md`/`AGENTS.md`) and **defect 3** (the chain check crashes on a token with no `gh` binary), each
  still needing a `/sdlc-intent`; the two red `delegated-merge` runs `34908767884` and `34909007398`, still
  unread. **New, found while writing this item's spec and deliberately not fixed in it**: the module
  docstring at `check_artifact_chain.py:23` says check 3 exempts `evals/`, but `EXEMPT` at `:55` has no such
  entry and the comment at `:53` says the omission is deliberate — the docstring is stale, and since it is
  also an `EXEMPT` defect it may belong with defect 2.
- **`.sdlc/active` still names `self-check-false-reds`** and this session never wrote it. The owner moves it
  by hand for a supervised item (`approve.yml` passes `--activate` only for `mode: delegated`); with (a)
  fixed, a retire tap with no `next` now leaves it empty and `main` stays green, so the placeholder slug the
  01:50-to-03:10 sections needed is no longer necessary.
- **Still true**: run the checks with `env -u GH_TOKEN -u GITHUB_TOKEN` (defect 3). Resume step 8's
  `git fetch --unshallow origin` is **no longer required for correctness** — a shallow clone now says so
  instead of misreporting — but it is still worth doing, because a shallow clone cannot verify an approval
  at all, only decline to guess. This session's container arrived with no repository cloned and the repo
  outside its authorized set; `add_repo` with `access: push` fixed both, and the clone came down complete.

## Task state (2026-09-15 ~03:10 UTC) — HISTORY, superseded by the section above
- **The cycle is closed: `parked-marker-on-retired` is merged and retired, the handoff is on `main`, and
  `main` is green.** After the 03:00 section: the owner's retire tap landed as `e8ec522` (03:05:27Z, three
  artifacts `superseded`, three retiring ledger lines by `luissiviero`, `.sdlc/active` repointed to
  `ci-budget`, every stale index regenerated in the same commit), and #101, the 03:00 handoff refresh,
  merged by click as `5bf9573`. On `5bf9573`: `INDEX: up to date`, `VERIFY: PASS (5bf9573)`,
  `python3 scripts/next_item.py --list` prints nothing. Nothing is granted and nothing is in flight.
- **The advance's two production effects are now both observed and both healed by the one tap**, exactly as
  the 03:00 section predicted: the pointer it empties (defect 1's common case) and the indexes it leaves
  stale (`work/<slug>/index.md` and `work/index.md`, because `advance()` appends a ledger line without
  regenerating). Between `4eb8383` and `e8ec522` every pull request was red on both lines. Both belong to
  **defect 1's intent**, which is now the strongest candidate: its fix would let the advance regenerate what
  it dirties and note an empty pointer instead of failing, retiring the placeholder `next` the retire tap
  needs today.
- **`.sdlc/active` names `ci-budget`, and that is a placeholder, not an item to work.** The retire tap's
  `next` input put it there so `verify.sh` has a slug; `ci-budget`'s own work keeps its scheduled session on
  2026-09-20 15:00 UTC. No session takes it, and the pointer moves again at the next grant tap.
- **A successor session was opened by this session with the seed prompt below** (step 7(d), its second use
  ever), at the owner's word, to draft **defect 1's intent** — `/sdlc-intent` needs no grant, so the session
  drafts it `in-review` on its own branch, opens the intent-only pull request, and stops for the owner's
  approval tap. Approving it with `mode` `delegated` also repoints `.sdlc/active` at it, and a later session
  runs it end to end. Nothing about that prompt grants anything.
- **Still open for the owner, in no order.** `standing-grant` (`main`, `in-review`, `mode: supervised`,
  `risk-class: medium`; the low-only policy cannot grant it, so it runs with a tap at every gate; its
  answers 3 and Depends-on line are overtaken, see the 00:35 section); defect 2 and defect 3, each still
  needing a `/sdlc-intent`; the two red `delegated-merge` runs `34908767884` and `34909007398`, still
  unread.
- **Still true**: deepen the clone first (resume step 8) and run the checks with
  `env -u GH_TOKEN -u GITHUB_TOKEN`; the defects keep the 01:50 section's numbers (defect 1: the self-check
  fails on an empty pointer instead of noting it, and misattributes approvals on a shallow clone, one
  intent; defect 2: `EXEMPT` in the chain check lists `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`; defect 3:
  the chain check crashes on a token with no `gh` binary). The session that wrote this section wrote
  `parked-marker-on-retired` on Fable 5.1 and was switched to Opus 5 by the owner after the merge, so this
  handoff and the item it reports are not the same model's work; the item's own review ran on Opus 5
  against the Fable 5.1 writer, as its ledger records. Both `send_later` check-ins this session armed were
  deleted once #100 merged, so nothing wakes it again.

## Task state (2026-09-15 ~03:00 UTC) — HISTORY, superseded by the section above
- **`parked-marker-on-retired` is merged by the delegated-merge workflow and its advance landed; `.sdlc/active`
  is empty; nothing is queued.** #100 merged as `94f89de` at 02:53 UTC by `github-actions[bot]` (run
  `34922908400`, triggered by the `pr-review` completion): nine `CONDITION ... ok` lines (`locked-paths: ok —
  8 changed file(s), none locked`; `review: ok — pr-review run 34922712662 reports Important: 0 | Nits: 0`),
  then `ADVANCE: .sdlc/active -> (empty queue)` and `DELEGATED-MERGE: merged #100 ffda529...`. `main` then
  gained `4eb8383` (`[queue-empty] Advance .sdlc/active after #100 merged`, author `github-actions[bot]`,
  first parent `94f89de`), which empties `.sdlc/active` and appends `PR #100 | in-review -> in-review |
  github-actions[bot] | 94f89de | merged as 94f89de; the queue is empty, .sdlc/active cleared` to the item's
  ledger. **That is the first delegated merge since `risk-detour` landed and the production observation
  `advance-push` was built for: the advance pushes.** The park's advance skip stays fixture-only (nothing
  parked was in the queue behind this item).
- **What the item landed (`work/parked-marker-on-retired/spec.md` R-1 to R-6).** `gen_index.build_item` asks
  `next_item.parked_note` only when `intent.md` reads `status: approved` (the queue's own comparison), so a
  retired item renders like any other: the `risk-detour` row's stage cell reads `plan` and its index has no
  `Parked:` line; `next_item.py` untouched. Two cases in the new module `scripts/test_gen_index_retired.py`,
  committed red on their own (`c63ac83`) before the condition (`8e99321`). Review: `plan-reviewer` and
  `security-reviewer` on Opus 5 against a Fable 5.1 writer, `Important: 0 | Nits: 6`, three carried into
  the code (`ffda529`: the approvers file is still read per item so a malformed one fails loudly; one
  spelling with the queue's guard; the import comment); the automated review on `ffda529` ended
  `Important: 0 | Nits: 0`. Two `deviation:` ledger lines of five (two acceptance-test sentences and a
  design line in the signed spec corrected after measurement; no requirement or test changed).
- **`main` at `4eb8383` is red for two reasons, and one tap heals both.** `scripts/verify.sh` ends
  `VERIFY: FAIL`: `FAIL: no active work item (.sdlc/active is empty ...)` (defect 1 below), and
  `INDEX: 2 file(s) drifted` (`work/parked-marker-on-retired/index.md`, `work/index.md`): the advance commit
  appends a ledger line and empties the pointer but regenerates no index, so the item's `Last gate:` and its
  row are stale. A first occurrence, noted here rather than as a lesson; the retire tap regenerates every
  stale index on `main` (`work/approve-tap-regenerates-index`) and points the pointer, so the next tap fixes
  both. Every pull request opened before that tap is red on these two lines, this session's handoff pull
  request included; the owner merges it by click as always (`docs/sdlc/handoff` is a locked path).
- **Two things for the owner, in this order.** (1) Retire `parked-marker-on-retired` by tap with `next`
  `ci-budget`: **Actions -> approve -> Run workflow** on `main`, `mode` `retire`, `slug`
  `parked-marker-on-retired`, `next` `ci-budget`. (2) Merge the handoff pull request that carries this
  section. Then name the next item; nothing is granted, so no session has an item until a grant tap.
- **Nothing is granted; the next item is the owner's choice.** Candidates: `standing-grant` (`main`,
  `in-review`, `mode: supervised`, `risk-class: medium`; runs supervised with the owner's taps at every gate;
  its answers 3 and Depends-on line are overtaken, see the 00:35 section); the three defect intents below,
  each a `/sdlc-intent` (defect 1 now has its common case on record: every delegated merge with an empty
  queue leaves the pointer empty, so its fix would retire the placeholder `next`). `ci-budget` keeps its
  session on 2026-09-20 15:00 UTC and works by slug.
- **Still true**: deepen the clone first (resume step 8) and run the checks with
  `env -u GH_TOKEN -u GITHUB_TOKEN`; the two red `delegated-merge` runs `34908767884` and `34909007398` are
  unread; the filed defects keep the 01:50 section's numbers (defect 1: the self-check fails on an empty
  pointer instead of noting it, and misattributes approvals on a shallow clone, one intent; defect 2:
  `EXEMPT` in the chain check lists `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`; defect 3: the chain check
  crashes on a token with no `gh` binary). No successor was scheduled: the queue is empty, so step 7(d)
  did not fire; the `send_later` check-ins this session armed were deleted at handoff, so no second session
  acts on #100 or on the handoff pull request.

## Task state (2026-09-15 ~02:30 UTC) — HISTORY, superseded by the section above
- **`parked-marker-on-retired` is granted and `.sdlc/active` names it; it is the whole queue.** After the
  01:50 section: the owner locked `scripts/next_item.py` (`796d47b`, intent `risk-detour` Q5, done), merged
  the handoff refresh #97 (`b15bacb`), retired `risk-detour` by tap with `next` `ci-budget` (`fd39dd0`:
  three artifacts `superseded`, pointer `ci-budget`, indexes regenerated), then chose a separate low item for
  the one defect that retirement exposed: the retired item's `work/index.md` row still read `parked` and its
  index kept the `Parked:` line, because `gen_index.py` reads only the latest `parked:`/`resumed:` ledger
  line and a retirement writes neither word. The session drafted `work/parked-marker-on-retired/intent.md`
  (#98, `0a6d336`, one open question answered by the owner: the marker reads `parked` only for
  `status: approved`), and the grant tap landed as `bad2b14` (`approved`, `mode: delegated`,
  `delegated-on: 2026-09-15`, pointer moved to the item). On `bad2b14`: `INDEX: up to date`,
  `VERIFY: PASS (bad2b14)`; `python3 scripts/next_item.py --list` prints `parked-marker-on-retired` and
  nothing else.
- **What the next session does: `/sdlc-run` on `parked-marker-on-retired`, spec to merged pull request.**
  `kind: fix`: the regression case goes in a new module (`scripts/test_gen_index_retired.py`, the intent
  names it; existing test files are locked under fix) and is seen red before the one condition in
  `scripts/gen_index.py` changes; `next_item.parked_note` does not change (intent Must). Its file list is
  `scripts/` and generated indexes only, so `check_detour.py` ends `DETOUR: none` and the delegated merge
  should take the pull request: **this is the first delegated merge since `risk-detour` landed and the
  production observation `advance-push` was built for.** Read the `delegated-merge` job log for
  `ADVANCE: .sdlc/active -> (empty queue)` (the queue behind it is empty, so the advance clears the pointer),
  check that `main` gained an advance commit whose first parent is the merge commit, and record both in the
  next Task state. An empty pointer then makes `verify.sh` end `FAIL: no active work item` on every later
  pull request (defect 1 below), so the next session's first ask to the owner is the retire tap with `next`
  set to a placeholder, as on 2026-09-14.
- **The predicted refusal on `risk-detour` is on record and the park machinery is in production.**
  `delegated-merge` run `34917675636` ended `DELEGATED-MERGE: refused (locked-paths)` on
  `.claude/skills/sdlc-intent/SKILL.md`; `next_item.py` skipped the parked item while it was active (the
  queue printed nothing at `e7fa769`); the advance's own skip of a parked item is still proven on the merge
  tests' fixture only.
- **Still true**: deepen the clone first (resume step 8) and run the checks with
  `env -u GH_TOKEN -u GITHUB_TOKEN`; the two red `delegated-merge` runs `34908767884` and `34909007398` are
  unread; the filed defects keep the 01:50 section's numbers (defect 1: the self-check fails on an empty
  pointer instead of noting it, and misattributes approvals on a shallow clone, one intent; defect 2:
  `EXEMPT` in the chain check lists `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`; defect 3: the chain check
  crashes on a token with no `gh` binary); `standing-grant` stays in-review, supervised, medium; `ci-budget`
  keeps its session on 2026-09-20 15:00 UTC. The successor for this state was scheduled by the finishing
  session through the session API (step 7(d)), the first time (d) has fired; no other trigger is armed.

## Task state (2026-09-15 ~01:50 UTC) — HISTORY, superseded by the section above
- **`risk-detour` is merged; `.sdlc/active` still names it, parked; nothing is queued.** The owner merged #96
  by click at 01:45 UTC (`c377b0c`) and #95, the earlier handoff refresh, right after (`e7fa769`). The pointer
  was last written by the grant tap (`3ce6eae`) and a click runs no advance, so it still reads `risk-detour`.
  On `e7fa769`: `VERIFY: PASS (e7fa769)`, `INDEX: up to date`, `CONTEXT: 3 files up to date`;
  `python3 scripts/next_item.py --list` prints nothing (the item's spec is signed and its ledger's last
  `intent.md` line is `parked: ready PR #96; click needed (.claude/skills/sdlc-run/SKILL.md)`, so the new
  queue rule skips it twice over); `work/index.md` shows its stage cell as `parked`, the item's own R-6
  rendered on itself.
- **The predicted refusal happened.** `delegated-merge` run `34917675636` on `main` (01:32 UTC, after the
  `pr-review` completion on #96) ended `CONDITION locked-paths: refused — .claude/skills/sdlc-intent/SKILL.md
  is under the locked path '.claude'` / `DELEGATED-MERGE: refused (locked-paths)`; the five conditions before
  it were `ok`. That is one red run per check completion on a locked-path pull request, as the 14:10 section
  explains, and the reason the merge was a click. No delegated merge has run since, so the park's advance
  (`next_item.py` skipping a parked item inside `advance()`) is proven on the merge tests' fixture
  (`scripts/test_park_advance.py`) and still unobserved in production, like `advance-push` before it.
- **What `risk-detour` landed (`work/risk-detour/spec.md` R-1 to R-10, `knowledge/decisions/risk-detour.md`).**
  `scripts/check_detour.py` (`--paths`, `--plan`, `--diff`; `DETOUR: none` exit 0 or `DETOUR: needed (<n>)`
  exit 3, through `delegated_merge.check_locked_paths` per path); `kind: detour` and `## Route` in the revision
  template; `parked:`/`resumed:` on `intent.md` ledger lines, read by `next_item.parked_note` (a `resumed:`
  counts only from an actor holding the `intent.md` role in `.sdlc/approvers.yaml`) and by `gen_index.py`;
  `## The detour rule` in `sdlc-run`, one check step each in `sdlc-spec`, `sdlc-plan`, `sdlc-intent`; three
  eval cases; two rule bullets rewritten with no net line (adopter's render `120 119 99`, at the cap). Review:
  two passes on Opus 5 found two Important defects on `49ba7f3` (C-quoted diff names hid locked files; any
  actor's `resumed:` lifted a park), fixed in `cffcedd`; the automated review on `15ef690` ended
  `Important: 0 | Nits: 1`. Five `deviation:` ledger lines, exactly the policy cap.
- **Two things for the owner, in this order.** (1) Intent Q5, not yet done at `e7fa769`: add
  `scripts/next_item.py` to `locked-paths` in `.sdlc/delegation.yaml` on `main` (line 64, the web editor; the
  advance reads that script, so a delegated pull request must not change it under the merge that reads it).
  (2) Retire `risk-detour` by tap with `next` set to a placeholder such as `ci-budget`, as on 2026-09-14: an
  empty pointer still makes `verify.sh` end `FAIL: no active work item` (defect 1 below), so every pull request
  would be red until the pointer names something.
- **Nothing is granted; the next item is the owner's choice.** Candidates: `standing-grant` (`main`,
  `in-review`, `mode: supervised`, `risk-class: medium`; the policy delegates `low` only, so it runs supervised
  with the owner's taps at every gate, and its answers 3 and Depends-on line are overtaken, see the 00:35
  section); the four defects below, three `/sdlc-intent`s, numbered in the "Still true" bullet (all low, all
  grantable; the chain check and `verify.sh` are locked paths, so their pull requests are clicks too). `ci-budget` keeps its session on
  2026-09-20 15:00 UTC and works by slug.
- **One new gotcha from this session, a first occurrence with no lesson file yet:** a commit staged before
  `gen_index.py` ran carried stale indexes (`cffcedd`, `INDEX: 2 file(s) drifted` on the runner; the next
  commit carried the regeneration): regenerate, then `git add`, then commit. The token-without-`gh` crash hit
  this session too, but it is not new: "Hard facts" below records it with the `env -u GH_TOKEN -u GITHUB_TOKEN`
  workaround, the 2026-09-08 section says it bit two sessions before it was written down, and it is defect 3
  below, whose fix is the intent it still needs rather than another gotcha line.
- **Still true**: the container clone is shallow, deepen first (resume step 8); the two red
  `delegated-merge` runs `34908767884` and `34909007398` on `cb5cde5`/`8f4bb3c` are still unread; the filed
  defects each need an intent, numbered here so the references above and in later sections mean one thing:
  defect 1, the self-check fails on an empty pointer instead of noting it, and misattributes approvals on a
  shallow clone (one intent, as the 00:10 section decided); defect 2, `EXEMPT` in the chain check lists
  `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`; defect 3, the chain check crashes on a token with no `gh`
  binary instead of returning the no-token note. Older sections list the same three in other orders. The
  `send_later` check-in this session armed was deleted at handoff, so no second session acts on #96.

## Task state (2026-09-15 ~00:35 UTC) — HISTORY, superseded by the section above
- **`risk-detour` is granted and `.sdlc/active` names it; nothing else is queued.** The owner answered
  the sixth open question on #60 (`0e7eb1a`: the intent-drafting gate re-signs nothing, the route goes
  into the in-review intent's Proposed outcome, the tap is the sign-off), merged #60 (`27457ba`), #61
  (`4c17609`) and #94 (`ae35caf`), then tapped the grant: run `34913272819`, commit `3ce6eae`, `status:
  approved`, `mode: delegated`, `approved-by`/`delegated-by: luissiviero`, `delegated-on: 2026-09-15`,
  ledger line `in-review -> approved | luissiviero | ae35caf | mode: delegated`, and the pointer moved
  from `ci-budget` to `risk-detour` in the same commit with the indexes regenerated. On `3ce6eae`:
  `INDEX: up to date`, `CONTEXT: 3 files up to date`, `CHAIN: PASS` (in-progress mode, intent only),
  `VERIFY: PASS (3ce6eae)`. `python3 scripts/next_item.py --list --exclude risk-detour` prints nothing:
  the queue is this one item.
- **What the next session does: `/sdlc-run` on `risk-detour`, spec to ready pull request.** Its
  precondition holds on `main` (`enabled: True`, `risk-classes: [low]`, the intent approved and
  delegated, the pointer set). Steps 1 to 5 as the skill says: `/sdlc-spec` and `sign.py risk-detour
  spec.md`, `/sdlc-plan` and `sign.py risk-detour plan.md`, build on a `claude/` branch, verify at every
  step, `/sdlc-review` on a different model, ready. **Expect the merge to be the owner's click, not the
  workflow's.** The intent's file list names `.claude/skills/*`, `docs/sdlc/templates/*` and
  `docs/sdlc/rules/*`, all on the merge script's `ALWAYS_LOCKED` floor, so the delegated merge will end
  `refused` on locked paths whatever else holds. None of those paths is in `PROTECTED_PATHS`, so the hooks
  let the build proceed; the skill's "locked path ends the queue quietly" case applies at the merge, not
  at the plan gate. Do not stop at the spec or plan because the merge is locked: finish to a ready pull
  request and say so, which is the intent's own first answer, verbatim from `work/risk-detour/intent.md`:
  "finish to a ready pull request and park with `parked: ready PR #<n>; click needed (<path>)`, so the
  pointer moves on" (the `parked:` line itself is what this item builds; until then, say it in the pull
  request). Because the merge is a click, no `advance()` runs on it and the production
  observation `advance-push` waits for is still unobserved; the pointer stays on `risk-detour` until
  the owner retires it by tap (`mode: retire`, `next` blank or the next item).
- **`standing-grant` is on `main`, `in-review`, `mode: supervised`, `risk-class: medium`.** Its six
  answers stand as written on 2026-09-08. Two are overtaken and a spec writer should read them with
  that in mind: answer 3 (this item's pull request clears the pointer after #58) is moot, the pointer is
  moved by the retire tap's `next` and by the delegated merge's advance today; and its Depends-on line
  names `advance-push`, merged, and `risk-detour`, now real and active. Not this session's item.
- **Still true from the section below**: the container clone is shallow, deepen it first (resume step
  8); the two red `delegated-merge` runs on `main` (`34908767884`, `34909007398`) are unread; the four
  defects (empty pointer and shallow misattribution in the chain check, `EXEMPT` without `GEMINI.md`/
  `AGENTS.md`, the crash on a token with no `gh`) each need an intent; `ci-budget` has its session on
  2026-09-20 15:00 UTC and works by slug, since the pointer no longer names it.

## Task state (2026-09-15 ~00:10 UTC) — HISTORY, superseded by the section above
- **`.sdlc/active` names `ci-budget` as a placeholder, and `main` verifies green on a full clone.** After
  the section below was written, the owner re-ran the retire tap with `next` set to `ci-budget` (run
  `34908559088`, commit `cb5cde5`, 23:22 UTC, touching only the pointer; the indexes were already current),
  and #93 merged as `8f4bb3c` at 23:25 UTC. On `8f4bb3c`: `INDEX: up to date`, `CONTEXT: 3 files up to
  date`, `VERIFY: PASS (8f4bb3c)`, `CHAIN: PASS`, `OKF: 213 docs, 0 warnings`; `protect-approvals.sh`
  refuses an Edit of `approved-by`, a Write carrying `status: approved` and a Bash line naming the approval
  script, exit 2 each. The only trigger left is `ci-budget`'s session on 2026-09-20 15:00 UTC.
- **New: a shallow clone makes the chain check blame the wrong commit.** The remote container clones with
  a shallow boundary (15 commits in `.git/shallow` on 2026-09-15). `check_artifact_chain.py` attributes an
  approval with `git log -n1 -G '^status: approved$'`, and on a shallow clone the newest boundary commit
  that carries the file is the first hit: for `work/ci-budget/plan.md` that was `007b5c3`, an agent ledger
  commit, rather than the tap `104c27d`, so `verify.sh` ended `FAIL` on "the commit that set status:
  approved is authored by an agent identity". After `git fetch --unshallow origin` the same command ends
  `CHAIN: PASS`. Resume step 8 above now says to deepen first. The check itself could note or refuse a
  shallow repository (`git rev-parse --is-shallow-repository`) instead of misattributing; it is a locked
  path, so that is a fourth defect for the empty-pointer intent below, not an item of its own.
- **Not investigated**: two `delegated-merge` runs on `main` concluded failure, `34908767884` on `cb5cde5`
  and `34909007398` on `8f4bb3c`. The 14:10 section explains one red run per check completion on a pull
  request that is not the active item's; #93 carried `Work-Item: ci-budget`, which was the active item,
  so these two may be something else. Read their logs before the next merge.
- **Nothing is in flight and no item is granted.** The session that wrote this holds no item and asked
  the owner which is next. Candidates, unchanged: #60 `risk-detour` and #61 `standing-grant`, both with
  unanswered open questions; the three defects filed below each need an intent. `ci-budget` waits for
  its 2026-09-20 session.

## Task state (2026-09-14 ~19:00 UTC) — HISTORY, superseded by the section above
- **`retire-delegated-items` is merged (#92 as `ea289b7`, 18:49 UTC) and retired by the tap it built
  (`302becb`, 18:51 UTC), and `.sdlc/active` is empty.** The first `mode: retire` run in production is
  `34883307360`: run-name `approve intent.md (retire) on retire-delegated-items by @luissiviero`,
  conclusion success, one commit `[retire-delegated-items] Retire as luissiviero` authored by the owner,
  committed by `github-actions[bot]`, with `Approved-Run: 34883307360` / `Approved-Actor: luissiviero`,
  touching exactly the three artifacts (`approved -> superseded`, `approved-by` untouched), three ledger
  lines, `.sdlc/active` (cleared, `next` was blank) and the two indexes regenerated in the same commit.
  `python3 scripts/gen_index.py --check` on `main` prints `INDEX: up to date`: the retirement route's
  drift, filed as this item's second half, is closed on the tap route.
- **`main` is `VERIFY: FAIL` on the empty pointer, and that is the one consequence of blank `next` the
  spec under-described.** `scripts/verify.sh` runs `check_artifact_chain.py --base HEAD` with no slug, which
  with an empty `.sdlc/active` ends `FAIL: no active work item (.sdlc/active is empty; pass --slug or set
  it)`; `sdlc-gate` runs the same step, so every pull request is red on verify until the pointer names a
  live item, whatever `Work-Item:` it carries. The spec's G-6 named the pull-request half of this and not
  the verify half. The remedy is the tap the owner already has: re-run `mode: retire` on `main` with `slug`
  `retire-delegated-items` and `next` set to a live item; every artifact is already `superseded` (a no-op
  each), only the pointer moves, and the committer regenerates the indexes with it. The owner's second
  answer on the intent foresaw exactly this use ("the only tap that can point at a supervised item").
  `ci-budget` is the one live, fully approved item on `main` today; `risk-detour` becomes one when #60
  merges. The defect proper needs its own intent: the self-check (`--base HEAD`, no pull request) should
  treat an empty pointer as nothing to check, a note and `CHAIN: PASS`, rather than a failure; it is one
  branch in `check_artifact_chain.py`, a locked path, with a case in `ActiveSlugRequired`.
- **The item's record.** Intent `017c832`, spec `fa0ac9b`, plan `6016332`, all tapped; one review round
  on Opus (plan-reviewer three Important, security-reviewer none, nine nits, every finding taken with a
  case each); revision 1 signed by both reviewers and accepted by the owner's web-editor ledger line
  `ae0e759` (whose index drift `7f05b9b` regenerated, the web-editor route in action once more); the
  automated review on the final head `Important: 0 | Nits: 0`; merged with the `control-plane-approved`
  label for the workflow change. Two defects the reviews named are unfiled and need an intent each:
  `EXEMPT` in the chain check lists `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`, and the check crashes on
  a token with no `gh` binary instead of returning the no-token note. A third is the empty-pointer verify
  failure above. `CLAUDE.md` still says the tap takes three inputs; it takes five, and a retirement needs
  `next`.
- **Still open and unchanged**: the advance is unobserved in production until a delegated item merges;
  `protect-tests.sh` locks a new test file the moment it exists; #60 and #61 wait on the owner's merge and
  their open questions; `ci-budget` has a scheduled session on 2026-09-20.

## Task state (2026-09-14 ~17:30 UTC) — HISTORY, superseded by the section above
- **`retire-delegated-items` is built on `claude/retire-delegated-items`, pull request #92, and
  `.sdlc/active` names it.** The owner tapped intent (`017c832`, on `main`), spec (`fa0ac9b`) and plan
  (`6016332`) today; the build followed the plan's seven steps in one commit each. What changed: the chain
  check judges a `superseded` artifact by its retirer (the `-> superseded` ledger line's actor and the
  commit's author or verified trailer, bound to a `mode: retire` run-name), never by `approved-by`, which
  the approver list is asked about only where the ledger shows no signature for the artifact; the approval
  script gains `--retire` and `--next`; the dispatch helper's role gate requires every present artifact's
  role under `mode: retire` and its commit subject reads `Retire`; the workflow offers `mode: retire` and
  a `next` input with the run-name byte-identical. On `main`'s own tree,
  `python3 scripts/check_artifact_chain.py --base HEAD --slug approve-tap-regenerates-index` went from two
  `FAIL` lines to `CHAIN: PASS` with the change and nothing else.
- **One spec amendment after approval, told to the owner on #92.** The spec's R-1 first said `approved-by`
  is never validated on `superseded`; the pre-existing case `test_superseded_with_an_invalid_approver_fails`
  pins that a human-approved plan with a bot approver still fails after retirement, and the intent keeps
  every existing case green. The rule shipped narrower (validated where the ledger shows no `-> delegated`
  line and no retiring line from `delegated`), the spec's R-1 and D1 say so, and the plan's deviation 3
  records it. The spec read that case while it was written and did not see it.
- **Done when #92 is merged and the owner retires this item, by the tap it built.** The first
  `mode: retire` run on `main` is the production observation of R-9 and R-10: its summary reads `Retired`,
  its commit is `[retire-delegated-items] Retire as luissiviero` with the trailers, and `gen_index.py
  --check` on `main` afterwards prints `INDEX: up to date`. The `next` input is the owner's choice; blank
  leaves the pointer empty, and then every pull request needs a `Work-Item:` line until a grant or a
  retirement points it again.
- **Still open and unchanged from the section below**: the advance is unobserved in production until a
  delegated item merges; `EXEMPT` in the chain check lists `CLAUDE.md` but not its two sibling renders;
  `protect-tests.sh` locks a new test file the moment it exists; #60 and #61 wait on the owner's merge.

## Task state (2026-09-14 ~14:10 UTC) — HISTORY, superseded by the section above
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
  R-7 made `not-delegated` exit 0 and in the same breath kept this one red: "a locked path or a refused
  pull request on a supervised item stays a red run with its own `CONDITION` line"
  (`work/ci-budget/spec.md`, the R7 row, verbatim). The same file states the reason: "A
  `not-delegated` verdict must not hide a refusal that is about the pull request rather than the
  grant." Two
  comments in `delegated_merge.py` say as much in their own words, and neither is that sentence: the
  one above `NOT_DELEGATED`, "a refusal about the pull request itself stays red beside it", and the one
  in the supervised branch beside the `locked-paths` call, "stays a red run with its own condition line
  whatever its item's mode".
  It costs a run per event, which is the price R-7 weighed and paid. Changing it needs an intent that
  argues the case R-7 already decided, not a bug report.
- **New, unfiled: `EXEMPT` in `check_artifact_chain.py` lists `CLAUDE.md` but not `GEMINI.md` or
  `AGENTS.md`**, its two sibling renders of the same fragments. So a pull request that adds one line to
  `docs/sdlc/rules/` outside the active item's own plan is red by construction: `docs/` and `knowledge/`
  are exempt, `CLAUDE.md` is exempt by name, and the other two renders are not, so the check demands
  they be listed in a plan that is already merged and approved. #90 is the live case — rule 7 asked for
  a lesson pointer in the same pull request, and there was no green route to it. Either all three
  renders are exempt or none is; `CLAUDE.md` alone is the accident of it having once been the only one.
  Needs an intent, and until then a rules-fragment line either rides the active item's plan or merges
  with the check red (`knowledge/decisions/merge-click-is-the-gate.md`).
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
(2026-09-18 ~20:50 UTC). `chain-check-without-gh` (defect 3) is merged by the owner's click (#111,
`c96184d`); `.sdlc/active` is empty, which is the normal state between items and not yours to move; nothing
is granted or in flight. **You have no item.** Your task is to confirm `main` and then ask the owner which
item is next; do not start one on your own.

First, bare, with whatever the container sets in its environment: `python3 scripts/gen_index.py --check` and
`scripts/verify.sh` on main. Both were green on `c96184d` with the token set and no `gh` binary; the
`env -u GH_TOKEN -u GITHUB_TOKEN` prefix earlier prompts carried is retired, and a `FileNotFoundError: 'gh'`
anywhere is a regression to report, not a workaround to remember. `git fetch --unshallow origin` is optional;
the checks say `history is shallow` instead of misreporting. If the container arrives with no repository
cloned, or the push is refused as not in this session's authorized set, use `add_repo` with `access: push`
and clone; that happened on 2026-09-15 and 2026-09-17.

Then check one thing before reporting: `work/chain-check-without-gh/intent.md` on `main`. If its status is
still `approved`, the item's retire tap has not landed; say so to the owner (Actions -> approve -> Run
workflow on main, mode retire, slug chain-check-without-gh, next blank) and do nothing else about it. If it
is `superseded`, the item is closed.

Then report to the owner and stop. The candidates, none granted: `standing-grant` (`main`, `in-review`,
`mode: supervised`, `risk-class: medium`; the low-only policy cannot grant it as it stands, so every gate is
a tap; its answers 3 and Depends-on line are overtaken, see the 2026-09-15 ~00:35 section); **defect 2**
(`EXEMPT` in the chain check lists `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`), still needing a
`/sdlc-intent`, which can absorb the stale `evals/` sentence in `check_artifact_chain.py`'s module docstring
at `:23`; the two nits on `scripts/test_chain_no_gh.py` left for a human's edit (see the 20:50 section); and
the two red `delegated-merge` runs `34908767884` and `34909007398`, still unread. `ci-budget` keeps its own
session on 2026-09-20 15:00 UTC and works by slug — do not touch it.

If the owner names an item, that item's own gates start from its first unapproved artifact. Under a grant
(`mode: delegated`, a `risk-class` the policy lists), `/sdlc-run` drives it; a locked path is the detour
rule's trigger, and `work/chain-check-without-gh/revisions/` shows the two records and the park that route
produces. Under `mode: supervised`, every gate is a tap you ask for and never make. Expect the `kind: fix`
hook to stop you if a fix would change an existing test: say so and stop; the owner edits the test. Never
write approved or superseded, never touch the grant keys, never sign `intent.md`, never merge, never move
`.sdlc/active`."

(Superseded, kept as a record: the prompt before it named defect 3 as one `/sdlc-intent` to draft and stop
at the approval tap, which is what this cycle then carried, under a grant the owner gave mid-cycle, all the
way to a merged code pull request. Before that, the prompt held no item, said defect 1 was merged with the pointer
still on it, and told the next session to confirm `main` and ask the owner which item was next. Before that,
the prompt named defect 1 as one `/sdlc-intent` to draft and stop
at the approval tap, which is what this cycle then carried all the way to a merged code pull request. Before
that, the prompt held no item, said `parked-marker-on-retired` was merged
with its advance landed and the pointer empty, and told the next session to ask for the retire tap if the
checks were red and then to ask the owner which item was next. Before that, the prompt named
`parked-marker-on-retired` as the item to take from
spec to a merged pull request under `/sdlc-run`, `kind: fix` with the regression case in a new module, and told
the session to observe the first delegated merge's advance and do step 7 with `Work-Item: ci-budget`. Before
that, the prompt held no item, said `risk-detour` was merged and parked
with the pointer still on it, and told the next session to run the checks with the token unset, ask for the
retire tap if the pointer was empty, and ask the owner which item was next. Before that, the prompt named
`risk-detour` as the item to take from spec to a
ready pull request under `/sdlc-run`, said its skill, template and rule paths would make the merge a click,
and told the session to do step 7 with `Work-Item: ci-budget` on the merge. Before that, the prompt held no
item, told the next session to run the checks
on main and ask the owner which item was next, with #60 and #61 still open. Before that, the same against
the 2026-09-14 ~19:00 Task state, with the pointer possibly empty and no unshallow step. Before that, the
prompt named
`retire-delegated-items` as the active item
with #92 open or merged, and told the next session to ask for the retire tap if it had not happened.
Before that, the prompt said nothing was in flight, `.sdlc/active` named
`advance-push`, finished and merged, and told the next session to ask the owner to retire it and say
which item was next. Before that, the prompt named `advance-push` as the item to take from spec to
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
- Retiring an item is a human act, and since `work/retire-delegated-items` it is one tap on `main`:
  **Actions -> approve -> Run workflow** with `mode` `retire`, the `slug` (required) and `next` (the slug to
  point `.sdlc/active` at; blank clears a pointer naming the retired item and leaves any other alone). The
  run sets `status: superseded` on every present artifact with its `approved-by` untouched, appends one
  `approved -> superseded` (or `delegated -> superseded`) ledger line per artifact, moves the pointer and
  regenerates the indexes in one commit. The web editor still works for the same four edits and still leaves
  the indexes stale (`knowledge/lessons/human-commits-leave-indexes-stale.md`). `check_artifact_chain.py`
  judges a retired artifact by who retired it -- the retiring ledger line's actor, who must hold the
  artifact's role, and the commit that set `superseded`, by author or by verified trailer -- so an
  agent-signed item retires into a green chain; `approved-by` is validated against the approver list only
  where the ledger shows no signature. `require-plan.sh` refuses a `superseded` plan; the check fails every
  pull request whose base already has `.sdlc/active` naming a retired item (the retiring pull request itself
  gets a note to move the pointer), and notes one whose `Work-Item` differs from the pointer. A pull request
  whose `Work-Item:` names a **retired** item passes only in in-progress mode (its own files and the two
  indexes, nothing else): so a clean-up after a retirement carries the retired slug's line, and a pull
  request carrying code never does. A retirement on a branch that *moves* the pointer is strict, because
  `.sdlc/active` counts as the item's own file only while it names the item; that is why the tap runs on
  `main` and its role gate refuses any other branch. Verify such a pull request with the slug the gate will use, not with the default. Fix the body
  **before** the push: the gate resolves the slug from `github.event.pull_request.body` in the event payload,
  so a body edited after the push never reaches the run it was meant to fix, and re-running that run replays
  the same payload. Only the next push carries a corrected body. Nothing *retires* an item on merge
  (`superseded` stays the owner's act; one tap for it is a follow-up item), but since `work/run-queue` the
  merge does *move the pointer*: `delegated_merge.py` advances `.sdlc/active` to the next granted, unstarted
  item (`scripts/next_item.py`: earliest `delegated-on`, ties by slug) and writes a ledger line on both items,
  committed to `main` as `github-actions[bot]`. An owner's merge click runs no workflow, so it does not advance.
- The queue's first item is whatever `.sdlc/active` names, and every grant tap repoints it — so **the last
  tap runs first**, then the rest in date/slug order. Tap the item you want first, last.
- No `gh` binary in the remote container, and it no longer matters: since `c96184d` (2026-09-18,
  `work/chain-check-without-gh`) the chain check's trailer verification takes the same skipped path for a
  missing binary as for a missing token, one `note:` per artifact and then the author rule. From 2026-09-06
  to that commit every local run needed `GH_TOKEN= GITHUB_TOKEN=` in front of `scripts/verify.sh` and the
  chain check; that prefix is retired. CI has `gh` and never saw the fault.
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
