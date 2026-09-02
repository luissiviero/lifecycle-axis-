---
name: sdlc-intent
description: Plan stage. Interview the originator and write work/<slug>/intent.md from the template. Use when someone describes a problem, feature, or incident that has no intent.md yet.
---
# /sdlc-intent — capture intent

You are producing the first link in the artifact chain. Do not design or plan yet.

1. Ask for a slug (kebab-case) if not given. Create `work/<slug>/` and copy `docs/sdlc/templates/intent.md`.
2. Interview the originator in their own words. Ask until you can fill every section without inventing:
   problem, who is affected, how we would observe success, hard constraints, what is explicitly out of scope, risk class.
   Ask at most three questions per turn. Record unanswered ones under "Open questions".
3. Quote the originator where possible; do not paraphrase intent into solution language.
4. Write the file with `status: in-review`. Print the path and the open questions.
5. Stop. A human sets `status: approved` and `approved-by`. Never set them yourself.

Done means: every success criterion is observable and has a number or a test attached.
