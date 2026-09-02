# Evals

Continuous evaluation of the *agent workflow*, not just the code. Target 20–50 cases drawn from real recent tasks.
Every production incident adds one case here (see `/sdlc-incident`). Cases run in CI on every change to
CLAUDE.md, skills, hooks, agents, or the model/config, because those are the things that change agent behaviour.

Case format (`evals/cases/<name>.yaml`):
```yaml
name: hook-blocks-secret-write
kind: hook | skill | e2e
prompt: "…what the agent is asked to do…"        # for skill/e2e cases
check: "bash command that exits 0 on pass"         # deterministic oracle
source: incident id or PR that motivated the case
```
`scripts/run_evals.sh` is a placeholder runner that executes `check` only. Replace it with a runner that
drives your agent (`claude -p`, the Agent SDK, etc.) and then runs `check`.
