---
type: sdlc/intent
id: retire-active-pointer
title: Retire `.sdlc/active` when a work item completes, so the plan gate stops opening on finished work
description: "Nothing clears `.sdlc/active` when an item finishes, so it still names a merged item; require-plan.sh judges only that item's plan status and opens the code gate against a plan that has already landed."
stage: plan
status: approved
author: Luis Siviero (repo owner), drafted by Claude from the follow-up recorded three times in the repo and the gate state measured in this session
approved-by: luissiviero
approved-on: 2026-09-08
risk-class: low
mode: delegated
delegated-by: luissiviero
delegated-on: 2026-09-08
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/51
tags: [control-plane, active-pointer, plan-gate, chain-check, followup]
timestamp: 2026-09-07T12:00:00Z
---
# Intent: retire `.sdlc/active` when a work item completes

## Problem
This is the standing follow-up, deferred by three items in a row and never opened. In the repo's own
words: "Retiring `.sdlc/active` when an item completes; the grant overwrites it"
(`work/delegated-mode/spec.md:226`); "retiring `.sdlc/active` when an item completes (the standing
follow-up)" (`work/approve-by-dispatch/intent.md:104`); "the standing follow-up, still open. This item
sets the slug on a delegated grant (`--activate`) but never clears it"
(`work/approve-by-dispatch/spec.md:251`).

Something sets the pointer; nothing unsets it. A delegated grant writes it (`--activate`, via
`.github/workflows/approve.yml`), and it then names that item forever. Today it names
`approve-by-dispatch`, whose work merged in pull request 51 on 2026-09-06.

The cost is not cosmetic, and it is live right now. `.claude/hooks/require-plan.sh:17` resolves the
slug from `.sdlc/active`, then decides the gate on that item's `plan.md` **status alone**
(`:26-35`) — it never asks whether the item is finished. For the item currently named, every
condition passes: the plan carries an agent signature, delegated mode is on, `plan.md` is signable,
`intent.md` is approved with a grant, and `claude` is a listed agent. So the plan gate over
`PLAN_REQUIRED_PATHS` (`scripts`) is **open in any session started today, against a plan that merged
yesterday**.

CI still catches what such an edit would produce — the chain check fails a pull request whose diff
touches files the plan does not list (rule 2) — so this is not a hole in the merge gate. It is the
*local* gate, the one meant to stop the edit before it is made, failing open. The repo's own value is
that hooks stop the mistake and CI is the backstop; here the order is reversed.

Two smaller effects follow from the same pointer: a session reading `.sdlc/active` to learn "which item
are we on" is told a finished one, and a supervised approval tap left with a blank `slug` — the
documented convenience in `approve.yml` — resolves to that finished item.

## Proposed outcome
- An edit under `PLAN_REQUIRED_PATHS` is refused while `.sdlc/active` names a completed item, with a
  message naming the item and how to clear it. Observable: a case in the hook's Python suite that fails
  against today's `require-plan.sh` and passes after the change.
- `python3 scripts/check_artifact_chain.py` reports a stale pointer in one clear line, the way it
  already reports an empty one. Observable: a case in `scripts/test_check_artifact_chain.py`.
- Clearing the pointer is available to the owner without a shell, consistent with the value
  `approve-by-dispatch` established. Observable: the route is exercised in a test, and the prose that
  tells the owner how to use it is in the same pull request.
- Nothing else changes: `scripts/verify.sh` ends `VERIFY: PASS`, `scripts/run_evals.sh` ends `0 fail`,
  `python3 scripts/check_okf.py` ends `0 warnings`, and the existing `.sdlc/active` readers keep working.

## Affected users and systems
- Users: the repo owner, who reads the pointer to know what is in flight; every agent session, which
  resolves its work item from it.
- Services / repos / data: `.sdlc/active` and its readers — `.claude/hooks/require-plan.sh`,
  `.claude/hooks/protect-tests.sh`, `scripts/check_artifact_chain.py`, `scripts/approve.py`,
  `scripts/approve_dispatch.py`, `scripts/delegated_merge.py`, `.github/workflows/approve.yml`,
  `.github/workflows/sdlc-gate.yml`, `.claude/skills/sdlc-review`, `.claude/skills/sdlc-run`,
  `scripts/adopt.sh`.

## Constraints
- Must: keep the file's shape — one slug, one line, blank allowed. Nineteen files read it.
- Must: keep a blank `.sdlc/active` a valid state; the chain check already reports it in one line.
- Must: leave the act of retiring available to the owner from a phone, not only from a shell.
- Must not: change `.sdlc/approvers.yaml`, `.sdlc/delegation.yaml` or `.sdlc/config.env`.
- Must not: let an agent decide on its own that an item is complete without evidence a human can check.
- Out of scope: control-plane tiering; changing what `--activate` writes on a grant; letting
  `.sdlc/active` name more than one item; retroactively auditing past items.

## Risk class
low — the change is confined to one pointer file, its readers and their tests. Blast radius is this
repository; no data is sensitive and no regulation applies. The failure mode of getting it wrong is a
gate that refuses too much, which is visible immediately and safe by default. It closes a gate rather
than opening one, which is why the class stays low even though hooks are involved.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: what makes an item "complete"? Proposed: every chain artifact terminal (`approved`, signed, or
  `superseded`) **and** the item's pull request merged, since only the second is evidence outside the
  repository's own text.
  A:
- Q: who clears the pointer — the merge that lands the work, a tap in the Actions tab, or does the chain
  check only warn and leave the clearing to the owner? Proposed: warn first and add the clearing route in
  the same item, so the pointer is never cleared by something the owner did not press.
  A:
- Q: should a stale pointer block the plan gate or only warn there? Proposed: block, because failing open
  is the defect this item exists to fix.
  A:
