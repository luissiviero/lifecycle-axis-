---
type: sdlc/spec
id: bash-guard-hardening
title: Bounded hardening of bash_write_targets, cwd-aware candidates, NotebookEdit coverage
description: Requirements and design for closing the verified silent-allow shapes of the Bash write guard within a 140-line bound, reading the hook input's cwd, covering NotebookEdit, and recording the accepted residuals.
stage: design
status: approved
reads: intent.md
approved-by: luissiviero
approved-on: 2026-09-05
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Transcribed from the approved implementation plan (session above), section WI-4 and appendix A4, by a drafting subagent; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, bash-guard, control-plane, security, consensus-item-3]
timestamp: 2026-09-04T21:48:41Z
---
# Spec: bounded hardening of bash_write_targets, cwd-aware candidates, NotebookEdit coverage

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) the A4 block list is blocked and the allow list allowed; (2) `cwd`, `$PWD/` and
`~/` resolve; (3) NotebookEdit is covered; (4) delete/rename refused under `kind: fix`; (5) 140-line
bound, existing tests unchanged, residuals documented; (6) tests and evals grow, verify green.
All new tests drive the hooks through `scripts/hooktest.py` like the modules they extend.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `2> X`, `&> X`, `>| X` are write targets; `N>&M`, `>&N`, `/dev/null` are not | 1 | `scripts/test_protect_paths_bash.py`: `test_blocks_stderr_redirect_into_sdlc_config`, `test_blocks_ampersand_redirect_into_sdlc_config`, `test_blocks_clobber_redirect_into_sdlc_config`; `test_allows_devnull_with_descriptor_dup`, `test_allows_stderr_to_devnull`, `test_allows_pipe_into_tee_outside_repo` |
| R-2 | Commands after a newline, a glued `;` or `&&`, or inside `( )` / `{ }` are seen in command position | 1 | same module: `test_blocks_semicolon_glued_cp`, `test_blocks_newline_separated_cp`, `test_blocks_and_glued_cp`, `test_blocks_subshell_cp`, `test_blocks_brace_group_cp`, `test_blocks_subshell_without_spaces` |
| R-3 | `rm`, `unlink`, `rmdir`, `chmod`, `chown`, `chgrp` report every non-option operand | 1 | same module: `test_blocks_rm_of_sdlc_active`, `test_blocks_rm_rf_of_hooks_dir`, `test_blocks_unlink_of_sdlc_active`, `test_blocks_rmdir_under_sdlc`, `test_blocks_chmod_on_hook`, `test_blocks_chown_on_config`; `test_allows_rm_outside_repo`, `test_allows_chmod_outside_repo` |
| R-4 | `mv` reports source and destination; `cp`/`install`/`rsync` report `-t DIR` and `--target-directory`; `sort -o` reports its output | 1 | same module: `test_blocks_mv_out_of_sdlc`, `test_blocks_cp_target_directory_flag`, `test_blocks_install_target_directory_flag`, `test_blocks_cp_long_target_directory_option`, `test_blocks_sort_output_into_config`; `test_allows_mv_outside_repo`, `test_allows_sort_read_of_config` |
| R-5 | `sed --in-place`, `perl -pi`, `perl -0pi.bak` count as in-place | 1 | same module: `test_blocks_sed_long_in_place`, `test_blocks_perl_pi`, `test_blocks_perl_bundled_pi_with_suffix` |
| R-6 | `git rm|mv|clean|checkout|restore` report every non-option operand, `--` optional | 1 | same module: `test_blocks_git_rm`, `test_blocks_git_mv`, `test_blocks_git_restore_without_double_dash`; `test_allows_git_checkout_new_branch`, `test_allows_git_rm_cached_outside_repo` |
| R-7 | Candidates resolve against the payload's `cwd`, `$PWD/` and `~/` expand, `cd` targets resolve from `cwd` | 2 | same module (`bash()` gains `cwd=`): `test_blocks_pwd_prefixed_redirect`, `test_blocks_relative_write_when_cwd_is_sdlc`, `test_blocks_cd_from_cwd_into_hooks`; `test_allows_relative_write_when_cwd_is_tmp` |
| R-8 | NotebookEdit `notebook_path` takes the `$FILE` branch; `new_source` is scanned for credentials | 3 | `scripts/test_hooks_baseline.py::ProtectPathsHook.test_blocks_notebook_under_sdlc`; `scripts/test_protect_paths_bash.py::BlockSecretsWiderSurface.test_blocks_key_in_notebook_new_source`; fixture `scripts/fixtures/hook_inputs/notebookedit.json` |
| R-9 | Under `kind: fix`, deleting or renaming an existing test file through Bash is refused | 4 | `scripts/test_bash_plan_gates.py::ProtectTestsBashBranch`: `test_blocks_rm_of_test_file_during_fix`, `test_blocks_git_rm_of_test_file_during_fix`, `test_blocks_mv_of_test_file_to_tmp_during_fix`, `test_blocks_perl_pi_on_test_file_during_fix` |
| R-10 | Runtime oracles for the new shapes | 6 | `scripts/run_evals.sh --only 'hook-blocks-*'` ends `0 fail`; new `evals/cases/hook-blocks-delete-and-glued-writes.yaml`; `hook-blocks-bash-write-to-protected-path.yaml` gains the newline form |
| R-11 | `bash_write_targets` at or under 140 lines; every existing hook test passes unchanged | 5 | `awk '/^bash_write_targets\(\) \{/,/^\}/' .claude/hooks/_lib.sh | wc -l` prints at most 140; `python3 scripts/run_tests.py` ends `OK` |
| R-12 | Decision record names the residuals; verify green | 5, 6 | `grep -c '^## Accepted residuals' knowledge/decisions/bash-write-guard.md` prints 1; `python3 scripts/check_okf.py` ends `0 warnings`; `scripts/verify.sh` ends `VERIFY: PASS (<sha>)` |

## Design
### Architecture / data flow
Unchanged: a hook reads one JSON object, `_lib.sh` extracts fields, `bash_write_targets` turns the
command text into candidate paths, `bash_write_candidates` canonicalises each against ROOT and every
`cd` target, and the calling hook applies its own prefix test. This item changes the extraction
(steps 1, 2 and 4 of `bash_write_targets`, `_lib.sh:102-108`, `:114`, `:120`, `:129`, `:191-198`),
adds one input field (`cwd`) and one base for canonicalisation, and widens the `$FILE` field. The
`$FILE` branch of every hook, the unlock, `BASH_WRITE_GUARD` and the exit-code contract stay as they are.

### Interfaces (APIs, events, schemas) — exact shapes
`_lib.sh:49` becomes `FILE="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')"`
and a new line reads `CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty')"`. After `canon` is defined:
`CWD_CANON="$([ -n "$CWD" ] && canon "$CWD")"` and `rel() { canon "$1" "${CWD_CANON:-}"; }`.
`protect-paths.sh:36` switches `canon "$FILE"` to `rel "$FILE"`, as `require-plan.sh:24` and
`protect-tests.sh:64` already do. `block-secrets.sh:6` appends `+ "\n" + (.tool_input.new_source // "")`.

Step 1, redirections (replaces `_lib.sh:102-108`), quoted from A4:
```bash
  s="$(printf '%s' "$cmd" | sed -E 's/[0-9]*>&[0-9-]+//g; s/[0-9]*<&[0-9-]+//g; s/>&/\&>/g')"
  while IFS= read -r t; do
    t="${t#*>}"; t="${t#[>|]}"; t="${t#"${t%%[![:space:]]*}"}"; out+=("$t")
  done < <(printf '%s' "$s" | grep -Eo '(&|[0-9])?>(>|\|)?[[:space:]]*[^[:space:]|;&<>()]+')
```
Step 2, pre-split (replaces `:114`; `)` and `}` join the separator list at `:120` and the argument-end
scan at `:129`, see gotcha G2), quoted from A4:
```bash
  s="${cmd//$'\n'/ ; }"; s="${s//;/ ; }"; s="${s//&&/ && }"
  s="${s//(/ ( }"; s="${s//)/ ) }"; s="${s//\{/ { }"; s="${s//\}/ } }"
  s="${s//|/ | }"; s="${s// |  | / || }"
  case "$-" in *f*) noglob=1;; *) set -f;; esac
  # shellcheck disable=SC2206
  toks=( $s )
```
Gotcha G3 narrows the brace lines: split only a `{` that is followed by a blank and a `}` that follows
`;` (already isolated by the `;` split), so `${VAR}` stays one token.
New arms (the skip class becomes `-*|'<'*|'>'*|'&'*`), quoted from A4; they replace the `sed|perl`,
`cp|mv|install|rsync` and `git` arms at `:142-155` and `:166-174`:
```bash
      rm|unlink|rmdir|chmod|chown|chgrp)  for ((j=i+1; j<e; j++)); do case "${toks[j]}" in -*|'<'*|'>'*|'&'*) continue;; esac; out+=("${toks[j]}"); done ;;
      mv)                                 for ((j=i+1; j<e; j++)); do case "${toks[j]}" in -*|'<'*|'>'*|'&'*) continue;; esac; out+=("${toks[j]}"); done ;;
      cp|install|rsync)                   q="${toks[e-1]}"; case "$q" in -*|'<'*|'>'*|'&'*) ;; *) out+=("$q");; esac
        for ((j=i+1; j<e; j++)); do case "${toks[j]}" in
            -t|--target-directory) [ $((j+1)) -lt "$e" ] && out+=("${toks[j+1]}");;
            --target-directory=*) out+=("${toks[j]#--target-directory=}");;
            -t?*) out+=("${toks[j]#-t}");; esac; done ;;
      sort)                               for ((j=i+1; j<e; j++)); do case "${toks[j]}" in
            -o) [ $((j+1)) -lt "$e" ] && out+=("${toks[j+1]}");; -o?*) out+=("${toks[j]#-o}");; --output=*) out+=("${toks[j]#--output=}");; esac; done ;;
      sed|perl)                           k=0; for ((j=i+1; j<e; j++)); do case "${toks[j]}" in -[!-]*i*|--in-place*) k=1;; esac; done
                                          # then the existing "every non-option argument" loop when k=1
      git)                                case "${toks[i+1]}" in rm|mv|clean|checkout|restore)
                                            for ((j=i+2; j<e; j++)); do case "${toks[j]}" in -*) continue;; esac; out+=("${toks[j]}"); done ;; esac ;;
```
Step 4 (replaces `:191-198`): strip all quotes (every `"` and `'`, not only a leading and trailing
one); rewrite a leading `$PWD/` to the expanded value of `${CWD:-$ROOT}/` and a leading `~/` to the
expanded value of `$HOME/` (gotcha G4); then the existing `''|/dev/*|\$*|*'${'*` drop.

`bash_write_candidates` (`:204-219`): `base="$(canon "$CWD")"` when `CWD` is set; each candidate is
resolved against `base`, against ROOT as before, and against each `cd`/`pushd` target itself resolved
from `base` (`canon "$cand" "$(canon "$d" "$base")"`). A payload without `cwd` behaves exactly as today.

Block tests (`test_protect_paths_bash.py`, rc 2), verbatim from A4: `true; cp /tmp/f .sdlc/config.env`;
`true\ncp /tmp/f .sdlc/config.env`; `true&&cp /tmp/f .sdlc/config.env`; `true 2> .sdlc/config.env`;
`true &> .sdlc/config.env`; `echo x >| .sdlc/config.env`; `rm -f .sdlc/active`; `rm -rf .claude/hooks`;
`unlink .sdlc/active`; `rmdir .sdlc/release-authorizations`; `git rm -q .sdlc/active`;
`git mv .sdlc/active /tmp/a`; `git restore .sdlc/config.env`; `chmod -x .claude/hooks/protect-paths.sh`;
`chown 0 .sdlc/config.env`; `mv .sdlc/active /tmp/a`; `cp -t .claude/hooks /tmp/x.sh`;
`install -t .claude/hooks /tmp/x.sh`; `cp --target-directory=.claude/hooks /tmp/x.sh`;
`sort -o .sdlc/config.env /tmp/x`; `sed --in-place s/a/b/ .sdlc/active`; `perl -pi -e s/a/b/ .sdlc/active`;
`perl -0pi.bak -e s/a/b/ .sdlc/active`; `( cp /tmp/f .sdlc/x )`; `{ cp /tmp/f .sdlc/x; }`;
`(cp /tmp/f .sdlc/x)`; `echo x > "$PWD"/.sdlc/x`; payload `cwd=<root>/.sdlc` + `echo x > config.env`;
payload `cwd=<root>/.claude` + `cd hooks && echo x > y.sh`; NotebookEdit `notebook_path: .sdlc/x.ipynb`.
Allow tests (rc 0), verbatim from A4: `cmd >/dev/null 2>&1`; `ls 2>/dev/null`; `make test 2>&1 | tee /tmp/log`;
`rm -rf /tmp/build`; `mv /tmp/a /tmp/b`; `chmod +x /tmp/x.sh`; `git checkout -b kit/x`;
`git rm --cached /tmp/x`; `sort .sdlc/config.env`; payload `cwd=/tmp` + `echo x > out.txt`;
`echo "a > b"` (existing test, still allows). Existing pins stay: `scripts/verify.sh 2>&1 | tail -3`
(`test_protect_paths_bash.py:133`) and `grep -rn TODO src/ 2>&1 | head` (`test_bash_plan_gates.py:84`).
Eval `hook-blocks-delete-and-glued-writes.yaml`: `rm -f .sdlc/active`, `true; cp /tmp/f .sdlc/x` and
`true 2> .sdlc/x` blocked, `ls 2>/dev/null` allowed, in the `jq -nc … | protect-paths.sh` form of
`hook-blocks-bash-write-to-protected-path.yaml`.

### Data and migrations
None. No new field is stored; `cwd` is read from the hook input and used only within the hook process.
No dependency is added (security-standards 5).

### Failure modes and how they surface
A wrong or missing arm fails toward a block: the agent sees one `SDLC hook blocked this action:` line
naming the path and retries with the Write tool. A syntax error in `_lib.sh` blocks every tool at once;
the second-shell rule in plan.md catches it before the session depends on it. A payload without `cwd`
(older client, hand-built fixture) falls back to ROOT, which is today's behaviour, never an error. The
accepted residuals fail open by design and are listed in the decision record so a reader does not
mistake the guard for a parser; the CI control-plane check and the merge click remain the gate.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: a verdict-changing edit to `_lib.sh` can lock the session out of Edit, Write and Bash — policy: CLAUDE.md lessons learned (test `_lib.sh` from a second shell) — contradiction? no — owner: luissiviero — resolution: one Write per change, `bash -n`, hook modules from a second shell before the next tool call.
- C2: `chmod`/`chown` and `rm` on ordinary paths become candidates, so `chmod +x scripts/new.sh` needs an approved plan and `rm -rf build/` inside `PLAN_REQUIRED_PATHS` too — policy: hard rule 1 and bash-write-guard.md "false positives are nearly free" — contradiction? no — owner: luissiviero — resolution: accepted; a plan is needed to add a script anyway, and the cost is one stderr line.
- C3: after this item the guard still fails open on the residual list (`bash -c`, `eval`, `xargs`, archives, variables, quoted spaces) — policy: security-standards 8 and bash-write-guard.md:57-61 — contradiction? no — owner: luissiviero — resolution: documented as accepted residuals; CI plus branch protection plus the owner's merge click stop intent.
- C4: `cwd` is a field the agent's tool call does not author but the guard now trusts it as a base — policy: security-standards 3 (validate at the boundary) — contradiction? no — owner: luissiviero — resolution: `canon` normalises it like any path; an absent or non-path value falls back to ROOT.
- C5: `cp … 2>/dev/null` and `cp … 2>&1` pass today and after A4 as written (gotcha G1) — policy: bash-write-guard.md "deliberately over-inclusive" — contradiction? no — owner: luissiviero — resolution: proposed one-line fix in D3; owner decides in intent Q1.

## Open questions carried from intent.md
- Q1 (trailing redirection after `cp`): proposed answer is the backwards scan in D3, one test added.
- Q2 (which arms to drop if the 140-line bound is exceeded): proposed answer is `chgrp` then `rmdir`.

## Decisions (ADR-style: context → decision → consequences)
- D1: keep the text heuristic and the 140-line bound rather than a shell parser → the arms above and nothing more; every shape outside them is a named residual → predictable cost per Bash call (one `sed`, one `grep`, one token loop).
- D2: `rel()` reads `cwd` for every hook instead of each hook reading it → `protect-paths.sh` switches to `rel` at `:36` → the three plan/path hooks judge relative paths the same way.
- D3: proposed, pending Q1: the `cp|install|rsync` last-argument rule scans back from `e-1` over tokens in the skip class → `cp /tmp/x .claude/hooks/y.sh 2>/dev/null` reports `.claude/hooks/y.sh` → one extra test `test_blocks_cp_with_trailing_redirect`.
- D4: `mv` reports both operands → `mv .sdlc/active /tmp/a` is a write to `.sdlc/active` and `mv /tmp/a /tmp/b` reports two paths outside ROOT → no new false positive on repo-external moves.

## Gotchas found while reading the codebase
- G1: `cp /tmp/x .claude/hooks/y.sh 2>/dev/null` and `… 2>&1` return rc 0 today (reproduced): the trailing token is taken as the destination at `_lib.sh:154` and A4's skip class does not cover a token starting with a digit. See C5/D3.
- G2: A4 names line 120 for `)`/`}`; the argument-end scan at `:129` needs them too, otherwise `( cp /tmp/f .sdlc/x )` still reports `)` as `cp`'s last argument.
- G3: A4's `{`/`}` split turns `${SRC}` into four tokens and `{` becomes a separator, so `cp ${SRC} .sdlc/x`, which is blocked today (reproduced, rc 2), would end `cp`'s arguments at `$`. Split braces only where the shell requires blanks around them.
- G4: A4 writes the step-4 rewrites as `$PWD/`→`${CWD:-$ROOT}/…` and `~/`→`$HOME/…`; substituting those literal strings would leave a `$` prefix and the drop rule at `:195` would discard the candidate. The rewrite must expand the value.
- G5: `hooktest.run_hook` passes the payload dict untouched, so a top-level `cwd` key needs no harness change; only the `bash()` builders in the two test modules gain `cwd=`.
- G6: `test_hooks_baseline.py` has no NotebookEdit case and no fixture exists for it; `.claude/settings.json` already lists `NotebookEdit` in both matchers, so the hooks are invoked and exit 0 blind.
- G7: `under_any` (`_lib.sh:76-78`) matches a candidate equal to a prefix, so `rm -rf .claude/hooks` blocks on `.claude/hooks` itself without a trailing slash.

## Not doing
- A shell parser, quoting-aware tokenisation, or paths with spaces.
- The residual list from intent.md (`bash -c`, `sh -c`, `eval`, `node -e`, `ruby -e`, `python3 -c` beyond `open(…,'w')`, `tar x`, `unzip`, `xargs`, `find -exec`, variable-assembled paths, variable `cd` targets, scripts written elsewhere then run). Owner sign-off: the decision record names them under `## Accepted residuals`.
- Changes to `.claude/settings.json`, the unlock, `BASH_WRITE_GUARD`, `production-gate.sh` or CI.
