---
type: sdlc/spec
id: advance-push
title: The advance fetches and fast-forwards onto the merged main before it writes, and lands
description: "delegated_merge.advance() fetches the default branch, refuses unless the fetched tip is the merge commit the API returned, fast-forwards the job's checkout onto it, and only then writes and pushes, so the advance commit's parent is the merge commit and the push is a fast-forward; a rejected push after that stays a note. Proven by a fixture whose bare remote moves between the checkout and the advance, as the merge API moves main."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: approved
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by: luissiviero
approved-on: 2026-09-14
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: e879ca8
prompt: "/sdlc-spec advance-push in session_01WSLuyVWcurCx6yPwNqxPPo, on the owner's direction after approve-tap-regenerates-index retired; from the approved supervised intent and its three owner-answered questions, a direct read of scripts/delegated_merge.py (run() from the merge call to advance(), advance() itself, _git), scripts/test_delegated_merge.py (the Advance fixture and its cases), .github/workflows/delegated-merge.yml (the single checkout of the default branch), .claude/hooks/protect-tests.sh (kind: fix locks existing test files, a new file stays writable), knowledge/decisions/run-queue.md, and main's history (two delegated merges, no advance commit)"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/55
tags: [delegated-mode, run-queue, delegated-merge, active-pointer, fix]
timestamp: 2026-09-14T05:20:00Z
---
# Spec: the advance fetches and fast-forwards onto the merged main before it writes

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | **The advance runs on the merged `main`.** After the merge API call succeeds, `advance()` fetches the checkout's branch from `origin` and fast-forwards the checkout onto the fetched tip before the dirty-tree check and before any write. The advance commit's parent is therefore the merge commit, the push is a fast-forward, and the ledger note's `merged as <sha>` names the merge commit, not the pre-merge `main`. | 1 (the advance commit's parent is the merge commit; the note names it) | `scripts/test_delegated_merge_advance.py::MovingRemote::test_the_advance_lands_on_top_of_the_merge` — the fixture's bare remote receives a commit after the checkout was taken (a second clone commits `Merge pull request #12 (delegated)` and pushes), then `advance(..., merge_sha=<that sha>)`: returns `next-item`; the remote's `main` tip is an advance commit whose first parent is that merge commit; the local `HEAD` equals the remote tip; `work/merged-item/log.md` on the remote carries `merged as <short merge sha>`. **Red on today's code**: the push is rejected as non-fast-forward, `advance` returns `None`, and the remote tip is still the merge commit. |
| R-2 | **A fetched tip that is not the merge commit is a note and no write.** When `merge_sha` is given and `FETCH_HEAD` differs from it (another push landed on `main` after the merge, or the fetch saw something else), `advance` writes one note naming both shas and returns `None` without touching the tree, the index, or `HEAD`. | 1 (exactness of the "merged as" record; the intent's second answer) | `MovingRemote::test_a_tip_that_is_not_the_merge_commit_is_a_note` — the remote moves by two commits; `advance` is given the first's sha: returns `None`; the note contains `not the merge commit`; `git status --porcelain` is empty; `HEAD` and `.sdlc/active` are unchanged; the remote tip is unchanged. Red today: today's code commits locally before its push fails, so `HEAD` moves. |
| R-3 | **A checkout that cannot fast-forward is a note and no write.** When `git merge --ff-only FETCH_HEAD` fails, `advance` writes one note and returns `None`; it never resets, rebases, or force-pushes (intent Must-not). | 1 and the intent's first answer | `MovingRemote::test_a_diverged_checkout_is_a_note_not_a_reset` — the local checkout gains a commit the remote does not have, and the remote gains one the checkout does not: returns `None`; the note contains `could not fast-forward`; the local `HEAD` is the local commit, unchanged; nothing staged; the remote tip unchanged. Red today: today's code writes, commits and fails the push, so `HEAD` moves. |
| R-4 | **The lost-update guard stays exactly as it is.** A push rejected after the fast-forward is still a note and never a retry or a force; a fetch that fails is the same note shape, so the existing rejected-push case passes unmodified. | 3 (the intent's third outcome) | Existing `scripts/test_delegated_merge.py::Advance::test_a_failed_push_leaves_the_run_reporting_the_merge` passes **unmodified** (its remote does not exist, so the fetch fails first; the note still contains `not pushed`). New `MovingRemote::test_a_push_rejected_after_the_fast_forward_is_a_note` — a `pre-receive` hook on the bare remote rejects every push and counts attempts: returns `None`; the note contains `not pushed`; the hook counted exactly one attempt; the remote tip is unchanged. |
| R-5 | **Nothing before the merge changes.** Every merge condition, the shallow checkout of the default branch, the never-check-out-the-head rule, the staged-path allowlist and the `ALWAYS_LOCKED` floor are untouched; the existing suite passes with no edit to any existing test file (the plan is `kind: fix`, so `protect-tests.sh` refuses such an edit anyway). | 4 | `git diff origin/main --name-only` on the pull request lists exactly `scripts/delegated_merge.py`, `scripts/test_delegated_merge_advance.py`, `scripts/test_delegated_merge_advance_review.py` (the review round's cases, plan deviation 3), `knowledge/decisions/run-queue.md` and this item's `work/advance-push/**`; `git diff origin/main --stat -- scripts/test_delegated_merge.py .github/workflows/delegated-merge.yml` prints nothing; `python3 scripts/run_tests.py` is green with the pre-existing `Advance`, `EndToEnd` and every other class unmodified. |
| R-6 | **The merge commit's sha reaches the advance.** `run()` keeps the merge endpoint's response and passes its `sha` to `advance(..., merge_sha=...)`; a response without a `sha` passes `None`, and `advance` then skips the comparison of R-2 but still fetches and fast-forwards (R-1). | 1 | `MovingRemote::test_run_passes_the_merge_sha_to_advance` — `run()` driven with the end-to-end fixture's fake API returning `{"sha": "<40 hex>", "merged": true}` from the merge endpoint and `advance` replaced by a recorder: the recorder was called once with `merge_sha` equal to that value. `MovingRemote::test_no_merge_sha_still_fast_forwards` — the moving-remote fixture with `merge_sha=None`: returns `next-item` and lands on the remote as in R-1. |
| R-7 | **The decision record says what shipped without.** `knowledge/decisions/run-queue.md` gains one sentence under its consequences: the advance shipped with a fixture whose remote never moved between the checkout and the push, which is the one case production never produces, and `advance-push` added that fixture. | intent Affected systems | `grep -c "advance-push" knowledge/decisions/run-queue.md` is at least 1; `python3 scripts/check_okf.py` ends `0 warnings`. |
| R-8 | **The loop is green.** `scripts/verify.sh` ends `VERIFY: PASS`, `python3 scripts/check_artifact_chain.py --base origin/main --slug advance-push` ends `CHAIN: PASS`, `scripts/run_evals.sh` ends `0 fail`, `python3 scripts/check_okf.py` ends `0 warnings`, both generators report up to date. | 4 | The last lines, pasted in the pull request; the new module's six cases counted, all six seen red before the code (the count was four when this spec was signed; the plan's step 1 observed six, and its deviations log says why). |

## Design
### Architecture / data flow
The change is confined to the write-back after a successful merge (`delegated_merge.py`, the `advance()`
call site in `run()` at `:1006-1013` on `main` and `advance()` itself at `:1055-1133`). Today `advance()`
runs: dirty check → pointer check → next item → write pointer and two ledger lines → commit → `git push
origin HEAD:<branch>`. The checkout is the workflow's single checkout of the default branch, taken before
the merge API call moved it, so the push is non-fast-forward on every real merge, and `:1126-1130`
swallows the rejection as a note whose comment blames a racing third party.

It becomes, in `advance()`, before the dirty check:

1. `branch = git rev-parse --abbrev-ref HEAD` (already computed for the push; moved up).
2. `git fetch origin <branch>`. On failure: the note `advance commit not pushed (fetch of origin/<branch>
   failed: <last stderr line>); the next merge will advance`, return `None`. The `not pushed` wording is
   what keeps the existing missing-remote case green without an edit (R-4).
3. `tip = git rev-parse FETCH_HEAD`. If `merge_sha` was given and `tip != merge_sha`: the note
   `origin/<branch> is at <tip[:12]>, not the merge commit <merge_sha[:12]>; not advancing`, return `None`.
4. `git merge --ff-only FETCH_HEAD`. On failure: the note `the checkout could not fast-forward to
   origin/<branch> (<last stderr line>); not advancing`, return `None`.
5. The existing flow, unchanged: pointer check, next item, writes, allowlist, commit, the non-forced
   push, the existing rejected-push note. The existing dirty check runs before step 1, not here: the
   second security pass on pull request 89 showed a dirty checkout being fast-forwarded and then told
   nothing was advanced (plan deviation 4).

And in `run()`: `merged = gh_api("PUT", .../merge, {...})`; `advance(root, out, slug, number, policy,
now=now, merge_sha=(merged or {}).get("sha"))`. The merge endpoint returns `{"sha", "merged", "message"}`
on success; `gh_api` already parses the body.

### Interfaces (APIs, events, schemas) — exact shapes
- `advance(root, out, merged_slug, number, policy, now=None, merge_sha=None) -> str | None`: one new
  keyword, default `None`; every existing caller and test keeps working.
- Three new notes on the run's stream, each one line, each ending the advance with `None` and no write:
  `note: advance commit not pushed (fetch of origin/<branch> failed: <err>); the next merge will advance`;
  `note: origin/<branch> is at <sha12>, not the merge commit <sha12>; not advancing`;
  `note: the checkout could not fast-forward to origin/<branch> (<err>); not advancing`;
  and, from the review round (plan deviation 3), `note: the checkout is detached, not on a branch; not
  advancing`. The fetch passes the branch after `--`, and a `merge_sha` that is not a 7-to-40 hex string
  is treated as absent at both ends.
- The existing `ADVANCE: .sdlc/active -> <slug>` line, the existing rejected-push note, the ledger line
  shapes and the commit subject are unchanged. The ledger's `merged as <sha>` now holds the short sha of
  `HEAD` after the fast-forward, which is the merge commit.
- No new flag, workflow input, environment variable, file, front-matter key or policy key.
- `scripts/test_delegated_merge_advance.py`: a new module, `class MovingRemote(unittest.TestCase)`, its
  own fixture built from the existing module's constants (`FIXTURE_POLICY`, `ADVANCE_INTENT`,
  `ADVANCE_LOG`, `_write`), imported as a module so the loader does not collect the existing classes
  twice. Six cases named in R-1 to R-4 and R-6.

### Data and migrations
None. No field, no schema, no classification (security-standards §4: n/a).

### Failure modes and how they surface
- **Fetch fails** (no network, a deleted branch, a missing remote): a note, nothing written, the job
  still reports the merge. The existing case pins the shape.
- **The tip is not the merge commit**: someone pushed to `main` in the seconds after the merge, or the
  merge response carried an unexpected sha. A note names both; nothing written; the next merge advances
  from a fresh checkout, as today's comment already promises.
- **Fast-forward fails**: the checkout diverged, which the workflow's fresh checkout never does. A note,
  nothing written, no reset (R-3).
- **Push rejected after the fast-forward**: another push landed between the fetch and the push. The
  existing note, no retry, no force (R-4).
- **A dirty tree**: the existing refusal, unchanged, reached before the fetch, so a dirty checkout is
  neither written nor moved (plan deviation 4).
- **`git merge --ff-only` on a shallow checkout**: `actions/checkout` fetches depth 1; `git fetch origin
  <branch>` deepens as needed, and a fast-forward needs only that the current `HEAD` be an ancestor of the
  fetched tip, which the merge commit's first parent guarantees (G-4).

**Security standards, rule by rule**:
1. Secrets — n/a: the push already uses the checkout's configured credential; nothing new is read.
2. Auth — n/a: no new endpoint; the merge conditions and their order are untouched (R-5).
3. Input — the only new inputs are `git` outputs (`FETCH_HEAD`'s sha, stderr's last line) and the API's
   `sha`, all compared or printed, never interpolated into a command; every git call is an argv list.
4. Data — n/a, no new field.
5. Dependencies — none.
6. Infra — no path under `RELEASE_GATED_PATHS`; the workflow is untouched.
7. Logging — the notes carry shas and a git error line; no personal data.
8. Agent hygiene — the writer is Fable; `/sdlc-review` runs `plan-reviewer` and `security-reviewer` on
   Opus, read-only.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: `scripts/delegated_merge.py` is on `.sdlc/delegation.yaml`'s `locked-paths`, so this item's pull
  request never merges on its own; the queue ends at it — policy: `.sdlc/delegation.yaml` — contradiction?
  no — owner: luissiviero — resolution: expected and chosen in the intent (supervised, first of three).
- C2: the plan is `kind: fix`, which locks every existing test file, and the intent names
  `scripts/test_delegated_merge.py` as where the regression cases go — policy: `.claude/hooks/protect-tests.sh`
  — contradiction? yes, resolved — owner: luissiviero — resolution: the hook's own comment says the failing
  reproduction "is a new file and stays writable"; the cases go in a new module that imports the existing
  fixture's constants. The existing module is not edited, which is also what R-5 requires.
- C3: the fast-forward makes the advance depend on the fetched tip equalling the API's sha; a `main` that
  receives any push within seconds of a delegated merge will not advance that time — policy: none —
  contradiction? no — owner: luissiviero — resolution: the intent's second answer chose exactly this; the
  next merge advances, and the note says why this one did not.

## Open questions carried from intent.md
- None. The owner answered all three on 2026-09-08: fetch then `--ff-only`, compare the tip to the merge
  commit before writing, supervised and first of the three items.

## Decisions (ADR-style: context → decision → consequences)
- D1: **Fetch and fast-forward the existing checkout; never re-checkout, reset or force.** Context: the
  intent's first answer; the workflow's checkout is main's and must stay so. Decision: `git fetch origin
  <branch>` then `git merge --ff-only FETCH_HEAD`, both failures a note. Consequence: the checkout ends at
  the merge commit or is left exactly where it was.
- D2: **Compare the fetched tip to the merge commit's sha before writing.** Context: the intent's second
  answer. Decision: the sha comes from the merge endpoint's response through a new `merge_sha` keyword;
  a mismatch is a note and no write; `None` skips the comparison so direct callers and the existing tests
  keep working. Consequence: the ledger's "merged as" is exact, and a push that lands on `main` in the
  same seconds costs one advance, never a wrong write.
- D3: **The fetch failure reuses the "not pushed" wording.** Context: the existing missing-remote case
  asserts `not pushed`, and `kind: fix` forbids editing it. Decision: the fetch-failure note begins
  `advance commit not pushed (fetch of ...)`. Consequence: the case passes unmodified and the wording is
  still true, since the advance was indeed not pushed.
- D4: **The regression cases live in a new module built from the existing fixture's constants.** Context:
  C2. Decision: `scripts/test_delegated_merge_advance.py` imports `test_delegated_merge` as a module and
  reuses its constants and `_write`, with its own `setUp` that also opens a second clone to move the
  remote. Consequence: no existing test file changes; the loader collects the new class once.

## Gotchas found while reading the codebase
- G-1: the existing fixture's remote is written once in `setUp` and never moves (`test_delegated_merge.py:1457-1474`);
  every `Advance` case therefore exercises the one case production never produces. The intent says so;
  this spec adds the fixture that moves.
- G-2: `advance()` already computes `branch` for the push (`:1122`); the fetch needs the same name, so it
  moves to the top. `actions/checkout` with `ref: <default_branch>` leaves `HEAD` on that branch, so
  `rev-parse --abbrev-ref HEAD` is the branch name, not `HEAD`.
- G-3: `gh_api` returns the parsed JSON body; the merge endpoint's success body carries `sha`, `merged`
  and `message`. The current call discards it (`:979`), which is why the sha never reached the advance.
- G-4: a fast-forward from the pre-merge checkout is always possible in production: GitHub's merge commit
  has the base tip at merge time as its first parent, and the job's `HEAD` is that tip or an ancestor of
  it. Only a local commit on the checkout breaks it, and the workflow never makes one before the advance.
- G-5: `run()` wraps `advance()` in `except (OSError, ValueError, MergeError)`; `_git(check=True)` raises
  `MergeError`, so any git call left checked inside the new steps would become a "could not advance" note
  rather than a crash. The three new steps use `check=False` and write their own, more specific notes.
- G-6: `protect-tests.sh` locks only *existing* test files under `kind: fix` and says so in its header;
  a new module is the designed escape, not a loophole.

## Not doing
- Any change to `.github/workflows/delegated-merge.yml`, the merge conditions, the checkout ref, or the
  staged-path allowlist (intent Must-not).
- A retry or a force on a rejected push (intent Must-not; `work/run-queue` R-3).
- Editing `scripts/test_delegated_merge.py` (C2, R-5).
- The standing grant, the risk detour, or the `run-queue` ledger line the intent scopes out.
- Fixing the wider queue conditions the handoff records: that a supervised item like this one is never
  advanced *into*, and that a retired delegated item's artifacts fail the chain check. Both are separate
  intents.
