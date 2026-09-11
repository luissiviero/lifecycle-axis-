---
type: decision
title: Control-plane exemption is a human-applied PR label
description: The CI job that blocks agent-authored changes to protected paths is exempted only by a human with write access applying the control-plane-approved label after reviewing the diff; the check re-runs on label events.
tags: [ci, control-plane, github-actions, labels, sdlc]
timestamp: 2026-09-04T23:42:26Z
---

# Control-plane exemption is a human-applied PR label

## Context

Defect 2 in `work/sdlc-kit-phase-1/plan.md`: the scaffold's control-plane job in
`sdlc-gate.yml` fails *any* PR whose author looks agent-shaped (`user.type == 'Bot'` or a
`claude/*` head ref) and whose diff touches `PROTECTED_PATHS`
(`.claude/hooks .github/workflows .sdlc`) — with no escape hatch. That is correct as a default
(agents should not modify the enforcement layer unsupervised) but wrong as an absolute: this very
plan's own tasks (T05, T10–T14, T19–T22) legitimately touch those paths, reviewed by Fable and the
owner in-session. PR #1 itself would fail the job as originally written.

The fix needs to keep the block automatic and deterministic — never satisfied by anything an agent
can say about its own diff — while giving a human a one-click way to let a specific, already-seen
diff through.

## Decision

`scripts/check_control_plane.sh <base-ref>` is extracted from the inline workflow step (defect 2)
and gains a label exemption:

1. No changes under any `PROTECTED_PATHS` prefix → `CONTROL-PLANE: clean`, exit 0. This is the
   common case and needs no human action.
2. Changes present, but the PR is human-authored (`SDLC_PR_AUTHOR_TYPE` is not `Bot`,
   `SDLC_PR_HEAD_REF` does not start with an entry in `AGENT_BRANCH_PREFIXES` from
   `.sdlc/config.env`, default `claude/ kit/ spike/`, and no commit in `<base>..HEAD` carries a
   `Co-Authored-By: … Claude` or `Claude-Session:` trailer)
   → informational pass: `CONTROL-PLANE: human-authored, review by CODEOWNERS`, exit 0. CODEOWNERS
   (`.github/CODEOWNERS`) already requires the owner's review on these paths; this job does not
   duplicate that gate.
3. Changes present, agent-authored, and the PR carries the `control-plane-approved` label
   (`CONTROL_PLANE_LABEL` in `.sdlc/config.env`, casefolded compare) → `CONTROL-PLANE: EXEMPT
   (label control-plane-approved applied by a human with write access)`, exit 0.
4. Otherwise → the touched files, then `CONTROL-PLANE: BLOCKED — agent-authored change to
   protected paths. A human with write access applies the label 'control-plane-approved' after
   reviewing the diff above; the check re-runs on label.`, exit 1.

`sdlc-gate.yml` carries `labeled, unlabeled` in `on.pull_request.types` so applying or removing the
label re-triggers the job without a new commit, and always tees the script's output to
`$GITHUB_STEP_SUMMARY` so the touched-file diff is visible on every run, not only a blocked one.

Only accounts with write access to the repository can apply labels (GitHub's default permission
model), so the label itself is the access control — no separate allowlist is needed here.

## Residual risk

**The label persists across pushes.** GitHub does not remove a label when new commits land on a
PR. Once `control-plane-approved` is applied, every subsequent commit to that PR — including one
that touches a *different* protected path than the one a human reviewed — passes this check
without a fresh look, until someone removes the label.

## Mitigations

- **Write access only.** Applying the label already requires the same repository permission as
  pushing directly to protected paths by hand; the label cannot be used to grant more access than
  the applier already has.
- **Branch protection dismisses stale approvals.** `docs/sdlc/spikes/pr-review-identity.md`'s
  checklist turns on "dismiss stale approvals when new commits are pushed", so a post-label commit
  still needs a fresh required review before merge even though this CI job alone would pass it —
  the label exempts one job, not the merge gate.
- **The label is a CI exemption, not a merge permission.** It only silences
  `check_control_plane.sh`; branch protection's required status checks, required review, and
  CODEOWNERS still apply to the merge itself.
- **The diff is printed on every run.** `$GITHUB_STEP_SUMMARY` shows the touched protected-path
  files whether the job passes, is exempt, or blocks, so a reviewer re-checking a labelled PR after
  new commits can see at a glance whether the set of touched files has grown.

A future hardening (not built here): a workflow that removes the label automatically whenever a
new commit changes the set of touched protected-path files, forcing re-review. Left for adoption
if the residual risk proves costly in practice.

Two residuals recorded by `work/control-plane-visibility` (spec C3, C4):

- **The label can be applied by the agent's own session.** An agent running under the owner's
  login can run `gh pr edit --add-label control-plane-approved`; nothing in the kit gates that
  call. The owner's review under CODEOWNERS and branch protection remain the gate against intent.
- **Trailer detection needs trailers.** The prefix list and the trailer scan are belt and braces,
  not proof: a session that commits without a Claude trailer on a `work/<slug>` branch is still
  human to this job. The hook and `.sdlc/hook-decisions.log` are the local record for that case.
