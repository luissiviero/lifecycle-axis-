---
type: sdlc/spec
id: batch-b-followups
title: Close the three leftovers Batch B surfaced
description: "Requirements and design for the sdlc-gate trust step, the never-approve entry for the adopter placeholder with its test and docs, the superseded-predecessor rule in the chain check, and the handoff state update."
stage: design
status: approved
reads: intent.md
approved-by: luissiviero
approved-on: 2026-09-05
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Drafted from the intent, the follow-up notes on pull requests 37 and 38, agent-evals.yml lines 42-57, check_artifact_chain.py lines 181-198, test_check_artifact_chain.py InProgressChain, test_adopt.py test_handle_rewritten and approvers.py; reviewed by the orchestrator."
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/38
tags: [followups, sdlc-gate, adopt, chain-check, control-plane]
timestamp: 2026-09-05T05:25:00Z
---
# Spec: close the three leftovers Batch B surfaced

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) trusted triage; (2) placeholder cannot approve, documented and tested; (3) a retired
chain passes the in-progress check, with a regression test; (4) `HANDOFF.md` current.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `.github/workflows/sdlc-gate.yml` gains, immediately before the "Triage failure" step, a step with the same `run:` body as `agent-evals.yml`'s "Trust the checkout" step and the condition `if: failure() && env.HAS_CLAUDE_AUTH == 'true'`; no other line of the workflow changes | 1 | `grep -c 'hasTrustDialogAccepted' .github/workflows/sdlc-gate.yml` prints `1`; `scripts/checks/workflow-yaml.sh` and `workflow-permissions.sh` pass; `git diff origin/main -- .github/workflows/sdlc-gate.yml | grep -c '^-[^-]'` prints `0` (additions only); manual: the next failing run's triage log has no "has not been trusted" line |
| R-2 | `.sdlc/approvers.yaml` lists `<your-github-handle>` under `never-approve` (the owner's edit); `scripts/test_adopt.py::test_handle_rewritten` asserts `approvers.py --has-role tech-lead '<your-github-handle>'` exits 1 on the fresh target and that the copied file carries the entry; `docs/sdlc/github-setup.md` step 1 and `knowledge/decisions/adopt-script.md` say the placeholder cannot approve until replaced | 2 | `python3 scripts/approvers.py --has-role tech-lead '<your-github-handle>'` exits 1 in this repo; `python3 scripts/run_tests.py -p test_adopt.py` green; `grep -c 'cannot approve' docs/sdlc/github-setup.md knowledge/decisions/adopt-script.md` prints `1` each; `grep -c 'a name that is nobody' docs/sdlc/github-setup.md` prints `0` |
| R-3 | In `check_artifact_chain.py`'s in-progress stage-order rule, a predecessor whose status is `superseded` counts like `approved`; the error text names both accepted statuses; a new test `InProgressChain::test_fully_superseded_chain_passes` (all three artifacts `superseded`, three ledger lines by a valid approver) passes and the three existing supersession tests still pass | 3 | `python3 scripts/check_artifact_chain.py --base 2190c0c --slug sdlc-kit-phase-1` ends `CHAIN: PASS`; `python3 scripts/run_tests.py -p test_check_artifact_chain.py` green with one more test than `main` |
| R-4 | `docs/sdlc/handoff/HANDOFF.md` task state: Batch B merged (PRs #31-#37), Step 0 done (commits 568c5bd..07b4da9, indexes on PR #38), this item open; nothing else in the file changes | 4 | `grep -c 'batch-b-followups' docs/sdlc/handoff/HANDOFF.md` ≥ `1`; `grep -c 'Step 0 (owner: supersede' docs/sdlc/handoff/HANDOFF.md` prints `0` |
| R-5 | Suite green | all | `VERIFY: PASS`; `CHAIN: PASS` with `--slug batch-b-followups`; `EVALS: N pass, 0 fail`; `OKF: N docs, 0 warnings`; test count grows by one over `main` |

## Design
### Architecture / data flow
Nothing new moves. One workflow step, one list entry, one comparison.

**D1. Trust step (R-1).** Inserted at `sdlc-gate.yml:45`, before `- name: Triage failure`:
```
      - name: Trust the checkout so the repo's settings apply to claude -p
        if: failure() && env.HAS_CLAUDE_AUTH == 'true'
        run: |
          python3 - <<'PY'
          import json, os
          path = os.path.expanduser("~/.claude.json")
          data = {}
          if os.path.exists(path):
              with open(path) as f:
                  data = json.load(f)
          data.setdefault("projects", {}).setdefault(os.environ["GITHUB_WORKSPACE"], {})["hasTrustDialogAccepted"] = True
          with open(path, "w") as f:
              json.dump(data, f)
          PY
```
The condition mirrors the triage step's so the file is written only when triage will run. No secret is in
this step's environment. Control plane: the PR asks for `control-plane-approved`.

**D2. Never-approve (R-2).** `.sdlc/approvers.yaml:26` becomes
`never-approve: ["claude[bot]", "github-actions[bot]", "claude", "<your-github-handle>"]`. The session may
not write this file (the hooks refuse it with or without the unlock), so the owner makes the edit from the
web editor on this branch after the plan is approved; the test and docs land in the same PR. `approvers.py`
already normalises and compares list entries, and `adopt.sh` copies the file verbatim before rewriting the
role handles, so the copied target inherits the entry. `test_handle_rewritten` flips its assertion on
`a.has_role.returncode` from `0` to `1` and adds `assertIn('"<your-github-handle>"', approvers_text)`.
`github-setup.md` step 1: "Until you do, nothing can approve the example item: the placeholder is listed
under `never-approve`, so `approve.py --as '<your-github-handle>'` is refused and the plan gate stays
closed." `adopt-script.md`'s C1 bullet: the entry exists (`work/batch-b-followups`).

**D3. Stage-order rule (R-3).** `check_artifact_chain.py:194`: `if prev_status != "approved":` becomes
`if prev_status not in ("approved", "superseded"):`, and the message reads `not 'approved' or 'superseded'`.
Rationale: the rule protects the order in which humans approve; a superseded predecessor was approved and
then retired, which the supersession branch (`:215-260`) already validates with a ledger line by a valid
approver. Test: `_make_repo` on `main`, then on a branch write all three artifacts with `status: superseded`
(keeping `approved-by`), append three `approved -> superseded` lines by `luissiviero`, commit, run with
`--slug demo --base main`; expect rc 0, `mode: in-progress`, `CHAIN: PASS`.

**D4. Handoff (R-4).** Two lines in the "Task state" section and the "Work-item order" line; the rest of
the file is history and stays.

### Interfaces (APIs, events, schemas) — exact shapes
No interface changes. `check_artifact_chain.py`'s output line for the stage-order error changes text only.

### Data and migrations
None.

### Failure modes and how they surface
- The trust step fails to write `~/.claude.json` → the triage step still runs, untrusted, as today.
- An adopter skips step 1 → `approve.py` and the plan-gate hook refuse with a message naming `approvers.yaml`.
- A chain with a `draft` or `in-review` predecessor still fails the stage-order rule (unchanged).

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: a workflow edit by the session — policy: rule 3 — contradiction? no (WI-9 precedent under the label)
  — owner: luissiviero — resolution: `control-plane-approved` on the PR.
- C2: `.sdlc/approvers.yaml` is a never-unlock file — policy: `protect-paths.sh` human-only list —
  contradiction? no — owner: luissiviero — resolution: the owner edits line 26 from the web editor on this
  branch (plan step 5); the session never touches the file.
- C3: the adopter's first hour changes: approving `_example` is impossible until the handle is replaced —
  policy: `human-only-approvals.md` — contradiction? no, it is that policy applied — owner: luissiviero —
  resolution: intent Q1.

## Open questions carried from intent.md
- Q1 (blocked plan gate until the handle is replaced): proposed yes; D2 assumes it.
- Q2 (one item, three requirements): proposed yes; this spec assumes it.

## Decisions (ADR-style: context → decision → consequences)
- D-a: copy the trust step verbatim rather than factor it into a script → the two workflows stay
  independently readable; a later change edits both (noted in the step's comment).
- D-b: widen the stage-order comparison rather than special-case a "fully superseded" chain → a partially
  superseded chain (intent superseded, spec approved) also passes, which is the state during a staged
  retirement; the supersession branch still validates each superseded artifact.
- D-c: the owner edits `approvers.yaml`, the session ships the test that requires it → the test is red on
  the branch until the owner's edit lands (plan step 5 precedes step 8); the PR body says so.

## Gotchas found while reading the codebase
- `HAS_CLAUDE_AUTH` is a job-level boolean string; step `if:` compares it to `'true'` (as the triage step does).
- `test_handle_rewritten` covers two scenarios (`default` and `approve`); only the `approve` scenario runs
  `--has-role`, and it runs it before replacing the handle, which is exactly the moment R-2 changes.
- `_make_repo` in the chain tests seeds a fully approved `demo` item on `main`; the new test only adds a
  branch commit, so it follows the three existing supersession tests one-for-one.

## Not doing
- Making the supersession branch require all three artifacts to be superseded together (staged retirement
  stays allowed).
- Any other B13 fault; the review workflow's base-branch restore (by design, `pr-review.yml:60`).
