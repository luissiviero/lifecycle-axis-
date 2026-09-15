---
type: sdlc/spec
id: self-check-false-reds
title: The self-check fails on an empty pointer and misreads approvals on a shallow clone
description: "Three requirements: an empty .sdlc/active becomes a note where nothing needs proving, a grafted boundary commit is never reported as an approver, and advance() regenerates the indexes its own ledger line dirties."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: in-review
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by:
approved-on:
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: cffcedde592880a56c98fc7cfc2d8793c727c051
prompt: "/sdlc-spec on the approved intent (d3bd674), with the owner's six answers recorded in 6f303af"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/103
tags: [chain-check, delegated-merge, advance, shallow-clone, gen-index, fix, defect-1]
timestamp: 2026-09-15T14:15:00Z
---
# Spec: the self-check fails on an empty pointer and misreads approvals on a shallow clone

## Requirements (each maps to an intent outcome)

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R1 | With no slug (empty `.sdlc/active`, no `--slug`) and a diff in which **every** changed path is `EXEMPT`, the check prints a `note:` naming the empty pointer and exits 0. | "An empty pointer is a note, not a failure, where nothing needs proving." | New case: a fixture at `4eb8383`'s shape (empty pointer, diff touching only `work/`) ends `CHAIN: PASS` with the note, exit 0. Red on today's code, which exits 1 at `:528`. |
| R2 | With no slug and a diff containing **any** path outside `EXEMPT`, the check still prints `FAIL: no active work item` and exits 1. | Same outcome, strict half: "strict mode still FAILs ... because that is exactly where an approved chain must be proven." | New case: same empty pointer, diff additionally touching `scripts/foo.py`; ends `CHAIN: FAIL`, exit 1, on the same message as today. Green on today's code and must stay green. |
| R3 | An explicit `--slug` naming an item with no `work/<slug>/intent.md` still FAILs, whatever the pointer holds. | "An explicit `--slug` naming an item that does not exist still FAILs." | Existing behaviour pinned by a new case: `--slug no-such-item` exits 1. Green today; a regression guard for R1's reordering. |
| R4 | When the commit `git log -G` returns for an artifact's `status:` or `mode:` line is a grafted boundary commit, the check reports a `note:` naming the graft and the sha, attributes the act to nobody, and raises no error from it. | "A shallow clone never attributes an approval to the graft." | New case over a real depth-1 fixture clone at `4eb8383`: `--slug ci-budget` ends `CHAIN: PASS` with the graft note; today it ends `CHAIN: FAIL` with three agent-identity errors. |
| R5 | On a non-shallow repository both `-G` lookups return exactly the commit they return today. | "On a full clone the reported commit is unchanged." | New case: full clone, `--slug ci-budget`, the three resolved shas are `0e9d160`, `4a8fb4f`, `104c27d`. Green today and after. |
| R6 | The check performs no network operation and no write to the repository under any of R1–R5. | "The check still mutates nothing — it must not fetch." | New case asserts no `fetch`/`clone`/`remote` argv reaches `subprocess` during a full run (patched runner recording argv), and `git status --porcelain` is byte-identical before and after. |
| R7 | `advance()` regenerates `work/<merged>/index.md`, `work/<next>/index.md` (when there is a next) and `work/index.md` in the same commit that writes the pointer and the ledger lines. | "An advance leaves no drift behind." | New case: after `advance()` on a fixture, `gen_index.check()` reports no drift; the commit's `--name-only` list equals the allowlist exactly. Red today (`INDEX: 2 file(s) drifted`). |
| R8 | The `written` allowlist stays closed: any staged path outside it still raises `MergeError` and resets the index. | "Keep `advance()`'s allowlist a closed list." | Existing `:1169` behaviour pinned by a new case that dirties an extra path and asserts `MergeError` plus an empty staging area. Green today and must stay green. |

R1+R2+R3 are intent fault (a) with the owner's Q1 answer; R4+R5+R6 are fault (b) with the Q2 answer; R7+R8 are fault (c) with the Q3/Q4 answers.

## Design

### Architecture / data flow

**R1–R3 — the no-slug decision moves after the diff.** Today `:528` exits before the diff exists, so it cannot know whether anything needs proving. The check acquires a slugless mode question, because the existing `own_artifact(p)` predicate at `:656` is defined in terms of `slug` and is unavailable here.

Order becomes:

1. boundary validation of `--slug` and the pointer (unchanged, `:514-527`);
2. the base-ref and dirty-tree guards (unchanged, `:556-598`) — these already fail closed and must keep running first;
3. **new**: if there is no slug, decide on the diff alone —
   - every path in `changed_all` starts with an `EXEMPT` prefix → `note: no active work item (.sdlc/active is empty); the diff touches no code, so there is no chain to prove` and exit 0 after printing `CHAIN: PASS`;
   - otherwise → today's `FAIL: no active work item ...` line and exit 1;
4. everything downstream is unchanged and still runs only with a slug.

`EXEMPT` is reused verbatim rather than re-spelled (`knowledge/lessons/one-path-spelling-in-guards.md`). It is the repository's existing answer to "does this path need a plan to authorise it", which is the same question asked here.

**R4–R6 — the graft predicate.** One helper, used by both `-G` call sites (`:386` for `^mode: delegated$`, `:833` for `^status: {status}$`):

```
_is_graft(sha) -> bool
    read the file named by `git rev-parse --git-path shallow`
    return sha in its lines
```

Measured on a real depth-1 clone at `4eb8383`: `.git/shallow` holds `4eb8383c9171b0c227366f84cc4b863805edd2df` and `-G` returns that same sha. Membership is exact, needs no parsing beyond splitting lines, and is false for every commit in a full clone (the file is absent, which the helper treats as "no grafts").

At each call site, when `_is_graft(sha)` is true the code takes the **same branch it already takes when `who` is empty** — the "not committed yet (author check skipped)" note — with a message naming the graft instead:

```
work/<slug>/<name>: history is shallow at <sha12>; the author check needs the real approval
commit -- run `git fetch --unshallow origin`
```

No new error path, no new exit code, and the existing note-only shape is reused, so the failure mode is the one the code already has: an author check that did not run says so.

**R7–R8 — regeneration inside `advance()`.** `delegated_merge.py` does not import `gen_index` today. It gains a module-level import beside the existing `chain` import, and after the ledger appends at `:1150-1163`:

```
written.extend(gen_index.write_all(root))   # returns the repo-relative paths it wrote
```

`write_all` is the existing full regeneration (what `gen_index.main()` runs) returning its written paths, so the allowlist grows by exactly what was regenerated, computed rather than hard-coded. The `staged - written` refusal at `:1164-1170` is untouched and keeps its meaning: it now refuses anything outside {pointer, ledgers, regenerated indexes}.

### Interfaces (APIs, events, schemas) — exact shapes

- `check_artifact_chain._is_graft(sha: str) -> bool` — new, module-private. Returns False when the shallow file is absent or unreadable (a full clone, and any environment where the path cannot be read: failing to detect a graft leaves today's behaviour, which is the safe direction here because R5 pins it).
- `gen_index.write_all(root: str) -> list[str]` — the one new public seam. If `gen_index` already exposes an equivalent, that one is used unchanged and no new function is added; the plan resolves this by reading `gen_index.main()` (see C3).
- No change to `check_artifact_chain.main()`'s argv, exit codes (0 / 1), or the `CHAIN: PASS|FAIL` last line.
- No change to `advance()`'s signature or return value (`nxt` or `None`).

### Data and migrations

None. No file format, front-matter key, ledger grammar or policy file changes. `.sdlc/active`'s two valid states (a slug, or empty) are unchanged — R1 changes only how a reader reacts to the empty one.

### Failure modes and how they surface

| Failure | Surfaces as |
|---|---|
| Shallow file unreadable | `_is_graft` returns False → today's behaviour, including today's false FAIL. Degrades to the status quo, never to silence. |
| `gen_index.write_all` raises inside `advance()` | The existing `MergeError`/exception path: the advance commits nothing and the merge job reports it. The pointer is not moved, matching every other "not advancing" branch. |
| Regeneration produces a path outside the allowlist | `:1169` `MergeError` — unchanged, and R8 pins it. |
| An empty pointer with a code diff | Still `CHAIN: FAIL` (R2). |
| A graft that is also the real approval commit | Reported as a note, not an approval. Conservative: an approval that cannot be proven is not counted. |

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)

- **C1: R4 changes the one check standing between an agent commit and an accepted approval** — policy: `security-standards` §3 (validate at the boundary), `knowledge/decisions/human-only-approvals.md` — contradiction? **no** — owner: luissiviero — resolution: the change is strictly narrowing. Today a graft is reported *as an approver* in both directions: it falsely fails a human-approved chain (measured) and falsely passes when the boundary happens to be human-authored (also measured, on `5bf9573`). Reporting nobody removes the false pass as well as the false fail. The predicate is membership in a git-maintained file, not a heuristic on commit content, and R6 pins that nothing fetches. **A shallow clone cannot be used to skip the check deliberately**: `sdlc-gate.yml:46` is `fetch-depth: 0`, so a pull request cannot make the gate's clone shallow, and the note is printed, not swallowed.
- **C2: R7 widens what an unattended `github-actions[bot]` job commits and pushes to `main`** — policy: `.sdlc/config.env` `PROTECTED_PATHS`, the `advance()` allowlist (`work/advance-push`) — contradiction? **no** — owner: luissiviero — resolution: the allowlist stays closed and computed, never open. It grows only by paths `gen_index` itself just wrote, all of which are already `GENERATED_PATHS` in `.sdlc/config.env` and are byte-compared by `scripts/checks/index-drift.sh` on every run, so a wrong regeneration is caught by an independent check rather than trusted. R8 pins the refusal.
- **C3: `gen_index.write_all` may not exist** — policy: `knowledge/lessons/one-path-spelling-in-guards.md` — contradiction? **no** — owner: luissiviero — resolution: the design requires *a* seam that regenerates and returns its paths; it does not require a new function. The plan reads `gen_index.main()` first and reuses whatever it already factors out. If a new seam is genuinely needed, `gen_index.py` is **not** on `locked-paths` (measured, `DETOUR: needed (5)` names five paths and this is not among them), so adding it costs no extra gate.
- **C4: the locked paths** — policy: `.sdlc/delegation.yaml` `locked-paths`, `.sdlc/config.env` `PROTECTED_PATHS` — contradiction? **no** — owner: luissiviero — resolution: per the skill's step 5, on a supervised item the locked paths are named here rather than routed around. `python3 scripts/check_detour.py --slug self-check-false-reds --paths <the design's paths>` returns `DETOUR: needed`: `scripts/check_artifact_chain.py`, `scripts/delegated_merge.py` and `scripts/next_item.py` are on `locked-paths`; `scripts/verify.sh` and `.sdlc/active` are `PROTECTED_PATHS, ALWAYS_LOCKED`. **The code lands by the owner's click with the `control-plane-approved` label, never by a delegated merge.** This was answered as open question 5 on the intent: no detour record, because the item seeks no grant.

## Open questions carried from intent.md

None. All six were answered by the owner on 2026-09-15 and are recorded in the intent's "Open questions" section and in the ledger (`6f303af`). The answers are load-bearing here: Q1 → R1/R2/R3, Q2 → R4/R5/R6, Q3 → this single spec rather than two, Q4 → R7's placement inside `advance()`, Q5 → C4's resolution, Q6 → `risk-class: medium`, which is why every gate on this item is a human tap.

One design detail the intent flagged and this spec resolves rather than re-asking: Q1 said "strict mode keeps `FAIL`", but strict/in-progress is decided by `own_artifact(p)`, which needs a slug and so cannot be evaluated when there is none. D1 records the substitute.

## Decisions (ADR-style: context → decision → consequences)

- **D1: with no slug, the mode question becomes "is every changed path `EXEMPT`?"** — Context: `in_progress` at `:661` is `all(own_artifact(p) ...)` and `own_artifact` closes over `slug`; with no slug there is no such predicate, so Q1's answer cannot be implemented literally. Decision: reuse `EXEMPT`, the repository's existing "does this path need a plan" line, as the slugless stand-in. Consequences: the note-and-pass case is exactly "a diff that changes no code", which is what the empty-queue advance produces; a code diff with no active item still fails, preserving everything the original FAIL protected. It is deliberately *more* conservative than `own_artifact`, since `EXEMPT` also covers `docs/`, `monitoring/` and `knowledge/` — paths that genuinely need no chain.
- **D2: the empty-pointer decision moves after the base-ref and dirty-tree guards, not before them.** — Context: `:528` currently runs first, so a repository with both an empty pointer and an unknown base ref reports the pointer. Decision: those two guards keep priority. Consequences: an observable ordering change — that repository now reports the base ref first. Both are `CHAIN: FAIL` with exit 1, so no caller's pass/fail flips; only the message does. Recorded because it is a behaviour change, not a refactor.
- **D3: a graft is detected by membership in git's own shallow file, not by counting parents or catching an error.** — Context: alternatives are "the commit has no parents" (false for a real root commit) and "let the author check fail and retry deeper" (a fetch, which R6 forbids). Decision: read `git rev-parse --git-path shallow`. Consequences: exact, local, zero-network, and correct for a genuine root commit — a full clone has no shallow file, so its root is never mistaken for a graft.
- **D4: on a graft, reuse the existing "author check skipped" note branch rather than adding an error.** — Context: the alternative is a new failure class for "cannot determine the approver". Decision: it is the same situation the code already handles when the artifact is not committed yet. Consequences: no new exit path to test or reason about; an unprovable approval is uncounted rather than counted wrongly, in both directions.
- **D5: `advance()` extends its allowlist with what `gen_index` reports writing, never a hard-coded list.** — Context: a hard-coded triple would drift the moment `gen_index` writes a fourth path. Decision: compute it. Consequences: the allowlist stays exactly as closed as today while remaining correct by construction; `:1169` keeps working unchanged.

## Gotchas found while reading the codebase

- **The module docstring at `check_artifact_chain.py:23` is wrong about `evals/`.** It says check 3 exempts "work/, docs/, evals/, monitoring/, knowledge/", but `EXEMPT` at `:55` has no `evals/` entry, and the comment at `:53` says so deliberately: *"evals/ is deliberately NOT exempt: run_evals.sh executes each case's `check:` block as shell in CI"*. The code is right and the docstring is stale. R1 reuses `EXEMPT`, so it inherits the correct behaviour — but anyone reading the docstring to predict R1's note-and-pass case would get `evals/` wrong. **Not fixed here** (a one-word docstring edit in a locked file, unrelated to the three faults); filed as a note for the owner, who may want it folded into defect 2, which is also an `EXEMPT` defect.
- **The `-G` fix already in the tree is doing its job, and this session proved it live.** `:819-821` records that `-S` once counted the phrase anywhere in the file, so a later agent commit mentioning `status: approved` in prose was read as the approver (`work/agent-evals` R-5). When this session added the owner's answers to an already-approved intent (`6f303af`, authored by Claude), `git log -G '^status: approved$'` still resolved to `d3bd674` (luissiviero). `-S` would have returned the agent commit. R4 must not regress this: R5 exists to pin it.
- **`advance()` never imports `gen_index` at all** — verified by grep, not assumed. So R7 is a new dependency edge between two locked files, not a call that already exists with a missing argument.
- **`delegated-merge.yml:81` checks out with no `fetch-depth`**, so the job `advance()` runs in is itself shallow. R7's regeneration therefore must read only the working tree. `gen_index.py` does, so this is a constraint satisfied by construction — but it is also why R4 and R7 must not be assumed independent: the very job that will regenerate indexes runs on a clone where R4's graft predicate is true.
- **`approve.yml` passes `--activate` only for `mode: delegated`** (`:140`), so a supervised item's `.sdlc/active` is moved by hand or not at all. This is why the empty/placeholder pointer is a standing condition rather than a transient, and therefore why R1 is worth fixing rather than working around.

## Not doing

- Fixing the stale `evals/` docstring at `:23` (above; belongs with defect 2, owner's call).
- Defect 2 (`EXEMPT` lists `CLAUDE.md` but not `GEMINI.md`/`AGENTS.md`) and defect 3 (the chain check crashes on a token with no `gh` binary), which keep their own intents.
- Any auto-deepening, auto-fetch or retry-on-shallow anywhere (R6 forbids it by test).
- Changing `next_item.py`. It is named in the intent's Affected systems so the detour check sees it, and it is read by `advance()`, but no requirement changes it.
- Moving `.sdlc/active`, or removing the retire tap's `next` input. R1 removes the *need* for the placeholder; retiring the input itself is a separate change the owner can make once this lands.
- Reading the two unread red `delegated-merge` runs `34908767884` and `34909007398`.
