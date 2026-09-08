---
type: sdlc/intent
id: run-queue
title: Grant several items up front and let one delegated run work through them, so I can be away for hours
description: "A delegated run ends at one ready pull request and nothing starts the next item; every grant tap repoints .sdlc/active at one item; so one tap buys one item and the project idles until the owner is back. Let the owner grant a queue of intents at the start and have the run advance from one merged item to the next granted one without a human."
stage: plan
status: in-review
author: Luis Siviero (repo owner), in the session that shipped work/retire-active-pointer; drafted by Claude from the owner's statement of the objective and the lifecycle facts measured in that session
approved-by:
approved-on:
risk-class: low
mode: supervised
delegated-by:
delegated-on:
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/53
tags: [delegated-mode, run-queue, sdlc-run, active-pointer, delegated-merge, unattended]
timestamp: 2026-09-08T15:35:00Z
---
# Intent: grant several items up front and let one delegated run work through them

## Problem
In the owner's words, restating the objective of the session that closed `work/retire-active-pointer`:

> I want to have 2 very distinct modes — supervised and delegated. Whatever mode is the chosen model,
> we're backed by a very robust logging system, which makes possible the retracing of any changes made
> in the project. Supervised: it asks for my approval and revision constantly — I'm happy with how this
> mode is currently, nothing to change. Delegated: this one is meant for moments I'm away from my PC —
> so, beside any input needed from me at the start of the run, even a smaller ask will go unanswered,
> leaving the project idle for hours. This is the point we're working on: currently I can't get away
> for too long from my PC if I want the project to keep running.

What the repository does today, measured on 2026-09-08:

- A delegated run ends at "the ready pull request" (`.claude/skills/sdlc-run/SKILL.md`, step 6). The
  merge is `.github/workflows/delegated-merge.yml`'s, woken by the three required checks completing;
  after the merge API call the script deletes the head branch and posts one comment
  (`scripts/delegated_merge.py:847-869`). It writes nothing back and starts nothing. The session that
  produced the pull request has, by then, nothing left to do, and no session is woken.
- `.sdlc/active` names **one** item, and `delegated_merge.py:329` refuses every pull request whose
  `Work-Item:` is not that item ("only the active work item is merged"). Every grant tap repoints the
  pointer (`approve.yml`, `--activate`). So granting two intents up front leaves only the last tap's
  item mergeable; the first is granted, signable, buildable — and cannot land until the pointer moves,
  and nothing moves it. The repository holds two granted intents right now (`approve-by-dispatch`,
  `retire-active-pointer`), both finished, and the pointer still names the second.
- So one tap buys exactly one item: intent granted → spec → plan → build → review → ready pull request
  → merge → idle. The owner must come back to tap the next one. That is the tether the owner
  describes. `work/retire-active-pointer` gave the pointer a defined retirement and made stale pointers
  visible; it did not give the run a way to move on.

Also measured, in the same session: the session *can* outlive the merge. Subscribed to its own pull
request, it received the `merged` event for pull request 53 and continued on the owner's next
message. Nothing in the run uses that today.

## Proposed outcome
- The owner grants N intents at the start (N taps, all up front — the input the owner accepts) and
  runs `/sdlc-run` once. The run works item 1 to a merged pull request, then item 2, then item 3,
  with **zero human input between items**. Observable: with two granted intents in a test repository
  or a dry run, the ledgers show item 2's `spec.md | in-review -> delegated` line after item 1's
  `PR #n | ... -> merged` line, and `git log` between the two merges has no human-authored commit.
- The pointer advances by itself: after item k's pull request merges, `.sdlc/active` names item k+1
  (the next granted, unstarted intent in a defined order) — and never a finished item. Observable: a
  case in `scripts/test_check_artifact_chain.py` or a new script's suite; `check_artifact_chain.py`
  passes on the commit that moves it.
- Every advance is retraceable: one ledger line on the item being left (its pull request merged, as
  sha) and one on the item being opened (the pointer moved to it, by whom, under which grant), so the
  owner can read the whole night's work from `work/*/log.md` alone. Observable: `log_ledger.py` parses
  both lines; the chain check accepts them.
- The queue stops cleanly and says so once: when no granted, unstarted intent remains; on any of the
  run's existing "stop and call the owner back" conditions (deviation cap, a `keep` verdict, a
  protected or locked path, a red check the item cannot fix, a hook refusal); and when an item's merge
  needs the owner's click (a locked-path item). Observable: one message and one ledger line per stop;
  no second attempt at the same item.
- Nothing else changes: supervised mode is untouched; every per-item gate is exactly as today (a
  human-approved, human-granted intent per item; the same checks; the same merge conditions; the same
  policy); `scripts/verify.sh` ends `VERIFY: PASS`, the chain check `CHAIN: PASS`, the evals `0 fail`,
  `check_okf.py` `0 warnings`.

## Affected users and systems
- Users: the owner, who taps N times and leaves; any agent session running `/sdlc-run`.
- Services / repos / data: `.claude/skills/sdlc-run/SKILL.md` (control-plane: the owner's label);
  `.sdlc/active` and its readers; `scripts/delegated_merge.py` and `.github/workflows/delegated-merge.yml`
  (only if the merge is where the advance happens — a design choice, not decided here); possibly a
  new script for "which granted intent is next" with its tests; `docs/sdlc/` prose; the ledger format
  (`docs/sdlc/templates/log.md`) if a new line shape is needed; `knowledge/decisions/delegated-mode.md`
  (an amendment).

## Constraints
- Must: every human input is at the start of the run. No tap, click, edit or answer is needed between
  item 1's grant and item N's merge, except a locked-path merge, which is by policy and stops the queue.
- Must: every advance is logged on both items' ledgers, and the pointer's every move is a commit a
  human can read (the owner's "very robust logging system" is the point of the whole design).
- Must: the order of the queue is defined and printed at the start, so the owner knows what will
  happen before leaving.
- Must not: widen what an agent may sign. `intent.md` stays human-only; `approved` and `superseded`
  stay words only a human writes. A queue of N items is N human grants, not one grant for N.
- Must not: change `.sdlc/approvers.yaml`, `.sdlc/delegation.yaml` or `.sdlc/config.env` in the
  agent's diff. If the design needs a policy key, the spec names it and the owner writes it.
- Must not: retry a stopped item, or skip past it to the next one silently; a stop is a stop.
- Out of scope: the one-tap retire route in `approve.yml` (`work/retire-active-pointer` D-4); the
  `gh`-absent crash in `check_artifact_chain.py:192`; parallel items; any change to supervised mode;
  reordering or cancelling a queue mid-run from the phone (a later item).

## Risk class
low — every per-item safety property is unchanged: each item still needs its own human-approved,
human-granted intent (a human act per item, not per queue), passes the same checks, and merges under
the same conditions. What changes is scheduling: how many of those already-authorised items one run
may work through without the owner present. The failure mode of getting it wrong is a run that stops
early or works the items in a surprising order, both visible in the ledger and recoverable with a tap.
The owner should still read this class as their call: it is the first item that lengthens how long
an agent works unattended, even though it widens nothing the agent may decide.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: who starts item k+1 after item k merges? Proposed: the same session — `/sdlc-run` subscribes to
  its own pull request and advances on the `merged` event, which this repository's session did on
  pull request 53 today; a scheduled Routine that runs `/sdlc-run` again is the fallback if the
  session dies, and a design question for the spec.
  A:
- Q: in what order are granted intents worked? Proposed: earliest `delegated-on` first, ties by slug;
  printed at the start; an explicit order file is a later item.
  A:
- Q: does advancing retire item k? Proposed: no. `superseded` stays human-only
  (`protect-approvals.sh:48`); the pointer moves (an agent write under the unlock, audited, as
  `HANDOFF.md` already relies on) and item k's retirement stays the owner's act
  (`work/retire-active-pointer` R-5) — unless the owner chooses to let an agent write `superseded` on
  a *merged* item, which is a `.sdlc/delegation.yaml` edit only they can make.
  A:
- Q: what does the queue do at an item whose merge needs the owner's click (a locked path)? Proposed:
  stop there and say so once; the owner orders such items last when granting. Skipping ahead would
  leave a pull request behind with the pointer moved off it, which `delegated_merge.py` then refuses.
  A:
