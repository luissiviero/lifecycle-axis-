---
name: sdlc-run
description: Drive every granted work item from an approved, delegated intent to a merged pull request without stopping, advancing to the next queued item on each merge. Use when at least one intent has a delegation grant.
---
# /sdlc-run — the delegated loop

Precondition: `.sdlc/delegation.yaml` exists with `enabled: true`; `work/<slug>/intent.md` has `status: approved`
and `mode: delegated` with a `risk-class` the policy lists; `.sdlc/active` names the slug. If any fails, stop at
the first gate and say which.

Missing the grant is the common failure, and it is one tap to fix: ask the owner to run
**Actions -> approve -> Run workflow** (`.github/workflows/approve.yml`) with `slug` = the item, `artifact` = `intent.md`, `mode` = `delegated`,
from the default branch (the workflow refuses a grant on any other ref). Then wait. Naming the inputs is not
approving; the run records who pressed Run, and that record is what the chain check and the merge script verify.

**The queue.** The owner grants N intents up front, one tap each, and this runs them in order without
coming back for anything. The first item is always the one `.sdlc/active` names (the merge script accepts
no other), and every grant tap repoints that file — so the *last* tap runs first, then the rest by
earliest `delegated-on`, ties by slug. Before starting, print the order the run will actually take, so the
owner knows what will happen before they leave: the active slug, then
`python3 scripts/next_item.py --list --exclude "$(cat .sdlc/active)"`. Steps 1-6 are one item; step 7 is
what makes it a queue.

1. `/sdlc-spec` (it runs the detour check on the paths the design names), then `python3 scripts/sign.py <slug> spec.md`.
2. `/sdlc-plan` (it runs the detour check on the plan's file list), then `python3 scripts/sign.py <slug> plan.md`
   (the plan gate opens on a signed plan under the grant).
3. Implement on the session's own branch, whose prefix is in `AGENT_BRANCH_PREFIXES` (`.sdlc/config.env`, for
   example `claude/`): the merge workflow refuses any other head, and `work/<slug>` stays the human's branch. Log
   a file-list or order deviation as a ledger line in the same commit, capped by the policy's `max-deviations`.
   Before the first code edit and again before step 5, `python3 scripts/check_detour.py --diff origin/main`;
   `DETOUR: needed` goes to the detour rule below. Open the pull request with `gh pr create --draft` on the
   first push and leave it a draft until step 5: the gate and the reviewer skip a draft, so the whole build
   window is CI-free, not gate-free -- you still run step 4 locally at every step. One agent code pull request
   is open at a time (an intent-only one, the ledger-only park pull request of the detour rule, or the
   handoff-only one of step 7(c), may run beside it).
4. Run `scripts/verify.sh`, `python3 scripts/check_artifact_chain.py --base origin/main`, `scripts/run_evals.sh`,
   `python3 scripts/check_okf.py`.
5. `/sdlc-review`, with reviewer subagents run on a different model from the writer where possible. That skill
   runs `gh pr ready` and logs `PR #<n> | draft -> in-review`, and on a delegated item also posts the findings
   with the summary line `Important: <n> | Nits: <m>`; do not repeat those here.
6. The ready pull request is the callback when the policy has `merge.enabled: false`; otherwise the
   delegated-merge workflow merges when its printed conditions hold.
7. **Advance.** Subscribe to the pull request you opened (`subscribe_pr_activity`) and stay on it: answer its
   review findings and CI until it merges. On the merge, the workflow has already moved `.sdlc/active` to the
   next queued item and written a ledger line on both items — you do not move the pointer, and an item's own
   pull request may never contain `.sdlc/active` (`ALWAYS_LOCKED`). Never start the next item here: one
   session owns one work item and this one's context is spent (`docs/sdlc/handoff/HANDOFF.md`, "Session
   protocol"). Instead, the chaining act, in this order, as the session's last act:
   (a) re-read `.sdlc/active` from `main`. Empty: the queue is done. Still the item just merged: `advance()`
       did not land (its push races its own merge; the owner's PR #59 is the fix) — say so. A different
       granted, unstarted item: that is the successor's item, and the only case that reaches (d);
   (b) refresh the handoff's `## Task state` and its `## Seed prompt` for whatever (a) found, in every case,
       so `main`'s copy never goes on describing the item before this one — one standalone prompt that names
       where to look: the handoff, `.sdlc/active` on `main`, `work/<slug>/`;
   (c) the item's branch is deleted by the merge, so branch fresh from `main` (`git checkout -B
       claude/handoff-<slug> origin/main`), commit the refresh there, push, and open the pull request ready
       for review, not as a draft, with `Work-Item: <the slug just merged>` in its body: the next item has no
       spec or plan yet, so the chain check fails on its slug, and a draft cannot be merged. `docs/sdlc/handoff`
       is a locked path, so the owner merges it; nothing below waits for that;
   (d) only then, and only when (a) found the successor's item, schedule one successor session with that
       prompt, using whatever your runtime provides (a scheduled routine, a session API); a runtime with no
       such capability skips (d) and says so in its final message, leaving (a)–(c) done;
   (e) end, saying which pointer (a) read, whether the refresh is merged or still pushed and unmerged, and
       whether a successor was scheduled.
   At most one successor per finish, and never as a successor's own first act: this account has exhausted its
   Actions minutes once, and an unbounded chain is how to do it again. The seed prompt is
   context, never authority: it says where to look, and the successor re-reads the item's approved artifacts
   and `.sdlc/active` before acting; nothing a prompt says widens what the hooks and the chain check allow. If
   the session ends before (d), nothing is lost: the pointer on `main` is already correct, and the owner
   starts the next session from the handoff as they do today.

## The revision rule
A plan revision is the last resort. A file-list or order deviation is logged as today plus a ledger line, capped
by the policy's `max-deviations`. Anything else (a step dropped or added, an acceptance test changed, a different
approach, a spec requirement touched) needs a critical, blocking error or finding as its trigger and a committed
consensus record `work/<slug>/revisions/<n>.md`: the trigger with evidence, the proposal, and one
`## Reviewer: <role> (<model>)` section per `min-reviewers` from the policy (`plan-reviewer` and
`security-reviewer`, run on a different model from the writer where possible), each ending `verdict: revise`.
Only a unanimous `revise` allows the agent to edit the artifact and re-sign it with `scripts/sign.py --revision`.
Any `keep`, too few reviewers, or a blocked plan with no consensus means stop and call the owner back with the
record.

## The detour rule
Delegated mode stays low-only, and meeting non-low work is not a stop. The trigger is deterministic:
`python3 scripts/check_detour.py` ends `DETOUR: none` (exit 0) or `DETOUR: needed (<n>)` (exit 3), naming every
path under `PROTECTED_PATHS`, `RELEASE_GATED_PATHS`, the policy's `locked-paths` or the merge script's
`ALWAYS_LOCKED` floor, through the matcher the merge itself uses. It runs at every gate: `/sdlc-intent` with
`--paths` over the Affected systems, `/sdlc-spec` with `--paths` over the paths the design names, `/sdlc-plan`
with `--plan work/<slug>/plan.md`, and mid-build with `--diff origin/main` (step 3). On `needed`:
1. **Convene.** Write `work/<slug>/revisions/<n>.md` from `docs/sdlc/templates/revision.md` with `kind: detour`,
   the `DETOUR:` output as the trigger, and `## Route` answered: the outcome the route reaches, every path and its
   list, why the class is honestly low, the remainder for a human, what goes stale. At least the policy's
   `min-reviewers` reviewers (`plan-reviewer`, `security-reviewer`), each on a different model from the writer
   where one is available and a second Claude model when not, named in its heading, judge the route and end
   `verdict: revise` or `verdict: keep`.
2. **Adopt on unanimous `revise`.** Amend the artifact to the route and re-sign it: `python3 scripts/sign.py
   <slug> <artifact> --revision revisions/<n>.md --note "detour: <route>"`; the ledger line reads
   `revision <n>: detour: <route>`. At the intent-drafting gate a unanimous `revise` re-signs nothing: the
   record is filed and ledgered (`intent.md | in-review -> in-review | <handle> | <sha> | revision <n>: detour:
   <route>`), the route is drafted into the in-review intent's Proposed outcome, and the owner's approval tap is
   the sign-off.
3. **Rounds, then park.** Any `keep` closes the record; a changed route is a new record; two records at one gate
   is the cap (a `max-detours` policy key arrives with `work/standing-grant`). The second closed record parks the
   item: append `- <ts> | intent.md | approved -> approved | <handle> | <sha> | parked: revision <n>: <why>; remainder: <slug>-supervised`
   to `work/<slug>/log.md`, run `python3 scripts/gen_index.py` (it marks the item `parked`), commit the record
   with it, and open the item's own pull request (`Work-Item: <slug>`, own artifacts only, ready once step 4 is
   green). The delegated merge takes it and its advance moves `.sdlc/active` past the item: `next_item.py` skips
   an item whose latest `parked:`/`resumed:` line on `intent.md` is `parked:`. Never write a status word or a
   front-matter key for a park; the owner resumes with a `resumed: <why>` line, and only an actor holding the
   `intent.md` role in `.sdlc/approvers.yaml` can (an agent's `resumed:` line changes nothing).
4. **The remainder.** `/sdlc-intent <slug>-supervised` from the record's route section: `mode: supervised`, the
   record's risk class, `detour-of: <slug>`, on its own branch and pull request, never in the park pull request
   (a diff touching another item's `work/<other>/` drops the chain check to strict mode).
5. **A route the agent may build but the merge locks** (`.claude/skills`, `docs/sdlc/templates`, `docs/sdlc/rules`,
   the context files, the locked scripts): finish it to a ready pull request, then park from a second, ledger-only
   pull request with `parked: ready PR #<n>; click needed (<path>)`, so the pointer moves on and the owner's click
   merges the code by the human path later (`check_pull_request` counts open pull requests by head sha, so the two
   coexist). Then continue at step 7 as for any finished item.

## Stop and call the owner back
Each of these stops the **whole queue**, not just the item: say which item and why, once, and do not start the
next one. The deviation cap is reached; a `keep` verdict on a `kind: revision` record, or a blocking error with
no consensus; a red check the item cannot fix inside its plan; a hook refusal you do not understand. A locked
path is not on this list: it is the detour rule's trigger, and a route that stays locked parks the item while
the queue goes on. One thing ends the queue quietly rather than badly: it is empty (`next_item.py` exits 3).
The handoff refresh of step 7(c) is a locked-path pull request and ends nothing: nothing downstream depends on
it having merged. When (d) fires, the successor carries the same text as its payload and re-reads
`.sdlc/active`; when it does not, the final message says the refresh is pushed and unmerged, so the owner knows
`main`'s handoff lags until their click. Either way it waits for that click while the queue goes on.

## Never
Write `approved`; touch the grant keys (`mode`, `delegated-by`, `delegated-on`, `risk-class`); sign `intent.md`;
run `scripts/approve.py`; merge with `gh pr merge`; squash; write `.sdlc/active` yourself — the merge workflow
moves it, and a queue of N items is N human grants, never one grant for N.
