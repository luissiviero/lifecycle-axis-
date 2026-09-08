---
type: decision
title: The merge advances the pointer; the session only follows it
description: "Why a queue of granted items advances from CI after the merge rather than from the item's own pull request or from a session: an item's diff may never contain .sdlc/active, and the merge workflow already holds main's checkout at the moment an item finishes."
tags: [decision, delegated-mode, run-queue, active-pointer, delegated-merge]
resource: ../../work/run-queue/
amends: delegated-mode.md
timestamp: 2026-09-08T18:10:00Z
---
# The merge advances the pointer; the session only follows it

## Context
`work/delegated-mode` decision 6 ended the delegated lane at a merge: the workflow "merges, deletes
the branch, and comments naming the grant commit". Nothing more. `work/approve-by-dispatch` made the
grant one tap, and `work/retire-active-pointer` gave a finished item a defined retirement. What none
of them gave was a way for the *next* item to start, so one tap bought exactly one item: intent →
spec → plan → build → review → merge → idle, with the owner needed again for the next grant. The
owner's objective for delegated mode is the opposite — every input at the start, then hours away.

Three routes could move `.sdlc/active` from item k to item k+1. Two are closed:

- **The item's own pull request cannot.** `scripts/delegated_merge.py`'s `ALWAYS_LOCKED` includes
  `.sdlc`, and `check_locked_paths` refuses on a prefix match. A delegated pull request that moved the
  pointer would be refused by the very script that merges it.
- **A session cannot be relied on to.** Nothing in the repository wakes a session: no
  `repository_dispatch`, no cross-workflow dispatch, no watched comment. A session that happens to be
  alive can notice, but a design that *requires* one alive is a design that stops when it dies.

## Decision
The advance is a write-back in `scripts/delegated_merge.py`, immediately after the merge API call,
committed to `main`. That workflow already checks out the default branch — never the pull request
head — and already holds `contents: write` on `check_workflow_permissions.py`'s allowlist, so it needs
no new permission and no workflow edit. The queue rule lives in `scripts/next_item.py`: approved,
granted, a delegated risk class, and unstarted, ordered by earliest `delegated-on` with ties broken by
slug. The session's role shrinks to noticing the merge and looping.

Guards, because this is a bot commit to the default branch that no chain check sees:
- a staged-path allowlist — exactly `.sdlc/active` and the two `log.md` files, refusing anything else,
  the same shape as `scripts/approve_dispatch.py`'s;
- a lost-update guard — the pointer is re-read immediately before writing and the advance stands down
  if it no longer names the merged item;
- a rejected push is a note, never a retry: the merge already happened, and the next merge advances.

## Consequences
- The pointer on `main` is correct whether or not any session is alive, so a dead session mid-queue is
  recoverable: the next session resumes at the right item with no repair. That is the property that
  makes the wake being an *instruction* acceptable rather than fragile.
- N queued items are N human grants. Nothing an agent may sign widened: `intent.md` is still never
  signable, and `approved` and `superseded` are still words only a human writes. The advance never
  retires item k — retirement stays the owner's act (`work/retire-active-pointer`).
- An item whose merge needs the owner's click (a locked path) produces no merge event and therefore no
  advance, so the queue ends there by construction. Grant such items last.
- A new commit author appears on `main`: `github-actions[bot]`, one commit per advance, each naming the
  pull request it followed.

## Amends
`delegated-mode.md` decision 6, which said the workflow does nothing after merging and commenting: it
now also advances the pointer, under the guards above. The rest of that record stands unchanged — in
particular decision 2 (the grant lives on `intent.md` and only a human sets it) and decision 7 (the
gates that stay human in every mode).
