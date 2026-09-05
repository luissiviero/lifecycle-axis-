---
type: decision
title: A second, delegated mode where an agent signs under its own handle and CI merges
description: "Beside the existing supervised mode, an owner-approved intent may carry a delegation grant (mode, delegated-by, delegated-on, risk-class); under it the agent signs spec, plan and incident status delegated with its own handle from .sdlc/delegation.yaml, a plan deviation past a cap needs a committed, unanimous revision record, and a CI workflow, not a click, merges the pull request. Decided in work/delegated-mode (issue 40)."
tags: [delegation, approvals, hooks, chain-check, auto-merge, policy, control-plane, sdlc]
timestamp: 2026-09-05T12:05:00Z
---

# A second, delegated mode where an agent signs under its own handle and CI merges

> **Amends [`human-only-approvals.md`](human-only-approvals.md)** (an agent may now sign
> `status: delegated`, under a grant; `approved` stays a word only a human writes, as that record
> decided) **and supersedes [`merge-click-is-the-gate.md`](merge-click-is-the-gate.md) for
> delegated items only** (the CI merge workflow is the gate for those; every supervised item still
> waits on the owner's click, unchanged).

## Context

The owner, in the session that drafted `work/delegated-mode/intent.md`: "sometimes I just want a
draft from Claude. In these cases the strict rules we set, where I have to personally approve the
commits, are overkill." The wanted shape: "give starting instructions and be called back only
after everything is done", the agent doing "whatever I should do" in between, "writing its own
name, not mine, so we can know later on what I actually reviewed and what was left for the AI." In
the same breath, the plan approved at the start stays the contract: a mid-run change "must be
thoroughly discussed internally (between AIs) to reach a consensus that changing is the best course
of action. If not, changes will start happening in a place I won't be able to keep track."

The numbers behind the ask: over the 57 pull requests merged on `main` between 2026-09-02 and
2026-09-05, the ledgers record 44 human approvals, the plans record 68 deviations, and every merge
was a click from a phone. `bands.yml`'s first green run (run 7) caught a 3-sigma breach on
`pr_cycle_time_hours` — 21.31 hours against a trailing mean of 2.67 — and filed issue 40 with a
drafted `pr-review-bottleneck` intent. Every gate being human is the bottleneck, for drafts where
the owner's attention was never the scarce resource.

## Decision

1. **A distinct status word, `delegated`, never `approved`.** `human-only-approvals.md` still holds
   for `approved`: no hook, script or CI check ever lets an agent write it. `delegated` is a fifth
   value in every enumeration that lists `status` (`check_artifact_chain.py`, the four templates'
   comments, `docs/sdlc/rules/00-chain.md`, `docs/sdlc/templates/log.md`,
   `knowledge/lessons/ledger-slot-holds-status-only.md`), so every existing reader that treats
   `approved` as "a human read this" stays correct without a change.
2. **The grant lives on `intent.md` only, and only a human sets it.** `risk-class`, `mode`,
   `delegated-by`, `delegated-on` sit in the intent's front matter, right after `approved-on`, with
   the same protection: `protect-approvals.sh` refuses any agent-side change to any of the four,
   `scripts/approve.py --delegate` (run from the owner's own shell, or the same four lines edited in
   the GitHub web editor) is the only writer. The agent never signs the file that carries its own
   grant, so it cannot widen its own permission.
3. **The agent signs with its own handle, from the policy, never the owner's.**
   `scripts/sign.py <slug> <artifact>` refuses to run outside an agent session, checks the handle
   (`SDLC_AGENT_HANDLE`, default `claude`) against `.sdlc/delegation.yaml`'s `agents` list, and
   writes `status: delegated`, `approved-by: <handle>`, `approved-on`, plus the ledger line — the
   only honest-path writer of a delegated signature, exactly as `approve.py` is for `approved`.
4. **A plan revision is a recorded last resort, not a skill's good intentions.** A file-list or
   order deviation logs as today, plus a ledger line, capped at `.sdlc/delegation.yaml`'s
   `max-deviations`. Anything larger needs a committed `work/<slug>/revisions/<n>.md` — the trigger,
   the proposal, and one `## Reviewer: <role> (<model>)` section per `min-reviewers`, each ending
   `verdict: revise` — before `sign.py --revision` will re-sign; `check_artifact_chain.py` checks
   the same record again from CI, independent of the skill that produced it.
5. **Everything tunable lives in one human-only file, `.sdlc/delegation.yaml`.** Which handles may
   sign, which artifacts, which risk classes, the deviation cap, the revision rule, and the merge
   conditions are all policy, read through exactly two entry points
   (`scripts/delegation.py` for Python, the `policy_*` helpers in `_lib.sh` for the hooks). The file
   is on `protect-paths.sh`'s never-unlock list, so no agent session writes it even with the
   control-plane unlock set; a missing file or `enabled: false` turns delegated mode off everywhere,
   with supervised mode untouched.
6. **The merge is a CI workflow, deterministic, for delegated items only.**
   `.github/workflows/delegated-merge.yml` fires on `workflow_run` from the default branch and calls
   `scripts/delegated_merge.py`, which merges only when every condition it prints holds: the policy
   allows it, the grant on the head's `intent.md` is server-side verified (a GitHub-verified commit
   authored by a product owner, not merely git-authored), every required check is green, the diff
   touches none of `PROTECTED_PATHS`, `RELEASE_GATED_PATHS` or the policy's own `locked-paths`, and
   (when `require-review`) the review comment ends `Important: 0`. It merges as
   `github-actions[bot]`, `merge_method: merge` (never squash, so agent-signed commits keep their
   own author for the `-G` checks the chain check runs), deletes the branch, and comments naming the
   grant commit. This is the click, for delegated items only; every supervised pull request still
   waits on the owner's click as `merge-click-is-the-gate.md` describes.
7. **The gates that stay human, in every mode.** Writing `approved`; the control plane and the
   verify loop; secrets; direct and force pushes; deploys; release-gated paths; any risk class the
   policy does not list. The existing hooks, checks and tests for those are unchanged.

## Alternatives considered

| # | Alternative | Why not |
|---|---|---|
| D-a | `approved` with an agent handle, instead of a new status word | breaks every existing rule and reader that treats `approved` as "a human read this"; one new enum value is cheaper than re-auditing all of them |
| D-b | The grant on `plan.md` (or later), instead of `intent.md` only | would let a later artifact grant permission for its own signing, and a plan revision could quietly widen the grant along the way |
| D-c | Delegation keys folded into `.sdlc/config.env` and `.sdlc/approvers.yaml`, instead of one new file | two parsers and two never-unlock entries to keep in sync, against `approvers._parse`'s `TOP_KEYS` check, which already raises on an unlisted top-level key |
| D-d | The revision rule stated only in a skill, with no committed record | unauditable: the owner could not later find which plan changes happened, on whose say, or under what pressure — exactly the loss of track the owner named as the line not to cross |
| D-e | The session itself running `gh pr merge`, instead of a CI workflow | keeps a credential and a discretionary act in the agent's hands where the owner asked for none after the grant; `github-actions[bot]` merging under fixed, printed conditions removes the discretion |
| D-f | `squash` or `rebase` as the merge method | a squash re-authors every agent-signed commit as whoever clicked merge, which is exactly what the ledger and the `-G` author checks must not lose |
| D-g | One large pull request for the whole item, instead of four small ones | unreadable from a phone, and the owner's stated review habit is a list of taps; small pull requests keep every review inside that habit |

## Consequences and residuals

- **An agent identity now satisfies a gate a human satisfied alone before.** The residual spec C3
  names directly: a session running with the owner's own `gh` login could still create a
  GitHub-verified, product-owner-authored grant commit through the API, since the API call itself
  would carry the owner's authentication. Delegated mode is therefore built to require the session
  to hold an agent identity — the remote Claude app identity, or a bot token locally — never the
  owner's login; `protect-approvals.sh`'s Bash branch refuses a mutating `gh api` call against a
  `contents/` or `git/` path, and a GraphQL `createCommitOnBranch`, `createRef`, `updateRef`,
  `deleteRef` or `mergePullRequest` mutation, regardless; a raw `curl` to the same endpoints is not caught, which is the identity
  residual restated: the boundary is which login the session holds, not the hook.
- **The Bash guard's blind spot is unchanged, and now covers one more honest-path script.**
  `human-only-approvals.md` already notes that the write-candidate parser cannot see a command it
  does not recognise — a Python heredoc, an obfuscated variable split — so it is a tripwire on the
  honest path, not a sandbox. `scripts/sign.py` sits behind the same tripwire as `approve.py`: the
  hook refusing a command that names it is a convenience, and `sign.py`'s own `CLAUDECODE` check
  plus CI's `check_artifact_chain.py` (signer must be a listed agent, the grant must be a verified,
  product-owner commit) are the backstops that hold regardless of how the write was spelled.
- **`require-review` fails closed with no credential, not silently.** If `pr-review` has no
  credential and never posts the `claude[bot]` tracking comment, `delegated_merge.py`'s
  `require-review` condition simply never becomes true; the pull request waits for the owner, same
  as a missing policy file. The owner can lower `require-review` in `.sdlc/delegation.yaml`; that is
  a deliberate loosening, not a default.
- **The advisory reviewer cannot see a pull request's own changes to `.claude/` or `CLAUDE.md`.**
  `pr-review.yml` restores both from the base branch before it runs, so a delegated pull request that
  touches `.claude/skills/`, `.claude/agents/` or `CLAUDE.md` always draws a false `Important` from
  the reviewer and so always waits for the owner under `require-review`, observed on pull request 44.
  This is the same fail-closed shape as a missing credential, not a separate hole; the owner can lower
  `require-review` to accept the trade for such a pull request.
- **The `-G` pickaxe reads text, not meaning.** The grant-commit author check and the hooks' word
  rule both look for the literal `mode: delegated` (or `status: approved`) on its own line in a
  commit's diff. A prose sentence that happened to contain that exact line, inside `work/`, would
  read as the grant or the approval; the convention that keeps this from happening is that neither
  literal is ever written that way outside `docs/sdlc/templates/` and this decision record, which
  the check does not read. This is a limitation of a text-based check, accepted the same way
  `human-only-approvals.md` already accepts it for the word rule on `approved`.

## Links

- `work/delegated-mode/intent.md`, `work/delegated-mode/spec.md`, `work/delegated-mode/plan.md`
- `knowledge/decisions/human-only-approvals.md`, `knowledge/decisions/merge-click-is-the-gate.md`
- `.sdlc/delegation.yaml` (shipped in pull request 43, a byte-for-byte copy of
  `docs/sdlc/templates/delegation.yaml`; switched off by the owner's commit 9e405fa)
- `scripts/sign.py`, `scripts/delegated_merge.py`, `scripts/delegation.py`
