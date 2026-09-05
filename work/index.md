---
type: sdlc/index
title: Work items
description: Generated index of every work/<slug> item; run scripts/gen_index.py to refresh.
timestamp: 2026-09-04T21:53:54Z
---
# Work items

| slug | title | stage | intent | spec | plan | last gate |
|---|---|---|---|---|---|---|
| [_example](_example/index.md) | Example work item | plan | approved | approved | approved | plan.md -> approved by luissiviero |
| [approval-gate](approval-gate/index.md) | Only a human can flip an artifact to approved | plan | in-review | in-review | in-review | plan.md -> in-review by claude |
| [bash-guard-hardening](bash-guard-hardening/index.md) | The Bash write guard silently allows deletes, glued commands, stderr redirects and two-step cd into the control plane | plan | approved | approved | approved | plan.md -> in-review by claude |
| [control-plane-visibility](control-plane-visibility/index.md) | Hook decisions must be logged; the control-plane unlock must be visible; CI must recognise the kit's own agent PRs | plan | approved | approved | approved | plan.md -> in-review by claude |
| [delegation-boundary](delegation-boundary/index.md) | Decide whether a subagent may ever write code in this kit | intent | draft | — | — | intent.md -> draft by claude[bot] |
| [deploy-gate](deploy-gate/index.md) | The deploy path fails open; every route to production must fail closed on a named human | plan | approved | approved | approved | PR #27 -> in-review by claude |
| [front-matter](front-matter/index.md) | Templates and artifact parsers must agree; approve.py must not misfire | plan | approved | approved | approved | plan.md -> in-review by claude |
| [loop-protection](loop-protection/index.md) | The agent must not be able to weaken the check on its own work | plan | approved | approved | approved | plan.md -> in-review by claude |
| [sdlc-kit-phase-1](sdlc-kit-phase-1/index.md) | Make lifecycle-axis a reusable AI-native SDLC kit for Claude + Gemini projects | plan | approved | approved | approved | plan.md -> approved by luissiviero |
