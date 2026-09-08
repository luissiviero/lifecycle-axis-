---
type: sdlc/intent
id: run-queue-followups
title: Close the three leftovers the first delegated queue surfaced, so the next queue starts on a true printout and two repeated mistakes stop repeating
description: "The queue the sdlc-run skill prints before a run is not the order it works (the pointer item goes first, the print says otherwise); the adopter's context-file cap and the chain check's empty diff on staged-but-uncommitted work each bit twice in one day with no lesson filed. One small item: one skill line, two lesson files, their pointer lines."
stage: plan
status: in-review
author: Luis Siviero (repo owner), from the handoff that opened this session; drafted by Claude from that handoff and the ledgers of work/retire-active-pointer and work/run-queue
approved-by:
approved-on:
risk-class: low
mode: supervised
delegated-by:
delegated-on:
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/55
tags: [sdlc-run, run-queue, active-pointer, lessons, context-files, check-artifact-chain, followups]
timestamp: 2026-09-08T18:00:00Z
---
# Intent: close the three leftovers the first delegated queue surfaced

## Problem
Three things left over from `work/run-queue` (pull request 55), in the words of the handoff the owner
opened this session with:

> Known follow-ups, not yet items: skill should print [pointer]+rest; adopter CLAUDE.md cap and
> staged-but-uncommitted chain diffs both bit twice -> lessons.

And from the session that shipped pull request 55, closing its reply:

> The last tap runs first. `/sdlc-run` must start at whatever `.sdlc/active` names, and every grant
> tap repoints it — so if you grant A, then B, then C, the pointer lands on C. The run does C, then
> A, then B (the rest in date/slug order), while `next_item.py --list` prints A, B, C. Nothing
> breaks, but the printed order lies about the first item.

> Two more things met twice this session that rule 7 says should become lessons, and haven't yet:
> the adopter's CLAUDE.md sitting at exactly 120/120 (every rules-fragment line added bites there,
> not here), and the chain check silently diffing an empty set when work is staged but
> uncommitted. Both are a five-minute docs item for the new session to open.

What the repository does today, measured on 2026-09-08:

1. **The printed queue is not the run order.** `.claude/skills/sdlc-run/SKILL.md` ("The queue")
   tells the run to print `python3 scripts/next_item.py --list` — earliest `delegated-on` first,
   ties by slug — "so the owner knows what will happen before they leave". But the precondition
   above it makes the run start at the item `.sdlc/active` names, and `approve.yml:115-117` points
   `.sdlc/active` at every item it grants (`--delegate --activate`). So the pointer names the
   *last* tap, the run opens that item first, and the printout puts it wherever its date and slug
   fall. `next_item.py` itself is right about the rest: `delegated_merge.py` advances to its first
   entry after every merge. Only the first line of the printout is wrong, and only that line is
   what the owner reads before leaving. The workaround in the handoff — "tap the item you want
   first, last" — is a rule the owner has to remember instead of a printout they can trust.
2. **The adopter's context-file cap bit twice, no lesson.** `MAX_CONTEXT_LINES=120`
   (`.sdlc/config.env`) is enforced by `scripts/gen_context_files.py:192-201` on every rendered
   context file. This repository's `CLAUDE.md` renders at 108 lines; the adopter's, seeded by
   `scripts/adopt.sh` with project sections above the generated block, sits at the cap, so every
   line added to a fragment under `docs/sdlc/rules/` (a lesson pointer under rule 7, a two-line
   convention) fails the adopter render and not this one. Ledger evidence, both on the same day:
   `work/retire-active-pointer/log.md` (15:05Z: "the two-line rules addition put the adopter's
   CLAUDE.md at 121 of 120, so the paragraph was re-flowed to net zero lines") and
   `work/run-queue/log.md` (17:22Z: "one paragraph re-flowed six lines to five because the new
   lesson pointer put the adopter's CLAUDE.md at 121 of 120"). Rule 7 says a mistake made twice
   becomes a file in `knowledge/lessons/` and a pointer line in `docs/sdlc/rules/60-lessons.md`,
   in the same pull request; neither exists.
3. **The chain check diffs an empty set on staged, uncommitted work, twice, no lesson.**
   `scripts/check_artifact_chain.py:526` lists changed files with `git diff --name-only
   <base>...HEAD`, which sees commits only. Run before the commit, with the work staged, the diff
   is empty, and an empty diff is by design the self-check that "validates what exists"
   (`check_artifact_chain.py:540`): the in-progress mode, a pass on the wrong question. First
   time: `work/batch-b-followups/plan.md:77` ("the local chain check ran in the same command as the
   commit, before the files were staged, so it read a diff that did not yet include them. Run
   `check_artifact_chain.py` after committing, never before") — recorded in one plan's deviation
   log, where no later session reads it. Second time: the session that shipped pull request 55,
   per the handoff. The 2026-09-08 fix for the *unknown base ref* case (retire-active-pointer R-4,
   `check_artifact_chain.py:527-535`) shows the shape of a check that says something instead of
   passing silently; the staged case has no such line.

## Proposed outcome
- The queue the skill prints is the order the run works. Observable: with the pointer naming C and
  A, B granted earlier, the printout reads `C`, `A`, `B`, in that order, C marked as the pointer
  item; `next_item.py --list` alone is no longer what the skill tells the run to print, or the
  script gains a mode that prints the pointer first — the spec chooses, and the skill text says
  which. The handoff's "tap the item you want first, last" rule is no longer needed and is not
  written anywhere as advice.
- Two lesson files under `knowledge/lessons/`, each with its pointer line in
  `docs/sdlc/rules/60-lessons.md`, per rule 7 and the naming in `knowledge/lessons/index.md`:
  one for the adopter's context-file cap (the rule: measure the adopter render, not this repo's,
  before adding a fragment line — the exact command belongs in the lesson), one for the chain
  check's empty diff on staged-but-uncommitted work (the rule: commit first, then check; a `CHAIN:
  PASS` printed before the commit proved nothing about the commit). Observable: `python3
  scripts/check_okf.py` ends `0 warnings` with the two files counted; `knowledge/lessons/index.md`
  lists both; `CLAUDE.md`, `GEMINI.md` and `AGENTS.md` regenerate with the two pointer lines and
  every rendered file, including the adopter's under `scripts/adopt.sh`, stays at or under
  `MAX_CONTEXT_LINES` — the adopter test suite (`scripts/test_adopt.py`) is the oracle.
- Nothing else changes: `scripts/verify.sh` ends `VERIFY: PASS`, the chain check `CHAIN: PASS`,
  the evals `0 fail`; no script under the policy's `locked-paths` and no `PROTECTED_PATHS` entry
  is touched, so the item can merge without a click.

## Affected users and systems
- Users: the owner, reading the printout before leaving; any session running `/sdlc-run`; any
  session adding a rules fragment line or running the chain check locally.
- Services / repos / data: `.claude/skills/sdlc-run/SKILL.md` (the queue paragraph and step 7's
  re-read, prose only); possibly `scripts/next_item.py` and `scripts/test_next_item.py` if the
  pointer-first print lives in the script rather than the skill (under `PLAN_REQUIRED_PATHS`, not
  locked); `knowledge/lessons/` (two new files, `index.md`), `docs/sdlc/rules/60-lessons.md`, the
  three generated context files; `docs/sdlc/handoff/HANDOFF.md` only if the spec chooses to
  carry the local-check note (see the open question).

## Constraints
- Must: the printed order and the worked order come from the same rule, in one place, so they
  cannot drift again; whichever file holds it, the other refers to it.
- Must: each lesson names the two occurrences it comes from (ledger line or plan line, with the
  path) and states one rule an agent can follow before the mistake, not after.
- Must: every rendered context file, including a fresh adopter's, stays at or under
  `MAX_CONTEXT_LINES` after the two pointer lines land; if that needs a re-flow of another
  fragment, the re-flow is prose only, every rule kept, and the plan lists the file.
- Must not: touch `.sdlc/`, `.claude/hooks/`, `.github/workflows/`, `scripts/verify.sh`,
  `scripts/checks/`, or any path in `.sdlc/delegation.yaml`'s `locked-paths`
  (`scripts/check_artifact_chain.py` among them). If the staged-diff case deserves a check that
  says something instead of passing silently, this item writes the lesson and the spec names the
  change as a later item; the check itself is a locked path and the owner's click.
- Must not: change `next_item.py`'s queue order (earliest `delegated-on`, ties by slug) or the
  advance in `delegated_merge.py`; the rest of the queue is right, only the first line is wrong.
- Out of scope: reordering a queue from the phone; a grant tap that does not move the pointer;
  a third lesson for the `gh`-absent crash in `check_artifact_chain.py` (it is in two plans' risk
  sections; whether it is a lesson, a HANDOFF line or a code fix is the open question below).

## Risk class
low — a skill paragraph, two knowledge files, their pointer lines and a regenerated context block.
No gate, hook, policy or merge condition changes. Getting it wrong is a printout that is still
misleading or a lesson nobody reads, both visible and both a one-commit fix. The same value is in
the `risk-class` front-matter key above, and the policy delegates `low`, so the owner may grant
this item delegated and let the queue work it.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: does the pointer-first print live in the skill (one shell line: the pointer, then
  `next_item.py --list --exclude <pointer>`) or in `next_item.py` (a `--pointer-first` mode with a
  test)? Proposed: the script, so the skill has one command to print and the order has one test;
  the skill's step 7 already reads the pointer from `main`.
  A:
- Q: the local checks in a container with no `gh` need `GH_TOKEN= GITHUB_TOKEN=` in front of
  `scripts/verify.sh` and the chain check; it is in two plans' risk sections and not in
  `docs/sdlc/handoff/HANDOFF.md`. Carry it as one line in that handoff in this item, file it as a
  third lesson, or leave it for the item that fixes the crash? Proposed: the one handoff line
  here, since a new session hits it cold; the crash fix stays a later item because the check is a
  locked path.
  A:
- Q: for the staged-diff lesson, is the rule "commit, then check" enough, or should the lesson
  also ask for a `notes` line in the chain check when `git diff --cached` is non-empty (a locked
  path, so a later item)? Proposed: the rule now; the check line as the later item's intent, named
  in the lesson.
  A:
