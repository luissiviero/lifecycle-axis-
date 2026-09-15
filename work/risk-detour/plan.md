---
type: sdlc/plan
id: risk-detour
title: Tests first, then the check, the queue rule, the index marker, the templates, the skills, two rewritten rule lines, three evals and the decision record, in one pull request the owner clicks
description: "Thirty-two files in one claude/ branch: eight under scripts/ (a new check_detour.py and its test module, a parked_note helper in next_item.py with four cases, a parked marker in gen_index.py with a golden case, a detour-record guard in test_sign.py, a new test_park_advance.py composing the merge tests' Advance fixture), three templates, four skills, two rule fragments with the three context files regenerated, three eval cases, a decision record with an amendment note and an index line, and the item's own artifacts; every new case is watched red before its code, the adopter's render is measured at the cap, and the last commit parks the item as `parked: ready PR #<n>; click needed (<path>)` because every skill, template and rule path sits on the merge script's ALWAYS_LOCKED floor."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: superseded
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: feature
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by: claude
approved-on: 2026-09-15
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/60
tags: [delegated-mode, run-queue, sdlc-run, risk-class, revision-record, consensus, parking, detour]
timestamp: 2026-09-15T00:58:00Z
---
# Plan: a deterministic detour check at every gate, a route record, a park of two ledger words, and a queue that skips it (from intent.md 2026-09-08)

`kind: feature`: new behaviour, no defect; existing test modules gain cases and stay editable. No engineer
interview: the owner is the only human and works from a phone, so the repository's own record stood in for it
(`CLAUDE.md` conventions, the lessons named under Risks, the spec's gotchas G-1 to G-11, the six owner answers
on the intent). The pull request is the owner's click (spec C1): `.claude/skills`, `docs/sdlc/templates`,
`docs/sdlc/rules` and the three context files are on `delegated_merge.py`'s `ALWAYS_LOCKED` floor, none is in
`PROTECTED_PATHS`, so the hooks allow every edit and the delegated merge refuses the whole.

## Files that change
- scripts/check_detour.py — new; `locked(paths, root, slug=None)`, `verdict(hits)`, `plan_paths(plan_file, root)`, `diff_paths(root, base)`, `main(argv)`; imports `delegated_merge` for `check_locked_paths`, `_locked_paths`, `ALWAYS_LOCKED`, `load_config`, and `delegation.load`; exit 0 `DETOUR: none`, 3 `DETOUR: needed (<n>)`, 2 bad input (spec R-2, Interfaces)
- scripts/test_check_detour.py — new; classes `Matching`, `Sources`, `Cli` with the seven cases spec R-2 names, on a fixture root carrying its own `.sdlc/config.env` and `.sdlc/delegation.yaml`, and a throwaway git repository for `--diff`
- scripts/next_item.py — `parked_note(entries)` and the `_eligible` branch before the spec test; docstring gains the parked rule (spec R-3)
- scripts/test_next_item.py — `class Parked` with the five cases spec R-3 names; a `_log(root, slug, notes)` fixture helper writing `work/<slug>/log.md`; `_repo` also writes `.sdlc/approvers.yaml`
- scripts/gen_index.py — `build_item` reads `next_item.parked_note(entries)` into `item["parked"]`; `_stage` unchanged, `render_top_index` writes `parked` in the stage cell when set; `render_item_index` writes `Parked: <note>` before `Last gate:` (spec R-6)
- scripts/test_gen_index.py — `class ParkedMarker` with its own three-item tree and golden strings; existing goldens untouched (spec G-7)
- scripts/test_sign.py — `REVISION_DETOUR_RECORD` constant in the template's detour shape and `SignPasses::test_resigns_with_a_detour_record` (spec R-1)
- scripts/test_park_advance.py — new; `class ParkAdvance(test_delegated_merge.Advance)` overriding `setUp` to park `next-item` with a `parked:` ledger line, one case: the advance lands on `later-item` (spec R-4)
- docs/sdlc/templates/revision.md — `kind:` key with its comment, `## Route (detour only)` section with five bullets, the detour question sentence in the first `## Reviewer:` section and "Same questions" in the second, one sentence in `## Closing note` (spec R-1)
- docs/sdlc/templates/intent.md — `# detour-of:` comment and `detour-of:` key after `supersedes:` (spec R-5)
- docs/sdlc/templates/log.md — one example line in the park shape (spec R-5, Interfaces)
- .claude/skills/sdlc-run/SKILL.md — the locked-path case leaves "Stop and call the owner back"; new `## The detour rule` section with the gates, the trigger command per gate, the record, rounds, the park (both shapes), the remainder, the second-Claude-model rule; step 3 names the park pull request beside the code one (spec R-7)
- .claude/skills/sdlc-spec/SKILL.md — one step: run `scripts/check_detour.py --paths` on the paths the design names before signing; `needed` goes to the run skill's detour rule (spec R-7)
- .claude/skills/sdlc-plan/SKILL.md — one step: run `scripts/check_detour.py --plan work/<slug>/plan.md` before signing (spec R-7)
- .claude/skills/sdlc-intent/SKILL.md — one step: run `scripts/check_detour.py --paths` on the Affected systems paths; a `needed` files the record, drafts the route into Proposed outcome, re-signs nothing; a remainder intent carries `detour-of: <slug>` and `mode: supervised` (spec R-5, R-7)
- docs/sdlc/rules/30-conventions.md — the delegated-mode bullet rewritten in its three lines to name `parked:`/`resumed:` beside `deviation:` and `revision <n>:`; no net line (spec R-8)
- docs/sdlc/rules/40-claude-only.md — the `/sdlc-run` bullet rewritten in its two lines: the detour and the park replace "a plan revision is the last resort" in the same width; no net line (spec R-8)
- CLAUDE.md — regenerated by `scripts/gen_context_files.py`
- GEMINI.md — regenerated
- AGENTS.md — regenerated
- evals/cases/detour-check-names-locked-paths.yaml — `kind: hook`; fixture root, two locked and one clean path, `needed (2)` exit 3 and `none` exit 0 (spec R-2)
- evals/cases/run-queue-skips-parked-item.yaml — `kind: hook`; two granted items, a park, a resume (spec R-3)
- evals/cases/detour-is-written-down.yaml — `kind: hook`; structural greps over the templates and the four skills (spec R-5, R-7)
- knowledge/decisions/risk-detour.md — new; `amends: delegated-mode.md`; context, decision, alternatives, consequences (spec R-9)
- knowledge/decisions/delegated-mode.md — one "Amended on 2026-09-15" paragraph in the header quote naming decision 4 (spec R-9)
- knowledge/decisions/index.md — one line (spec R-9)
- work/_example/intent.md — `detour-of:` after `supersedes:`, so the always-green example keeps the template's keys in the template's order (deviation 3; `test_check_artifact_chain.py::ExampleMatchesTemplates` compares them)
- work/risk-detour/spec.md — amendments under this plan's deviations, logged as `deviation:` lines (spec G-4: an amendment line on a delegated artifact must start `deviation:` or name a record)
- work/risk-detour/plan.md — this plan; its deviations log
- work/risk-detour/log.md — one ledger line per gate; the park line as the last commit
- work/risk-detour/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none) — no path under `RELEASE_GATED_PATHS` (`migrations infra terraform helm`) is touched. Every path under
`scripts/` here is under `PLAN_REQUIRED_PATHS`, none is on the policy's `locked-paths`; the skills, templates,
rules and context files are on `ALWAYS_LOCKED`, so the pull request is the owner's click (spec C1).

## Order of work (each step independently verifiable)
1. **The failing cases first.** `scripts/test_check_detour.py` (seven cases; red: `ModuleNotFoundError` on
   `check_detour`), `test_next_item.py::Parked` (four cases; red: the parked item is offered and
   `parked_note` does not exist), `test_gen_index.py::ParkedMarker` (red: no `parked` cell, no `Parked:` line),
   `test_park_advance.py::ParkAdvance` (red: `advance()` returns `next-item`, the parked one), and
   `test_sign.py::test_resigns_with_a_detour_record` (a guard, predicted green; mutation-checked in step 2 by
   flipping one verdict to `keep`, which must refuse). Verifiable: `python3 -m unittest scripts.test_check_detour
   scripts.test_next_item scripts.test_gen_index scripts.test_park_advance scripts.test_sign -q` shows exactly
   the predicted failures and errors; the counts go into the deviations log if they differ.
2. **`scripts/check_detour.py`.** As spec R-2 and Interfaces: the three sources, the per-path call to
   `delegated_merge.check_locked_paths`, the label from a set lookup of the returned prefix, the verdict line
   and exit codes. Verifiable: `python3 -m unittest scripts.test_check_detour -q` green;
   `python3 scripts/check_detour.py --paths .claude/skills/sdlc-run/SKILL.md scripts/next_item.py` ends
   `DETOUR: needed (1)` exit 3 on this checkout; `--paths scripts/next_item.py` ends `DETOUR: none` exit 0.
3. **`scripts/next_item.py`.** `parked_note` and the `_eligible` branch. Verifiable: `python3 -m unittest
   scripts.test_next_item -q` green (16 cases); `python3 scripts/next_item.py --list --exclude risk-detour`
   still prints nothing on this checkout.
4. **`scripts/gen_index.py`.** The marker. Verifiable: `python3 -m unittest scripts.test_gen_index -q` green;
   `python3 scripts/gen_index.py --check` ends `INDEX: up to date` (no item is parked today, so no generated
   file changes).
5. **`scripts/test_park_advance.py` goes green** with step 3's code alone (no code of its own). Verifiable:
   `python3 -m unittest scripts.test_park_advance -q`; the fixture's `git log --format=%an` shows one
   `github-actions[bot]` commit after `Fixture` and none else.
6. **Templates.** `revision.md`, `intent.md`, `log.md` as spec Interfaces. Verifiable: `scripts/checks/front-matter.sh`
   ends `0 problems`; `python3 scripts/check_okf.py` ends `0 warnings`; `grep -n '^kind:\|^## Route' docs/sdlc/templates/revision.md`
   shows both; `grep -n '^detour-of:' docs/sdlc/templates/intent.md` shows one.
7. **Skills.** `sdlc-run` (the detour rule replaces the locked-path stop; the park; step 3's second pull
   request), `sdlc-spec`, `sdlc-plan`, `sdlc-intent` (one step each). Verifiable: eval
   `detour-is-written-down` green (written in step 9 and watched red before this step); `session-protocol-is-written-down`
   and `skill-names-match-templates` still green (`scripts/run_evals.sh --only 'skill-*' --only 'session-*'`
   or the whole suite).
8. **Rule fragments and the render.** Rewrite the two bullets, `python3 scripts/gen_context_files.py`, then
   `scripts/adopt.sh <scratch>/adopt-after --with-hooks` and `wc -l` on its three context files. Verifiable:
   `CONTEXT: 3 files up to date`; the three counts are at most `120 119 99` (measured before the change on
   `3ce6eae`); `wc -l CLAUDE.md` in the kit at most 108.
9. **Evals.** The three cases; `detour-is-written-down` written first and watched red against the unchanged
   skills (spec R-5/R-7, lesson `a-verifiable-command-fails-before-the-change`), the other two watched red
   by running them against `origin/main`'s `scripts/` in a scratch worktree. Verifiable:
   `scripts/run_evals.sh --only 'detour-*' --only 'run-queue-*'` ends `EVALS: 4 pass, 0 fail`; `scripts/checks/eval-cases.sh`
   ends `0 problems`.
10. **Knowledge.** `risk-detour.md`, the amendment paragraph, the index line. Verifiable: `python3 scripts/check_okf.py`
    ends `0 warnings`; `grep -c 'Amended on 2026-09-15' knowledge/decisions/delegated-mode.md` is 1.
11. **The four checks** (`env -u GH_TOKEN -u GITHUB_TOKEN` in this container, spec G-10): `scripts/verify.sh`,
    `python3 scripts/check_artifact_chain.py --base origin/main --slug risk-detour`, `scripts/run_evals.sh`,
    `python3 scripts/check_okf.py`. Verifiable: `VERIFY: PASS (<sha>)`, `CHAIN: PASS`, `EVALS: N pass, 0 fail, ...`,
    `OKF: N docs, 0 warnings`.
12. **Pull request.** Draft on the first push (`Work-Item: risk-detour`), `/sdlc-review` with reviewer subagents on
    a different model, findings posted, ready. Then the last commit: the park line
    `parked: ready PR #<n>; click needed (.claude/skills/sdlc-run/SKILL.md)` on `intent.md`, indexes regenerated,
    pushed; the pull request says the merge is the owner's click and why (spec C1, intent Q1). Verifiable: the
    chain check on the final head ends `CHAIN: PASS`; `python3 scripts/next_item.py --list` on the branch prints
    nothing (the parked item is skipped, and the queue was empty anyway).

## Risks
- Risk: importing `delegated_merge` from the check pulls `approvers`, `chain`, `delegation`, `log_ledger`,
  `next_item` at module level → mitigation: all stdlib and local, no network until `main()`; the test module
  imports it the same way the merge tests do; a slow import would show in `run_tests.py`'s per-module time.
- Risk: the label parses the matcher's reason string (`... locked path '<prefix>'`) → mitigation: one test pins
  the format by asserting the prefix it names; a reworded reason fails that test, not silently mislabels.
- Risk: `parked:` on `intent.md` is an `approved -> approved` line an agent writes → mitigation: the advance
  already writes that shape on intents; `approvals()` on `intent.md` is read by nothing in the chain; the hook
  lets a ledger line through (advance-push's ledger carries agent-written `approved -> approved` lines).
- Risk: the adopter's `CLAUDE.md` is at the cap → mitigation: no net line in `30` and `40`; step 8 measures.
- Risk: `glob.glob(root_dir=...)` needs Python 3.10 → mitigation: the kit already requires 3.11 (`f"{x!r}"` and
  `datetime.fromisoformat` uses); the runner is 3.11.
- What this could break: `next_item.py` is imported by `delegated_merge.py`'s advance; a bug in `parked_note`
  would move the pointer wrongly on the first delegated merge after this lands → the four cases plus the
  advance case in `test_park_advance.py` cover the parked, resumed, missing-record and unparked paths; the
  helper returns `None` on any entry set without the two words, which is today's behaviour.
- Options considered and not taken: a `status: parked` word (closes `STATUSES`, changes the chain check); a
  `parked:` front-matter key on the intent (an agent may write no key on the file that carries the grant); a
  separate `detour.md` template (two record types for two locked readers); computing the label by
  re-implementing the prefix rule (`one-path-spelling-in-guards.md`).
- Lessons applied: `a-verifiable-command-fails-before-the-change.md` (step 1, 9), `stage-new-files-before-verify.md`
  (`git add` before every `verify.sh`), `commit-before-the-chain-check.md`, `eval-checks-have-no-blank-lines.md`,
  `adopter-context-file-sits-at-the-cap.md` (step 8), `plan-bullets-start-with-the-path.md` (this list),
  `tests-carry-their-own-environment.md` (every fixture writes its own policy, config and git identity),
  `quote-the-file-not-your-memory.md` (the eval's greps quote the skill text they assert).

## Proof
- `scripts/verify.sh` green
- Spec rows → tests: R-1 → `test_sign.py::SignPasses::test_resigns_with_a_detour_record`; R-2 →
  `test_check_detour.py` (7) and eval `detour-check-names-locked-paths`; R-3 → `test_next_item.py::Parked` (4) and
  eval `run-queue-skips-parked-item`; R-4 → `test_park_advance.py::ParkAdvance` (1); R-5, R-7 → eval
  `detour-is-written-down`; R-6 → `test_gen_index.py::ParkedMarker` (1); R-8 → step 8's `wc -l` and
  `context-drift.sh`; R-9 → `check_okf.py` and the `grep -c`; R-10 → the four last lines.
- Manual / browser / screenshot / eval: `check_detour.py --plan work/risk-detour/plan.md` on this plan ends
  `DETOUR: needed (<n>)` naming every skill, template, rule and context-file path here, which is the fact behind
  the park in step 12; recorded in the pull request.

## Rollback
- Revert the merge commit; no data, no migration, no generated state outside git. The park line on this
  item's own ledger is append-only history and stays; the pointer is unaffected (a click runs no advance).

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-15 step 1 observed: `test_check_detour.py` 1 error (the module import, as predicted); `test_next_item.py::Parked`
  2 failures + 1 error of 4 (the parked-then-resumed case is green by construction, since an unparked item is offered
  anyway; the spec's R-3 row names it as a case, not as a red one); `test_gen_index.py::ParkedMarker` 1 failure;
  `test_park_advance.py` 1 failure (`'next-item' != 'later-item'`); `test_sign.py` green, the guard as predicted.
  No file-list change.
- 2026-09-15 spec amendment 2 (ledger `deviation:` line): the Interfaces example row for a parked item carried a
  Markdown link the OKF checker read as broken (`WARN work/risk-detour/spec.md link slug/index.md`); reworded to
  describe the cell. No file-list change.
- 2026-09-15 deviation 3 (file list, ledger `deviation:` line): `work/_example/intent.md` gains the blank `detour-of:`
  key, because `scripts/test_check_artifact_chain.py::ExampleMatchesTemplates::test_front_matter_keys_match` holds the
  always-green example to the intent template's keys in the template's order and went red on the template change
  (step 6). Added to `## Files that change`.
- 2026-09-15 review round on pull request 96 (security pass, Opus 5: Important 2, Nits 3; plan pass, Opus 5:
  Important 0, Nits 5). Fixed in the same push, no file-list change: `diff_paths` reads `git diff --name-status
  -M -z` and splits on NUL, since a C-quoted name never matched a locked prefix (`test_diff_names_arrive_unquoted`,
  watched red first); `parked_note(entries, av)` lifts a park on a `resumed:` line only when the actor holds the
  `intent.md` role in `.sdlc/approvers.yaml`, through `next_item.resumers(root)`, so the agent a park stops cannot
  lift it (`test_an_agent_cannot_lift_a_park`, watched red first; fixtures and the eval write an approvers file);
  plan bullets are normalised with `os.path.normpath` and an absolute or root-escaping bullet is exit 2
  (`test_plan_bullets_are_normalised_and_confined_to_the_root`). The Markdown nit on the `Parked:` line is
  accepted as cosmetic (the table cell is the literal `parked`; a note can carry no `|`). Spec R-2, R-3 and the
  Interfaces section amended under a ledger `deviation:` line; the plan's description count, the `_log` helper
  name and the revision-template bullet corrected here.
- 
