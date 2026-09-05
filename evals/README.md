# Evals

Continuous evaluation of the *agent workflow*, not just the code. Target 20–50 cases drawn from real recent tasks.
Every production incident adds one case here (see `/sdlc-incident`). Cases run in CI on every change to
CLAUDE.md, its rule and template sources, skills, hooks, agents, evals or the control plane, and nightly.

## Two kinds of case, one runner

- **Gate tests** (`hook-*`, `gate-*`, `chain-*`, `ci-*`, `okf-*`, `index-*`, `plugin-*`, `review-*`, `adopt-*`,
  `bands-*`, `deploy-*`, `skill-names-*`): deterministic checks of a hook, a `scripts/checks/*.sh`, or a CI
  script. No model. **Every deterministic gate ships at least one** alongside the code that implements it, in the
  same PR (see `chain-rejects-unknown-approver.yaml`, `ci-control-plane-label-exempts.yaml`,
  `okf-warns-on-missing-type.yaml`, `plugin-manifest-lists-every-skill.yaml` for the pattern per gate).
- **Evals proper** (`skill-*`, `e2e-*`, and `hook-refuses-planted-key`, which is `kind: skill` despite its prefix
  because it meets a hook through the agent): the playbook's evals. A `prompt` drives `claude -p` with bounded
  tools, then a deterministic `check` reads what the agent left behind. These are the cases an adopter grows to
  20–50 from real tasks. Today: `skill-intent-does-not-self-approve`, `skill-spec-flags-concerns`,
  `skill-plan-names-files-and-proof`, `skill-fix-leaves-tests-alone`, `hook-refuses-planted-key`,
  `skill-incident-names-an-eval`.

Case format (`evals/cases/<name>.yaml`):
```yaml
name: hook-blocks-secret-write
kind: hook | skill | e2e
prompt: "…what the agent is asked to do…"        # for skill/e2e cases
allowed_tools: "Read,Grep,Glob,Bash(scripts/verify.sh)"  # optional; this is the default
setup: |                                           # optional; stages a fixture before the prompt
  …bash…
check: "bash command that exits 0 on pass"         # deterministic oracle
source: incident id or PR that motivated the case
```

A prompt case works in a temporary slug (`work/eval-<name>/`) that its `check` removes whatever the outcome, so
nothing it writes is ever committed. `setup:` runs before the prompt (and before `check` for a case without one);
a failing setup fails the case with its output. Assertions are structural (a heading, a field, a path that exists,
a checksum), never wording.

## Writing a check that can fail

Under `set -e`, a negated command (`! cmd`) never triggers errexit: when `cmd` unexpectedly succeeds, the line's
failure is ignored and the case passes. End every such assertion that is not the block's last command with
`|| exit 1`:

```bash
! printf '%s' "$P" | .claude/hooks/protect-paths.sh 2>/dev/null || exit 1
```

`scripts/check_eval_cases.py` (run by `scripts/verify.sh` through `scripts/checks/eval-cases.sh`) refuses a case
that reintroduces the bare form, names the file and line, and also refuses an unknown `kind` or a case with neither
`check` nor `prompt`.

## Running cases

`scripts/run_evals.sh` runs `hook` cases anywhere — they need no model, only the deterministic `check`. `skill` and
`e2e` cases carry a `prompt`: when `claude` and a credential (`ANTHROPIC_API_KEY`, or `CLAUDE_CODE_OAUTH_TOKEN`
from `claude setup-token` on a Pro/Max plan) are both available it runs the prompt
non-interactively with `--allowedTools` (bounded to `allowed_tools`, default
`Read,Grep,Glob,Bash(scripts/verify.sh)`) before running `check`; without a key, prompt cases are skipped and
counted, not run. With `--require-claude` a skipped prompt case counts as a **failure**; that is how the nightly
`agent-evals` job runs, so an expired credential is a red run, never a green one that tested nothing.

Prompt cases run **nightly only**, on the default branch, in the one job that holds the credential
(`.github/workflows/agent-evals.yml`, `full-suite`; also startable by hand from the Actions tab). The PR-time job
runs `--kind hook` with no secret, because eval cases are shell executed from the PR head. The nightly job trusts
the checkout (`~/.claude.json`, `hasTrustDialogAccepted`) so the project's hooks and permissions apply to `claude -p`.

Selectors:
- `--only <glob>` — run only cases whose basename (without `.yaml`) matches `<glob>`.
- `--kind hook|skill|e2e` — run only cases of that kind. A kind matching no case is not an error.
- `--list` — print each selected case's name and kind, one per line, and exit 0 without running anything.
- `--require-claude` — a prompt case that cannot run counts as a failure.
- an unknown flag prints usage to stderr and exits 2.

Last line: `EVALS: N pass, N fail, N skipped`; a non-zero exit means at least one case failed.
