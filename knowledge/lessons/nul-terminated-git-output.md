---
type: lesson
title: A text delimiter a filename can contain is not a delimiter; ask git for NUL-terminated output
description: "Twice in one item the committer's porcelain parser split on the rename arrow ` -> ` and mis-read a path: first a plain untracked file whose name held the arrow became two phantom paths, then a renamed source whose name held it was cut at the wrong arrow and git add exited 128. git status --porcelain -z ends every field with a byte no filename can contain, quotes nothing, and reports a rename as two fields."
tags: [lesson, git, porcelain, parsing, approve-dispatch]
resource: ../../scripts/approve_dispatch.py
timestamp: 2026-09-14T04:00:00Z
---
# A text delimiter a filename can contain is not a delimiter

## What happened
`scripts/approve_dispatch.py`'s `changed_paths` read `git status --porcelain` line by line and split a
rename entry on the first ` -> `. The second review round of `work/approve-tap-regenerates-index` found
that a plain untracked file named `work/demo/spec.md -> work/demo/plan.md` was parsed as a rename of two
phantom paths, so the real stray was never named and `git add` died on a path that did not exist. The
fix required a rename or copy status code before splitting. The automated review on pull request 83 then
found the other half: a tracked file named `a -> b` renamed onto an allowed path was split at the wrong
arrow, `old="a"`, `new="b -> work/index.md"`, and `git add` exited 128 again. Both were fail-safe and both
were the same mistake: a delimiter chosen from the data's own alphabet. The line-oriented format also
quotes and escapes paths with spaces or non-ASCII, which the parser stripped by hand, a second place to
be wrong.

## Rule
When parsing tool output that carries filenames, never split on a text sequence a filename may contain,
and never unquote by hand. Ask for the tool's NUL-terminated mode (`git status --porcelain -z`,
`git diff --name-only -z`, `find -print0`, `xargs -0`): every field ends with a byte no filename can
contain, nothing is quoted or escaped, and a rename is two fields, destination then source. Pin the
parser with a filename that contains the delimiter you are no longer splitting on.

## Where it is enforced
`scripts/approve_dispatch.py`, `changed_paths`, reads `--porcelain -z`; `scripts/test_approve_dispatch.py`,
`test_index_lookalikes_are_stray`, pins both cases (the plain file and the renamed source). Nothing
enforces it for new code yet; a check that greps for `--porcelain` without `-z` would.
