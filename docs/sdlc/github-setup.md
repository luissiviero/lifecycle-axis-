---
type: doc
title: GitHub-side setup for an adopted repository
description: "The first hour after scripts/adopt.sh, in order, and the GitHub settings the kit's gates rely on: plan check, branch protection, the control-plane-approved label, secrets, and the review App."
tags: [sdlc, adopt, github, setup, branch-protection]
timestamp: 2026-09-05T21:00:00Z
---

# GitHub-side setup for an adopted repository

`scripts/adopt.sh` copies the kit into your repository (this file travels with it). What it cannot do is
approve anything as you or change your GitHub settings. This page is that remainder, in the order that
keeps every check green from the first pull request.

## The first hour, in order

1. **Replace the placeholder handle.** `adopt.sh` wrote `<your-github-handle>` into every role of
   `.sdlc/approvers.yaml` and every line of `.github/CODEOWNERS`. Put your GitHub login there (no `@` in
   `approvers.yaml`; keep the `@` in `CODEOWNERS`). Until you do, nothing can approve: `approvers.py` refuses
   any handle still in angle brackets, so `approve.py --as '<your-github-handle>'` cannot approve the example
   item and the plan gate stays closed. Replace it and approval works; a real login has no angle brackets.
2. **Set the verify command.** `.sdlc/config.env` holds a placeholder `VERIFY_CMDS` that prints a TODO and
   fails, so `scripts/verify.sh` is red on purpose until you set it (`npm test`, `pytest -q`, `make lint`;
   separate several with `;`).
3. **Approve the example item as yourself, from your own shell** (not from an agent session; the script
   refuses there and the chain check rejects agent-authored approvals):
   ```
   git init   # if the repo is new; the script needs a git repository
   python3 scripts/approve.py _example intent.md spec.md plan.md --as <your-github-handle>
   ```
   `work/_example/` ships `in-review` with a plan that lists exactly the files `adopt.sh` installed, so the
   plan gate is closed until this step and the install commit is covered by that plan after it.

   **Or approve from the Actions tab, once this branch is on GitHub.** *Actions → approve → Run workflow*,
   with `artifact` (the chain file), `mode` (`supervised`, or `delegated` to grant delegated mode on an
   intent), `slug` (blank means whatever `.sdlc/active` names on the selected branch) and an optional `note`.
   The branch selector is the target: the run commits and pushes to it, so a grant must be dispatched from
   the default branch. This is the same script with the run's actor as the handle, and it is the routine an
   agent will ask you for, because it is one gesture rather than a shell. The run refuses before writing
   anything if the actor does not hold the artifact's role, so a wrong tap changes nothing.
4. **Commit as yourself** and open the install pull request. `sdlc-gate` runs `check_artifact_chain.py`
   against the base branch; with the approvals in the same PR it ends `CHAIN: PASS`.
5. **Fill the top of `CLAUDE.md`.** `adopt.sh` seeded `## Commands`, `## Architecture` and `## Lessons
   learned` above the generated block; those sections are yours, the block is regenerated from
   `docs/sdlc/rules/`.
6. Do the GitHub settings below, then run the loop once by hand: `/sdlc-intent` → `/sdlc-spec` → `/sdlc-plan`
   → implement → `/sdlc-review`.

## Plan check first

Branch protection, rulesets and environment protection rules return HTTP 403 ("Upgrade to GitHub Pro or make
this repository public") on a **private repository under the Free plan**. If that is your situation, the checks
are informational and the merge click is the gate: read the checks, then merge (the kit's own decision record
on this is `knowledge/decisions/merge-click-is-the-gate.md`). The checklist below applies once the repository is
public or on a paid plan.

## Labels

- Create the label **`control-plane-approved`** (Issues → Labels → New label). CI blocks any agent-authored
  pull request (head branch under `claude/`, `kit/` or `spike/`, a Bot author, or a Claude commit trailer) that
  touches `PROTECTED_PATHS` from `.sdlc/config.env` (`.claude/hooks/`, `.github/workflows/`, `.sdlc/`,
  `.gemini/`, `.claude/settings.json`, `scripts/verify.sh`, the two runners, `scripts/checks/`). A human
  applying this label after reading that part of the diff is the only exemption.

## Branch protection (on `main`)

- [ ] Require a pull request before merging: **on**; required approving reviews **1**; dismiss stale approvals
      when new commits are pushed: **on**.
- [ ] Require review from Code Owners: **on** (`.github/CODEOWNERS`, with your handle from step 1).
- [ ] Require approval of the most recent reviewable push: **off** while there is one human; **on** with a
      second one.
- [ ] Require status checks: `sdlc-gate / artifact-chain`, later `pr-review`. **Never `agent-evals`**: it runs
      nightly and on demand, not on every pull request, and a required check that never reports blocks every
      merge forever. Require branches to be up to date: **off**, with "one agent code pull request open at a
      time" as the compensating control (the queue branches each code pull request from a fresh `main`);
      require conversation resolution: **on**.
- [ ] Create the **`triage`** label (Issues → Labels). A red gate does not run the model triage step unless a
      human applies it; `labeled` is a trigger, so applying it re-runs the gate with triage on. That step was
      3.6 minutes median and 10.6 at worst, most often on a failure that was not the pull request's own.
- [ ] Do not allow bypassing the above settings: **off** with one human (the admin-merge escape hatch, logged
      as a `work/<slug>/log.md` line naming the merge); **on** with two.
- [ ] Restrict who can push: you plus the Claude App; block force pushes and deletions.
- [ ] **`sdlc-gate` runs only on `pull_request`.** A direct push to `main` sees no gate at all. With branch
      protection, direct pushes are refused; without it, work by pull request only.

## Actions and secrets

- [ ] Settings → Actions → General: workflow token permissions **read-only**; "Allow GitHub Actions to create
      and approve pull requests" **unchecked**. Every kit workflow declares its own `permissions:`;
      `scripts/checks/workflow-permissions.sh` fails `verify.sh` if one ever asks for `contents: write`, with
      one exception: `delegated-merge.yml`, allowlisted by name for the merge endpoint it calls.
- [ ] Secrets: `ANTHROPIC_API_KEY` at repository scope with a spend limit, or `CLAUDE_CODE_OAUTH_TOKEN` from
      `claude setup-token` on a Pro/Max plan. Without one, prompt-based evals are skipped (and counted), the
      `pr-review` workflow does nothing, the `bands` workflow files the raw detector output, and the
      `sdlc-gate` triage step is skipped (it is also skipped without the `triage` label, whatever the
      credential). Nothing fails for lack of a key.
- [ ] Install the Claude GitHub App on the repository so `pr-review.yml` can post its review as `claude[bot]`,
      an identity distinct from yours that can never approve.
- [ ] `deploy.yml` runs behind a GitHub Environment (`production`); add its required reviewers where the plan
      allows it, and store `RELEASE_APPROVAL` as an Environment secret per release
      (`knowledge/runbooks/rollback-deploy.md`), or commit `.sdlc/release-authorizations/<sha>` as a
      release manager.

## Delegated mode (optional)

A second mode where the agent signs its own progress and a CI workflow, not a click, merges the pull request.
Off by default; opt in per repo.

1. **Copy the policy template and edit it there.** `cp docs/sdlc/templates/delegation.yaml
   .sdlc/delegation.yaml`, then tune `agents`, `signable`, `risk-classes`, `max-deviations`, `revisions`,
   `min-reviewers` and `merge` to taste. This is the one tuning surface for the mode; it is human-only, like
   `.sdlc/approvers.yaml`, and on `protect-paths.sh`'s never-unlock list. The master switch is `enabled`: flip it
   in `.sdlc/delegation.yaml` on `main` from the web editor, in either direction; no agent session can, since
   the file never unlocks. In the kit's own repository it is `false` until the owner turns it on.
2. **Grant it on an intent, from your own shell:**
   ```
   python3 scripts/approve.py <slug> intent.md --delegate --activate --as <your-github-handle>
   ```
   or edit the same four keys (`risk-class`, `mode`, `delegated-by`, `delegated-on`) plus the ledger note
   in the GitHub web editor. Land it on `main`: the merge workflow reads the grant, and the `.sdlc/active`
   slug it must match, from the base branch only, so a grant that exists only on the pull request's own
   branch never counts.
3. **Sign the grant commit.** A local commit needs `git commit -S`: the merge workflow verifies the grant
   commit server-side (a verified signature, `author.login` holding `product-owner`), and an unsigned local
   commit fails that check even with the right author. A web-editor commit is GitHub-signed already, so
   this step only matters on the shell path.
4. **What happens next, and when you are called back.** `/sdlc-run` drives the item from the grant to a
   ready pull request without stopping, signing each artifact with `scripts/sign.py` under its own handle.
   You are called back at a deviation cap, a `keep` verdict with no consensus on a plan revision, a path the
   policy locks, a red check the item cannot fix, or a hook refusal it does not understand — otherwise the
   delegated-merge workflow merges once its printed conditions hold. Two waits fail closed by design: no
   Claude credential means no `claude[bot]` review comment, so `require-review` never turns true; and a pull
   request editing `.claude/skills/`, `.claude/agents/` or `CLAUDE.md` always draws a false `Important` from
   the reviewer, which restores those files from `main` before it runs and so never sees the diff. Set
   `require-review: false` in the policy to accept that trade; it is a deliberate loosening, not a default.
5. **Read the verdicts for any open pull request without a shell.** Actions → `delegated-merge` → Run
   workflow, with the pull request's head sha: the run prints one `CONDITION` line per check and never
   merges (that route is dry-run only). Two rules the conditions imply: `merge.require-checks` lists only
   workflows that run on every pull request (`agent-evals.yml` runs nightly and on demand only, so it has no
   run to be green on a pull request, and the script refuses rather than waits), and the intent's
   `delegated-by` is the login that made the grant commit. A pull request that spent time as a draft carries
   a `skipped` run of each required workflow on the same sha as its ready run; the script ignores those, and
   a `cancelled` run only where a later run of the same workflow on that sha succeeded (work/ci-budget).
   A pull request on a supervised item ends its merge run green with `not-delegated` rather than red: red
   there means a human is needed.

## Related

- `docs/sdlc/README.md` §3, "Using it in a project".
- `knowledge/decisions/adopt-script.md`: what `adopt.sh` copies, merges, rewrites and writes.
- `docs/sdlc/spikes/pr-review-identity.md`: why the reviewer is a separate identity.
