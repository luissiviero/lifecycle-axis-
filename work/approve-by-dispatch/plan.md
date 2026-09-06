---
type: sdlc/plan
id: approve-by-dispatch
title: One tap in the Actions tab writes what approve.py writes
description: "Build approve.yml and approve_dispatch.py, teach approve.py --from-dispatch, and give the chain check and the merge script a trailer-verified route, so every approval and every delegation grant is one tap whose actor GitHub records server-side."
stage: build
status: delegated
kind: feature
reads: spec.md
approved-by: claude
approved-on: 2026-09-06
risk-class: low
record:
resource:
tags: [approvals, delegation, workflow-dispatch, control-plane, chain-check, auto-merge]
timestamp: 2026-09-06T17:30:00Z
---
# Plan: one tap in the Actions tab writes what approve.py writes (from intent.md 2026-09-06)

## Files that change
Every path that will change. Globs allowed. CI fails the PR if the diff touches anything else.
- .github/workflows/approve.yml — new; workflow_dispatch with the four inputs, `permissions: contents: write`, one checkout, run-name carrying actor/slug/artifact/mode (R-1, R-8)
- .github/workflows/sdlc-gate.yml — add `actions: read` to permissions and `GH_TOKEN` to the Artifact chain step's env (R-13)
- scripts/approve_dispatch.py — new; `--check-actor` role gate and `--commit` staged-path allowlist, author/committer split, trailers (R-2, R-4, R-8)
- scripts/test_approve_dispatch.py — new; ActorCheck, Commit, Mode (R-2, R-4, R-8)
- scripts/approve.py — add `--from-dispatch RUN_ID`, requiring `--as`, `GITHUB_ACTIONS=true` and a matching `GITHUB_RUN_ID` (R-3)
- scripts/test_approve.py — add ApproveFromDispatch, including the byte-comparison against a plain run (R-3)
- scripts/check_artifact_chain.py — add `dispatch_attestation` and `verify_dispatch_run`; the trailer route for the approval-author rule (R-5, R-6)
- scripts/test_check_artifact_chain.py — extend ApprovalAuthor, add DispatchAttestation (R-5, R-6)
- scripts/delegated_merge.py — split `check_grant_commit` into `_grant_route_a` and `_grant_route_b`; move the signature gate inside route A (R-7)
- scripts/test_delegated_merge.py — extend GrantCommit with the route-B cases and the unchanged route-A cases (R-7)
- scripts/check_workflow_permissions.py — allowlist `.github/workflows/approve.yml` for `contents: write` (R-1, C2)
- scripts/test_check_workflow_permissions.py — add SdlcGate; cover the new allowlist entry (R-1, R-13)
- evals/cases/gate-blocks-workflow-dispatch.yaml — new; an unattended session running `gh workflow run approve.yml` is blocked (R-9)
- knowledge/decisions/approve-by-dispatch.md — new; the decision record amending the two below (R-11)
- knowledge/decisions/human-only-approvals.md — amend: the tap is the human act (R-11)
- knowledge/decisions/delegated-mode.md — amend: decision 6's signature proxy is replaced by the run record (R-11, C4)
- knowledge/decisions/index.md — list the new record (R-11)
- knowledge/lessons/tests-carry-their-own-environment.md — new; rule 7, a mistake made twice in this pull request
- knowledge/lessons/index.md — list the new lesson (rule 7)
- docs/sdlc/rules/60-lessons.md — the pointer line for it (rule 7)
- .claude/skills/sdlc-intent/SKILL.md — ask for the tap, naming slug/artifact/mode (R-10)
- .claude/skills/sdlc-spec/SKILL.md — ask for the tap (R-10)
- .claude/skills/sdlc-plan/SKILL.md — ask for the tap (R-10)
- .claude/skills/sdlc-incident/SKILL.md — ask for the tap (R-10)
- .claude/skills/sdlc-run/SKILL.md — ask for the tap (R-10)
- docs/sdlc/rules/10-hard-rules.md — the tap is the human act; `approved` stays human-caused (R-10)
- docs/sdlc/rules/30-conventions.md — the dispatch route beside the shell and web-editor routes (R-10)
- docs/sdlc/README.md — the stage matrix names the tap (R-10)
- docs/sdlc/github-setup.md — the routine for running the workflow (R-10)
- docs/sdlc/handoff/HANDOFF.md — the routine for a new owner (R-10)
- CLAUDE.md — regenerated from the rule fragments (generated)
- GEMINI.md — regenerated (generated)
- AGENTS.md — regenerated (generated)
- work/approve-by-dispatch/plan.md — this file
- work/approve-by-dispatch/log.md — ledger lines for the plan gate and any deviation
- work/approve-by-dispatch/index.md — regenerated (generated)
- work/index.md — regenerated (generated)

## Release-gated
Paths under RELEASE_GATED_PATHS with a named human owner (leave "(none)" if none).
- (none)

## Order of work (each step independently verifiable)
1. **Measure the commit mechanism (D7, closes C6) — done before this plan was signed; result recorded here.** Evidence from this repository's own history, `git log -1 --format=%G?`: commits created server-side by GitHub (`72bf0ef`, `bf15030`; committer `GitHub`, author `luissiviero`, both web-editor approvals of this very item) report `E` — a signature is present, unverifiable locally only because no allowed-signers file is configured. Commits pushed over git from a session (`82537ce`, `47dbbe8`, `c62bfe1`; committer `Claude`) report `N` — no signature at all. A runner's `git push` is the same operation as that session's, so a commit made by mechanism 1 carries no signature and `verification.verified` is false. Mechanisms 2 and 3 are ruled out by R-4 itself, without needing a measurement: the REST contents API writes one file per call, so an approval touching the artifact, `log.md`, `index.md` and `.sdlc/active` could not be the single commit R-4 and R-5 both key on; GraphQL `createCommitOnBranch` sets author *and* committer to the token identity, which `is_agent_identity` matches on `[bot]@`, destroying D2's reason for the author split. **Therefore: mechanism 1 (plain `git commit` + `git push` on the runner), and route B drops the signature condition** — under D7's own terms ("if the plan's step 1 shows a dispatch-made commit can be GitHub-signed, route B keeps the gate too"), it cannot be, so it does not. Route B keeps the committer condition only as `committer is github-actions[bot]`, which mechanism 1 does set.
2. `scripts/approve.py`: add `--from-dispatch RUN_ID`. Verify: `ApproveFromDispatch` — exits 3 outside Actions; inside a faked Actions env the written files are byte-identical to a plain run.
3. `scripts/approve_dispatch.py` + its tests: `--check-actor` first (refuse before any write), then `--commit` with the staged-path allowlist, the author/committer split and the two trailers. Verify: `test_approve_dispatch.py` green.
4. `.github/workflows/approve.yml` + the `check_workflow_permissions.py` allowlist entry, in one commit (the suite reads the live workflow directory, so a lone workflow fails it). Verify: `scripts/checks/workflow-permissions.sh`, `workflow-yaml.sh`, `test_check_workflow_permissions.py`.
5. `scripts/check_artifact_chain.py`: the trailer route and the run verification. Verify: `ApprovalAuthor`, `DispatchAttestation`.
6. `.github/workflows/sdlc-gate.yml`: `actions: read` and `GH_TOKEN`, in the same commit as step 5 (R-13 says the same pull request; same commit is stricter and cheaper). Verify: `SdlcGate`.
7. `scripts/delegated_merge.py`: the route split, with the signature gate moved inside route A per step 1. Verify: `GrantCommit`, every existing route-A case unchanged.
8. `evals/cases/gate-blocks-workflow-dispatch.yaml` (R-9). Verify: `scripts/run_evals.sh`.
9. Decision record + the two amendments + the index (R-11). Verify: `check_okf.py`.
10. Skills, rule fragments and docs (R-10), then regenerate `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` and the indexes. Verify: `context-drift.sh`, `wc -l CLAUDE.md` ≤ 120, `check_okf.py`.
11. Full loop (R-12): `scripts/verify.sh`, `check_artifact_chain.py --base origin/main`, `run_evals.sh`, `check_okf.py`; paste the four last lines in the PR.

## Risks
- Risk: the workflow holds `contents: write` and pushes to `main` → mitigation: allowlisted in `check_workflow_permissions.py` with the reason, one checkout of the dispatch ref, no PR-head code executed, and the staged-path allowlist in `approve_dispatch.py --commit` aborting on any path outside `work/<slug>/` + `.sdlc/active` (C2, D6).
- Risk: route B widens what `delegated_merge.py` accepts → mitigation: route B is not a fallback; a commit carrying an `Approved-Run:` trailer that does not resolve to a successful `workflow_dispatch` run of `approve.yml` with the right actor is refused outright, never retried on route A (R-7, C4).
- Risk: R-6's verification silently no-ops in CI for want of a token → mitigation: R-13 grants `actions: read` and passes `GH_TOKEN` in the same commit, and its oracle reads the parsed permissions block rather than trusting a token is present (`knowledge/lessons/workflow-permissions-name-every-api.md`).
- Risk: the author/committer split misleads a reader of `git log` → mitigation: explained once in `knowledge/decisions/approve-by-dispatch.md` (D2).
- What this could break: every existing approval must keep passing the chain check unchanged — the trailer route is additive and only reached when a trailer is present; the no-trailer git-author rule is untouched.
- Options considered and not taken: committing entirely as `github-actions[bot]` (rejected, D2 — `is_agent_identity` would match and a tokenless local `verify.sh` would fail closed); a `branch` input instead of the dispatch ref (rejected, D3 — it could disagree with GitHub's own selector); reimplementing approval logic in the workflow (rejected, D4 — the two routes would drift).

## Proof
- `scripts/verify.sh` green (`VERIFY: PASS (<sha>)`)
- Spec rows → tests: R-1 → `test_check_workflow_permissions.py::CheckFile::test_real_workflows_directory` + `scripts/checks/workflow-permissions.sh`; R-2 → `test_approve_dispatch.py::ActorCheck`; R-3 → `test_approve.py::ApproveFromDispatch`; R-4 → `test_approve_dispatch.py::Commit`; R-5 → `test_check_artifact_chain.py::ApprovalAuthor`; R-6 → `test_check_artifact_chain.py::DispatchAttestation`; R-7 → `test_delegated_merge.py::GrantCommit`; R-8 → `test_approve_dispatch.py::Mode`; R-9 → `evals/cases/gate-blocks-workflow-dispatch.yaml` + `evals/cases/approve-refuses-in-agent-session.yaml`; R-10 → `scripts/checks/context-drift.sh` + `check_okf.py`; R-11 → `check_okf.py` + the two `grep -c` oracles; R-12 → the four last lines; R-13 → `test_check_workflow_permissions.py::SdlcGate`
- Manual / browser / screenshot / eval: the first real tap is the owner's, after merge — this pull request cannot exercise `approve.yml` end to end, because a `workflow_dispatch` workflow is only selectable once its file is on a ref, and the AI may not press Run (R-9). The merge is the owner's click regardless: this diff touches `scripts/approve.py`, `scripts/check_artifact_chain.py`, `scripts/delegated_merge.py` and `scripts/check_workflow_permissions.py`, all on `.sdlc/delegation.yaml`'s `locked-paths`, so `delegated_merge.py` refuses to auto-merge it by design.

## Rollback
- Revert the merge commit. Nothing is stateful: no migration, no stored data, no artifact front-matter field is added, so every existing artifact and every existing approval stays valid under the unchanged author rule. `approve.yml` disappearing from `main` makes the workflow unselectable in the Actions tab; the shell and web-editor routes are untouched throughout and remain the fallback.

## Deviations log (append during implementation; same commit as the deviation)
- deviation: step 1 measured D7 by a different method than spec.md's D7 names, and this should have
  been declared when the plan was signed rather than found by the review. D7 specifies "a throwaway
  dispatch on a scratch branch that prints the API's own view of the commit it just made ... for each
  mechanism". That is not performable from here, for two independent reasons: a `workflow_dispatch`
  workflow is only selectable once its file is on a ref, so `approve.yml` cannot be dispatched before
  the pull request that adds it merges; and R-9 forbids this session pressing Run at all. What step 1
  did instead is retrospective evidence from this repository's own history — `git log -1 --format=%G?`
  on commits GitHub made server-side (`72bf0ef`, `bf15030`: `E`) against commits pushed over git
  (`82537ce`, `47dbbe8`, `c62bfe1`: `N`) — plus ruling mechanisms 2 and 3 out on R-4's own
  requirements, which needs no measurement. The conclusion is the same one D7 anticipated, and the
  evidence was independently re-verified in the plan-conformance pass on pull request 51. But it is
  evidence about the *category* (any locally-made `git commit` + `git push`) rather than a direct
  observation of a runner-made commit, so the owner may want to amend D7 to match; that is a spec
  edit on a human-approved artifact and is theirs, not this session's, to make.
- deviation: three files added to the list above that the signed plan did not name —
  `knowledge/lessons/tests-carry-their-own-environment.md`, `knowledge/lessons/index.md` and
  `docs/sdlc/rules/60-lessons.md`. Rule 7 requires it: the same mistake appeared twice inside this
  one pull request. A test inherited this container's global git identity and exited 128 on the CI
  runner (`test_check_artifact_chain.py`, red on `ddac58a`), and a comparison inherited a wall-clock
  second that happened not to tick (`test_approve.py`, found by the plan-conformance review). Both
  are the same thing: the fixture did not supply what the test depended on. The lesson and its two
  pointer lines land in this pull request, as rule 7 and REVIEW.md's Memory pass both require.
