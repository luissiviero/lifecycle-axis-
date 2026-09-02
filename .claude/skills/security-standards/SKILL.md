---
name: security-standards
description: Security policy applied as hard constraints during Design, Build, and Review. Load whenever writing a spec, a plan, or reviewing code that touches auth, data, secrets, inputs, or infrastructure.
---
# Security standards (policy as a skill)

These are requirements. A spec that cannot satisfy one must say so explicitly under "Not doing" with a human sign-off.

1. **Secrets** never appear in code, configs, tests, fixtures, or logs. Reference by name; load from the environment or the secret manager.
2. **Auth**: compare tokens with constant-time functions; sessions expire; every new endpoint states its authz rule in the spec.
3. **Input**: validate at the boundary with a schema; never build SQL/shell/HTML by string concatenation.
4. **Data**: classify new fields (public / internal / personal / regulated). Personal or regulated data requires an entry under `## Data and migrations` in spec.md and a named owner in plan.md.
5. **Dependencies**: adding one requires stating why in plan.md; pin versions; no post-install scripts from unknown publishers.
6. **Infra and migrations**: anything under `RELEASE_GATED_PATHS` is reviewed by a human. Migrations must be reversible or state why not.
7. **Logging**: no personal data in logs; errors carry a correlation id.
8. **Agent hygiene**: the agent that writes a change is not the one that approves it. Reviewer subagents are read-only.

Reviewer checklist: for each rule, cite `file:line` or write "n/a — <reason>".
