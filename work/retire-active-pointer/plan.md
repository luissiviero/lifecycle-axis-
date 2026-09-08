---
type: sdlc/plan
id: retire-active-pointer
title: Pin the gate, teach the chain check three lines, write the retirement act down
description: "One test pins that a superseded plan closes the plan gate; check_artifact_chain.py gains the retired-pointer failure, the slug/pointer mismatch note and the base-ref check, each with a test; the rules fragment and the handoff carry the retirement act; no hook, workflow or skill is touched."
stage: build
status: delegated
kind: feature
reads: spec.md
approved-by: claude
approved-on: 2026-09-08
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/52
tags: [control-plane, active-pointer, plan-gate, chain-check, followup]
timestamp: 2026-09-08T15:20:00Z
---
# Plan: pin the gate, teach the chain check three lines, write the retirement act down (from intent.md 2026-09-07)

## Files that change
- scripts/check_artifact_chain.py — R-2 retired-pointer error, R-3 mismatch note, R-4 base-ref check, all in `main()` before the chain loop
- scripts/test_check_artifact_chain.py — new class `StalePointer` with the three cases R-2, R-3 and R-4 name
- scripts/test_hooks_baseline.py — `RequirePlanHook.test_blocks_when_plan_superseded` (R-1; pins existing behaviour, no hook edit)
- docs/sdlc/rules/00-chain.md — the retirement act, two lines at most (R-5; see risk 1)
- docs/sdlc/handoff/HANDOFF.md — the retirement routine next to the existing `.sdlc/active` bullet (R-5)
- CLAUDE.md — regenerated from the rules fragments
- GEMINI.md — regenerated from the rules fragments
- AGENTS.md — regenerated from the rules fragments
- work/retire-active-pointer/plan.md — this plan; its deviations log
- work/retire-active-pointer/log.md — ledger lines at each gate
- work/retire-active-pointer/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none)

## Order of work (each step independently verifiable)
1. **R-1, the pin.** Add `test_blocks_when_plan_superseded` to `RequirePlanHook` in `scripts/test_hooks_baseline.py`, shaped like `test_blocks_when_plan_in_review` (`:174-179`) with `status: superseded`. Verify: it passes against today's `require-plan.sh` (that is the point: the property already holds, and is now named).
2. **R-4, the base ref.** Write `StalePointer.test_unknown_base_ref_is_one_clear_failure` first and watch it fail (today: exit 0, a false in-progress note). Then in `main()` check `diff.returncode` at `check_artifact_chain.py:506`; on non-zero print the R-4 line and `CHAIN: FAIL`, exit 1, the way `:479-481` does for an empty pointer. Verify: the new case passes; every existing case in the file passes.
3. **R-2, the retired pointer.** Write `test_retired_active_item_is_one_clear_failure` (intent.md `superseded`, `.sdlc/active` naming it, run with `--slug` naming the same item) and watch it fail. Then, after the slug is resolved, read `.sdlc/active` and `work/<active>/intent.md`'s front matter; if its status is `superseded`, append the R-2 error. Verify: the new case passes; exactly one `  FAIL:` line.
4. **R-3, the mismatch.** Write `test_slug_differs_from_active_is_a_note` (two items, `--slug` one, pointer the other) and watch it fail. Then append the R-3 note when `a.slug` is given and differs from the pointer. Verify: exit 0, one `  note:` line, `CHAIN: PASS`.
5. **R-5, the documents.** Add the retirement act to `docs/sdlc/rules/00-chain.md` (two lines) and the routine to `docs/sdlc/handoff/HANDOFF.md` next to its `.sdlc/active` bullet (`:150-151`). Regenerate with `python3 scripts/gen_context_files.py`. Verify: `scripts/checks/context-drift.sh`; `wc -l CLAUDE.md GEMINI.md AGENTS.md` each ≤ 120; the two greps in R-5.
6. **R-6, the loop.** `scripts/verify.sh`; `GH_TOKEN= GITHUB_TOKEN= python3 scripts/check_artifact_chain.py --base origin/main --slug retire-active-pointer` (see risk 4 for why the token is unset locally); `scripts/run_evals.sh`; `python3 scripts/check_okf.py`. Regenerate indexes. Paste the four last lines and the test counts before and after in the pull request.

## Risks
- Risk: `GEMINI.md` is at 116 lines against a cap of 120, and every line added to `00-chain.md` lands in all three context files → mitigation: the addition is two lines at most, measured with `wc -l` after regenerating; if any file exceeds 120, trim prose in the fragment (never a rule), per CLAUDE.md.
- Risk: R-4 changes what a bad `--base` does, from a silent pass to a failure → mitigation: both supported callers already pass a real ref (`VERIFY_CMDS` uses `--base HEAD`; CI fetches with depth 0 and passes `origin/$BASE_REF`), so only a misconfigured local run sees the new line, and the line names `--base HEAD`.
- Risk: R-2 fails every pull request while the pointer names a retired item → mitigation: by design (spec C1, D-3); the fix is a one-line edit of `.sdlc/active`, which an agent may make under the unlock with an audit line. The pointer names `retire-active-pointer` today, which is not retired, so this pull request is unaffected.
- Risk: with `GH_TOKEN` set and no `gh` binary, `verify_dispatch_run` (`check_artifact_chain.py:192`) raises `FileNotFoundError` and the chain check crashes; found in this session, in this container, on the intent's own dispatch-made approval → mitigation: local runs unset the token, which takes the documented author-rule fallback (`:187-188`); CI has `gh`. Fixing the crash is outside this plan's spec (a signed spec; the revision rule needs a blocking error, and this one has a workaround); the pull request proposes the two-line fix as a follow-up.
- Risk: `scripts/check_artifact_chain.py` is on `.sdlc/delegation.yaml`'s `locked-paths` → not a defect: `delegated_merge.py` refuses and the owner merges by hand; stated in the pull request.
- Risk: the Bash guard reads prose — a heredoc whose text mentions a protected status word is refused (spec G-10) → mitigation: every edit to a file that mentions those words is made with the Edit or Write tool.
- What this could break: nothing that runs today. The hook is not edited; the chain check's new lines are reached only by a bad base ref, a retired pointer or a mismatched slug, none of which the current tree has; the documents add prose.
- Options considered and not taken: editing `require-plan.sh` to refuse a retired item by name (already refused by `:35`; a protected path; spec D-2); a one-tap retire in `approve.yml` (protected path; follow-up item; spec D-4); changing `adopt.sh`'s `_example` seed (spec D-6); a new terminal status word (spec D-1).

## Proof
- `scripts/verify.sh` green
- Spec rows → tests: R-1 → `test_hooks_baseline.py::RequirePlanHook::test_blocks_when_plan_superseded`; R-2 → `test_check_artifact_chain.py::StalePointer::test_retired_active_item_is_one_clear_failure`; R-3 → `StalePointer::test_slug_differs_from_active_is_a_note`; R-4 → `StalePointer::test_unknown_base_ref_is_one_clear_failure`; R-5 → `scripts/checks/context-drift.sh`, `wc -l` ≤ 120 on the three context files, `grep -c superseded docs/sdlc/rules/00-chain.md` ≥ 1, `grep -c 'sdlc/active' docs/sdlc/handoff/HANDOFF.md` ≥ 2; R-6 → the four last lines in the pull request
- Manual / browser / screenshot / eval: none; every oracle is a test or a check

## Rollback
- Revert the pull request. Nothing is persisted outside the repository; no data, no workflow, no hook changes.

## Deviations log (append during implementation; same commit as the deviation)
- 
