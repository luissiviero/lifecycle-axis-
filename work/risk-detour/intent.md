---
type: sdlc/intent
id: risk-detour
title: A delegated item that meets non-low work looks for a low-only route by reviewer consensus, and parks instead of stopping the queue
description: "Delegated mode stays low-only. Today non-low work is refused at admission or stops the whole queue mid-item; the only consensus record asks for the smallest change that clears a trigger, never for a route that stays low. Let the run convene reviewers at every gate for a route that reaches the intent's outcome touching only low-risk surface, adopt it on a unanimous verdict, and otherwise park the item and continue."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: approved
author: Luis Siviero (repo owner), in the session of 2026-09-08 that planned delegated-by-default; drafted by Claude from the owner's statement and an exploration of the run skill, the revision record and the queue
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by: luissiviero
approved-on: 2026-09-15
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: low
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: delegated
delegated-by: luissiviero
delegated-on: 2026-09-15
# supersedes: previous intent id, if any
supersedes:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: knowledge/decisions/delegated-mode.md
tags: [delegated-mode, run-queue, sdlc-run, risk-class, revision-record, consensus, parking]
timestamp: 2026-09-08T22:00:00Z
---
# Intent: a delegated item that meets non-low work looks for a low-only route by reviewer consensus, and parks instead of stopping the queue

## Problem
In the owner's words, 2026-09-08:

> I want `delegated` to only touch `low`, but instead of stopping if it finds something else in its
> objective, instead of stop, make it check for alternative solutions that reach the end only in `low`.
> To make this decision, I'd like as many agents you think are necessary to discuss and find a
> consensus on the best course of action.

Asked whether that was already the behaviour: it is not. Measured on 2026-09-08, on `main` at c0aa58c:

- Non-low work never enters delegated mode. The risk class is checked at admission in five places and
  each refusal is terminal: the approval script refuses the grant, `scripts/next_item.py:59-61` drops
  the item from the queue without a message, `scripts/sign.py:152-157` refuses to sign,
  `scripts/check_artifact_chain.py:346-348` fails the chain, `scripts/delegated_merge.py:404-406`
  refuses the merge.
- Mid-item, the run's only rule is to stop everything. `.claude/skills/sdlc-run/SKILL.md:56-63`: a path
  under `PROTECTED_PATHS`, `RELEASE_GATED_PATHS` or the policy's `locked-paths` "stops the whole queue,
  not just the item", and "a locked-path item never merges on its own, so no advance follows it and
  the queue ends there".
- The consensus record exists, but for another question. `docs/sdlc/templates/revision.md` is triggered
  by "the error or finding that blocks the plan" and asks its reviewers whether the change is "the
  smallest one that clears the trigger". Nothing asks whether a route exists that stays low. The two
  records written so far (`work/run-queue/revisions/1.md`, `work/retire-active-pointer/revisions/1.md`)
  were both triggered by review findings.
- No item has ever exercised any of this: every `risk-class:` under `work/` is `low`, and the risk class
  is transcribed from the interview (`.claude/skills/sdlc-intent/SKILL.md:11,15`) and never revisited,
  not even by `/sdlc-spec`, which is where the real blast radius first becomes known.
- Parking has nowhere to live today. The status vocabulary is closed (`check_artifact_chain.py:60`); a
  delegated pull request may not touch its own `intent.md` (`delegated_merge.py:822-827`); and an item
  parked before its spec is signed is "unstarted" to `next_item.py:62-64`, so the next advance would
  offer it again.

## Proposed outcome
The owner's decisions in the same session: the detour fires at every gate, intent drafting included,
and mid-build; when no low-only route exists, the item is parked and the queue continues.

- A revision record carrying a risk trigger and a proposed route is accepted by `scripts/sign.py
  --revision` and by `check_artifact_chain.py` as they are today. Observable: the existing unanimous
  re-sign test passes on a record that carries the new marker and section; the verdict words stay
  `revise` and `keep`, so CI keeps judging every record.
- The run convenes at least the policy's `min-reviewers` reviewers, on a different model from the
  writer where one is available, with a question set about the route rather than the trigger: which of
  the intent's outcomes the route reaches, every path it touches and the list each falls under, whether
  the class is honestly low, what remainder is left for a human, what in spec and plan goes stale.
  Unanimous `revise` means the route stands and the artifact is amended and re-signed under the record.
  "As many agents as necessary" is rounds: a split record is closed, a changed route is a new record.
  Observable: the record shape in the template; a ledger line `revision <n>: detour: <route>`.
- The trigger is deterministic, not a feeling: a local check names every planned or changed path under
  `PROTECTED_PATHS`, `RELEASE_GATED_PATHS`, the policy's `locked-paths` or the merge script's
  `ALWAYS_LOCKED` floor, through the one matcher the merge script already uses, and ends
  `DETOUR: none` or `DETOUR: needed (<n>)`. Observable: a test module and an eval case; exit 0 or 3.
- A parked item is never offered again by the queue. Observable: `next_item.py` skips an item whose
  latest `parked:` or `resumed:` ledger line on `intent.md` is `parked:`; three test cases (parked before
  the spec, parked then resumed by the owner, a `parked:` note naming a missing record still parks) and
  an eval case.
- The park itself moves the pointer on. Observable: in a dry run with two granted items, the ledger of
  the first shows `parked: revision <n>: <why>; remainder: <slug>-supervised` and the second item's
  ledger shows the pointer advancing to it, with no human commit between.
- The non-low remainder reaches the owner as a supervised intent, not as a lost note. Observable:
  `work/<slug>-supervised/intent.md` with `mode: supervised`, the record's class, and a `detour-of:
  <slug>` key, on its own branch and pull request.
- Nothing the owner reads by hand gets longer than the cap: the adopter's rendered context file stays
  at or under `MAX_CONTEXT_LINES`. Observable: `scripts/adopt.sh` into scratch, `wc -l`.
- All green: `VERIFY: PASS`, `CHAIN: PASS`, `EVALS: 0 fail`, `OKF: 0 warnings`.

## Affected users and systems
- Users: the owner, who grants, reads parked items and approves the remainder; every delegated session.
- Services / repos / data: `.claude/skills/sdlc-run/SKILL.md` (the stop rule becomes the detour rule),
  `sdlc-intent`, `sdlc-spec`, `sdlc-plan`; `docs/sdlc/templates/revision.md`, `intent.md`, `log.md`;
  `scripts/next_item.py` and its tests (imported by the advance in `delegated_merge.py`); a new path
  check script and its tests; two rule fragments under `docs/sdlc/rules/` and the regenerated context
  files; `knowledge/decisions/` (amends decision 4 of `delegated-mode.md`); two eval cases.

## Constraints
- Must: keep `revise` and `keep` as the only verdict words and `STATUSES` closed, so no judging script
  changes and CI's reading of a record is the same before and after.
- Must: write no status word and no front-matter key on a parked item; a park is a ledger line and a
  record, and the follow-up intent never rides in the park pull request (a diff touching another
  item's `work/<other>/` drops the chain check to strict mode).
- Must: keep `min-reviewers` as the floor and name each reviewer's model in its heading.
- Must: a regression test per new rule; every context-file line paid for at the adopter's cap.
- Must not: change `check_artifact_chain.py`, `sign.py`, `delegated_merge.py`, `delegation.py`, the
  hooks, the workflows or `.sdlc/`; add a policy key; write `approved`; move `.sdlc/active` from a session.
- Out of scope: the advance push defect (`work/advance-push`, a prerequisite for the queue to continue
  at all); the standing grant and everything that comes with it (`work/standing-grant`: an agent-written
  risk class, a `max-detours` policy key, a dedicated reviewer role, hook protection of `risk-class`).

## Risk class
low — no script that judges a merge or a signature changes. The one queue change narrows what is
offered; the path check is advisory locally and duplicates a matcher that is already deterministic at
the merge; templates and skills are advisory by nature. The item's pull request is the owner's click
regardless, because skills and templates sit on the merge script's `ALWAYS_LOCKED` floor. What this
item does widen is how far a run goes before it asks: a parked item is a decision the owner reads after
the fact rather than a stop they are called back for, and that is the trade the owner asked for.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: when the only route needs a surface an agent may build but the merge locks (`.claude/skills`,
  templates, rules, the locked scripts), park the work or finish it? Proposed: finish to a ready pull
  request and park with `parked: ready PR #<n>; click needed (<path>)`, so the pointer moves on and the
  owner's click merges by the human path later.
  A: agreed (owner, 2026-09-08): finish to a ready pull request and park with `parked: ready PR #<n>; click needed (<path>)`, so the pointer moves on.
- Q: how many rounds before a park? Proposed: two records per gate, a skill convention now; a
  `max-detours` policy key comes with `work/standing-grant`, whose policy parser change it needs.
  A: agreed (owner, 2026-09-08): two records per gate, a skill convention; `max-detours` arrives with work/standing-grant.
- Q: when a second model is not on the machine (a remote session, no `agy`), is a second Claude model
  an acceptable second reviewer? Proposed: yes, named in the heading as today.
  A: agreed (owner, 2026-09-08): a second Claude model is acceptable, named in the heading as today.
- Q: should `work/index.md` mark a parked item, or is the park pull request's title enough? Proposed:
  a `parked` marker in the generated index, with a golden test; it is where the owner looks first.
  A: agreed (owner, 2026-09-08): a `parked` marker in the generated index, with a golden test.
- Q: `scripts/next_item.py` is read by the advance but is not on `locked-paths`. Add it? Proposed: yes,
  in `.sdlc/delegation.yaml`, the owner's file, after this item merges.
  A: agreed (owner, 2026-09-08): add `scripts/next_item.py` to `locked-paths` after this item merges, as the owner's own edit.
- Q: the detour fires at intent drafting too (Proposed outcome, first line), but the adoption mechanism
  this intent names is `scripts/sign.py --revision`, and `intent.md` is never signable: it carries the
  grant, and making it signable is a `sign.py` change the Must-not list forbids. At that one gate, what
  does a unanimous `revise` amend and re-sign? Raised by the automated review on pull request 60 and
  unresolved across three passes; carried here so `spec.md` inherits a question, not a contradiction.
  Proposed: at the intent-drafting gate there is nothing to re-sign, and none is needed. The record is
  still filed and ledgered, the route it agrees is drafted into the intent's own Proposed outcome while
  the intent is `in-review`, which an agent may write, and the owner's approval tap is the sign-off that a
  signature would be at every later gate. If the owner would rather the detour start at the spec gate,
  the first line of Proposed outcome changes to say so and this question closes the other way.
  A: agreed (owner, 2026-09-15): at the intent-drafting gate a unanimous `revise` files and ledgers the record and re-signs nothing; the route is drafted into the in-review intent's Proposed outcome, and the owner's approval tap is the sign-off. Once the intent is signable under a standing grant, this gate re-signs like the others.
