---
type: doc
title: "Implementation plan: close the consensus findings"
description: "Approved 2026-09-04 plan: eleven work items, explicit file lists, tests, evals, landing order, verified hook designs."
tags: [sdlc, handoff, playbook-comparison]
timestamp: 2026-09-05T04:48:42Z
---

# Implementation plan: close the consensus findings in lifecycle-axis

## Context

Two independent analyses (an earlier row-by-row page and this session's adversarial run of the code)
were reconciled into a twelve-item fix list (`scratchpad/consensus.md`). The repo has the playbook's
shape, but several controls do not hold as written: approval is a record not a gate; the control-plane
unlock is invisible and the CI backstop never matched the kit's own branches; the verify loop is
unprotected; the deploy path fails open; the band detector cannot see a spike after a flat baseline;
the templates break their own parsers; a fresh adopter breaks in the first hour; and the docs claim
controls the code does not deliver.

Owner decisions (asked, answered): several per-change work items; keep the unlock and make it visible;
all twelve items, phased; bounded Bash-guard hardening with documented residuals.

Every `file:line` below was read from the working tree at `64bcb17` by read-only explorers in this
session, and the hook designs in the appendix were written by a design agent that reproduced each defect
against the live hooks first. Nothing has been changed yet.

## How the work runs (the repo's own process, applied to itself)

- Each work item is `work/<slug>/` with `intent.md` → `spec.md` → `plan.md`; the agent writes each with
  `status: in-review`; the owner approves with `python3 scripts/approve.py <slug> <artifact> --as
  luissiviero` from their own shell (`scripts/approve.py:70-73` refuses under `CLAUDECODE`). The plan's
  `## Files that change` lists explicit paths, never `**` globs (`.claude/skills/sdlc-plan/SKILL.md:10`).
  This retires the umbrella plan by example.
- Before implementing an item the owner runs `approve.py <slug> plan.md --activate` (or the agent exports
  `SDLC_WORK_ITEM=<slug>`); `require-plan.sh:14-20` blocks every write under `PLAN_REQUIRED_PATHS=
  "scripts"` (`.sdlc/config.env:4`) otherwise. Today `.sdlc/active` is `delegation-boundary`, a draft
  intent, so nothing under `scripts/` is editable until an item is activated. Every plan is
  `kind: feature` (tests change in all of them).
- Branch `work/<slug>`, PR title `[<slug>] …`, body `Work-Item: <slug>` (`docs/sdlc/rules/30-conventions.md:17`).
- Control-plane files (`.claude/hooks/`, `.claude/settings.json`, `.github/workflows/`, `.sdlc/`,
  `.gemini/`) are writable here under the unlock. From WI-2 on, `check_control_plane.sh` recognises the
  kit's own agent PRs, so each such PR needs the owner's `control-plane-approved` label.
- `_lib.sh` is sourced by every hook: a bad edit locks Edit, Write and Bash at once (CLAUDE.md line 70).
  Rule: one Write per `_lib.sh` change, `bash -n` it, then run the hook test modules from a second
  shell before the session issues its next tool call. Hook wiring is read at session start; restart
  after changing `.claude/settings.json`.
- Per PR: `scripts/verify.sh` → `VERIFY: PASS (<sha>)`; `python3 scripts/check_artifact_chain.py --base
  origin/main --slug <slug>` → `CHAIN: PASS`; `scripts/run_evals.sh` → `0 fail`; `python3
  scripts/run_tests.py -p <module>.py` for every touched test module; regenerate with
  `python3 scripts/gen_context_files.py && python3 scripts/gen_index.py` before committing.

## Step 0 (owner, before WI-1): retire the umbrella plan

Set `work/sdlc-kit-phase-1/{intent,spec,plan}.md` to `status: superseded` (keep `approved-by`), append
one `approved -> superseded` line per artifact to `work/sdlc-kit-phase-1/log.md`, commit as the owner
(`check_artifact_chain.py:191-218` validates supersession like approval). Run `python3 scripts/gen_index.py`.

## Order and why

WI-1 front-matter → WI-2 visibility (additive `_lib.sh`) → WI-3 loop protection → WI-4 Bash guard →
WI-5 deploy gate → WI-6 approval gate (the new hook, last of the hook items: most restrictive, depends
on WI-2's helpers) → WI-7 detector → WI-8 adopter (needs WI-3 settings, WI-5 `deploy.sh`, WI-6
`approve.py`) → WI-9 agent evals → WI-10 delegation (any time after Step 0) → WI-11 docs sweep.
WI-2..WI-6 all touch `_lib.sh` or the hooks: land serially, never in parallel worktrees.

---

## WI-1 `front-matter` — templates stop breaking their parsers; approve.py stops misfiring

No hook runtime change. Consensus item 6 and part of 1.

1. `scripts/check_artifact_chain.py:42-53`: add `_fm_value()` and make `front_matter_text()` skip
   comment lines and strip trailing ` #…` and matching quotes (appendix A6). Imported by
   `approve.py:33`, `gen_index.py`, `gen_context_files.py`, `check_okf.py`, `check_plugin_manifest.py`,
   so all readers get it. Fix the error text at `:281` (`'## Files'` → `'## Files that change'`).
2. Templates: move inline comments to a `#` line above the field in `docs/sdlc/templates/intent.md:7,9,11,12`,
   `plan.md:7-8,10`, `spec.md:9,11`, `incident.md:8` (exact new lines in A6). `evals/cases/
   skill-names-match-templates.yaml` greps `^skills-applied:` and `^## `, unaffected.
3. `work/_example/{intent,spec,plan}.md`: front matter and headings match the templates
   (`originator:`→`author:`, `source:`→`resource:`, `## Success criteria`→`## Proposed outcome`,
   `## Constraints and non-goals`→`## Constraints`; add the missing spec sections as empty stubs).
4. `scripts/approve.py:75`: default handle is `git config sdlc.approver` only; if unset, exit 1 with
   the `--as` hint (today `user.name` yields `luis`, not an approver). Add stage order: refuse `spec.md`
   unless `intent.md` is approved, `plan.md` unless `spec.md` is.
5. `scripts/approvers.py`: `Approvers.has_role(role, handle) -> (bool, reason)` (same normalisation
   and never-approve check as `is_valid`, keyed by role) and a CLI `python3 scripts/approvers.py
   --has-role <role> <handle>` exiting 0/1. Used by WI-5's `deploy.sh`.
6. `scripts/hooktest.py:fake_repo`: new kwarg `approvers_yaml=None`; when None, copy
   `REAL_ROOT/.sdlc/approvers.yaml` into the fake repo (needed by WI-6; forward-compatible now).
   Fixtures at `scripts/test_hooks_baseline.py:106` and `scripts/test_bash_plan_gates.py:22-24` gain
   `approved-by: luissiviero` (passes before and after WI-6).
7. Tests: `scripts/test_check_artifact_chain.py` new class `TemplateFrontMatter` (verbatim template
   copy passes in-progress mode; `status: draft   # …` parses; quoted status; `# status:` comment line
   is not a key; `\r\n` input; `resource: https://x/y#z` keeps its anchor). `scripts/test_approve.py`
   (template-derived approval yields a 5-field ledger line, `malformed == []`, no `#` left on the
   `status:` line; missing `sdlc.approver` exits 1 with the hint; stage-order refusal).
   `scripts/test_approvers.py` (`has_role`: listed → 0, `claude` → 1, unknown role → 1).
8. Docs: `docs/sdlc/rules/30-conventions.md:23-24` (approve from your own shell, or the GitHub web
   editor; set `git config sdlc.approver`). Regenerate context files.

Files: `scripts/check_artifact_chain.py`, `scripts/approve.py`, `scripts/approvers.py`,
`scripts/hooktest.py`, `scripts/test_check_artifact_chain.py`, `scripts/test_approve.py`,
`scripts/test_approvers.py`, `scripts/test_hooks_baseline.py`, `scripts/test_bash_plan_gates.py`,
`docs/sdlc/templates/{intent,spec,plan,incident}.md`, `work/_example/{intent,spec,plan}.md`,
`docs/sdlc/rules/30-conventions.md`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `work/index.md`,
`work/_example/index.md`.

---

## WI-2 `control-plane-visibility` — decisions are logged; unlocked writes are visible; CI sees agent PRs

Consensus items 2 and 4. `_lib.sh` changes are additive (no verdict changes) except the never-unlock list.

1. `_lib.sh` after line 50: read `CWD` and `SESSION_ID` from the input (A2). After line 78:
   `DECISION_LOG`, `log_decision <verdict> <detail>`; `block()`/`ask()` (`:79-80`) log first. Add
   `fm_value <file|-> <key> [any]`, `artifact_role <artifact>`, `approver_has_role <handle> <role>`
   (A1, A3); `FILE` at `:49` falls back to `.tool_input.notebook_path`; `rel()` (`:75`) resolves a
   relative path against `CWD` when set. New `scripts/test_lib_helpers.py` drives these through
   `bash -c '. _lib.sh; …'` with `input="{}"` (pattern: `scripts/test_gemini_wiring.py` `_canon`).
2. `.gitignore`: add `.sdlc/hook-decisions.log` and `monitoring/series/`.
3. `protect-paths.sh:23-28`: an `UNLOCKED` accumulator; the unlock branch keeps the stderr line
   (tests at `test_protect_paths_bash.py:170`, `test_bash_plan_gates.py:151,158`,
   `test_control_plane_hardening.py:111` and eval `hook-unlock-covers-edit-branch` assert it), logs
   `unlock`, and a `finish()` emits one `{"systemMessage": …}` JSON on exit 0 (A2). Never
   `permissionDecision: allow`. Before the `PROTECTED_PATHS` test, a never-unlock `case` for
   `.sdlc/release-authorizations`, `.sdlc/approvers.yaml`, `.sdlc/hook-decisions.log` (A5).
4. `scripts/check_control_plane.sh:35,76-79`: `AGENT_BRANCH_PREFIXES` becomes a `.sdlc/config.env` key
   (default `"claude/ kit/ spike/"`; not `work/`, which humans use); add `has_agent_trailer()` over
   `git log --format=%B "$BASE..HEAD"` matching `^(Co-Authored-By:.*Claude|Claude-Session:)` (A2).
   `sdlc-gate.yml:19` already checks out with `fetch-depth: 0`; no workflow change.
5. Tests: `scripts/test_bash_plan_gates.py::UnlockOnEditBranch` (log line on unlock; one
   `systemMessage` for two targets, no `hookSpecificOutput`; block and ask are logged; read-only
   `.sdlc` does not break the hook, skipped on Windows; unlock never covers the three never-unlock
   paths). `scripts/test_check_control_plane.py` (`kit/foo` blocked; `Co-Authored-By: Claude` trailer
   on `work/x` blocked; `Claude-Session:` blocked; trailer + label exempt; trailer only on a base
   commit is human; prefixes from config).
6. Evals: `hook-unlock-writes-decision-log.yaml`, `ci-control-plane-detects-agent-trailer.yaml`.
7. Docs: `knowledge/decisions/self-hooks-on.md:55,59-61`, `knowledge/decisions/bash-write-guard.md:51-56,77-78`,
   `knowledge/decisions/control-plane-label.md:32-34`, CLAUDE.md lesson line 68 (outside the markers,
   edit directly), `.sdlc/README.md:1` and a line for the new key, `docs/sdlc/README.md:108`,
   `docs/sdlc/metrics.md` approval-gates row (gate wait is now readable from the log).

Files: `.claude/hooks/_lib.sh`, `.claude/hooks/protect-paths.sh`, `.gitignore`, `.sdlc/config.env`,
`.sdlc/README.md`, `scripts/check_control_plane.sh`, `scripts/test_lib_helpers.py` (new),
`scripts/test_bash_plan_gates.py`, `scripts/test_check_control_plane.py`,
`evals/cases/hook-unlock-writes-decision-log.yaml`, `evals/cases/ci-control-plane-detects-agent-trailer.yaml`,
`knowledge/decisions/{self-hooks-on,bash-write-guard,control-plane-label}.md`, `CLAUDE.md`,
`docs/sdlc/README.md`, `docs/sdlc/metrics.md`.

---

## WI-3 `loop-protection` — the agent cannot weaken the check on its own work

Consensus items 3 and 12.

1. `.sdlc/config.env:7`: `PROTECTED_PATHS=".claude/hooks .github/workflows .sdlc .gemini
   .claude/settings.json scripts/verify.sh scripts/run_tests.py scripts/run_evals.sh scripts/checks"`
   (`under_any`, `_lib.sh:76-78`, matches file entries as is). `adopt.sh:249-256` rewrites only two
   other keys, so adopters get this verbatim (locked there; edited via PR). Mirror in
   `.github/CODEOWNERS` after line 16: `/.gemini/`, `/.claude/settings.json`, `/scripts/verify.sh`,
   `/scripts/run_tests.py`, `/scripts/run_evals.sh`, `/scripts/checks/`. `docs/sdlc/rules/10-hard-rules.md:16`
   names them in rule 3.
2. `TEST_FILE_GLOBS` (`:17`) keeps `evals/cases/*`: PR #21 added it so oracles are locked, and the
   existence check below makes a *new* incident eval writable under a fix item.
3. `protect-tests.sh:15` → `KIND="$(fm_value "$PLAN" kind)"`; `:22` blocks only when
   `[ -e "$ROOT/$R" ]` (a new failing test is allowed, the playbook's own flow); message says
   "existing test file". `require-plan.sh:19` → `fm_value "$PLAN" status`. Delete/rename blocking
   arrives with WI-4's `bash_write_targets` arms; its tests are listed there.
4. `.claude/settings.json` and `docs/sdlc/templates/claude-settings.json` gain `permissions.deny`
   (`Read(./.env)`, `Read(./.env.*)`, `Read(./secrets/**)`, `Read(~/.ssh/**)`, `Read(~/.aws/**)`,
   `WebFetch`, `Bash(curl *)`, `Bash(wget *)`) and `permissions.allow` (`Bash(scripts/verify.sh)`,
   `Bash(python3 scripts/run_tests.py*)`, `Bash(scripts/run_evals.sh*)`,
   `Bash(python3 scripts/check_artifact_chain.py*)`, `Bash(git status*)`, `Bash(git diff*)`,
   `Bash(git log*)`); source `docs/sdlc/managed-settings.example.json:5`.
   `scripts/test_adopt.py:307` compares the installed file byte-for-byte to the template, so both
   change together; the kit file differs only by `env`.
5. `scripts/verify.sh:15`: print `skipped (not executable): <check>` and fail unless
   `VERIFY_ALLOW_SKIPPED_CHECKS=1`; `scripts/test_verify.py:76` asserts the report. `scripts/run_evals.sh:75`:
   capture the oracle output to a temp file and print it on `✘`.
6. `REVIEW.md` Compliance pass: a diff touching `scripts/verify.sh`, `scripts/checks/`, the runners
   or, under `kind: fix`, an existing test, is Important unless the plan names it.
7. Tests: `scripts/test_hooks_baseline.py::ProtectTestsHook` (new test file allowed; new eval case
   allowed; existing eval case blocked; `kind: fix   # comment` locks; `kind: "Fix"` locks; CRLF plan
   locks). Fixture flips: add the test file to `test_hooks_baseline.py:121-126`,
   `test_bash_plan_gates.py:107-117`, and `evals/cases/hook-protects-tests-during-fix.yaml` (create
   `src/foo.test.ts` first; add a passing Write to `src/new.test.ts`).
   `scripts/test_protect_paths_bash.py` (Edit `scripts/verify.sh` under adopter config → 2).
   `scripts/test_verify.py`, `scripts/test_run_evals.py`, `scripts/test_control_plane_hardening.py`
   (settings.json protected).
8. Evals: `hook-allows-new-test-under-fix.yaml`, `hook-blocks-verify-edit.yaml`.

Files: `.sdlc/config.env`, `.github/CODEOWNERS`, `.claude/hooks/protect-tests.sh`,
`.claude/hooks/require-plan.sh`, `.claude/settings.json`, `docs/sdlc/templates/claude-settings.json`,
`scripts/verify.sh`, `scripts/run_evals.sh`, `REVIEW.md`, `scripts/test_hooks_baseline.py`,
`scripts/test_bash_plan_gates.py`, `scripts/test_protect_paths_bash.py`, `scripts/test_verify.py`,
`scripts/test_run_evals.py`, `scripts/test_control_plane_hardening.py`, `evals/cases/
hook-protects-tests-during-fix.yaml`, `evals/cases/hook-allows-new-test-under-fix.yaml`,
`evals/cases/hook-blocks-verify-edit.yaml`, `docs/sdlc/rules/10-hard-rules.md`, `docs/sdlc/README.md`
(rows 97, 99, 101), `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`.

---

## WI-4 `bash-guard-hardening` — bounded closure of the write-guard gaps

Consensus item 3, second half. Verdict changes in `_lib.sh`; test from a second shell before relying on it.

1. `bash_write_targets` (`_lib.sh:93-199`, target ≤ 140 lines), per A4: redirections keep `2> X`,
   `&> X`, `>| X` as writes and neutralise only `N>&M` forms; pre-split on newlines, glued `;`, `&&`,
   `|`, `(`, `)`, `{`, `}` before tokenising (`)`/`}` join the separator list); new arms
   `rm|unlink|rmdir|chmod|chown|chgrp` (non-option args), `mv` (source and destination),
   `cp|install|rsync` `-t DIR`/`--target-directory`, `sort -o`, `sed|perl` `-i*`/`--in-place`/`-pi`,
   `git rm|mv|clean|checkout|restore` (all non-option args, `--` optional); step 4 strips all quotes
   and rewrites `$PWD/` and `~/` prefixes.
2. `bash_write_candidates` (`:201-219`): resolve every candidate against `canon "$CWD"` as well as
   ROOT and the `cd` targets (A4). `protect-paths.sh:36` uses `rel` like the other hooks.
3. `block-secrets.sh:6`: append `.tool_input.new_source`. New fixture
   `scripts/fixtures/hook_inputs/notebookedit.json` with a `_note` like `multiedit.json`'s.
4. Tests in `scripts/test_protect_paths_bash.py` (the `bash()` builder gains `cwd=`): the block list
   and allow list in A4 verbatim; `BlockSecretsWiderSurface` gets the notebook `new_source` case;
   `test_hooks_baseline.py` gets the NotebookEdit protected-path case. Delete/rename tests for
   `protect-tests.sh` go in `scripts/test_bash_plan_gates.py::ProtectTestsBashBranch` (`rm`,
   `git rm`, `mv … /tmp/`, `perl -pi -e` on an existing test under `kind: fix` → 2).
5. Evals: `hook-blocks-delete-and-glued-writes.yaml` (`rm -f .sdlc/active`, `true; cp …`,
   `true 2> .sdlc/x` blocked; `ls 2>/dev/null` allowed); extend
   `hook-blocks-bash-write-to-protected-path.yaml` with the newline form.
6. `knowledge/decisions/bash-write-guard.md`: reword `:99-102` (`2>`/`&>` are now writes), replace
   `:104-119` with the accepted-residuals list: `bash -c`/`sh -c`/`eval`, other interpreters
   (`node -e`, `ruby -e`, `python3 -c` beyond the `open(…,'w')` heuristic), archives (`tar x`,
   `unzip`), `xargs`, `find -exec`, variable-assembled paths, quoted paths with spaces, variable `cd`
   targets, scripts written elsewhere then run. Reason stays `:57-61`; the decision log, the
   trailer-aware CI check and the merge click stop intent.

Files: `.claude/hooks/_lib.sh`, `.claude/hooks/protect-paths.sh`, `.claude/hooks/block-secrets.sh`,
`scripts/fixtures/hook_inputs/notebookedit.json` (new), `scripts/test_protect_paths_bash.py`,
`scripts/test_hooks_baseline.py`, `scripts/test_bash_plan_gates.py`,
`evals/cases/hook-blocks-delete-and-glued-writes.yaml` (new), `evals/cases/hook-blocks-bash-write-to-protected-path.yaml`,
`knowledge/decisions/bash-write-guard.md`.

---

## WI-5 `deploy-gate` — the deploy path fails closed

Consensus item 4.

1. `production-gate.sh:92-95`: read `approved-by` with `fm_value "$AUTH" approved-by any`, require
   `approver_has_role "$BY" release-manager`; log `allow`/`reject` (A5). `:26`: `DEPLOY_RE` gains
   `deploy.sh` in command position and `gh (release create|workflow run|pr merge)`; new
   `DEPLOY_WORD_RE`+`PROD_RE` (the playbook's `deploy` and `prod|production` in one command) and
   `GH_API_RE`+`GH_MUT_RE` (mutating `gh api` on `releases|merges|dispatches`); `is_deploy()` replaces
   the grep at `:90` (A5).
2. `.github/workflows/deploy.yml:55`: `RELEASE_APPROVAL: ${{ secrets.RELEASE_APPROVAL }}` with a
   comment (empty unless a human stored the sha as an Environment secret); `CI: "true"` stays.
3. `scripts/deploy.sh` between `:75` and `:79`: if `RELEASE_APPROVAL` is empty and
   `.sdlc/release-authorizations/<sha>` exists, accept it only when `python3 scripts/approvers.py
   --has-role release-manager <handle>` exits 0; else refuse naming the handle (A5). The
   `GITHUB_ACTIONS` check stays, no longer described as unforgeable.
4. Tests: `scripts/test_hooks_baseline.py::ProductionGateHook` (authorization by release-manager →
   allow; by `claude` → ask; by `someone` unattended → 2; the seven ask and five allow strings in A5;
   `gh pr merge --admin 12` → ask). `scripts/test_deploy_guard.py`: `_make_repo` also copies
   `.sdlc/approvers.yaml`, `.sdlc/config.env`, `scripts/approvers.py`, `scripts/check_artifact_chain.py`;
   rename `:113` to `…release_approval_env_and_github_actions_succeeds` (Environment-secret path); new:
   committed authorization by release-manager succeeds; by non-release-manager refuses; file without
   `approved-by` refuses; env wins over file; `deploy.yml` has no `RELEASE_APPROVAL:` line containing
   `github.sha`.
5. Evals: `gate-blocks-unattended-deploy.yaml` (+ `gh release create`), `gate-ignores-unauthorized-release-file.yaml`
   (new), `deploy-refuses-without-approval.yaml` (file route).
6. Docs: `knowledge/decisions/deploy-from-ci.md:28-29,34-35,40-43`, `knowledge/decisions/
   merge-click-is-the-gate.md:32-33,43-45` (`gh pr merge` now prompts; the click on that prompt is the
   merge click), `.sdlc/environments.yaml:16-18` (drop "rehearsed in staging on a schedule"),
   `.sdlc/README.md` release-authorizations paragraph, `docs/sdlc/README.md:102,112`,
   `knowledge/runbooks/rollback-deploy.md:25-26` (pass the 40-hex SHA; `deploy.sh:75,83` compares it).

Files: `.claude/hooks/production-gate.sh`, `.github/workflows/deploy.yml`, `scripts/deploy.sh`,
`scripts/test_hooks_baseline.py`, `scripts/test_deploy_guard.py`, `evals/cases/
gate-blocks-unattended-deploy.yaml`, `evals/cases/gate-ignores-unauthorized-release-file.yaml` (new),
`evals/cases/deploy-refuses-without-approval.yaml`, `knowledge/decisions/{deploy-from-ci,merge-click-is-the-gate}.md`,
`knowledge/runbooks/rollback-deploy.md`, `.sdlc/environments.yaml`, `.sdlc/README.md`, `docs/sdlc/README.md`.

---

## WI-6 `approval-gate` — only a human can flip an artifact to approved

Consensus item 1. Last hook item; restart the session after it lands.

1. New `.claude/hooks/protect-approvals.sh` (A1, ~45 lines): on the edit tools, block a write to
   `work/*/{intent,spec,plan,incident}.md` whose new text sets `status:` to `approved|superseded` or
   a non-empty `approved-by:`/`approved-on:` that differs from the file's current value (so editing an
   already-approved plan's deviations log still passes); on Bash, block `approve.py` invocations,
   `env -u CLAUDECODE`/`unset CLAUDECODE`/`CLAUDECODE=` assignments, and any write candidate under
   `work/` naming an artifact when the command mentions approval. The unlock never applies.
2. Wire it after `protect-tests.sh` in both matchers of `.claude/settings.json:13,22`,
   `docs/sdlc/templates/claude-settings.json:10,19`, and `.gemini/settings.json` after line 10 as
   `{ "name": "sdlc-protect-approvals", "type": "command", "command": "bash .claude/hooks/protect-approvals.sh" }`.
   `scripts/test_gemini_wiring.py:76-83` requires only the four existing hooks; `adopt.sh:181`
   `copy_tree ".claude/hooks"` picks the file up. Check `scripts/check_plugin_manifest.py` for a hook
   enumeration (`scripts/checks/plugin-manifest.sh:10`) and add the path if it lists hooks.
3. `require-plan.sh` after `:20`: `BY="$(fm_value "$PLAN" approved-by)"; ROLE="$(artifact_role
   plan.md)"; approver_has_role "$BY" "${ROLE:-tech-lead}" || block …` (A1). Consequence: every
   fixture with `status: approved` and no `approved-by` blocks; WI-1 already updated them.
4. Tests: new `scripts/test_protect_approvals.py` (builders from `test_bash_plan_gates.py:21-52`;
   fixture `work/foo/intent.md` with `status: draft`): the eight block cases and six allow cases in A1,
   including unlock-set-still-blocks. `scripts/test_hooks_baseline.py::RequirePlanHook`
   (`approved-by: claude` blocks; `someone-else` blocks; approvers file missing blocks;
   `"@LuisSiviero"` allows).
5. Evals: `hook-blocks-agent-approval.yaml` (new); `approve-refuses-in-agent-session.yaml` gains the
   Bash-hook line.
6. Docs: `knowledge/decisions/human-only-approvals.md` (new; add to the hand-kept
   `knowledge/decisions/index.md`), `docs/sdlc/rules/10-hard-rules.md:16` (rule 3 names the approval
   fields), `docs/sdlc/README.md:95,107`, `docs/sdlc/rules/00-chain.md:21-22`.

Files: `.claude/hooks/protect-approvals.sh` (new), `.claude/hooks/require-plan.sh`,
`.claude/settings.json`, `docs/sdlc/templates/claude-settings.json`, `.gemini/settings.json`,
`scripts/check_plugin_manifest.py` (if needed), `scripts/test_protect_approvals.py` (new),
`scripts/test_hooks_baseline.py`, `evals/cases/hook-blocks-agent-approval.yaml` (new),
`evals/cases/approve-refuses-in-agent-session.yaml`, `knowledge/decisions/human-only-approvals.md` (new),
`knowledge/decisions/index.md`, `docs/sdlc/rules/{00-chain,10-hard-rules}.md`, `docs/sdlc/README.md`,
`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`.

---

## WI-7 `band-detector` — the detector sees the breach it exists for

Consensus item 6.

1. `scripts/detect_bands.py` (47 lines): `side()` (`:19-23`) treats `s == 0` with `x != m` as beyond
   every band; `detect()` (`:25-36`) uses a trailing baseline (the `window` points preceding each
   tested point), tests every point after the first `window` and reports the highest tier seen, adds
   the fourth Western Electric rule (8 consecutive on one side → `"drift"`, mapped to the 1σ action);
   `--window < 2`, NaN or non-numeric input → message and exit 2 (not a traceback). Docstring `:5-9`
   updated.
2. `scripts/github_metrics.py`: `pr_cycle_series(prs, days)` filters `merged_at` to the window; the
   fetch at `:158` adds `&sort=updated&direction=desc`; `ci_failure_series` counts `timed_out` and
   `startup_failure` as failures. `monitoring/bands.yaml:5` adds `--workflow sdlc-gate.yml` so the
   bands and review jobs leave the denominator; `:13` points at `work/sdlc-kit-phase-1/decisions.md`.
3. `.github/workflows/bands.yml`: new `scripts/bands_config.py` (stdlib, unit-tested) prints each
   metric's `source`, `tools`, `window` from `monitoring/bands.yaml` as JSON; the matrix is built from
   it (`:35-42` hard-copy removed); `--window` (`:61`) comes from the file (set `window: 14` there and
   say so in the docs); before `gh issue create` (`:105`, `:130`) search for an open `[band] <metric>
   breached` issue and comment instead; upload `monitoring/series/*.txt` as an artifact; the prompt at
   `:91` drops "recent commits" or the 2σ tool list gains `Bash(git log *)`.
4. Tests: `scripts/test_detect_bands.py` (flat baseline then spike → `3sigma`; downward breach; drift
   rule; window 0 → exit 2; NaN → exit 2; an earlier 3σ point in the tail is reported).
   `scripts/test_github_metrics.py` (`--days` filters PRs; end-to-end tests assert the expected tier,
   not `in (0, 3)`). `scripts/test_bands_config.py` (new).
5. Eval: `bands-detects-spike-after-flat-baseline.yaml` (`evals/README.md:6` requires one per gate).
6. Docs: `knowledge/metrics/ci-test-failure-rate.md:4,29,38,49`, `pr-cycle-time-hours.md:4,29,38,48`
   (window 14, trailing, 3σ = diagnose only in this phase), `docs/sdlc/README.md:38,83,86,106`,
   `docs/sdlc/metrics.md:11,27`, `docs/sdlc/rules/20-verifying.md` (the CLAUDE.md line 40 source names
   `github_metrics.py`).

Files: `scripts/detect_bands.py`, `scripts/github_metrics.py`, `scripts/bands_config.py` (new),
`scripts/test_detect_bands.py`, `scripts/test_github_metrics.py`, `scripts/test_bands_config.py` (new),
`monitoring/bands.yaml`, `.github/workflows/bands.yml`, `evals/cases/bands-detects-spike-after-flat-baseline.yaml` (new),
`knowledge/metrics/{ci-test-failure-rate,pr-cycle-time-hours}.md`, `docs/sdlc/README.md`,
`docs/sdlc/metrics.md`, `docs/sdlc/rules/20-verifying.md`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`.

---

## WI-8 `adopter-first-hour` — a fresh install works

Consensus item 7. Depends on WI-3, WI-5, WI-6.

1. `scripts/adopt.sh:195-199` copy list: add `approve.py`, `hooktest.py`, `github_metrics.py`,
   `bands_config.py`, `deploy.sh`; `:207` add `deploy.yml`, `bands.yml`; copy `.gitignore`; copy a
   new `docs/sdlc/github-setup.md` (the checklist from `docs/sdlc/spikes/pr-review-identity.md:71-86`
   with the plan-check note first, plus the `control-plane-approved` label and "sdlc-gate runs only on
   pull_request").
2. `:180` existing `.claude/settings.json`: merge the `hooks` entries and missing `permissions` keys
   with `python3 -c` (stdlib `json`; append hook entries whose `command` is absent) and print
   `merged:`; on parse failure print a loud warning. Never silent.
3. `:241` placeholder: `VERIFY_CMDS="sh -c 'echo TODO(adopter): set VERIFY_CMDS …; exit 1'"` so
   verify is red until set (what `knowledge/decisions/adopt-script.md:56-60` already claims).
4. Identity: `adopt.sh` rewrites `luissiviero` to `<your-github-handle>` in the copied
   `.sdlc/approvers.yaml` and `.github/CODEOWNERS` (same mechanism as the `VERIFY_CMDS` rewrite);
   Next steps step 0 says to replace it.
5. `work/_example` in the target: rewrite to `status: in-review`, empty `approved-by`/`approved-on`,
   and a `## Files that change` listing exactly the paths `adopt.sh` copied, so the install PR passes
   the chain check under `_example` without globs and the plan gate is closed until the adopter
   approves (the copied `approve.py` now works). The kit's own `work/_example` stays approved.
6. Context file: `adopt.sh` writes the target's `docs/sdlc/rules/00-chain.md` with a neutral first
   paragraph and seeds `CLAUDE.md` with `## Commands` / `## Architecture` stubs outside the markers
   (`gen_context_files.py:12-15` preserves them); Next steps step 2 becomes "fill those sections".
7. `:215-218`: write minimal `knowledge/*/index.md` files for the target instead of copying the kit's
   (no dangling links).
8. `--force` (`:235`): preserve `VERIFY_CMDS`, `PLAN_REQUIRED_PATHS` and the handle when they differ
   from the kit defaults; print `differs from kit:` for existing files that differ even without
   `--force`. Add `--help`/`-h` (`:46`).
9. Tests in `scripts/test_adopt.py` (scenario pattern `:107-224`): `preexisting_settings_json`
   (merged, hooks present), `approve_works` (copied `approve.py --as <handle>` from a shell without
   `CLAUDECODE` → 0, chain PASS), `install_commit_chain_passes`, `placeholder_verify_is_red`,
   `handle_rewritten`, `help_flag`; update `SAMPLE_FILES` (`:16-45`) and `:307` (template equality
   only when no file pre-existed).
10. Docs: `knowledge/decisions/adopt-script.md:56-62,74-95`, `docs/sdlc/README.md:130-142`,
    `docs/sdlc/spikes/pr-review-identity.md:71` (pointer to the new doc), the Next steps heredoc
    (`adopt.sh:283-299`).

Files: `scripts/adopt.sh`, `scripts/test_adopt.py`, `docs/sdlc/github-setup.md` (new),
`docs/sdlc/spikes/pr-review-identity.md`, `knowledge/decisions/adopt-script.md`, `docs/sdlc/README.md`,
`evals/cases/adopt-is-idempotent.yaml`.

---

## WI-9 `agent-evals` — evals test the agent, and can go red

Consensus item 8.

1. Five `kind: skill` cases under `evals/cases/` (format `skill-intent-does-not-self-approve.yaml`;
   runner reads `kind`, `prompt`, `allowed_tools`, `check` at `run_evals.sh:53-76`), each against a
   temp copy of `work/_example` with a unique slug and cleanup in `check`:
   `skill-spec-flags-concerns`, `skill-plan-names-files-and-proof`, `skill-fix-leaves-tests-alone`
   (`allowed_tools: Read,Edit,Bash(python3 -m unittest *)`), `hook-refuses-planted-key` (a Write with
   an `AKIA…` string is refused, file unchanged), `skill-incident-names-an-eval`.
2. `scripts/run_evals.sh`: `--require-claude` (a skipped prompt case counts as a failure at `:72,79`).
   `.github/workflows/agent-evals.yml:26-42`: nightly runs with `--require-claude` (expired credential
   → red); `:8` path filter adds `docs/sdlc/rules/**`, `docs/sdlc/templates/**`, `GEMINI.md`,
   `AGENTS.md`, `.gemini/**`, `.claude-plugin/**`. Skill cases stay nightly-only (never hand the token
   to PR-head code); `evals/README.md` says so.
3. `evals/README.md:3-9`: `hook-*`/`gate-*`/`chain-*`/`ci-*` are deterministic gate tests;
   `skill-*` are the playbook's evals; adopters need 20 to 50 of the latter.
4. Tests: `scripts/test_run_evals.py` (`--require-claude` fails on skip).

Files: five new `evals/cases/*.yaml`, `scripts/run_evals.sh`, `scripts/test_run_evals.py`,
`.github/workflows/agent-evals.yml`, `evals/README.md`, `docs/sdlc/README.md:104`.

---

## WI-10 `delegation-boundary` (existing draft intent) — decide provisionally

Consensus item 9. The owner answers the four open questions in `work/delegation-boundary/intent.md`
first; spec and plan are short.

1. `knowledge/decisions/one-writer-until-ledger.md` (new): one writer per work item; subagents read
   only; expires when the Phase 2 cost ledger exists or on a named date; names the measurement that
   flips it; notes the hooks match tool calls, not identity, so a writing subagent would be
   hook-equivalent (the risk is rule 2 checkability and the pilot's silent-failure rate).
2. `docs/sdlc/spikes/prompt-surfaces.md` §2.6 and `build-stage-from-claude-agents.md` §2/§3.1 each
   gain an "overruled/confirmed by …, <date>" line; `docs/sdlc/phase-2-roadmap.md` item 1b.
3. `docs/sdlc/rules/40-claude-only.md`: one sentence. `knowledge/decisions/index.md`: add this record
   and the missing `adopt-script.md` entry.

Files: `work/delegation-boundary/{intent,spec,plan,log}.md`, `knowledge/decisions/one-writer-until-ledger.md`
(new), `knowledge/decisions/index.md`, `docs/sdlc/spikes/{prompt-surfaces,build-stage-from-claude-agents}.md`,
`docs/sdlc/phase-2-roadmap.md`, `docs/sdlc/rules/40-claude-only.md`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`.

---

## WI-11 `docs-reconcile` — the docs say what the code does

Consensus items 10 and 11; whatever WI-1..10 did not already correct.

1. `docs/sdlc/README.md`: rows 35, 103, 112 (no branch protection on this plan: "merge click");
   line 27 (spec pass is not automated); line 137 ("fill the sections outside the generated block");
   line 142.
2. `docs/sdlc/rules/index.md:10-11` (order is `(order, filename)`; the real BEGIN marker text);
   `docs/sdlc/lessons.md:11` (a Markdown link so `check_okf.py` validates it);
   `knowledge/lessons/index.md:11-13` and `.claude/skills/sdlc-incident/SKILL.md` (one destination:
   the skill writes `knowledge/lessons/<slug>.md`; drop the "appends a row" claim; step 2's tier
   wording matches `bands.yaml`); `docs/sdlc/phase-2-roadmap.md:116-117` (mark what WI-7/WI-9 did);
   `docs/sdlc/spikes/gemini-parity.md:83` (insurance until a Gemini CLI account exists).
3. OKF freeze and honest timestamps: a one-off (not committed) script sets each `docs/`+`knowledge/`
   doc's `timestamp` to `git log -1 --format=%cI -- <file>`; `docs/sdlc/okf-pairing.md` records "no
   new OKF directories until lessons/ or services/ has content".
4. `.gitattributes`: `*.md`, `*.py`, `*.yml`, `*.yaml` `text eol=lf` (CLAUDE.md line 71 lesson).
5. Lessons: the five CLAUDE.md lessons (lines 68-72) become `knowledge/lessons/<name>.md` each; a
   one-line pointer list stays in CLAUDE.md and is added to the shared fragment so GEMINI.md gets it
   (`knowledge/decisions/one-rule-source.md:57-58` lists this as undone).

Files: `docs/sdlc/README.md`, `docs/sdlc/rules/{index,00-chain,30-conventions}.md`,
`docs/sdlc/lessons.md`, `knowledge/lessons/index.md`, five new `knowledge/lessons/*.md`,
`.claude/skills/sdlc-incident/SKILL.md`, `docs/sdlc/phase-2-roadmap.md`,
`docs/sdlc/spikes/gemini-parity.md`, `docs/sdlc/okf-pairing.md`, `.gitattributes`, `CLAUDE.md`,
`GEMINI.md`, `AGENTS.md`, plus every `docs/`+`knowledge/` file whose timestamp is rewritten (the list
goes in the plan's deviations log).

---

## Verification (per PR, and once at the end)

- `python3 scripts/run_tests.py` → `Ran N tests … OK`; `scripts/verify.sh` → `VERIFY: PASS (<sha>)`;
  `python3 scripts/check_artifact_chain.py --base origin/main --slug <slug>` → `CHAIN: PASS`;
  `scripts/run_evals.sh` → `EVALS: N pass, 0 fail, …`; `python3 scripts/check_okf.py` → `0 warnings`;
  `gen_context_files.py --check` and `gen_index.py --check` clean; `bash -n .claude/hooks/*.sh`.
- Re-run this session's two adversarial tables (scratchpad `bypass_table.md`, and the
  production-gate table) through `scripts/hooktest.py`: every row a work item claims to close shows
  `BLOCK` or `ask`; every residual is listed in `bash-write-guard.md`.
- Fresh-adopter walkthrough after WI-8: `adopt.sh --with-hooks` into a temp git repo; copied
  `approve.py` from a plain shell → 0; `verify.sh` red on the placeholder, green with
  `VERIFY_CMDS="true"`; chain check on the install commit → PASS; Edit `src/app.py` blocked until
  `_example` is approved.
- Detector after WI-7: `python3 scripts/detect_bands.py --series 0,0,…(30 zeros),1` → `3sigma`, exit 3.
- After WI-6: in a fresh session, an Edit flipping `work/x/intent.md` to `status: approved` is blocked,
  and `python3 scripts/approve.py …` from Bash is blocked, while the owner's shell approval still works.

---

## Appendix: hook and gate designs (verified against the live files by the design agent)

### A1. `protect-approvals.sh` and the approver checks

```bash
#!/usr/bin/env bash
# Only a human approves. An agent may draft, revise and flip an artifact to in-review, but may
# never set `status: approved|superseded`, `approved-by:` or `approved-on:` on
# work/<slug>/{intent,spec,plan,incident}.md, nor run scripts/approve.py. The human unlock
# (SDLC_CONTROL_PLANE_UNLOCK) never applies here.
. "$(dirname "$0")/_lib.sh"
ARTIFACT_RE='^work/[^/]+/(intent|spec|plan|incident)\.md$'
APPROVE_PY_RE='(^|[/[:space:]])approve\.py([[:space:]]|$)'
CLAUDECODE_RE='(env[[:space:]]+(-u|--unset)[[:space:]]+CLAUDECODE|unset[[:space:]]+CLAUDECODE|(^|[[:space:];&|])CLAUDECODE=)'
check_approval_fields() {  # <repo-relative path> <new text> <where>
  local R="$1" new="$2" where="$3" ns nb no cs cb co
  printf '%s' "$R" | grep -Eq "$ARTIFACT_RE" || return 0
  ns="$(printf '%s\n' "$new" | fm_value - status any)"
  nb="$(printf '%s\n' "$new" | fm_value - approved-by any)"
  no="$(printf '%s\n' "$new" | fm_value - approved-on any)"
  cs="$(fm_value "$ROOT/$R" status)"; cb="$(fm_value "$ROOT/$R" approved-by)"; co="$(fm_value "$ROOT/$R" approved-on)"
  case "$ns" in approved|superseded) [ "$ns" = "$cs" ] || block "'$R' would become status: $ns$where. Only a human approves: ask them to run scripts/approve.py from their own shell, then wait.";; esac
  [ -n "$nb" ] && [ "$nb" != "$cb" ] && block "'$R' would set approved-by: $nb$where. Only a human sets approved-by."
  [ -n "$no" ] && [ "$no" != "$co" ] && block "'$R' would set approved-on: $no$where. Only a human sets approved-on."
  return 0
}
if [ -n "$FILE" ]; then
  NEW="$(printf '%s' "$INPUT" | jq -r '(.tool_input.content // "") + "\n" + (.tool_input.new_string // "") + "\n" + ([.tool_input.edits[]?.new_string] | join("\n")) + "\n" + (.tool_input.new_source // "")')"
  check_approval_fields "$(rel "$FILE")" "$NEW" ""; exit 0
fi
[ -z "$CMD" ] && exit 0
printf '%s' "$CMD" | grep -Eq "$APPROVE_PY_RE" && block "scripts/approve.py is run by a human from their own shell, never from an agent session."
printf '%s' "$CMD" | grep -Eq "$CLAUDECODE_RE" && block "unsetting CLAUDECODE is how an agent impersonates a human; not allowed."
[ "${BASH_WRITE_GUARD:-1}" = 1 ] || exit 0
WHERE=" (write detected in a Bash command)"
while IFS= read -r CAND; do
  [ -z "$CAND" ] && continue
  printf '%s' "$CAND" | grep -Eq "$ARTIFACT_RE" || continue
  check_approval_fields "$CAND" "$CMD" "$WHERE"
  printf '%s' "$CMD" | grep -Eiq 'approved|supersed' && block "'$CAND' is a chain artifact and the command mentions approval$WHERE. Use Write/Edit for drafts; approvals are a human act."
done < <(bash_write_candidates "$CMD" "work")
exit 0
```

Shared helpers in `_lib.sh` (awk, ~2 ms; not python: it imports `check_artifact_chain`, which runs
`git rev-parse` at import, and on the owner's Windows PC `python3` may be the Store stub):

```bash
fm_value() {  # <file|-> <key> [any]  -> value with CR, trailing ` # comment`, quotes stripped; casefolded
  awk -v k="$2" -v any="${3:-}" '
    { sub(/\r$/, "") }
    !any && /^---[[:space:]]*$/ { c++; if (c == 2) exit; next }
    (any || c == 1) && index($0, k ":") == 1 {
      v = substr($0, length(k) + 2)
      sub(/^[[:space:]]+/, "", v); sub(/[[:space:]]+#.*$/, "", v); if (v ~ /^#/) v = ""
      sub(/[[:space:]]+$/, "", v)
      if (length(v) >= 2 && substr(v, 1, 1) == substr(v, length(v), 1) && (substr(v, 1, 1) == "\"" || substr(v, 1, 1) == "\047")) v = substr(v, 2, length(v) - 2)
      print tolower(v); exit }' "$1" 2>/dev/null
}
artifact_role() {  # <artifact> -> role under `artifacts:` in APPROVERS_FILE
  awk -v a="$1" '{ sub(/\r$/, "") } /^[A-Za-z]/ { top = $0; sub(/:.*/, "", top) }
    top == "artifacts" && index($0, "  " a ":") == 1 { v = $0; sub(/^[^:]*:[[:space:]]*/, "", v); sub(/[[:space:]]*#.*$/, "", v); print v; exit }' \
    "$ROOT/${APPROVERS_FILE:-.sdlc/approvers.yaml}" 2>/dev/null
}
approver_has_role() {  # <handle> <role> -> 0 when listed under roles.<role> and not in never-approve; missing file fails closed
  local f="$ROOT/${APPROVERS_FILE:-.sdlc/approvers.yaml}" h="$1"
  h="${h//\"/}"; h="${h//\'/}"; h="${h#"${h%%[![:space:]]*}"}"; h="${h%%[[:space:]]*}"; h="${h#@}"; h="${h,,}"
  [ -n "$h" ] && [ -f "$f" ] || return 1
  awk -v role="$2" -v h="$h" '
    function norm(x) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", x); gsub(/^["\047]|["\047]$/, "", x); sub(/^@/, "", x); return tolower(x) }
    function has(list,   n, a, i) { sub(/^[[:space:]]*\[/, "", list); sub(/\][[:space:]]*(#.*)?$/, "", list)
      n = split(list, a, ","); for (i = 1; i <= n; i++) if (norm(a[i]) == h) return 1; return 0 }
    { sub(/\r$/, "") }
    /^[A-Za-z]/ { top = $0; sub(/:.*/, "", top) }
    /^never-approve:/ { v = $0; sub(/^never-approve:/, "", v); if (has(v)) bad = 1 }
    top == "roles" && index($0, "  " role ":") == 1 { v = $0; sub(/^[^:]*:/, "", v); if (has(v)) ok = 1 }
    END { exit (ok && !bad) ? 0 : 1 }' "$f"
}
```

`require-plan.sh` after line 20:

```bash
  BY="$(fm_value "$PLAN" approved-by)"; ROLE="$(artifact_role plan.md)"; ROLE="${ROLE:-tech-lead}"
  approver_has_role "$BY" "$ROLE" || block "'$R' needs an approved plan$where: work/$SLUG/plan.md says approved-by '$BY', who is not a $ROLE in ${APPROVERS_FILE:-.sdlc/approvers.yaml} (or the file is missing). A listed human must approve with scripts/approve.py."
```

`test_protect_approvals.py` cases. Block (rc 2): Edit `new_string` `status: approved`; Edit
`approved-by: luissiviero`; Write of a template-shaped file with `status: superseded`; MultiEdit whose
second edit sets `approved-on: 2026-09-04`; Bash `python3 scripts/approve.py foo intent.md --as
luissiviero`; Bash `env -u CLAUDECODE python3 scripts/approve.py foo plan.md`; Bash `sed -i
's/draft/approved/' work/foo/intent.md`; Bash heredoc writing `status: approved` into
`work/foo/plan.md`. Allow (rc 0): Edit `status: in-review`; Write of a draft intent copied verbatim
from the template; Edit on an already-approved plan whose `new_string` repeats the unchanged values;
Edit to `docs/x.md` containing `status: approved`; Bash `cat work/foo/plan.md`; unlock set + Edit to
`approved` still rc 2.

### A2. Decision log, visibility, and CI trailer detection

`_lib.sh` after line 50:

```bash
{ IFS= read -r CWD; IFS= read -r SESSION_ID; } < <(printf '%s' "$INPUT" | jq -r '(.cwd // ""), (.session_id // "")')
CWD="${CWD//\\//}"
```

after line 78:

```bash
DECISION_LOG="$ROOT/.sdlc/hook-decisions.log"
log_decision() {  # <verdict> <detail>; never fails the hook
  { printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$(basename "$0")" "${TOOL:-?}" "${SESSION_ID:-?}" "$2" >> "$DECISION_LOG"; } 2>/dev/null || true
}
block() { log_decision block "$1"; printf 'SDLC hook blocked this action: %s\n' "$1" >&2; exit 2; }
ask()   { log_decision ask "$1"; jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'; exit 0; }
```

`protect-paths.sh`: `UNLOCKED=()`; the unlock branch keeps its stderr line, adds `log_decision unlock
"$R$where"; UNLOCKED+=("$R")`; both `exit 0` paths (`:37`, `:48`) call:

```bash
finish() {
  [ "${#UNLOCKED[@]}" -gt 0 ] || exit 0
  jq -n --arg m "SDLC: control-plane unlock used: wrote ${UNLOCKED[*]} (logged in .sdlc/hook-decisions.log)" '{systemMessage:$m}'
  exit 0
}
```

Claude Code's hooks reference (fetched by the design agent) lists `systemMessage` as a universal
top-level output field shown to the user, and `cwd` as a common input field. Whether every front end
renders it for an exit-0 PreToolUse hook is unverified, so the log file is the primary channel. No
`permissionDecision: allow` is emitted (that would suppress the tool's own permission prompt).

`check_control_plane.sh` lines 35 and 76-79:

```bash
: "${AGENT_BRANCH_PREFIXES:=claude/ kit/ spike/}"   # also a key in .sdlc/config.env (config wins)
AGENT_TRAILER_RE='^(Co-Authored-By:.*Claude|Claude-Session:)'
has_agent_trailer() { git -C "$ROOT" log --format=%B "${BASE}..HEAD" 2>/dev/null | grep -Eiq "$AGENT_TRAILER_RE"; }
agent_authored=0
if [ "$SDLC_PR_AUTHOR_TYPE" = "Bot" ] || is_agent_branch "$SDLC_PR_HEAD_REF" || has_agent_trailer; then agent_authored=1; fi
```

Evidence: 54 of 95 commits carry `Co-Authored-By: Claude`, 24 carry `Claude-Session:`; the kit's PR
branches are `kit/*` and `spike/*`. `sdlc-gate.yml:19` checks out with `fetch-depth: 0`.

### A3. `protect-tests.sh` existence check (line 22)

```bash
    case "$R" in $g|*/$g)
      [ -e "$ROOT/$R" ] || return 0   # a NEW test (the failing reproduction) is allowed
      block "'$R' is an existing test file and work/$SLUG/plan.md is kind: fix$where. Fix the code, not the test. If the test itself is wrong, say so and stop; a human changes it." ;;
```

Deletes and renames need no code here: WI-4's arms emit `rm`/`unlink`/`git rm`/`git mv`/`mv` operands
as candidates, and an existing test being removed is `-e` at hook time.

### A4. `bash_write_targets` / `bash_write_candidates`

Redirections (replaces `_lib.sh:102-108`):

```bash
  s="$(printf '%s' "$cmd" | sed -E 's/[0-9]*>&[0-9-]+//g; s/[0-9]*<&[0-9-]+//g; s/>&/\&>/g')"
  while IFS= read -r t; do
    t="${t#*>}"; t="${t#[>|]}"; t="${t#"${t%%[![:space:]]*}"}"; out+=("$t")
  done < <(printf '%s' "$s" | grep -Eo '(&|[0-9])?>(>|\|)?[[:space:]]*[^[:space:]|;&<>()]+')
```

Pre-split (replaces line 114; `)`/`}` join the separator list at line 120):

```bash
  s="${cmd//$'\n'/ ; }"; s="${s//;/ ; }"; s="${s//&&/ && }"
  s="${s//(/ ( }"; s="${s//)/ ) }"; s="${s//\{/ { }"; s="${s//\}/ } }"
  s="${s//|/ | }"; s="${s// |  | / || }"
  case "$-" in *f*) noglob=1;; *) set -f;; esac
  # shellcheck disable=SC2206
  toks=( $s )
```

New arms (the skip class becomes `-*|'<'*|'>'*|'&'*`):

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

Step 4 (replaces `:191-198`): strip all quotes; `$PWD/`→`${CWD:-$ROOT}/…`; `~/`→`$HOME/…`; then the
existing `''|/dev/*|\$*|*'${'*` drop.

`bash_write_candidates`: `base="$(canon "$CWD")"` when `CWD` is set; each candidate resolved against
`base`, against ROOT (as before), and against each `cd` target resolved from `base`. `rel()` becomes
`canon "$1" "${CWD_CANON:-}"`; `protect-paths.sh:36` switches `canon "$FILE"` → `rel "$FILE"`.
`FILE` at `:49`: `.tool_input.file_path // .tool_input.notebook_path // empty`.

Block tests (`test_protect_paths_bash.py`, rc 2): `true; cp /tmp/f .sdlc/config.env`;
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
Allow tests (rc 0): `cmd >/dev/null 2>&1`; `ls 2>/dev/null`; `make test 2>&1 | tee /tmp/log`;
`rm -rf /tmp/build`; `mv /tmp/a /tmp/b`; `chmod +x /tmp/x.sh`; `git checkout -b kit/x`;
`git rm --cached /tmp/x`; `sort .sdlc/config.env`; payload `cwd=/tmp` + `echo x > out.txt`;
`echo "a > b"` (existing test, still allows). Existing tests pin `scripts/verify.sh 2>&1 | tail -3` as
allowed (`test_protect_paths_bash.py:132-133`, `test_bash_plan_gates.py:84`); the sed keeps them green.

### A5. Release gate

`production-gate.sh:92-95`:

```bash
  AUTH="$ROOT/.sdlc/release-authorizations/$SHA"
  if [ -f "$AUTH" ]; then
    BY="$(fm_value "$AUTH" approved-by any)"
    if approver_has_role "$BY" release-manager; then log_decision allow "release authorization $SHA by $BY"; exit 0; fi
    log_decision reject "release authorization $SHA names '$BY', not a release-manager"
  fi
```

`protect-paths.sh` `check_target`, before the `PROTECTED_PATHS` test:

```bash
  case "$R" in
    .sdlc/release-authorizations|.sdlc/release-authorizations/*|.sdlc/approvers.yaml|.sdlc/hook-decisions.log)
      block "'$R' is a human-only file$where. The control-plane unlock never covers it; the release manager / repo owner writes it from their own shell.";;
  esac
```

`DEPLOY_RE` and friends (line 26 and a new `is_deploy()` used at line 90):

```bash
DEPLOY_RE="$BOUND"'(kubectl…|cap[[:space:]]+production|([^[:space:]]*/)?deploy\.sh|gh[[:space:]]+(release[[:space:]]+create|workflow[[:space:]]+run|pr[[:space:]]+merge))'
DEPLOY_WORD_RE="$BOUND"'([^[:space:]]*/)?deploy([[:space:]]|$)'
PROD_RE='(^|[^[:alnum:]_])(prod|production)([^[:alnum:]_-]|$)'
GH_API_RE="$BOUND"'gh[[:space:]]+api[[:space:]]+[^;&|]*(releases|merges|dispatches)'
GH_MUT_RE='(-X|--method)[[:space:]=]*(POST|PUT|PATCH|DELETE)|(^|[[:space:]])(-f|-F|--field|--raw-field|--input)([[:space:]]|=)'
is_deploy() {
  printf '%s' "$1" | grep -Eiq "$DEPLOY_RE" && return 0
  printf '%s' "$1" | grep -Eiq "$DEPLOY_WORD_RE" && printf '%s' "$1" | grep -Eiq "$PROD_RE" && return 0
  printf '%s' "$1" | grep -Eiq "$GH_API_RE" && printf '%s' "$1" | grep -Eiq "$GH_MUT_RE" && return 0
  return 1
}
```

Ask: `make deploy ENV=production`, `./scripts/deploy.sh production`, `gh workflow run deploy.yml -f
environment=production`, `./deploy production`, `gh release create v1.0`, `gh pr merge 5 --squash`,
`gh api -X POST repos/o/r/merges -f base=main`. Allow: `deploy --help`, `echo deployment notes`,
`gh pr view 12`, `gh api repos/o/r/releases/latest`, `git log --grep=deploy`.

`scripts/deploy.sh` between lines 75 and 79:

```bash
AUTH="$ROOT/.sdlc/release-authorizations/$SHA"
if [ -z "${RELEASE_APPROVAL:-}" ] && [ -f "$AUTH" ]; then
  BY="$(sed -n 's/^approved-by:[[:space:]]*//p' "$AUTH" | head -1 | sed 's/[[:space:]]*#.*$//')"
  if python3 "$ROOT/scripts/approvers.py" --has-role release-manager "$BY" >/dev/null 2>&1; then
    RELEASE_APPROVAL="$SHA"
  else
    echo "deploy refused: $AUTH names '$BY', who is not a release-manager in .sdlc/approvers.yaml." >&2; exit 1
  fi
fi
```

`deploy.yml:55`: `RELEASE_APPROVAL: ${{ secrets.RELEASE_APPROVAL }}`.

### A6. Front matter

`scripts/check_artifact_chain.py`:

```python
def _fm_value(raw):
    v = raw.strip()
    if v.startswith("#"):
        return ""
    v = re.split(r"\s+#", v, 1)[0].rstrip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1].strip()
    return v

def front_matter_text(text):
    fm = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.lstrip().startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = _fm_value(v)
    return fm
```

Accepted: a title `Fix #12 crash` reads as `Fix` (YAML reads it the same way); URLs with `#anchor` are
untouched (no whitespace before `#`). `approve.py:set_front_matter` replaces whole lines, so it needs
no change; the ledger `<from>` field now comes from the cleaned status.

Template lines, `docs/sdlc/templates/intent.md:7-12`:

```
# status: draft | in-review | approved | superseded
status: draft
author: <originator name and team>
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by:
approved-on:
# supersedes: previous intent id, if any
supersedes:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
```

`docs/sdlc/templates/plan.md:7-10`:

```
# status: draft | in-review | approved | superseded  (require-plan.sh refuses code edits until approved)
status: draft
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: feature
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by:
```

`spec.md:9,11` and `incident.md:8` get the same treatment.
