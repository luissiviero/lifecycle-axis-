---
type: sdlc/intent
id: retire-delegated-items
title: A delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale
description: "An agent signs spec.md and plan.md with approved-by: claude; when the owner retires the item the chain check validates superseded against the approver list exactly as approved, so every pull request that names the retired item fails, including the one that regenerates the indexes the web-editor retirement left stale. Make superseded a human act the check reads from the ledger, and make the retirement a tap that regenerates what it changes."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: in-review
author: Luis Siviero (repo owner), who retired work/approve-tap-regenerates-index on 2026-09-14 and hit both halves; drafted by Claude from the measurement on pull request 86 and the 2026-09-13 retrospective that predicted it
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
resource: https://github.com/luissiviero/lifecycle-axis-/pull/86
tags: [delegated-mode, retirement, chain-check, approvals, gen-index, control-plane]
timestamp: 2026-09-14T05:35:00Z
---
# Intent: a delegated item cannot be retired into a green chain, and its retirement leaves the indexes stale

## Problem
The 2026-09-13 retrospective named it before it happened: "retiring a delegated item is impossible today
(`superseded` needs a human approver and those artifacts carry `approved-by: claude`)". On 2026-09-14 the
owner retired `work/approve-tap-regenerates-index`, the first delegated item to complete, from the web
editor: five commits (`e7d7ae7`, `f00c002`, `58a5852`, `4d9ccd9`, `5a58b17`) set the three artifacts
`superseded`, appended three ledger lines and moved `.sdlc/active`. Two things followed, both measured on
pull request 86:

- **The retired item cannot be named by any pull request that passes the chain check.** Its `spec.md` and
  `plan.md` carry `approved-by: claude`, the handle the agent signed them with under the grant, and
  `scripts/check_artifact_chain.py` validates the approver of a `superseded` artifact against
  `.sdlc/approvers.yaml` exactly as it does for `approved`; by design a superseded artifact "keeps the
  approved-by it earned", and the agent's handle then fails the approver list it was never on. With
  `Work-Item: approve-tap-regenerates-index` and only the item's own files in the
  diff, the check takes in-progress mode and still fails twice: `spec.md approved-by 'claude' is not
  valid: agent identities cannot approve`, and the same for `plan.md`. With anything else in the diff it
  takes strict mode and fails five times, the three `status is 'superseded', must be 'approved'` lines on
  top. With no `Work-Item:` line it falls back to `.sdlc/active`, now `advance-push`, and fails on that
  item's missing spec and plan. Every route is red.
- **The retirement left `main` at `VERIFY: FAIL`.** A web-editor commit runs no script, so
  `work/approve-tap-regenerates-index/index.md` and `work/index.md` drifted, and the only pull request
  that could regenerate them is one of the red ones above. The owner merged it with the check red
  (`knowledge/decisions/merge-click-is-the-gate.md`). `work/approve-tap-regenerates-index` closed the
  tap route of this drift and deliberately left the web-editor route open, because a retirement has no
  tap today.

So the delegated loop can run an item grant to merge with no click, and then needs two human commits
and one red merge to close it. Every delegated item from here on repeats that.

## Proposed outcome
- A retired delegated item passes the chain check. Observable: on a tree where `spec.md` and `plan.md`
  read `status: superseded` with `approved-by: claude`, and `log.md` carries a `delegated -> superseded`
  line whose actor is a handle in `.sdlc/approvers.yaml` in a commit that handle authored,
  `python3 scripts/check_artifact_chain.py --slug <item>` ends `CHAIN: PASS` in both modes; the same
  tree with that ledger line's actor set to `claude` ends `CHAIN: FAIL` naming the line. A new case in
  `scripts/test_check_artifact_chain.py` pins each half, red before the change.
- A retirement is one tap that regenerates what it changes. Observable: `.github/workflows/approve.yml`
  accepts `mode: retire` (or an equivalent input the spec decides), runs the retirement the way the
  approval script would (three `superseded` statuses, three ledger lines, the pointer cleared or left to
  the owner's next grant), and commits through `scripts/approve_dispatch.py --commit`, which already
  regenerates the indexes; `gen_index.py --check` on the resulting commit prints `INDEX: up to date`. The
  web-editor route stays valid for a human who prefers it, and stays stale, as the lesson records.
- Nothing an agent can do becomes wider. Observable: `protect-approvals.sh` still refuses an Edit that
  sets `superseded` (eval `hook-blocks-agent-approval` and the existing hook cases green); `sign.py`
  still refuses `superseded`; the chain check still fails a `superseded` artifact whose retiring ledger
  line is agent-authored or missing.

## Affected users and systems
- Users: the owner, who retires every item; every session that cuts a branch from `main` in the window a
  retirement opens; the delegated loop, which cannot close an item cleanly today.
- Services / repos / data: `scripts/check_artifact_chain.py` (the approver rule for `superseded`; on the
  policy's `locked-paths`), `scripts/test_check_artifact_chain.py`; `scripts/approve.py` (a retirement
  mode, if the spec puts it there; locked) and `scripts/test_approve.py`; `.github/workflows/approve.yml`
  (the input; protected, so the owner's label and click); `docs/sdlc/github-setup.md` and
  `docs/sdlc/handoff/HANDOFF.md` (the routine); `knowledge/lessons/human-commits-leave-indexes-stale.md`
  (the tap half of the retirement route closes).

## Constraints
- Must: keep `superseded` a word only a human writes, and make the check read *who retired* from the
  ledger line and its commit author, never from `approved-by`, which stays the signature's record.
- Must: keep every existing chain-check case green unmodified; add the two retirement cases (human
  retirer passes, agent retirer fails) and see both red before the change.
- Must: route the tap's commit through `scripts/approve_dispatch.py --commit` so the indexes regenerate
  by the code that already does it; do not add a second regeneration path.
- Must not: relax the approver rule for `approved`; let a grant, a signature or an Edit set
  `superseded`; touch `.sdlc/`, `.claude/hooks/` or `scripts/checks/`.
- Out of scope: retiring an item automatically on merge (a human act by design,
  `knowledge/decisions/run-queue.md`); the advance itself (`work/advance-push`); the web-editor route's
  drift, which stays documented rather than enforced.

## Risk class
medium — the change loosens one rule of the approval chain, the approver check on `superseded`, under a
condition read from the ledger. The blast radius is every retired artifact's validity, and a mistake in
the condition could let an agent-authored retirement pass, which is a policy breach rather than a
production failure. The workflow change is one input on a protected file, the owner's click either way.
The same value is in the `risk-class` key above; the policy delegates `low` only, so this item is
supervised by construction and needs the tech lead's eye on spec and plan.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: where does the retirement mode live, `scripts/approve.py --retire` under the same `--from-dispatch`
  attestation, or a separate script? Proposed: `approve.py --retire`, so the tap runs the one script a
  human would run in a shell and the trailers, the role gate and the committer are the ones already
  verified; the script refuses an agent session as it does today.
  A:
- Q: should the retirement tap also clear `.sdlc/active`, or leave the pointer for the next grant tap to
  move? Proposed: leave it; every grant tap repoints the pointer, and clearing it makes the next
  `/sdlc-run` precondition fail until the owner taps again anyway.
  A:
- Q: for the chain check, is the retiring ledger line enough, or must the retirement commit also carry
  `Approved-Run`/`Approved-Actor` trailers like a dispatch approval? Proposed: the ledger line's actor
  plus the commit's author for a shell or web-editor retirement, and the trailers when the tap did it,
  the same two routes `check_grant_commit` already knows.
  A:
