---
type: lesson
title: Stage new files before running verify, or the front-matter check never sees them
description: "scripts/check_front_matter.py reads git ls-files, so a new file that is not yet staged is skipped locally and first checked in CI; twice in one pull request a new file with an unquoted colon in its front matter passed locally and turned CI red."
tags: [lesson, verify, front-matter, yaml, generators]
resource: ../../scripts/check_front_matter.py
timestamp: 2026-09-05T12:10:00Z
---
# Stage new files before running verify, or the front-matter check never sees them

## What happened
`scripts/check_front_matter.py` lists the files it checks with `git ls-files`, so an untracked file is
invisible to it. In `work/delegated-mode`, pull request 42 went red twice on the same shape of defect
in two new files: `work/delegated-mode/index.md` (generated, the intent's description holding `: `)
and `docs/sdlc/templates/revision.md` (a `trigger:` placeholder holding `: `). Both times
`scripts/verify.sh` was green locally because the file had not been `git add`ed yet, and the local
run happened before the commit that made it tracked. CI checks out the commit, so it saw both.

## The rule
- Run `git add` on every new file, then `scripts/verify.sh`, then commit. The verify line pasted in the
  pull request must come from a run that saw every file the commit carries.
- A front-matter value that holds `: `, ` #`, or starts with a YAML indicator is quoted. Generators
  quote for you (`gen_index.py`'s `_yaml_scalar`); templates and hand-written docs do not, so a
  placeholder such as `<a: b>` needs quotes too.
- A new file that CI fails on and the local run passed on means the local run did not see it, not
  that CI is flaky.
