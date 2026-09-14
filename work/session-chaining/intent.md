---
type: sdlc/intent
id: session-chaining
title: "The kit never says who manages session context, so the owner has been doing it by hand"
description: "One session per work item is the protocol the owner chose, but nothing in the kit writes it down or acts on it: sdlc-run's advance step does not open the next session, the handoff carries no protocol, and two skills give instructions that are wrong or incomplete against the repository as it stands."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: superseded
author: Luis Siviero (repo owner), asking during the ci-budget execution session of 2026-09-11; the three defects come from the mock walk of 2026-09-11 and were re-verified against main at 6cd63b1
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by: luissiviero
approved-on: 2026-09-13
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: low
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
# supersedes: previous intent id, if any
supersedes:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: work/ci-budget/log.md (the ci-budget session where the question was asked and answered)
tags: [sdlc, skills, handoff, context, session]
timestamp: 2026-09-13T16:30:00Z
---
# Intent: The kit never says who manages session context, so the owner has been doing it by hand

## Problem
The originator, mid-way through executing `ci-budget`, asked:

> "before moving on with execution, how will the project handle the amount of context that's created
> during production? I mean, will it create multiple sessions, clear the ones already documented, of
> what other alternative? **so far I've been the one managing that**"

and, having been given the options, chose one and asked the question the kit could not answer:

> "**Answer when will it start opening new sessions by it self.** I choose 'one session power work
> item', as you recommended"

The kit has no answer today. Nothing in it names a session protocol, so the decision lives only in
the owner's head and in a chat transcript that ends when the session does. Three concrete gaps, each
re-verified against `main` at `6cd63b1`:

1. **`sdlc-run` step 7 ("Advance") never opens the next session.** It tells the session to re-read
   `.sdlc/active` from `main` and "go to step 1 for that item" — inside the same session, whose
   context is exactly what the owner is worried about. It also says "If the session ends mid-queue,
   nothing is lost", which is true of the git state and silent about who starts the next one. In
   practice the owner starts it.
2. **`docs/sdlc/handoff/HANDOFF.md` carries no protocol.** It has a "Suggested first prompt", which
   is a template for a human to paste, not a rule the kit follows.
3. **Two skills give instructions that are wrong against this repository.**
   - `.claude/skills/sdlc-review/SKILL.md:20` says to "add a line to CLAUDE.md 'Lessons learned' in
     this PR". `CLAUDE.md` has no "Lessons learned" section — and more seriously, `CLAUDE.md` is a
     **generated** file: `gen_context_files.py` renders it from `docs/sdlc/rules/*`, so an agent
     following this instruction edits a file whose change `scripts/checks/context-drift.sh` then
     fails. The real convention is a file in `knowledge/lessons/` plus a pointer line in
     `docs/sdlc/rules/60-lessons.md`.
   - `.claude/skills/sdlc-intent/SKILL.md` never mentions `work/<slug>/log.md` or
     `scripts/gen_index.py` (0 occurrences of either). An item created by following the skill
     literally has no ledger, and `work/index.md` drifts, which `scripts/checks/index-drift.sh`
     fails. Every item so far has had a ledger only because the session knew to write one.

Who is affected: the owner, who is doing by hand what the kit should do; and any adopter, who gets
the same three gaps with none of the tacit knowledge that has been covering them here.

## Proposed outcome
The protocol is written down where the kit acts on it, and the two skills stop giving instructions
that the repository's own checks refuse.

Observable:
- A named session protocol exists in `docs/sdlc/handoff/HANDOFF.md` and in `sdlc-run`, saying what a
  session owns (one work item), what it leaves behind (git: `.sdlc/active`, the item's `log.md`, the
  handoff), and what starts the next one.
- An eval case, sibling to the five `skill-*` cases, fails against `main` today and passes after:
  `sdlc-review` no longer names a `CLAUDE.md` section to edit, and `sdlc-intent` names both `log.md`
  and `gen_index.py`.
- Following `/sdlc-intent` literally, end to end, produces an item with a `log.md` and a clean
  `python3 scripts/gen_index.py --check`; today it produces neither.
- Whatever answers "when does it open the next session by itself" is stated as a mechanism with a
  trigger, not as advice — or, if no mechanism in this kit can do it, that is written down as the
  answer rather than left open.

## Affected users and systems
- Users: the repo owner; any adopter running `scripts/adopt.sh`; every future agent session.
- Services / repos / data: `.claude/skills/sdlc-run`, `sdlc-review`, `sdlc-intent`;
  `docs/sdlc/handoff/HANDOFF.md`; `evals/cases/`; possibly `docs/sdlc/rules/` if the protocol earns
  a rendered line, which is paid for at the adopter's render
  (`knowledge/lessons/adopter-context-file-sits-at-the-cap.md`).

## Constraints
- Must: keep every rendered context file at or under `MAX_CONTEXT_LINES`, measured on the adopter's
  render, which sits at exactly the cap.
- Must: leave the durable state in git. A session is disposable; `.sdlc/active`, the item's `log.md`
  and the handoff are what survive.
- Must not: move `.sdlc/active` from an agent session, or otherwise let a session promote itself to
  the next item without the human act the kit already requires.
- Must not: widen what an agent may do. This item is about who does the work and what they are told,
  not about new authority.
- Out of scope: the other four fix-queue items from the mock walk (`chain-check-robustness`,
  `adopt-ships-what-it-references`, `index-after-approval`, `pointer-contradiction`); the
  `ci-budget` acceptance run; any change to the delegation policy.

## Risk class
**low.** The blast radius is instructions and documentation: skills, the handoff, an eval case. No
`scripts/` change is anticipated, no `PROTECTED_PATHS` path, no data, no credential, no release
path. The failure mode of getting it wrong is an agent following bad advice, which is the failure
mode that already exists today. If the spec concludes that "open the next session by itself" needs a
script or a scheduled trigger, that is a material change of shape and the risk class is re-examined
at the spec, not assumed here.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: "Opens the next session by itself" — do you want a real mechanism (a scheduled routine, or an
  API call that starts a fresh session on merge), or is the honest answer "the kit cannot start a
  session; here is the one prompt you paste, and here is where the state lives so it costs you
  nothing to do"? The first is a genuinely new capability and would likely raise the risk class; the
  second is documentation and stays low.
  A:
- Q: `pointer-contradiction` (fix-queue item 5 — the handoff and `sdlc-run` say opposite things
  about `.sdlc/active`) touches the same two files as this item. Fold it in here, or keep it
  separate as the queue has it?
  A:
- Q: Should the protocol earn a rendered line in `docs/sdlc/rules/`, so every model sees it in
  `CLAUDE.md`/`GEMINI.md`/`AGENTS.md`? It would have to be paid for by re-flowing prose elsewhere,
  as `ci-budget` did — the adopter's render has zero slack.
  A:
