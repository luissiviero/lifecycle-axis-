---
type: lesson
title: A drift check that compares bytes is wrong on a Windows checkout
description: "core.autocrlf hands back CRLF while the generators write LF, so two --check modes reported drift on a clean tree; every --check folds CRLF to LF before comparing, and .gitattributes now keeps text types LF."
tags: [lesson, windows, crlf, generators]
resource: ../../scripts/gen_context_files.py
timestamp: 2026-09-05T04:45:00Z
---
# A drift check that compares bytes is wrong on a Windows checkout

## What happened
`core.autocrlf` hands back CRLF while `gen_context_files.py` and `gen_index.py` write LF, so first
`gen_context_files.py --check` and then `gen_index.py --check` each reported drift on a clean tree until CRLF was
normalised before comparing. A drift report on a file nobody edited is the first thing to suspect.

## Rule
Any new `--check` compares with `\r\n` folded to `\n`. `.gitattributes` forces `text eol=lf` on `*.sh`, `*.md`,
`*.py`, `*.yml` and `*.yaml` (`work/docs-reconcile`), so the generated files stay LF on every checkout.

## Where it is enforced
`.gitattributes`; the `--check` paths of both generators; `scripts/check_front_matter.py` folds too.
