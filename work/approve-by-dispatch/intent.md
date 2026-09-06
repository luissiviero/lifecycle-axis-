---
type: sdlc/intent
id: approve-by-dispatch
title: Give permission for the AI to change from one mode to the other when I request, without doing everything manually
description: "Make every approval and every delegation grant one tap in the Actions tab: a workflow_dispatch workflow that writes what approve.py writes, with GitHub's own record of who pressed Run as the human act, so the owner chooses supervised or delegated per item on request and never edits a file by hand."
stage: plan
status: approved
author: Luis Siviero (repo owner), interviewed by Claude in the session that closed work/delegated-mode
approved-by: luissiviero
approved-on: 2026-09-06
risk-class: low
mode: supervised
delegated-by:
delegated-on:
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/45
tags: [approvals, delegation, workflow-dispatch, control-plane, chain-check, auto-merge]
timestamp: 2026-09-06T02:05:00Z
---
# Intent: give permission for the AI to change from one mode to the other when I request, without doing everything manually

## Problem
In the owner's words, right after `work/delegated-mode` merged: "I need to give permission for the IA
change from one mode to the other when I request, without having to do everything manually — that for
both modes."

Today the choice of mode is a human act, by design (`knowledge/decisions/delegated-mode.md`, decision 2:
the grant lives on the intent and only a human writes it), but the act is typing. Running an item
delegated means, from a phone: edit the four grant keys and the three approval keys on `intent.md`, add a
ledger line to `log.md`, point `.sdlc/active` at the slug, and commit each of them as oneself. Running an
item supervised means the three approval keys plus a ledger line, three times per item. The shell shortcut
(`scripts/approve.py`) exists but assumes a shell, which the owner does not have on the phone. The
session that built delegated mode watched a web-editor edit fail to land four times (two approvals, the
policy switch, its fix), each costing a round trip; the master switch itself took three edits to get right
because its second key sits inside a nested block.

What must not change is the boundary: the AI can never write `approved`, `mode`, `delegated-by` or
`delegated-on`, because the ledger's whole value is saying what the owner actually decided. So the AI
cannot be given the mode switch. What it can be spared is the owner's typing: the decision stays the
owner's, the mechanics move to a machine the owner triggers.

Who is affected: the owner, at every gate; adopters of the kit, who inherit the same routine. How we know:
the ledger of `work/delegated-mode` (three approvals, one grant-switch, all by web editor, with the
retries in this session's transcript); `docs/sdlc/handoff/HANDOFF.md`, "Owner routine", which is a list
of taps that are still edits.

## Proposed outcome
- One tap per decision, from the Actions tab, for both modes. A `workflow_dispatch` workflow, "approve",
  with inputs `slug`, `artifact` (`intent.md`, `spec.md`, `plan.md`, `incident.md`), `mode`
  (`supervised` or `delegated`, read only for `intent.md`) and an optional note. The run writes exactly
  what `scripts/approve.py` writes today (the approval keys, the grant keys and `.sdlc/active` when the
  mode is delegated, the ledger line) and commits it. Observable: an intent is approved and granted from
  the phone with no file edited by hand; the ledger line names the owner; `check_artifact_chain.py` and
  `scripts/delegated_merge.py` accept the result exactly as they accept a web-editor commit today.
- The tap is the human act, and GitHub is its record. The run's actor (`github.actor`, the account that
  pressed Run, which no input and no commit field can spoof) must hold the artifact's role in
  `.sdlc/approvers.yaml`, or the run refuses and writes nothing. The commit the run makes cites its own
  run id, and the run's name carries the inputs, so the chain check and the merge script can verify a
  dispatch-made approval or grant against the run's server-side record, not against the commit alone.
  Observable: a run by a login outside the role fails without a commit; a commit citing a run whose actor
  or inputs do not match is refused by both checks.
- The AI still cannot press it. The production gate already treats `gh workflow run` as a deploy-class
  command (ask, or block when unattended), and the actor of a run is GitHub's record. The AI's part is to
  draft, push, and hand the owner the exact inputs: "Run approve: `<slug>`, `intent.md`, `delegated`".
  Observable: the eval suite has a case where an agent session's attempt to dispatch is refused.
- Both directions, per item, at approval time. `supervised` is the default and needs no grant; `delegated`
  is the grant on the intent; an item finishes in the mode it started (the chain check validates the grant
  as long as any artifact carries a signature, so a mid-run switch is refused, not silently accepted).
  Observable: the run skill and the setup doc state the rule; the chain check's existing behaviour pins
  it.
- The master switch in `.sdlc/delegation.yaml` stays on and is never part of the routine again.
  Observable: the owner routine in the handoff and the setup doc name one tap per gate and no file edit.

## Affected users and systems
- Users: the owner; adopters; every session that asks for an approval or a grant.
- Services / repos / data: `.github/workflows/` (a new `approve.yml`, `workflow_dispatch`, holding
  `contents: write` for the commit it makes: the second allowlist entry in
  `scripts/check_workflow_permissions.py`), `scripts/approve.py` (a mode usable from CI: the actor as the
  handle, the role checked, no interactive git identity), `scripts/check_artifact_chain.py` (a
  dispatch-made approval passes the commit-author check through the run's record), `scripts/delegated_merge.py`
  (a dispatch-made grant passes the committer rule the same way), `.claude/skills/sdlc-{intent,spec,plan,incident}`
  and `sdlc-run` (ask for the tap instead of "wait for a human"), `docs/sdlc/github-setup.md`,
  `docs/sdlc/README.md` (enforcement matrix), `docs/sdlc/handoff/HANDOFF.md` (owner routine),
  `knowledge/decisions/` (a record amending `delegated-mode.md`: the human act is the tap), the evals.

## Constraints
- Must: the identity of the approver is GitHub's record of who pressed Run, never a commit field the
  workflow or a session could set; the workflow refuses an actor outside the artifact's role in
  `.sdlc/approvers.yaml` or in `never-approve`, before writing anything.
- Must: a dispatch-made commit is verifiable after the fact by the chain check and the merge script (run
  id in the commit, inputs in the run's name, actor from the API), and both refuse a commit that cites a
  run whose actor, workflow or inputs do not match.
- Must: the workflow never checks out or executes pull-request code; it edits the four files of one work
  item and nothing else, on the item's branch for a supervised approval and on `main` for a delegated
  grant, so the delegated run and its merge can start from `main`.
- Must: the hooks that refuse agent-side `approved`, `mode`, `delegated-by`, `delegated-on` and
  `approve.py` stay exactly as they are; nothing in this item widens what a session may write.
- Must: ship this item supervised (it touches workflows and both judging scripts), in pull requests
  readable from a phone, and use the new workflow for its own later approvals only after the first one
  has landed.
- Must not: give the workflow any scope beyond `contents: write` on this repository, and never a secret.
- Must not: change `.sdlc/approvers.yaml`, `.sdlc/delegation.yaml` or `.sdlc/config.env`.
- Out of scope: retiring `.sdlc/active` when an item completes (the standing follow-up); control-plane
  tiering; pre-filling the run's inputs from a link (GitHub offers no such URL for dispatch inputs).

## Risk class
low — the supervised and delegated paths are unchanged in what they accept; this adds a second way to
produce the same commit, gated by a server-side identity that is stronger than the git author string the
chain check reads today, and it fails closed (an actor outside the role, a missing run, a mismatched run:
no commit, or a refused one). Blast radius: who can approve, which stays the handles in
`.sdlc/approvers.yaml`; reversal is deleting one workflow file. The one new surface is a workflow holding
`contents: write`, the same surface `delegated-merge.yml` already holds, reviewed the same way.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Every approval as a tap, or only the delegation grant?
  A: (proposed by the session) Every approval: intent, spec, plan, incident, in either mode. One routine
  to learn, and the supervised path gets the same relief.
- Q: Where does a delegated grant land, on the item's branch or on `main`?
  A: (proposed by the session) On `main`, in the same tap: the merge script reads the grant from the base
  branch only, so a grant on a branch would need one more click to count. A supervised approval lands on
  the item's branch, where the artifact under approval lives.
- Q: Who may press Run?
  A: (proposed by the session) Anyone with write access can press; the workflow refuses unless the actor
  holds the artifact's role in `.sdlc/approvers.yaml`. On this repository that is the owner alone;
  adopters see the rule in the setup doc.
- Q: How does the AI ask?
  A: (proposed by the session) It posts the three inputs in the chat and in the pull request body, and
  waits; under a delegation grant it never needs to ask again until the callback.
- Q: Should a run be able to demote an artifact (approved back to in-review)?
  A: (proposed by the session) No. The tap approves; a demotion stays a web-editor edit, as today.
