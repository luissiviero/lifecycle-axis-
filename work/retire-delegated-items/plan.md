---
type: sdlc/plan
id: retire-delegated-items
title: Red cases in four test modules first, then the check, the script, the dispatch helper, the workflow and the three documents
description: "Step 1 writes every new case the spec names across scripts/test_check_artifact_chain.py, scripts/test_approve.py, scripts/test_approve_dispatch.py and scripts/test_check_workflow_permissions.py and records the red set; steps 2 to 5 change check_artifact_chain.py (superseded judged by the retirer, the trailer route bound to the retiring line, the retire run-name waiver), approve.py (--retire, --next), approve_dispatch.py (mode retire in the role gate and the commit subject) and approve.yml (mode retire, next input, slug required) under the unlock; step 6 writes the routine into github-setup.md, HANDOFF.md and the indexes lesson; step 7 is the loop, the review on a second model and the ready flip."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: approved
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: feature
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by: luissiviero
approved-on: 2026-09-14
risk-class: medium
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/92
tags: [delegated-mode, retirement, chain-check, approvals, gen-index, control-plane]
timestamp: 2026-09-14T17:00:00Z
---
# Plan: red cases first, then the check, the script, the dispatch helper, the workflow and the documents (from intent.md 2026-09-14)

`kind: feature`, as spec C4 and G-7 require: four existing test modules gain cases and one existing case in
`scripts/test_check_workflow_permissions.py` changes its expected input list, which `protect-tests.sh` would
refuse under `kind: fix`. The discipline of a fix is kept by hand: step 1 writes every case and records which
are red before step 2 writes any code, and `scripts/test_check_artifact_chain.py` receives additions only
(spec R-4's `--numstat` clause).

`risk-class: medium`, the intent's class: the change loosens one rule of the approval chain under a condition
read from the ledger, so the tech lead's eye is on this plan as it was on the spec.

No engineer interview: the owner is the only human and works from a phone, so the repository's own record
stood in for it (`CLAUDE.md` conventions, the lessons named under Risks, the spec's gotchas G-1 to G-8, and
the three owner answers on the intent).

## Files that change
- scripts/check_artifact_chain.py — the per-artifact block under "Approving and superseding are both human acts" splits by status: `approved` unchanged; `superseded` skips `av.is_valid(name, approved_by)` only where the ledger holds a `-> delegated` line for the artifact whose actor is that handle (revision 1, deviations 3 and 6), keeps the existing `-> superseded` ledger rule (actor holds the artifact's role) and records that line's actor as the retirer; the author/trailer check on the `-G '^status: superseded$'` commit compares `Approved-Actor` to the retirer, not to `approved-by`, and calls `verify_dispatch_run(..., retired=True)` (R-1, R-2, R-3). `verify_dispatch_run` gains `retired=False`: with `retired=True` the title must parse under `RUN_NAME_RE` with `mode == "retire"` (else the existing `does not name` refusal, naming the mode) and the `artifact in title` line is skipped; the slug binding, the four-field check and the no-token fallback untouched (R-3, G-2). The comment above the block rewritten to say who is judged on each status
- scripts/test_check_artifact_chain.py — additions only: `class RetiredDelegatedItem` with a helper `_retire_agent_signed(root, wd, actor, trailers=None)` (on `_base_delegated_repo`, cut `work/demo`, set the three artifacts `superseded` with `approved-by` kept, append `<old> -> superseded | <actor>` lines, commit by the human identity or, with trailers, as `_reapprove_with_trailers` shapes it: actor author, bot committer, both trailers) and five cases: `test_human_retirement_of_an_agent_signed_item_passes` (R-1), `test_agent_actor_on_the_retiring_line_fails_naming_the_line` (R-2, counts `FAIL:` lines naming spec.md), `test_tap_retirement_with_trailers_passes` (R-3), `test_tap_retirement_by_a_handle_outside_the_role_fails` (R-3, a pin), `test_strict_mode_still_refuses_a_superseded_artifact` (R-4, a pin); `DispatchAttestation.test_a_retire_run_verifies_any_artifact_and_an_approval_run_does_not` (R-3: `_verify(run, slug="demo", artifact="spec.md", retired=True)` with title `approve intent.md (retire) on demo by @luissiviero` is `True`; the same title with `(supervised)` is `False` with `does not name` in the detail)
- scripts/approve.py — `artifacts` becomes `nargs="*"` with an explicit usage error when empty and `--retire` is absent (G-4); new `--retire` and `--next SLUG` (default `None`; `--next ""` is blank); `--retire` refuses `--delegate` and `--activate` with the spec's wordings; validation before any write: every present artifact of `ARTIFACTS` (or the ones named) is `approved`, `delegated` or `superseded` (the last skipped as a no-op), the handle holds each one's role, `--next` matches `check_artifact_chain.SLUG_RE`, differs from the slug, names an on-disk `work/<next>/intent.md` not `superseded`; writes `status: superseded` only, a `<old> -> superseded` ledger line each, and the pointer per spec D3 (repoint; clear when it names the retired slug; otherwise leave with a note); `--from-dispatch` writes `retired=`, `run-id=`, `actor=` to `$GITHUB_OUTPUT`; the human-commit hint names `.sdlc/active` when it changed; the module docstring gains the mode (R-5, R-6). The import line becomes `from check_artifact_chain import ROOT, SLUG_RE, front_matter` (G-5)
- scripts/test_approve.py — new `class Retire` on `make_repo()` (its three artifacts are `approved`; a helper flips one to `delegated`/`claude` or to `in-review` as a case needs) with the fifteen cases spec R-5 and R-6 name: `test_retires_every_present_artifact_and_keeps_approved_by` (then `check_artifact_chain.py --slug demo --base main` from a retiring branch ends `CHAIN: PASS`), `test_a_delegated_artifact_is_retired_from_delegated`, `test_refuses_an_in_review_artifact_and_writes_nothing`, `test_a_handle_without_a_role_is_refused_before_writing`, `test_already_superseded_is_a_noop`, `test_refuses_delegate_and_activate`, `test_agent_session_is_refused`, `test_from_dispatch_writes_retired_to_github_output`, `test_dry_run_writes_nothing`, `test_next_repoints_the_pointer`, `test_blank_next_clears_a_pointer_naming_the_item`, `test_a_pointer_at_another_item_is_left_alone`, `test_next_naming_no_item_is_refused`, `test_next_naming_a_retired_item_is_refused`, `test_next_with_a_traversing_slug_is_refused`
- scripts/approve_dispatch.py — `check_actor(..., mode="retire", ...)`: requires `slug` and `root`-relative `work/<slug>/`, lists the chain artifacts present there (`ARTIFACTS` order: intent.md, spec.md, plan.md, incident.md), refuses when none, and requires `av.is_valid(name, login)` for each, naming the first refused; `commit(..., mode=None)`: subject `[slug] Retire as actor` when `mode == "retire"`, otherwise unchanged; `main()` threads `--mode` into `commit`; the module docstring's usage lines gain `--mode` on `--commit` (R-7, R-8)
- scripts/test_approve_dispatch.py — new `class Retire` on `make_repo()` (plus `write()` for the artifacts it needs, and an approvers file variant where the actor holds `product-owner` only): `test_retire_requires_every_present_artifacts_role`, `test_retire_with_every_role_passes`, `test_retire_without_a_slug_is_refused`, `test_retire_subject_and_trailers`, `test_retire_commits_the_pointer_and_the_regenerated_indexes` (`gen_index.py --check` on the committed tree, the way `Commit.test_commit_regenerates_both_indexes` does it), `test_the_workflow_requires_an_explicit_slug_for_a_retirement` (asserts the Resolve step's retire condition and its message literally, as the grant case does)
- .github/workflows/approve.yml — on rule 3's never-edit list; edited under the unlock (`knowledge/lessons/control-plane-unlock-is-advisory.md`), gated by the owner's label and click (spec C2): `mode` options `[supervised, delegated, retire]` and description; `artifact` description gains "ignored for retire"; new input `next` (string, optional, "retire only: the slug to point .sdlc/active at; blank clears a pointer naming the retired item"); the Resolve step sanitises `NEXT` like `SLUG` and adds a second condition line `[ -z "$slug" ] && [ "$MODE" = retire ]` with `a retirement must name its slug explicitly` (G-8: the grant line is not edited); the Approve step builds `"$SLUG" --retire --as "$ACTOR" --from-dispatch "$GITHUB_RUN_ID" --next "$NEXT" [--note]` when `MODE = retire`; the Commit step passes `--mode "$MODE"` and writes a `Retired` summary; `run-name` byte-identical; the header comment gains three lines on the retirement (R-9, D4)
- scripts/test_check_workflow_permissions.py — `ApproveWorkflow.test_offers_the_four_inputs` renamed `test_offers_the_five_inputs`: `["artifact", "mode", "next", "note", "slug"]`, mode options `["supervised", "delegated", "retire"]`; nothing else in the class changes (R-9)
- docs/sdlc/github-setup.md — the "Or approve from the Actions tab" paragraph gains the retirement: `mode` `retire` with an explicit `slug` and a `next` input, one commit that supersedes every present artifact, writes the ledger lines, moves the pointer and regenerates the indexes; the web-editor route still valid and still stale (R-12)
- docs/sdlc/handoff/HANDOFF.md — the bullet beginning "Retiring an item is a human act, from the web editor today" rewritten: the tap first, the web editor second, and the clean-up advice corrected (an in-progress pull request may name a retired item once this lands; a pull request carrying code may not); a new Task state section and seed prompt on completion, per the session protocol (R-12)
- knowledge/lessons/human-commits-leave-indexes-stale.md — "Where it is enforced": the tap route is closed for approvals (`approve-tap-regenerates-index`) and retirements (this item); the web-editor route stays open and the pointer stays (R-12)
- work/retire-delegated-items/spec.md — R-1 and D1 amended under deviation 3 and revision 1 (added to this list by deviation 5: the plan review on #92 found it changed and unlisted)
- work/retire-delegated-items/revisions/1.md — the consensus record for the R-1 amendment (deviation 5)
- docs/sdlc/rules/60-lessons.md, CLAUDE.md, GEMINI.md, AGENTS.md — the indexes lesson's pointer line corrected to what the code does since `approve-tap-regenerates-index` (a tap regenerates; the web editor does not), and the three renders regenerated (deviation 5; the plan review found the lesson contradicting the code two paragraphs above the line this item added)
- work/retire-delegated-items/plan.md — this plan; its deviations log
- work/retire-delegated-items/log.md — one ledger line per gate
- work/retire-delegated-items/index.md — regenerated
- work/index.md — regenerated

Not in the list, on purpose: `.sdlc/`, `.claude/hooks/`, `scripts/checks/`, `scripts/sign.py`, `scripts/delegated_merge.py`
and `scripts/log_ledger.py` (spec R-11). No *new* rules-fragment line either (spec Not doing, the adopter cap):
the one line under `docs/sdlc/rules/` that changes is an existing pointer reworded in place, and the
adopter's render measured 120 lines before and after (deviation 5).

## Release-gated
(none)

## Order of work (each step independently verifiable)
1. **Write every case, run the suite, record the red set.** All four test modules from the list above, in
   one commit before any code. Expected red before step 2: the chain module's R-1, R-2 and R-3 pass cases and
   the retire attestation case (four), every `Retire` case in `test_approve.py` (fifteen, `--retire` is unknown),
   every `Retire` case in `test_approve_dispatch.py` except the workflow-text one (five; the sixth is red
   too until step 5), and `test_offers_the_five_inputs` (one): twenty-six red. Expected green as pins: R-3's
   wrong-handle case and R-4's strict-mode case. The observed count goes in this plan's deviations log if it
   differs (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`). Verifiable:
   `python3 -m unittest scripts.test_check_artifact_chain scripts.test_approve scripts.test_approve_dispatch scripts.test_check_workflow_permissions 2>&1 | tail -3`
   reports the failures and errors; the two pins are not among them.
2. **The check.** `scripts/check_artifact_chain.py` as listed. Verifiable: the four chain cases from step 1
   green; every pre-existing case in the module green; `git diff origin/main --numstat -- scripts/test_check_artifact_chain.py`
   shows `0` in the deletions column.
3. **The script.** `scripts/approve.py` as listed. Verifiable: the fifteen `Retire` cases green; the three
   pre-existing classes green; `python3 scripts/approve.py demo --retire --dry-run` from a `test_approve.make_repo()`
   tree prints three `would retire` lines and touches nothing.
4. **The dispatch helper.** `scripts/approve_dispatch.py` as listed. Verifiable: the five `Retire` cases
   that do not read the workflow green; `Mode` and `Commit` green unmodified.
5. **The workflow, under the unlock.** `.github/workflows/approve.yml` and the one edited workflow-permissions
   case. Verifiable: `test_the_workflow_requires_an_explicit_slug_for_a_retirement`, `test_offers_the_five_inputs`
   and `test_run_name_still_matches_the_checker_that_parses_it` green; `scripts/checks/workflow-permissions.sh`
   and `scripts/checks/workflow-yaml.sh` pass; `git diff origin/main -- .github/workflows/approve.yml | grep '^[-+]run-name'`
   prints nothing.
6. **The documents.** The three files as listed, plus this item's Task state in the handoff. Verifiable:
   spec R-12's three greps; `python3 scripts/check_okf.py` ends `0 warnings`.
7. **The loop, the review, the ready flip.** `python3 scripts/gen_index.py && python3 scripts/gen_context_files.py`;
   `git add -A`; `scripts/verify.sh`; commit; `python3 scripts/check_artifact_chain.py --base origin/main --slug retire-delegated-items`
   (strict mode from here on, so the plan must be approved before this passes); `scripts/run_evals.sh`;
   `python3 scripts/check_okf.py`; the adopter cap (`bash scripts/adopt.sh "$S/adopt"` into scratch, then
   `gen_context_files.py --root "$S/adopt"` at or under 120, the docs change adds no rules line so this is a
   confirmation); push; `/sdlc-review` on a model other than the writer's, findings fixed and re-reviewed until
   `Important: 0`; the last lines pasted in the pull request; ready once. Verifiable: `VERIFY: PASS`, `CHAIN: PASS`,
   `EVALS: N pass, 0 fail`, `OKF: N docs, 0 warnings`, and the ledger line naming the writer and the reviewer models.

## Risks
- Risk: the status split in step 2 leaves a path where `superseded` skips the ledger rule as well as the
  approver rule, so an agent-actored retirement passes → mitigation: R-2 counts `FAIL:` lines and requires
  the ledger message; R-3's wrong-handle pin and the pre-existing `test_superseded_without_a_ledger_line_by_a_valid_approver_fails`
  stay green; the security reviewer reads the split (spec C3).
- Risk: the `retired=True` waiver in `verify_dispatch_run` is reached for an `approved` artifact by a wrong
  call site → mitigation: the argument is passed only from the `superseded` branch; the attestation case
  asserts a `(supervised)` title is refused under the waiver and the pre-existing different-artifact case
  asserts the binding still holds without it.
- Risk: `nargs="*"` on `artifacts` lets `approve.py demo` (no artifact, no `--retire`) fall through to an
  approval of nothing → mitigation: an explicit usage error, exit 1, with its own case in `Retire`
  (`test_refuses_delegate_and_activate` is the neighbour; the no-artifact case is added to it as a second
  assertion rather than a sixteenth method, or named in the deviations log if it becomes one).
- Risk: the workflow edit is on the never-edit list → mitigation: edited under the unlock, which logs it;
  the owner's label and click gate it; the change is confined to inputs, three shell lines and one flag; the
  run-name is proven byte-identical in step 5.
- Risk: a Bash command that names `scripts` near a write, or names the approval script, is refused by
  `require-plan.sh` or `protect-approvals.sh` even with this plan approved → mitigation: edits through the
  Edit/Write tools, test runs through `python3 -m unittest` with module names; no `sed -i` on those paths.
- What this could break: a retired item that was red becomes green (intended); a strict-mode pull request
  naming a retired item stays red (intended, D5); nothing on the approval path changes, proven by the
  pre-existing classes running unmodified.
- Options considered and not taken: a separate `retire.py` (the owner's first answer chose `--retire`);
  an `all` option on the `artifact` input (D4: the run-name shape would change and route B parses it);
  opening strict mode (D5, C1).

## Proof
- `scripts/verify.sh` green: `VERIFY: PASS (<sha>)`.
- Spec rows → tests: R-1 → `RetiredDelegatedItem.test_human_retirement_of_an_agent_signed_item_passes`;
  R-2 → `test_agent_actor_on_the_retiring_line_fails_naming_the_line`; R-3 → `test_tap_retirement_with_trailers_passes`,
  `test_tap_retirement_by_a_handle_outside_the_role_fails`, `DispatchAttestation.test_a_retire_run_verifies_any_artifact_and_an_approval_run_does_not`;
  R-4 → `test_strict_mode_still_refuses_a_superseded_artifact` and the `--numstat` clause; R-5 → the first
  nine `test_approve.Retire` cases; R-6 → the six `--next` cases; R-7 → `test_approve_dispatch.Retire`'s three
  role cases; R-8 → `test_retire_subject_and_trailers`, `test_retire_commits_the_pointer_and_the_regenerated_indexes`;
  R-9 → `test_offers_the_five_inputs`, `test_run_name_still_matches_the_checker_that_parses_it`,
  `test_the_workflow_requires_an_explicit_slug_for_a_retirement`; R-10 → `test_retire_commits_the_pointer_and_the_regenerated_indexes`
  and `grep -c render_all` unchanged; R-11 → the `git diff --stat` on the untouched paths prints nothing,
  `scripts/run_evals.sh --only hook-blocks-agent-approval`, `test_sign.py`; R-12 → the three greps and OKF;
  R-13 → the last lines in the pull request.
- Manual / browser / screenshot / eval: the production observation is the owner's first `mode: retire` tap
  on `main`, which this plan cannot run; the run's summary and the commit it pushes are the evidence, recorded
  in the ledger of the item it retires.

## Rollback
- Revert the pull request's merge commit: every change is in tracked files, no data moved, no index format
  changed. A retirement already made by the tap stays valid after a revert only if its artifacts were
  human-approved (an agent-signed one goes red again, the state before this item).

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-14 step 1: twenty-five red, not twenty-six. `test_approve_dispatch.Retire.test_retire_with_every_role_passes`
  is green before the code because `check_actor` treats an unknown mode as supervised and the actor holds
  every role; it stays as the pin it is. The other twenty-five and the two chain pins are as predicted
  (chain 3 failures and 1 error, approve 15, dispatch 5, workflow-permissions 1).
- 2026-09-14 step 1: two fixture facts the file list had wrong. `test_approve.make_repo()` writes its three
  artifacts `in-review`, so `Retire.setUp` approves them with the script and commits before each case; and
  `own_artifact` counts `.sdlc/active` as the item's own file only while it names the item, so a retirement
  that moves the pointer is strict on a pull request. The R-5 chain case therefore points the pointer at
  another live item on the base first, and the `RetiredDelegatedItem` fixture does the same. The tap runs
  on `main` and never meets this; the handoff bullet in step 6 says so.
- 2026-09-14 step 2, deviation 3: the pre-existing `InProgressChain.test_superseded_with_an_invalid_approver_fails`
  went red under the spec's R-1 as written (a superseded plan.md with `approved-by: claude[bot]` and a valid
  human retiring line must still fail). The intent's Must keeps every existing case green unmodified, so the
  rule is narrowed rather than the case changed: `approved-by` is skipped only when the ledger shows the
  artifact signed under a grant (a `-> delegated` line for it, or a retiring line from `delegated`); with
  no signature line the approver check stays. The signature is read from the whole ledger, not from the
  retiring line alone, so an agent-actored retiring line on a signed artifact is still one ledger fault (R-2).
- 2026-09-14 step 3, deviation 4 (logged after the plan review on #92 named it): `approve.py` gained one
  refusal the spec's list does not name, `--next applies to --retire only` (a `--next` outside `--retire`
  would otherwise be silently ignored), now with an assertion in `Retire.test_refuses_delegate_and_activate`;
  and the approval path's ledger writing moved into `append_ledger()`, shared with `retire()`, so the two
  routes cannot drift in the header they create. Behaviour on the approval path is unchanged (the three
  pre-existing classes green unmodified).
- 2026-09-14 step 7, deviation 5, from the plan review on #92 (plan-reviewer on Opus, three Important):
  (a) `work/retire-delegated-items/spec.md` was changed by step 2 and not on this list; listed now.
  (b) The amendment of an approved spec's requirement is outside the deviation rule ("a spec requirement
  touched" needs a consensus record, `.claude/skills/sdlc-run/SKILL.md` "The revision rule"); the record is
  `work/retire-delegated-items/revisions/1.md` with the trigger, the proposal and both reviewers' sections,
  and on a supervised item the human's acceptance is a ledger line the owner writes, asked for on #92.
  (c) `knowledge/lessons/human-commits-leave-indexes-stale.md` still said "nothing in that path runs
  gen_index.py" two paragraphs above the line this item added, and its title and pointer line said a tap
  commits no index; all three now say what the code does (the tap regenerates, the web editor does not), so
  `docs/sdlc/rules/60-lessons.md` and the three renders change and are listed. The review's two bug nits are
  taken: the trailer route no longer reports a missing retirer twice (a new R-2 case on that route), and the
  seed prompt in the handoff is refreshed to this item's state.
- 2026-09-14 step 7, deviation 6, from the security review on #92 (security-reviewer on Opus, no Important,
  four nits, all taken with a case each): the signature that spares `approved-by` is the `-> delegated` line
  whose actor is that handle, not any such line (spec R-1, D1 and revision 1 amended again); a partial
  retirement leaves the pointer and refuses `--next` (spec Interfaces and Failure modes); the chain check's
  `append:` hint never names the agent's handle; and `mode: retire` is dispatched from the default branch
  only, like a grant, because a retirement moves the pointer and a branch whose diff moves it is strict
  (spec R-7). No file joins or leaves the list. Two pre-existing defects the reviews named are out of this
  plan and filed in the handoff: `EXEMPT` and the `gh`-less crash on a token. The spec's R-1 row and D1 are amended to say so, in this commit; the owner is told on the pull
  request, since the spec was approved before the amendment. This spec read the case and did not see it
  (gotcha missed).
