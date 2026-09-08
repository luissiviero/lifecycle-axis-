---
type: sdlc/intent
id: standing-grant
title: Delegated mode is the state every session starts in, a subject typed in and a merged pull request out, with no per-item tap
description: "Today every delegated item needs a human tap that writes mode: delegated on its intent; a queue of N items is N taps and an idle repository between them. Move the grant for low-risk items to the human-only policy file as one standing grant, let the intent be signed by the agent under it, and let the merge workflow open a new item when the pointer is empty. Supervised becomes what the owner asks for."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: in-review
author: Luis Siviero (repo owner), in the session of 2026-09-08 that planned delegated-by-default; drafted by Claude from the owner's statement and an exploration of every reader of the grant
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by:
approved-on:
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: medium
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
# supersedes: previous intent id, if any
supersedes:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: knowledge/decisions/delegated-mode.md
tags: [delegated-mode, standing-grant, run-queue, sdlc-run, sdlc-intent, active-pointer, delegated-merge, policy, risk-class]
timestamp: 2026-09-08T22:00:00Z
---
# Intent: delegated mode is the state every session starts in, with no per-item tap

## Problem
In the owner's words, 2026-09-08:

> I much rather have "delegated mode" as my default mode — always; the "supervised mode" would be
> something I'd have to ask for.

And, asked whether one tap per item was the floor:

> I'd want no tap. I'd just start writing and the mode was already "delegated".

Measured on 2026-09-08, on `main` at c0aa58c:

- The grant is per item and is a human act on that item: a human-authored commit that writes
  `mode: delegated` on `work/<slug>/intent.md` (the approve workflow's tap, or the approval script from
  the owner's shell). Every reader keys on that line: `check_grant` in `scripts/check_artifact_chain.py:299-368`
  (status `approved` by a product owner, `mode: delegated`, a risk class the policy lists, and the
  `-G '^mode: delegated$'` pickaxe finding a human author), `scripts/sign.py:143-156`,
  `scripts/next_item.py:55-58`, `scripts/delegated_merge.py:386-410`, and `intent_mode` in
  `.claude/hooks/_lib.sh:211-217`, which `require-plan.sh:31` and `protect-approvals.sh:128` call.
- `intent.md` is never signable by an agent, by design (`work/delegated-mode` D-b: the agent must never
  sign the file that carries its own grant). `sign.py:189-192`, `delegation.py:152-158`,
  `protect-approvals.sh:126` and `check_grant` all refuse it.
- `.sdlc/active` is written by exactly two things: the tap (`approve.yml:115-118`, `--activate`) and the
  advance after a merge (`delegated_merge.py:925-1003`). The merge script refuses any pull request whose
  slug the pointer does not name (`delegated_merge.py:329-332`), and an item's own pull request may never
  carry `.sdlc/active` (the `ALWAYS_LOCKED` floor, `:89-93`). So a brand-new item cannot open itself.
- `work/run-queue` bought "N taps up front, none after" and wrote the rule down: "a queue of N items is
  N human grants, not one grant for N" (`knowledge/decisions/run-queue.md`). This item asks for the
  other half: one human act that stands for every low-risk item to come.
- Three facts the design must respect, found on the way. `approvers._parse` raises on an unknown
  top-level key (`scripts/approvers.py:96`), so the policy key must ship after its parser. `verify.sh`
  fails the chain check on an empty pointer with no `--slug` (`check_artifact_chain.py:496-501`), and
  between items the pointer is empty by design. And `protect-approvals.sh` does not guard `risk-class`
  (it compares `status`, `mode`, `delegated-by`, `delegated-on` and the approval keys, `:89-111`),
  although `knowledge/decisions/delegated-mode.md` decision 2 says it guards all four grant keys; a
  narrowing edit from `medium` to `low` passes every check today.

## Proposed outcome
- One human act is the grant for every future low-risk item: the owner's commit adding a standing
  grant (who, when, which risk classes) to `.sdlc/delegation.yaml` on `main`, a file no agent writes.
  Observable: the policy parser reads it; a policy without it leaves every `intent.md` unsignable, so
  the existing `sign-refuses-intent` eval passes unchanged.
- With the pointer empty, `/sdlc-intent` ends in a signed intent and a pull request that opens the item
  by itself: the intent carries `status: delegated`, `approved-by: <agent handle>` and a third mode word
  written only by the signing script (never `mode: delegated`, which the hook refuses on an agent write
  and whose pickaxe must keep finding a human); the merge workflow accepts the pull request when its diff
  is confined to `work/<slug>/` and the pointer is empty, merges it, and sets `.sdlc/active` to the slug
  with one ledger line. Observable: a merge-script test with a real bare remote, modelled on the advance
  tests; the chain check passes an intent-only standing diff.
- The rest of the item runs and merges exactly as `work/run-queue` left it, and the advance follows.
  Observable: every existing `test_delegated_merge.py` case passes unchanged.
- A standing signature is worth exactly what the policy commit is worth: the chain check and the merge
  script accept it only when the commit that added the standing grant is a GitHub-verified product-owner
  commit whose author is the handle the grant names. Observable: an agent-authored or unverified policy
  commit gives `CHAIN: FAIL` and `CONDITION grant: refused`.
- The agent's own risk class cannot widen the lane: `risk-class` is refused to agent edits once the
  intent is signed, and a `low` standing item whose diff touches a protected, release-gated, locked or
  floor path fails the chain check on that fact alone. Observable: two eval cases.
- The self-check passes between items: `scripts/verify.sh` ends `VERIFY: PASS` with an empty pointer
  on a clean tree. Observable: an eval case.
- Supervised is what the owner asks for: the per-item tap, the approval script and `mode: delegated` on
  an intent all keep working unchanged, and any item the owner approves or merges by hand stays
  supervised. Observable: the existing approval and grant tests pass unchanged.
- All green: `VERIFY: PASS`, `CHAIN: PASS`, `EVALS: 0 fail`, `OKF: 0 warnings`; the adopter's rendered
  context file at or under the cap.

## Affected users and systems
- Users: the owner (one policy edit, then absent; supervised on request); every session running
  `/sdlc-intent` or `/sdlc-run`; adopters of the kit (template and docs).
- Services / repos / data: `scripts/delegation.py`, `sign.py`, `check_artifact_chain.py`, `next_item.py`,
  `delegated_merge.py` (five judging surfaces, four of them `locked-paths`) and their tests;
  `.claude/hooks/_lib.sh`, `require-plan.sh`, `protect-approvals.sh`; `docs/sdlc/templates/delegation.yaml`
  and `intent.md`; the `sdlc-intent` and `sdlc-run` skills, one line each in `sdlc-spec`, `sdlc-plan`,
  `sdlc-incident`; rule fragments and the three regenerated context files; `docs/sdlc/README.md`,
  `github-setup.md`, `handoff/HANDOFF.md`; a new decision record amending `delegated-mode.md` decisions
  2, 3 and 5 and `run-queue.md`; eight eval cases.

## Constraints
- Must: `approved`, `superseded`, a human handle in `approved-by`, `mode: delegated`, `delegated-by`
  and `delegated-on` stay human-only at every layer; the agent never writes `mode` through an edit.
- Must: the standing grant is verified server-side before any merge, in both the chain check and the
  merge script, from the base branch's policy file, never from the head.
- Must: the merge script reads nothing executable from the head; on an opening pull request it reads
  the head's `intent.md` only after proving the diff is confined to `work/<slug>/`.
- Must: `.sdlc/active` is written only by the merge workflow and the approve tap; an item's own pull
  request never carries it; the pointer must be empty for the lane to open.
- Must: the standing grant's risk classes bound what the lane may merge; `medium` and `high` still need
  the per-item tap; the `ALWAYS_LOCKED` floor and `locked-paths` are untouched.
- Must: ship supervised, in pull requests readable from a phone, with the parser merged before the
  owner writes the key.
- Must not: edit `.sdlc/delegation.yaml`, `.sdlc/approvers.yaml`, `.sdlc/config.env` or
  `.github/workflows/` in the agent's diff; squash; change supervised mode or the per-item grant route.
- Out of scope: retiring items automatically (`superseded` stays human-only); a one-tap revoke
  (deleting the key is the revoke, already human-only); per-item grants at `medium` or `high` under a
  standing grant; reordering a queue; parallel items; the advance push defect (`work/advance-push`,
  a prerequisite) and the low-only detour (`work/risk-detour`, which this item relies on once the
  agent classifies its own risk).

## Risk class
medium — the owner should read this as their call. Every prior control-plane item declared `low` on
the argument "fail-closed on a missing key, revertible, adds a mode", and all of that holds here: a
missing or disabled policy, or a missing standing grant, closes the lane everywhere. What is new is
who classifies. For the first time the agent writes the `risk-class` that decides whether its own item
merges without a human, and nobody reads the intent before the merge. The blast radius is bounded by
the path lists (the floor, `locked-paths`, the new diff-versus-class check), not by the agent's honesty,
and the property changes from "a human read this intent" to "a human pre-authorised this class".
Either value keeps this item supervised: the policy delegates `low` only, and the diff is locked five
ways.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: one intent-only pull request that opens the item, then one code pull request (two merges per
  item), or a single pull request per item? Proposed: two; the intent gets its own review and stays
  locked in the code pull request, as the merge script already requires.
  A:
- Q: does the standing grant also cover items that start from an `incident.md` (a band breach filed by
  `bands.yml`)? Proposed: yes when the class is low, with the same signature rule.
  A:
- Q: after pull request 58 merges by click, the pointer still names `run-queue-followups`. Who clears
  it so the lane can open? Proposed: this item's own pull request, under the control-plane label;
  otherwise the owner, one line in the web editor.
  A:
- Q: a nested `standing-grant:` map in the policy, or three flat keys? Proposed: nested, matching
  `merge:`; one small reader added to the hooks' library.
  A:
- Q: a started standing item whose pointer a supervised tap stole mid-run is invisible to the queue.
  Should the queue also return started-but-unmerged standing items? Proposed: not now; recorded as a
  residual, the same one per-item grants already have.
  A:
- Q: does the owner want a cap on standing items per day, or a `max-detours` key, in the policy?
  Proposed: `max-detours` yes (it is what `work/risk-detour` defers here); a daily cap no, the queue is
  serial by construction.
  A:
