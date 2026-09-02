---
name: sdlc-spec
description: Design stage. Read an approved intent.md, explore the codebase, apply the standards skills as hard constraints, and write work/<slug>/spec.md. Use after an intent is approved.
---
# /sdlc-spec — requirements and design in one pass

Precondition: `work/<slug>/intent.md` has `status: approved`. If not, stop and say so.

1. Read intent.md, CLAUDE.md, and the relevant code. Use the `explorer` subagent for broad code questions; it returns file paths and evidence.
2. Load every standards skill listed in `docs/sdlc/README.md` (at minimum `security-standards`). Treat their rules as requirements, not suggestions; list them in `standards-applied`.
3. Fill `docs/sdlc/templates/spec.md`. Every requirement row maps to an intent success criterion and names a machine-checkable acceptance test.
4. Record decisions as ADRs. Record gotchas you found in the code (they are the most valuable part).
5. Write with `status: in-review`. Summarize open design choices for the human in five lines or fewer. Do not approve.
