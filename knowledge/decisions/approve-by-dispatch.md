---
type: decision
title: The tap in the Actions tab is the human act
description: A workflow_dispatch workflow runs scripts/approve.py with the run's actor as the handle and commits the result, so every approval and every delegation grant is one tap; the commit carries Approved-Run and Approved-Actor trailers, and the chain check and the merge script resolve them against the run record rather than trusting the commit. Decided in work/approve-by-dispatch.
tags: [approvals, delegation, workflow-dispatch, control-plane, chain-check, auto-merge, sdlc]
timestamp: 2026-09-06T18:30:00Z
---

# The tap in the Actions tab is the human act

## Context

Approving meant editing YAML front matter and appending a ledger line, in a shell with
`scripts/approve.py` or by hand in the GitHub web editor. Both work and both are the owner's own
act, but both are manual enough that the owner asked for something else: *give permission for the
AI to change from one mode to the other when I request, without doing everything manually, for both
modes*.

The obvious shortcut — let the agent write `approved` when asked — is the one thing the kit refuses,
and for a good reason: `human-only-approvals.md` makes `approved` a word no hook, script or check
ever lets an agent write, and `delegated-mode.md` kept that line intact even while adding a second
status word. What was needed was not a weaker rule but a *cheaper human act*: something that takes
one gesture and still leaves a record only a human could have caused.

## Decision

1. **The tap is the act, and GitHub records it.** `.github/workflows/approve.yml` runs on
   `workflow_dispatch` with four inputs. `github.actor` on the resulting run names whoever pressed
   Run. That field is not an input, not a commit field, and not writable by the token: nothing
   inside the run can change it. Everything the run writes is therefore attributable to that person.

2. **Pressing is not deciding.** Anyone with write access can press Run. The first step refuses an
   actor who does not hold the artifact's role in `.sdlc/approvers.yaml`, before anything is
   written, so a refusal leaves the tree untouched. On this repository that role is the owner alone.

3. **The same script, not a second implementation.** The workflow calls `scripts/approve.py`, the
   one the owner would call in a shell, through a new `--from-dispatch RUN_ID` flag. The flag is
   refused unless `GITHUB_ACTIONS` is `true` and `GITHUB_RUN_ID` matches, so passing it from a
   session buys nothing. Every file the flag's run writes is byte-identical to a plain run. The two
   routes cannot drift.

4. **Author is the actor, committer is the bot.** `is_agent_identity` matches `[bot]@` in the
   *email*, so committing entirely as `github-actions[bot]` would have made every dispatch-made
   approval depend on the API path, which fails closed on a local `verify.sh` with no token. With
   the author as the actor, the existing git-author rule keeps working untouched and the trailers
   add verification on top. The committer stays the bot so the commit never claims a human typed it.

5. **The trailers are checked, not believed.** `Approved-Run` and `Approved-Actor` are message text,
   which anyone can write. `check_artifact_chain.py` requires the trailer's actor to equal the
   artifact's `approved-by`, then resolves the run against the Actions API: event, workflow path,
   conclusion and actor must all agree. `delegated_merge.py` does the same for a grant.

6. **Two routes, chosen — never tried in turn.** `check_grant_commit` picks route A (a human's own
   signed commit) or route B (a dispatch) from the commit itself, and evaluates only that route's
   conditions. A trailer that does not resolve is refused outright. A fallback would have made a
   forged trailer a way to *choose* the weaker check.

7. **Route B has no signature condition, because it cannot have one.** Measured rather than
   assumed: in this repository's own history, commits GitHub creates server-side carry a signature
   (`git log --format=%G?` reports `E`) and commits pushed over git carry none (`N`). A runner
   pushes over git. The two API mechanisms that *are* signed were ruled out by other requirements —
   the REST contents API writes one file per call, so it cannot be the single commit the checkers
   key on, and GraphQL `createCommitOnBranch` sets author and committer to the token identity,
   destroying decision 4. The signature was only ever a proxy for "a human caused this"; the run
   record is a stronger one.

8. **The AI still cannot press it.** `production-gate.sh` already catches `gh workflow run` and a
   POST to the dispatches endpoint. An eval pins that, so the guard cannot be narrowed later
   without going red.

## Alternatives considered

- **Let the agent write `approved` when the owner says so in chat.** Rejected: a chat message is not
  a record. It leaves nothing a later reader or CI can verify, and it is exactly what
  `human-only-approvals.md` exists to prevent.
- **A `branch` input on the workflow.** Rejected: GitHub's "Use workflow from branch" selector
  already *is* that input, and a second one could disagree with it.
- **Commit entirely as `github-actions[bot]`.** Rejected, see decision 4.
- **Require a GitHub signature on the dispatch-made commit.** Rejected as unsatisfiable, see
  decision 7.

## Consequences

- The owner chooses supervised or delegated per item from a form, and never edits a file by hand.
- One new API surface for the chain check, `repos/{repo}/actions/runs/{id}`. It is granted
  explicitly on `sdlc-gate.yml` (`actions: read` plus `GH_TOKEN`) rather than left to the code
  change, because a missing scope would fail *open* — the check would print its no-token note and
  never verify the attestation. That is the failure
  `knowledge/lessons/workflow-permissions-name-every-api.md` records.
- A commit whose author is the owner may not have been typed by the owner. This narrows rather than
  widens the existing residual: the author field is already forgeable with `git commit --author`,
  which `human-only-approvals.md` accepts as backstopped by CI, and a dispatch-made approval is
  *verifiable* where a hand-typed one is only plausible.
- `git log` now shows a split identity on approval commits. Explained here so a reader is not
  misled.
- A branch cut before `approve.yml` existed cannot be selected in the Actions tab; the first branch
  after this merges is the first that can.
