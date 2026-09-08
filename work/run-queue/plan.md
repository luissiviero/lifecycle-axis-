---
type: sdlc/plan
id: run-queue
title: A next-item rule, an advance after the merge, and a skill that loops
description: "scripts/next_item.py fixes the queue order; delegated_merge.py advances .sdlc/active and both ledgers on main after a successful merge, behind a staged-path allowlist and a lost-update guard; the sdlc-run skill subscribes to its pull request and loops on the merge instead of ending."
stage: build
status: delegated
kind: feature
reads: spec.md
approved-by: claude
approved-on: 2026-09-08
risk-class: low
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/54
tags: [delegated-mode, run-queue, sdlc-run, active-pointer, delegated-merge, unattended]
timestamp: 2026-09-08T17:20:00Z
---
# Plan: a next-item rule, an advance after the merge, and a skill that loops (from intent.md 2026-09-08)

## Files that change
- scripts/next_item.py — new; the queue rule as a function and a CLI (R-1)
- scripts/test_next_item.py — new; the six R-1 cases (R-1)
- scripts/test_run_evals.py — `CaseBlocksAreWhole`, so a blank line can never truncate an eval check again (deviation 1, rule 7)
- knowledge/lessons/eval-checks-have-no-blank-lines.md — new; the lesson (deviation 1, rule 7)
- docs/sdlc/rules/60-lessons.md — its pointer line (deviation 1, rule 7)
- CLAUDE.md — regenerated from the rules fragments
- GEMINI.md — regenerated from the rules fragments
- AGENTS.md — regenerated from the rules fragments
- scripts/delegated_merge.py — the advance after the merge call, its allowlist and lost-update guard; `run()` gains `root` (R-2, R-3, R-5)
- scripts/test_delegated_merge.py — new class `Advance` (R-2, R-3, R-5)
- .claude/skills/sdlc-run/SKILL.md — the loop, the printed queue, the two new stop conditions (R-4)
- evals/cases/run-queue-stops-on-empty.yaml — new; an empty queue ends the run once (R-4)
- knowledge/decisions/run-queue.md — new; the advance route, amending delegated-mode.md decision 6
- knowledge/decisions/delegated-mode.md — the amendment pointer line
- knowledge/decisions/index.md — its entry for run-queue.md, written by hand (this index is not generated)
- docs/sdlc/rules/30-conventions.md — one paragraph re-flowed to free a line for the new lesson pointer (deviation 2)
- work/retire-active-pointer/revisions/index.md — new; the OKF warning this session left on main in pull request 53 (deviation 2)
- docs/sdlc/README.md — the inventory gains next_item.py
- work/run-queue/plan.md — this plan; its deviations log
- work/run-queue/log.md — ledger lines at each gate
- work/run-queue/index.md — regenerated
- work/index.md — regenerated

## Release-gated
(none)

## Order of work (each step independently verifiable)
1. **R-1, the rule.** Write `scripts/test_next_item.py` first (three granted intents, two sharing a date; a started item; a `superseded` intent; a risk class outside the policy; an empty queue), then `scripts/next_item.py`: `next_item(root, policy, exclude=None)` plus a CLI printing the slug (exit 0) or nothing (exit 3). Reuse `check_artifact_chain.front_matter` and `delegation.load`; validate the slug with the `SLUG_RE` shape before it names a path. Verify: `python3 -m unittest scripts.test_next_item`.
2. **R-2/R-3/R-5, the advance.** Write the `Advance` class in `scripts/test_delegated_merge.py` first and watch it fail. Then in `delegated_merge.py`: thread `root` into `run()` (it takes `active_slug` today but not the path), and after the comment call at `:868-869`, add `advance(root, out, merged_slug, number, head_sha, policy)` — compute the next item, re-read `.sdlc/active` and refuse unless it still names the merged item (lost-update guard), write the pointer, append the two ledger lines, stage exactly the three allowlisted paths and refuse any other, commit with `git -c user.name=... -c user.email=...` as `github-actions[bot]`, push to main. Never on refusal, never on `--dry-run`, never when the next item is the merged one. Verify: `python3 -m unittest scripts.test_delegated_merge` — the new class green, all 111 existing cases unchanged.
3. **R-4, the loop.** Edit `.claude/skills/sdlc-run/SKILL.md`: print the queue from `next_item.py` before starting; after the ready pull request, subscribe to it and wait for its merge; on merge re-read `.sdlc/active` and return to step 1 when it names a different granted, unstarted item; make every existing stop condition end the queue, and add the two new ones (empty queue; a merge needing the owner's click). Verify: the three greps in R-4.
4. **R-4, the eval.** `evals/cases/run-queue-stops-on-empty.yaml`, shaped like the existing hook cases. Verify: `scripts/run_evals.sh`.
5. **The record.** `knowledge/decisions/run-queue.md` (why the advance is CI's and not the pull request's: `ALWAYS_LOCKED`; why the wake is an instruction), its pointer line in `delegated-mode.md`, the regenerated decisions index, and `docs/sdlc/README.md`'s inventory line. Verify: `python3 scripts/check_okf.py`; `grep -c run-queue knowledge/decisions/delegated-mode.md` ≥ 1.
6. **R-6, the loop.** `GH_TOKEN= GITHUB_TOKEN= scripts/verify.sh`; `GH_TOKEN= GITHUB_TOKEN= python3 scripts/check_artifact_chain.py --base origin/main --slug run-queue`; `scripts/run_evals.sh`; `python3 scripts/check_okf.py`. Regenerate the indexes first. Paste the four last lines and the before/after test counts in the pull request.

## Risks
- Risk: the advance pushes to main from CI, and nothing chain-checks a push to main (spec G-5, C2) → mitigation: the staged-path allowlist refuses anything but the three files, mirroring `approve_dispatch.py:69-73`; the lost-update guard refuses when the pointer already moved; every write is one reviewable commit in main's history. The route is authorised by the owner merging this item.
- Risk: a push race — two pull requests merging close together, or a human commit landing between the checkout and the push → mitigation: **the push, and only the push**. It is not forced, so any commit that reached the remote first rejects it; the rejection is logged and the run ends without retry, leaving the pointer as it was for the next merge to advance. Corrected in review round 1: the pointer re-read inside `advance()` cannot fire through `run()`, because `check_pull_request` has already refused any pull request whose `Work-Item` is not the active slug, so it compares the file to itself. It stays as a precondition for a direct call, and the code says so.
- Risk: `run()`'s signature changes, and 111 existing tests call it → mitigation: `root` is added as a keyword argument with a default, so every existing call site and test keeps working; the count before and after goes in the pull request.
- Risk: the pull request cannot auto-merge — `.claude` and `scripts/delegated_merge.py` are both on the merge's locked paths (spec G-4) → not a defect: the owner clicks merge. No `control-plane-approved` label is needed, because no `PROTECTED_PATHS` entry is touched (spec G-3, G-4).
- Risk: `pr-review.yml` restores `.claude/skills` from the base branch, so the reviewer draws a false `Important` on the skill edit (`knowledge/decisions/delegated-mode.md:138-141`, seen on pull request 44) → mitigation: expected; the pull request says so, and the finding is answered rather than fixed.
- Risk: this item cannot be shown end to end before it merges — it is the only granted, unstarted item (spec C3) → mitigation: fixtures prove the mechanism; the pull request states plainly that the first real two-item run is the owner's next queue, and claims no live demonstration.
- What this could break: `delegated_merge.py` is the code that merges every delegated pull request. A defect in the advance runs *after* the merge call, so it cannot cause a wrong merge — the worst case is a wrong or missing pointer move, visible in main's history and fixable with a one-line edit. Every existing condition is untouched.
- Options considered and not taken: moving the pointer in the item's own pull request (refused by `ALWAYS_LOCKED`, spec G-2); a `repository_dispatch` to wake a session (nothing in-repo does this; bigger design, spec "Not doing"); relaxing the merge's active-slug check instead of moving the pointer (weakens a gate that exists to keep one item at a time); a policy key for order (spec D-4).

## Proof
- `scripts/verify.sh` green
- Spec rows → tests: R-1 → `scripts/test_next_item.py`; R-2 → `test_delegated_merge.py::Advance` (advance after merge; nothing on refusal; nothing on dry-run; empty queue clears the pointer); R-3 → `Advance::test_ledger_lines_parse_and_name_both_items`; R-4 → the three greps on the skill plus `evals/cases/run-queue-stops-on-empty.yaml`; R-5 → `Advance::test_refuses_any_path_outside_the_allowlist` and the 111 unchanged cases; R-6 → the four last lines in the pull request
- Manual / browser / screenshot / eval: no live two-item run is possible before this merges (spec C3); the eval covers the empty-queue stop only

## Rollback
- Revert the pull request. The advance is additive and runs after the merge call, so reverting restores today's behaviour exactly: the merge happens, nothing is written back, the pointer stays. Any pointer already advanced is a one-line edit.

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-08, step 4: the file list gains `scripts/test_run_evals.py`, `knowledge/lessons/eval-checks-have-no-blank-lines.md` and `docs/sdlc/rules/60-lessons.md`, under rule 7. The eval written in this step reported `✔ pass` while testing nothing: `run_evals.sh`'s `field()` ends a `key: |` block at the first unindented line and a blank line is unindented, so every assertion below the first blank was dead text. Found by mutating `next_item.py` on purpose and noticing the eval stayed green. That is the second oracle in this repository written so it could not fail — the first is `work/approve-by-dispatch` R-10's grep, which passes and which nothing runs — so rule 7 applies: the lesson file, its pointer line in the rules fragment, and `CaseBlocksAreWhole` in `test_run_evals.py` so the trap cannot come back silently. The eval now starts `set -e` and is mutation-tested three ways (a signed spec counted as unstarted, an empty queue exiting 0, the order reversed); the first two turn it red, and the third is caught by `test_next_item.Order` instead.
- 2026-09-08, step 5: two more files, both found unlisted by the plan-conformance pass. `docs/sdlc/rules/30-conventions.md` -- the new lesson's pointer line put the **adopter's** `CLAUDE.md` at 121 of 120 (this repository's own is only 108, so the cap bites on the adopter render, as it did on `retire-active-pointer`), so one paragraph of mine from pull request 51 was re-flowed from six lines to five; every rule kept, prose only. `work/retire-active-pointer/revisions/index.md` -- an OKF warning this session left on `main` in pull request 53: `revisions/` gained `1.md` during that item's review round, after the `0 warnings` line in its pull request had already been run and pasted, so the number was true when measured and stale by merge. Both are now in the file list. The `knowledge/decisions/index.md` bullet said "regenerated", which was wrong -- that index is hand-written -- and now says so.
- 2026-09-08, review round 1 (security-reviewer and plan-reviewer, both on sonnet; writer Opus 5): four Important and four nits, all taken, each with a regression case. Security: the lost-update guard is dead through `run()` because `check_pull_request` has already bound the slug, so the docstring now names the non-forced push as the real protection and keeps the check only as a precondition for a direct call; the allowlist bounds files and not their contents, so a clean-tree precondition refuses a dirty checkout outright; a non-UTF-8 `intent.md` in the queue crashed a job whose merge had already succeeded, so `run()` now catches `ValueError` too; and a `|` in a hand-typed grant field would have made the ledger line malformed and silently dropped, so `_ledger_safe()` replaces it. Compliance: the two unlisted files above, the two missing ledger lines, and R-3's actor string, which needed a spec revision (`revisions/1.md`).
- 
