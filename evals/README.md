# Evals

Continuous evaluation of the *agent workflow*, not just the code. Target 20–50 cases drawn from real recent tasks.
Every production incident adds one case here (see `/sdlc-incident`). Cases run in CI on every change to
CLAUDE.md, skills, hooks, agents, or the model/config, because those are the things that change agent behaviour.
**Every deterministic gate** — every hook and every `scripts/checks/*.sh` — ships at least one case here alongside
the code that implements it, in the same PR (see `chain-rejects-unknown-approver.yaml`,
`ci-control-plane-label-exempts.yaml`, `okf-warns-on-missing-type.yaml`, `plugin-manifest-lists-every-skill.yaml` for
the pattern per gate).

Case format (`evals/cases/<name>.yaml`):
```yaml
name: hook-blocks-secret-write
kind: hook | skill | e2e
prompt: "…what the agent is asked to do…"        # for skill/e2e cases
allowed_tools: "Read,Grep,Glob,Bash(scripts/verify.sh)"  # optional; this is the default
check: "bash command that exits 0 on pass"         # deterministic oracle
source: incident id or PR that motivated the case
```

## Running cases

`scripts/run_evals.sh` runs `hook` cases anywhere — they need no model, only the deterministic `check`. `skill` and
`e2e` cases carry a `prompt`: when `claude` and `ANTHROPIC_API_KEY` are both available it runs the prompt
non-interactively with `--allowedTools` (bounded to `allowed_tools`, default
`Read,Grep,Glob,Bash(scripts/verify.sh)`) before running `check`; without a key, prompt cases are skipped and
counted, not run. That is how CI drives this: `agent-evals.yml` sets `ANTHROPIC_API_KEY` so prompt cases run for
real there; locally, without the key, only hook cases execute and prompt cases show as skipped.

Selectors:
- `--only <glob>` — run only cases whose basename (without `.yaml`) matches `<glob>`.
- `--kind hook|skill|e2e` — run only cases of that kind. A kind matching no case is not an error.
- `--list` — print each selected case's name and kind, one per line, and exit 0 without running anything.
- an unknown flag prints usage to stderr and exits 2.

Last line: `EVALS: N pass, N fail, N skipped`; a non-zero exit means at least one case failed.
