---
type: lesson
title: A skill or agent that names a template's field or heading spells it as the template does
description: "/sdlc-spec said standards-applied where the template says skills-applied, and /sdlc-plan plus both plan-reviewer agents said '## Files' and '## Verification' where the plan template says '## Files that change' and '## Proof'; the wrong spelling shipped into work/_example before anyone noticed."
tags: [lesson, skills, templates, evals]
resource: ../../evals/cases/skill-names-match-templates.yaml
timestamp: 2026-09-05T04:45:00Z
---
# A skill or agent that names a template's field or heading spells it as the template does

## What happened
`/sdlc-spec` said `standards-applied` where `templates/spec.md` says `skills-applied`; `/sdlc-plan` and both
`plan-reviewer` agents said `## Files` and `## Verification` where `templates/plan.md` says `## Files that change`
and `## Proof`. The wrong spelling shipped into `work/_example/spec.md` before anyone noticed, and the chain check
reads the plan by heading.

## Rule
When a template field or heading changes, grep `.claude/skills`, `.claude/agents` and `.gemini/agents` for the old
spelling in the same PR.

## Where it is enforced
Eval `skill-names-match-templates` pins the spellings; `scripts/run_evals.sh` runs it.
