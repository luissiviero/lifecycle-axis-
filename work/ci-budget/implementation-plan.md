---
type: sdlc/decision-record
id: ci-budget-implementation-plan
title: "Implementation guide for ci-budget: the two pull requests, the merge-script rule, and the measure"
description: "The owner's answers to every open question, the exact workflow and script changes for the control-plane and agent-side pull requests, the fork-pull-request pass for going public, the verification commands and the acceptance numbers. Written in the session that traced the Actions quota block and revised in the second session after the repository went public; the implementing session works from this file."
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

**Status 2026-09-09, second session (on Fable):** Actions runs again. The owner made the repository public
and changed nothing else; the gate ran green on this pull request's head at 12:36 UTC in 32 s. A public
repository gets unlimited minutes on standard runners, so goal (a) is a waste problem now, not a quota one;
(b) and (c) stand. Failure e-mails are off on the owner's side; Sourcery is uninstalled. Every row below
marked *revised* or *new* was decided in that session and is recorded on the intent. Every click the owner
still has to make is in the table at the end of this file, with its link.

## Everything decided (owner, 2026-09-09)
| # | Question | Decision |
|---|---|---|
| Q1 | Gate on drafts | **Skip `sdlc-gate` entirely on drafts**; `ready_for_review` added to its triggers. Agent runs `verify.sh` + chain check locally; nothing merges from a draft. |
| Q2 | "Require branches to be up to date" | **Off.** Compensating control: one agent *code* PR open at a time; intent-only PRs may run in parallel. |
| Q3 | Reviewer model | **Unchanged.** Cut the count first; measure a week; decide with a number. |
| Q4 | Failure triage | Kept behind a **`triage` label** (the `labeled` trigger re-runs the gate). |
| Q5 | Stale tracking comment after a cancelled review | Verified: `check_review` keys on the newest successful run's id (`delegated_merge.py:605-610`); a cancelled run's comment is never read. **No change.** |
| Q6 | The measure | New series `actions_minutes_per_pr` in `scripts/github_metrics.py` + a band in `monitoring/bands.yaml`. |
| I1 | Unblocking Actions | **Done: the repo is public** (2026-09-09, nothing else changed). *Revised:* the fork-PR pass came after the flip, so A2b is the first item of PR-A and the settings the flip skipped are Phase 0 clicks (0.2). The history scan ran in the second session: nothing. |
| I2 | PR shape | **Two PRs**: PR-A control plane first, PR-B agent side second. |
| I3 | Models | *Revised:* **the session runs on Opus and writes; Sonnet subagents scout, verify and review; Fable does a full revision at each milestone** (M1 spec+plan before the taps; M2 the PR-A diff before ready; M3 PR-A merged and branch protection edited; M4 the PR-B diff before ready; M5 the acceptance numbers before retirement), not only the divergence check. |
| I4 | Who edits workflows | **Agent writes under the unlock; owner labels `control-plane-approved`.** |
| F1 | Skipped runs in `delegated_merge.py` | *Revised, simpler:* **`_pr_runs` drops runs whose conclusion is `skipped`**; `cancelled` still refuses. A skipped `pull_request` run only ever means "every job's `if:` was false", i.e. the head was a draft, so it is never evidence; with cancel-in-progress bound to `synchronize` a cancelled run never lands on the head sha. Without the rule every PR that was ever a draft is unmergeable at its ready SHA. |
| F2 | Writer mechanism | **One session is the single writer** (one-writer-until-ledger stands), on Opus per I3; Sonnet subagents review; Fable milestone revisions. |
| F3 | `edited` trigger on the gate | *New:* keep `edited`, **skip the job when the action is `edited` and the sender is a Bot**. PR #63's last commit got two gate runs on one sha, the second from Sourcery's body edit; each woke the merge script. |
| F4 | Red merge-script runs on supervised PRs | *New:* a **`delegation` condition after `event`**: when the base checkout's `work/<slug>/intent.md` exists and its mode is not `delegated`, the verdict is **`not-delegated` and the run exits 0**; every other refusal stays red (exit 1). Today every gate/review completion on a supervised PR is a red, billed run (run 34352116586). |
| F5 | The measure's filter | *New:* **sum minutes of every run whose `event` is neither `schedule` nor `workflow_dispatch`; divide by the distinct non-default head branches in the bucket.** `head_branch != main` would drop every `delegated-merge` wake: the live API shows `workflow_run` runs with `head_branch: main`. |
| F6 | `.sdlc/active` | *New:* **the owner retires `run-queue-followups` and points the file at `ci-budget` on `main` before PR-A** (step 0.0). The plan gate reads the pointer; only a human writes `superseded` or the pointer. |
| F7 | Sourcery | **Uninstalled** (owner, 2026-09-09). |
| F8 | Skipped counts as green in branch protection | GitHub treats a skipped required check as passing. Nothing merges from a draft and the merge script demands `success`, so the controls hold; **the decision record (B4) says so**. |
| F9 | `triage` label | Does not exist yet (`control-plane-approved` does). **Owner creates it** before PR-A goes ready. |

**Crucial, kept byte-for-byte / name-for-name:** chain check + `verify.sh` + `check_control_plane.sh` on
every ready head before merge; check-run names `artifact-chain`, `review`, `merge`; policy
`require-checks: [sdlc-gate, pr-review]` and `require-review: true` on the final SHA; human-only
approvals and the tap; nightly `agent-evals --require-claude` and nightly `bands`; the `@claude` review;
`test_fork_head_repository_is_refused` (`test_delegated_merge.py:260-264`) untouched.

**Loosened → compensating control:** gate on drafts off → nothing merges from a draft, local verify;
review of every push → once per ready state, superseded pushes cancelled; model triage → `triage` label;
`agent-evals` on PRs → `verify.sh` runs the same cases on the same commit; merge wake on `agent-evals` →
it gated nothing since 15424e0; up-to-date rule → serial queue, one code PR at a time; a red merge run on
a supervised PR → a green `not-delegated` one, every real refusal still red; a gate run per Bot body edit →
none, a human's `edited` still runs.

## Roles and models (revised 2026-09-09)
- **Writer:** one session on Opus (`/model claude-opus-5` before Phase 0.4; one writer per item,
  `knowledge/decisions/one-writer-until-ledger.md`).
- **Scouts / verifier:** `explorer`, `verifier` subagents on Sonnet (`model: sonnet` at launch).
- **Reviewers:** `plan-reviewer` and `security-reviewer` on Sonnet (`model: sonnet`): once on spec+plan before
  code (as PR #58's `revisions/1.md`), once on each PR diff before it goes ready. A different model from the
  writer, as `30-conventions.md:21-25` asks.
- **Milestone revision:** switch to Fable (`/model claude-fable-5-1`) at each milestone and do a full pass, not
  only the divergence check: the artifacts or the diff against the intent's success criteria, the crucial
  list, the risks table and the verification output. M1 spec+plan before the taps; M2 the PR-A diff before
  `gh pr ready`; M3 PR-A merged and branch protection edited (the Phase 3 dry run); M4 the PR-B diff before
  ready; M5 the acceptance numbers before retirement. Each ends in a ledger line naming the model and the
  verdict ("no divergence" or the list).
- **Ledger** records writer, reviewer and revision models on every gate line (`30-conventions.md:21-25`).
- **Owner:** the clicks in the table at the end of this file, each with its link: the pointer, the settings,
  the taps, the `triage` and `control-plane-approved` labels, branch protection, merge clicks (PR-A carries a
  locked path; PR-B touches `.claude/skills/` — both wait on a click).

## Phase 0 — bookkeeping and unblocking (any model; no code)
0.0 **Retire `run-queue-followups` and move the pointer** (owner, from their own shell, one commit on `main`):
    `status: superseded` on `work/run-queue-followups/{intent,spec,plan}.md`, a ledger line each in its
    `log.md`, `.sdlc/active` set to `ci-budget`. Web editor for the pointer alone (one file per commit
    there): https://github.com/luissiviero/lifecycle-axis-/edit/main/.sdlc/active. Until this lands the
    plan gate refuses every edit under `scripts/`, and the chain check notes the mismatch on every
    ci-budget pull request.
0.1 Record the answers in `work/ci-budget/intent.md` — done twice: 2c16dae (Q1–Q6, I1–I4, F1) and the
    second session (the revisions, F3–F9); `gen_index.py`; a ledger line; one push to PR #63 each.
0.2 **Public — done** (owner, 2026-09-09, nothing else changed). What the flip skipped, now as clicks:
    - https://github.com/luissiviero/lifecycle-axis-/settings/actions — already right: fork workflow
      approval is "Require approval for all external contributors", and "Allow GitHub Actions to create and
      approve pull requests" is unchecked. **Still to change: Workflow permissions is "Read and write
      permissions"; select "Read repository contents and packages permissions"** and Save (every kit
      workflow declares its own `permissions:`, so no job loses a scope; `github-setup.md:78-80`). Optional:
      tick "Require actions to be pinned to a full-length commit SHA" — every `uses:` in
      `.github/workflows/` is pinned already.
    - https://github.com/luissiviero/lifecycle-axis-/settings/security_analysis — the section is called
      **Secret Protection** (GitHub's current name for secret scanning), at the bottom of the page: click
      **Enable**; a **Push protection** row appears under it once enabled; enable that too.
    - The history scan, run read-only in the second session — nothing found, as expected:
      `git grep -nIE 'sk-ant-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-|-----BEGIN [A-Z ]*PRIVATE KEY-----' $(git rev-list --all) -- . | grep -v block-secrets.sh`
      and `git log --all --diff-filter=D --name-only -- '*.env' '*.pem' '*.key'` (the only key-shaped
      strings are the pattern list in `.claude/hooks/block-secrets.sh:9` and the synthetic `AKIA…` token in
      `evals/cases/hook-refuses-planted-key.yaml`).
    - The fork-PR checklist (end of this file) stands; A2b, the one gap, is the first item of PR-A since
      the flip preceded it.
0.3 **Merge this pull request first, then tap.** `approve.yml` checks out the ref chosen in "Use workflow
    from branch" and writes there (`approve.yml:14-18`), and `work/ci-budget/` exists only on PR #63's
    branch — so a tap run from `main` fails with "no work/ci-budget/intent.md". Every previous approval in
    this repository followed the same order: the intent pull request merged, then the tap on `main` (runs 6,
    7 and 9 of `approve.yml`, each on a merge commit of the intent's own pull request). So: `gh pr ready` on
    #63, the owner merges it, then Actions → approve → Run workflow with branch `main`, `artifact:
    intent.md`, `mode: supervised`, **`slug` blank** (`.sdlc/active` on `main` already reads `ci-budget`,
    and a blank slug resolves to it; the slug is a free-text box, not a list of items) —
    https://github.com/luissiviero/lifecycle-axis-/actions/workflows/approve.yml. Running the tap from the
    pull request's own branch also works for a supervised approval, but it costs a second gate and review
    round on the approval commit and has no precedent here.
0.4 `/sdlc-spec` then `/sdlc-plan` (Opus session) from this document; Sonnet reviewers over both; Fable M1;
    taps (same link as 0.3, `artifact: spec.md`, then `plan.md`). `scripts/` is in `PLAN_REQUIRED_PATHS`, so
    no code before the plan tap.

## Phase 1 — PR-A: control plane (Opus writes under `SDLC_CONTROL_PLANE_UNLOCK`; owner labels + clicks)
Branch `claude/ci-budget-control-plane`; title `[ci-budget] Control plane: …`; body `Work-Item: ci-budget`;
opened as a **draft**, ready after the Fable M2 revision. A2b first: it is the one open exposure now.

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
    # the skipped-run rule in the merge script (work/ci-budget). A body edit by a Bot (Sourcery's
    # summary, an app's tracking comment) changes nothing the gate reads; a human's `edited` still runs.
    if: >-
      github.event.pull_request.draft == false &&
      !(github.event.action == 'edited' && github.event.sender.type == 'Bot')
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
**A2b — fork guard for the `@claude` route (first item of PR-A: the repo is public already).** On `issue_comment` the job
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

### A5 `scripts/delegated_merge.py` — the skipped-run rule and the not-delegated verdict (locked path; owner's click)
**Rule (F1, revised):** *a run whose conclusion is `skipped` is not a run of this pull request.* A
`pull_request` run concludes `skipped` only when every job's `if:` was false, which after A1 and the existing
`pr-review` guard means "the head was a draft"; it is never evidence for or against the head. `cancelled`,
`failure`, `timed_out` and an in-progress run are all kept, so every condition stays fail-closed.
```python
SKIPPED = "skipped"                                    # beside OK_CHECK_CONCLUSIONS, :78

def _pr_runs(runs, head_ref):                          # :243-253, one clause added
    """... A run concluded `skipped` is dropped too: a `pull_request` run skips only when every job's
    `if:` was false, i.e. the head was a draft (sdlc-gate.yml, pr-review.yml), and a draft's run says
    nothing about the head that later went ready on the same sha (work/ci-budget F1)."""
    return [r for r in (runs or [])
            if r.get("event") == "pull_request" and r.get("head_branch") == head_ref
            and not (r.get("status") == "completed" and r.get("conclusion") == SKIPPED)]
```
`check_required_runs`, `check_review` and `check_cool_off` all read `_pr_runs`, so nothing else changes; the
"no run at all" refusal now also covers a sha with only a skipped run (a draft that never went ready), which
`check_pull_request` refuses anyway. `check_check_runs` (`:366-380`) already accepts `skipped` check runs.

**Verdict (F4):** a new condition, `delegation`, recorded in `run()` after `event` (`:774-776`) and before
`pull-request`: `check_delegation(pulls, head_sha, root)` reads `work/<slug>/intent.md` from the checkout this
job runs from (main: `delegated-merge.yml:75-79`), `<slug>` being the body's `Work-Item` line through
`work_item_slug` (`SLUG_RE`, `:76`; no slug → `ok`, the pull-request condition refuses as today). When the
file exists and its `mode` is not `delegated`, the verdict is `NOT_DELEGATED = "not-delegated"` with the
detail `#<n>, Work-Item: <slug>, mode <mode>`; a missing file is `ok` here and refused later by the grant
check as today. `Run._code()` (`:698-709`) returns 0 for it like `WAITING`; `finish()` prints
`DELEGATED-MERGE: not-delegated (delegation)` through the existing line. Every other refusal keeps exit 1;
`check_grant_front_matter`'s own mode test (`:401-403`) stays as the second reading, from the API on the
base ref. The workflow's `pipefail` line (`delegated-merge.yml:89-91`) needs no change.

**Tests** (`scripts/test_delegated_merge.py`) — fixtures to the live two-name policy: `FIXTURE_POLICY:49`,
`RUN_IDS:85`, `make_runs:158`, `make_check_runs:169-173`, `required` at `:350` and `:842`,
`test_required_workflow_missing_is_refused:360-363` (filter on `sdlc-gate`). New — `Plumbing`: `_pr_runs`
drops a completed skipped run and keeps an in-progress one with no conclusion. `ChecksCondition`: a skipped
draft run beside a later success → OK; a sha with only a skipped run → REFUSED (no run); cancelled beside a
success → REFUSED (never dropped); failed beside a success → REFUSED. `ReviewCondition`: skipped review run
beside a success → OK and `newest` is the successful run; only a skipped run → WAITING (no completed run).
`CoolOff`: the skipped run's `updated_at` is not a stamp. `DelegationCondition`: a supervised intent →
`not-delegated` and `run()` returns 0 with the two summary lines; a delegated one → `ok`; no intent file →
`ok`; a body with no slug → `ok`; the dry run prints it and keeps going. `Plumbing`: `_code()` maps
`not-delegated` to 0 and `refused` to 1. `EndToEnd`: a PR that was a draft merges on its ready run
(`happy_path()` + a lower-id skipped run for both workflows → `DELEGATED-MERGE: merged #12`); a supervised
PR ends `DELEGATED-MERGE: not-delegated (delegation)` with exit 0 and no merge call.

### A6 Docs (replacement sentences in the same PR)
`docs/sdlc/README.md:84` (gate row: "skips drafts; triage is label-gated"), `:86`, `:106`, `:153` ("require
`sdlc-gate` and `pr-review`; never a workflow with a `paths:` filter or a draft guard"); `docs/sdlc/github-setup.md:72-73`
(required checks `sdlc-gate / artifact-chain`, later `pr-review`; up-to-date **off** with the serial-queue
rationale; conversation resolution on), `:88-89` (triage behind the label), `:132-135` (`agent-evals` no
longer runs on PRs; the skipped-run rule; a supervised pull request's merge run is green `not-delegated`),
new bullet: the `triage` label exists; `docs/sdlc/handoff/HANDOFF.md:78-80`
(done); `knowledge/decisions/merge-click-is-the-gate.md:31` and `:55-56` ("revisit if the repo goes public" →
superseded by the owner's flip, work/ci-budget); `knowledge/decisions/control-plane-label.md:46` ("keeps",
plus the triage route); `docs/sdlc/spikes/pr-review-identity.md:82-83`; `docs/sdlc/spikes/prompt-surfaces.md:289-291`
(`paths:` proposal moot); header comments in the three workflow files. `scripts/adopt.sh:347-349` copies the
three workflows verbatim — no template copy to edit.

### A7 Land it (order matters)
1. Verify (below); Sonnet reviewers on the diff; Fable M2; `gh pr ready`; ledger
   `PR #<n> | draft -> in-review | claude | <sha> | writer opus, reviewers sonnet, revision fable`.
2. Owner creates the `triage` label (https://github.com/luissiviero/lifecycle-axis-/labels), reads the
   workflow diff on the pull request, applies `control-plane-approved` there.
3. **Owner: branch protection** at https://github.com/luissiviero/lifecycle-axis-/settings/branches — as of
   2026-09-09 `main` carries **no protection rule at all** (the branches API reports `protected: false`;
   protection rules on a private repository need a paid plan, which is why the checklist in
   `github-setup.md` was never applied, and the flip to public has just made them free). So this step is
   "create the rule", not "edit it": required checks `sdlc-gate / artifact-chain` (add `pr-review` once it
   reports), **never** `agent-evals` (a `paths:` filter means it does not run on every pull request, and a
   required check that never reports blocks the merge forever — the same rule `delegated_merge.py:341-352`
   states), require branches to be up to date **off**, conversation resolution on. Creating it is optional
   for this item and changes no acceptance number; skipping it leaves the merge script's `require-checks`
   and the owner's click as the only controls, which is the state everything has run under so far.
4. Owner clicks merge (locked path → no delegated merge). Open PRs #59–#62 pick the workflows up on their
   next push; no close/reopen. Fable M3 after the Phase 3 dry run.

## Phase 2 — PR-B: agent side (Opus writes; Sonnet reviews; Fable M4; owner click)
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
- `actions_minutes_series(runs, days, bucket="day", default_branch="main")` (F5): count runs whose `event`
  is neither `schedule` nor `workflow_dispatch` (that is every run a PR causes: the gate, the review and
  `delegated-merge`'s `workflow_run` wake, which the live API reports with `head_branch: main`, so a branch
  filter would drop it) and whose `conclusion` is not `None`; sum `_billed_minutes` per
  `_bucket_key(created_at)` and divide by the number of distinct head branches ≠ default branch in the
  bucket (one branch = one PR by `AGENT_BRANCH_PREFIXES`; a bucket with minutes and no such branch is
  omitted); omit empty buckets; keep the trailing `days` buckets from the newest present; one float per line
  oldest first.
- Fixture `scripts/fixtures/gh_runs_minutes.json` (same envelope as `gh_runs.json`, which has no timing
  fields): seven runs over three days → expected series `[5.0, 3.0]` (day 1: gate 48 s → 1 + review 3:00 →
  3 + merge wake 30 s on `main`, event `workflow_run` → 1, one branch; the nightly on `main`, event
  `schedule`, excluded; day 2: skipped 1 + success 2; day 3 only an in-progress run → omitted).
- Tests in `scripts/test_github_metrics.py`, class `ActionsMinutesSeries` mirroring `CiFailureSeries`:
  ordering; the one-minute floor; rounding up (3:05 → 4); `schedule` and `workflow_dispatch` runs excluded;
  the `workflow_run` wake on `main` counts; a day with wakes and no PR branch is omitted; in-progress omits
  its bucket; two PRs on one day divide; empty input; `days=1` trims; `_api_path` starts with
  `repos/o/r/actions/runs?per_page=100&created=>=`; end-to-end `--from-json` piped into
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
GitHub counts a skipped required check as passing, and nothing merges from a draft while the merge script
demands `success` (F8); stale tracking comment harmless; the skipped-run rule and the not-delegated verdict
are the two widened paths in the merge script and have their own tests; the band makes a regression a filed
issue) / Alternatives considered (Pro ≈ +3 days; spending
limit; public — taken separately by the owner; self-hosted runner) / Links. One line in
`knowledge/decisions/index.md` (hand-maintained).

### B5 Handoff
`docs/sdlc/handoff/HANDOFF.md`: new `## Task state (2026-09-09 …)` above `:48`, the old heading suffixed
`— HISTORY, superseded by the section above` (pattern at `:63`): the two PRs, the superseded-run rule as the
one non-obvious thing, branch protection's new required list, open follow-ups (triage JSON schema,
whether `edited` is still needed, the timing endpoint).

### B6 Land it
Verify; Sonnet reviewers; Fable M4; ready; ledger; owner click.

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
7. Fable M5 over the numbers; owner retires the item (`superseded`, ledger lines, pointer).

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
| Skipped-run rule | Widens an acceptance path in the script that performs the click | Only `skipped`, which a `pull_request` run reaches only through a false job `if:`; `cancelled` and `failure` are never dropped; the no-run refusal still catches a sha with only a skipped run. **Correction (2026-09-09): `main` has no branch protection, so the required-status-check second control the earlier draft cited does not exist today** — the merge script's own `require-checks` and the owner's click are the controls, which is why the tests below are the bound that matters | Delete the one clause in `_pr_runs` |
| Not-delegated verdict | A real refusal hides behind exit 0 | One reason only (the base intent's mode is not `delegated`), decided before any grant check; every other refusal keeps exit 1, each with a test | Map the verdict to `REFUSED` in `_code()` |
| Bot-edited guard | A Bot body edit that mattered gets no gate run | The gate reads only `Work-Item:` from the body, which no Bot writes; the next push runs it | Drop the clause |
| Draft guard | A Linux-only failure surfaces one round later, at ready | The ready gate run | Delete the job `if:` |
| Cancel-in-progress | A `cancelled` run on the head SHA | Only `synchronize` cancels; the rule absorbs the rest (a queued run evicted by a third event is the residual: re-apply the label) | `cancel-in-progress: false` |
| Triage label | A red gate is unexplained by default | The failing step is still named in the log | Drop the `contains(...)` clause |
| `agent-evals` off PRs | A regression if `VERIFY_CMDS` ever loses `run_evals.sh` | `test_the_deterministic_cases_still_run_on_every_gated_commit`; the nightly | Restore the trigger and job |
| Branch protection edit | Landed late, a required check that never reports blocks every PR | Same sitting as PR-A, before its merge | Re-add the check |
| Up-to-date off | Two code PRs semantically conflict | Serial queue; the merge script re-checks the head it merges | Turn it on; revert the convention line with it |
| Convention line | Adopter render at 121 → no context files written | `adopt.sh` measurement before commit | Re-flow one more prose line |
| `actions_minutes_per_pr` | Run-level approximation ≠ billing page | Trend detector; compare once against Billing | Switch `_billed_minutes` to `/timing` |
| Fork guard in `pr-review` | A wrong `--jq` path silently disables `@claude` | A green run whose summary says "refusing" on a repo-local PR | Remove the step and the four clauses — never before the flip |

## Owner's clicks, with links (in order)
| # | Click | Where | When |
|---|---|---|---|
| 1 | Workflow permissions → "Read repository contents and packages permissions"; optional: require SHA-pinned actions | https://github.com/luissiviero/lifecycle-axis-/settings/actions | Now |
| 2 | Secret Protection → Enable, then Push protection → Enable | https://github.com/luissiviero/lifecycle-axis-/settings/security_analysis | Now |
| 3a | Set `.sdlc/active` to `ci-budget` — **done** 2026-09-09 (308f1a2) | https://github.com/luissiviero/lifecycle-axis-/edit/main/.sdlc/active | Done |
| 3b | Retire `run-queue-followups`: `superseded` on its `intent.md` (now `approved`), `spec.md` and `plan.md` (now `delegated`), a ledger line each in its `log.md` | your shell, one commit on `main` | Before PR-A |
| 4a | Mark PR #63 ready and merge it — the tap needs `work/ci-budget/` on `main` | the pull request's page | Before 4b |
| 4b | Approve `intent.md`: branch `main`, `artifact` intent.md, `mode` supervised, **`slug` blank** | https://github.com/luissiviero/lifecycle-axis-/actions/workflows/approve.yml | After 4a |
| 5 | Approve `spec.md`, then `plan.md` | same as 4 | After Fable M1 |
| 6 | Create the `triage` label | https://github.com/luissiviero/lifecycle-axis-/labels | Before PR-A goes ready |
| 7 | Apply `control-plane-approved` on PR-A | the pull request's page | After Fable M2 |
| 8 | Branch protection (optional): `main` has none today — if you create one, require `sdlc-gate / artifact-chain`, never `agent-evals`, up-to-date off | https://github.com/luissiviero/lifecycle-axis-/settings/branches | Same sitting as 9 |
| 9 | Merge PR-A | the pull request's page | After 8 |
| 10 | Dry run of the merge conditions on a ready SHA | https://github.com/luissiviero/lifecycle-axis-/actions/workflows/delegated-merge.yml | Phase 3, then Fable M3 |
| 11 | Merge PR-B | the pull request's page | After Fable M4 |
| 12 | Retire `ci-budget` | your shell | After Fable M5 |

## Fork-PR checklist (the flip came first; the table stands, A2b closes the one gap)
No workflow uses `pull_request_target`; a fork `pull_request` run gets no secrets and a read-only token.
| Workflow | Fork can reach | Guard |
|---|---|---|
| `sdlc-gate` | runs fork code on a read-only token; `HAS_CLAUDE_AUTH` false → triage never runs (`:22,58,72`) | boolean env indirection; none needed |
| `pr-review` `pull_request` | job runs, every step skipped (`HAVE_CLAUDE_AUTH` false, `:50-51`) | none needed |
| `pr-review` `issue_comment` | **base context, the key, `pull-requests: write`, fork head checked out (`:57`)** — owner's `@claude` on a fork PR | **A2b** head-repo guard before checkout; `author_association` (`:45`); no Bash (`:97`) |
| `agent-evals`, `bands` | none (schedule/dispatch on `main`) | trigger shape; A3 also closes fork-authored eval cases running on `scripts/**` PRs |
| `delegated-merge` | `workflow_run` fires with `contents: write` | `check_event` refuses `head_repository != repository` (`delegated_merge.py:274-278`, `test_delegated_merge.py:260-264`); checks out `main` only; `AGENT_BRANCH_PREFIXES` + `.sdlc/active` + `ALWAYS_LOCKED` behind it |
| `approve`, `deploy` | dispatch/release: write access, role gate, environment reviewers | none needed |
