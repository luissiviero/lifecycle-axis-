---
type: doc
title: Author brief for chain artifacts
description: The brief given to the subagents that drafted Batch A intents, specs and plans.
tags: [sdlc, handoff, playbook-comparison]
timestamp: 2026-09-04T22:13:40Z
---

# Brief for chain-artifact authors (Batch A)

You are drafting SDLC chain artifacts for ONE work item of the approved implementation plan.

READ FIRST (all read-only):
- The approved plan: /root/.claude/plans/draft-a-implementation-plan-glimmering-ember.md  (your item's section + the appendix it references)
- Templates, copy their headings VERBATIM: /home/user/lifecycle-axis-/docs/sdlc/templates/intent.md, spec.md, plan.md
- Style example for an intent: /home/user/lifecycle-axis-/work/front-matter/intent.md
- Tone example for spec/plan (but NEVER copy its `**` globs): /home/user/lifecycle-axis-/work/sdlc-kit-phase-1/spec.md and plan.md
- The security skill, to be applied as hard constraints in the spec: /home/user/lifecycle-axis-/.claude/skills/security-standards/SKILL.md

HARD RULES
- Write ONLY under /tmp/claude-0/-home-user-lifecycle-axis-/2f1b2a2d-073a-5a84-a273-d7f99f7cbee7/scratchpad/batchA/<slug>/ . Never write, edit, git-commit, or checkout anything under /home/user/lifecycle-axis-. Read-only there.
- Before citing any file:line, open the file and confirm the line says what you claim. No invented paths, functions or line numbers. If the plan cites a line and the file disagrees, follow the file and note it under "Gotchas".
- Front matter: every key from the template, in the template's order; NO inline `# comments` on any front-matter line (they break the chain check today); `status: in-review`; `approved-by:` and `approved-on:` empty; `id: <slug>`; `timestamp:` = current UTC RFC3339 (run `date -u +%Y-%m-%dT%H:%M:%SZ`); `resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo`; `record:` empty; `tags:` a short list.
  - spec.md extra fields: `reads: intent.md`, `skills-applied: [security-standards]`, `skills-version: <output of: git -C /home/user/lifecycle-axis- log -1 --format=%h -- .claude/skills>`, `prompt: "Transcribed from the approved implementation plan (session above), section WI-N and appendix A-x, by a drafting subagent; reviewed by the orchestrator."`
  - plan.md extra fields: `kind: feature`, `reads: spec.md`, `risk-class: low` (or what the intent says).
- Headings: copy every `##`/`###` heading text from the template exactly (an eval pins the spellings). Fill every section; write "(none)" rather than deleting a section.
- spec.md `## Requirements` table: rows `R-1..R-n`, each mapping to an intent outcome and naming a MACHINE-CHECKABLE acceptance test (a test method name in a named `scripts/test_*.py`, an eval case file, or a command with its expected last line). `## Design` describes the change concretely with the code shapes from the plan's appendix where they exist (quote them). `## Areas of concern`: one bullet per real tension, format `- Cn: <concern> — policy: <which> — contradiction? yes/no — owner: luissiviero — resolution: <proposed>`. `## Gotchas found while reading the codebase`: things you verified in the files that the plan did not say.
- plan.md `## Files that change`: ONE explicit path per bullet, `- <path> — <why>`; new files marked "(new)"; regenerated files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `work/index.md`, `work/<slug>/index.md`) listed explicitly too. NO `**` or `*` globs. `## Proof`: map every R-row to its test/eval/command. `## Order of work`: numbered, each step independently verifiable, honoring the plan's landing-order constraints (e.g. `_lib.sh` changes tested from a second shell). `## Deviations log`: the heading with a single empty bullet `- `.
- Length: intent ≤ 90 lines, spec ≤ 170 lines, plan ≤ 90 lines. Prose, no em-dashes in prose (the templates use them in headings; that is fine).
- The repo's secrets hook scans everything you write, including scratchpad files: never write a credential-shaped literal (e.g. a quoted value after `password:`/`secret:`/`api_key:`, an `AKIA…` key, `sk-…`). Describe such test inputs in words instead.
- Final message: the list of files you wrote and any place where the file you read disagreed with the plan.
