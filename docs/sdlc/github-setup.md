---
type: doc
title: GitHub-side setup for an adopted repository
description: "The first hour after scripts/adopt.sh, in order, and the GitHub settings the kit's gates rely on: plan check, branch protection, the control-plane-approved label, secrets, and the review App."
tags: [sdlc, adopt, github, setup, branch-protection]
timestamp: 2026-09-05T03:00:57Z
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
- [ ] Require status checks: `sdlc-gate / artifact-chain`, `agent-evals`, later `pr-review`; require branches
      to be up to date: **on**; require conversation resolution: **on**.
- [ ] Do not allow bypassing the above settings: **off** with one human (the admin-merge escape hatch, logged
      as a `work/<slug>/log.md` line naming the merge); **on** with two.
- [ ] Restrict who can push: you plus the Claude App; block force pushes and deletions.
- [ ] **`sdlc-gate` runs only on `pull_request`.** A direct push to `main` sees no gate at all. With branch
      protection, direct pushes are refused; without it, work by pull request only.

## Actions and secrets

- [ ] Settings → Actions → General: workflow token permissions **read-only**; "Allow GitHub Actions to create
      and approve pull requests" **unchecked**. Every kit workflow declares its own `permissions:`;
      `scripts/checks/workflow-permissions.sh` fails `verify.sh` if one ever asks for `contents: write`.
- [ ] Secrets: `ANTHROPIC_API_KEY` at repository scope with a spend limit, or `CLAUDE_CODE_OAUTH_TOKEN` from
      `claude setup-token` on a Pro/Max plan. Without one, prompt-based evals are skipped (and counted), the
      `pr-review` workflow does nothing, the `bands` workflow files the raw detector output, and the
      `sdlc-gate` triage step is skipped. Nothing fails for lack of a key.
- [ ] Install the Claude GitHub App on the repository so `pr-review.yml` can post its review as `claude[bot]`,
      an identity distinct from yours that can never approve.
- [ ] `deploy.yml` runs behind a GitHub Environment (`production`); add its required reviewers where the plan
      allows it, and store `RELEASE_APPROVAL` as an Environment secret per release
      (`knowledge/runbooks/rollback-deploy.md`), or commit `.sdlc/release-authorizations/<sha>` as a
      release manager.

## Related

- `docs/sdlc/README.md` §3, "Using it in a project".
- `knowledge/decisions/adopt-script.md`: what `adopt.sh` copies, merges, rewrites and writes.
- `docs/sdlc/spikes/pr-review-identity.md`: why the reviewer is a separate identity.
