---
type: sdlc/intent
id: self-check-false-reds
title: The self-check fails on an empty pointer and misreads approvals on a shallow clone
description: "check_artifact_chain.py ends verify.sh with FAIL when .sdlc/active is empty -- now the common case, because a delegated merge with an empty queue clears the pointer -- and on a shallow clone attributes every approval to the grafted boundary commit; the same advance also leaves work/<slug>/index.md and work/index.md stale, so main is red on three counts that are not the work."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: approved
author: Luis Siviero (repo owner), who named defect 1 as the next item in the 2026-09-15 ~03:10 Task state; drafted by Claude in the successor session opened for it
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by: luissiviero
approved-on: 2026-09-15
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: medium
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
# supersedes: previous intent id, if any
supersedes:
# detour-of: the slug of the parked item this intent is the remainder of, if any (mode stays supervised; the class is the record's)
detour-of:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: https://github.com/luissiviero/lifecycle-axis-/actions/runs/34922908400
tags: [chain-check, delegated-merge, advance, shallow-clone, gen-index, fix, defect-1]
timestamp: 2026-09-15T03:30:00Z
---
# Intent: the self-check fails on an empty pointer and misreads approvals on a shallow clone

## Problem
Three separate faults make `scripts/verify.sh` end `VERIFY: FAIL` for reasons that are not the work being
checked. All three were live on `main` in the window `4eb8383`..`e8ec522` on 2026-09-15, and every pull
request opened in that window was red on them. Each is reproduced below from that window.

**(a) An empty `.sdlc/active` is a failure, and it is now the common case.** `scripts/check_artifact_chain.py:528`
prints `FAIL: no active work item (.sdlc/active is empty; pass --slug or set it)` and exits 1 before any
chain is read. The comment there calls it "a setup mistake rather than a broken chain"
(`work/delegated-mode` R-6) — but it is no longer a mistake. `advance()` clears the pointer whenever the
queue is empty (`scripts/delegated_merge.py:1144-1146`; "An empty queue clears the pointer, which is a
valid state every reader already handles" — this reader does not), and the first delegated merge to do it
in production was #100 at 02:53 UTC, which wrote `ADVANCE: .sdlc/active -> (empty queue)` and then
`4eb8383`. So every delegated merge that empties the queue turns `main` red until a tap puts a slug back.
Reproduced at `4eb8383`:

    $ cat .sdlc/active            # empty
    $ python3 scripts/check_artifact_chain.py --base HEAD
      FAIL: no active work item (.sdlc/active is empty; pass --slug or set it)
    CHAIN: FAIL

Today this is worked around by the retire tap's `next` input: `.sdlc/active` currently names `ci-budget`
purely so `verify.sh` has a slug, which is why the 03:10 Task state calls it "a placeholder, not an item
to work".

**(b) On a shallow clone the approval is attributed to the grafted boundary commit.** Both author checks
find their commit with `git log -n1 -G ... -- <artifact>`: `check_artifact_chain.py:833` for
`^status: {status}$` and `:386` for `^mode: delegated$`. On a shallow clone `git log` stops at the graft,
and the boundary commit's diff appears to add the whole file, so the boundary commit matches `-G` and is
read as the approver. It then fails the `is_agent_identity` test at `:885` whenever that commit happens to
be an agent's. Reproduced at the same `4eb8383` — the only difference between the two runs is clone depth:

    # shallow (depth 1), boundary 4eb8383 github-actions[bot]
    $ python3 scripts/check_artifact_chain.py --base HEAD --slug ci-budget
      FAIL: work/ci-budget/intent.md: the commit that set status: approved is authored by an agent
            identity (github-actions[bot] <41898282+github-actions[bot]@...>); a human must set it and commit
      ... the same for spec.md and plan.md
    CHAIN: FAIL

    # full clone, same commit
    $ python3 scripts/check_artifact_chain.py --base HEAD --slug ci-budget
    CHAIN: PASS

The three real approval commits are `0e9d160`, `4a8fb4f` and `104c27d`, all authored by `luissiviero`; the
shallow run collapses all three onto one boundary commit. The failure is a property of the clone, not of
`main`. Note the graft can equally hide a genuine fault: on `5bf9573` the boundary is a human-authored
merge commit, so the same misattribution silently *passes* all three artifacts. The check is reporting on
the boundary, not on the approval, in both directions.

This is why "deepen the clone first" is resume step 8 of the handoff: a fresh remote container clones
shallow, and every session has to remember `git fetch --unshallow origin` before it can trust the check.
CI is unaffected — `sdlc-gate.yml:46` checks out with `fetch-depth: 0` — so the fault is invisible where
it is watched and load-bearing where it is not.

**(c) The same advance leaves both indexes stale.** `advance()` commits exactly `.sdlc/active` and the
ledger lines it appended (the `written` allowlist, `delegated_merge.py:1146-1164`, enforced at `:1169`,
which refuses any other staged path). It never regenerates, and `delegated_merge.py` does not import
`gen_index` at all. But the ledger line it appends is in the item's index (`Last gate:`) and its row in
`work/index.md`, so both drift the moment it commits. Reproduced at `4eb8383`:

    $ python3 scripts/gen_index.py --check
    work/parked-marker-on-retired/index.md: drifted
    work/index.md: drifted
    INDEX: 2 file(s) drifted

The 03:00 Task state recorded this as "a first occurrence, noted here rather than as a lesson"; the 03:10
section confirms both effects are now observed in production and that the retire tap
(`work/approve-tap-regenerates-index`) heals both — which is the point. **One tap heals what an unattended
job dirtied, so the repository's green state depends on a human being asked for a click.** The owner's
words in the 03:10 section: defect 1's fix "would let the advance regenerate what it dirties and note an
empty pointer instead of failing, retiring the placeholder `next` the retire tap needs today."

The 03:10 Task state folds (c) in here "for the owner to accept or split" — see open question 3.

## Proposed outcome
- **An empty pointer is a note, not a failure, where nothing needs proving.** Observable: at `4eb8383`
  (or any tree whose `.sdlc/active` is empty), `python3 scripts/check_artifact_chain.py --base HEAD` ends
  `CHAIN: PASS` with a `note:` naming the empty pointer, and exits 0. An explicit `--slug` naming an item
  that does not exist still FAILs. Strict mode — a diff that touches paths outside a work item — still
  FAILs on an empty pointer, because that is exactly where an approved chain must be proven (open
  question 1).
- **A shallow clone never attributes an approval to the graft.** Observable: the shallow and full runs
  above agree. On a shallow clone where the `-G` match is the grafted boundary commit, the check emits a
  `note:` that history is shallow and the author check was skipped, and does not report an approver it
  cannot see. On a full clone the reported commit is unchanged (`0e9d160`, `4a8fb4f`, `104c27d` for
  `ci-budget`). The check still mutates nothing — it must not fetch (open question 2).
- **An advance leaves no drift behind.** Observable: after a delegated merge that runs `advance()`,
  `python3 scripts/gen_index.py --check` on the resulting commit ends `INDEX: up to date`. The advance
  commit's file list grows by exactly the regenerated indexes and by nothing else — the allowlist at
  `delegated_merge.py:1169` keeps refusing every path outside it (open question 4).
- **Regression tests that are red on today's code**, one per fault, committed red before the fix
  (`kind: fix`). The shallow case needs a real shallow fixture clone, not a mock, since the fault is in
  what `git log` does at a graft.
- **The placeholder goes away.** Observable: with (a) fixed, a retire tap with no `next` leaves
  `.sdlc/active` empty and `main` stays green, so `ci-budget` need not sit in the pointer to keep the
  check quiet. A consequence to confirm, not a separate requirement.
- All green on the fix: `VERIFY: PASS`, `CHAIN: PASS`, `EVALS: 0 fail`, `OKF: 0 warnings`,
  `INDEX: up to date`.

## Affected users and systems
- Users: the owner, who is asked for a healing tap today and reads `VERIFY: FAIL` on pull requests that
  contain nothing wrong; every session, which cannot tell a real chain break from a shallow clone or an
  empty queue without deepening the clone by hand first (resume step 8).
- Services / repos / data: `scripts/check_artifact_chain.py` (faults a and b — both `-G` call sites, `:386`
  and `:833`, and the early exit at `:528`); `scripts/delegated_merge.py` (fault c — `advance()` and its
  `written` allowlist); `scripts/gen_index.py` (called by the advance, not changed);
  `scripts/next_item.py` and `scripts/verify.sh` (read, expected unchanged — named here because the detour
  check must see them); `.sdlc/active` (the value that triggers a, not edited by this item); new test
  modules under `scripts/`; `work/index.md` and `work/<slug>/index.md` (regenerated output).

## Constraints
- Must: **keep every check that actually catches an agent approving itself.** Fault (b)'s fix changes how
  the human-approval author is computed — the single check standing between an agent commit and an accepted
  approval. It may degrade to a `note` only when it can prove it is looking at a graft; it must never
  degrade to silence on a full clone, and a shallow clone must not become a way to skip the check
  deliberately. This is the sharpest edge in the item (open question 2).
- Must: `kind: fix` — each of the three regression tests is written and seen red before its fix.
- Must: keep `advance()`'s allowlist a closed list. It exists so an unattended `github-actions[bot]` job
  cannot push anything to `main` beyond what it declared; widening it to two generated paths must not turn
  it into an open list.
- Must: leave the shallow-clone workaround working. Resume step 8 and `git fetch --unshallow` stay correct;
  this item removes the need to remember it, not the ability.
- Must not: write `approved`, `delegated` or `superseded` anywhere; touch the four grant keys; sign any
  artifact; move `.sdlc/active` from a session; touch `work/ci-budget`, `work/standing-grant`, or the
  intents for defects 2 and 3.
- Must not: change `.sdlc/delegation.yaml`, `.sdlc/config.env`, the hooks, or any workflow's permissions.
- Out of scope: defect 2 (`EXEMPT` in the chain check lists `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`)
  and defect 3 (the chain check crashes on a token with no `gh` binary) — both keep their own intents, even
  though defect 3 is why every command in this session runs under `env -u GH_TOKEN -u GITHUB_TOKEN`. Also
  out of scope: the two unread red `delegated-merge` runs `34908767884` and `34909007398`; any other
  regeneration the merge workflow might owe.

## Risk class
**medium — and the honest reason is that two of the three fixes are inside the control plane's own
judgement.** Fault (b) rewrites how the check decides which commit approved an artifact, and a wrong
weakening there accepts an agent-authored approval as a human one; fault (c) widens what an unattended
`github-actions[bot]` job commits and pushes to `main` unreviewed. Blast radius is the approval gate and
the default branch. It is not high: there is no data sensitivity, no regulated surface and no external
consumer, the whole effect is observable in one `verify.sh` run, and `scripts/check_artifact_chain.py`,
`scripts/delegated_merge.py` and `scripts/next_item.py` are all on the policy's `locked-paths`, so nothing
here can reach `main` without the owner's click. It is not low, and that matters concretely: the policy
delegates `risk-classes: [low]` only, so `medium` is what keeps this item supervised, with a tap at every
gate — which is the right outcome for a change to the file that judges taps.

`python3 scripts/check_detour.py --paths <the paths above>` returns **`DETOUR: needed (5)`**:
`scripts/check_artifact_chain.py`, `scripts/delegated_merge.py` and `scripts/next_item.py` are locked by
`locked-paths`, and `scripts/verify.sh` and `.sdlc/active` by `PROTECTED_PATHS, ALWAYS_LOCKED`. **The code
lands by the owner's click, not by a delegated merge.** No detour record is filed at this gate: the detour
rule routes an item that is seeking a grant around the locked paths, and this intent seeks none
(`mode: supervised`). There is no low-only remainder to carve out either — the locked files *are* the
defect. See open question 5 if the owner reads that differently.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: what should an empty `.sdlc/active` do, exactly? A blanket exit 0 would let a genuinely unset pointer
  pass silently in the one mode where the chain must be proven.
  Proposed: split it by mode. In **in-progress** mode (the diff touches only one item's own paths, or is
  empty) an empty pointer with no `--slug` becomes `note: no active work item ...` and the run exits 0 —
  there is no item to check and nothing is claiming to be approved. In **strict** mode (the diff reaches
  outside the item) it stays `FAIL`, because a diff that changes code must name the approved chain
  authorising it. An explicit `--slug` that names nothing stays a FAIL in both.
  A: accepted as proposed (owner, 2026-09-15): split by mode -- a note and exit 0 in in-progress
     mode, `FAIL` kept in strict mode, and an explicit `--slug` that names nothing stays a `FAIL` in both.
- Q: how should the shallow clone be handled — degrade, or deepen?
  Proposed: **degrade, never deepen.** The check is read-only and runs in CI; making it fetch would give a
  verification step a network dependency and a way to mutate the repo it is judging. So: ask
  `git rev-parse --is-shallow-repository`, and when the commit `-G` returned is the grafted boundary
  (`.git/shallow` lists it), report `note: history is shallow at <sha>; the author check needs the real
  approval commit -- run git fetch --unshallow` and do not report an approver. A full clone behaves exactly
  as today. Deliberate abuse is not widened: CI is `fetch-depth: 0`, so a pull request cannot make the gate
  shallow, and the note is loud rather than silent.
  A: accepted as proposed (owner, 2026-09-15): degrade, never deepen. The check stays read-only and
     reports a loud note naming the graft; it never fetches.
- Q: keep fault (c) in this intent, or split it into its own item? The 03:10 Task state explicitly leaves
  this to you.
  Proposed: **keep it here.** All three are one symptom — `verify.sh` red for a reason that is not the work
  — and (a) and (c) are two effects of the same `advance()` call, first observed in the same commit. One
  spec with three requirements and three independent tests keeps the evidence together, and the item stays
  small. Split it only if you would rather land (a) and (b) first; say so and (c) becomes `advance-regenerates-index`.
  A: accepted as proposed (owner, 2026-09-15): keep all three faults in this one item. No split; the
     spec carries three requirements with three independent tests.
- Q: where should (c)'s regeneration live — inside `advance()`, or as a step in `delegated-merge.yml` after it?
  Proposed: **inside `advance()`**, importing `gen_index` and extending the `written` allowlist with exactly
  `work/<merged-slug>/index.md`, `work/<next-slug>/index.md` (when there is a next) and `work/index.md`.
  Keeping it in `advance()` keeps one commit and keeps the allowlist check at `:1169` as the safety
  property; a workflow step would need its own commit, its own push and its own race with the same
  not-forced push. Note `delegated-merge.yml:81` checks out with no `fetch-depth`, so the regeneration must
  read only the working tree — `gen_index.py` does.
  A: accepted as proposed (owner, 2026-09-15): inside `advance()`, extending the `written` allowlist
     by exactly the regenerated index paths, so the refusal at `delegated_merge.py:1169` stays the
     safety property.
- Q: do you read `DETOUR: needed` as requiring a detour record at this gate anyway?
  Proposed: **no.** The skill files a record for "an intent meant for a grant"; this one is supervised and
  its code will land by your click, so the detour has nothing to route around. If you would rather have the
  record on file regardless, say so and it is filed under `work/self-check-false-reds/revisions/` before the
  spec.
  A: accepted as proposed (owner, 2026-09-15): no detour record at this gate; the item is supervised
     and seeks no grant, so the detour has nothing to route around.
- Q: is `medium` the class you want, or would you rather this be `high`?
  Proposed: **medium**, for the reasons above — `high` would not change the route (both stay supervised and
  both need your tap at every gate), so the difference is only what the record says about blast radius, and
  `medium` is the honest reading for a change that cannot reach `main` unclicked.
  A: accepted as proposed (owner, 2026-09-15): `medium`. Confirmed in production by the approval tap
     itself -- the `mode: delegated` run (approve run #33, 03:42:33Z) failed at `approve.py:347`'s
     `policy.risk_ok()` and recorded nothing; the `supervised` run (#34) succeeded.
