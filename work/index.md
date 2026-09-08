---
type: sdlc/index
title: Work items
description: Generated index of every work/<slug> item; run scripts/gen_index.py to refresh.
timestamp: 2026-09-08T15:20:00Z
---
# Work items

| slug | title | stage | intent | spec | plan | last gate |
|---|---|---|---|---|---|---|
| [_example](_example/index.md) | Example work item | plan | approved | approved | approved | plan.md -> approved by luissiviero |
| [adopter-first-hour](adopter-first-hour/index.md) | A fresh install of the kit breaks in the first hour; the adopter path must work end to end | plan | approved | approved | approved | PR #33 -> in-review by claude |
| [agent-evals](agent-evals/index.md) | Evals test the agent, and can go red | plan | approved | approved | approved | PR #34 -> in-review by claude |
| [approval-gate](approval-gate/index.md) | Only a human can flip an artifact to approved | plan | approved | approved | approved | PR #25 -> in-review by claude |
| [approve-by-dispatch](approve-by-dispatch/index.md) | Give permission for the AI to change from one mode to the other when I request, without doing everything manually | plan | approved | approved | delegated | plan.md -> delegated by claude |
| [band-detector](band-detector/index.md) | The band detector cannot see the breach it exists for | plan | approved | approved | approved | PR #31 -> in-review by claude |
| [bash-guard-hardening](bash-guard-hardening/index.md) | The Bash write guard silently allows deletes, glued commands, stderr redirects and two-step cd into the control plane | plan | approved | approved | approved | plan.md -> in-review by claude |
| [batch-b-followups](batch-b-followups/index.md) | Close the three leftovers Batch B surfaced | plan | approved | approved | approved | PR #39 -> in-review by claude |
| [control-plane-visibility](control-plane-visibility/index.md) | Hook decisions must be logged; the control-plane unlock must be visible; CI must recognise the kit's own agent PRs | plan | approved | approved | approved | plan.md -> in-review by claude |
| [delegated-mode](delegated-mode/index.md) | A second way to run a work item, where I approve the start and the AI signs the rest under its own name | plan | approved | approved | approved | PR #45 -> in-review by claude |
| [delegation-boundary](delegation-boundary/index.md) | Decide whether a subagent may ever write code in this kit | plan | approved | approved | approved | PR #36 -> in-review by claude |
| [deploy-gate](deploy-gate/index.md) | The deploy path fails open; every route to production must fail closed on a named human | plan | approved | approved | approved | PR #27 -> in-review by claude |
| [docs-reconcile](docs-reconcile/index.md) | The docs say what the code does | plan | approved | approved | approved | PR #37 -> in-review by claude |
| [front-matter](front-matter/index.md) | Templates and artifact parsers must agree; approve.py must not misfire | plan | approved | approved | approved | plan.md -> in-review by claude |
| [loop-protection](loop-protection/index.md) | The agent must not be able to weaken the check on its own work | plan | approved | approved | approved | plan.md -> in-review by claude |
| [retire-active-pointer](retire-active-pointer/index.md) | Retire `.sdlc/active` when a work item completes, so the plan gate stops opening on finished work | plan | approved | delegated | delegated | PR #53 -> in-review by claude |
| [sdlc-kit-phase-1](sdlc-kit-phase-1/index.md) | Make lifecycle-axis a reusable AI-native SDLC kit for Claude + Gemini projects | plan | superseded | superseded | superseded | plan.md -> superseded by luissiviero |
