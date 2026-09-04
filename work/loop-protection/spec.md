---
type: sdlc/spec
id: loop-protection
title: The agent must not be able to weaken the check on its own work
description: Protect the verify loop and the session settings as control plane, lock only existing tests under a fix, pre-approve the loop and deny egress in settings, and make a skipped check or a failing eval speak.
stage: design
status: in-review
reads: intent.md
approved-by:
approved-on:
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Transcribed from the approved implementation plan (session above), section WI-3 and appendix A3, by a drafting subagent; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, verify, protect-tests, settings, consensus-item-3, consensus-item-12]
timestamp: 2026-09-04T21:49:03Z
---
# Spec: the agent must not be able to weaken the check on its own work

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) loop files protected; (2) existing-only test lock through one parser; (3) permissions in both settings files; (4) skipped checks and failing evals report; (5) REVIEW.md rule; (6) tests, evals, docs, verify green.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `PROTECTED_PATHS` in `.sdlc/config.env` also lists `.claude/settings.json scripts/verify.sh scripts/run_tests.py scripts/run_evals.sh scripts/checks`; Edit and Bash writes to them exit 2 without the unlock | 1 | `scripts/test_protect_paths_bash.py::BashWriteGuardBlocks::test_blocks_edit_of_verify_script` and `::test_blocks_redirect_into_checks_dir`; `scripts/test_control_plane_hardening.py::LoopProtection::test_settings_json_is_protected`; eval `evals/cases/hook-blocks-verify-edit.yaml` |
| R-2 | `.github/CODEOWNERS` has an owner line for every entry of `PROTECTED_PATHS`, including `.gemini` | 1 | `scripts/test_control_plane_hardening.py::LoopProtection::test_codeowners_mirrors_protected_paths` |
| R-3 | Rule 3 in `docs/sdlc/rules/10-hard-rules.md` names the five new entries; the three context files are regenerated | 1, 6 | `python3 scripts/gen_context_files.py --check` last line `CONTEXT: 3 files up to date`; `grep -q 'scripts/verify.sh' CLAUDE.md` exit 0 |
| R-4 | `protect-tests.sh` reads `kind:` with `fm_value`: `kind: fix   # comment`, `kind: "Fix"`, `kind: Fix` and a CRLF plan all lock | 2 | `scripts/test_hooks_baseline.py::ProtectTestsHook::test_kind_with_trailing_comment_locks`, `::test_quoted_kind_locks`, `::test_capitalised_kind_locks`, `::test_crlf_plan_locks` |
| R-5 | Under `kind: fix` a path matching `TEST_FILE_GLOBS` is blocked only when it exists; the message says "existing test file"; a new test file or a new `evals/cases/*.yaml` is allowed, an existing one blocked, on both branches | 2 | `ProtectTestsHook::test_blocks_existing_test_file_when_kind_fix`, `::test_allows_new_test_file_when_kind_fix`, `::test_allows_new_eval_case_when_kind_fix`, `::test_blocks_existing_eval_case_when_kind_fix`; `scripts/test_bash_plan_gates.py::ProtectTestsBashBranch::test_blocks_sed_in_place_on_existing_test_file_during_fix`, `::test_allows_redirect_creating_new_test_during_fix`; evals `hook-allows-new-test-under-fix.yaml`, `hook-protects-tests-during-fix.yaml` |
| R-6 | `require-plan.sh` reads `status:` with `fm_value`; `status: approved   # comment` allows, `status: in-review # c` blocks quoting `'in-review'` with no `#` | 2 | `scripts/test_hooks_baseline.py::RequirePlanHook::test_status_with_trailing_comment_is_read`, `::test_status_in_review_with_comment_blocks_with_clean_value` |
| R-7 | `.claude/settings.json` and `docs/sdlc/templates/claude-settings.json` carry the same `permissions.deny` and `permissions.allow` lists and differ only by the `env` key | 3 | `scripts/test_control_plane_hardening.py::LoopProtection::test_settings_files_carry_permissions_and_differ_only_by_env`; `scripts/test_adopt.py::AdoptScript::test_with_hooks_settings_is_the_kit_template` (existing, unchanged) |
| R-8 | `scripts/verify.sh` prints `skipped (not executable): <check>` and ends `VERIFY: FAIL` (exit 1) for a non-executable check; with `VERIFY_ALLOW_SKIPPED_CHECKS=1` it prints the line and passes | 4 | `scripts/test_verify.py::VerifyScript::test_non_executable_check_fails_verify_and_reports`, `::test_non_executable_check_skipped_when_allowed_by_env` |
| R-9 | `scripts/run_evals.sh` prints the oracle's stdout and stderr, indented, after `✘ <name>`; a `✔` case prints nothing extra; the `EVALS:` line is unchanged | 4 | `scripts/test_run_evals.py::RunEvalsScript::test_failing_check_prints_its_output`; `::test_counts_and_exit_code` (existing, unchanged) |
| R-10 | `REVIEW.md` Compliance pass: a diff touching `scripts/verify.sh`, `scripts/checks/`, `scripts/run_tests.py`, `scripts/run_evals.sh` or, under `kind: fix`, an existing test file is Important unless `plan.md` names it | 5 | `grep -q 'kind: fix' REVIEW.md && grep -q 'scripts/verify.sh' REVIEW.md && echo REVIEW-RULE: OK` prints `REVIEW-RULE: OK` |
| R-11 | Every hook verdict for an input that passes today is unchanged except the cases in R-4 and R-5; the whole suite is green | 6 | `scripts/verify.sh` last line `VERIFY: PASS (<sha>)`; `scripts/run_evals.sh` last line `EVALS: N pass, 0 fail, M skipped` |

## Design
### Architecture / data flow
No new component. `protect-paths.sh:23` already tests every candidate with `under_any` (`_lib.sh:76-78`), which matches `"$prefix"` or `"$prefix"/*`, so a file entry in `PROTECTED_PATHS` matches as is and `scripts/checks` covers the directory. `adopt.sh:249-256` rewrites only `VERIFY_CMDS` and `PLAN_REQUIRED_PATHS`, so adopters receive the new list verbatim. The two plan hooks stop parsing front matter with their own `awk` and call `fm_value` from `_lib.sh`, which the `control-plane-visibility` item adds (`fm_value <file|-> <key> [any]`: CR, trailing ` # comment` and quotes stripped, casefolded). `protect-tests.sh` adds one existence test before its `block`. The two runners change one line each. The settings files gain a `permissions` object; nothing reads it but Claude Code.

### Interfaces (APIs, events, schemas) — exact shapes
`.sdlc/config.env:7`:
```
PROTECTED_PATHS=".claude/hooks .github/workflows .sdlc .gemini .claude/settings.json scripts/verify.sh scripts/run_tests.py scripts/run_evals.sh scripts/checks"
```
`.github/CODEOWNERS`, after line 16 (`/.sdlc/ @luissiviero`), one line each: `/.gemini/`, `/.claude/settings.json`, `/scripts/verify.sh`, `/scripts/run_tests.py`, `/scripts/run_evals.sh`, `/scripts/checks/`, all `@luissiviero`.

`protect-tests.sh:15` becomes `KIND="$(fm_value "$PLAN" kind)"`; the `case` at `:22` becomes (appendix A3):
```bash
    case "$R" in $g|*/$g)
      [ -e "$ROOT/$R" ] || return 0   # a NEW test (the failing reproduction) is allowed
      block "'$R' is an existing test file and work/$SLUG/plan.md is kind: fix$where. Fix the code, not the test. If the test itself is wrong, say so and stop; a human changes it." ;;
```
`require-plan.sh:19` becomes `STATUS="$(fm_value "$PLAN" status)"`; the block message at `:20` is unchanged and now quotes the cleaned value. `TEST_FILE_GLOBS` (`.sdlc/config.env:17`) keeps `evals/cases/*`.

`permissions` in both settings files (the template has no `env`; the kit file keeps `"env": {"SDLC_CONTROL_PLANE_UNLOCK": "1"}` and is otherwise identical):
```json
"permissions": {
  "deny": ["Read(./.env)", "Read(./.env.*)", "Read(./secrets/**)", "Read(~/.ssh/**)", "Read(~/.aws/**)", "WebFetch", "Bash(curl *)", "Bash(wget *)"],
  "allow": ["Bash(scripts/verify.sh)", "Bash(python3 scripts/run_tests.py*)", "Bash(scripts/run_evals.sh*)", "Bash(python3 scripts/check_artifact_chain.py*)", "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)"]
}
```
`scripts/verify.sh:15` (`[ -x "$check" ] || continue`) becomes:
```bash
  if [ ! -x "$check" ]; then
    echo "  skipped (not executable): $check"
    [ "${VERIFY_ALLOW_SKIPPED_CHECKS:-0}" = 1 ] || { echo "  ✘ FAIL"; fail=1; }
    continue
  fi
```
`scripts/run_evals.sh:75` captures `bash -c "$check"` into a `mktemp` file instead of `/dev/null`; on `✘` it prints that file with a four-space indent, then removes it. `REVIEW.md` Compliance bullet gains: "A diff that touches `scripts/verify.sh`, `scripts/checks/`, `scripts/run_tests.py` or `scripts/run_evals.sh`, or under `kind: fix` an existing test file, is **Important** unless `plan.md` names that file."

### Data and migrations
None. No new field; nothing personal or regulated (security-standards §4 n/a). `.sdlc/.last-verify` semantics unchanged: still touched only on pass (`verify.sh:21`).

### Failure modes and how they surface
- `fm_value` absent (this item merged before `control-plane-visibility`): bash prints `fm_value: command not found` on stderr; `KIND` is empty and `protect-tests.sh` fails open, `STATUS` is empty and `require-plan.sh` fails closed. R-4 turns red before that ships; the order-of-work constraint in `plan.md` prevents it.
- A protected write from an agent: `protect-paths.sh` exit 2 with the path and the whole list in the message; under the unlock, one audit line per write on stderr (unchanged).
- `chmod -x scripts/checks/x.sh`: `verify.sh` prints the skipped line and `VERIFY: FAIL`; CI goes red; the Stop hook stays armed because the stamp is not touched.
- A failing eval: the oracle's output appears under the `✘` line, so the reason is in the CI log.
- A session that needs `WebFetch` or `curl`: refused by Claude Code with the deny rule named; the fix is a PR on the now-protected `.claude/settings.json`, not a local override (deny wins over allow across settings files).

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: in this repo `scripts/verify.sh` and friends become protected while the kit's own `SDLC_CONTROL_PLANE_UNLOCK=1` still lets an agent edit them with an audit line, so rule 3 stays advisory for the loop here — policy: CLAUDE.md rule 3, `knowledge/decisions/self-hooks-on.md` — contradiction? yes, for this repo only — owner: luissiviero — resolution: accepted; CODEOWNERS plus `check_control_plane.sh` (agent-trailer aware after `control-plane-visibility`) make the `control-plane-approved` label the human act.
- C2: `permissions.allow` pre-approves `python3 scripts/run_tests.py*` and `scripts/run_evals.sh*`, which run code from the repo without a prompt — policy: security-standards §3 (no unvalidated input at a boundary), §8 — contradiction? no — owner: luissiviero — resolution: allow only commands whose file is in `PROTECTED_PATHS` in the same change; never add `Bash(git *)`.
- C3: `permissions.deny` removes `WebFetch`, `curl` and `wget` from every session, including the owner's own research sessions here — policy: security-standards §1, playbook Deploy play — contradiction? no — owner: luissiviero — resolution: accept; egress is not needed by any script in `scripts/`; revisit if a workflow needs it.
- C4: the agent drafting this spec is the agent the change constrains — policy: security-standards §8 — contradiction? no — owner: luissiviero — resolution: only the owner approves the three artifacts and applies the label; reviewer subagents stay read-only.

## Open questions carried from intent.md
- Q1 (verify from the base branch in CI): unresolved; proposed answer "not now" stands; the spec does not touch `.github/workflows/`.
- Q2 (`Bash(git *)` vs the three read-only forms): unresolved; the design uses the three; D4 records the reason.

## Decisions (ADR-style: context → decision → consequences)
- D1: protect the loop by file entries, not by adding `scripts` to `PROTECTED_PATHS`: the kit gates `scripts` with `PLAN_REQUIRED_PATHS` and adopters put nothing there, so a directory entry would block the kit's own product code and protect nothing for adopters → five file entries; a new check under `scripts/checks/` is a control-plane change and needs the label.
- D2: the test lock decides on `-e` at hook time, not `git ls-files`: a test created uncommitted earlier in the session is still the check being weakened, and the delete and rename arms of the Bash-guard item rely on the file existing when the hook runs → an agent that deletes then recreates a test is caught only by the delete arm (that item).
- D3: `verify.sh` fails on a skipped check by default; `VERIFY_ALLOW_SKIPPED_CHECKS=1` is the escape for an adopter mid-migration → a `chmod -x` is now a red build, and the contract line on the passing path is byte-identical.
- D4: `permissions.allow` lists the exact loop commands and `git status|diff|log` only → `git push`, `git commit` and everything else still prompt; `production-gate.sh` remains the gate for pushes.
- D5: the two plan hooks share `fm_value` rather than each fixing its own `awk` → one parser, one test module for it (`scripts/test_lib_helpers.py`, owned by `control-plane-visibility`); this item lands after it.

## Gotchas found while reading the codebase
- `docs/sdlc/managed-settings.example.json`: the `deny` list is line 4 and the `allow` list line 5; the plan cites `:5` for both.
- `scripts/test_adopt.py:307` is `AdoptScript.test_with_hooks_settings_is_the_kit_template`; it also asserts (`:318-320`) that six hook names appear in the template, so the `permissions` object must be added without disturbing the `hooks` wiring.
- `evals/cases/hook-protects-tests-during-fix.yaml` never creates `src/foo.test.ts`, so after the existence check its `!` line would fail: the case must `touch` the file first and gains a passing Write to `src/new.test.ts`.
- `scripts/test_hooks_baseline.py:121-126` and `scripts/test_bash_plan_gates.py:107-117` also never create the test they expect to be locked (`src/foo.test.ts`, `tests/test_a.py`); both fixtures must create the file, or the assertions flip.
- `scripts/hooktest.py:68-84` copies the real `.sdlc/config.env` into every fake repo, rewriting only `PLAN_REQUIRED_PATHS`, so every hook test sees the new `PROTECTED_PATHS` with no fixture change; `scripts/test_protect_paths_bash.py:38-41` and `scripts/test_bash_plan_gates.py:26-30` carry their own hard-coded configs and stay valid.
- `fm_value` casefolds (`print tolower(v)` in the appendix), so `KIND` compares as `fix` for `Fix`; the literal `kind: fix` in the block message keeps `test_hooks_baseline.py:126` passing.
- `scripts/run_evals.sh:51` unsets `SDLC_CONTROL_PLANE_UNLOCK` before running oracles, which is what lets `hook-blocks-verify-edit.yaml` observe a block from inside this repo.
- The `require-plan.sh` Bash branch blocked this drafting session's own `python3 - <<EOF` edit of a scratchpad file because the inline-script rule matched the word `scripts` inside the heredoc body: over-inclusive by design (`knowledge/decisions/bash-write-guard.md`); the implementer should use the Write tool for text that mentions `scripts`.

## Not doing
- `rm`, `unlink`, `git rm`, `git mv`, `mv`-source and `chmod` as writes: the `bash-guard-hardening` item, whose tests cover the delete and rename of an existing test under `kind: fix`.
- Running `scripts/verify.sh` from the base branch in CI (Q1); `incident.md` in the chain; adopter installation changes (`adopt.sh` is untouched and copies the new files as they are).
- Protecting `scripts/hooktest.py` or the `scripts/test_*.py` modules outside `kind: fix`: they are product code here and are plan-gated, not control plane.
- `permissions` in `.gemini/settings.json`: Gemini CLI has no equivalent key; Gemini sessions stay governed by the hooks, CI and branch protection only.
