---
type: spike
title: PR review action, bot identity, and branch protection
description: claude-code-action v1 inputs and minimum permissions, the identity its review posts under, whether a bot review can satisfy "require 1 approval", and the single-human branch-protection setup.
tags: [ci, review, github-actions, branch-protection, identity, sdlc]
timestamp: 2026-09-02T00:00:00Z
status: decided
---

# Spike T04 - review action, identity, branch protection

Sources: Context7 `/anthropics/claude-code-action` plus live `raw.githubusercontent.com/anthropics/claude-code-action/main/{action.yml,README.md,src/github/constants.ts,docs/*.md}`. **`docs.github.com` is blocked by the egress proxy** (`EGRESS_BLOCKED`), as is `api.github.com` outside this repo, so every GitHub-platform claim below comes from WebSearch of community discussions - UNVERIFIED.

## Findings

### 1. `anthropics/claude-code-action@v1` inputs (action.yml - verified)
| Need | Input |
|---|---|
| API key | `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` (alt: `claude_code_oauth_token`, or OIDC federation via `anthropic_federation_rule_id` + `anthropic_organization_id`, which needs `id-token: write` and no static key) |
| Prompt | `prompt:` free multiline text. v0 `direct_prompt`/`override_prompt`/`custom_instructions` are deprecated in favour of `prompt` + `claude_args --append-system-prompt` |
| Tools/model | `claude_args: \|` with `--allowedTools`, `--disallowedTools`, `--model`, `--max-turns` (v0 `allowed_tools`/`model` inputs are gone) |
| @claude trigger | `trigger_phrase` (default `@claude`), plus `assignee_trigger`, `label_trigger` (default `claude`). **Supplying `prompt` switches to automation mode: it runs with no mention.** Two workflows can coexist |
| Untrusted actors | `allowed_bots` (default: none) and `allowed_non_write_users` (default: none) - leave both empty |

**Referencing `REVIEW.md` by path**: by instruction, not by input. The base tool set already includes file reads ("By default, Claude only has access to: File operations (reading, committing, editing files, read-only git commands)" - configuration.md), so `prompt: "Read REVIEW.md and follow it verbatim..."` works. There is no `prompt_file` input on v1; `@path` at-mention expansion inside `prompt` is UNVERIFIED, so write the explicit "Read `REVIEW.md`" sentence.

Two gotchas for T20: (a) "The base GitHub tools are always included. Use `--allowedTools` to add additional tools ... and `--disallowedTools` to prevent specific tools" - `--allowedTools` only *adds*, so a read-only review also needs `--disallowedTools "Edit,Write,MultiEdit,NotebookEdit"`. (b) On `pull_request` events the action restores `.claude/`, `.mcp.json`, `CLAUDE.md`, `CLAUDE.local.md`, `.gitmodules`, `.ripgreprc`, `.husky/` **from the base branch** (PR copies read-only under `.claude-pr/`); `REVIEW.md` is *not* on that list, so a PR can rewrite the file the reviewer follows - pin it with `git show "origin/$GITHUB_BASE_REF:REVIEW.md"`.

Minimum `permissions:` for a review-only job (README + solutions.md - verified):

```yaml
permissions:
  contents: read        # checkout and read the diff
  pull-requests: write  # post the review comments
  id-token: write       # required by the default GitHub App auth path (setup.md)
```
Add `actions: read` only alongside `additional_permissions: actions: read`. `issues: write` is not needed for PR-only review. Never `contents: write`.

### 2. Identity
- With the official [Claude GitHub app](https://github.com/apps/claude) installed and no `github_token` input, the action mints a short-lived App installation token (output `github_token` = "Claude App token if available") and posts as **`claude[bot]`** (`CLAUDE_BOT_LOGIN`, `CLAUDE_APP_BOT_ID = 41898282` in `src/github/constants.ts`; the `bot_name`/`bot_id` inputs reuse them for git authorship).
- Pass `github_token: ${{ secrets.GITHUB_TOKEN }}` and it posts as **`github-actions[bot]`**; a custom App posts as `<app>[bot]`; a PAT would post as that human - do not use one. All three are Bot accounts, so a PR *opened* by one carries `pull_request.user.type == 'Bot'` (UNVERIFIED for `claude[bot]`; `api.github.com` blocked).
- **Consequence for `sdlc-gate.yml` line 23**: by default the action **does not open PRs** ("Claude provides a link to the GitHub PR creation page ... the user must click the link"), so the author is `luissiviero` with `user.type == 'User'`. The `Bot` half of the guard rarely fires; `startsWith(github.head_ref, 'claude/')` carries the load and matches the action's default `branch_prefix: "claude/"`. Keep both; treat the branch prefix as primary.

### 3. Bot review vs "require 1 approval" (UNVERIFIED - docs.github.com blocked)
- The action posts comments and inline comments, not an `APPROVE` review event: assume it cannot approve.
- `github-actions[bot]` with the default `GITHUB_TOKEN` cannot submit approving reviews unless *Settings
  -> Actions -> General -> Workflow permissions -> "Allow GitHub Actions to create and approve pull
  requests"* is on ([#150278](https://github.com/orgs/community/discussions/150278)); there is no
  per-account exemption from an approval requirement ([#167357](https://github.com/orgs/community/discussions/167357)).
- With CODEOWNERS an approval from any one owner suffices, so a single code owner means one approval.
- "Require approval of the most recent reviewable push" = the last push must be approved by *someone
  other than the pusher* ([#109549](https://github.com/orgs/community/discussions/109549),
  [jessehouwing](https://jessehouwing.net/github-githubs-require-approval-of-the-most-recent-push-policy/));
  with one human it blocks every self-merge, hence off in the checklist.

### 4. Environment approval inside the job: **not observable** (UNVERIFIED - docs.github.com blocked)
No context or env var names the environment approver; the job simply does not start until a required reviewer approves ([#44139](https://github.com/orgs/community/discussions/44139), [#159342](https://github.com/orgs/community/discussions/159342)). The approver is retrievable only via `GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals` (`actions: read`); the fact of execution is the only in-job proof.

## Decision
1. **Identity: the official Claude GitHub App** - the review posts as `claude[bot]`, distinct from
   `luissiviero` (Q4: agents use a separate identity and can never self-approve). Auth by
   `anthropic_api_key` from repo secrets (Q7/Q8); no PAT, no custom App in phase 1, federation later.
2. **The bot never approves.** Its output is advisory findings in `REVIEW.md` format; approval stays a
   human act recorded in `work/<slug>/log.md` and `approved-by` (validated by T13).
3. **Single-human approval**: CODEOWNERS `* @luissiviero` + "Require review from Code Owners" + 1
   approval. The PR is opened by the owner, who cannot approve their own PR, so the documented escape
   hatch is **admin merge with "Do not allow bypassing" left off**, logged as a `log.md` entry naming
   the merge. With a second human: enable "require approval of the most recent reviewable push" and
   turn bypassing off.

## Branch-protection checklist (owner clicks these on `main`)
- [ ] Require a pull request before merging - **on**; required approving reviews **1**; dismiss stale
      approvals when new commits are pushed - **on**
- [ ] Require review from Code Owners - **on** (needs `.github/CODEOWNERS`, T07)
- [ ] Require approval of the most recent reviewable push - **off** while there is one human
- [ ] Require status checks: `sdlc-gate / artifact-chain`, `agent-evals`, later `pr-review`; require
      branches up to date - **on**; require conversation resolution - **on**
- [ ] Do not allow bypassing the above settings - **off** (the admin-merge escape hatch)
- [ ] Restrict who can push: `luissiviero` + the Claude App; block force pushes and deletions
- [ ] Settings -> Actions -> General: workflow token **read-only**; "Allow GitHub Actions to create and
      approve pull requests" **unchecked**
- [ ] Secrets: `ANTHROPIC_API_KEY` at repo scope with a spend limit (Q7)

## Consequences
- **T12** - the branch-prefix test is the real trigger; `SDLC_PR_AUTHOR_TYPE` stays advisory and must
  never be *required* to equal `Bot`, or the guard silently stops firing.
- **T20** - `permissions: {contents: read, pull-requests: write, id-token: write}`; prompt = read
  `REVIEW.md` from the base ref and run `/sdlc-review`; `claude_args` with **both** a narrow
  `--allowedTools` (`Bash(scripts/verify.sh)`, `Bash(python3 scripts/check_artifact_chain.py:*)`,
  `Bash(gh pr comment:*)`, `mcp__github_inline_comment__create_inline_comment`) and
  `--disallowedTools "Edit,Write,MultiEdit,NotebookEdit"`; `allowed_bots` empty; skip drafts.
  `check_workflow_permissions.py` also rejects `contents: write` and `pull_request_target`.
- **T19** - environment approval is invisible in-job, so keep `RELEASE_APPROVAL == HEAD` + `CI` as the
  assertion; optionally record the approver afterwards via `.../actions/runs/$GITHUB_RUN_ID/approvals`.

## Unverified items
1. `claude[bot]`-authored PRs report `pull_request.user.type == 'Bot'`.
2. `CLAUDE_APP_BOT_ID = 41898282` also being `github-actions[bot]`'s user id.
3. All GitHub branch-protection and environment-approval semantics (`docs.github.com` **blocked**; taken
   from community discussions) - re-verify from GitHub docs before T24 sign-off.
4. `@REVIEW.md` at-mention expansion inside the action's `prompt`.
5. Whether an approving review from a GitHub App bot counts toward the required-approval count.
