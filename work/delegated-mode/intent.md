---
type: sdlc/intent
id: delegated-mode
title: A second way to run a work item, where I approve the start and the AI signs the rest under its own name
description: "Add a delegated mode beside the current supervised one: the owner approves the intent and grants delegation once, the agent signs spec, plan, review and merge under its own handle with every act in the ledger, plan changes are a recorded last resort, and everything tunable lives in one human-edited policy file."
stage: plan
status: approved
author: Luis Siviero (repo owner), interviewed by Claude in the session that drafted this item
approved-by: luissiviero
approved-on: 2026-09-05
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/issues/40
tags: [delegation, approvals, hooks, chain-check, auto-merge, policy, control-plane]
timestamp: 2026-09-05T11:28:24Z
---
# Intent: a second way to run a work item, where I approve the start and the AI signs the rest under its own name

## Problem
In the owner's words: "sometimes I just want a draft from Claude. In these cases the strict rules we set,
where I have to personally approve the commits, are overkill." The objective is "to give starting
instructions and be called back only after everything is done", with the AI doing "whatever I should do"
in between, "writing its own name, not mine, so we can know later on what I actually reviewed and what was
left for the AI."

Today every gate is human. Over the 57 pull requests merged on `main` between 2026-09-02 and 2026-09-05 the
ledgers record 44 approvals, the plans record 68 deviations, and every merge was a click from a phone. The
Maintain stage's first green run (`bands.yml` run 7) detected a 3-sigma breach on `pr_cycle_time_hours`
(21.31 hours against a trailing mean of 2.67) and filed issue 40 with a drafted `pr-review-bottleneck`
intent. The bottleneck is the owner's attention at gates that, for low-risk drafts, do not need it.

Two things must not change. First, the record: the ledger and the front matter must always say who signed
the current text and what the owner actually read. Second, the plan approved at the start is the contract:
in the owner's words, a mid-run change "must be thoroughly discussed internally (between AIs) to reach a
consensus that changing is the best course of action. If not, changes will start happening in a place I
won't be able to keep track."

Who is affected: the owner (every gate today), and every future adopter of the kit who wants a draft mode.
How we know: the ledger counts above; issue 40; the handoff's owner routine, which is a list of taps.

## Proposed outcome
- Two modes per work item, chosen by the owner on the intent: `supervised` (today, unchanged) and
  `delegated`. In delegated mode the owner's only acts are the intent approval with the delegation grant,
  and reading the ledger afterwards. The agent signs spec, plan and incident, runs the review, and the
  repository's own CI merges the pull request. Observable: one work item runs from grant to merge with no
  owner action after the grant, and `git log` shows no commit by the owner between the grant and the merge.
- The agent signs with its own handle, never the owner's. A new status word, `delegated`, marks every
  artifact the agent signed; `approved` stays a word only a human can write. Observable: `work/<slug>/log.md`
  carries one line per signature with the agent's handle; the hook refuses an agent edit that sets
  `approved` or a human handle; CI fails a `delegated` artifact whose signer is not a listed agent.
- A plan revision is the last resort. A file-list or order deviation is logged as today plus a ledger line,
  capped per item; anything else needs a consensus record with at least two independent reviewer verdicts,
  all `revise`, before the agent may re-sign. Observable: CI fails a second signature on an artifact that
  has no matching revision record, or one with a `keep` verdict, or fewer reviewers than the policy names.
- Everything tunable lives in one human-only file, `.sdlc/delegation.yaml`: which handles may sign, which
  artifacts, which risk classes, the deviation cap, the revision rule, and the merge conditions. Observable:
  changing a value there changes behaviour with no code change; a missing file switches the mode off.
- The gates that stay human whatever the mode: writing `approved`; the control plane and the verify loop;
  secrets; direct pushes and force pushes; deploys; release-gated paths; any risk class the policy does not
  list. Observable: the existing hooks, checks and tests for those gates are unchanged and still green.
- Handoff follow-ups absorbed on the way: the chain check reports an empty `.sdlc/active` in one clear
  line, and the lesson `workflow-permissions-name-every-api.md` gets its pointer in the rules fragment.

## Affected users and systems
- Users: the owner; adopters of the kit; every session that runs a delegated item.
- Services / repos / data: `.claude/hooks/` (approval, plan and path guards), `scripts/` (chain check,
  approvers, approval and signing scripts, index generator, a new merge decision script), `.sdlc/`
  (`active`, the new policy file created by the owner), `.github/workflows/` (a new merge workflow),
  `docs/sdlc/templates/` and `docs/sdlc/rules/` (new keys, a new status, a new revision template),
  `.claude/skills/` (sign-and-continue instead of stop, a new run skill), `REVIEW.md` (a summary line),
  `knowledge/decisions/` (a new record amending two existing ones).

## Constraints
- Must: keep `approved`, `approved-by` with a human handle, `mode`, `delegated-by` and `delegated-on`
  human-only at every layer that guards them today (hook, approvers file, CI commit-author check).
- Must: validate the delegation grant server-side before an automatic merge (the grant commit is
  GitHub-verified and authored by a product owner), because with the merge click gone the git author
  string is no longer a sufficient backstop.
- Must: never let the merge workflow check out or execute pull-request code; it reads head files through
  the API and refuses any diff that touches the control plane, the verify loop, release-gated paths, or the
  scripts that judge the merge.
- Must: keep one writer per work item (the session edits, subagents return evidence), per
  `knowledge/decisions/one-writer-until-ledger.md`.
- Must: ship this item itself in supervised mode, in small pull requests readable from a phone.
- Must not: touch `.sdlc/approvers.yaml`, `.sdlc/config.env`, or `.sdlc/release-authorizations/`.
- Must not: squash-merge delegated pull requests (a squash re-authors agent-signed lines as the opener).
- Out of scope: tiering the control-plane list so fewer diffs need the label (follow-up item); retiring
  `.sdlc/active` automatically when an item completes; the flaky eval `skill-spec-flags-concerns`; the
  NUL-byte check; pinning subagent models in `.claude/agents/`.

## Risk class
low — the change adds a mode and leaves the supervised path byte-for-byte as it is; every new permission is
fail-closed on a missing or disabled policy file; nothing deploys; reversal is a revert plus deleting the
policy file. Blast radius: which artifacts CI accepts and which pull requests merge without a click, both
limited to items the owner explicitly granted and to `risk-class: low`.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Where does the grant live, on the intent only, or may the owner grant from the plan onward?
  A: (answered in the session on 2026-09-05) On the intent only. The intent is the "starting instructions"
  the owner approves; the agent never signs it; spec and plan are the agent's from then on.
- Q: One work item or several? Merge workflow in the same item?
  A: (answered) One item, one chain, four small pull requests: vocabulary, hooks and scripts, prose, merge
  workflow. Control-plane tiering is a separate follow-up item. No cool-off before a merge.
- Q: What if the review workflow has no credential, or a check flakes?
  A: (proposed by the session) The merge fails closed and the owner gets the pull request as today; the
  owner can lower `require-review` in the policy file. Not a reason to loosen the default.
- Q: Which model runs the second reviewer of a revision record?
  A: (proposed by the session) A different model from the writer where the session can choose one; the
  record names the model per reviewer section so the owner can see it.
