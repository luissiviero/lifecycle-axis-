---
type: sdlc/plan
id: chain-check-without-gh
title: One new module seen red, then one except clause, then the production shapes measured with the token set
description: "kind fix: scripts/test_chain_no_gh.py lands red on three of its six cases, then verify_dispatch_run gains a NO_GH_NOTE constant and a try/except around its one gh call, the module goes green with every locked suite green unmodified, and the two real items that crashed on 17004b4 end CHAIN: PASS with the token set; the locked file lands by the owner's click and the item parks from a ledger-only pull request."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: delegated
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: fix
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by: claude
approved-on: 2026-09-18
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/111
tags: [chain-check, dispatch-attestation, gh, remote-session, fix, defect-3]
timestamp: 2026-09-18T17:20:00Z
---
# Plan: one new module seen red, then one except clause, then the production shapes measured with the token set (from intent.md 2026-09-17)

`kind: fix`, as the intent requires: `protect-tests.sh` locks every existing test file and eval case for the
life of this plan, so the six regression cases live in one new module the hook leaves writable, composing
`scripts/test_check_artifact_chain.py`'s fixture by import the way `scripts/test_chain_no_slug.py` and
`scripts/test_chain_shallow.py` do (spec D4). No engineer interview: the owner is the only human and works
from a phone, so the repository's record stood in -- `CLAUDE.md`, the suite this sits beside, defect 1's two
modules, and the spec's five gotchas.

**The merge is the owner's click.** `python3 scripts/check_detour.py --slug chain-check-without-gh --plan
work/chain-check-without-gh/plan.md` ends `DETOUR: needed (1)`: `scripts/check_artifact_chain.py` is on the
policy's `locked-paths`, so the delegated merge refuses this item's code pull request by design, while the
hooks permit the edit under this signed plan (`PLAN_REQUIRED_PATHS` is `scripts`; the file is not under
`PROTECTED_PATHS`). The route is the detour rule's step 5, adopted at the spec gate in
`revisions/1.md` and confirmed at this gate in `revisions/2.md`: build to a ready pull request (#111), then
park from a second, ledger-only pull request with `parked: ready PR #111; click needed
(scripts/check_artifact_chain.py)`, so the pointer moves on and the click merges the code later.

## Files that change
- scripts/test_chain_no_gh.py — new; `class MissingBinary` on `test_check_artifact_chain._make_repo` / `_write` / `_git` / `_artifact` / `_last_line` / `SCRIPT`, with its own `_approve_with_trailers(root, wd, actor, author=None)` in the shape of `ApprovalAuthor._reapprove_with_trailers` (author the run's actor, committer the bot, both trailers), its own `_bin(tmp, name, script)` and `_bin_with_git_shim(tmp, argv_log)` (a directory holding only a `git` shim that logs argv and execs the real `git`, as `test_chain_shallow.py` builds one), `_env(bin_dirs, argv_log=None, token="t")` (`PATH` = exactly those directories, `GH_TOKEN`, `GITHUB_REPOSITORY=luissiviero/lifecycle-axis-`, `HOME` kept, nothing else), `_run_script`, `_porcelain` and an `_Environ` context manager that swaps `os.environ` for the in-process cases (the bullet first named narrower signatures; corrected to the module as committed on the review's two nits): `test_a_token_with_no_gh_is_a_note_not_a_crash` (the script as a subprocess, `--base HEAD`; expects `CHAIN: PASS`, `no gh binary on PATH` in stdout, no `Traceback` in stderr) — **red today**, exit 1 on `FileNotFoundError`; `test_a_token_with_no_gh_still_applies_the_author_rule_to_a_forged_trailer` (same, `author="Claude <noreply@anthropic.com>"`; expects `CHAIN: FAIL` and `unverified dispatch trailer and is authored by an agent identity`) — **red today**, the same traceback; `test_the_retire_route_takes_the_same_path` (in-process: `os.environ` patched to `_env`, `cac.verify_dispatch_run("12345", "luissiviero", slug="demo", artifact="intent.md", retired=True)`; expects `(None, cac.NO_GH_NOTE)`) — **red today**, raises; `test_a_present_gh_that_fails_is_still_false` (a second `bin` with a `gh` shim `printf 'boom' >&2; exit 1`; in-process; expects `ok is False` and `could not be read` in the detail) — green today, a pin; `test_the_check_never_reaches_for_the_network` (the R1 run through the logging shim; no argv line contains `fetch`, `clone`, `pull`, `remote` or `push`; `git status --porcelain` byte-identical before and after) — green today, a pin; `test_a_stubbed_subprocess_still_reaches_the_call` (`cac.subprocess.run` replaced by a fake answering `["gh", "api", ...]` with a matching run, `_env` in force; expects `True`) — green today, **the pin against a lookup before the call** (spec R1–R6, D3, D4, D5)
- scripts/check_artifact_chain.py — `NO_GH_NOTE = "no gh binary on PATH; the dispatch trailer was accepted on the author rule alone"` as a module constant beside `DISPATCH_WORKFLOW_PATH` (`:130`); in `verify_dispatch_run`, the `subprocess.run([...gh api...])` at `:237` wrapped in `try:` / `except FileNotFoundError: return None, NO_GH_NOTE`; one sentence in the function's docstring, after "(None, reason) when there is no token to ask with": "or when the `gh` exec itself raises FileNotFoundError: no `gh` on PATH (every remote session container), or `cwd=ROOT` gone from under the process. Both are "could not ask", the same skipped path, so the caller's author rule still applies (work/chain-check-without-gh R1, R2)". The wording names both causes, not only the absent binary (security-reviewer, revisions/2.md; the review nit on #111 line 220; shipped in `3982151`, deviation 1). Nothing before the call; nothing else in the file (spec D1, D3, R6)
- work/chain-check-without-gh/plan.md — this plan; its deviations log
- work/chain-check-without-gh/log.md — one ledger line per gate; the park line at the end
- work/chain-check-without-gh/revisions/2.md — this gate's detour record (`kind: detour`, `artifact: plan.md`), referring back to `revisions/1.md`
- work/chain-check-without-gh/revisions/index.md — one line for `2.md`
- work/chain-check-without-gh/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none) — `RELEASE_GATED_PATHS` is `migrations infra terraform helm`; nothing here is under it. The click owed
on `scripts/check_artifact_chain.py` is the `locked-paths` route stated above, not a release gate.

## Order of work (each step independently verifiable)
1. **The module, red.** Draft `scripts/test_chain_no_gh.py` in the scratchpad against the suite's helpers,
   copy it in, `git add` it (`knowledge/lessons/stage-new-files-before-verify.md`). Verify: `python3 -m
   unittest scripts/test_chain_no_gh.py -v` reports exactly **three** failures (R1, R2, R3 cases, each on
   `FileNotFoundError` or an exit-1 traceback) and three passes (R4, R5, R6). Commit red:
   `[chain-check-without-gh] Red: six cases, three failing on the missing binary`.
2. **The fix.** The constant, the `try`/`except`, the docstring sentence. Verify: the module is six green;
   `python3 -m unittest scripts/test_check_artifact_chain.py` is 94 green unmodified;
   `scripts/test_chain_no_slug.py` and `scripts/test_chain_shallow.py` green unmodified; `git diff --stat
   origin/main -- scripts/` names exactly the two files above. Commit: `[chain-check-without-gh] Fix: a
   missing gh binary takes the skipped path`.
3. **The production shapes, with the token set.** On this full clone with the container's token in the
   environment and no `gh`: `python3 scripts/check_artifact_chain.py --base HEAD --slug ci-budget` and
   `--slug self-check-false-reds` each end `CHAIN: PASS` with three `no gh binary on PATH` notes and no
   traceback (the two runs the intent measured crashing on `17004b4`); `scripts/verify.sh` with the token set
   ends `VERIFY: PASS` (the pointer names this item, whose intent carries a tapped approval, so this is R7's
   second half). Paste all three last lines into the pull request.
4. **The whole loop.** `python3 scripts/gen_index.py`; `scripts/verify.sh` under `env -u GH_TOKEN -u
   GITHUB_TOKEN` and bare; `python3 scripts/check_artifact_chain.py --base origin/main --slug
   chain-check-without-gh` after committing; `scripts/run_evals.sh`; `python3 scripts/check_okf.py`;
   `python3 scripts/check_detour.py --diff origin/main` (expected `DETOUR: needed (1)`, the same path, the
   route already adopted: no third record). Push.
5. **Review, ready, park.** `/sdlc-review` with reviewer subagents on a different model from the writer;
   findings posted on #111 ending `Important: <n> | Nits: <m>`; fix and repeat to `Important: 0`; `gh pr
   ready` and `PR #111 | draft -> in-review` in the ledger. Then, from a fresh branch off `origin/main`
   (`claude/chain-check-without-gh-park`), the ledger-only park pull request: append `- <ts> | intent.md |
   approved -> approved | claude | <sha> | parked: ready PR #111; click needed
   (scripts/check_artifact_chain.py)` to `log.md`, `python3 scripts/gen_index.py`, commit, push, ready with
   `Work-Item: chain-check-without-gh`. The delegated merge takes it and its advance moves the pointer
   (empty queue: it clears it). Once it merges, merge `origin/main` into `claude/chain-check-without-gh`
   (both branches append to `log.md`; keep both sets of lines, the park line last) and push, so #111 is
   clean for the owner's click.
6. **Step 7 of `/sdlc-run`** after the click lands #111: the handoff refresh, the seed prompt (empty queue:
   no successor), and the retirement of the `env -u` workaround in the same refresh (owner's answer 4).

## Risks
- Risk: a lookup before the call sneaks in during review (a `shutil.which` "for clarity") → mitigation:
  R6's case is red under any such guard on this machine, and the spec's gotcha 1 explains why (the locked
  suite stubs `subprocess.run`).
- Risk: the `PATH`-only-shim environment breaks `git` itself (helpers it execs) → mitigation: `git` locates
  its own `--exec-path` binaries without `PATH`; defect 1's `test_the_check_never_fetches` already ran the
  check through a shim-first `PATH`, and step 1 will show the three green pins passing under the same
  `PATH` before the fix, which proves the environment, not the fix, is what the red cases see.
- Risk: R2's fixture reaches the crash through a different branch than production → mitigation: the fixture
  is `ApprovalAuthor._reapprove_with_trailers`'s exact commit shape, and step 3 measures the two real items.
- Risk: the token-set `verify.sh` in step 3 crashes on something other than this defect → mitigation: it is
  the measurement the intent already made with the token unset; a new red there is a finding, reported, not
  fixed in this plan.
- Risk: the review round asks for a change to the new module → mitigation: none inside this plan, and none
  is wanted. `protect-tests.sh` locks a test file the moment it exists on disk (`[ -e "$ROOT/$R" ]`,
  `:29`), so after step 1 commits `scripts/test_chain_no_gh.py` the hook refuses every edit to it, as it
  refused defect 1's. Step 5's "fix and repeat" means the code; a finding against the module is a stop:
  say so on the pull request, and a human changes it (security-reviewer, revisions/2.md).
- What this could break: nothing with a token and a binary (R4); the no-token path is untouched. A runner
  with no `gh` now degrades to the author rule with a note instead of an unreadable traceback (spec C2, the
  owner's answer 5).
- Options considered and not taken: `shutil.which` before the call (gotcha 1); catching `OSError` (a present
  binary that cannot execute is not "absent", spec Not doing); a `gh --version` step in the workflow (the
  owner's, not this item's); installing `gh` in the environment (hides the defect for one runtime).

## Proof
- `scripts/verify.sh` green, under `env -u GH_TOKEN -u GITHUB_TOKEN` and bare (R7).
- Spec rows → tests, all in `scripts/test_chain_no_gh.py::MissingBinary`: R1 → `test_a_token_with_no_gh_is_a_note_not_a_crash`; R2 → `test_a_token_with_no_gh_still_applies_the_author_rule_to_a_forged_trailer`; R3 → `test_the_retire_route_takes_the_same_path`; R4 → `test_a_present_gh_that_fails_is_still_false` plus `scripts/test_check_artifact_chain.py` 94 green unmodified; R5 → `test_the_check_never_reaches_for_the_network`; R6 → `test_a_stubbed_subprocess_still_reaches_the_call`; R7 → step 4's five last lines.
- Red before green: step 1's commit shows exactly three failures; step 2's shows six passes with the same
  module byte-identical (`git diff <red-commit> <fix-commit> -- scripts/test_chain_no_gh.py` is empty).
- Manual / browser / screenshot / eval: step 3's three last lines with the token set, pasted into #111. No
  eval case is added: the fault has no hook or skill surface, and `run_evals.sh` runs the deterministic
  suite already (`evals/cases/*` is locked under `kind: fix` besides).

## Rollback
- `git revert` of step 2's commit restores the crash and turns the module's three cases red again; step 1's
  commit may stay (a red test module is a true statement about the reverted code) or be reverted with it.
  Nothing else depends on the constant.

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-18, `3982151` then this commit: the docstring sentence shipped with different wording than the
  bullet quoted, naming both causes of the caught exception (the review nit on #111 line 220, after the
  security-reviewer's nit in `revisions/2.md`); the bullet now quotes the shipped sentence. Wording inside
  one bullet, no file added, no step reordered; logged because rule 2 wants the plan and the code to agree
  in the same commit, which `3982151` did not do.
