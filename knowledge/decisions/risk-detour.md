---
type: decision
title: A delegated run detours around non-low work by a route record, and parks with two ledger words instead of stopping the queue
description: "Why the detour trigger is one command that calls the merge script's own locked-path matcher, why a detour is a revision record of kind detour whose reviewers judge the route rather than the trigger, why a park is a parked: ledger line on intent.md read by the queue and the index rather than a status word or a key, and why the park lands through the merge's own advance. Decided in work/risk-detour."
tags: [decision, delegated-mode, run-queue, sdlc-run, risk-class, revision-record, consensus, parking, detour]
resource: ../../work/risk-detour/
amends: delegated-mode.md
timestamp: 2026-09-15T01:10:00Z
---
# A delegated run detours around non-low work by a route record, and parks with two ledger words

> **Amends [`delegated-mode.md`](delegated-mode.md) decision 4** (a plan revision is a recorded last
> resort): the same consensus record now also answers a second question, whether a route exists that
> reaches the intent's outcome touching only low-risk surface, and a split record on that question
> parks the item rather than calling the owner back. Decisions 1, 2, 5 and 7 are untouched: no new
> status word, no agent-written key on the intent, no policy change, `approved` stays a human's word.

## Context

The owner, 2026-09-08 (`work/risk-detour/intent.md`): "I want `delegated` to only touch `low`, but
instead of stopping if it finds something else in its objective, instead of stop, make it check for
alternative solutions that reach the end only in `low`. To make this decision, I'd like as many agents
you think are necessary to discuss and find a consensus on the best course of action."

Measured the same day on `main` at `c0aa58c`: non-low work never entered delegated mode (five terminal
admission checks); mid-item the run's only rule was to stop the whole queue on a locked path
(`.claude/skills/sdlc-run/SKILL.md`, "Stop and call the owner back"); the one consensus record asked
whether a change was "the smallest one that clears the trigger", never whether a route stayed low; and
a parked item had nowhere to live: `STATUSES` is closed, a delegated pull request may not touch its
own `intent.md`, and an item parked before its spec looked "unstarted" to `scripts/next_item.py`, so
the next advance would have offered it again. Six open questions were answered by the owner as
decisions on 2026-09-08 and 2026-09-15.

## Decision

1. **The trigger is a line, not a feeling.** `scripts/check_detour.py` takes the paths a gate is about
   to plan (`--paths`, `--plan work/<slug>/plan.md`) or has changed (`--diff origin/main`) and calls
   `scripts/delegated_merge.py`'s `check_locked_paths` once per path with the same prefixes the merge
   uses (`PROTECTED_PATHS`, `RELEASE_GATED_PATHS`, the policy's `locked-paths`, `ALWAYS_LOCKED`, the
   item's `intent.md`). It ends `DETOUR: none` (exit 0) or `DETOUR: needed (<n>)` (exit 3), naming each
   locked path with its list and prefix. Only the label is computed locally; the matching rule is
   never re-spelled (`knowledge/lessons/one-path-spelling-in-guards.md`).
2. **A detour is a revision record with a route.** `docs/sdlc/templates/revision.md` gains
   `kind: detour` and a `## Route` section with five questions -- which outcome the route reaches,
   every path it touches and its list, why the class is honestly low, the remainder left for a human,
   what in spec and plan goes stale -- and the reviewers judge the route. The verdict words stay
   `revise` and `keep`, so `sign.py --revision` and `check_artifact_chain.py` read the record exactly
   as before; unanimous `revise` amends the artifact and re-signs it with the ledger note
   `revision <n>: detour: <route>`. At the intent-drafting gate nothing is re-signed: the route is
   drafted into the in-review intent's Proposed outcome and the owner's approval tap is the sign-off.
3. **Rounds, not a wider panel.** "As many agents as necessary" is rounds: a split record is closed, a
   changed route is a new record, and the second closed record at one gate parks the item. A second
   Claude model is a valid second reviewer when no other model is on the machine, named in its heading.
   `max-detours` as a policy key arrives with `work/standing-grant`.
4. **A park is two ledger words.** `parked:` and `resumed:` notes on `intent.md` ledger lines,
   `approved -> approved`, latest wins; no status word, no front-matter key, no record opened by the
   reader. `scripts/next_item.py` skips an item whose latest such line is `parked:`, and
   `scripts/gen_index.py` writes `parked` in the index's stage cell and a `Parked:` line on the item's
   index, through the one helper `next_item.parked_note`. The owner resumes with one web-editor line.
5. **The park lands through the merge's own advance.** The park is the item's own delegated pull
   request -- ledger, record, regenerated indexes, nothing else -- so `delegated_merge.py` merges it
   and its `advance()` moves `.sdlc/active` past the parked item to the next queued one, writing the
   two ledger lines it writes today, with no human commit between. A route the agent may build but the
   merge locks is finished to a ready pull request and parked `parked: ready PR #<n>; click needed
   (<path>)` from a second, ledger-only pull request; the click merges the code later by the human path.
6. **The remainder is a supervised intent.** `work/<slug>-supervised/intent.md` with `mode: supervised`,
   the record's risk class and `detour-of: <slug>`, on its own branch and pull request, never in the
   park pull request.

## Alternatives considered

| # | Alternative | Why not |
|---|---|---|
| D-a | A `parked` status word | `STATUSES` is closed on purpose; every reader of `status` would need re-auditing, and the chain check is a locked path |
| D-b | A `parked:` front-matter key on the intent | the intent carries the grant, and an agent may write no key on it; `protect-approvals.sh` guards the file for that reason |
| D-c | A separate `detour.md` template and record type | two record types for two locked readers (`sign.py`, the chain check); one record with a `kind` costs them nothing |
| D-d | Re-implementing the prefix rule in the check | a second spelling of a path guard is the mistake `one-path-spelling-in-guards.md` records; calling the matcher is cheaper and stays in step |
| D-e | Moving the pointer from the session on a park | a session never writes `.sdlc/active` (`run-queue.md`); the merge's advance already does, and a park pull request is an ordinary delegated merge |
| D-f | Stopping the queue on a click-locked route, as before | the owner asked for the queue to continue; a ready pull request plus a park line loses nothing and frees the pointer |

## Consequences and residuals

- **How far a run goes before it asks widens.** A parked item is a decision the owner reads after the
  fact, in the index and the ledger, rather than a stop they are called back for; this is the trade
  the owner asked for. The record and the remainder intent are what make it readable.
- **The park's advance is unobserved in production until the first delegated merge after this lands.**
  The workflow runs `main`'s `next_item.py`; a park merged before that would be re-offered by the old
  code. `scripts/test_park_advance.py` proves the new behaviour on the merge tests' own fixture.
- **`next_item.py` is read by the advance and is not on `locked-paths`.** The owner adds it to
  `.sdlc/delegation.yaml` after this item merges (intent Q5); until then a delegated pull request could
  change the queue rule under the same merge that reads it.
- **The check is advisory.** A skill that skips it meets the same paths at the merge, refused; the
  merge script is unchanged and still the gate.
- **This item's own pull request is the first click-locked park.** Every skill, template and rule path
  it touches is on `ALWAYS_LOCKED`; it ends `parked: ready PR #<n>; click needed (.claude/skills/sdlc-run/SKILL.md)`
  in its own ledger, and the queue behind it is empty, so the pointer stays until the owner retires it.

## Links

- `work/risk-detour/intent.md`, `work/risk-detour/spec.md`, `work/risk-detour/plan.md`
- `scripts/check_detour.py`, `scripts/next_item.py`, `scripts/gen_index.py`
- `docs/sdlc/templates/revision.md`, `.claude/skills/sdlc-run/SKILL.md`
- `knowledge/decisions/delegated-mode.md`, `knowledge/decisions/run-queue.md`
