---
type: lesson
title: The adopter's CLAUDE.md sits at exactly the cap, so every rules line is paid for there
description: "This repository's CLAUDE.md renders at ~108 of MAX_CONTEXT_LINES=120, but adopt.sh seeds an 11-line project header above the generated block, so an adopter's render sits at exactly 120; any line added to a rules fragment pushes it to 121 and test_adopt.py goes red twice with no mention of the cap."
tags: [lesson, context-files, adopt, rules-fragments]
resource: ../../work/run-queue/
timestamp: 2026-09-08T19:30:00Z
---
# The adopter's CLAUDE.md sits at exactly the cap

## What happened
Twice on one day, on consecutive items. `work/retire-active-pointer` added two lines to
`docs/sdlc/rules/00-chain.md`; `work/run-queue` added one pointer line to `60-lessons.md`. Both times
this repository's own `CLAUDE.md` rendered comfortably under the cap (108, 109) and `verify.sh` went red
anyway, in `test_adopt.py`, with two failures that never name the cap: `BEGIN GENERATED` missing from
the adopted `CLAUDE.md`, and `GEMINI.md` missing after adopt. The cause each time:
`scripts/adopt.sh` seeds an 11-line project header above the generated block, so the **adopter's**
render sits at exactly 120 of `MAX_CONTEXT_LINES=120`, and `gen_context_files.py` exits 1 writing
nothing when a render goes over — so the adopter gets no context files at all.

## Rule
A rules-fragment line is paid for at the adopter's render, not this repository's. Before adding one,
measure where it bites:

```
bash scripts/adopt.sh "$SCRATCH/adopt" >/dev/null 2>&1
python3 scripts/gen_context_files.py --root "$SCRATCH/adopt"   # must not say "over MAX_CONTEXT_LINES"
```

Pay for the line by re-flowing prose in a fragment (never a rule), or by deleting a lesson pointer
whose mistake a hook or test now makes impossible — which is what the lessons rule already says to do.

## Where it is enforced
`scripts/test_adopt.py::AdoptScript::test_adopts_expected_files_and_is_executable` and
`test_fresh_claude_md_has_project_sections` — indirectly, and without naming the cap; this lesson is
what turns those two failures into a five-second diagnosis.
