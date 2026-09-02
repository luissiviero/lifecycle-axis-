---
name: sdlc-incident
description: Maintain stage. Given a breached control band or a bug report, diagnose with evidence, write work/<slug>/incident.md, add a regression eval, and open the follow-up intent.md. Use for production anomalies, CI failures, and bug triage.
---
# /sdlc-incident — close the loop

1. Gather evidence first: logs, metrics, the breaching band from `monitoring/bands.yaml`, recent commits (`git log --since`), and the last deploy authorization.
2. Diagnose. State confidence. Propose the smallest safe action per the band tier: 1σ log only, 2σ diagnose and propose, 3σ propose rollback or fix for a human to authorize.
3. Write `work/<slug>/incident.md` from the template.
4. Add an eval case under `evals/cases/` that would have caught this. Mandatory; the incident is not closed without it.
5. Draft `work/<new-slug>/intent.md` for the durable fix and link it from the incident record. Do not implement it in the same session.
