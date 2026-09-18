---
type: sdlc/spec
id: chain-check-without-gh
title: The chain check crashes on a token with no gh binary instead of taking the skipped path
description: "Seven requirements: a missing gh binary takes the no-token path (None, one note, then the author rule), the retire route included; a present binary that fails stays False; every existing attestation answer is unchanged; the check stays offline; all seen red-then-green in one new test module, with the locked file landing by the owner's click."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: delegated
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by: claude
approved-on: 2026-09-18
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: cffcedde592880a56c98fc7cfc2d8793c727c051
prompt: "/sdlc-run on the granted intent (2a3d2f8, mode delegated, risk-class low), step 1 /sdlc-spec, with the owner's five answers recorded in b4073a5 and 9adde1a"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/110
tags: [chain-check, dispatch-attestation, gh, remote-session, fix, defect-3]
timestamp: 2026-09-18T17:00:00Z
---
# Spec: the chain check crashes on a token with no gh binary instead of taking the skipped path

## Requirements (each maps to an intent outcome)

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R1 | With `GH_TOKEN` or `GITHUB_TOKEN` set and no `gh` executable on `PATH`, `verify_dispatch_run` returns `(None, "no gh binary on PATH; the dispatch trailer was accepted on the author rule alone")` and raises nothing; the check prints that text as one `note:` per attested artifact and ends `CHAIN: PASS` on a chain a human approved. | "A missing binary takes the path a missing token takes." | New module `scripts/test_chain_no_gh.py::MissingBinary::test_a_token_with_no_gh_is_a_note_not_a_crash`: the script run as a subprocess against a fixture whose approval commit carries the trailers, `GH_TOKEN=t`, `PATH` a directory holding only a `git` shim; ends `CHAIN: PASS`, stdout contains `no gh binary on PATH`, stderr contains no `Traceback`. Red today: exit 1, `FileNotFoundError: [Errno 2] No such file or directory: 'gh'`. |
| R2 | Under R1's conditions the caller's author rule still applies: an approval commit that carries the trailers but is authored by an agent identity ends `FAIL ... unverified dispatch trailer and is authored by an agent identity`. | "The author rule still applies under the new note." | `MissingBinary::test_a_token_with_no_gh_still_applies_the_author_rule_to_a_forged_trailer`: same fixture with `--author "Claude <noreply@anthropic.com>"`; ends `CHAIN: FAIL` on that message. Red today: the same traceback, before any verdict. |
| R3 | The retire route takes the same path: `verify_dispatch_run(..., retired=True)` with a token and no binary returns the R1 tuple. | "The same for `--slug self-check-false-reds` (the retire route)." | `MissingBinary::test_the_retire_route_takes_the_same_path`: the function called in-process with `retired=True`, `PATH` holding only the `git` shim; returns `(None, <the R1 note>)`. Red today: raises. |
| R4 | A binary that is present and exits non-zero still returns `(False, "run <id> could not be read from <repo>: ...")`; with a token and a binary that answers, every existing attestation case keeps its answer. | "Nothing else about the attestation changes." Owner's answer 2: "keep the hard False". | `MissingBinary::test_a_present_gh_that_fails_is_still_false`: a `gh` shim on `PATH` that prints to stderr and exits 1; the function returns `False` with `could not be read` in the detail. Green today and after (the pin). Plus `scripts/test_check_artifact_chain.py` (94 tests, `DispatchAttestation` and `ApprovalAuthor` among them) green unmodified, which `kind: fix` guarantees by refusing edits to it. |
| R5 | The check stays read-only and offline under R1 to R3: no network verb reaches `git`, nothing is installed or fetched, and the working tree is byte-identical before and after. | "The check stays read-only and offline." | `MissingBinary::test_the_check_never_reaches_for_the_network`: the `git` shim of `test_chain_shallow.py` records every argv; no `fetch`/`clone`/`pull`/`remote`/`push` appears and `git status --porcelain` is unchanged. Green today and after. |
| R6 | The fix is one `except` clause around the existing call and one note constant; no lookup runs before the call, so a test that stubs `subprocess.run` at the `["gh", "api"]` boundary on a machine with no `gh` still reaches its stub. | "Nothing else about the attestation changes." (gotcha 1 below) | `MissingBinary::test_a_stubbed_subprocess_still_reaches_the_call`: `subprocess.run` replaced by a fake returning a matching run, `PATH` holding only the `git` shim; `verify_dispatch_run` returns `True`. Green today; it is the mutation check against a `shutil.which` guard, which would turn it red on every machine without `gh`, this container and the 94-test suite's `DispatchAttestation._verify` included. |
| R7 | All green on the fix with the token set and unset alike. | "All green on the fix." | `scripts/verify.sh` ends `VERIFY: PASS (<sha>)` under both `env -u GH_TOKEN -u GITHUB_TOKEN` and the container's default environment (pointer naming this item, whose intent carries a tapped approval); `python3 scripts/check_artifact_chain.py --base origin/main --slug chain-check-without-gh` ends `CHAIN: PASS`; `scripts/run_evals.sh` ends `0 fail`; `python3 scripts/check_okf.py` ends `0 warnings`; `python3 scripts/gen_index.py --check` ends `INDEX: up to date`. |

R1 to R3 and R7 are the intent's first outcome with the owner's answers 1 and 2; R4 to R6 pin what must not move.

## Design

### Architecture / data flow

One function changes, `verify_dispatch_run` in `scripts/check_artifact_chain.py` (`:209`). Its order today:

1. no token → `(None, "no GH_TOKEN/GITHUB_TOKEN; ... author rule alone")` (`:232-233`, unchanged);
2. no repository slug → `(None, "cannot determine the repository; ...")` (`:234-236`, unchanged);
3. `subprocess.run(["gh", "api", f"repos/{repo}/actions/runs/{run_id}"], ...)` (`:237`);
4. non-zero → `(False, "run <id> could not be read ...")`; unparseable → `False`; the four field checks, the
   run-name bindings, `True` (`:239-284`, unchanged).

After the fix, step 3 becomes

```
try:
    r = subprocess.run(["gh", "api", f"repos/{repo}/actions/runs/{run_id}"],
                       capture_output=True, text=True, cwd=ROOT)
except FileNotFoundError:
    return None, NO_GH_NOTE
```

with `NO_GH_NOTE = "no gh binary on PATH; the dispatch trailer was accepted on the author rule alone"` a
module constant beside the other message shapes, so the test asserts the same string the code prints. The
return is exactly the no-token tuple's shape, so the caller at `:922-935` needs no edit: `ok is None` prints
the note and then applies `is_agent_identity` to the commit's author, which is R2. The retire route (`:922`,
`retired=(status == "superseded")`) calls the same function and therefore takes the same path, which is R3.

Nothing runs before the call to decide whether it can run: no `shutil.which`, no `PATH` scan (D3, gotcha 1).
The binary's absence is learned from the one place it is certain, the failed `exec`.

### Interfaces (APIs, events, schemas) — exact shapes

- `verify_dispatch_run(run_id, actor, slug=None, artifact=None, commit_sha=None, retired=False)`: signature
  unchanged. Return values unchanged in kind: `(True, detail)`, `(False, reason)`, `(None, reason)`. One new
  `(None, reason)` text: `no gh binary on PATH; the dispatch trailer was accepted on the author rule alone`.
- Printed line, unchanged shape: `  note: work/<slug>/<artifact>: no gh binary on PATH; the dispatch trailer
  was accepted on the author rule alone`.
- Exit codes unchanged: 0 on `CHAIN: PASS`, 1 on `CHAIN: FAIL`. The uncaught exception's exit 1 with no
  `CHAIN:` line disappears from the surface.
- `scripts/verify.sh`'s `VERIFY_CMDS` unchanged; `sdlc-gate.yml` unchanged.

### Data and migrations

None. No data field, no personal or regulated data (security-standards §4: n/a). The token is read from the
environment by name and never printed (§1: the note names neither the token's value nor its variable's value).

### Failure modes and how they surface

- Token set, no binary → R1's note, author rule, `CHAIN: PASS` or `FAIL` on that rule. Was: traceback.
- Token set, binary present, non-zero exit (revoked token, wrong repository, no network) → `False`, `FAIL` with
  the API's own stderr, unchanged (R4; owner's answer 2).
- Token set, binary present, exit 0 → the four field checks and the run-name bindings, unchanged.
- No token → the no-token note, unchanged, whether or not a binary exists.
- Binary present but not executable (`PermissionError`) → still raises, unchanged: it is not the measured
  fault and it is not "absent" (Not doing).
- CI runner without `gh` → the R1 note in the gate's log and the author rule, the same fail-open class as a
  runner without a token; the owner's answer 5 keeps environment sniffing out of the check and names the
  `gh --version` step in the workflow as the hard stop only the owner adds (C2).

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: `python3 scripts/check_detour.py --slug chain-check-without-gh --paths scripts/check_artifact_chain.py
  scripts/test_chain_no_gh.py` ends `DETOUR: needed (1)`: `scripts/check_artifact_chain.py: locked by
  locked-paths`. The test module is not locked. — policy: `.sdlc/delegation.yaml` `locked-paths`;
  `.claude/skills/sdlc-run/SKILL.md` "The detour rule" step 5 — contradiction? no: the route the agent may
  build but the merge locks is finished to a ready pull request and parked `click needed`, and the owner's
  click merges it by the human path — owner: luissiviero — resolution: the detour record
  `work/chain-check-without-gh/revisions/1.md` (kind `detour`) at this gate carries the route; the owner
  chose this route by word on 2026-09-18 ("the code merge stays the owner's click whatever the class").
- C2: fail-open on a runner without `gh` — policy: `work/approve-by-dispatch` R-13 (the gate's token and
  scope are declared, not assumed) — contradiction? no: the note is the same class of signal R-13 relies on
  for the token, `ubuntu-latest` ships `gh`, and the check does not sniff its environment — owner:
  luissiviero — resolution: owner's answer 5; the `gh --version` step in `sdlc-gate.yml` is available and
  not taken.
- C3: `kind: fix` locks `scripts/test_check_artifact_chain.py`, whose `DispatchAttestation._verify` stubs the
  call at the `["gh", "api"]` boundary — policy: `.claude/hooks/protect-tests.sh` — contradiction? no: the
  new cases live in a new module and R6 pins the design that keeps the locked suite green on a machine
  without `gh` — owner: n/a — resolution: D3, D4.

## Open questions carried from intent.md
- None carried. All five are closed on the intent by the owner (b4073a5, 9adde1a): (1) same skipped path as
  a missing token; (2) a present binary that fails stays `False`; (3) revised to `low`, `delegated`, the
  click on the locked file being the safety net; (4) the workaround retires in the step-7 handoff refresh;
  (5) no environment sniffing, the `gh --version` workflow step noted and not taken. One refinement of answer
  1 is made here rather than carried: it named `shutil.which` plus the exception; D3 keeps the exception only,
  for the reason gotcha 1 measures.

## Decisions (ADR-style: context → decision → consequences)
- D1: **A missing binary is "could not ask", never "refused".** Context: the caller has two fallbacks, `None`
  (note, then the author rule) and `False` (`FAIL`). Decision: absence returns `None`, exactly as absence of
  the token does. Consequences: an agent-authored trailer commit still fails on the author rule (R2, the
  security-pass finding on pull request 51 kept intact); a human-authored one passes with a note, which is
  what every remote session needs.
- D2: **A binary that answers non-zero stays `False`.** Context: owner's answer 2. Decision: no change to
  `:239`. Consequences: a revoked token on a workstation with `gh` is a `FAIL` with the API's message, and
  the remedy stays "unset the token, or fix it"; CI keeps its strictness.
- D3: **Catch the failed exec; do not look up the binary first.** Context: gotcha 1 -- the locked suite's
  `_verify` helper replaces `subprocess.run` and never has a real `gh`; a `shutil.which` guard ahead of the
  call would skip the stub and turn five green cases red on every machine without `gh`, this container
  included, and `kind: fix` forbids editing that suite. Decision: `except FileNotFoundError` around the
  existing call, nothing before it. Consequences: one fewer spelling than `github_metrics.py:71-77` uses;
  the note is produced after a failed `exec` rather than before an attempted one, which costs nothing
  observable; R6 pins it.
- D4: **New test module, composing the existing fixture by import.** Context: `kind: fix`; the pattern of
  `test_chain_no_slug.py` and `test_chain_shallow.py`. Decision: `scripts/test_chain_no_gh.py` imports
  `test_check_artifact_chain` as `base` for `_make_repo`, `_write`, `_git`, `_artifact`, `_last_line`,
  `SCRIPT`, and builds the trailer commit in the shape `ApprovalAuthor._reapprove_with_trailers` builds it
  (author the run's actor, committer the bot, both trailers), with a `PATH` of its own. Consequences: a
  renamed helper fails loudly here; the module carries its own identities and its own `PATH`
  (`knowledge/lessons/tests-carry-their-own-environment.md`).
- D5: **The note names the binary, not the token.** Context: two skipped causes must be distinguishable in a
  pasted log. Decision: `no gh binary on PATH; the dispatch trailer was accepted on the author rule alone`,
  sharing the second clause with the no-token note so a reader searching for "author rule alone" finds both.
  Consequences: one new constant; no existing assertion matches it.

## Gotchas found while reading the codebase
- **The locked suite passes here only because it never spawns `gh`.** `DispatchAttestation._verify`
  (`scripts/test_check_artifact_chain.py:657-687`) replaces `check_artifact_chain.subprocess.run` with a
  fake that answers `["gh", "api", ...]` from a JSON payload, and its `setUp` sets a token. On this
  container, with no `gh`, all five of its verifying cases are green today for that reason alone. Any
  guard that asks the filesystem before the call (`shutil.which`, `os.access`) runs before the fake and
  returns the skipped tuple, so `test_matching_run_verifies` would assert `True` and get `None`. The intent's
  proposed answer 1 named `shutil.which`; measured, it would have broken the suite the plan may not touch.
  D3 and R6 are the consequence.
- **The crash is reached only with a trailer to attest.** `verify_dispatch_run` is called at `:922` only when
  `dispatch_attestation(sha)` finds `Approved-Run`/`Approved-Actor` on the commit that set the status. A
  fixture built with `base._make_repo` alone (plain approval commits) never reaches it, so R1's fixture must
  carry the trailers, and `verify.sh` on a commit whose pointer is empty passes with the token set (measured
  on `17004b4` in the intent).
- **`protect-approvals.sh` refuses any Bash command whose text names `approve.py`**, a `grep` included; it
  bit this session once while reading the script. Read it with the file tools, never through a shell line.
- **`sign.py --revision` on a first signature warns and proceeds** (`scripts/sign.py:222-225`), and
  `check_revisions` (`check_artifact_chain.py:465`) counts only re-signatures, so the detour record at this
  gate is validated by the reviewers' verdicts and the ledger note's shape, not by the chain check. This
  is the first `kind: detour` record in the repository; the next item to file one at a first signature
  should expect the same.
- **`run_tests.py` discovers `test_*.py` by name** (`scripts/run_tests.py:44`), so the new module runs in
  `verify.sh` with no registration.

## Not doing
- Installing `gh` in the remote environment: it would hide the defect for one runtime and leave the check
  crashing wherever else a token meets no binary.
- Catching `OSError` broadly (a present binary that cannot execute, `PermissionError`): not the measured
  fault, and not "absent"; it keeps raising until someone measures it.
- `scripts/approve_dispatch.py:198`'s own `gh api` call (runs only inside `approve.yml` on a runner with the
  binary); `scripts/delegated_merge.py`'s `gh_api`, which already names its error.
- Retiring the handoff's `env -u GH_TOKEN -u GITHUB_TOKEN` lines here: owner's answer 4, the step-7 refresh.
- The `gh --version` step in `sdlc-gate.yml`: owner's answer 5, a workflow change only the owner makes.
- Defect 2 (`EXEMPT` and the stale `evals/` docstring at `check_artifact_chain.py:23`).
- The tap count: this item runs under a grant with one click owed on the locked file; how many items can run
  tap-free is `work/standing-grant`'s question, not this spec's.
