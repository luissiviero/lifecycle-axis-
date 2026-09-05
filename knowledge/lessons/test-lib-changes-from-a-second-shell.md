---
type: lesson
title: Test a _lib.sh change from a second shell before relying on it
description: "The hooks need jq and refuse every edit without it; a bad edit to .claude/hooks/_lib.sh locks the session that made it out of Edit, Write and Bash at once."
tags: [lesson, hooks, jq, recovery]
resource: ../decisions/gemini-hooks.md
timestamp: 2026-09-05T04:45:00Z
---
# Test a `_lib.sh` change from a second shell before relying on it

## What happened
Every hook sources `.claude/hooks/_lib.sh` and every hook needs `jq`; without it they fail closed and refuse every
edit ([gemini-hooks](../decisions/gemini-hooks.md)). A syntax error in `_lib.sh` has the same effect: the session
that made the edit loses Edit, Write and Bash in one stroke, and cannot repair the file it broke.

## Rule
Change `_lib.sh` only with a second shell open that can revert it, and run `bash -n` plus the hook tests from that
shell before the editing session depends on the new file.

## Where it is enforced
Prose only; `scripts/test_hooks_baseline.py` catches the breakage after the fact.
