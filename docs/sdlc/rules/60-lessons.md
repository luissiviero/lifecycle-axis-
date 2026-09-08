---
type: sdlc/rule-fragment
title: Lessons
description: One pointer line per lesson file in knowledge/lessons/, rendered into every context file so every model sees them.
targets: [claude, gemini, agents]
order: 60
tags: [rules, lessons, context-files]
timestamp: 2026-09-05T04:45:00Z
---
## Lessons (one file each in knowledge/lessons/)
A mistake made twice becomes a file there and a pointer line here, in the same PR; delete the pointer when a hook makes the mistake impossible.
- Rule 3 is advisory in this repo: the unlock logs control-plane writes, CI and the owner's review gate them — knowledge/lessons/control-plane-unlock-is-advisory.md
- A path guard compares one spelling; normalise first, never widen its input without a test — knowledge/lessons/one-path-spelling-in-guards.md
- Test a `_lib.sh` change from a second shell; a bad edit locks the session out of every tool — knowledge/lessons/test-lib-changes-from-a-second-shell.md
- Every `--check` folds CRLF before comparing; drift on a file nobody edited means line endings — knowledge/lessons/fold-crlf-before-comparing.md
- A skill or agent spells a template's field or heading exactly as the template does — knowledge/lessons/skills-spell-template-headings.md
- A plan bullet starts with the bare path, then ` — `; the empty deviation bullet is `- ` with a trailing space — knowledge/lessons/plan-bullets-start-with-the-path.md
- The ledger's from/to slot holds `status` values only; log the build gate on the PR — knowledge/lessons/ledger-slot-holds-status-only.md
- Send ledger lines to the owner in a fenced block, never as bullets; run `log_ledger.py` after the approval lands — knowledge/lessons/send-ledger-lines-in-a-fenced-block.md
- `git add` every new file before `verify.sh`: the front-matter check reads `git ls-files`, and a colon in an unquoted value is what it catches — knowledge/lessons/stage-new-files-before-verify.md
- A workflow's permissions block names every API surface its scripts touch, not only the one in mind when it was written — knowledge/lessons/workflow-permissions-name-every-api.md
- A fixture supplies its own identity and time; a test that reads the ambient environment passes here and fails on the runner — knowledge/lessons/tests-carry-their-own-environment.md
- No blank line in an eval `check:` block (it truncates the block into a stub that always passes); break what a new oracle watches and watch it go red — knowledge/lessons/eval-checks-have-no-blank-lines.md
