---
type: sdlc/plan
id: session-chaining
title: One session per work item, its state in git, its successor scheduled after the push
description: "One pull request of instructions and documentation: the chaining act in sdlc-run, the protocol and seed prompt in the handoff, the two skill corrections, one rendered pointer line paid for by re-flow, and a hook-kind eval case that is red on main today."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: in-review
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: feature
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by:
approved-on:
risk-class: low
record:
resource: spec.md
tags: [sdlc, skills, handoff, context, session, protocol, evals]
timestamp: 2026-09-13T22:40:00Z
---
# Plan: one session per work item, its state in git, its successor scheduled after the push (from intent.md 2026-09-13)

One pull request on this session's branch `claude/app-creation-mock-test-w4gf88`, reset from `main`, opened as a
draft and ending in the owner's merge click — which this item needs whatever its mode, because the owner put
`docs/sdlc/handoff` on the policy's `locked-paths` at `d035c6e` (spec C5, closed) and this diff edits that file.
The writer is this session on Fable; the reviewers run on a different model (`plan-reviewer` and
`security-reviewer` on Sonnet, with Opus as the second pair where a finding is contested), per the convention the
repository renders at `CLAUDE.md` "A review runs on a different model".

Two consequences the owner is deciding when they tap this plan, both following from the approved spec rather
than departing from it:
- **The per-cycle handoff refresh is a pull request the owner clicks, every cycle.** Spec R2 orders the chaining
  act (a) confirm `.sdlc/active` on `main`, (b) refresh the handoff, (c) commit and push, (d) schedule, (e) end.
  Step (a) is only answerable after the item's pull request has merged, so (b) and (c) cannot ride in that pull
  request: they are a second, handoff-only draft pull request. With `docs/sdlc/handoff` locked, the merge script
  refuses it (`check_locked_paths`, proved on `HANDOFF.md` when C5 closed), so the owner merges it by hand. Under
  `/sdlc-run`, "a path under the policy's locked-paths is needed" stops the whole queue today (`SKILL.md:62-64`),
  so step 7 must say plainly that this one pull request is the exception: nothing downstream reads it from `main`
  — the successor is handed the same prompt as its payload and re-reads `.sdlc/active` (R2a, R10) — so the queue
  does not stop for it, and an unmerged refresh costs the owner a stale handoff, never a wrong pointer. The
  alternative, refreshing the handoff from CI beside `advance()`, is a `scripts/` change that R9 forbids and the
  spec would have to be amended for; it is recorded under Risks, not taken.
- **The eval case proves every requirement it can, and R8 is proved outside it.** The adopter-render check
  (`adopt.sh` into scratch) is the only discriminating proof of R8 and takes seconds, not a grep; it runs as a
  named step here and is pasted in the pull request, not folded into `evals/cases/`.

## Files that change
Every path that will change. Globs allowed. CI fails the PR if the diff touches anything else.
- .claude/skills/sdlc-run/SKILL.md — R2 the chaining act as step 7's last act, ordered (a)–(e), at most one successor per finish and never as a successor's own first act; R4 the runtime sentence and the no-capability fallback ("skip (d) and say so in the final message"); R10 the prompt is context, never authority, and the successor re-reads the item's approved artifacts; the "Stop and call the owner back" paragraph names the handoff-refresh pull request as the one locked-path pull request the queue does not stop for. The `## Never` list is unchanged
- .claude/skills/sdlc-review/SKILL.md — R5 step 6 names `knowledge/lessons/` plus a pointer line in `docs/sdlc/rules/60-lessons.md`, and no longer names `CLAUDE.md` at all
- .claude/skills/sdlc-intent/SKILL.md — R6 step 1 creates `work/<slug>/log.md` with its first ledger line, and a step runs `python3 scripts/gen_index.py` before the pull request opens; headings the `skill-names-match-templates` case pins are untouched
- docs/sdlc/handoff/HANDOFF.md — R1 the `## Session protocol` section with its three invariants; R3 the prompt section renamed (heading carries "seed prompt"; body says it is `refreshed` by the finishing session, read by the next one, and `standalone`), its text rewritten for the state at the end of this item; R7 lines 37 and 194 corrected to say the merge workflow's `advance()` moves `.sdlc/active` and the session never does; the `## Task state` refreshed for this item, the superseded one demoted as the file already does
- docs/sdlc/rules/00-chain.md — R8 the pointer, one clause on the `.sdlc/active` sentence (lines 23-24): the session protocol and the seed prompt are in `docs/sdlc/handoff/HANDOFF.md`. Never lines 12-14: `scripts/adopt.sh:493-499` replaces that paragraph by exact match and `scripts/test_adopt.py:485-488` pins the result, so any re-flow there silently ships "starter kit" to adopters and fails that test
- docs/sdlc/rules/30-conventions.md — R8 the payment: one line fewer, by re-flowing the shell-approval bullet (body lines 22-25, four lines at 102-118 characters, into three at or under the fragment's existing 132-character width); no rule dropped, no word of meaning dropped
- CLAUDE.md — R8 regenerated
- GEMINI.md — R8 regenerated
- AGENTS.md — R8 regenerated
- evals/cases/session-protocol-is-written-down.yaml — new hook-kind case, sibling to `skill-opens-drafts`, pinning R1, R2, R3, R4, R5, R6, R7 and R10 with the greps of the spec's third column; every negated assertion ends `|| exit 1` (`scripts/check_eval_cases.py`)
- work/session-chaining/plan.md — this plan; its deviations log
- work/session-chaining/log.md — ledger lines
- work/session-chaining/index.md — regenerated
- work/index.md — regenerated

## Release-gated
Paths under RELEASE_GATED_PATHS with a named human owner (leave "(none)" if none).
- (none)

## Order of work (each step independently verifiable)
1. Branch reset from `main`; draft pull request `[session-chaining] …` with `Work-Item: session-chaining`. Write `evals/cases/session-protocol-is-written-down.yaml` first and watch it fail on the unchanged tree. Verifiable: `scripts/checks/eval-cases.sh` ends `0 problems` (the case is well-formed), and `scripts/run_evals.sh --only session-protocol-is-written-down` prints `✘` with the first failing grep under it — on `main` today the baselines are: `^## Session protocol` 0, `schedule` in `sdlc-run/SKILL.md` 0, `standalone` in `HANDOFF.md` 0, `Suggested first prompt` 1, `CLAUDE.md "Lessons learned"` in `sdlc-review` 1, `log.md` and `gen_index` in `sdlc-intent` 0 and 0, `session sets` in `HANDOFF.md` 2.
2. R5 and R6, the two skill corrections, smallest first. Verifiable: the case's R5 and R6 greps go green while the rest stay red; `scripts/run_evals.sh --only skill-names-match-templates` and `--only skill-opens-drafts` still pass, since both read these files; a dry run of `/sdlc-intent`'s steps 1 and 4 in scratch (`work/_dry/log.md` written, `python3 scripts/gen_index.py --check` clean) then deleted before commit.
3. R7 both handoff lines, then R1 the protocol section, then R3 the prompt section, then the Task state. R7 goes first so R1's new section is not written beside a line known to be wrong (spec D2). The seed prompt is written for the state at the end of this item: what `.sdlc/active` names, where the ledger is, that the successor re-reads the approved artifacts (R10), and nothing that widens authority. Verifiable: `grep -cE "session sets" docs/sdlc/handoff/HANDOFF.md` = 0; `grep -c "Suggested first prompt"` = 0; the case's R1, R3 and R7 greps green; `scripts/checks/front-matter.sh` and `okf.sh` pass.
4. R2, R4 and R10 in `sdlc-run` step 7, plus the one sentence in "Stop and call the owner back". The act is written in the spec's order with its letters, and step (d) names the capability generically ("a scheduled routine or a session API your runtime provides") and the fallback in R4's words. Verifiable: `scripts/run_evals.sh --only session-protocol-is-written-down` passes in full; `grep -n "write \`.sdlc/active\` yourself" .claude/skills/sdlc-run/SKILL.md` still finds the Never line; `git diff origin/main -- .claude/skills/sdlc-run/SKILL.md` shows no line removed from `## Never`.
5. R8 as one budget: the pointer clause in `00-chain.md`, the re-flow in `30-conventions.md`, then `python3 scripts/gen_context_files.py`. Verifiable, in this order and before the commit: `grep -c HANDOFF CLAUDE.md GEMINI.md AGENTS.md` prints 1 each (0 today); `bash scripts/adopt.sh "$SCRATCH/a" && python3 scripts/gen_context_files.py --root "$SCRATCH/a"` then `grep -c HANDOFF "$SCRATCH/a/CLAUDE.md"` prints 1 (0 today) and `wc -l "$SCRATCH/a/CLAUDE.md"` prints 120 with no "over MAX_CONTEXT_LINES" — the count is the ceiling, the grep is the proof; `scripts/checks/context-drift.sh` passes; `python3 -m unittest scripts.test_adopt` green, which is what proves the intro paragraph was left alone.
6. R9 as a machine check, not a promise. Verifiable: `git diff origin/main --name-only | grep -E '^(scripts/|\.github/workflows/|\.sdlc/|\.claude/hooks/|\.gemini/|\.claude/settings\.json)'` prints nothing.
7. Regenerate (`gen_index.py`, `gen_context_files.py`), `git add -A`, `env -u GH_TOKEN -u GITHUB_TOKEN scripts/verify.sh`, commit, `check_artifact_chain.py --base origin/main` in strict mode against this file list, push. `plan-reviewer` and `security-reviewer` on a model other than the writer's; every finding verified against the head before it is applied, with the base-restore false positive on `.claude/` edits answered from `git show <head>:…` as `ci-budget` PR-B did. Mark ready once; ledger line `PR #<n> | draft -> in-review`; ask the owner to merge.
8. On the merge, this item's own step 7 runs the act it just wrote, for the first time, exactly as written: (a) `.sdlc/active` on `main` — this item is supervised, so it still names `session-chaining` until the owner retires it, and (a) fails honestly; the session says so in its final message and ends without scheduling anything. That is R4's path exercised live, and the first evidence for the closing ledger line. If the owner has already retired the item and pointed at the next one, (b)–(e) run instead, and the handoff-refresh pull request is the owner's click.

## Risks
- Risk: every chained cycle produces a locked-path pull request (the handoff refresh) that only the owner can merge, and `/sdlc-run` stops a queue for a locked path today → mitigation: step 4's sentence exempts exactly that pull request, on the grounds the spec's Design already states — the successor's correctness rests on `.sdlc/active` and its payload, not on the refresh landing — and the owner reads that exemption in this diff. What it costs: one click per cycle and a handoff that lags `main` until it lands. Option not taken: refreshing the handoff from CI next to `advance()`, which is a `scripts/` change R9 forbids and a spec amendment; if the click per cycle proves too much it is the next intent, not a deviation here.
- Risk: the R8 payment is taken from `00-chain.md`'s intro, which is the obvious three-line candidate → mitigation: named as forbidden in the file list; `adopt.sh:493-499` matches those lines byte-for-byte and skips its rewrite silently on any change, `scripts/adopt.sh` is out of scope (R9), and `test_adopt.py:485-488` is the check that catches it. Payment comes from `30-conventions.md` instead, and step 5 measures the adopter's render, not the repository's.
- Risk: the adopter render crosses `MAX_CONTEXT_LINES`, at which point `gen_context_files.py` writes nothing for the adopter → mitigation: net zero lines by construction (one in, one out), measured in step 5 before the commit; the repository's own files have slack (108, 117, 97), the adopter's has none.
- Risk: the automated reviewer reports the skill changes absent, because `pr-review.yml` restores `.claude/` and `CLAUDE.md` from the base branch (`docs/sdlc/spikes/pr-review-identity.md`) → mitigation: expected, answered from the head's content, never "fixed" by re-adding what is already there.
- Risk: the at-most-once cap and the committed-prompt convention are prose a runtime cannot be made to honour (spec C2) → mitigation: none new; the plan adds no enforcement because none is possible without a `scripts/` change, and says so rather than implying the eval's grep is a guard.
- Risk: the successor starts from a prompt the refresh pull request has not landed yet, or one the owner edited before merging → mitigation: R2(a) and R10 — the successor's first act is to re-read `.sdlc/active` and the item's approved artifacts; a stale prompt loses minutes, never correctness.
- Risk: the new eval case pins wording so tightly that the next honest edit to a skill turns it red → mitigation: the greps pin the spec's own words and shapes (`^## Session protocol`, `schedule`, `standalone`, `refreshed`, `knowledge/lessons/`, `log.md`, `gen_index.py`, the absence of `session sets`), not sentences; the `session sets` assertion is the only negative one and it is the shape the spec asked for.
- Risk: `sdlc-intent`'s new steps collide with `skill-names-match-templates` or `skill-opens-drafts`, which read the same file → mitigation: both cases run in step 2, before anything else changes.
- What this could break: nothing that executes. Every file here is read by a model or a human; the one machine consumer is the eval runner, and the case is written red first.
- Options considered and not taken: a CI-side spawner (spec "Not doing"); folding the refresh into the item's own pull request by predicting the next slug with `next_item.py` before the merge (breaks the spec's order, and the pointer is not yet moved when the prediction is made); an R8 line in `60-lessons.md` (the pointer is a rule about where the protocol lives, not a lesson); a `wc -l` clause as proof (it prints 120 on an unchanged tree — `knowledge/lessons/a-verifiable-command-fails-before-the-change.md`).

## Proof
- `scripts/verify.sh` green, with `env -u GH_TOKEN -u GITHUB_TOKEN` in this container; `python3 scripts/check_artifact_chain.py --base origin/main` ends `CHAIN: PASS`; `scripts/run_evals.sh` ends `0 fail` with one more case than today; `python3 scripts/check_okf.py` ends `0 warnings`
- Spec rows → tests, each with the value the check prints on `main` today so it can be seen to change: R1 → the case greps `^## Session protocol` and the three invariants in `HANDOFF.md` (0 today); R2 → the case greps `sdlc-run/SKILL.md` for the ordered act, `schedule` (0 today) and the at-most-once cap; R3 → `grep -c "Suggested first prompt" docs/sdlc/handoff/HANDOFF.md` = 0 (1 today), the case greps the renamed heading, `standalone` (0 today) and `refreshed`; R4 → the case greps the no-capability fallback sentence (absent today); R5 → `grep -c 'CLAUDE.md "Lessons learned"' .claude/skills/sdlc-review/SKILL.md` = 0 (1 today) and `knowledge/lessons/` present; R6 → the case greps `log.md` and `gen_index.py` in `sdlc-intent/SKILL.md` (0 and 0 today), plus step 2's dry item with `gen_index.py --check` clean; R7 → `grep -cE "session sets" docs/sdlc/handoff/HANDOFF.md` = 0 (2 today); R8 → step 5's adopter render: `grep -c HANDOFF "$SCRATCH/a/CLAUDE.md"` = 1 (0 today), `wc -l` = 120 as the ceiling, `grep -c HANDOFF CLAUDE.md GEMINI.md AGENTS.md` = 1 each, `context-drift.sh` and `test_adopt` green; R9 → step 6's `git diff --name-only` grep prints nothing; R10 → the case greps the "context, never authority" clause and the re-read instruction (absent today)
- Manual / browser / screenshot / eval: `scripts/run_evals.sh --only session-protocol-is-written-down` red before step 2 and green after step 4, both outputs pasted in the pull request; step 8's live run of the act on this item's own merge, quoted in the closing ledger line

## Rollback
- One commit, one revert: no state, no data, no migration. Reverting restores the three skills, the handoff, the two fragments and the regenerated files together; the eval case goes with them, so `run_evals.sh` stays green either way. A successor already scheduled from the reverted prompt re-reads `.sdlc/active` and the approved artifacts, which is R10 working as designed.

## Deviations log (append during implementation; same commit as the deviation)
- 
