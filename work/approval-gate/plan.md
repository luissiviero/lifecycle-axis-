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
- .sdlc/active — set to `approval-gate` by the session after merging main (deviation 1)

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
- `.sdlc/active` was set to `approval-gate` by the session, not by `approve.py --activate`: the owner approves from a phone through the GitHub web editor, which cannot run the script. The file is added to `## Files that change` above (same practice as `deploy-gate`).
- Step 4's "second shell" was one atomic Bash call: copy the original aside, apply the edit, `bash -n`, run the full `scripts/run_tests.py` (443 tests), and restore the original on any failure. The hook stayed live for every later tool call.
- `scripts/run_tests.py -p a -p b` runs only the last pattern, so the per-module checks in steps 4 and 5 were run one module per call; the full suite covers them all.
- `scripts/test_protect_approvals.py` has 17 cases, not 14: the spec's list plus a `CLAUDECODE=` reassignment (R-3 names it), `approve.py` with `BASH_WRITE_GUARD=0` (spec D4), and a draft heredoc that never mentions approval (allow). The `superseded` Write case anchors its replacement at line start because `templates/intent.md` carries a commented `# status: draft | ...` line above the real field.
- Wiring is read at session start (spec, Risks), so this session ran to the end on the old hook set; the first check in the next session is the plan's manual proof (an Edit that flips an artifact to approved is refused).
- Review (PR #25, security): the spec's appendix A1 judged an Edit by the key lines in its new text, so a bare-value edit (`luissiviero` → `mallory` on an approved plan) or a `sed` rename passed. The edit branch now applies the edit to the current text and compares the resulting front matter; the Bash branch refuses any write candidate that is an already-approved artifact. Five tests added (22 in the module), the eval gains both cases, and the obfuscated-command residual (a split `approve.py` string) is recorded in `knowledge/decisions/human-only-approvals.md` with its backstops (the script's own `CLAUDECODE` refusal and CI's author and ledger checks).
- Review (PR #25, second pass): a MultiEdit whose earlier edit plants a decoy `status:` line was named against the appendix's concatenated-text design; the result-based check already reads the front matter after all edits are applied, and it now judges every occurrence of each approval key in the resulting front matter, so a duplicated key inside the block cannot hide behind a first-match read. Three tests added (25 in the module).
- Review (PR #25, nits): `CLAUDECODE_RE` also matches GNU env's glued `-uCLAUDECODE` and `--unset=CLAUDECODE` forms (one test, 26 in the module). The spec's appendix A1 stays as approved (an approved artifact is not rewritten by the agent); a note above it points at the deviations and the decision record for the shipped design.
- Eval oracles: under `set -e`, a `! cmd` line that fails does not end the case, so the two evals of this item check exit codes explicitly. Older hook evals use the `! cmd` pattern and are worth a follow-up item; not widened here.
- A post-approval edit to `plan.md` must not add or remove the literal approval phrase (`status:` followed by `approved`): `check_artifact_chain.py` finds the approving commit with `git log -S` on that phrase, so the previous deviation entry, which quoted it, made CI attribute the approval to the agent's commit (artifact-chain red on 55cf5f5). Reworded here; the count now matches the owner's commit.
- 2026-09-05: luissiviero re-confirms the approval above after the agent's post-approval deviation entries; the front matter stays `status: approved`, and this human commit is the one the chain check attributes the approval to.
