---
type: sdlc/decision-record
id: ci-budget-implementation-plan
title: "Implementation guide for ci-budget: the two pull requests, the merge-script rule, and the measure"
description: "The owner's answers to every open question, the exact workflow and script changes for the control-plane and agent-side pull requests, the fork-pull-request pass for going public, the verification commands and the acceptance numbers. Written in the session that traced the Actions quota block; the implementing session works from this file."
status: draft
resource: ../../work/ci-budget/intent.md
tags: [ci, github-actions, minutes, tokens, latency, drafts, concurrency, delegated-merge, bands, public-repo]
timestamp: 2026-09-09T09:40:00Z
---
# ci-budget — implementation guide

## Context
GitHub Actions on `luissiviero/lifecycle-axis-` (private) exhausted the account's 2,000 free minutes on
2026-09-08 21:43 UTC after 1,124 runs in six days. Every run since dies in 3–5 s before reaching a runner,
including the owner's `mode: delegated` tap (run 34288111993) and both nightlies. The run history shows
most minutes, tokens and waiting went to work nobody used: a 5m54s `claude -p` triage on every red gate
(three of the last four on a drift already on `main`), an `agent-evals` PR job that repeats what
`verify.sh` ran, `delegated-merge` wakes on a workflow the policy no longer requires, and 89 of 96 gate
runs superseded by a later push with no concurrency group.

Owner's goals: reduce (a) GitHub minutes, (b) waiting time, (c) wasted tokens — keep the crucial
procedures, loosen the rest. Intent filed: `work/ci-budget/intent.md`, PR #63 (draft, `in-review`).
This document is the implementation guide; the repo's own `spec.md` and `plan.md` are written from it
under the chain (intent tap → spec → tap → plan → tap → code). Design reviewed on Opus; exploration on Sonnet.

## Everything decided (owner, 2026-09-09)
| # | Question | Decision |
|---|---|---|
| Q1 | Gate on drafts | **Skip `sdlc-gate` entirely on drafts**; `ready_for_review` added to its triggers. Agent runs `verify.sh` + chain check locally; nothing merges from a draft. |
| Q2 | "Require branches to be up to date" | **Off.** Compensating control: one agent *code* PR open at a time; intent-only PRs may run in parallel. |
| Q3 | Reviewer model | **Unchanged.** Cut the count first; measure a week; decide with a number. |
| Q4 | Failure triage | Kept behind a **`triage` label** (the `labeled` trigger re-runs the gate). |
| Q5 | Stale tracking comment after a cancelled review | Verified: `check_review` keys on the newest successful run's id (`delegated_merge.py:605-610`); a cancelled run's comment is never read. **No change.** |
| Q6 | The measure | New series `actions_minutes_per_pr` in `scripts/github_metrics.py` + a band in `monitoring/bands.yaml`. |
| I1 | Unblocking Actions | **Make the repo public** — after the fork-PR pass and the history scan (Phase 0.2). |
| I2 | PR shape | **Two PRs**: PR-A control plane first, PR-B agent side second. |
| I3 | Models | **Sonnet writes, Opus reviews, Fable checks divergence from the objective.** |
| I4 | Who edits workflows | **Agent writes under the unlock; owner labels `control-plane-approved`.** |
| F1 | Superseded-run rule in `delegated_merge.py` | **Approved** — a `skipped`/`cancelled` run is ignored only when a later run of the same workflow on the same SHA succeeded. Without it every PR that was ever a draft is unmergeable at its ready SHA. |
| F2 | Writer mechanism | **A Sonnet session is the single writer** (one-writer-until-ledger stands); Opus subagents review; Fable checkpoint. |

**Crucial, kept byte-for-byte / name-for-name:** chain check + `verify.sh` + `check_control_plane.sh` on
every ready head before merge; check-run names `artifact-chain`, `review`, `merge`; policy
`require-checks: [sdlc-gate, pr-review]` and `require-review: true` on the final SHA; human-only
approvals and the tap; nightly `agent-evals --require-claude` and nightly `bands`; the `@claude` review;
`test_fork_head_repository_is_refused` (`test_delegated_merge.py:260-264`) untouched.

**Loosened → compensating control:** gate on drafts off → nothing merges from a draft, local verify;
review of every push → once per ready state, superseded pushes cancelled; model triage → `triage` label;
`agent-evals` on PRs → `verify.sh` runs the same cases on the same commit; merge wake on `agent-evals` →
it gated nothing since 15424e0; up-to-date rule → serial queue, one code PR at a time.

## Roles and models
- **Writer:** one session on Sonnet (`/model claude-sonnet-5` before Phase 1; one writer per item,
  `knowledge/decisions/one-writer-until-ledger.md`).
- **Scouts / verifier:** `explorer`, `verifier` subagents on Sonnet (`model: sonnet` at launch).
- **Reviewers:** `plan-reviewer` and `security-reviewer` on Opus (`model: opus`): once on spec+plan before
  code (as PR #58's `revisions/1.md`), once on each PR diff before it goes ready.
- **Checkpoint:** switch to Fable (`/model claude-fable-5-1`) once per PR: read the diff against the
  intent's success criteria and the crucial list; "no divergence" or a list; then `gh pr ready`.
- **Ledger** records writer and reviewer models on every gate line (`30-conventions.md:21-25`).
- **Owner:** visibility flip + settings, taps, `control-plane-approved` label, branch-protection clicks,
  merge clicks (PR-A carries a locked path; PR-B touches `.claude/skills/` — both wait on a click).

## Phase 0 — bookkeeping and unblocking (any model; no code)
0.1 Record the answers in `work/ci-budget/intent.md`: every `A:` for Q1–Q6, two added questions with
    answers (F1, noting it refines the intent's "no merge condition changes" wording; I1), a ledger line
    `intent.md | in-review -> in-review | claude | <sha> | open questions answered by the owner …`;
    `gen_index.py`; one push to PR #63.
0.2 **Go public** (owner), after the agent posts on #63:
    - the fork-PR checklist (end of this file), including the one gap it closes (A2b);
    - the history scan, run read-only:
      `git grep -nIE 'sk-ant-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-|-----BEGIN [A-Z ]*PRIVATE KEY-----' $(git rev-list --all) -- . | grep -v block-secrets.sh`
      and `git log --all --diff-filter=D --name-only -- '*.env' '*.pem' '*.key'` (expect nothing; the only
      key-shaped strings are the pattern list in `.claude/hooks/block-secrets.sh:9` and the synthetic
      `AKIA…` token in `evals/cases/hook-refuses-planted-key.yaml`).
    Settings at the flip: Actions → fork PR workflows **require approval for all outside collaborators**;
    workflow permissions read-only, "create and approve pull requests" unchecked (`github-setup.md:78-80`);
    secret scanning + push protection on. The four open intent PRs need a push or a re-run to report.
0.3 Owner taps `slug: ci-budget`, `artifact: intent.md`, `mode: supervised` (the tap is an Actions run, so
    0.2 first — or approve from a shell / the web editor).
0.4 `/sdlc-spec` then `/sdlc-plan` (Sonnet session) from this document; Opus reviewers over both; taps.
    `scripts/` is in `PLAN_REQUIRED_PATHS`, so no code before the plan tap.

## Phase 1 — PR-A: control plane (Sonnet writes under `SDLC_CONTROL_PLANE_UNLOCK`; owner labels + clicks)
Branch `claude/ci-budget-control-plane`; title `[ci-budget] Control plane: …`; body `Work-Item: ci-budget`;
opened as a **draft**, ready after the Fable checkpoint.

### A1 `.github/workflows/sdlc-gate.yml`
```yaml
on:
  pull_request:
    # ready_for_review starts the gate for a pull request that lived as a draft. `edited` stays (the
    # body's Work-Item line is read at run time); `labeled`/`unlabeled` stay (control-plane and triage labels).
    types: [opened, synchronize, reopened, ready_for_review, edited, labeled, unlabeled]
# One gate per pull request. Only a NEW PUSH cancels a run in flight; a same-sha re-trigger (labeled,
# edited, ready_for_review) queues behind it, so the head sha never carries a `cancelled` run.
concurrency:
  group: sdlc-gate-${{ github.event.pull_request.number }}
  cancel-in-progress: ${{ github.event.action == 'synchronize' }}
jobs:
  artifact-chain:
    runs-on: ubuntu-latest
    # A draft costs nothing: the agent verifies locally (sdlc-run step 4), GitHub refuses to merge a
    # draft, delegated_merge.py refuses one too. The run still exists, concluded `skipped` — hence
    # the superseded-run rule in the merge script (work/ci-budget).
    if: github.event.pull_request.draft == false
```
Both triage steps (`:58` "Trust the checkout…", `:72` "Triage failure…"):
`if: failure() && env.HAS_CLAUDE_AUTH == 'true' && contains(github.event.pull_request.labels.*.name, 'triage')`;
comment at `:52-56` rewritten (the trust step now diverges from `agent-evals.yml`'s on purpose; triage cost
3.6 min median, opt-in via the label). `permissions:` untouched (`test_check_workflow_permissions.py:290,304-313`).

### A2 `.github/workflows/pr-review.yml`
```yaml
concurrency:
  group: pr-review-${{ github.event.pull_request.number || github.event.issue.number }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' && github.event.action == 'synchronize' }}
```
**A2b — fork guard for the `@claude` route (needed before going public).** On `issue_comment` the job
checks out `refs/pull/N/head` (`:57`) with the key, and the action restores `.claude/`, `CLAUDE.md` from
base only on `pull_request` events (`:60-63`), so an owner typing `@claude` on a fork PR runs the reviewer
steered by the fork's config. Add a first step, before the checkout: `if: env.HAVE_CLAUDE_AUTH == 'true'
&& github.event_name == 'issue_comment'`, `gh api repos/$REPO/pulls/$NUMBER --jq .head.repo.full_name`,
write `ok=true|false` to `$GITHUB_OUTPUT` (a refusal is a green run with a summary line, no failure mail);
the four existing step guards become `env.HAVE_CLAUDE_AUTH == 'true' && (github.event_name == 'pull_request'
|| steps.local.outputs.ok == 'true')`. The job's draft skip (`:41`) and `author_association` gate (`:45`) stay.

### A3 `.github/workflows/agent-evals.yml`
`on:` = `schedule` + `workflow_dispatch`; delete `hook-cases`; `full-suite` loses its `if:`; header (`:2-7`)
rewritten: nightly on `main` and by hand; per-commit cases run inside `sdlc-gate`'s `verify.sh` via
`VERIFY_CMDS` (`.sdlc/config.env:26`). The header must not contain the literal `pull_request:`.
**Test rewrite (breaks by design):** `scripts/test_run_evals.py:301-327` `AgentEvalsWorkflow` →
`test_no_pull_request_trigger_and_no_hook_cases_job` (assertNotIn `pull_request:`, `hook-cases`, `--kind hook`,
`paths:`), `test_runs_nightly_and_can_be_started_by_hand` (`schedule:`, `cron:`, `workflow_dispatch:`),
`test_nightly_requires_claude` (`--require-claude`), `test_nightly_trusts_the_checkout` (unchanged),
`test_the_deterministic_cases_still_run_on_every_gated_commit` (`scripts/run_evals.sh` in `.sdlc/config.env`).

### A4 `.github/workflows/delegated-merge.yml`
`workflows: [sdlc-gate, pr-review]` (`:31`); comment `:26-30` "three" → "two", one sentence on why
`agent-evals` left. The job `if` (`:73`, `conclusion == 'success'`) already means a draft's skipped gate
run starts no job.

### A5 `scripts/delegated_merge.py` — the superseded-run rule (locked path; owner's click)
Rule: *a completed run with conclusion `skipped` or `cancelled` is ignored when a run of the same
workflow on the same head sha and branch with a **higher run id** concluded `success`; otherwise it
refuses exactly as today.* Ids increase with time and cancel-in-progress cancels the older run.
```python
SUPERSEDABLE_CONCLUSIONS = ("skipped", "cancelled")   # beside OK_CHECK_CONCLUSIONS, :78

def _live_runs(matching):                              # after _pr_runs, :243-253
    """`matching` minus the runs a later successful run of the same workflow superseded. The caller
    already narrowed to one workflow name, one head sha (?head_sha=) and one head branch (_pr_runs), so
    only the id is compared. A failure, a timeout, an in-progress run and a skipped/cancelled run with
    no later success are all kept, so the conditions stay fail-closed (work/ci-budget)."""
    newest_success = max([int(r.get("id") or 0) for r in matching
                          if r.get("status") == "completed" and r.get("conclusion") == "success"], default=0)
    return [r for r in matching
            if not (r.get("status") == "completed" and r.get("conclusion") in SUPERSEDABLE_CONCLUSIONS
                    and int(r.get("id") or 0) < newest_success)]
```
`check_required_runs`: `matching = _live_runs(matching)` after the `if not matching:` refusal (`:348-353`),
before `failed` (`:354`) — the "no run at all" refusal stays on the unfiltered list. `check_review`: the same
line after `matching = [...]` (`:604`), before `completed`. Docstrings get one sentence each. `check_cool_off`
needs nothing (max `updated_at` is monotone).
**Tests** (`scripts/test_delegated_merge.py`) — fixtures to the live two-name policy: `FIXTURE_POLICY:49`,
`RUN_IDS:85`, `make_runs:158`, `make_check_runs:169-173`, `required` at `:350` and `:842`,
`test_required_workflow_missing_is_refused:360-363` (filter on `sdlc-gate`). New — `ChecksCondition`:
skipped draft run superseded by a later success → OK; cancelled superseded → OK; skipped with no later
success → REFUSED; cancelled with no later success → REFUSED; cancelled *newer* than the success → REFUSED;
failed + later success → REFUSED (never superseded); a failed run of a workflow no longer required → OK;
in-progress beside a superseded one → WAITING. `ReviewCondition`: skipped/cancelled review run superseded
→ OK and `newest` is the successful run (its id in the detail); skipped with no later success → REFUSED;
a comment linking only the superseded run → WAITING. `Plumbing`: `_live_runs` is identity when nothing
succeeded. `EndToEnd`: a PR that was a draft merges on its ready run (`happy_path()` + a lower-id skipped
run for both workflows → `DELEGATED-MERGE: merged #12`).

### A6 Docs (replacement sentences in the same PR)
`docs/sdlc/README.md:84` (gate row: "skips drafts; triage is label-gated"), `:86`, `:106`, `:153` ("require
`sdlc-gate` and `pr-review`; never a workflow with a `paths:` filter or a draft guard"); `docs/sdlc/github-setup.md:72-73`
(required checks `sdlc-gate / artifact-chain`, later `pr-review`; up-to-date **off** with the serial-queue
rationale; conversation resolution on), `:88-89` (triage behind the label), `:132-135` (`agent-evals` no
longer runs on PRs; the skipped-run rule), new bullet: the `triage` label exists; `docs/sdlc/handoff/HANDOFF.md:78-80`
(done); `knowledge/decisions/merge-click-is-the-gate.md:31` and `:55-56` ("revisit if the repo goes public" →
superseded by the owner's flip, work/ci-budget); `knowledge/decisions/control-plane-label.md:46` ("keeps",
plus the triage route); `docs/sdlc/spikes/pr-review-identity.md:82-83`; `docs/sdlc/spikes/prompt-surfaces.md:289-291`
(`paths:` proposal moot); header comments in the three workflow files. `scripts/adopt.sh:347-349` copies the
three workflows verbatim — no template copy to edit.

### A7 Land it (order matters)
1. Verify (below); Opus reviewers on the diff; Fable checkpoint; `gh pr ready`; ledger
   `PR #<n> | draft -> in-review | claude | <sha> | writer sonnet, reviewers opus, checkpoint fable`.
2. Owner reads the workflow diff, applies `control-plane-approved`.
3. **Owner: branch protection before the merge** — remove `agent-evals` from required checks (PR-A's own
   head produces no `agent-evals` PR run any more, so with it still required PR-A cannot merge); up-to-date
   **off**; keep `sdlc-gate / artifact-chain`, add `pr-review` when ready.
4. Owner clicks merge (locked path → no delegated merge). Open PRs #59–#62 pick the workflows up on their
   next push; no close/reopen.

## Phase 2 — PR-B: agent side (Sonnet writes; Opus reviews; owner click)
Branch `claude/ci-budget-agent-side`, draft first.

### B1 Skills
- `.claude/skills/sdlc-run/SKILL.md` step 3: open the item's pull request as a **draft** (`gh pr create
  --draft`) and keep it so until step 5 — the gate and the reviewer skip a draft, so the build window costs
  no CI and no review tokens, and nothing merges from it; one agent **code** PR open at a time, an
  intent-only one may run beside it. Step 4 unchanged (local verify is the only signal on a draft).
- `.claude/skills/sdlc-review/SKILL.md:10-12` step 4: `gh pr ready` + ledger `PR #<n> | draft -> in-review`
  on **every** item (ready is what starts the gate), findings posted as a comment when delegated; if the gate
  is red for a reason the diff does not explain, apply `triage` and remove it once diagnosed.
- `.claude/skills/sdlc-intent/SKILL.md` step 5: open the intent PR as a draft; `gh pr ready` once the open
  questions are answered (one gate, one review), as PR #63 did. Keep every string
  `evals/cases/skill-names-match-templates.yaml` pins.

### B2 Rules fragment + the cap (net 0 lines)
`docs/sdlc/rules/30-conventions.md`: one new bullet after `:20` — "One agent **code** pull request open at
a time (intent-only ones may run beside it); open it as a draft and mark it ready once, at review — the gate
and the reviewer skip a draft, so the build window is CI-free, not gate-free." Pay for it by re-flowing the
reviewer-model bullet `:21-25` from five lines to four (drop "two of them introduced by the fix before" and
"so a later reader can tell a second pair of eyes from one"; prose only). Why net 0 is mandatory: adopter
CLAUDE.md = 11-line seeded header + 108 + 1 (`adopt.sh:489-503` re-flows `00-chain.md`) = **120** =
`MAX_CONTEXT_LINES`, and `gen_context_files.py:192-201` writes nothing when over. Measure before commit:
`bash scripts/adopt.sh "$SCRATCH/adopt" >/dev/null 2>&1 && python3 scripts/gen_context_files.py --root "$SCRATCH/adopt" && wc -l "$SCRATCH/adopt/CLAUDE.md"`
(no "over MAX_CONTEXT_LINES"; 120). Then `python3 scripts/gen_context_files.py`.

### B3 The measure — `actions_minutes_per_pr`
- `scripts/github_metrics.py`: choices (`:160`) += `actions_minutes_per_pr`; `--default-branch` (default
  `main`); `_api_path` (`:83-92`) shares the runs branch: `repos/{repo}/actions/runs?per_page=100&created=>={since}`
  (all workflows; each run carries `head_branch`, `event`, `created_at`, `run_started_at`, `updated_at`, `conclusion`).
- `_billed_minutes(run)`: `max(1, ceil((updated_at − run_started_at)/60))`, 0 when a stamp is missing or
  negative; `import math`. Per run, not per job (a multi-job run undercounts, a queued one overcounts; the
  band detects a trend against its own baseline so a constant bias cancels; `/actions/runs/{id}/timing` is
  the exact route, one call per run — switch only if the two diverge by more than the band width).
- `actions_minutes_series(runs, days, bucket="day", default_branch="main")`: count runs whose `head_branch`
  ≠ default branch (that is every run a PR causes, `delegated-merge`'s `workflow_run` wake included) and
  whose `conclusion` is not `None`; sum `_billed_minutes` per `_bucket_key(created_at)` and divide by the
  number of distinct branches in the bucket (one branch = one PR by `AGENT_BRANCH_PREFIXES`); omit empty
  buckets; keep the trailing `days` buckets from the newest present; one float per line oldest first.
- Fixture `scripts/fixtures/gh_runs_minutes.json` (same envelope as `gh_runs.json`, which has no timing
  fields): seven runs over three days → expected series `[5.0, 3.0]` (day 1: gate 48 s → 1 + review 3:00 →
  3 + merge wake 30 s → 1, one branch; nightly on `main` excluded; day 2: skipped 1 + success 2; day 3 only
  an in-progress run → omitted).
- Tests in `scripts/test_github_metrics.py`, class `ActionsMinutesSeries` mirroring `CiFailureSeries`:
  ordering; the one-minute floor; rounding up (3:05 → 4); default-branch runs excluded; the workflow_run wake
  counts; in-progress omits its bucket; two PRs on one day divide; empty input; `days=1` trims; `_api_path`
  starts with `repos/o/r/actions/runs?per_page=100&created=>=`; end-to-end `--from-json` piped into
  `detect_bands.py --window 2` (mirror `:134-141`).
- `monitoring/bands.yaml` entry (flat / flow-map shape only; `source:` must start with
  `scripts/github_metrics.py`, `window` ≥ 2):
```yaml
  - metric: actions_minutes_per_pr
    source: "scripts/github_metrics.py actions_minutes_per_pr --days 30"
    baseline: rolling_30d
    rules: western_electric
    window: 14
    tiers:
      1sigma: { action: log }
      2sigma: { action: diagnose, tools: "Read,Grep,Bash(gh run list *)" }
      3sigma: { action: propose,  routes: [report:engineering-leadership] }
```
- `scripts/test_bands_config.py:38-45` asserts exactly two GitHub metrics → three (names, windows, tools).
  `bands.yml` `actions: read` (`:17`) already covers `/actions/runs`; one more nightly matrix job.

### B4 Decision record + index
`knowledge/decisions/ci-budget-crucial-and-loosened.md` (front matter as `merge-click-is-the-gate.md:1-7`):
Context (the numbers) / Decision — crucial, untouched (one bullet each, naming the file that proves it) /
Decision — loosened, with the compensating control for each / Consequences (Linux signal one round later;
stale tracking comment harmless; the superseded-run rule is the one widened acceptance path and has its
own tests; the band makes a regression a filed issue) / Alternatives considered (Pro ≈ +3 days; spending
limit; public — taken separately by the owner; self-hosted runner) / Links. One line in
`knowledge/decisions/index.md` (hand-maintained).

### B5 Handoff
`docs/sdlc/handoff/HANDOFF.md`: new `## Task state (2026-09-09 …)` above `:48`, the old heading suffixed
`— HISTORY, superseded by the section above` (pattern at `:63`): the two PRs, the superseded-run rule as the
one non-obvious thing, branch protection's new required list, open follow-ups (triage JSON schema,
whether `edited` is still needed, the timing endpoint).

### B6 Land it
Verify; Opus reviewers; Fable checkpoint; ready; ledger; owner click.

## Phase 3 — acceptance (one week after PR-A merges), then retire
1. A throwaway draft: `sdlc-gate` and `pr-review` runs conclude `skipped` in seconds; a second push, same.
2. `gh pr ready` with no push → one gate run and one review on the same SHA, both `success` (that SHA now
   carries `skipped` and `success` runs — the exact shape F1 handles).
3. Actions → delegated-merge → Run workflow with that SHA (dry run): `CONDITION checks: ok — 2 required
   workflow(s) green` and `CONDITION review: ok …`.
4. Apply/remove `triage` on the ready PR: the new gate run queues, does not cancel; the dry run still `ok`.
5. `python3 scripts/github_metrics.py actions_minutes_per_pr --days 14` prints one float per day; the nightly
   `bands` matrix carries the metric.
6. After a week: the last seven values ≤ 10 (baseline 30); a PR of #61's shape ≤ 6 billed minutes; tracking
   comments per PR ≤ pushes-after-ready + 1; no `npm install -g @anthropic-ai/claude-code` in any gate log
   without the label; a red gate red in ≤ 1 min. Numbers into the closing ledger line.
7. Owner retires the item (`superseded`, ledger lines, pointer).

## Verification (per PR, this order; no `gh` in the container → chain check on the no-token path)
```
python3 scripts/gen_index.py && python3 scripts/gen_context_files.py && git add -A
env -u GH_TOKEN -u GITHUB_TOKEN scripts/verify.sh              # VERIFY: PASS (<sha>)
git commit …                                                    # commit BEFORE the origin/main chain check
env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/check_artifact_chain.py --base origin/main --slug ci-budget  # CHAIN: PASS
scripts/run_evals.sh | tail -1 ; python3 scripts/check_okf.py | tail -1
# PR-A
scripts/checks/workflow-yaml.sh && scripts/checks/workflow-permissions.sh
python3 -m unittest scripts.test_delegated_merge scripts.test_run_evals -v
# PR-B
python3 -m unittest scripts.test_github_metrics scripts.test_bands_config scripts.test_adopt -v
python3 scripts/github_metrics.py actions_minutes_per_pr --from-json scripts/fixtures/gh_runs_minutes.json   # 5.000000 / 3.000000
python3 scripts/bands_config.py                                 # 3 rows
bash scripts/adopt.sh "$SCRATCH/adopt" >/dev/null 2>&1 && python3 scripts/gen_context_files.py --root "$SCRATCH/adopt" && wc -l "$SCRATCH/adopt/CLAUDE.md"   # 120
```

## Risks and rollbacks
| Change | Risk | Bound / detection | Rollback |
|---|---|---|---|
| Superseded-run rule | Widens an acceptance path in the script that performs the click | Only `skipped`/`cancelled`, only with a later success of the same workflow on the same SHA; 13 tests incl. the directional and never-supersede-a-failure cases; branch protection's required check is the independent second control | Delete the two `_live_runs` lines |
| Draft guard | A Linux-only failure surfaces one round later, at ready | The ready gate run | Delete the job `if:` |
| Cancel-in-progress | A `cancelled` run on the head SHA | Only `synchronize` cancels; the rule absorbs the rest (a queued run evicted by a third event is the residual: re-apply the label) | `cancel-in-progress: false` |
| Triage label | A red gate is unexplained by default | The failing step is still named in the log | Drop the `contains(...)` clause |
| `agent-evals` off PRs | A regression if `VERIFY_CMDS` ever loses `run_evals.sh` | `test_the_deterministic_cases_still_run_on_every_gated_commit`; the nightly | Restore the trigger and job |
| Branch protection edit | Landed late, a required check that never reports blocks every PR | Same sitting as PR-A, before its merge | Re-add the check |
| Up-to-date off | Two code PRs semantically conflict | Serial queue; the merge script re-checks the head it merges | Turn it on; revert the convention line with it |
| Convention line | Adopter render at 121 → no context files written | `adopt.sh` measurement before commit | Re-flow one more prose line |
| `actions_minutes_per_pr` | Run-level approximation ≠ billing page | Trend detector; compare once against Billing | Switch `_billed_minutes` to `/timing` |
| Fork guard in `pr-review` | A wrong `--jq` path silently disables `@claude` | A green run whose summary says "refusing" on a repo-local PR | Remove the step and the four clauses — never before the flip |

## Fork-PR checklist (posted on PR #63 before the flip)
No workflow uses `pull_request_target`; a fork `pull_request` run gets no secrets and a read-only token.
| Workflow | Fork can reach | Guard |
|---|---|---|
| `sdlc-gate` | runs fork code on a read-only token; `HAS_CLAUDE_AUTH` false → triage never runs (`:22,58,72`) | boolean env indirection; none needed |
| `pr-review` `pull_request` | job runs, every step skipped (`HAVE_CLAUDE_AUTH` false, `:50-51`) | none needed |
| `pr-review` `issue_comment` | **base context, the key, `pull-requests: write`, fork head checked out (`:57`)** — owner's `@claude` on a fork PR | **A2b** head-repo guard before checkout; `author_association` (`:45`); no Bash (`:97`) |
| `agent-evals`, `bands` | none (schedule/dispatch on `main`) | trigger shape; A3 also closes fork-authored eval cases running on `scripts/**` PRs |
| `delegated-merge` | `workflow_run` fires with `contents: write` | `check_event` refuses `head_repository != repository` (`delegated_merge.py:274-278`, `test_delegated_merge.py:260-264`); checks out `main` only; `AGENT_BRANCH_PREFIXES` + `.sdlc/active` + `ALWAYS_LOCKED` behind it |
| `approve`, `deploy` | dispatch/release: write access, role gate, environment reviewers | none needed |
