---
type: sdlc/plan
id: approval-gate
title: Only a human can flip an artifact to approved
description: New protect-approvals.sh hook, approver check in require-plan.sh, wiring in three settings files, tests, eval and decision record.
stage: build
status: approved
kind: feature
reads: spec.md
approved-by: luissiviero
approved-on: 2026-09-05
risk-class: low
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, approvals, chain-check, approve, consensus-item-1]
timestamp: 2026-09-04T21:49:27Z
---
# Plan: only a human can flip an artifact to approved (from intent.md 2026-09-04)

## Files that change
- .claude/hooks/protect-approvals.sh — (new) the hook from spec Design, verbatim from appendix A1; mode 100755
- .claude/hooks/require-plan.sh — after line 20: `approved-by` must hold the plan's role (spec Interfaces)
- .claude/settings.json — new entry after lines 13 and 22 (both matchers, after `protect-tests.sh`)
- docs/sdlc/templates/claude-settings.json — same entry after lines 10 and 19 (`test_adopt.py:307` compares byte for byte)
- .gemini/settings.json — `sdlc-protect-approvals` entry after line 11
- scripts/test_protect_approvals.py — (new) the eight block and six allow cases; builders copied from `test_bash_plan_gates.py:37-52`
- scripts/test_hooks_baseline.py — `RequirePlanHook`: four approver cases (spec R-6)
- scripts/test_gemini_wiring.py — add `protect-approvals.sh` to the required tuple at line 81
- evals/cases/hook-blocks-agent-approval.yaml — (new) Edit to `status: approved` and Bash `approve.py` both refused by the real hook
- evals/cases/approve-refuses-in-agent-session.yaml — one more line: the Bash hook refuses `python3 scripts/approve.py ...`
- knowledge/decisions/human-only-approvals.md — (new) why a hook, why no unlock, the demotion residual, the web-editor route
- knowledge/decisions/index.md — link the new record
- docs/sdlc/rules/10-hard-rules.md — rule 3 (line 16) names `status: approved`, `approved-by`, `approved-on` and `scripts/approve.py`
- docs/sdlc/rules/00-chain.md — lines 21-22: "Only a human sets `status: approved`" gains "a hook refuses it from an agent"
- docs/sdlc/README.md — enforcement rows 95 and 107 name `protect-approvals.sh` and the approver check
- CLAUDE.md — regenerated
- GEMINI.md — regenerated
- AGENTS.md — regenerated
- work/index.md — regenerated
- work/approval-gate/index.md — regenerated
- work/approval-gate/log.md — gate entries
- work/approval-gate/plan.md — deviations log

## Release-gated
(none)

## Order of work (each step independently verifiable)
1. Preflight from a second shell: `bash -c '. .claude/hooks/_lib.sh; type fm_value artifact_role approver_has_role' <<< "{}"` prints three function definitions (the `control-plane-visibility` helpers are present) and `grep -c "approved-by: luissiviero" scripts/test_hooks_baseline.py scripts/test_bash_plan_gates.py` is non-zero (the `front-matter` fixtures are in). Stop if either fails.
2. Write `.claude/hooks/protect-approvals.sh` (one Write, then `bash -n`, `chmod +x`). Do not wire it yet.
3. Write `scripts/test_protect_approvals.py`; `python3 scripts/run_tests.py -p test_protect_approvals.py` ends `OK` (the harness runs the hook by path, wiring not needed).
4. Edit `require-plan.sh` after line 20; add the four `RequirePlanHook` cases; `python3 scripts/run_tests.py -p test_hooks_baseline.py -p test_bash_plan_gates.py -p test_gemini_wiring.py` ends `OK`. Run it from a second shell before this session's next tool call, since the live hook changed.
5. Wire the three settings files and extend `test_gemini_wiring.py:81`; `python3 scripts/run_tests.py -p test_gemini_wiring.py -p test_adopt.py -p test_control_plane_hardening.py` ends `OK`.
6. Evals: new `hook-blocks-agent-approval.yaml`; extend `approve-refuses-in-agent-session.yaml`; `scripts/run_evals.sh --kind hook` ends `0 fail`.
7. Docs and decision record; `python3 scripts/gen_context_files.py && python3 scripts/gen_index.py`; `wc -l CLAUDE.md` under 120; `python3 scripts/check_okf.py` ends `0 warnings`.
8. `scripts/verify.sh`, chain check, log entry, PR with `Work-Item: approval-gate`; ask the owner for `control-plane-approved`. Restart the session after merge.

## Risks
- Risk: this is the last hook item and depends on `fm_value`/`artifact_role`/`approver_has_role` from `control-plane-visibility` and on the `approved-by: luissiviero` fixture and `fake_repo` approvers copy from `front-matter` → mitigation: step 1 preflight; land strictly after both; any helper drift goes in the deviations log.
- Risk: a defect in the hook blocks this session's own artifact drafting once wired → mitigation: tests pass unwired (steps 2-4) before wiring (step 5); wiring is read at session start, so the session must be restarted after it lands and the first action in the new session is a Write of `status: in-review` to a scratch artifact.
- Risk: `require-plan.sh` now fails closed without `.sdlc/approvers.yaml` in the fake repo → mitigation: `front-matter`'s `fake_repo(approvers_yaml=None)` copies it; step 1 checks.
- Risk: the new file lands without its exec bit (happened before via the connector push) → mitigation: commit with `git update-index --chmod=+x`; `test_gemini_wiring.py:70` catches it.
- What this could break: nothing outside the hooks; an approved plan by an approver not in `tech-lead` (none today) would start blocking implementation.
- Options considered and not taken: a `python3` call from the hook (import-time `git rev-parse`, Windows Store stub); honouring the unlock for the kit repo (would leave the owner's own sessions able to self-approve); blocking every write that touches the front matter (would stop drafting).

## Proof
- `scripts/verify.sh` green: ends `VERIFY: PASS (<sha>)`
- Spec rows → tests: R-1, R-2, R-5 → `scripts/test_protect_approvals.py::EditBranch`; R-3, R-4 → `scripts/test_protect_approvals.py::BashBranch`; R-6 → `scripts/test_hooks_baseline.py::RequirePlanHook`; R-7 → `test_gemini_wiring.py`, `test_adopt.py`, `test_control_plane_hardening.py`; R-8 → `scripts/run_evals.sh --only hook-blocks-agent-approval` ends `EVALS: 1 pass, 0 fail, ...`; R-9 → `scripts/verify.sh`
- `python3 scripts/check_artifact_chain.py --base origin/main --slug approval-gate` ends `CHAIN: PASS`
- Manual / browser / screenshot / eval: in a fresh session, Edit `work/approval-gate/intent.md` to `status: approved` is refused; Bash `python3 scripts/approve.py approval-gate plan.md --as luissiviero` is refused; the owner's `approve.py` from their shell succeeds and `CHAIN: PASS` follows.

## Rollback
- Revert the PR; remove the three settings entries first if a session is wedged, then restart it. Nothing outside this repo changes.

## Deviations log (append during implementation; same commit as the deviation)
- 
