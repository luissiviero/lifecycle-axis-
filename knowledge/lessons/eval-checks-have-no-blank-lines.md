---
type: lesson
title: An eval check block has no blank line, and an oracle must be shown to fail
description: "run_evals.sh's field() ends a `key: |` block at the first unindented line, and a blank line is unindented, so a blank inside a check silently truncates it into a stub that always passes. Prove every new oracle red before trusting it green."
tags: [lesson, evals, oracles, run-queue]
resource: ../../work/run-queue/
timestamp: 2026-09-08T18:00:00Z
---
# An eval check block has no blank line, and an oracle must be shown to fail

## What happened
`work/run-queue`'s eval `run-queue-stops-on-empty` was written with blank lines separating its
sections, the way a shell script normally reads. `scripts/run_evals.sh`'s `field()` ends a `key: |`
block at the first line that is not indented:

```awk
blk && /^[ \t]+/ {sub(/^[ \t]+/,""); print; next}
blk {exit}
```

A blank line is not indented, so extraction stopped there. Only the lines above the first blank ever
ran — a `mkdir` and some `printf`s — and the case reported `✔ pass` because the last surviving
command exited 0. Every assertion in the case was dead text. It was caught only by mutating
`next_item.py` on purpose and noticing the eval stayed green.

This is the second oracle in this repository written so that it could not fail. The first was
`work/approve-by-dispatch` R-10's `grep -c 'approve.yml' .claude/skills/*/SKILL.md`, which passes
today and which nothing in CI runs, found while reading the handoff for the next item. Two of the
same class is what rule 7 is for.

## Rule
No blank line inside a `check:` or `setup:` block — use an indented `# comment` line to separate
sections. Start a multi-line check with `set -e`, so every assertion counts rather than only the last
command. And before trusting a new oracle: **break the thing it watches and watch the oracle go red.**
A green oracle that has never been red is evidence of nothing.

## Where it is enforced
`scripts/test_run_evals.py::CaseBlocksAreWhole` scans every real case in `evals/cases/` and fails on a
`check:`/`setup:` block truncated by a blank line, so the trap cannot come back silently.
