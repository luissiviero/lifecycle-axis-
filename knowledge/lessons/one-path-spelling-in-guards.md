---
type: lesson
title: A guard that compares paths must compare one spelling
description: "Three bypasses of protect-paths.sh came from Windows path forms the comparison did not recognise, and each made the hook allow silently; normalise through canon()/winpath() and never widen a guard's input without a test."
tags: [lesson, hooks, windows, paths]
resource: ../../work/bash-guard-hardening/
timestamp: 2026-09-05T04:45:00Z
---
# A guard that compares paths must compare one spelling

## What happened
Three separate bypasses came from a Windows path form the comparison did not recognise: `C:\...` read as a relative
path; a POSIX path under an MSYS mount such as `/tmp` left unconverted by `winpath()`. Each one made the hook *allow*
silently, which is the worst failure a guard can have. The third hid behind a test that could not run on Windows
until Developer Mode was enabled: a skipped guard test is not a passing one.

## Rule
Normalise every path through `canon()` / `winpath()` before comparing, and never widen a guard's input without a test
that runs on the platform the bypass came from.

## Where it is enforced
`scripts/test_protect_paths_bash.py`, `scripts/test_hooks_baseline.py`; the `_lib.sh` helpers
([bash-write-guard](../decisions/bash-write-guard.md)).
