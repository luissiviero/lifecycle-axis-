---
type: sdlc/intent
id: chain-check-without-gh
title: The chain check crashes on a token with no gh binary instead of taking the skipped path
description: "check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: superseded
author: Luis Siviero (repo owner), who named defect 3 as the next item in the 2026-09-17 ~22:45 Task state; drafted by Claude in the successor session opened for it
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by: luissiviero
approved-on: 2026-09-18
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
resource: https://github.com/luissiviero/lifecycle-axis-/blob/17004b4/docs/sdlc/handoff/HANDOFF.md
tags: [chain-check, dispatch-attestation, gh, remote-session, fix, defect-3]
timestamp: 2026-09-17T23:00:00Z
---
# Intent: the chain check crashes on a token with no gh binary instead of taking the skipped path

## Problem
`scripts/check_artifact_chain.py` verifies a tap-made approval against the Actions API: when the commit
that set `status: approved` (or `superseded`, for a retirement) carries an `Approved-Run:` trailer,
`verify_dispatch_run` (`:209`) asks `gh api repos/<repo>/actions/runs/<id>` whether that run really was a
successful `workflow_dispatch` of `approve.yml` by the named actor (`work/approve-by-dispatch` R-6). The
function has one guard for "cannot ask", at `:233`: with neither `GH_TOKEN` nor `GITHUB_TOKEN` set it
returns `None` with the note `no GH_TOKEN/GITHUB_TOKEN; the dispatch trailer was accepted on the author rule
alone`, and the caller at `:922` falls back to the git-author rule. Then `:237` runs
`subprocess.run(["gh", "api", ...])` with nothing guarding the binary. **The guard exists; it guards the
wrong condition** (the owner's words in the 22:45 Task state): a missing token and a missing binary are the
same inability to ask, and only one of them is handled.

Every remote session container this repository has run in is the unhandled case: the runtime sets both
`GH_TOKEN` and `GITHUB_TOKEN` and ships no `gh` (`which gh` prints nothing in this one). CI never sees it:
`sdlc-gate.yml:61-62` passes `GH_TOKEN` and runs on `ubuntu-latest`, which ships `gh`. So, as with defect 1's
shallow clone, the fault is invisible where it is watched and load-bearing where it is not.

Reproduced on `17004b4` (`main`, full clone of 646 commits, token set, no `gh`), against two items whose
approval commits carry the trailer; the only difference between each pair of runs is the environment:

    $ python3 scripts/check_artifact_chain.py --base HEAD --slug ci-budget
    Traceback (most recent call last):
      ...
      File ".../scripts/check_artifact_chain.py", line 237, in verify_dispatch_run
        r = subprocess.run(["gh", "api", f"repos/{repo}/actions/runs/{run_id}"],
      ...
    FileNotFoundError: [Errno 2] No such file or directory: 'gh'
    $ echo $?
    1

    $ env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/check_artifact_chain.py --base HEAD --slug ci-budget
    Artifact chain check for work item 'ci-budget' vs HEAD
      note: mode: in-progress -- ...
      note: work/ci-budget/intent.md: no GH_TOKEN/GITHUB_TOKEN; the dispatch trailer was accepted on the author rule alone
      note: work/ci-budget/spec.md: no GH_TOKEN/GITHUB_TOKEN; the dispatch trailer was accepted on the author rule alone
      note: work/ci-budget/plan.md: no GH_TOKEN/GITHUB_TOKEN; the dispatch trailer was accepted on the author rule alone
    CHAIN: PASS

`--slug self-check-false-reds` (retired on `17004b4`; the retire route at `:922` calls the same function with
`retired=True`) behaves identically: the same traceback with the token set, three notes and `CHAIN: PASS`
without it. Note what the crash is **not**: it is not a `FAIL:` line. The script's output "is meant to be
pasted into a PR comment" (its docstring); here it prints no `CHAIN:` line at all, only a Python stack, and
`verify.sh` reports the command as failed.

**Exactly when it bites, measured rather than assumed.** The call at `:237` is reached only when the item
being checked has an artifact whose approval or retirement commit carries a dispatch trailer. On `17004b4`
itself `.sdlc/active` is empty, so `scripts/verify.sh` with the token set ends `VERIFY: PASS (17004b4)` today,
one commit after the retire tap: the pointer names nothing and the check has nothing to attest. The 22:45
Task state's line that `verify.sh` itself ends `FileNotFoundError` was true of every commit from the first
tap (`ba4227f`, 2026-09-06, `approve-by-dispatch` R-6) until the retire tap at 22:30, when the pointer
named an item with tapped approvals, and it becomes true again the moment `.sdlc/active` names any such
item. For this item that is its own first gate: the intent tap writes the trailer, the owner points the
pointer at it, and every later `verify.sh` in the session that writes the spec crashes unless the token is
unset. The chain check on a pull request for any approved item, `--base origin/main --slug <slug>`, crashes
the same way with no pointer involved.

The workaround is old and hand-carried. `docs/sdlc/handoff/HANDOFF.md` "Hard facts" records it: "No `gh`
binary in the remote container: with `GH_TOKEN` set, the chain check's trailer verification raises
`FileNotFoundError` ... Locally, prefix `GH_TOKEN= GITHUB_TOKEN=` on `scripts/verify.sh` and on the chain
check; that takes the documented author-rule fallback. CI has `gh`." The 2026-09-08 section says "This bit
two sessions before it was written down", and every Task state since then, and every seed prompt, repeats
`env -u GH_TOKEN -u GITHUB_TOKEN` before the checks. By rule 7 a mistake made twice becomes a lesson; there is
no lesson file for this one because its fix is this item rather than another line to remember.

## Proposed outcome
- **A missing binary takes the path a missing token takes.** Observable: on `17004b4` with `GH_TOKEN` set
  and no `gh` on `PATH`, `python3 scripts/check_artifact_chain.py --base HEAD --slug ci-budget` ends
  `CHAIN: PASS`, exit 0, with one `note:` per attested artifact that names the missing binary (the shape of
  the no-token note, `... the dispatch trailer was accepted on the author rule alone`), and prints no
  traceback. The same for `--slug self-check-false-reds` (the retire route). `scripts/verify.sh` with the
  token set ends `VERIFY: PASS` on any commit whose active item carries a tapped approval.
- **Nothing else about the attestation changes.** With a token and a binary, every existing case keeps its
  answer: a matching run verifies, a run of another workflow, event, conclusion, actor, slug or artifact is
  `False` and a `FAIL`. Observable: `scripts/test_check_artifact_chain.py` (94 tests, `DispatchAttestation`
  among them) stays green unmodified.
- **The author rule still applies under the new note.** The skipped path returns `None`, exactly as the
  no-token path does, so the caller's `ok is None and is_agent_identity(...)` branch at `:932` still fails an
  agent-authored commit that carries a trailer nobody could verify (the security-pass finding on pull request
  51 that made the no-token path safe). Observable: a test with a token, no binary and an agent author ends
  `FAIL ... unverified dispatch trailer and is authored by an agent identity`.
- **A regression test that is red on today's code**, committed red before the fix (`kind: fix`), in a new
  module so the `protect-tests.sh` lock on existing test files is never in the way: token set, `PATH` with
  no `gh`, `verify_dispatch_run` returns `(None, <note naming gh>)` rather than raising. It should drive the
  real function through the real `subprocess` boundary, since the fault is what `subprocess.run` does when
  the executable is absent.
- **The workaround retires.** Observable: after the fix merges, the handoff's "Hard facts" line and the seed
  prompt's `env -u GH_TOKEN -u GITHUB_TOKEN` are history, and the next session runs `verify.sh` bare. A
  consequence to confirm at the handoff refresh, not a change this item's code pull request makes (open
  question 4).
- All green on the fix, with the token set and unset alike: `VERIFY: PASS`, `CHAIN: PASS`, `EVALS: 0 fail`,
  `OKF: 0 warnings`, `INDEX: up to date`.

## Affected users and systems
- Users: every agent session in a remote container, which today must remember to unset the token before
  every check and reads a traceback when it forgets; the owner, who reads `VERIFY: FAIL` and a Python
  stack, on pull requests and in handoffs, for a reason that is not the work.
- Services / repos / data: `scripts/check_artifact_chain.py` (`verify_dispatch_run`, `:233`-`:237`); a new
  test module under `scripts/` beside `scripts/test_check_artifact_chain.py` (read, must stay green
  unmodified); `scripts/verify.sh` (read, unchanged; it is how the crash reaches a session); `.github/workflows/sdlc-gate.yml`
  (read, unchanged; it is where the binary and the token both exist today); `docs/sdlc/handoff/HANDOFF.md`
  (the workaround lines, retired at the handoff refresh). Precedents for the answer inside this repository:
  `scripts/github_metrics.py:71-77` checks `shutil.which("gh")` and catches `FileNotFoundError` around the
  same call; `scripts/delegated_merge.py:180-182` catches `OSError` on it and raises a named error.

## Constraints
- Must: **keep the attestation exactly as strong wherever it can run.** With a binary and a token nothing
  changes. A binary that is present and answers non-zero (bad token, wrong repository, network down) stays
  a hard `False` and a `FAIL` unless the owner decides otherwise (open question 2): an oracle that spoke
  and refused is not an oracle that could not be asked.
- Must: `kind: fix` -- the regression test is written and seen red before the fix, in a new module.
- Must: the check stays read-only and offline. It never installs `gh`, never fetches, never retries with a
  different tool; the whole change is one more condition on the existing skipped path and one note text.
- Must: the note is loud and one line, the same shape and the same `None` return as the no-token note, so
  the caller's author-rule fallback is reached unchanged.
- Must not: write `approved`, `delegated` or `superseded` anywhere; touch the four grant keys; sign any
  artifact; move `.sdlc/active` from a session; merge anything.
- Must not: change `.sdlc/*`, the hooks, any workflow, `scripts/verify.sh`, `scripts/run_tests.py`; touch
  `work/standing-grant`, `work/ci-budget` (its own session runs on 2026-09-20 15:00 UTC), the two red
  `delegated-merge` runs `34908767884` and `34909007398`, or `EXEMPT` and the module docstring at
  `check_artifact_chain.py:23` (defect 2's ground).
- Out of scope: installing `gh` in the remote environment. That would hide the defect for one runtime and
  leave the check crashing on every other machine that has a token and no binary; the check must degrade
  by itself wherever `verify.sh` runs. Also out of scope: `scripts/approve_dispatch.py:198`'s own `gh api`
  call, which runs only inside `approve.yml` on a runner that has the binary; `delegated_merge.py`'s
  `gh_api`, which already names the error; defect 2.

## Risk class
**medium -- because the fix is one more condition on the path where the gate decides *not* to check.** The
skipped path is the one place a trailer is taken on the author rule alone, and a wrong test for "no binary"
(a `PATH` lookup that fails in CI, say) would make the gate take that path where the attestation is relied
on -- precisely the fail-open that `work/approve-by-dispatch` R-13 and its `SdlcGate` test exist to keep
loud. Blast radius is the approval gate on the default branch. It is not high: no data, no regulated
surface, no external consumer, the whole effect visible in one `verify.sh` run, and
`scripts/check_artifact_chain.py` is a `locked-paths` entry, so nothing here reaches `main` without the
owner's click. It is not low, and as with defect 1 that is load-bearing: the policy delegates
`risk-classes: [low]` only, so `medium` is what keeps a change to the gate script supervised, with a tap at
every gate. The honest counter-reading is in open question 3.

`python3 scripts/check_detour.py --paths <the paths above>` returns **`DETOUR: needed (2)`**:
`scripts/check_artifact_chain.py` is locked by `locked-paths`, `scripts/verify.sh` by
`PROTECTED_PATHS, ALWAYS_LOCKED`. The code lands by the owner's click, not by a delegated merge. No detour
record is filed at this gate: the detour rule routes an item that is seeking a grant around the locked paths,
and this intent seeks none (`mode: supervised`); there is no low-only remainder, the locked file *is* the
defect (the same reading the owner accepted on defect 1's question 5).

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: should a missing binary take the same skipped path a missing token takes?
  Proposed: **yes.** Neither can attest anything, and the caller already has the right fallback for "could
  not ask": `None`, one note, then the author rule. Detect it the way `scripts/github_metrics.py:71-77`
  already does, the repository's one existing spelling: `shutil.which("gh") is None` before the call, and
  `except FileNotFoundError` around it for a `PATH` that changes between the two. The note names the binary
  (`no gh binary on PATH; the dispatch trailer was accepted on the author rule alone`) so a reader can tell
  the two skipped causes apart in a pasted log.
  A: accepted as proposed (owner, 2026-09-18): a missing binary takes the no-token path -- None, one note naming gh, then the author rule; detected as github_metrics.py does, shutil.which plus except FileNotFoundError.
- Q: a binary that is present but fails -- non-zero exit on a bad token, the wrong repository, no network --
  stays a hard `False` today (`:239`). Keep that?
  Proposed: **keep it.** A refusal from an oracle that answered is evidence; treating it as "could not ask"
  would let a revoked token or a mis-set `GITHUB_REPOSITORY` pass on the author rule alone, and CI is where
  that path runs. The cost is that a workstation with `gh` installed and an expired token gets `CHAIN: FAIL`
  with the API's own message, and the remedy stays what it is today: unset the token, or fix it.
  A: accepted as proposed (owner, 2026-09-18): keep the hard False; a binary that answers non-zero is a FAIL with the API's own message.
- Q: is `medium` the class you want, or is this `low`?
  Proposed: **medium**, for the reason above. `low` is defensible -- one guard, one note, in-CI behaviour
  unchanged because the runner has the binary -- and would let you grant it, but a grant buys nothing here:
  the only file that changes is on `locked-paths`, so `/sdlc-run` would open a detour record at the first
  gate around a locked file that is the whole item, and the merge is your click either way. `medium`
  keeps the route straight: a tap at each gate, no detour machinery.
  A: accepted as proposed (owner, 2026-09-18): medium, supervised. The owner's preference is maximal autonomy, and low would still cost a risk-class edit, a grant tap, detour records at every gate and the same click on the locked file, so medium is the shorter route here; the autonomy lever is standing-grant.
- Q: where does the workaround retire -- in this item's code pull request, or in the handoff refresh the
  finishing session writes at `sdlc-run` step 7?
  Proposed: **the handoff refresh.** `docs/sdlc/handoff` is itself a `locked-paths` entry, the finishing
  session rewrites the Task state and the seed prompt regardless, and the "Hard facts" line becomes history
  in the same edit. The code pull request then touches exactly the script and the new test module, and the
  plan's file list stays two entries.
  A: accepted as proposed (owner, 2026-09-18): the workaround retires in the step-7 handoff refresh, not in this item's code pull request.
- Q: CI cannot be told apart from a workstation by the check today, and the fix makes a runner with no
  `gh` degrade to the author rule silently in the gate's log, as a runner with no token already would.
  Do you want the gate to fail closed on a missing binary?
  Proposed: **no environment sniffing in the check.** The note line is the same class of signal R-13
  relies on for the token, and `ubuntu-latest` ships `gh`. If you want a hard stop, it is one line the
  gate's job can run before the check -- `gh --version` -- in `.github/workflows/sdlc-gate.yml`, which is a
  workflow change only you make; named here so it is a decision and not an omission.
  A: accepted as proposed (owner, 2026-09-18): no environment sniffing in the check; the gh --version step in sdlc-gate.yml is noted as available and not taken.
