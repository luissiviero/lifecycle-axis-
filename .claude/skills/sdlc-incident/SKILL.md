---
name: sdlc-incident
description: Maintain stage. Given a breached control band or a bug report, diagnose with evidence, write work/<slug>/incident.md, add a regression eval, and open the follow-up intent.md. Use for production anomalies, CI failures, and bug triage.
---
# /sdlc-incident — close the loop

1. Gather evidence first: logs, metrics, the breaching band from `monitoring/bands.yaml`, recent commits (`git log --since`), and the last deploy authorization.
2. Diagnose. State confidence. Propose the smallest safe action per the band tier in `monitoring/bands.yaml`: 1σ `log` only; 2σ `diagnose` read-only with the tier's `tools:`; 3σ `propose` along the metric's `routes:` (a PR, a runbook, a report) for a human to authorize.
3. Write `work/<slug>/incident.md` from the template. When the intent has `mode: delegated`, run
   `python3 scripts/sign.py <slug> incident.md` and continue; otherwise stop and wait for a human.
4. Write the lesson as `knowledge/lessons/<incident-slug>.md` (`type: lesson`, linked back to the incident record) and list it in `knowledge/lessons/index.md`; if it changes how the agent should behave, add a pointer line to `docs/sdlc/rules/60-lessons.md` in the same PR (rule 7).
5. Add an eval case under `evals/cases/` that would have caught this. Mandatory; the incident is not closed without it.
6. Draft `work/<new-slug>/intent.md` for the durable fix and link it from the incident record. Do not implement it in the same session.
