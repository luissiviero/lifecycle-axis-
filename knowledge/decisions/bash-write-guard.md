---
type: decision
title: Bash writes to protected paths are stopped by a hook heuristic and a CI job
description: protect-paths.sh inspects Bash command text for write targets under PROTECTED_PATHS because the edit hooks only matched Edit/Write/MultiEdit; the heuristic is deliberately over-inclusive, the CI control-plane job remains the gate against deliberate obfuscation, and a human-only environment variable unlocks the guard with an audit line.
tags: [hooks, control-plane, bash, security, sdlc]
timestamp: 2026-09-02T00:00:00Z
---

# Bash writes to protected paths are stopped by a hook heuristic and a CI job

## Context

Defect 4 in `work/sdlc-kit-phase-1/plan.md`: every PreToolUse edit hook in
`.claude/settings.json` was registered under the matcher `Edit|Write|MultiEdit`, and each one keys
off `.tool_input.file_path`. The `Bash` matcher held only `production-gate.sh`, which looks for
deploy and destructive commands and never at write targets.

So the entire enforcement layer had one door left open: a single `cat > .sdlc/config.env` heredoc
that sets `PROTECTED_PATHS=""` rewrites the file defining which paths are protected, and it passed
`protect-paths.sh`, `block-secrets.sh`, `require-plan.sh` and `protect-tests.sh` without any of
them being consulted — `file_path` is empty for a Bash call, and each hook exits 0 on empty. The
same hole covered `>>` appends into `.claude/hooks/_lib.sh`, `sed -i` on `.sdlc/active`,
`tee` into `.github/workflows/`, and `cp` into the hooks directory.

`MultiEdit` had a narrower version of the same problem in `block-secrets.sh`: it read
`.tool_input.content` and `.tool_input.new_string`, but a MultiEdit payload carries its text in
`.tool_input.edits[].new_string`, so a credential written through MultiEdit was never scanned.

## Decision

**Both a hook heuristic and a CI job — not either alone.**

1. `protect-paths.sh` gains a second branch, taken when `$FILE` is empty and `$CMD` is not, guarded
   by `BASH_WRITE_GUARD` in `.sdlc/config.env` (default `1`). A new function
   `bash_write_targets` extracts candidate write targets from the command text; each candidate
   is normalised with `rel()` and fed through the same `under_any "$PROTECTED_PATHS"` test and the
   same secret-filename `case` the `$FILE` branch uses. The `$FILE` branch itself is unchanged.
2. `block-secrets.sh` widens the text it scans to
   `[.tool_input.edits[]?.new_string] | join("\n")` and `.tool_input.command`, so MultiEdit
   payloads and Bash heredoc bodies go through the same credential patterns. Exit codes are
   unchanged.
3. `.claude/settings.json` registers `protect-paths.sh` then `block-secrets.sh` then
   `production-gate.sh` on the `Bash` matcher.
4. A human-only unlock: if `SDLC_CONTROL_PLANE_UNLOCK=1` is set in the environment, the Bash branch
   prints `SDLC: control plane unlocked by human env (SDLC_CONTROL_PLANE_UNLOCK=1)` to stderr and
   allows the command.

## Why both, and why a heuristic is acceptable here

- **The CI job never fires for the case that matters most.** `scripts/check_control_plane.sh`
  blocks an agent-authored diff only when it can tell the author is an agent —
  `SDLC_PR_AUTHOR_TYPE == 'Bot'` or a `claude/*` head ref. In this kit the agent runs *as the
  owner*, on a `work/<slug>` branch, under the owner's identity (decision 4). For that PR the
  control-plane job takes the human-authored path and passes. The hook is the only thing standing
  between an agent and `.sdlc/config.env` in the session where the edit happens.
- **A hook alone is not enough either.** The heuristic reads shell text; shell text can always be
  obfuscated (a path assembled from two variables, base64, a helper script written elsewhere and
  then executed). Nothing pattern-based defeats an agent that is *trying* to get through. The hook
  stops the accident and the shortcut; CI plus branch protection plus CODEOWNERS remain the gate
  against intent, because they inspect the resulting diff rather than the command that produced it.
- **False positives are nearly free.** A wrong block costs one line on stderr and a retry with the
  Write tool. It never prompts a human, never fails a build, never blocks a merge. A false
  negative costs the control plane. The heuristic is therefore tuned to over-match: candidates that
  are not paths at all (a `sed` script, a `tee` operand) are simply tested against the protected
  prefixes and discarded.
- **The unlock is auditable and cannot be self-granted.** `SDLC_CONTROL_PLANE_UNLOCK` is read from
  the hook process's own environment, which is inherited from the process that launched Claude
  Code. A command the agent runs sets variables in *its own* shell, not in the hook's, so an agent
  cannot turn the guard off from inside a session. Every allow prints the audit line above to
  stderr, where it appears in the transcript, so a session that ran with the unlock is visible in
  review. `BASH_WRITE_GUARD=0` is the other off switch, and it lives in `.sdlc/config.env` — a
  protected path, so only a human can set it.

## What is covered

`bash_write_targets` (truncating the command at 16 KB first) yields candidates from:

| Pattern | Example |
|---|---|
| `>` / `>>` redirection targets | `cat > .sdlc/config.env`, `echo x >> .claude/hooks/_lib.sh` |
| heredoc writes | covered by the redirection target, which precedes `<<` |
| `tee [-a] <paths…>` up to the next `\|`, `;`, `&&` | `tee -a .github/workflows/sdlc-gate.yml` |
| `dd of=<path>` | `dd if=/tmp/x of=.sdlc/active` |
| `sed -i*` / `perl -i*` file arguments | `sed -i s/a/b/ .sdlc/active` |
| `cp` / `mv` / `install` / `rsync` last argument | `cp /tmp/x .claude/hooks/y.sh` |
| `truncate … <path>` | `truncate -s 0 .sdlc/active` |
| `git checkout <ref> -- <path>` (and `git restore`) | `git checkout HEAD~1 -- .sdlc/config.env` |
| `patch`, `git apply`, `git am` | any protected prefix named anywhere in the command |
| `python… -c`, `python… -`, `node …` with an inline script or heredoc | any protected prefix named in the command, plus `open(<path>, 'w'` or `'a')` targets |

Explicitly *not* treated as write targets: `>&`, `2>`, `&>` (descriptor redirection, so
`cmd 2>&1` and `scripts/verify.sh 2>&1 | tail` stay clean), anything under `/dev/`, and targets
that start with `$` or contain a `${` expansion (a variable target cannot be resolved without
executing the command, and guessing would produce noisy blocks on ordinary scripts).

## What is not covered

- **Obfuscation.** Variable-assembled paths, `eval`, base64, and a write performed by a script the
  agent wrote somewhere unprotected and then ran. By design: see above — CI and branch protection
  are the answer, not a longer regex.
- **Nested interpreters.** `bash -c` strings and `xargs` are tokenised as ordinary text; a write
  target inside them is caught only if it appears as a plain `>` redirection or names a protected
  prefix next to `patch` or an inline `python` script.
- **Word-splitting fidelity.** The tokeniser splits on whitespace with globbing disabled; it is not
  a shell parser. `echo "a > b"` offers `b` as a candidate (harmless), and two commands joined by a
  pipe with no surrounding spaces form one token, so a command-position rule such as `tee` may be
  missed there.
- **The other three edit hooks.** `require-plan.sh` and `protect-tests.sh` are still registered on
  `Edit|Write|MultiEdit` only. A Bash write to `src/` therefore does not require an approved plan.
  That is a smaller hole than the control-plane one closed here (CI's chain check compares the PR
  diff against `plan.md` regardless of which tool produced it) and is left for a follow-up.

## Consequences

- `scripts/test_protect_paths_bash.py` pins seven blocked and six allowed commands, both off
  switches, and the MultiEdit/heredoc surface of `block-secrets.sh`.
  `evals/cases/hook-blocks-bash-write-to-protected-path.yaml` and
  `evals/cases/hook-blocks-multiedit-secret.yaml` are the runtime oracles.
- Ordinary agent work pays one extra `grep -Eo` per Bash call, on top of the three `jq` calls
  `_lib.sh` already makes.
- This was the last control-plane edit of the phase, because it is the change that closes the
  path used to make it (see "Two constraints on execution" in `work/sdlc-kit-phase-1/plan.md`).
