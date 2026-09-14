---
type: sdlc/spec
id: approve-tap-regenerates-index
title: The approval tap regenerates the indexes it leaves stale, inside the committer
description: "scripts/approve_dispatch.py --commit renders work/<slug>/index.md and work/index.md with gen_index.py's own renderer before it stages, commits every generated index it changed (other items' included, so a tap heals drift already on main), keeps refusing every other stray path, and its allowlist and docstring say so. The workflow, approve.py and the generator do not change."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: delegated
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by: claude
approved-on: 2026-09-14
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: e879ca8
prompt: "/sdlc-run approve-tap-regenerates-index -> /sdlc-spec, in session_01WSLuyVWcurCx6yPwNqxPPo, from the approved and delegated intent; a direct read of .github/workflows/approve.yml, scripts/approve_dispatch.py, scripts/test_approve_dispatch.py, scripts/gen_index.py, scripts/checks/index-drift.sh and .sdlc/config.env; the five tap commits on main (a903a91, 3da8bb6, c0aa58c, b30feff, 70437ab); and a scratchpad probe of the generator's behaviour on malformed input. No explorer subagent: the code surface is two files"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/commit/c0aa58c
tags: [approvals, workflow-dispatch, gen-index, index-drift, verify, delegated-mode]
timestamp: 2026-09-14T02:45:00Z
---
# Spec: the approval tap regenerates the indexes it leaves stale, inside the committer

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `--commit` regenerates every index before it stages: it calls `gen_index.render_all(root)` on the checked-out tree and writes each rendered file with the generator's own encoding (`utf-8`, LF), so the tap's commit carries `work/<slug>/index.md` and `work/index.md` beside the artifact and `log.md`, and `python3 scripts/gen_index.py --check` on the committed tree prints `INDEX: up to date`. | 1 (the next tap commit touches both indexes; `--check` on it is up to date) | `scripts/test_approve_dispatch.py::Commit::test_commit_regenerates_both_indexes` — approve `demo`, run `commit()`: returns 0; `git show --name-only HEAD` is exactly `work/demo/index.md`, `work/demo/intent.md`, `work/demo/log.md`, `work/index.md`; each committed index is byte-identical to the matching entry of `gen_index.render_all(root)`; `gen_index.py --check --root <fixture>` exits 0 with `INDEX: up to date`. The case must be seen red on today's code, where the commit carries no index and `work/index.md` would be a stray path, before the change is written (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`). |
| R-2 | A tap heals drift it finds. When the tree already carries a stale index of another item, regeneration rewrites it and the commit carries it too, so the ref the tap pushes to is `INDEX: up to date` whatever it was before. | 2 (a stale index of another item is in the commit) | `Commit::test_a_stale_index_of_another_item_is_committed_too` — fixture adds `work/other/intent.md` and a hand-written, stale `work/other/index.md`, both committed in `init`; approve `demo`, run `commit()`: returns 0; `HEAD` names `work/other/index.md` beside the four paths of R-1; its bytes equal `render_all`'s entry for it. Red today: nothing regenerates, so the path is not in the commit. |
| R-3 | The allowlist widens by exactly the generated indexes and nothing else. A changed path is allowed when it is one of the item's chain files (`CHAIN_FILES` under `work/<slug>/`), `.sdlc/active`, `work/index.md`, or `work/<dir>/index.md` where `<dir>` is one path segment with no leading dot (`^[A-Za-z0-9_][A-Za-z0-9._-]*$`), the set of directories the generator itself visits. `SLUG_RE` still governs the slug a tap may name; it is not the test for a generated path (D4). | 3 (the allowlist names every generated index) and 4 (nothing else becomes committable) | `Commit::test_generated_indexes_of_any_item_are_allowed` — with `work/other/index.md`, `work/_example/index.md` and `work/index.md` changed, `unexpected_paths("demo")` is `[]` (red today: the first two are strays). `Commit::test_index_lookalikes_are_stray` — `index.md` at the root, `work/other/sub/index.md`, `work/.hidden/index.md`, `work/other/index.md.orig` and `work/other/intent.md` are each returned by `unexpected_paths("demo")`, sorted. |
| R-4 | The stray-path guard keeps its strength. A path outside the widened allowlist still aborts the commit, is named in the refusal, and the regenerated indexes do not mask it. | 4 | The existing `Commit::test_a_stray_path_aborts_the_commit`, `test_a_stray_path_is_named_in_the_refusal` and `test_another_items_files_are_a_stray_path` pass unmodified; new `Commit::test_a_stray_beside_regenerated_indexes_still_aborts` — approve `demo`, add `scripts/sneaky.py`: `commit()` returns 1, `HEAD` is unchanged, and the refusal on stderr names `scripts/sneaky.py` and no index path. |
| R-5 | A run in which the approval wrote nothing makes no commit, even when regeneration changed an index. The nothing-staged refusal judges the non-generated paths: if every staged path is a generated index, `--commit` prints the existing `nothing staged; approve.py wrote no change` line and returns 1 with `HEAD` unchanged (D3). | 4 (the tap's commit is an approval record, never an index-only commit under approval trailers) | The existing `Commit::test_nothing_to_stage_is_refused` passes unmodified on the unchanged fixture, whose `init` commit carries no index (G-3); new `Commit::test_index_only_changes_do_not_make_a_commit` — fixture with a stale `work/other/index.md` committed and no approval written: `commit()` returns 1, `HEAD` unchanged, `git diff --cached --name-only` empty afterwards. |
| R-6 | The committer's text says what is true. The module docstring's `--commit` paragraph and the comment above `CHAIN_FILES` name the regeneration that happens inside `--commit` and the two generated paths; the sentence "gen_index.py's index.md is regenerated in the same tree" is replaced by one that names who regenerates it. | 3 (the comment names the regeneration that happens) | `grep -c "gen_index" scripts/approve_dispatch.py` is at least 3 (the import, the docstring, the allowlist comment); `grep -c "is regenerated in the same tree" scripts/approve_dispatch.py` is 0. |
| R-7 | Everything the run trusts is unchanged: `.github/workflows/approve.yml`, `scripts/approve.py` and `scripts/gen_index.py` are byte-identical to `main`; no dependency is added (`gen_index.py` and the two kit modules it imports are stdlib only); the role gate `check_actor` and the slug containment `SLUG_RE` are untouched. | intent Constraints (one checkout, no head code, no dependency, `approve.py` untouched) | `git diff origin/main --stat -- .github/workflows/approve.yml scripts/approve.py scripts/gen_index.py` prints nothing; the pull request's changed files are exactly `scripts/approve_dispatch.py`, `scripts/test_approve_dispatch.py` and this item's `work/approve-tap-regenerates-index/*`; every pre-existing case in `ActorCheck`, `Mode` and `SlugContainment` passes unmodified; `python3 scripts/check_artifact_chain.py --base origin/main --slug approve-tap-regenerates-index` ends `CHAIN: PASS`. |
| R-8 | The run log shows what was regenerated. After rendering, `--commit` prints one stdout line, `approve-dispatch: regenerated <n> index file(s): <relpaths, comma-separated, sorted>` when at least one file's bytes changed, or `approve-dispatch: indexes already up to date` when none did. Stdout of the Commit step is the workflow's run log, so the owner can read from the run what the tap rewrote. | 1 (observable from the run) | `Commit::test_commit_regenerates_both_indexes` captures stdout and asserts the line names `work/demo/index.md` and `work/index.md` with `2 index file(s)`; `Commit::test_index_only_changes_do_not_make_a_commit` asserts the `regenerated 1 index file(s): work/other/index.md` line precedes the refusal. |
| R-9 | The whole loop is green with the new cases counted: `scripts/verify.sh` ends `VERIFY: PASS`, `python3 scripts/check_artifact_chain.py --base origin/main --slug approve-tap-regenerates-index` ends `CHAIN: PASS`, `scripts/run_evals.sh` ends `0 fail`, `python3 scripts/check_okf.py` ends `0 warnings`, and both generators report up to date. | 5 | The last lines, pasted in the pull request; `python3 scripts/run_tests.py -p test_approve_dispatch.py` reports 26 cases before and 32 after (six new cases: R-1, R-2, two for R-3, R-4, R-5). |

## Design
### Architecture / data flow
One function changes shape. `commit()` in `scripts/approve_dispatch.py:141-164` today runs: stray check →
stage the fixed `present` list → nothing-staged check → commit with the split identity and the two trailers.
It becomes:

1. **Regenerate.** `root = gen_index.resolve_root(root)` (the caller's `--root`, else the git toplevel: the
   workflow's Commit step runs from the checkout root with no `--root`, `approve.yml:130-132`). For each
   `(relpath, content)` in `gen_index.render_all(root)`, compare `content.encode("utf-8")` with the bytes on
   disk (CRLF folded to LF, as `gen_index.py:274` does) and write the file when they differ, with
   `open(full, "w", encoding="utf-8", newline="\n")`, the generator's own call at `gen_index.py:287`.
   Collect the relpaths written; print the R-8 line.
2. **Stray check.** `unexpected_paths(slug, root)` as today, with `allowed_paths` replaced by a predicate
   `is_allowed(path, slug)` (Interfaces). Any refused path aborts with the existing message and exit 1; the
   regenerated files stay in the runner's tree, which the run then discards.
3. **Stage.** `git add -- <every path git status reported>`: after step 2 each of them is allowed, and the
   list now includes the generated indexes wherever they sit. (Today's `present` list stages only the
   item's own files and `.sdlc/active`, which is why a regenerated `work/other/index.md` could never have
   been committed even if something had rendered it.)
4. **Nothing-staged check.** The reported paths, minus every path the index predicate accepts. Empty
   means the approval wrote nothing: print the existing refusal and return 1 before anything is staged
   (D3), so `git diff --cached` is empty as R-5 requires; the regenerated indexes stay unstaged in a
   tree the run discards, and no commit is made. (Build corrected this step: it first said the indexes
   were left staged, which R-5's own acceptance test contradicts.)
5. **Commit** exactly as today: subject `[<slug>] Approve <artifact> as <actor>`, optional note, the
   `Approved-Run` and `Approved-Actor` trailers, author the actor, committer the bot.

Nothing upstream moves: `check_actor` (`:76-97`) and the Approve step run before `--commit` as before, and
the workflow's `git push origin HEAD:$REF` follows it as before.

### Interfaces (APIs, events, schemas) — exact shapes
- `is_allowed(path, slug) -> bool`, replacing the set membership at `approve_dispatch.py:136`. True when
  `path` is in `allowed_paths(slug)` (unchanged: `work/<slug>/<CHAIN_FILES>` and `.sdlc/active`; `SLUG_RE`
  still refuses a traversing slug with the same `SystemExit`), or `path == "work/index.md"`, or
  `INDEX_RE.fullmatch(path)` with `INDEX_RE = re.compile(r"work/([A-Za-z0-9_][A-Za-z0-9._-]*)/index\.md")`.
  The segment class is the generator's, not the tap's: `gen_index._work_items` renders every directory
  under `work/` (`gen_index.py:118-125`), `_example` included, and `SLUG_RE` rejects a leading `_` (D4).
  A leading dot is excluded so `.`, `..` and `.git` never match, the same containment `SLUG_RE` gives the
  slug (`:47-54`).
- `regenerate(root) -> list[str]`: the relpaths whose bytes changed, sorted. Reads nothing but the tree;
  raises whatever `render_all` or `open` raises, and `commit()` does not catch it (Failure modes).
- Stdout, one line, before any staging: `approve-dispatch: regenerated <n> index file(s): <p1>, <p2>` or
  `approve-dispatch: indexes already up to date`.
- Stderr on refusal: unchanged text, `approve-dispatch: refusing to commit; an approval may not touch:
  <strays>` and `approve-dispatch: nothing staged; approve.py wrote no change`.
- `CHAIN_FILES` keeps `index.md`; the comment above it (`:56-58`) is rewritten to say that `--commit`
  regenerates `work/*/index.md` and `work/index.md` itself with `gen_index.render_all` and commits every
  one it changed. The docstring's `--commit` paragraph (`:16-17`) gains the same sentence.
- No new flag, input, environment variable, workflow step, front-matter key, or file outside the two.

### Data and migrations
None. The committer writes two kinds of generated Markdown whose content is a pure function of tracked front
matter and ledger lines already on the ref. No field is added; no data classification applies
(security-standards §4: n/a, no new field).

### Failure modes and how they surface
- **Regeneration raises.** The probe shows `gen_index` never raises on content: an unterminated front-matter
  block, a ledger line that does not parse, a file with no front matter and an item directory with no
  `intent.md` all render (with empty cells) and exit 0 (G-1). What can raise is the tree: an unwritable
  file or directory (`OSError`) or a `work/` that is not a directory. The exception propagates out of
  `commit()` before any `git add`, `--commit` exits non-zero with the traceback in the run log, the Commit
  step fails before its `git push`, and the runner's tree is discarded. Nothing lands, which is the
  intent's stated shape for this case.
- **A stray path.** Refused as today, naming the stray and only the stray (R-4). The regenerated indexes are
  in the discarded tree.
- **Only indexes changed.** Refused (R-5, D3). In production this needs the Approve step to have written
  nothing, which `approve.py` does not do silently; the case exists for the test fixture and as a guard on
  the trailers' meaning.
- **A generated index the predicate rejects.** Only a directory under `work/` with a leading dot could
  produce one; none exists, and if one appeared its index would be named as a stray and the tap would
  refuse, visibly, rather than commit it.
- **The predicate is too wide.** Pinned by `test_index_lookalikes_are_stray` (R-3): a root `index.md`, a
  nested one, a dot-directory, a suffix, and another item's `intent.md` all still refuse.

**Security standards, rule by rule** (the reviewer checklist the skill asks for):
1. Secrets — n/a: no secret is read or written; the fixtures carry none.
2. Auth — n/a, no endpoint: the role gate is `check_actor` (`approve_dispatch.py:76-97`) and does not
   change; the identity written to the commit is still the run's actor (`:100-111`).
3. Input — the slug is already schema-checked by `SLUG_RE` (`:54`); the new predicate is a `fullmatch`
   over the paths `git status --porcelain` reports; every git call is an argv list (`:62-66`), never a
   shell string; nothing is interpolated into a command.
4. Data — n/a, no new field (Data and migrations).
5. Dependencies — none added: `gen_index.py` imports `argparse`, `os`, `subprocess`, `sys`, `datetime`
   and the kit's own `check_artifact_chain` and `log_ledger` (`gen_index.py:32-40`).
6. Infra — no path under `RELEASE_GATED_PATHS`; the workflow file is untouched (R-7).
7. Logging — the R-8 line carries repository-relative paths only.
8. Agent hygiene — the writer of this item does not sign off its review: `/sdlc-review` runs
   `plan-reviewer` and `security-reviewer` on a different model where one is available, both read-only.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the committer becomes a writer as well as a stager, which `approve-by-dispatch.md` decision 6 (D6:
  "the committer refuses to stage any path outside work/<slug>/ and .sdlc/active") did not foresee —
  policy: `knowledge/decisions/approve-by-dispatch.md` — contradiction? no — owner: luissiviero —
  resolution: the owner chose this route in the intent's first open question (2026-09-08); the refusal set
  D6 describes widens by exactly the generated paths, each of which is a function of content already on
  the ref, and the widening carries its own positive and negative tests (R-3).
- C2: a `contents: write` run now commits files derived from other items' front matter and ledgers, not
  only the item being approved — policy: `.github/workflows/approve.yml` header ("the committer refuses to
  stage any path outside work/<slug>/ and .sdlc/active") — contradiction? the header sentence becomes
  imprecise — owner: luissiviero — resolution: accepted in the intent's second open question; the only way
  to change a generated index is to change a tracked artifact or ledger, which needs its own commit on the
  ref, so nothing becomes committable that a person could smuggle content through. The header sentence
  lives in a protected file this item may not edit; it is reported in the pull request for the owner to
  fix in a later tap-side change, and `approve_dispatch.py`'s own text is corrected here (R-6).
- C3: the allowlist now judges "an item" by two spellings: `SLUG_RE` for the slug a tap names, and the
  generator's directory class for a generated index — policy:
  `knowledge/lessons/one-path-spelling-in-guards.md` — contradiction? no — owner: luissiviero —
  resolution: the two answer different questions (may a tap name this item, versus did the generator
  write this file), and unifying them would either refuse every tap while `work/_example/index.md` is
  stale or let a tap name `_example`; both classes are pinned by tests (R-3, and the existing
  `SlugContainment` cases), and the D4 comment says why they differ.

## Open questions carried from intent.md
- None unresolved. Both of the intent's questions were answered by the owner on 2026-09-08 and are the
  basis of this design: the regeneration lives inside `--commit` (D1), and a tap commits every index it
  regenerates rather than refusing on, or staging around, another item's drift (D2, R-2).

## Decisions (ADR-style: context → decision → consequences)
- D1: **Call the renderer, write locally, and let `--check` be the arbiter of byte-identity.** Context: the
  intent requires the generator's own renderer, never a second one; `gen_index.py` exposes `render_all`
  but keeps its write loop inside `main()`, which calls `sys.exit`. Decision: `approve_dispatch` imports
  `gen_index`, calls `render_all`, and writes with the same `open(..., encoding="utf-8", newline="\n")`;
  `gen_index.py` is not edited. Consequence: the file list stays at the two files the intent names; the
  rendering is shared, the four-line write is not, and R-1's `gen_index.py --check` on the committed tree
  is what proves the two write routes agree, every time the suite runs.
- D2: **Regenerate before the stray check, not after.** Context: the intent wants a tap to heal drift found
  on `main`, and wants a stray path refused as today. Decision: render first, then judge the whole tree.
  Consequence: a regenerated index of any item is present when the guard runs and is allowed by R-3; a
  stray is still refused and the regenerated files go with the discarded tree. Refusing on drift, or
  staging around it, were both rejected by the owner in the intent.
- D3: **An index-only diff is not a commit.** Context: the fixture's `init` commit carries no index (G-3),
  so after D2 every `commit()` call finds two new files, and `test_nothing_to_stage_is_refused` would flip
  green-to-red unless the refusal ignores generated paths. Decision: the nothing-staged check subtracts the
  paths the index predicate accepts. Consequence: the tap's commit always records an approval the trailers
  can vouch for; the existing case passes unmodified; an index-only clean-up stays a session's or the
  owner's ordinary commit, as it is today.
- D4: **The generated-index predicate follows the generator's directory class, not `SLUG_RE`.** Context:
  `gen_index._work_items` renders every directory under `work/` and `main` tracks `work/_example/index.md`;
  `SLUG_RE` refuses a leading `_` because a tap must never name paths outside one item. Decision: a
  segment with no leading dot, one level deep, ending `/index.md`. Consequence: a stale `_example` index
  heals like any other; `.`/`..`/`.git` are excluded by the same rule that excludes them from slugs; C3
  records the two spellings and the tests pin both.
- D5: **Stage what `git status` reported, not a fixed list.** Context: today's `present` list (`:147-149`)
  stages the item's files and `.sdlc/active` and can never reach another item's index. Decision: after the
  stray check passes, every reported path is allowed, so stage exactly those. Consequence: one list drives
  both the guard and the staging, so they cannot disagree; a file that exists but did not change is no
  longer `git add`ed for nothing.

## Gotchas found while reading the codebase
- G-1: `gen_index.py` is tolerant by design. Probed on 2026-09-14: an unterminated front-matter block
  parses as the keys seen so far (`front_matter` returns `{'status': 'in-review', 'title': '[unterminated'}`),
  a ledger line that does not parse is dropped by `log_ledger.parse`, a file with no front matter renders
  empty cells, and a plain file under `work/` is skipped; each exits 0 and writes. So "the generator
  fails" means an `OSError` on the tree, not bad content, and the spec's failure mode says so.
- G-2: `work/_example` is a real, tracked item on `main` (26 `work/*/index.md` files tracked, that one
  among them) and its name fails `SLUG_RE`. A predicate built on `SLUG_RE` would refuse every tap the
  moment that one index drifted, with a message naming a file no tap wrote (D4).
- G-3: `make_repo` in `test_approve_dispatch.py:17-33` commits `.sdlc/active` and `work/demo/intent.md`
  and no index. After D2 every `commit()` in the suite renders two new untracked files, so the fixture is
  what forces D3; `--untracked-files=all` (`:124`) already lists a new file inside an existing directory
  one path at a time.
- G-4: `test_active_and_index_are_allowed` (`:242-249`) writes `# index\n` to `work/demo/index.md` and
  asserts only that the path is in the commit. Regeneration overwrites its content, and the assertion
  still holds, so the case passes unmodified; it is not a byte-identity test and R-1 adds the one that is.
- G-5: the import chain `approve_dispatch → gen_index → check_artifact_chain, log_ledger` reaches a
  `locked-paths` file, `scripts/check_artifact_chain.py`, for its `front_matter` reader only. Importing
  does not modify it; `delegated_merge.py`'s locked-path floor compares bytes on the head, so the pull
  request stays mergeable by the workflow.
- G-6: `commit()` is given `root=None` in production (the Commit step passes no `--root`,
  `approve.yml:130-132`), and every existing `git()` call already relies on `cwd=None` meaning the
  checkout root. `gen_index.resolve_root(None)` returns the git toplevel, which is the same directory, so
  the fixture (`--root <tmp>`) and the runner take the same code path.
- G-7: the drift the intent scoped out (c0aa58c's `work/run-queue-followups/index.md`) is already gone:
  `python3 scripts/gen_index.py --check` on `main` at 864923e prints `INDEX: up to date`, healed by the
  agent commits and the clean-up pull requests (#78, #80, #81) the handoff records. There is nothing stale
  for this item's pull request to report, and its own artifacts' indexes are regenerated before every
  commit as `CLAUDE.md` requires.
- G-8: the 2026-09-14 taps repeat the shape exactly: `b30feff` (`advance-push`) committed two paths,
  `70437ab` (`approve-tap-regenerates-index`) three, no index in either; the two clean-ups took two pull
  requests (#80, #81) because the chain check reads one work item at a time. The heal in R-2 is what
  removes that pair of pull requests from every future tap.
- G-9: `run-name`, the role gate and the slug resolution (`approve.yml:56-97`) run before the Approve
  step and do not read the tree's indexes, so nothing this item changes can alter which actor, slug or
  artifact a run records.

## Not doing
- A regeneration step in `.github/workflows/approve.yml`: rejected by the owner in the intent (a protected
  path forces the label, the click, and the end of the queue). The header sentence there that C2 finds
  imprecise is reported in the pull request, not edited.
- Any change to `scripts/approve.py` (a `locked-paths` entry; decision 3 of `approve-by-dispatch.md` keeps
  the tap's run of it byte-identical to a plain run) or to `scripts/gen_index.py` (D1).
- Guarding a human's hand-made approval commit, or a web-editor retirement, against the same omission:
  `knowledge/lessons/human-commits-leave-indexes-stale.md` covers the session side; a tap-shaped
  retirement is a follow-up item.
- Running `sdlc-gate` on pushes to `main`.
- Regenerating `CLAUDE.md`, `GEMINI.md` and `AGENTS.md` (`gen_context_files.py`) from the tap: a tap
  changes no rule fragment, so those never drift on a tap.
- A new eval case: the regression lives in `scripts/test_approve_dispatch.py`, the file that already tests
  the committer, as the intent requires; `scripts/verify.sh` runs it on every gated commit.
