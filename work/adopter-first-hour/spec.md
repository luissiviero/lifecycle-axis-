---
type: sdlc/spec
id: adopter-first-hour
title: A fresh install of the kit breaks in the first hour; the adopter path must work end to end
description: Requirements and design for adopt.sh: complete copy list, settings merge, red placeholder verify, placeholder handle, in-review example with an explicit file list, project-shaped context file, clean knowledge indexes, --force preservation, --help, and a GitHub-side checklist.
stage: design
status: in-review
reads: intent.md
approved-by:
approved-on:
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Transcribed from the approved 2026-09-04 implementation plan (docs/sdlc/handoff/PLAN.md on branch claude/session-handoff), section WI-8, after reading adopt.sh, test_adopt.py, check_artifact_chain.py's mode logic and verify.sh's command loop; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01Te8oN2GdvRupSixH4kjR8Y
tags: [adopt, distribution, first-hour, hooks, settings, approvals, consensus-item-7]
timestamp: 2026-09-05T02:33:32Z
---
# Spec: a fresh install of the kit breaks in the first hour; the adopter path must work end to end

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) complete copy list; (2) settings merged, never silent; (3) placeholder verify is red;
(4) placeholder handle; (5) `_example` in review with an explicit file list, approve-first install passes the
chain; (6) project-shaped context file; (7) clean knowledge indexes; (8) `--force` preservation, drift signal,
`--help`; (9) docs and suite.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | The copy list gains `scripts/{approve.py,hooktest.py,github_metrics.py,bands_config.py,deploy.sh}`, `.github/workflows/{deploy.yml,bands.yml}`, `.gitignore` and `docs/sdlc/github-setup.md` | 1 | `scripts/test_adopt.py::AdoptScript::test_adopts_expected_files_and_is_executable` with those nine paths added to `SAMPLE_FILES` |
| R-2 | With `--with-hooks` and an existing parsable `.claude/settings.json`, the file is merged: every hook entry of the template whose `command` is absent is appended under its event and matcher (a matcher group is created when absent); `permissions.deny` and `permissions.allow` are added only when the key is absent; every other key of the adopter's file is kept; stdout has `merged: .claude/settings.json (<n> hook entries added)`. An unparsable file is left untouched and stdout and stderr both carry `WARNING: .claude/settings.json could not be parsed; hooks NOT installed` | 2 | `::test_preexisting_settings_json_is_merged` (adopter's `permissions.allow` and a custom top-level key survive; all six hook scripts present; `merged:` printed; a second run adds `0 hook entries`), `::test_unparseable_settings_json_warns_loudly`; `::test_with_hooks_settings_is_the_kit_template` keeps asserting byte equality for the fresh target |
| R-3 | The placeholder line is `VERIFY_CMDS="echo 'TODO(adopter): set VERIFY_CMDS in .sdlc/config.env (e.g. npm test, pytest, make lint)' && false"`, so `scripts/verify.sh` in a fresh target prints the TODO and ends `VERIFY: FAIL` | 3 | `::test_placeholder_verify_is_red` (verify scenario: last line `VERIFY: FAIL`, `TODO(adopter)` in stdout); `::test_verify_cmds_left_as_placeholder_and_active_set` unchanged |
| R-4 | A freshly copied `.sdlc/approvers.yaml` and `.github/CODEOWNERS` have every `luissiviero` replaced by `<your-github-handle>`; a pre-existing file is not touched | 4 | `::test_handle_rewritten` (`<your-github-handle>` in both; `luissiviero` in neither; `python3 scripts/approvers.py --has-role tech-lead '<your-github-handle>'` in the target exits 0) |
| R-5 | The target's `work/_example/{intent,spec,plan}.md` have `status: in-review` and empty `approved-by`/`approved-on`; `plan.md`'s `## Files that change` is one bullet per path `adopt.sh` wrote (plus `.sdlc/active`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `work/index.md`, `work/_example/index.md`), no globs; `log.md` holds three `(none) -> in-review` lines with actor `adopt.sh`; only when `work/_example/` was freshly copied | 5 | `::test_example_is_in_review_with_explicit_file_list` (statuses, no `*` in the list, every `copy:` path from stdout is listed, ledger parses with three entries) |
| R-6 | In a `git init` target, after replacing the placeholder with `alice`, running the copied approval script `_example intent.md spec.md plan.md --as alice` from an environment without `CLAUDECODE` exits 0; a commit by `alice` on top of an empty base commit passes `check_artifact_chain.py --base <base>` (full mode) and `--base HEAD` | 5 | `::test_approve_works_from_a_plain_shell`, `::test_install_commit_chain_passes` (both `CHAIN: PASS`, no `not listed` line) |
| R-7 | In a fresh target `CLAUDE.md` begins with `# <target dir name>`, `## Commands` and `## Architecture` stubs (each one `TODO(adopter)` bullet) and `## Lessons learned` before the generated block; the target's `docs/sdlc/rules/00-chain.md` first paragraph reads "This repo follows the AI-native SDLC…" with no "starter kit"; a pre-existing `CLAUDE.md` is preserved as today | 6 | `::test_fresh_claude_md_has_project_sections` (`## Commands` index < `BEGIN GENERATED` index; `starter kit` absent from the target's `CLAUDE.md`); `::test_preexisting_claude_md_is_preserved` unchanged; the target's `scripts/checks/context-drift.sh` passes |
| R-8 | `knowledge/index.md` and the five `knowledge/<dir>/index.md` are written minimal (front matter `type: index`, one paragraph, no links to files that are not in the target) instead of copied | 7 | `::test_knowledge_indexes_have_no_dangling_links` (every `](…)` target in each index resolves inside the target); `python3 scripts/check_okf.py` run in the target reports `0 warnings` for `knowledge/` |
| R-9 | `--force` keeps the adopter's `VERIFY_CMDS` and `PLAN_REQUIRED_PATHS` when they differ from both the kit's line and the placeholder/default, and keeps the handle found in the existing `approvers.yaml` when it is not the placeholder, printing `preserved: <key>`; without `--force`, an existing file that differs from the kit prints `skip (exists, differs from kit): <path>` unless `adopt.sh` rewrites that path itself; `--help`/`-h` prints usage to stdout and exits 0 | 8 | `::test_force_preserves_adopter_values`, `::test_differs_from_kit_is_reported`, `::test_help_flag`; `::test_second_run_is_noop_and_only_skips` and eval `adopt-is-idempotent` unchanged in outcome |
| R-10 | `docs/sdlc/github-setup.md` (new, `type: doc`) holds the first-hour order and the GitHub-side checklist; `adopt-script.md`, `docs/sdlc/README.md` §3, the spike's checklist heading and the Next steps heredoc say what the code does; the eval also asserts `--help` exits 0 and a fresh target's verify is red | 9 | `grep -c 'a loud placeholder cannot' knowledge/decisions/adopt-script.md` prints `0`; `python3 scripts/check_okf.py` ends `0 warnings`; `scripts/run_evals.sh --only 'adopt-*'` ends `0 fail`; `::test_next_steps_are_literal_text_not_shell_substitutions` unchanged |
| R-11 | Whole suite green | 9 | `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`; `scripts/run_evals.sh` ends `EVALS: N pass, 0 fail, N skipped`; `python3 scripts/check_artifact_chain.py --base origin/main --slug adopter-first-hour` ends `CHAIN: PASS` |

## Design
### Architecture / data flow
`adopt.sh` keeps its shape: parse flags, resolve `KIT` and `TARGET`, copy a fixed list with `copy_file`/
`copy_tree`, then post-copy steps, then render context files and indexes, then print Next steps. Four things
change in the post-copy stage, all keyed on "was this file freshly copied in this run" so a second run is a
no-op: the identity rewrite, the `_example` rewrite, the context-file seed and the rules-fragment rewrite.
`copy_file` records every path it writes in `COPIED` (newline-separated); the `_example` plan is generated from
that list. The settings merge replaces the plain copy at `:180` when the destination exists.

### Interfaces (APIs, events, schemas) — exact shapes
`adopt.sh`:
- `--help`/`-h` (`:35-58`): `usage` to stdout, exit 0; usage lists every flag.
- `copy_file` (`:118-134`): on `skip (exists)`, when the path is not in `REWRITTEN` and `cmp -s` says the
  target differs from the kit file, print `skip (exists, differs from kit): <rel>` instead; on copy, append
  `rel` to `COPIED`. `REWRITTEN` = `.sdlc/config.env .sdlc/approvers.yaml .github/CODEOWNERS
  docs/sdlc/rules/00-chain.md work/_example/intent.md work/_example/spec.md work/_example/plan.md
  work/_example/log.md`.
- Copy list (`:195-199`): `+ approve.py hooktest.py github_metrics.py bands_config.py deploy.sh`; workflows
  (`:207`): `+ deploy.yml bands.yml`; `copy_file ".gitignore"`; `copy_file "docs/sdlc/github-setup.md"`.
- Settings (`:180`), `--with-hooks` only:
  ```bash
  if [ -e "$TARGET/.claude/settings.json" ] && [ "$FORCE" != true ]; then
    merge_settings "$KIT/docs/sdlc/templates/claude-settings.json" "$TARGET/.claude/settings.json"
  else
    copy_file "docs/sdlc/templates/claude-settings.json" ".claude/settings.json"
  fi
  ```
  `merge_settings <template> <existing>` runs `python3 - "$template" "$existing" <<'PY' … PY` (stdlib
  `json`): load both; for each event in the template's `hooks`, for each group, find the existing group with
  the same `matcher` (absent key counts as equal) or append the group whole; within a found group append each
  hook whose `command` is not already present; add `permissions.deny`/`permissions.allow` when the key is
  missing under `permissions` (creating `permissions` if absent); write back with two-space indent and a
  trailing newline only if something changed; print `merged: .claude/settings.json (<n> hook entries added)`.
  On `json.JSONDecodeError` print `WARNING: .claude/settings.json could not be parsed; hooks NOT installed
  (fix the JSON and rerun adopt.sh --with-hooks)` to stdout and stderr, exit 0, change nothing. `--dry-run`
  prints `merge: .claude/settings.json` and writes nothing.
- Placeholder (`:241`): `NEW_VERIFY_LINE="VERIFY_CMDS=\"echo 'TODO(adopter): set VERIFY_CMDS in
  .sdlc/config.env (e.g. npm test, pytest, make lint)' && false\""` (no `;`: `verify.sh:12` splits
  `VERIFY_CMDS` on `;`).
- Identity: after the copies, for `.sdlc/approvers.yaml` and `.github/CODEOWNERS`, when the path is in
  `COPIED`, `sed -i 's/luissiviero/<your-github-handle>/g'` (via a temp file and `mv`, as the config rewrite
  does); print `set the approver handle to <your-github-handle> in <path>`.
- `_example` rewrite, when `work/_example/intent.md` is in `COPIED`: `python3 - "$TARGET" <<'PY'` sets
  `status: in-review`, `approved-by:`, `approved-on:` (empty) in the three artifacts' front matter; replaces
  the `## Files that change` section body of `plan.md` with one `- <path>` bullet per line of `COPIED` plus
  `.sdlc/active`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `work/index.md`, `work/_example/index.md`, sorted;
  writes `log.md` from the template shape with three lines `- <ts> | <artifact> | (none) -> in-review |
  adopt.sh | 0000000 | installed by scripts/adopt.sh; approve as yourself from your own shell`.
- Context seed: when `$TARGET/CLAUDE.md` does not exist before rendering, write
  ```
  # <basename of TARGET>

  ## Commands
  - TODO(adopter): the verify command and its healthy last line, the test command, the run command

  ## Architecture
  - TODO(adopter): ten lines on how this repo is put together

  ## Lessons learned (append; one line each; delete when a hook makes it impossible)
  -

  ```
  then `gen_context_files.py --root` appends the generated block (`gen_context_files.py:12-15`).
- Rules fragment: when `docs/sdlc/rules/00-chain.md` is in `COPIED`, replace its first paragraph
  (`This repo is a starter kit … follow the rules below.`) with `This repo follows the AI-native SDLC: six
  non-linear stages (Plan → Design → Build → Test → Deploy → Maintain) connected by committed Markdown
  artifacts. The sections above the generated block are this project's own; \`docs/sdlc/README.md\`
  explains the stages; the rules below are generated from \`docs/sdlc/rules/\`.`
- Knowledge indexes (`:215-218`): `write_index <rel> <title> <description> <paragraph>` writes the file only
  when absent (prints `copy:`/`skip (exists):` like `copy_file`); six calls, no links to files.
- `--force` (`:235-272`): before the copies, when `--force` and the files exist, capture `VERIFY_CMDS=` and
  `PLAN_REQUIRED_PATHS=` lines from `.sdlc/config.env` and the first handle of `product-owner:` from
  `approvers.yaml`; after the rewrite, restore each captured value that differs from the kit's line and from
  the placeholder/default, printing `preserved: VERIFY_CMDS` (etc.); the handle, when not the placeholder,
  replaces `luissiviero` instead of `<your-github-handle>`.
- Next steps heredoc (`:283-299`): step 0 "replace `<your-github-handle>` in `.sdlc/approvers.yaml` and
  `.github/CODEOWNERS`", step 1 unchanged, step 2 "fill `## Commands` and `## Architecture` in `CLAUDE.md`",
  step 5 "approve `_example` as yourself: `python3 scripts/approve.py _example intent.md spec.md plan.md --as
  <handle>`, commit as yourself, then open the install PR", new step "read `docs/sdlc/github-setup.md`".

`docs/sdlc/github-setup.md` (new; `type: doc`): (1) the first hour in order (handle, approve `_example`,
commit as yourself, install PR, label, merge, `VERIFY_CMDS`); (2) the plan-check note first (Free-plan private
repos get 403 on protection); (3) the checklist from `pr-review-identity.md:72-86` verbatim in substance;
(4) the `control-plane-approved` label (Issues → Labels → New); (5) "`sdlc-gate` runs only on `pull_request`:
a direct push to `main` sees no gate; work by PR"; (6) secrets and the Claude GitHub App for `pr-review.yml`.
`pr-review-identity.md:71` gains one line pointing at the new doc.

`evals/cases/adopt-is-idempotent.yaml`: keeps the two-run check; adds `adopt.sh --help` exits 0 and, in the
adopted temp dir after `git init`, `scripts/verify.sh` ends `VERIFY: FAIL` with `TODO(adopter)` in its output.

### Data and migrations
None. The kit's own `work/_example` stays approved; only the target's copy is rewritten.

### Failure modes and how they surface
- Existing settings file unparsable: warning on both streams, hooks not installed, exit 0 (adoption continues).
- `python3` missing: the merge, the `_example` rewrite and the renderers fail with their own errors, as today.
- `_example` approved before the handle is replaced: the copied `approvers.yaml` lists the placeholder in every
  role, so the approval script accepts `--as '<your-github-handle>'` and the chain check passes on a
  human-authored commit with a visibly fake approver (C1). Step 0 of Next steps and `github-setup.md` put the
  handle replacement first; the placeholder's angle brackets make the slip obvious in any review.
- Install PR before approval: chain check red with the stage-order message; `github-setup.md` step order
  prevents it.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the placeholder handle satisfies every role in the copied `approvers.yaml`, so an adopter who forgets to replace it could approve as `<your-github-handle>` — policy: rule 8 / `human-only-approvals.md` — contradiction? no — owner: luissiviero — resolution: the chain check's commit-author test still holds (an agent cannot commit it), the handle is visibly a placeholder, and step 0 of Next steps and `github-setup.md` say to replace it; a `never-approve` entry for the placeholder would make the fresh target's `_example` unapprovable until edited, which is the same thing said louder — not done, noted for `docs-reconcile`.
- C2: merging into an adopter's `settings.json` writes a file the kit calls control plane — policy: rule 3 (the adopter's `protect-paths.sh` is not yet installed at that moment) — contradiction? no — owner: luissiviero — resolution: `adopt.sh` runs from the adopter's shell, not an agent session; the merge is additive and reported.
- C3: `_example`'s generated file list is long (every copied path) — policy: `/sdlc-plan` "prefer explicit paths" — contradiction? no — owner: luissiviero — resolution: this is the explicit list; the adopter's later items write their own short plans.
- C4: `adopt.sh` grows past 400 lines of bash — policy: none — owner: luissiviero — resolution: the Python snippets stay inline (no new file to copy), each under 40 lines; splitting is `docs-reconcile`'s call if it hurts.

## Open questions carried from intent.md
- Placeholder `<your-github-handle>`? (proposed yes)
- Approve-first install order, no chain-check exemption? (proposed yes)
- `--force` preserves only values that differ from the kit's and the placeholder? (proposed yes)
- Seed `CLAUDE.md` only? (proposed yes)

## Decisions (ADR-style: context → decision → consequences)
- D1: Approve-first rather than exempting the install commit in `check_artifact_chain.py`: an exemption keyed on "first commit" or "all files new" is a hole every later PR could dress up as → the adopter's first PR is red for the minutes between install and approval, and green after one command; `github-setup.md` puts the steps in order.
- D2: `_example`'s plan lists every path `adopt.sh` wrote rather than globs: the chain check's own rule (`sdlc-plan/SKILL.md:10`) and B8's lesson → a long but honest list, generated from the `copy:` lines so it cannot drift from what was installed.
- D3: The settings merge is additive and keyed on `command`: an adopter's own hooks, permissions and other keys are theirs → the kit never removes or reorders an adopter's entries, and a rerun adds nothing (idempotent).
- D4: The placeholder verify command ends `&& false` instead of `sh -c '…; exit 1'`: `verify.sh:12` splits on `;` → one line, no sub-shell, red until replaced.
- D5: `<your-github-handle>` with angle brackets: cannot be a GitHub login, reads as a placeholder in every file, parses as a list item in `approvers.py` → the fresh target is approvable only after a visible edit (C1).
- D6: Knowledge indexes are written minimal, not copied: the adopter's bundle starts empty and the OKF check is honest from day one → the kit's own decisions and metrics are not carried into the target (they describe this repo).
- D7: `--force` preserves three values only: the ones the first-hour report found reset (`VERIFY_CMDS`, `PLAN_REQUIRED_PATHS`, the handle) → everything else follows the documented "overwrite" meaning of `--force`.

## Gotchas found while reading the codebase
- `check_artifact_chain.py:38` exempts `work/`, `docs/`, `monitoring/`, `knowledge/`, `CLAUDE.md`, `REVIEW.md`, `README.md` from the file-list check; the generated list includes them anyway (harmless, complete).
- `check_artifact_chain.py:84-95` reads a bullet up to the first `—` or ` - `; the generated bullets are bare paths.
- `verify.sh:12` splits `VERIFY_CMDS` on `;` before `bash -c`; a placeholder with `;` would run as two commands.
- `test_adopt.py:307-320` asserts the fresh target's settings equal the template byte for byte; the merge path must not touch a freshly copied file.
- `test_adopt.py:255-263` asserts a second run rewrites nothing (mtimes) and prints no `copy:`; every rewrite must be keyed on `COPIED`, and the knowledge index writer must print `skip (exists)` on rerun.
- `gen_context_files.py:12-15`: a markerless existing file keeps its text and gains the block at the end; the seed must be written before the render and must contain no marker line.
- `approvers.py:52-56` parses `[a, b]` by splitting on commas and stripping quotes; `<your-github-handle>` survives; `normalize` strips a leading `@`.
- The copied approval script imports `check_artifact_chain`, which resolves `ROOT` with `git rev-parse` from the script's directory: the target must be a git repository before approving (the test scenario runs `git init` first; `github-setup.md` says so).
- `adopt.sh:275` renders context files on every run; the seed is written only when `CLAUDE.md` is absent, so a rerun is a no-op.
- The `_example` ledger's `sha` column: the target may have no commits; `0000000` matches what the approval script itself writes in that case (`approve.py:94`).

## Not doing
- Copying `scripts/run_tests.py` or the kit's `scripts/test_*.py` (an adopter's tests are their own).
- A `never-approve` entry for the placeholder handle (C1; noted for `docs-reconcile`).
- Merging an existing `.gemini/settings.json` (still `skip (exists)`, now with the differs-from-kit signal).
- Changing this repo's own `.claude/settings.json`, hooks, or `work/_example`.
