---
type: sdlc/plan
id: front-matter
title: Templates and artifact parsers must agree; approve.py must not misfire
description: Implementation steps for one tolerant front-matter parser, comment-line templates, a matching example, approve.py stage order and handle rules, has_role, and forward-compatible hook fixtures.
stage: build
status: in-review
kind: feature
reads: spec.md
approved-by:
approved-on:
risk-class: low
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [templates, chain-check, approve, hooks, consensus-item-6]
timestamp: 2026-09-04T21:50:19Z
---
# Plan: templates and artifact parsers must agree; approve.py must not misfire (from intent.md 2026-09-04)

## Files that change
Explicit paths only; no globs. No file under `.claude/hooks/` changes in this item.
- scripts/check_artifact_chain.py — add `_fm_value()`, make `front_matter_text()` skip comment lines and clean values (spec R-1); error text at line 281 names `'## Files that change'` (R-11)
- scripts/approve.py — handle from `git config sdlc.approver` only, exit 1 with the `--as` hint otherwise (R-7); stage order intent, spec, plan (R-8); usage text lines 8-9
- scripts/approvers.py — `Approvers.has_role(role, handle)`, `is_valid` delegates to it, `--has-role ROLE HANDLE` CLI (R-9)
- scripts/hooktest.py — `fake_repo(..., approvers_yaml=None)` copies `.sdlc/approvers.yaml` into the fake repo (R-10)
- scripts/test_check_artifact_chain.py — new classes `TemplateFrontMatter` (R-1, R-2) and `ExampleMatchesTemplates` (R-6); `FilesSectionRegression` asserts the new heading text (R-11)
- scripts/test_approve.py — template-derived approval (R-3), missing `sdlc.approver` (R-7), stage-order refusals (R-8); existing lone `plan.md` cases move to `intent.md`; the `--activate` case sets `sdlc.approver`
- scripts/test_approvers.py — new class `HasRole` (R-9)
- scripts/test_hooks_baseline.py — fixtures at lines 106, 122, 129, 135 gain `approved-by: luissiviero`; new `Harness` class (R-10); `RequirePlanHook::test_template_derived_plan_reads_clean_status` (R-5)
- scripts/test_bash_plan_gates.py — fixtures at lines 22-24 gain `approved-by: luissiviero` (R-10)
- docs/sdlc/templates/intent.md — comment lines above `status`, `approved-by`, `supersedes`, `record` (lines 7, 9, 11, 12) (R-4)
- docs/sdlc/templates/spec.md — comment lines above `approved-by`, `skills-applied` (lines 9, 11) (R-4)
- docs/sdlc/templates/plan.md — comment lines above `status`, `kind`, `approved-by` (lines 7, 8, 10) (R-4)
- docs/sdlc/templates/incident.md — comment line above `band-breached` (line 8) (R-4)
- work/_example/intent.md — `author:`, `resource:`, `supersedes:`, `record:`, `tags:`; template headings (R-6)
- work/_example/spec.md — template keys and every `##`/`###` heading, stubs as `(none)` (R-6)
- work/_example/plan.md — template keys and headings; file list unchanged (R-6)
- docs/sdlc/rules/30-conventions.md — lines 23-24: approve from your own shell or the GitHub web editor; set `git config sdlc.approver <handle>` (R-12)
- CLAUDE.md — regenerated from the rule fragments (R-12)
- GEMINI.md — regenerated (R-12)
- AGENTS.md — regenerated (R-12)
- work/index.md — regenerated
- work/_example/index.md — regenerated
- work/front-matter/index.md — regenerated
- work/front-matter/plan.md — deviations log entries, if any
- work/front-matter/log.md — gate entries

## Release-gated
Paths under RELEASE_GATED_PATHS with a named human owner (leave "(none)" if none).
- (none)

## Order of work (each step independently verifiable)
1. Parser: `_fm_value()` and the `front_matter_text()` loop change (spec Interfaces), the line-281 text, `TemplateFrontMatter` and the `FilesSectionRegression` assertion. Verify: `python3 scripts/run_tests.py -p test_check_artifact_chain.py` ends `OK`; `python3 scripts/gen_index.py --check` and `python3 scripts/gen_context_files.py --check` still clean; `python3 scripts/check_okf.py` ends `OKF: 64 docs, 0 warnings`.
2. Templates: the four files take the A6 lines. Verify: the R-4 grep prints nothing; `scripts/run_evals.sh --only skill-names-match-templates` ends `0 fail`; `python3 scripts/check_okf.py` unchanged; `TemplateFrontMatter::test_verbatim_template_copy_passes_in_progress` passes (it reads the real template).
3. Example: `work/_example/{intent,spec,plan}.md` and `ExampleMatchesTemplates`. Verify: that class passes; `python3 scripts/check_artifact_chain.py --slug _example --base HEAD` ends `CHAIN: PASS`; `python3 scripts/gen_index.py` then `--check` clean.
4. `approvers.py`: `has_role`, `is_valid` delegation, CLI; `HasRole` tests. Verify: `python3 scripts/run_tests.py -p test_approvers.py` ends `OK`; `python3 scripts/approvers.py --has-role tech-lead luissiviero; echo $?` prints `0`; `... --has-role tech-lead claude` prints `1`.
5. `approve.py`: handle rule, stage order, usage text; `test_approve.py` updates and new cases. Verify: `python3 scripts/run_tests.py -p test_approve.py` ends `OK`; eval `approve-refuses-in-agent-session` still passes.
6. Harness and fixtures: `hooktest.py` kwarg, the seven fixture lines, `Harness` and the R-5 test. Verify: `python3 scripts/run_tests.py -p test_hooks_baseline.py` and `-p test_bash_plan_gates.py` end `OK`; the R-10 grep prints `0` twice. No `_lib.sh` or hook file changes here, so the second-shell rule for `_lib.sh` does not apply.
7. Docs: `30-conventions.md:23-24`; `python3 scripts/gen_context_files.py && python3 scripts/gen_index.py`. Verify: both `--check` clean; `grep -l 'sdlc.approver' CLAUDE.md GEMINI.md AGENTS.md` lists three files; `wc -l CLAUDE.md` under 120.
8. Whole: `scripts/verify.sh`, `python3 scripts/check_artifact_chain.py --base origin/main --slug front-matter`, `scripts/run_evals.sh`, `python3 scripts/check_okf.py`; paste the last lines in the PR; append the ledger entry to `work/front-matter/log.md`.

## Risks
- Risk: the parser change reaches five importers at once (`gen_index.py:39`, `gen_context_files.py:34`, `check_okf.py:28`, `check_plugin_manifest.py:49`, `approve.py:33`) → mitigation: step 1 runs both drift checks and the OKF count before anything else changes; a value that gains or loses text shows up there.
- Risk: WI-5 (`deploy.sh`) and WI-6 consume `has_role` and the approvers file in fake repos; their drafts were written against this plan's shapes → mitigation: the signature `has_role(role, handle) -> (bool, reason)` and the exit-code CLI are fixed in spec R-9; any change is a deviation logged here and mirrored in their plans.
- Risk: stage order breaks the owner's batch command → mitigation: spec D4 processes a multi-artifact call in chain order; `test_approves_and_appends_ledger_then_chain_passes` keeps the three-in-one call green.
- Risk: a `title:` or `description:` containing ` #` is truncated for every reader → mitigation: spec C2; quote such values; `test_url_anchor_is_kept` proves links survive.
- What this could break: the chain check on every open branch (all readers change); `work/index.md` drift; the owner's approval habit (`--as` no longer optional without `sdlc.approver`).
- Options considered and not taken: PyYAML (intent says stdlib only); deleting template guidance instead of moving it (D2); a `--force` for stage order (C3); changing the hooks here (C1, owned by WI-2 and WI-3).

## Proof
- `scripts/verify.sh` green
- Spec rows → tests: R-1 → `test_check_artifact_chain.py::TemplateFrontMatter` (five methods); R-2 → `TemplateFrontMatter::test_verbatim_template_copy_passes_in_progress`; R-3 → `test_approve.py::Approve::test_template_derived_approval_yields_clean_ledger_line`; R-4 → the R-4 grep exits 1 and `scripts/run_evals.sh --only skill-names-match-templates` ends `0 fail`; R-5 → `test_hooks_baseline.py::RequirePlanHook::test_template_derived_plan_reads_clean_status`; R-6 → `test_check_artifact_chain.py::ExampleMatchesTemplates` (two methods) and `python3 scripts/check_artifact_chain.py --slug _example --base HEAD` ends `CHAIN: PASS`; R-7 → `test_approve.py::Approve::test_missing_sdlc_approver_exits_1_with_hint`; R-8 → `test_refuses_spec_before_intent_is_approved`, `test_refuses_plan_before_spec_is_approved`; R-9 → `test_approvers.py::HasRole` (four methods); R-10 → `test_hooks_baseline.py::Harness::test_fake_repo_carries_approvers_yaml` and the R-10 grep printing `0` twice; R-11 → `FilesSectionRegression::test_file_outside_plan_files_fails_against_base_branch`; R-12 → `python3 scripts/gen_context_files.py --check` ends `CONTEXT: 3 files up to date` and `grep -l 'sdlc.approver' CLAUDE.md GEMINI.md AGENTS.md` lists three; R-13 → `python3 scripts/run_tests.py` ends `Ran N tests` with N > 300 then `OK`, `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`.
- Manual / browser / screenshot / eval: `scripts/run_evals.sh` ends `EVALS: N pass, 0 fail, ...`; `python3 scripts/check_okf.py` ends `OKF: 64 docs, 0 warnings`; owner runs `python3 scripts/approve.py front-matter plan.md --dry-run` from their shell without `--as` after `git config sdlc.approver luissiviero` and sees `would approve`.

## Rollback
- Revert the PR's commits; no data, no migration, no hook wiring. Regenerate `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` and the indexes after the revert so the drift checks agree with the tree.

## Deviations log (append during implementation; same commit as the deviation)
- 
