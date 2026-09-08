---
type: sdlc/spec
id: run-queue
title: The merge advances the pointer to the next granted item, and the run loops instead of ending
description: "A deterministic next-item rule, an advance the merge workflow commits to main after it merges (the only place that may write .sdlc/active), ledger lines on both items, and a sdlc-run that loops on its own pull request's merge event instead of ending at one ready pull request."
stage: design
status: delegated
reads: intent.md
approved-by: claude
approved-on: 2026-09-08
skills-applied: [security-standards]
skills-version: a398fad
prompt: "/sdlc-run run-queue -> /sdlc-spec, in session_014hU9gCLdAQNspXN6Hnh6Nj, from the approved and delegated intent and an explorer pass over the seven workflows, delegated_merge.py, approve_dispatch.py, check_artifact_chain.py, protect-paths.sh, the sdlc-run skill, and knowledge/decisions/{delegated-mode,one-writer-until-ledger}.md"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/54
tags: [delegated-mode, run-queue, sdlc-run, active-pointer, delegated-merge, unattended]
timestamp: 2026-09-08T17:00:00Z
---
# Spec: the merge advances the pointer, and the run loops

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `scripts/next_item.py` answers "which item is next" deterministically from `work/*/intent.md` alone: candidates have `status: approved`, `mode: delegated`, a `risk-class` the policy delegates, and are **unstarted** (no `spec.md`, or its status is `draft`/`in-review`). Order: earliest `delegated-on`, ties broken by slug ascending (`delegated-on` is date-only, so ties are the normal case — G-6). Absent grant keys mean "not granted", never "empty" (G-7). CLI: prints the slug and exits 0, or prints nothing and exits 3 when the queue is empty. | 2 (the pointer names the next granted, unstarted item) | `scripts/test_next_item.py` — a fixture repo with three granted intents (two same-date) returns them in slug order; a started item (spec `delegated`) is skipped; a `superseded` intent is skipped; a `risk-class` outside the policy is skipped; an empty queue exits 3 |
| R-2 | After a successful merge, and only then, `scripts/delegated_merge.py` advances: it computes R-1's next item, writes `.sdlc/active`, appends one ledger line to the merged item's `log.md` and one to the next item's, and commits **to main** with its own git identity (`git -c user.name=... -c user.email=...`, so `.github/workflows/` needs no change — G-3). It never advances on a refusal, on `--dry-run`, or when the next item is the item just merged. | 1, 2, 3 (advance without a human; both ledgers) | `scripts/test_delegated_merge.py` — new class `Advance`: advances after a merge; writes nothing on every refusal path; `--dry-run` writes nothing; an empty queue clears the pointer and says so; the two ledger lines parse with `log_ledger.parse` |
| R-3 | The advance is retraceable from the ledgers alone: the merged item gets `- <ts> \| PR #<n> \| in-review -> in-review \| claude[bot] \| <sha> \| merged as <sha>; .sdlc/active advanced to <next>`, and the next item gets `- <ts> \| intent.md \| approved -> approved \| claude[bot] \| <sha> \| .sdlc/active advanced here after PR #<n> merged, under the grant by <handle> on <date>`. The `<from> -> <to>` slot holds `status` values only (`knowledge/lessons/ledger-slot-holds-status-only.md`). | 3 (the whole night readable from `work/*/log.md`) | `Advance::test_ledger_lines_parse_and_name_both_items` — both lines parse; the merged item's line names the next slug; the next item's names the pull request and the grant handle |
| R-4 | `.claude/skills/sdlc-run/SKILL.md` loops: it subscribes to the pull request it opens, and on that pull request's **merge** re-reads `.sdlc/active`; if the pointer names a different, granted, unstarted item it returns to step 1 for that item, with no human input. It prints the queue (R-1's order) before starting, so the owner knows what will happen before leaving. Every existing "stop and call the owner back" condition stops the **queue**, plus two new ones: the queue is empty, and a merge that needs the owner's click (a locked-path item). | 1, 4 (loop; clean stops) | `grep` on the skill: `subscribe_pr_activity` ≥ 1, `next_item.py` ≥ 1, `.sdlc/active` ≥ 1; `evals/cases/run-queue-stops-on-empty.yaml` — an empty queue ends the run with one message, no second attempt |
| R-5 | Nothing an agent may decide widens. The advance writes only `.sdlc/active` and two `log.md` files (a fixed allowlist, refusing any other staged path the way `approve_dispatch.py:69-73` does); it never writes `approved`, `superseded`, or any grant key; N queued items are N human grants. The pointer is only ever written by the merge workflow or the approve dispatch — never by an item's own pull request, which `ALWAYS_LOCKED` refuses (G-2). | 5 (nothing else changes) | `Advance::test_refuses_any_path_outside_the_allowlist`; `grep -c 'approved\|superseded' ` over the advance's write set is 0; every existing `test_delegated_merge.py` case passes unchanged |
| R-6 | The whole loop is green and supervised mode is untouched: `scripts/verify.sh` ends `VERIFY: PASS`, the chain check `CHAIN: PASS`, `scripts/run_evals.sh` `0 fail`, `check_okf.py` `0 warnings`; the 111 pre-existing `test_delegated_merge.py` cases pass unchanged. | 5 | the four last lines and the before/after test counts, in the pull request |

## Design
### Architecture / data flow
The run becomes a loop with a CI-side hinge. Per item k:

1. The session works item k exactly as today (spec → plan → build → review → ready pull request).
2. `delegated-merge.yml` merges it when its conditions hold — unchanged.
3. **New:** still inside that workflow run, on main's checkout, `delegated_merge.py` computes the next
   item (R-1), writes `.sdlc/active`, appends the two ledger lines (R-3), and commits to main.
4. **New:** the session, subscribed to its own pull request, is woken by the merge, re-reads
   `.sdlc/active`, sees item k+1, and loops to step 1 (R-4).

Step 3 is code and is fully tested. Step 4 is an instruction in the skill, exercised by this
repository's own harness rather than by a unit test — stated plainly in C1 rather than dressed up as
a machine-checked property.

### Interfaces (APIs, events, schemas) — exact shapes
- `python3 scripts/next_item.py` → the slug on stdout, exit 0; nothing, exit 3, when the queue is empty.
  `--exclude <slug>` omits one item (the one just merged, before its own spec is written).
- `next_item(root, policy, exclude=None) -> str | None` — the same rule as a function, so
  `delegated_merge.py` imports it rather than shelling out.
- The advance commit: message `[<next>] Advance .sdlc/active after #<n> merged`, author and committer
  `github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>`, staged paths exactly
  `{.sdlc/active, work/<merged>/log.md, work/<next>/log.md}`.
- An empty queue writes an empty `.sdlc/active` (a valid state, `check_artifact_chain.py:476-481`
  reports it in one line) and one ledger line on the merged item saying the queue is empty.
- The two ledger lines: as quoted in R-3.

### Data and migrations
None. No new file format, no front-matter key, no policy key (G-8: the intent allows the spec to name
one; none is needed — the order rule is fixed, not configurable). `.sdlc/active` keeps its shape.
No personal or regulated data (security-standards §4: n/a).

### Failure modes and how they surface
- Two workflow runs racing to advance → `delegated-merge.yml:59-62` serialises by head sha, but two
  *different* pull requests could merge close together. The advance therefore re-reads `.sdlc/active`
  immediately before writing and refuses if it no longer names the merged item (a lost-update guard),
  and the push is `--force-with-lease`-free: a rejected push is logged and the run ends without retry.
- The next item's grant has gone stale (its intent edited between grant and turn) → R-1 re-reads the
  intent at advance time, so a no-longer-eligible item is simply not selected.
- The session dies mid-queue → the pointer on main is already correct, so a new session started by
  the owner resumes at item k+1 with no repair. This is the design's recovery story.
- The merge needs the owner's click (locked path) → no merge event, so no advance and no loop; the
  queue stops there by construction, which is R-4's second new stop condition.
- The advance commit lands on main without a chain check (nothing runs `check_artifact_chain.py` on a
  push to main) → G-5; mitigated by the allowlist (R-5) and by the commit being reviewable in main's
  history, not by a gate. Named as C2.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the loop's wake (step 4) is a **skill instruction, not code**, and depends on the harness
  delivering the merge event to a live session. Observed working in this session (pull request 53's
  `merged` event arrived and the session continued), but it is not unit-testable and a dead session
  breaks the chain — policy: none — contradiction? no — owner: luissiviero — resolution: accepted with
  the recovery story above (a new session resumes from the pointer, no repair needed); an hourly
  `send_later` check-in is the documented fallback (`HANDOFF.md:17`).
- C2: the advance commits to **main** from CI, and no chain check runs on a push to main — policy:
  rule 4 ("never push to a protected branch") binds the *agent*, and `approve.yml` already pushes to
  main from CI under the same reasoning — contradiction? no — owner: luissiviero — resolution: the
  staged-path allowlist (R-5) is the guard, mirroring `approve_dispatch.py`; the owner authorises the
  route by merging this item.
- C3: this item **cannot be demonstrated end to end before it merges**: it is the only granted,
  unstarted item in the repository (G-1), so there is no second element for a live queue — policy:
  none — contradiction? no — owner: luissiviero — resolution: fixtures and unit tests prove the
  mechanism; the first real two-item run is the owner's next queue, and the pull request says so
  instead of claiming a live demonstration.

## Open questions carried from intent.md
- Q1 "who starts item k+1?" — answered by D-1: the pointer advance is CI's (code), the wake is the
  session's own pull-request subscription (instruction), with a new session from the pointer as recovery.
- Q2 "in what order?" — D-2: earliest `delegated-on`, ties by slug ascending, printed before the run
  starts. Ties are the normal case, not the exception (G-6).
- Q3 "does advancing retire item k?" — D-3: no. `superseded` stays human-only
  (`protect-approvals.sh:48`); the advance only moves the pointer and writes two ledger lines.
- Q4 "a locked-path item mid-queue?" — D-4: the queue stops there by construction (no merge, no
  event, no advance); the skill says to grant such items last.

## Decisions (ADR-style: context → decision → consequences)
- D-1: **The merge advances the pointer; the session only follows it.** Context: an item's own pull
  request may never contain `.sdlc/active` (`ALWAYS_LOCKED`, G-2), and `delegated-merge.yml` already
  checks out **main** with `contents: write` on the allowlist (G-3) at exactly the moment an item
  finishes. Decision: the advance is a write-back in `delegated_merge.py` after the merge call.
  Consequences: the pointer is correct on main whether or not any session is alive; the session's role
  shrinks to noticing, which is what makes a dead session recoverable rather than fatal.
- D-2: **Order is earliest `delegated-on`, ties by slug.** Context: `delegated-on` is date-only, so two
  items granted the same day tie (G-6, and the two live grants do tie). Decision: a total order, fixed
  in code, printed before the run. Consequences: the owner controls order by granting on different
  days or by naming; no order file, no policy key.
- D-3: **The advance never retires.** Context: `superseded` is human-only. Decision: the pointer moves;
  item k stays `approved`/`delegated` until the owner retires it. Consequences: `retire-active-pointer`'s
  R-2 failure does not fire (it keys on the *intent* being superseded, which the advance never writes),
  and the two features compose.
- D-4: **No new policy key.** Context: the intent permits one, and `.sdlc/delegation.yaml` is owner-only.
  Decision: none is needed — the order is fixed and the queue's membership is already governed by the
  existing `risk-classes` and the per-item grants. Consequences: nothing for the owner to write; the
  queue's size is bounded only by how many items they grant.
- D-5: **`next_item.py` is a separate script, imported.** Context: `delegated_merge.py` is on
  `locked-paths` and already 900 lines. Decision: the rule lives in its own tested module. Consequences:
  a second file on the diff, and a rule the skill can also run to print the queue (R-4).

## Gotchas found while reading the codebase
- G-1: **`run-queue` is the only granted, unstarted item in the repository.** `approve-by-dispatch` and
  `retire-active-pointer` are granted but fully built. So this item's own queue is empty behind it, and
  no live two-item run can be demonstrated before it merges (C3).
- G-2: **An item's own pull request may never move the pointer.** `delegated_merge.py:87-91`
  `ALWAYS_LOCKED` includes `.sdlc`, and `check_locked_paths` refuses on prefix match. This is what
  forces the advance into CI.
- G-3: **`delegated-merge.yml` checks out main, not the head** (`:75-79`, "the ONLY checkout, and it
  takes the default branch, never the pull request head"), and holds `contents: write`, allowlisted at
  `check_workflow_permissions.py:46-49`. So the advance needs no workflow edit — and therefore touches
  no `PROTECTED_PATHS` and needs no `control-plane-approved` label.
- G-4: **`.claude/skills` is not in `PROTECTED_PATHS`** (`.sdlc/config.env`), so `check_control_plane.sh`
  reports a skill edit clean — but `delegated_merge.py:88` `ALWAYS_LOCKED` includes `.claude`, so the
  pull request still cannot auto-merge, and `pr-review.yml` restores skills from the base branch, which
  draws a false `Important` (`knowledge/decisions/delegated-mode.md:138-141`, observed on pull request 44).
- G-5: **Nothing chain-checks a push to main.** `sdlc-gate.yml` runs on `pull_request`. The advance
  commit is therefore unchecked by CI; its guard is the staged-path allowlist (C2).
- G-6: **`delegated-on` is date-only** (`2026-09-06`, `2026-09-08`), so the tiebreak is the common path,
  not an edge case: the two live grants share a date.
- G-7: **A non-granted intent omits the grant keys entirely** rather than leaving them blank (only
  `_example` uses the blank form), so the ranker must treat an absent key as "not granted".
- G-8: **`.sdlc/delegation.yaml` has no queue, concurrency or session-lifetime key**, and
  `require-checks` lists two names while `delegated-merge.yml` listens on three — listing more only
  decides when to look (`:26-30`), never what is required.
- G-9: **No prior decision bounds how long an agent may run unattended.** The nearest rule is about
  unattended *deploys* (`production-gate.sh:117`), not unattended *runs*. This item is the first to
  raise it, as the intent's risk note says.
- G-10: **`one-writer-until-ledger.md` expires 2027-03-05** and constrains writers *within* an item;
  a serial queue keeps one writer per item, so it composes — a parallel queue would not, which is why
  the intent puts parallelism out of scope.

## Security standards, applied
§1 secrets: n/a, none touched; the advance uses the workflow's existing `GITHUB_TOKEN`. §2 auth: n/a,
no endpoint; the merge's own conditions are unchanged. §3 input: the slug from `next_item.py` is
validated with the same `SLUG_RE` shape before it names a path (`retire-active-pointer` R-7 set this
precedent); the staged-path allowlist bounds every write. §4 data: none. §5 dependencies: none.
§6 infra: no `RELEASE_GATED_PATHS`; the advance is a commit to main, covered by C2. §7 logging: the
ledger lines carry slugs, a handle and a sha, no personal data. §8 hygiene: the writer of this spec
does not approve it; signed under the grant, reviewed on a different model.

## Not doing
- Waking a session from CI (a `repository_dispatch`, a watched comment): nothing in-repo does this
  today (G-1 of the explorer pass) and the subscription route already works; a bigger design if the
  subscription proves unreliable.
- Parallel items — the intent's own out-of-scope, and it would break one-writer (G-10).
- Retiring item k on advance (D-3), or any change to what an agent may sign.
- A policy key for queue behaviour (D-4); reordering or cancelling a queue mid-run (intent, out of scope).
- Changing supervised mode, `approve.yml`, or the `gh`-absent crash in `check_artifact_chain.py:192`.
