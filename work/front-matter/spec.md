---
type: sdlc/spec
id: front-matter
title: Templates and artifact parsers must agree; approve.py must not misfire
description: One front-matter parser for every Python reader, comment lines instead of inline comments in the templates, an example that matches them, and an approve.py that only records gates a human can actually hold.
stage: design
status: approved
reads: intent.md
approved-by: luissiviero
approved-on: 2026-09-04
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Transcribed from the approved implementation plan (session above), section WI-1 and appendix A6, by a drafting subagent; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [templates, chain-check, approve, hooks, consensus-item-6]
timestamp: 2026-09-04T21:50:19Z
---
# Spec: templates and artifact parsers must agree; approve.py must not misfire

## Requirements (each maps to an intent outcome)
Intent outcomes, numbered as the bullets of `intent.md` "Proposed outcome": (1) a verbatim template copy passes the chain check and approves cleanly; (2) the hooks read `status:`/`kind:` through one parser and the templates keep guidance as a comment line; (3) `work/_example/` matches the templates; (4) `approve.py` never guesses a handle and refuses stage-order violations; (5) `approvers.py` gains `has_role`; (6) `hooktest.py` fake repos carry `approvers.yaml` and approved fixtures name an approver; (7) tests grow and verify stays green. Every test below is a method in the named `scripts/test_*.py` module, run with `python3 scripts/run_tests.py -p <module>`.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `front_matter_text()` skips `#` comment lines, strips a trailing ` #…`, matching quotes and `\r`, and keeps `#` that has no whitespace before it | 1 | `scripts/test_check_artifact_chain.py::TemplateFrontMatter` methods `test_inline_comment_is_stripped`, `test_quoted_status_parses`, `test_comment_line_is_not_a_key`, `test_crlf_input_parses`, `test_url_anchor_is_kept` |
| R-2 | A verbatim copy of `docs/sdlc/templates/intent.md` into `work/<slug>/` passes `check_artifact_chain.py` in in-progress mode | 1 | `TemplateFrontMatter::test_verbatim_template_copy_passes_in_progress` (last stdout line `CHAIN: PASS`) |
| R-3 | `approve.py` on a template-derived artifact writes a five-field ledger line, `log_ledger.parse()` reports `malformed == []`, and the `status:` line carries no `#` | 1 | `scripts/test_approve.py::Approve::test_template_derived_approval_yields_clean_ledger_line` |
| R-4 | The four templates carry each field's guidance on a `#` line above the field; no front-matter value is followed by ` #` | 2 | `grep -nE '^[a-z-]+:.*[[:space:]]#' docs/sdlc/templates/intent.md docs/sdlc/templates/spec.md docs/sdlc/templates/plan.md docs/sdlc/templates/incident.md` prints nothing and exits 1; `scripts/run_evals.sh --only skill-names-match-templates` ends `EVALS: 1 pass, 0 fail` |
| R-5 | Today's hook readers (`require-plan.sh:19`, `protect-tests.sh:15`) get a clean value from a template-derived `plan.md`, because the comment line does not match `^status:`/`^kind:` | 2 | `scripts/test_hooks_baseline.py::RequirePlanHook::test_template_derived_plan_reads_clean_status` (exit 2, stderr contains `status 'draft'` and no `#`) |
| R-6 | `work/_example/{intent,spec,plan}.md` have the templates' front-matter keys and `##` headings, in the templates' order | 3 | `scripts/test_check_artifact_chain.py::ExampleMatchesTemplates` methods `test_front_matter_keys_match`, `test_headings_match`; `python3 scripts/check_artifact_chain.py --slug _example --base HEAD` ends `CHAIN: PASS` |
| R-7 | Without `--as` and without `git config sdlc.approver`, `approve.py` exits 1 with the `--as <github-handle>` hint and never reads `user.name` | 4 | `scripts/test_approve.py::Approve::test_missing_sdlc_approver_exits_1_with_hint` (fixture `user.name` is `luissiviero`, `test_approve.py:35`, so success proves it is not consulted); `test_default_handle_from_git_config_and_activate` sets `sdlc.approver` |
| R-8 | `approve.py` refuses `spec.md` unless `intent.md` is approved and `plan.md` unless `spec.md` is; several artifacts in one call still work in chain order | 4 | `scripts/test_approve.py::Approve::test_refuses_spec_before_intent_is_approved`, `test_refuses_plan_before_spec_is_approved` (exit 1, stderr names the predecessor); existing `test_approves_and_appends_ledger_then_chain_passes` still passes |
| R-9 | `Approvers.has_role(role, handle) -> (bool, reason)` and `python3 scripts/approvers.py --has-role <role> <handle>` exit 0/1 | 5 | `scripts/test_approvers.py::HasRole` methods `test_listed_handle_ok`, `test_never_approve_handle_rejected`, `test_unknown_role_rejected`, `test_cli_exit_codes` |
| R-10 | `hooktest.fake_repo()` copies the kit's `.sdlc/approvers.yaml` unless `approvers_yaml=` is given; every `status: approved` fixture in the two hook test modules says `approved-by: luissiviero` | 6 | `scripts/test_hooks_baseline.py::Harness::test_fake_repo_carries_approvers_yaml`; `grep -cE 'status: approved\\n(kind: [a-z]+\\n)?---' scripts/test_hooks_baseline.py scripts/test_bash_plan_gates.py` prints `0` for both (today: 4 and 3) |
| R-11 | The plan-conformance error names the heading the template has: `'## Files that change'` | 1 | `scripts/test_check_artifact_chain.py::FilesSectionRegression::test_file_outside_plan_files_fails_against_base_branch` asserts the new text |
| R-12 | `docs/sdlc/rules/30-conventions.md` says approvals happen from the owner's own shell or the GitHub web editor and name `git config sdlc.approver`; the generated context files carry it | 4 | `python3 scripts/gen_context_files.py --check` ends `CONTEXT: 3 files up to date`; `grep -l 'sdlc.approver' CLAUDE.md GEMINI.md AGENTS.md` lists all three |
| R-13 | Test count grows and verify stays green | 7 | `python3 scripts/run_tests.py` ends `Ran N tests` with N > 300 (baseline 300 at `89bcf9a`) then `OK`; `scripts/verify.sh` ends `VERIFY: PASS (<sha>)` |

## Design
### Architecture / data flow
No hook runtime changes and no new files. One Python parser, `front_matter_text()` in `scripts/check_artifact_chain.py:42-53`, is read through `front_matter()` by `approve.py:33`, `gen_index.py:39`, `gen_context_files.py:34`, `check_okf.py:28` and `check_plugin_manifest.py:49`, so every reader gets the new tolerance at once. The templates move guidance out of the value and onto a `#` line above the field, so both the Python parser and today's awk readers in the hooks (`/^status:/` at `require-plan.sh:19`, `/^kind:/` at `protect-tests.sh:15`) see a bare value. `approve.py` stops guessing a handle and checks the predecessor's status before it records a gate. `approvers.py` answers a role question directly, for the deploy gate that follows. `hooktest.fake_repo()` gives every fake repo the kit's approvers file, ahead of the approval gate that will read it.

### Interfaces (APIs, events, schemas) — exact shapes
`scripts/check_artifact_chain.py` (appendix A6, quoted):
```python
def _fm_value(raw):
    v = raw.strip()
    if v.startswith("#"):
        return ""
    v = re.split(r"\s+#", v, 1)[0].rstrip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1].strip()
    return v
```
`front_matter_text(text)` keeps its signature; the loop gains `if line.lstrip().startswith("#"): continue` before the `":" in line` test and stores `_fm_value(v)` instead of `v.strip()`. `splitlines()` already drops `\r\n`; `_fm_value` also strips a stray `\r` via `strip()`. Line 281's message becomes `... not listed under '## Files that change' in work/{slug}/plan.md ...`.

`scripts/approve.py`: line 75 becomes `handle = a.handle or git("config", "sdlc.approver")`; the existing `if not handle:` branch at 76-78 keeps its exact hint text. Stage order: `PREDECESSOR = {"spec.md": "intent.md", "plan.md": "spec.md"}`; artifacts are processed in `CHAIN` order regardless of argument order; a predecessor counts as approved when its front matter says so on disk or when it was approved earlier in the same invocation (dry-run included). The check runs after the handle check at 97-100 and before `set_front_matter`; refusal is exit 1 with `approve: work/<slug>/spec.md needs work/<slug>/intent.md approved first (it is '<status>')`. `incident.md` has no predecessor. Docstring lines 8-9 drop the `user.name` fallback.

`scripts/approvers.py`: `Approvers.has_role(self, role, handle) -> (bool, reason)`: same `normalize()`, `exists` and `never_approve` checks as `is_valid` (121-135), then `norm in {normalize(h) for h in self.roles.get(role, [])}`; reasons `no approvers file at <path>`, `empty approver`, `agent identities cannot approve`, `no such role <role>`, `<norm> is not a <role>`, `ok`. `is_valid` is rewritten as `role_for(artifact)` then `has_role(role, handle)`, keeping its reason strings (`test_approvers.py:47,52,58,63` pin them). CLI: `main()` gains `argparse` with `--has-role ROLE HANDLE` (`nargs=2`); prints the reason to stderr and exits 0 when ok, 1 otherwise; with no flag it keeps today's JSON dump.

`scripts/hooktest.py`: `fake_repo(config_env=None, approvers_yaml=None, **files)`; `None` copies `REAL_ROOT/.sdlc/approvers.yaml`, a string is written as-is, both to `<root>/.sdlc/approvers.yaml`, before `files` so a test can still overwrite it. Docstring at 18-23 gains the kwarg.

Template lines (A6, quoted for `intent.md:7-12` and `plan.md:7-10`; `spec.md:9,11` and `incident.md:8` follow the same shape):
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
```
# status: draft | in-review | approved | superseded  (require-plan.sh refuses code edits until approved)
status: draft
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: feature
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by:
```
`work/_example/intent.md`: `originator:` becomes `author:`, `source:` becomes `resource:`, `supersedes:`/`record:`/`tags:` are added empty; `## Success criteria` becomes `## Proposed outcome`, `## Constraints and non-goals` becomes `## Constraints`, `## Open questions` takes the template's full heading. `work/_example/spec.md` and `plan.md` take every template key (`skills-version`, `prompt`, `record`, `resource`, `tags`) and every `##`/`###` heading verbatim, missing sections as `(none)` stubs; the plan's `docs/**` and `work/_example/**` file list stays.

### Data and migrations
None. No new field is personal or regulated (security-standards rule 4). No dependency is added (rule 5); stdlib only.

### Failure modes and how they surface
A status still outside the enum after cleaning: `CHAIN: FAIL` naming the file and the enum (`check_artifact_chain.py:166-167`). A ` #` inside a value that was meant to be kept: the value is truncated at the comment; quote the value (D1). Missing `sdlc.approver` and no `--as`: exit 1 with the hint (R-7). Stage order violated: exit 1 naming the predecessor and its status (R-8); nothing is written. `--has-role` on a missing approvers file: exit 1 with `no approvers file at <path>` (fails closed like `is_valid`). A `fake_repo` test that deletes the approvers file: hooks that read it (from WI-6 on) block, which is the intended fail-closed shape.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: intent outcome 2 asks for the shared hook parser (`fm_value` in `_lib.sh`, used by `require-plan.sh` and `protect-tests.sh`), but the approved implementation plan says WI-1 makes no hook runtime change and assigns `fm_value` to WI-2 and the hook wiring to WI-3 — policy: approved implementation plan, WI-1 and "Batches" (an earlier item's helper is named under Risks and absorbed by the deviations log) — contradiction? yes, on scope — owner: luissiviero — resolution: this item ships the template half of outcome 2 plus R-5, which proves today's awk reads a template-derived plan cleanly; the `kind: fix   # comment`, `kind: "Fix"` and CRLF hook cases are listed under Not doing with their owning items; the intent text is left as written.
- C2: YAML comment semantics turn `title: Fix #12 crash` into `Fix` — policy: intent open question 1 — contradiction? no — owner: luissiviero — resolution: follow YAML (A6 "Accepted"); a value that needs ` #` is quoted; R-1 pins the URL-anchor case so `resource:` links survive.
- C3: stage-order refusal has no `--force` — policy: intent open question 2 — contradiction? no — owner: luissiviero — resolution: refuse; the chain check at `check_artifact_chain.py:169-176` would reject the result anyway.
- C4: the session that writes the parser also writes the tests that prove it — policy: security-standards rule 8 (agent hygiene) — contradiction? no — owner: luissiviero — resolution: the decisive tests start from the repo's own template files, not from agent-shaped fixtures; the owner approves this plan and reviews the PR; CI re-runs everything.
- C5: `fake_repo()` copying the kit's real `approvers.yaml` couples every hook test to that file — policy: `hooktest.py` docstring 18-23 (a fake repo supplies only what the hook reads) — contradiction? no — owner: luissiviero — resolution: `approvers_yaml=` lets a test supply its own; the kit's file lists one human and three never-approve identities.

## Open questions carried from intent.md
- Q1 (title with ` #`): proposed answer in C2; the owner confirms by approving this spec or answers in `intent.md`.
- Q2 (`--force` on stage order): proposed answer in C3; same.

## Decisions (ADR-style: context → decision → consequences)
- D1: context: three readers disagree on what a value is; decision: one Python parser with YAML comment semantics (whitespace-then-`#`), matching-quote stripping, no PyYAML; consequences: every importer changes behaviour together; values with ` #` must be quoted.
- D2: context: the templates teach adopters; decision: guidance moves to a comment line above each field instead of being deleted; consequences: templates stay self-explaining and no reader, awk or Python, ever sees the comment as a value.
- D3: context: `git config user.name` is a display name, not a GitHub handle; decision: `approve.py` reads `sdlc.approver` only; consequences: one-time setup per clone, documented in R-12.
- D4: context: the ledger should never record an impossible gate; decision: `approve.py` enforces intent, spec, plan order and processes a multi-artifact call in that order; consequences: the batch command in the implementation plan keeps working; a lone `plan.md` approval on an unapproved chain is refused.
- D5: context: WI-5's deploy gate needs a role question, not an artifact question; decision: `has_role(role, handle)` is the primitive and `is_valid` delegates to it; consequences: one normalisation and one never-approve path.
- D6: context: WI-6 will validate approvers inside hooks; decision: `fake_repo()` carries the approvers file now and approved fixtures name `luissiviero`; consequences: WI-6 flips no test that this item leaves green.

## Gotchas found while reading the codebase
- `scripts/test_check_artifact_chain.py:181-183` asserts the old text with its closing quote, `not listed under '## Files'`; the line-281 fix in plan step 1 fails that test unless it is updated in the same commit (plan step 7 does not list it).
- `scripts/test_approve.py` approves `plan.md` alone at `:93-97`, `:99-104` and `:114-120` on a fixture whose `intent.md` and `spec.md` are `in-review` (`:13-28`, `:45-47`); stage order would refuse all three. They switch to `intent.md` (no predecessor) or approve the chain first. `:106-112` relies on the `user.name` fallback via `:35`; it sets `sdlc.approver` instead.
- `scripts/approve.py:8-9` documents the `user.name` fallback in the usage text; it changes with line 75.
- The plan cites `test_hooks_baseline.py:106` as the fixture to flip; `:122`, `:129` and `:135` also say `status: approved` without an approver (`ProtectTestsHook`). `protect-tests.sh` never reads `approved-by`, but the intent's outcome 6 covers every such fixture, so all four flip, plus `test_bash_plan_gates.py:22-24`.
- `check_okf.py` scans `docs/sdlc` (`KNOWLEDGE_PATHS`, `.sdlc/config.env`), so the templates are OKF docs; it reads only `type`, `title`, `description`, `timestamp` (`check_okf.py:128-140`), which the comment lines do not touch. Baseline `OKF: 64 docs, 0 warnings` must hold.
- `approve.py:set_front_matter` matches `^approved-by:.*$` (`:49`) and inserts after a line that `startswith("status:")` (`:55`), so a `# approved-by:` or `# status:` comment line is never rewritten or mistaken for the key; A6 is right that it needs no change.
- `section()` at `check_artifact_chain.py:62-66` matches headings with `startswith`, so `## Order of work (each step independently verifiable)` and the other long template headings the example adopts still resolve.
- `gen_index.py:117-122` reads `title` and `description` from `intent.md`, both unchanged in the example, so `work/_example/index.md` regenerates byte-identical; it is listed in the plan anyway because the drift check runs on it.
- `evals/cases/hook-protects-tests-during-fix.yaml:6` writes `status: approved\nkind: fix` without an approver; it belongs to WI-3's list, not this item's.

## Not doing
- `fm_value` in `.claude/hooks/_lib.sh` (WI-2) and its use in `require-plan.sh:19` and `protect-tests.sh:15` (WI-3), including the `kind: fix   # comment`, `kind: "Fix"` and CRLF lock cases and their `test_hooks_baseline.py::ProtectTestsHook` tests.
- Approver validation inside `require-plan.sh` and the `protect-approvals.sh` hook (WI-6); the deploy gate that consumes `--has-role` (WI-5).
- Rewriting `work/_example/plan.md`'s `docs/**` and `work/_example/**` globs; `_example` is exempt from plan conformance and the intent asks for field and heading parity only.
- Doc corrections beyond `docs/sdlc/rules/30-conventions.md:23-24` (WI-11).
- Setting `status: approved` or `approved-by` on any artifact from this session (security-standards rule 8; CLAUDE.md hard rules).
