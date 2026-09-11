---
type: sdlc/spec
id: ci-budget
title: Reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest
description: "Two pull requests: the control plane (draft-skipping gate, label-gated triage, per-PR concurrency, nightly-only evals, two-workflow merge wake, the skipped-run rule and the not-delegated verdict in the merge script) and the agent side (draft-first skills, one code PR at a time, the actions_minutes_per_pr measure with its band, the crucial-versus-loosened decision record)."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: in-review
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by:
approved-on:
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: a8b7001
prompt: "/sdlc-spec ci-budget, in session_01WHySf4V2YtqPc1KG1kvbfd on Fable (the guide's Opus writer was not available in the session; the reviewers run on Opus and Sonnet), from the approved intent, work/ci-budget/implementation-plan.md, and a Sonnet explorer pass that re-checked every line the guide cites against main at ca8dd32 (seven citations had moved; all are at their current lines here)"
record:
resource: implementation-plan.md
tags: [ci, github-actions, minutes, tokens, latency, drafts, concurrency, delegated-merge, bands]
timestamp: 2026-09-11T09:00:00Z
---
# Spec: reduce GitHub minutes, waiting time and wasted tokens; keep the crucial procedures, loosen the rest

The owner answered every open question on the intent (2026-09-09, two sessions); `implementation-plan.md`
carries the answers and the exact diffs. This spec is the contract the plan and the two pull requests are
checked against: PR-A is the control plane (`.github/workflows/`, `scripts/delegated_merge.py`; agent writes
under the unlock, owner labels and clicks), PR-B is the agent side (skills, one rule line, the measure, the
decision record, the handoff).

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R1 | `sdlc-gate.yml`: `types` gains `ready_for_review`; the `artifact-chain` job has `if: draft == false && !(action == 'edited' && sender.type == 'Bot')`; `concurrency: sdlc-gate-<pr number>` with `cancel-in-progress` only when `action == 'synchronize'`; the `permissions:` block (`:5-12`) and the job name are unchanged | (a) minutes, (b) time | `scripts/test_workflow_shapes.py::GateWorkflow::test_skips_drafts_and_bot_edits`, `::test_ready_for_review_triggers`, `::test_cancels_only_on_synchronize`; `scripts/test_check_workflow_permissions.py:290` unchanged |
| R2 | Both triage steps (`sdlc-gate.yml:58`, `:72`) run only when the pull request carries the `triage` label: `if: failure() && env.HAS_CLAUDE_AUTH == 'true' && contains(github.event.pull_request.labels.*.name, 'triage')` | (c) tokens | `scripts/test_workflow_shapes.py::GateWorkflow::test_triage_is_label_gated` (both `failure()` steps carry the `contains` clause; no other step does) |
| R3 | `pr-review.yml`: `concurrency: pr-review-<pr or issue number>`, cancel only on `pull_request`+`synchronize`; on `issue_comment` a first step reads the head repository and every later step is guarded by `env.HAVE_CLAUDE_AUTH == 'true' && (event == 'pull_request' \|\| steps.local.outputs.ok == 'true')`; the draft skip (`:41-42`), the `author_association` gate (`:45`) and `--disallowedTools` (`:97`) stay byte-identical | (c) tokens; crucial (the `@claude` route) | `scripts/test_workflow_shapes.py::ReviewWorkflow::test_concurrency`, `::test_fork_guard_precedes_checkout`, `::test_draft_skip_and_no_bash_unchanged` |
| R4 | `agent-evals.yml`: `on:` is `schedule` + `workflow_dispatch` only; the `hook-cases` job is gone; `full-suite` has no `if:`; the header names the nightly and `VERIFY_CMDS` as the per-commit route; `.sdlc/config.env:25` still runs `scripts/run_evals.sh` | (a) minutes | `scripts/test_run_evals.py::AgentEvalsWorkflow` rewritten: `test_no_pull_request_trigger_and_no_hook_cases_job`, `test_runs_nightly_and_can_be_started_by_hand`, `test_nightly_requires_claude`, `test_nightly_trusts_the_checkout`, `test_the_deterministic_cases_still_run_on_every_gated_commit` |
| R5 | `delegated-merge.yml:31` is `workflows: [sdlc-gate, pr-review]`; the job `if` (`:73`) and the `main` checkout (`:75-79`) are unchanged | (a) minutes | `scripts/test_workflow_shapes.py::MergeWorkflow::test_wakes_on_gate_and_review_only`; `scripts/test_check_workflow_permissions.py:304-313` unchanged |
| R6 | `scripts/delegated_merge.py::_pr_runs` (`:243-253`) drops a run whose `status` is `completed` and `conclusion` is `skipped`; `cancelled`, `failure`, `timed_out` and in-progress runs are kept; `check_required_runs`, `check_review` and `check_cool_off` change nothing else | crucial (every other refusal fail-closed), (a) | `scripts/test_delegated_merge.py`: `Plumbing::test_pr_runs_drops_completed_skipped_keeps_in_progress`; `ChecksCondition::test_skipped_draft_run_beside_success_is_ok`, `::test_only_a_skipped_run_is_refused`, `::test_cancelled_beside_success_still_refused`, `::test_failed_beside_success_still_refused`; `ReviewCondition::test_skipped_review_run_beside_success_reads_the_success`, `::test_only_a_skipped_review_run_waits`; `CoolOffCondition::test_skipped_run_is_not_a_stamp` |
| R7 | A `delegation` condition recorded after `event` (`run()` `:773-775`) and before `pull-request`: when `work/<slug>/intent.md` (slug from the body's `Work-Item`, `work_item_slug` `:293-303`) exists in the job's checkout and its `mode` is not `delegated`, the verdict is `not-delegated`, `Run._code()` (`:701-709`) returns 0, `finish()` prints `DELEGATED-MERGE: not-delegated (delegation)`; a missing file or no slug is `ok`; every other refusal keeps exit 1; `check_grant_front_matter` (`:401-403`) stays as the second reading | (c) tokens, (a) minutes (a green run, not a red billed one, on every supervised PR) | `scripts/test_delegated_merge.py::DelegationCondition::test_supervised_intent_is_not_delegated_exit_0`, `::test_delegated_intent_is_ok`, `::test_missing_intent_is_ok`, `::test_no_slug_is_ok`, `::test_dry_run_prints_and_continues`; `Plumbing::test_code_maps_not_delegated_to_0_refused_to_1`; `EndToEnd::test_pull_request_that_was_a_draft_merges_on_its_ready_run`, `::test_supervised_pull_request_ends_not_delegated` |
| R8 | The three skills: `sdlc-run` step 3 opens the item's pull request as a draft and keeps it so until step 5, one agent code PR open at a time (an intent-only one may run beside it); `sdlc-review` step 4 runs `gh pr ready` and logs `PR #<n> \| draft -> in-review` on every item, and names the `triage` label for an unexplained red gate; `sdlc-intent` step 5 opens the intent PR as a draft. Every string `evals/cases/skill-names-match-templates.yaml` pins is kept | (c) tokens, (b) time | `scripts/run_evals.sh --only skill-names-match-templates` passes; new `evals/cases/skills-open-drafts.yaml` (hook-kind grep case: `--draft` in `sdlc-run` and `sdlc-intent`, `gh pr ready` and `triage` in `sdlc-review`) |
| R9 | `docs/sdlc/rules/30-conventions.md` gains one bullet ("One agent code pull request open at a time …; open it as a draft and mark it ready once") after `:20` and pays for it by re-flowing the reviewer-model bullet (`:21-25`) from five lines to four; the adopter's rendered `CLAUDE.md` stays at 120 = `MAX_CONTEXT_LINES` | green (context file at or under the cap) | `bash scripts/adopt.sh "$SCRATCH/adopt" && python3 scripts/gen_context_files.py --root "$SCRATCH/adopt" && wc -l "$SCRATCH/adopt/CLAUDE.md"` prints 120 with no "over MAX_CONTEXT_LINES"; `scripts/checks/context-drift.sh` passes; `scripts/test_adopt.py` |
| R10 | `scripts/github_metrics.py` gains `actions_minutes_per_pr` (`choices` `:160`, `_api_path` `:83-92` shares the runs branch, `--default-branch` default `main`): per bucket, the sum of `_billed_minutes` (`max(1, ceil((updated_at − run_started_at)/60))`, 0 on a missing or negative stamp) over runs whose `event` is neither `schedule` nor `workflow_dispatch` and whose `conclusion` is not `None`, divided by the distinct head branches ≠ default in the bucket; a bucket with minutes and no such branch is omitted; `monitoring/bands.yaml` gains the entry in the guide (window 14, 2σ `Read,Grep,Bash(gh run list *)`, 3σ `report:engineering-leadership`) | (a) minutes, observable | `scripts/test_github_metrics.py::ActionsMinutesSeries` (ordering; one-minute floor; 3:05 → 4; `schedule`/`workflow_dispatch` excluded; the `workflow_run` wake on `main` counts; wakes-only day omitted; in-progress omits its bucket; two PRs divide; empty input; `days=1` trims; `_api_path` prefix; end-to-end into `detect_bands.py --window 2` as `:134-141`); fixture `scripts/fixtures/gh_runs_minutes.json` → `5.0, 3.0`; `scripts/test_bands_config.py:38-45` becomes three GitHub metrics; `python3 scripts/bands_config.py` prints 3 rows |
| R11 | `knowledge/decisions/ci-budget-crucial-and-loosened.md` (front matter as `merge-click-is-the-gate.md:1-7`): crucial list naming the file that proves each; loosened list with its compensating control; consequences (GitHub counts a skipped required check as passing; nothing merges from a draft and the merge script demands `success`; the two widened paths and their tests; the band); alternatives; one line in `knowledge/decisions/index.md` | crucial procedures untouched, and say so | `python3 scripts/check_okf.py` ends `0 warnings`; `grep -c ci-budget-crucial-and-loosened knowledge/decisions/index.md` = 1 |
| R12 | Crucial, byte-for-byte: no existing test in `scripts/test_delegated_merge.py` or `scripts/test_check_artifact_chain.py` is edited or removed except the fixture lists R6 names (`FIXTURE_POLICY:49`, `RUN_IDS:85`, `make_runs:154`, `make_check_runs:168`, `required` at `:350` and `:842`, `test_required_workflow_missing_is_refused:359-363`); `test_fork_head_repository_is_refused` (`:260-264`) untouched; check-run names `artifact-chain`, `review`, `merge` and the policy's `require-checks`/`require-review` unchanged | crucial | `git diff origin/main -- scripts/test_check_artifact_chain.py` empty; `git diff origin/main -- scripts/test_delegated_merge.py` has no `-    def test_` line; `.sdlc/delegation.yaml` untouched (`PROTECTED_PATHS`) |
| R13 | Docs say what the code does: `docs/sdlc/README.md:84,86,106,153`, `docs/sdlc/github-setup.md:72-73,88-89,132-135` (+ the `triage` bullet), `knowledge/decisions/merge-click-is-the-gate.md:31,55-56`, `knowledge/decisions/control-plane-label.md:46`, `docs/sdlc/spikes/pr-review-identity.md:82-83`, `docs/sdlc/spikes/prompt-surfaces.md:289-291`, the three workflow headers; `docs/sdlc/handoff/HANDOFF.md` gets a new `## Task state` section and the old heading is suffixed `— HISTORY` | everything green | `grep -c "agent-evals" docs/sdlc/github-setup.md` names it only as the nightly; `scripts/verify.sh` `VERIFY: PASS`; `python3 scripts/check_okf.py` `0 warnings` |
| R14 | Acceptance, one week after PR-A merges: a throwaway draft's gate and review runs conclude `skipped` in seconds; `gh pr ready` with no push yields one gate and one review run on the same sha, both `success`; the merge dry run prints `CONDITION checks: ok` and `CONDITION review: ok`; applying `triage` queues a run and cancels none; `actions_minutes_per_pr --days 14` prints one float per day; the last seven values ≤ 10, a PR of #61's shape ≤ 6 minutes, tracking comments ≤ pushes-after-ready + 1, a red gate red in ≤ 1 minute | (a), (b), (c) numbers | the closing ledger line carries the seven numbers; Fable M5 revision line |

## Design
### Architecture / data flow
Two pull requests, in order, both `Work-Item: ci-budget`, both opened as drafts:
- **PR-A `claude/ci-budget-control-plane`** (R1–R7, R12, R13's workflow headers and merge-click/label/README/github-setup
  sentences): four workflow files and the merge script, with tests. The agent writes under
  `SDLC_CONTROL_PLANE_UNLOCK` (each write logged); `check_control_plane.sh` blocks the PR until the owner applies
  `control-plane-approved`; `scripts/delegated_merge.py` is a locked path, so the owner clicks the merge.
  Order inside PR-A: A2b (the fork guard on the `@claude` route) first, then A1, A2, A3, A4, A5, A6.
- **PR-B `claude/ci-budget-agent-side`** (R8–R11, R13's handoff): skills, the rule fragment and regenerated context
  files, the measure with fixture, tests and band, the decision record, the handoff. It touches `.claude/skills/`,
  so the reviewer never sees that diff and the merge is the owner's click.
- Flow after PR-A: a push to a draft creates `skipped` gate and review runs in seconds; `ready_for_review` starts one
  gate run and one review on the ready sha; a later push cancels the in-flight pair; a same-sha re-trigger
  (`labeled`, `edited` by a human, `ready_for_review`) queues; the merge script wakes on the two workflows only,
  ignores the draft's `skipped` runs on that sha, and on a supervised PR ends green with `not-delegated`.
### Interfaces (APIs, events, schemas) — exact shapes
- `sdlc-gate.yml` `on.pull_request.types: [opened, synchronize, reopened, ready_for_review, edited, labeled, unlabeled]`;
  `concurrency.group: sdlc-gate-${{ github.event.pull_request.number }}`, `cancel-in-progress: ${{ github.event.action == 'synchronize' }}`.
- `pr-review.yml` `concurrency.group: pr-review-${{ github.event.pull_request.number || github.event.issue.number }}`;
  step `local` writes `ok=true|false` to `$GITHUB_OUTPUT` from `gh api repos/$REPO/pulls/$NUMBER --jq .head.repo.full_name`.
- `delegated_merge.py`: `SKIPPED = "skipped"` beside `OK_CHECK_CONCLUSIONS` (`:78`); `NOT_DELEGATED = "not-delegated"`;
  `check_delegation(pulls, head_sha, root) -> (verdict, detail)` with detail `#<n>, Work-Item: <slug>, mode <mode>`;
  the summary line `DELEGATED-MERGE: not-delegated (delegation)`.
- `github_metrics.py actions_minutes_per_pr [--days N] [--default-branch main] [--from-json FILE]`: one float per
  line, oldest first; API path `repos/{repo}/actions/runs?per_page=100&created=>={since}`.
- `bands.yaml` entry: flat flow-map shape as `:6-14`; `source:` starts with `scripts/github_metrics.py`; `window: 14`.
- Skill strings: `gh pr create --draft`, `gh pr ready`, ledger `PR #<n> | draft -> in-review`, label `triage`.
### Data and migrations
None. No personal data; run metadata only (security-standards §4 n/a). No new dependency (§5 n/a).
### Failure modes and how they surface
- A required check that never reports would block merges forever: `agent-evals` is never a required check
  (`delegated_merge.py:341-352` refuses instead of waiting); branch protection, if created, lists `sdlc-gate / artifact-chain`.
- A Linux-only failure surfaces at ready instead of on the first push: the ready gate run is red within a minute.
- A wrong `--jq` path in the fork guard would silently disable `@claude`: a green run whose summary says "refusing" on a
  repo-local PR is the detector; the four clauses and the step are the revert.
- A `cancelled` run on the head sha still refuses (only `synchronize` cancels; a queued run evicted by a third event is
  the residual: re-apply the label).
- `_billed_minutes` is a per-run approximation of the billing page; the band detects a trend, a constant bias cancels;
  `/actions/runs/{id}/timing` is the exact route if the two diverge by more than the band width.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: R6 and R7 widen two acceptance paths in the script that performs the click, against the intent's "must not
  touch the merge conditions" — policy: security-standards §8 (the writer is not the approver; the merge script is
  the approver's proxy) — contradiction? yes, refined — owner: luissiviero — resolution: approved on the intent
  (2026-09-09, both questions); bound: `skipped` only, one `not-delegated` reason only, every other refusal exit 1,
  each with its test in R6/R7; the owner's click lands the change (locked path).
- C2: `main` has no branch protection rule (branches API, 2026-09-09), so the "two independent controls" in the
  intent's risk class is one control today: the merge script's `require-checks` plus the owner's click — policy:
  `knowledge/decisions/merge-click-is-the-gate.md` — contradiction? no — owner: luissiviero — resolution: the
  tests in R6 are the bound; creating the rule (click 8 in the guide) is optional and never lists `agent-evals`.
- C3: PR-A edits `PROTECTED_PATHS` from an agent session — policy: rule 3, `knowledge/lessons/control-plane-unlock-is-advisory.md`
  — contradiction? no — owner: luissiviero — resolution: writes logged by the unlock; `control-plane-approved`
  applied by the owner after reading the workflow diff; `check_control_plane.sh` blocks until then.
- C4: the `@claude` route on a public repository checks out a fork head with the key (`pr-review.yml:57`) — policy:
  security-standards §3/§6 (untrusted input, infra) — contradiction? no — owner: luissiviero — resolution: A2b, the
  first item of PR-A; the `author_association` gate and `--disallowedTools` stay.

## Open questions carried from intent.md
- None unresolved. The reviewer-model question is closed as "unchanged, measure a week" (R14 gives the numbers).

## Decisions (ADR-style: context → decision → consequences)
- D1: two PRs, control plane first → the workflow change lands under one label and one click, and the four open PRs
  pick it up on their next push → PR-B's skills describe a gate that already behaves that way.
- D2: the skipped-run rule is one clause in `_pr_runs`, not an id comparison → a `pull_request` run concludes
  `skipped` only when every job `if:` was false, i.e. the head was a draft, so it is never evidence → `cancelled`
  keeps refusing, and the three conditions that read `_pr_runs` need no change of their own.
- D3: a `not-delegated` verdict with exit 0 rather than a red refusal → the run list means "a human is needed" only
  when red → one reason only, decided before any grant check.
- D4: the measure filters by `event`, not `head_branch` → the `workflow_run` wake reports `head_branch: main` and
  would be dropped by a branch filter → the denominator is distinct non-default head branches per bucket.
- D5: tests, not branch protection, are the bound on R6 → `main` has no rule today → the DelegationCondition,
  ChecksCondition and EndToEnd cases are mandatory in PR-A.
- D6: PR-A's skill-shaped strings are not touched; PR-B keeps every string `skill-names-match-templates.yaml` pins →
  the merge script's own eval stays green across both PRs.

## Gotchas found while reading the codebase
- `check_artifact_chain.py:648-656`: a pull request whose diff touches anything outside `work/ci-budget/`,
  `work/index.md` or a pointer move is checked strict, so the spec and plan PRs may carry only the item's own
  files; the handoff refresh (R13) rides in PR-B, after the plan tap.
- `check_artifact_chain.py:196-201` calls `gh` whenever a token is set; this container has none, so every local
  chain check and `verify.sh` run needs `env -u GH_TOKEN -u GITHUB_TOKEN` (HANDOFF.md:53-55).
- `approve.yml` writes to the ref selected in "Use workflow from branch"; the taps for this item run from `main`
  with a blank slug (`.sdlc/active` already reads `ci-budget`).
- `scripts/adopt.sh:347-349` copies `sdlc-gate.yml`, `agent-evals.yml`, `pr-review.yml`, `deploy.yml`, `bands.yml`
  verbatim and never `delegated-merge.yml`: adopters get the new shapes with no template to edit.
- The adopter's rendered `CLAUDE.md` is exactly 120 lines (`adopt.sh:489-503`), and `gen_context_files.py:192-201`
  writes nothing when over: R9 is net zero by construction, measured before commit.
- The live API reports `delegated-merge`'s `workflow_run` runs with `head_branch: main` (D4).
- `pr-review.yml` restores `.claude/` and `CLAUDE.md` from base only on `pull_request` events (`:60-63`); on
  `issue_comment` it checks out `refs/pull/N/head` (`:57`) with the key: that is the gap A2b closes.
- Seven of the guide's line citations had moved by 1 to 4 lines (`_code()` 701, `check_check_runs` 367, `SLUG_RE` 75,
  `make_runs` 154, `make_check_runs` 168, `test_required_workflow_missing_is_refused` 359, the conventions bullet
  21-25); this spec cites the current lines.

## Not doing
- Changing the reviewer's model, the merge method or conditions, approvals, grants or signatures.
- Repository visibility, the spending limit, the GitHub plan, self-hosted runners, the owner's e-mail settings.
- Making `index-drift.sh` tolerant of drift already on `main` (pull request 62).
- The on-demand `@claude` route beyond the fork guard (A2b).
- Branch protection on `main` (owner's optional click 8; never `agent-evals` as a required check).
