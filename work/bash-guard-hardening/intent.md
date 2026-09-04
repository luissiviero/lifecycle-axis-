---
type: sdlc/intent
id: bash-guard-hardening
title: The Bash write guard silently allows deletes, glued commands, stderr redirects and two-step cd into the control plane
description: bash_write_targets misses eleven command shapes that write to or remove protected paths, the hooks ignore the cwd field, and NotebookEdit bypasses every edit hook; harden within a stated bound and document the residuals.
stage: plan
status: in-review
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 adversarial run of the live hooks
approved-by:
approved-on:
supersedes:
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, bash-guard, control-plane, security, consensus-item-3]
timestamp: 2026-09-04T21:48:41Z
---
# Intent: the Bash write guard silently allows deletes, glued commands, stderr redirects and two-step cd into the control plane

## Problem
`protect-paths.sh`, `require-plan.sh` and `protect-tests.sh` all derive Bash write targets from
`bash_write_targets` in `.claude/hooks/_lib.sh:98-199`. It stops the heredoc and the plain `>`, but each
shape below returned rc 0 against the live hooks on 2026-09-04 (crafted hook JSON, unlock unset):
- Separators. `_lib.sh:114` splits on whitespace and `:120` recognises `;`, `&&`, `(`, `{` only as
  standalone tokens, so `true; cp /tmp/f .sdlc/config.env` (token `true;`), `true&&cp …` and a
  newline-separated `true\ncp …` never put `cp` in command position; `)` and `}` are in neither `:120`
  nor the argument-end scan at `:129`, so `( cp /tmp/f .sdlc/x )` and `{ cp /tmp/f .sdlc/x; }` report
  `)` or `}` as the destination, and `(cp /tmp/f .sdlc/x)` is one token.
- Truncation. `:104` deletes every `2>` and `&>` before looking for targets and the grep at `:108`
  excludes `|`, so `true 2> .sdlc/config.env`, `true &> .sdlc/config.env` and `echo x >|
  .sdlc/config.env` empty the file that defines `PROTECTED_PATHS`.
- Deletes, renames, metadata. No arm for `rm`, `unlink`, `rmdir`, `chmod`, `chown`, `chgrp`, `sort -o`
  (`rm -f .sdlc/active`, `rm -rf .claude/hooks` are the plain cases); `mv` (`:153-155`) reports only its
  destination, so `mv .sdlc/active /tmp/a` passes; `cp -t .claude/hooks /tmp/x.sh`, `install -t …` and
  `cp --target-directory=…` report the source; `sed --in-place` and `perl -pi -e` miss the `-i*` test at
  `:145`; the `git` arm (`:166-174`) knows only `checkout|restore` with `--`, so `git rm -q .sdlc/active`,
  `git mv` and `git restore .sdlc/config.env` pass.
- The ignored working directory. `_lib.sh:48-50` reads `tool_name`, `file_path`, `command` and never
  the input's top-level `cwd`, so `cwd=<root>/.sdlc` with `echo x > config.env` resolves against ROOT,
  as does `cwd=<root>/.claude` with `cd hooks && echo x > y.sh`; `"$PWD"/.sdlc/x` is dropped at `:195`.
- NotebookEdit. `:49` reads `file_path` only; NotebookEdit carries `notebook_path`, so `$FILE` and `$CMD`
  are empty and all four edit hooks exit 0 (`protect-paths.sh:35-40`); `block-secrets.sh:6` skips `new_source`.

`knowledge/decisions/bash-write-guard.md:99-102` documents `2>`/`&>` as ignored and `:104-119` the
tokeniser limits: a known gap grew wider than intended. Affected: every session of this repo (the unlock
makes rule 3 advisory here; adopters run the same hooks without it) and every `kind: fix` task, where a
test can be deleted instead of edited. Owner's decision: bounded hardening of the text heuristic, with
`bash -c`/`sh -c`/`eval`, other interpreters, archives, `xargs`, `find -exec`, variable paths and quoted
spaces as accepted residuals; the decision log, the trailer-aware CI check and the merge click stop intent.

## Proposed outcome
- Every command in the block list of the implementation plan's appendix A4 (30 shapes, verbatim in
  spec.md) returns rc 2 from `protect-paths.sh` naming the path; every command in its allow list (11
  shapes) returns rc 0. Today 29 of the 30 were reproduced returning 0 (the thirtieth follows).
- A Bash payload whose `cwd` is inside a protected directory is judged relative to it; `$PWD/` and
  `~/` prefixes resolve instead of being dropped. NotebookEdit takes the same `$FILE` branch as Edit;
  `block-secrets.sh` scans `new_source`. Under `kind: fix`, `rm`, `git rm`, `mv … /tmp/` and
  `perl -pi -e` on an existing test file are refused by `protect-tests.sh` like `sed -i` is today.
- `bash_write_targets` stays at or under 140 lines; existing hook tests pass unchanged; the decision
  record lists the residuals in one place. Tests grow by the two lists, the notebook cases and the
  delete/rename cases; two eval cases pin the runtime behaviour; `scripts/verify.sh` stays green.

## Affected users and systems
- Users: the owner and every Claude Code session in this repo; adopters running the copied hooks;
  any `kind: fix` task relying on the test lock.
- Services / repos / data: this repo only: `.claude/hooks/_lib.sh` (sourced by every hook), `protect-paths.sh`,
  `block-secrets.sh`, the hook tests under `scripts/`, one fixture, two eval cases, the decision record.

## Constraints
- Must: keep every verdict today's tests pin (`scripts/verify.sh 2>&1 | tail -3`, `ls > /tmp/out`,
  `cat .sdlc/config.env`, `echo "a > b"` allowed; the heredoc blocked); change `_lib.sh` in one Write,
  `bash -n` it, and run the hook test modules from a second shell before the session's next tool call
  (a bad edit locks Edit, Write and Bash at once); bash plus `sed`/`grep`/`jq` only, no shell parser.
- Must not: touch `.claude/settings.json` (the NotebookEdit matcher exists), the unlock semantics, the
  `BASH_WRITE_GUARD` switch or the `VERIFY:`/`CHAIN:`/`EVALS:` lines.
- Out of scope (accepted residuals, recorded in the decision log): `bash -c`, `sh -c`, `eval`;
  `node -e`, `ruby -e`, `python3 -c` beyond the `open(…,'w')` heuristic; `tar x`, `unzip`; `xargs`;
  `find -exec`; paths assembled from variables; quoted paths with spaces; variable `cd` targets;
  scripts written elsewhere and then run. The deploy gate, the approval gate and CI are other items.

## Risk class
low. Blast radius is this repo's hook layer and the adopters who copy it; a wrong pattern over-blocks
(one stderr line, a retry with the Write tool), never allows silently. The one real hazard is a syntax
error in `_lib.sh` locking the session, mitigated by the second-shell rule above. No data, no deploy path.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: `cp /tmp/x .claude/hooks/y.sh 2>/dev/null` passes today and after A4 as written (the last-argument
  rule takes the trailing redirection as the destination). Scan back over redirection tokens, or residual?
  A:
- Q: If the arms do not fit in 140 lines, drop `chgrp` then `rmdir` (rare) before `mv`/`rm` (common)?
  A:
