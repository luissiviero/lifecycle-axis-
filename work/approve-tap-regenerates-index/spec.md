---
type: sdlc/spec
id: approve-tap-regenerates-index
title: The approval tap regenerates the indexes it leaves stale, inside the committer
description: "scripts/approve_dispatch.py --commit renders work/<slug>/index.md and work/index.md with gen_index.py's own renderer before it stages, and on the default branch also every other item's index it finds stale, so a tap on main heals drift; on any other ref it writes and stages only the item's own two, because the chain check counts only those as the item's files. It keeps refusing every other stray path, judges a rename at both ends, and its allowlist and docstring say so. The workflow, approve.py and the generator do not change."
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
prompt: "/sdlc-run approve-tap-regenerates-index -> /sdlc-spec, in session_01WSLuyVWcurCx6yPwNqxPPo, from the approved and delegated intent; a direct read of .github/workflows/approve.yml, scripts/approve_dispatch.py, scripts/test_approve_dispatch.py, scripts/gen_index.py, scripts/checks/index-drift.sh and .sdlc/config.env; the five tap commits on main (a903a91, 3da8bb6, c0aa58c, b30feff, 70437ab); and a scratchpad probe of the generator's behaviour on malformed input. No explorer subagent: the code surface is two files. Revised once after the first review round (revisions/1.md)"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/commit/c0aa58c
tags: [approvals, workflow-dispatch, gen-index, index-drift, verify, delegated-mode]
timestamp: 2026-09-14T03:20:00Z
---
# Spec: the approval tap regenerates the indexes it leaves stale, inside the committer

Revised once before the second review round (`revisions/1.md`): the heal of other items' indexes is
scoped to the default branch, because `check_artifact_chain.py` counts only `work/index.md` and the
item's own directory as its files and a foreign index in a work branch's diff turns that branch's pull
request red; a rename is judged at both ends; and the ref decision reads runner-set values with a
narrow fallback.

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `--commit` regenerates before it stages: it calls `gen_index.render_all(root)` on the checked-out tree and writes each rendered file it may commit (R-2 says which) with the generator's own encoding (`utf-8`, LF), so the tap's commit carries `work/<slug>/index.md` and `work/index.md` beside the artifact and `log.md`, and `python3 scripts/gen_index.py --check` on the committed tree prints `INDEX: up to date` when nothing else was stale. | 1 (the next tap commit touches both indexes; `--check` on it is up to date) | `scripts/test_approve_dispatch.py::Commit::test_commit_regenerates_both_indexes` — approve `demo`, run `commit()`: returns 0; `git show --name-only HEAD` is exactly `work/demo/index.md`, `work/demo/intent.md`, `work/demo/log.md`, `work/index.md`; each committed index is byte-identical to the matching entry of `gen_index.render_all(root)`; `gen_index.py --check --root <fixture>` exits 0 with `INDEX: up to date`; a second `regenerate` on the committed tree returns `[]` and prints `indexes already up to date`. Seen red on the code before the item (the commit carried no index and `work/index.md` was a stray). |
| R-2 | **A tap heals drift only where the intent said: on `main`.** The intent's outcome 2 reads "When main already carries a stale index of another item ... the tap commits that regenerated file too". So on the default branch the tap writes and commits every generated index whose bytes changed, other items' included. On any other ref it writes only `work/<slug>/index.md` and `work/index.md`, the two paths `check_artifact_chain.py`'s `own_artifact` (`:645-648` on `main`) counts as the item's own, leaves a stale foreign index untouched and unstaged, and reports it (R-8). The route is decided by R-11. | 2 (a stale index of another item is in the commit, on `main`) | Wide route: `Commit::test_a_stale_index_of_another_item_is_committed_too` — fixture with a committed, stale `work/other/index.md`; approve `demo`; `commit(ref="main", default_branch="main")`: returns 0; `HEAD` names `work/other/index.md` beside the four paths of R-1; its bytes equal `render_all`'s entry; stdout carries exactly `approve-dispatch: regenerated 3 index file(s): work/demo/index.md, work/index.md, work/other/index.md` (the generator renders `work/index.md` last, so this pins the sort). Narrow route: `Commit::test_on_another_ref_only_the_items_indexes_are_written` — same fixture, `commit(ref="work/demo", default_branch="main")`: returns 0; `HEAD` names exactly the four paths of R-1; `work/other/index.md` still reads `# stale`; stdout carries `approve-dispatch: left 1 stale index file(s) unwritten on this ref: work/other/index.md`. Both red before the revision: the first because nothing regenerated, the second because the foreign index was committed. |
| R-3 | The allowlist widens by exactly the generated indexes, scoped by route. A changed path is allowed when it is one of the item's chain files (`CHAIN_FILES` under `work/<slug>/`), `.sdlc/active`, `work/index.md`, or, on the wide route only, `work/<dir>/index.md` where `<dir>` is one path segment with no leading dot (`^[A-Za-z0-9_][A-Za-z0-9._-]*$`), the set of directories the generator itself visits; on the narrow route the item's own `work/<slug>/index.md` is the only per-item index allowed. `SLUG_RE` still governs the slug a tap may name, is checked before any path is judged, and is not the test for a generated path (D4). | 3 (the allowlist names every generated index) and 4 (nothing else becomes committable) | `Commit::test_generated_indexes_of_any_item_are_allowed` — with `work/other/index.md`, `work/_example/index.md` and `work/index.md` changed, `unexpected_paths("demo", wide=True)` is `[]`. `Commit::test_a_foreign_index_is_a_stray_on_the_narrow_route` — same tree, `unexpected_paths("demo")` (narrow by default) is `["work/_example/index.md", "work/other/index.md"]`. `Commit::test_index_lookalikes_are_stray` — `index.md` at the root, `work/other/sub/index.md`, `work/.hidden/index.md`, `work/other/index.md.orig` and `work/other/intent.md` are each returned on either route, sorted. `Commit::test_a_traversing_slug_is_refused_on_a_clean_tree` — `unexpected_paths("..")` on a clean tree raises `SystemExit` naming `work/<slug>/`; mutation-tested red by removing the up-front `allowed_paths` call. |
| R-4 | The stray-path guard keeps its strength. A path outside the allowlist for the route still aborts the commit, is named in the refusal, and the regenerated indexes do not mask it. | 4 | The existing `Commit::test_a_stray_path_aborts_the_commit`, `test_a_stray_path_is_named_in_the_refusal` and `test_another_items_files_are_a_stray_path` pass unmodified; `Commit::test_a_stray_beside_regenerated_indexes_still_aborts` — approve `demo`, add `scripts/sneaky.py`: `commit()` returns 1, `HEAD` is unchanged, and the refusal on stderr names `scripts/sneaky.py` and no index path. |
| R-5 | A run in which the approval wrote nothing makes no commit, even when regeneration changed an index. The nothing-staged refusal judges the non-generated paths before anything is staged: if every reported path is a generated index, `--commit` prints `approve-dispatch: nothing staged; approve.py wrote no change (only generated indexes changed: <sorted paths>)` and returns 1 with `HEAD` unchanged and the index empty (D3). | 4 (the tap's commit is an approval record, never an index-only commit under approval trailers) | The existing `Commit::test_nothing_to_stage_is_refused` passes unmodified on the unchanged fixture, whose `init` commit carries no index (G-3); `Commit::test_index_only_changes_do_not_make_a_commit` — fixture with a stale `work/other/index.md` committed and no approval written, wide route: `commit()` returns 1, `HEAD` unchanged, `git diff --cached --name-only` empty, stderr carries `nothing staged` and `only generated indexes changed: work/other/index.md`. |
| R-6 | The committer's text says what is true. The module docstring's `--commit` paragraph and the comment above `CHAIN_FILES` name the regeneration that happens inside `--commit`, the two generated paths and the two routes; the sentence "gen_index.py's index.md is regenerated in the same tree" is gone. | 3 (the comment names the regeneration that happens) | `grep -c "gen_index" scripts/approve_dispatch.py` is at least 3; `grep -c "is regenerated in the same tree" scripts/approve_dispatch.py` is 0; `grep -c "default branch" scripts/approve_dispatch.py` is at least 2 (docstring and the ref decision's comment). |
| R-7 | Everything the run trusts is unchanged: `.github/workflows/approve.yml`, `scripts/approve.py` and `scripts/gen_index.py` are byte-identical to `main`; no dependency is added (`json` is stdlib; `gen_index.py` and the two kit modules it imports are stdlib only); `check_actor`'s behaviour is unchanged, with its default-branch comparison extracted to the shared `is_default_branch` (R-11); `SLUG_RE` is untouched; `main()` threads the already-parsed `--ref` and `--default-branch` into `commit()` so the CLI has one spelling of "which ref". | intent Constraints (one checkout, no head code, no dependency, `approve.py` untouched) | `git diff origin/main --name-only` lists only `scripts/approve_dispatch.py`, `scripts/test_approve_dispatch.py` and this item's `work/approve-tap-regenerates-index/**`; every pre-existing case in `ActorCheck`, `Mode` and `SlugContainment` passes unmodified; `Commit::test_cli_threads_ref_and_default_branch_into_commit` — `main(["--commit", ..., "--ref", "work/x", "--default-branch", "main"])` with `commit` patched records `ref="work/x"`, `default_branch="main"`; `python3 scripts/check_artifact_chain.py --base origin/main --slug approve-tap-regenerates-index` ends `CHAIN: PASS`. |
| R-8 | The run log shows what was regenerated and what was left. After rendering, `--commit` prints on stdout, in this order as they apply: `approve-dispatch: regenerated <n> index file(s): <sorted relpaths>` when at least one file's bytes changed, else `approve-dispatch: indexes already up to date`; and, on the narrow route when a rendered path it may not write differs from disk, `approve-dispatch: left <n> stale index file(s) unwritten on this ref: <sorted relpaths>`. Stdout of the Commit step is the workflow's run log. | 1 (observable from the run) | The three shapes are asserted verbatim: the first in R-1's and R-2's wide case (which pins the sort), the second in R-1's second `regenerate`, the third in R-2's narrow case. R-5's case asserts the first shape with `1 index file(s): work/other/index.md`. |
| R-9 | The whole loop is green with the new cases counted: `scripts/verify.sh` ends `VERIFY: PASS`, `python3 scripts/check_artifact_chain.py --base origin/main --slug approve-tap-regenerates-index` ends `CHAIN: PASS`, `scripts/run_evals.sh` ends `0 fail`, `python3 scripts/check_okf.py` ends `0 warnings`, and both generators report up to date. | 5 | The last lines, pasted in the pull request; `python3 scripts/run_tests.py -p test_approve_dispatch.py` reports 26 cases before the item and 41 after (fifteen new; two added by the second review round, R-10 and R-11). |
| R-10 | A rename is judged at both ends. A porcelain `R`/`C` entry (`R  old -> new`) contributes both `old` and `new` to the judged list, so a source outside the allowlist is a stray and refuses the commit as any other stray does; the staged list keeps one entry per porcelain line, the destination, because git already holds the source's deletion in the index and `git add` on a vanished path exits 128. | 4 (nothing else becomes committable) | `Commit::test_a_rename_source_is_judged_too` — commit `.sdlc/approvers.yaml` exists in the fixture; `git mv .sdlc/approvers.yaml work/demo/index.md`; approve `demo`; `commit()` returns 1, `HEAD` unchanged, the refusal names `.sdlc/approvers.yaml`. Red before the revision (the source was dropped; reproduced by both reviewers). `Commit::test_a_rename_within_the_allowlist_stages_its_destination` — `git mv work/demo/intent.md work/demo/plan.md`, write `log.md`, `commit(artifact="plan.md")` returns 0 and `git ls-files` shows `plan.md` and `log.md` and no `intent.md`; with the staged list replaced by the judged list this is the exit-128 `SystemExit` revision 1 reproduced (second review round). |
| R-11 | **The route is decided from runner-set values, one predicate, fail narrow.** `commit()` takes `ref` and `default_branch`; when either is not given it reads `GITHUB_REF` (the full `refs/heads/<name>`, whose prefix disambiguates a branch literally named `refs/heads/main`; the second review round), then `GITHUB_REF_NAME`, and the JSON at `GITHUB_EVENT_PATH` (`repository.default_branch`, the field the workflow's role gate already reads as `github.event.repository.default_branch`, and the field `delegated_merge.py:892` reads from the same file). The wide route needs `is_default_branch(ref, default_branch)` (accepts `<name>` and `refs/heads/<name>`, shared with `check_actor`) and `GITHUB_REF_TYPE`, when set, equal to `branch`. An unset or empty variable, an unreadable file, JSON that does not parse or nests past the recursion limit, a non-object top level or `repository`, or a `default_branch` that is not a non-empty string all yield `None`, and `None` takes the narrow route. | 2, and intent Constraints (nothing the run trusts changes) | `Commit::test_unknown_ref_takes_the_narrow_route` — stale foreign index, `commit()` with no `ref`/`default_branch` and the three variables unset: returns 0, `HEAD` does not name `work/other/index.md`, the `left 1 stale index file(s) unwritten` line prints. `Commit::test_a_malformed_event_payload_takes_the_narrow_route` — `GITHUB_REF_NAME=main`, `GITHUB_EVENT_PATH` pointing in turn at a missing file, a file of `not json`, `{"repository": 7}` and `{"repository": {"default_branch": null}}`: each returns 0 on the narrow route, no exception, no `work/other/index.md` in `HEAD`. `Commit::test_the_runner_variables_take_the_wide_route` — no flags, `GITHUB_REF_NAME=main`, `GITHUB_REF_TYPE=branch` and a payload naming `main`: `route()` is true, `commit()` returns 0 and `HEAD` carries `work/other/index.md`; `refs/heads/main` is also true; `GITHUB_REF_TYPE=tag` is false (second review round: the inputs production uses were untested). `Mode` cases pin `is_default_branch` through `check_actor` unmodified. |

## Design
### Architecture / data flow
One function changes shape. `commit()` in `scripts/approve_dispatch.py` (`:141-164` on `main`) today runs:
stray check → stage the fixed `present` list → nothing-staged check → commit with the split identity
and the two trailers. It becomes:

1. **Decide the route.** `wide = is_default_branch(ref, default_branch) and ref_type_ok`, with `ref`,
   `default_branch` and the ref type resolved as R-11 says. Wide means the tap may write and stage any
   generated index; narrow means only `work/<slug>/index.md` and `work/index.md`.
2. **Regenerate.** `root = gen_index.resolve_root(root)` (the caller's `--root`, else the git toplevel:
   the workflow's Commit step runs from the checkout root with no `--root`, `approve.yml:126-131`). For
   each `(relpath, content)` in `gen_index.render_all(root)`, compare `content.encode("utf-8")` with the
   bytes on disk (CRLF folded to LF, as `gen_index.py:274` does). When they differ and the route's
   write predicate accepts the path, write it with `open(full, "w", encoding="utf-8", newline="\n")`,
   the generator's own call at `gen_index.py:287`; when they differ and the predicate rejects it, leave
   it and remember it. Print the R-8 lines.
3. **One status run, two lists.** `changed_paths(root)` returns the judged list (both ends of a rename or
   copy entry) and the staged list (one entry per porcelain line, the destination of a rename).
4. **Stray check.** `unexpected_paths(slug, root, changed=<judged list>, wide=wide)`: the slug is
   validated first (`allowed_paths`, which refuses a traversing slug whatever the tree holds), then each
   judged path against `is_allowed(path, slug, allowed, wide)`. Any refused path aborts with the existing
   message and exit 1; the regenerated files stay in the runner's tree, which the run then discards.
5. **Nothing-staged check.** The staged list minus every generated index. Empty means the approval
   wrote nothing: print the refusal with its cause (R-5), return 1 before anything is staged.
6. **Stage** exactly the staged list with `git add -- <paths>`, then the existing belt check that
   something is in the index.
7. **Commit** exactly as today: subject `[<slug>] Approve <artifact> as <actor>`, optional note, the
   `Approved-Run` and `Approved-Actor` trailers, author the actor, committer the bot.

Nothing upstream moves: `check_actor` and the Approve step run before `--commit` as before, and the
workflow's `git push origin HEAD:$REF` follows it as before.

### Interfaces (APIs, events, schemas) — exact shapes
- `is_default_branch(ref, default_branch) -> bool`: true when `default_branch` is non-empty and `ref` is
  `default_branch` or `refs/heads/<default_branch>`. `check_actor`'s comparison (`:107` on `main`) calls
  it; its two accepted spellings are pinned by the existing `Mode` cases.
- `event_default_branch(path=None) -> str | None`: reads `path` or `GITHUB_EVENT_PATH`; returns
  `repository.default_branch` when it is a non-empty string, else `None`, never raising on a missing or
  malformed file (R-11).
- `route(ref=None, default_branch=None) -> bool`: `ref` falls back to `GITHUB_REF`, then
  `GITHUB_REF_NAME`; `default_branch` to `event_default_branch()`; `False` unless `is_default_branch`
  holds and `GITHUB_REF_TYPE` is unset or `branch`.
- `is_generated_index(path) -> bool`: `path == "work/index.md"` or `INDEX_RE.fullmatch(path)`, with
  `INDEX_RE = re.compile(r"work/([A-Za-z0-9_][A-Za-z0-9._-]*)/index\.md")`. The segment class is the
  generator's, not the tap's: `gen_index._work_items` renders every directory under `work/`
  (`gen_index.py:118-125`), `_example` included, and `SLUG_RE` rejects a leading `_` (D4). A leading dot
  is excluded so `.`, `..` and `.git` never match.
- `own_index(path, slug) -> bool`: `path in {f"work/{slug}/index.md", "work/index.md"}`.
- `is_allowed(path, slug, allowed=None, wide=False) -> bool`: `path in allowed_paths(slug)`, or
  `own_index`, or, when `wide`, `is_generated_index`.
- `changed_paths(root=None) -> (judged, staged)`: two sorted lists from one `git status --porcelain
  --untracked-files=all`; a rename or copy entry (status code carrying `R` or `C`) contributes both ends
  to `judged` and its destination to `staged`; every other entry contributes its path to both, a literal
  ` -> ` in a plain filename included (git does not quote that sequence; the second review round).
- `unexpected_paths(slug, root=None, changed=None, wide=False) -> list[str]`: `allowed_paths(slug)`
  first (its `SystemExit` for a traversing slug), then the judged paths (from `changed`, else a fresh
  `changed_paths(root)[0]`) that `is_allowed` rejects, sorted.
- `regenerate(root=None, writable=None) -> (written, skipped)`: two sorted lists of relpaths whose bytes
  differ, split by whether `writable(relpath)` accepted them (`None` accepts everything); writes the
  first list; prints the R-8 lines. Raises whatever `render_all` or `open` raises.
- `commit(slug, actor, run_id, artifact=None, note="", root=None, identity=None, ref=None, default_branch=None) -> int`.
- `main()`: `--commit` passes `--ref` and `--default-branch` through to `commit()`; no new flag.
- Stdout lines: `approve-dispatch: regenerated <n> index file(s): <p1>, <p2>`; `approve-dispatch: indexes
  already up to date`; `approve-dispatch: left <n> stale index file(s) unwritten on this ref: <p1>, <p2>`.
- Stderr refusals: `approve-dispatch: refusing to commit; an approval may not touch: <strays>` unchanged;
  `approve-dispatch: nothing staged; approve.py wrote no change (only generated indexes changed: <paths>)`
  on the index-only case; the belt check keeps the bare `nothing staged; approve.py wrote no change`.
- `CHAIN_FILES` keeps `index.md`; the comment above it and the docstring's `--commit` paragraph name the
  regeneration, the two paths and the two routes.
- New reads of the environment: `GITHUB_REF_NAME`, `GITHUB_REF_TYPE`, `GITHUB_EVENT_PATH`, all set by the
  runner, none by a caller. No new flag, workflow input, workflow step, front-matter key, or file outside
  the two.

### Data and migrations
None. The committer writes generated Markdown whose content is a pure function of tracked front matter
and ledger lines already on the ref. No field is added; no data classification applies
(security-standards §4: n/a, no new field).

### Failure modes and how they surface
- **Regeneration raises.** The probe shows `gen_index` never raises on content: an unterminated front-matter
  block, a ledger line that does not parse, a file with no front matter and an item directory with no
  `intent.md` all render (with empty cells) and exit 0 (G-1). What can raise is the tree: an unwritable
  file or directory (`OSError`) or a `work/` that is not a directory. The exception propagates out of
  `commit()` before any `git add`, `--commit` exits non-zero with the traceback in the run log, the Commit
  step fails before its `git push`, and the runner's tree is discarded. Nothing lands.
- **The route cannot be decided.** Every malformed or missing input to R-11 yields `None` from the
  readers and `False` from `route()`, the narrow route; nothing raises. The tap then behaves as before this item for foreign indexes (leaves them) and
  as R-1 for its own. The `left ... unwritten` line says so in the run log.
- **A stray path.** Refused as today, naming the stray and only the stray (R-4). On the narrow route a
  foreign index dirtied by anything at all is such a stray (R-3). The regenerated files are in the
  discarded tree.
- **Only indexes changed.** Refused before staging (R-5, D3), with the cause in the message.
- **A rename with a source outside the allowlist.** Refused (R-10); a rename within the allowlist stages
  its destination only, which git accepts.
- **A generated index the write predicate rejects.** Left unwritten and reported (R-8), never refused as a
  stray the tap itself created; on the wide route only a dot-directory could produce one, on the narrow
  route every foreign index does.

**Security standards, rule by rule** (the reviewer checklist the skill asks for):
1. Secrets — n/a: no secret is read or written; the event payload holds none and only one field is read.
2. Auth — n/a, no endpoint: the role gate is `check_actor` and its behaviour does not change; the identity
   written to the commit is still the run's actor.
3. Input — the slug is schema-checked by `SLUG_RE` before any path is judged; the generated-index
   predicate is a `fullmatch` over the paths `git status --porcelain` reports; the ref decision reads
   three runner-set variables and one JSON field, each validated for shape and failing narrow; every git
   call is an argv list, never a shell string; nothing is interpolated into a command.
4. Data — n/a, no new field (Data and migrations).
5. Dependencies — none added: `json` is stdlib; `gen_index.py` imports `argparse`, `os`, `subprocess`,
   `sys`, `datetime` and the kit's own `check_artifact_chain` and `log_ledger`.
6. Infra — no path under `RELEASE_GATED_PATHS`; the workflow file is untouched (R-7).
7. Logging — the R-8 lines carry repository-relative paths only.
8. Agent hygiene — the writer of this item does not sign off its review: `/sdlc-review` runs
   `plan-reviewer` and `security-reviewer` on a different model where one is available, both read-only;
   revision 1's two sections were written by those reviewers on Opus against a Fable writer.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the committer becomes a writer as well as a stager, which `approve-by-dispatch.md` decision 6 (D6:
  "the committer refuses to stage any path outside work/<slug>/ and .sdlc/active") did not foresee —
  policy: `knowledge/decisions/approve-by-dispatch.md` — contradiction? no — owner: luissiviero —
  resolution: the owner chose this route in the intent's first open question (2026-09-08); the refusal set
  D6 describes widens by the generated paths, on the default branch only, each of which is a function of
  content already on the ref, and the widening carries positive and negative tests on both routes (R-3).
- C2: a `contents: write` run on the default branch commits files derived from other items' front matter
  and ledgers, not only the item being approved — policy: `.github/workflows/approve.yml` header ("the
  committer refuses to stage any path outside work/<slug>/ and .sdlc/active") — contradiction? the header
  sentence becomes imprecise for `main` — owner: luissiviero — resolution: accepted in the intent's second
  open question; the only way to change a generated index is to change a tracked artifact or ledger,
  which needs its own commit on the ref. The header sentence lives in a protected file this item may not
  edit; it is reported in the pull request for the owner, and `approve_dispatch.py`'s own text is
  corrected here (R-6).
- C3: the allowlist judges "an item" by two spellings: `SLUG_RE` for the slug a tap names, and the
  generator's directory class for a generated index — policy:
  `knowledge/lessons/one-path-spelling-in-guards.md` — contradiction? no — owner: luissiviero —
  resolution: the two answer different questions (may a tap name this item, versus did the generator
  write this file); both classes are pinned by tests, and the D4 comment says why they differ. The
  default-branch comparison, by contrast, has one spelling shared with `check_actor` (R-11).
- C4: on a non-default ref the committer that runs is the branch's own copy of `approve_dispatch.py`, so
  the narrow route is a chain-check correctness guard, not a boundary against a hostile branch — policy:
  `knowledge/decisions/approve-by-dispatch.md` — contradiction? no — owner: luissiviero — resolution:
  the boundary is that a grant lands only on the default branch (`check_actor`, R-8 of that decision) and
  that a supervised approval on a branch is reviewed with the branch; stated so a later reader does not
  over-trust the route.

## Open questions carried from intent.md
- None unresolved. Both of the intent's questions were answered by the owner on 2026-09-08 and are the
  basis of this design: the regeneration lives inside `--commit` (D1), and a tap on `main` commits every
  index it regenerates rather than refusing on, or staging around, another item's drift (D2, R-2). The
  first review round found the spec had generalised the second answer from `main` to any ref; revision 1
  restored the intent's own scope.

## Decisions (ADR-style: context → decision → consequences)
- D1: **Call the renderer, write locally, and let `--check` be the arbiter of byte-identity.** Context: the
  intent requires the generator's own renderer, never a second one; `gen_index.py` exposes `render_all`
  but keeps its write loop inside `main()`, which calls `sys.exit`. Decision: `approve_dispatch` imports
  `gen_index`, calls `render_all`, and writes with the same `open(..., encoding="utf-8", newline="\n")`;
  `gen_index.py` is not edited. Consequence: the file list stays at the two code files; the rendering is
  shared, the four-line write is not, and R-1's `gen_index.py --check` on the committed tree proves the
  two write routes agree every time the suite runs.
- D2: **Regenerate before the stray check, and heal foreign drift only on the default branch.** Context:
  the intent wants a tap on `main` to heal drift found there; `own_artifact` in the chain check counts
  only the item's own directory and `work/index.md` as its files, so a foreign index in a work branch's
  diff selects strict mode and fails the branch's pull request (revision 1, reproduced by both reviewers).
  Decision: render first, then judge the whole tree; write and allow foreign indexes only when the run is
  on the default branch. Consequence: a tap on `main` leaves `main` `INDEX: up to date`; a tap on a branch
  never widens the branch's diff beyond the item's own files; refusing on drift, staging around it, and
  editing `own_artifact` (a `locked-paths` file) were all rejected.
- D3: **An index-only diff is not a commit.** Context: the fixture's `init` commit carries no index (G-3),
  so after D2 every `commit()` call finds two new files, and `test_nothing_to_stage_is_refused` would flip
  green-to-red unless the refusal ignores generated paths. Decision: the nothing-staged check subtracts
  generated indexes and runs before staging. Consequence: the tap's commit always records an approval the
  trailers can vouch for; the existing case passes unmodified; the index is empty on refusal.
- D4: **The generated-index predicate follows the generator's directory class, not `SLUG_RE`.** Context:
  `gen_index._work_items` renders every directory under `work/` and `main` tracks `work/_example/index.md`;
  `SLUG_RE` refuses a leading `_` because a tap must never name paths outside one item. Decision: a
  segment with no leading dot, one level deep, ending `/index.md`. Consequence: a stale `_example` index
  heals like any other on `main`; `.`/`..`/`.git` are excluded by the same rule that excludes them from
  slugs; C3 records the two spellings and the tests pin both.
- D5: **One `git status`, two lists.** Context: the first build ran `git status` twice and judged only a
  rename's destination, so a staged rename could delete a path outside the allowlist under the approver's
  authorship (revision 1, the security pass's Major). Decision: `changed_paths` returns a judged list with
  both ends of a rename and a staged list with one entry per porcelain line; the guard reads the first,
  `git add` the second. Consequence: the guard and the staging read the same run; a source outside the
  allowlist is a stray; a rename within it stages without `git add` failing on the vanished source.
- D6: **The route is decided from runner-set values, with one predicate and a narrow fallback.** Context:
  the Commit step's environment carries the ref but not the default branch, and adding it means editing a
  protected file; the event payload at `GITHUB_EVENT_PATH` already carries `repository.default_branch`,
  which the role gate and `delegated_merge.py:892` read. Decision: `commit()` takes `ref` and
  `default_branch`, threaded from the CLI's existing flags, and falls back to `GITHUB_REF_NAME`, the
  payload and `GITHUB_REF_TYPE`; every malformed or missing value yields the narrow route; the comparison
  is `is_default_branch`, shared with `check_actor`. Consequence: no workflow change, no new flag, one
  spelling of "which ref", and a spoofed or missing value can only stop a heal, never cause one.
- D7: **The staging predicate is route-scoped, not only the writes.** Context: scoping only what
  `regenerate` writes would leave `is_allowed` willing to stage a foreign index on a side branch if
  anything else had dirtied it, a containment that holds only because a runner checkout is fresh
  (revision 1, both reviewers). Decision: `is_allowed` takes the route; on the narrow route a foreign
  index is a stray. Consequence: the property does not depend on what happens not to exist; R-3 pins it.

## Gotchas found while reading the codebase
- G-1: `gen_index.py` is tolerant by design. Probed on 2026-09-14: an unterminated front-matter block
  parses as the keys seen so far (`front_matter` returns `{'status': 'in-review', 'title': '[unterminated'}`),
  a ledger line that does not parse is dropped by `log_ledger.parse`, a file with no front matter renders
  empty cells, and a plain file under `work/` is skipped; each exits 0 and writes. So "the generator
  fails" means an `OSError` on the tree, not bad content, and the spec's failure mode says so.
- G-2: `work/_example` is a real, tracked item on `main` (26 `work/*/index.md` files tracked, that one
  among them) and its name fails `SLUG_RE`. A predicate built on `SLUG_RE` would refuse every tap on
  `main` the moment that one index drifted, with a message naming a file no tap wrote (D4).
- G-3: `make_repo` in `test_approve_dispatch.py` commits `.sdlc/active` and `work/demo/intent.md` and no
  index. After D2 every `commit()` in the suite renders two new untracked files, so the fixture is what
  forces D3; `--untracked-files=all` already lists a new file inside an existing directory one path at a
  time.
- G-4: `test_active_and_index_are_allowed` writes `# index\n` to `work/demo/index.md` and asserts only
  that the path is in the commit. Regeneration overwrites its content, and the assertion still holds, so
  the case passes unmodified; it is not a byte-identity test and R-1 adds the one that is.
- G-5: the import chain `approve_dispatch → gen_index → check_artifact_chain, log_ledger` reaches a
  `locked-paths` file, `scripts/check_artifact_chain.py`, for its `front_matter` reader only. Importing
  does not modify it; its one import-time side effect is `git rev-parse --show-toplevel` from the process
  cwd (`:52`), unused by `front_matter`. `delegated_merge.py`'s locked-path floor compares bytes on the
  head, so the pull request stays mergeable by the workflow.
- G-6: `commit()` is given `root=None` in production (the Commit step passes no `--root`), and every
  existing `git()` call already relies on `cwd=None` meaning the checkout root. `gen_index.resolve_root(None)`
  returns the git toplevel, which is the same directory, so the fixture (`--root <tmp>`) and the runner
  take the same code path.
- G-7: the drift the intent scoped out (c0aa58c's `work/run-queue-followups/index.md`) is already gone:
  `python3 scripts/gen_index.py --check` on `main` at 864923e prints `INDEX: up to date`, healed by the
  agent commits and the clean-up pull requests (#78, #80, #81) the handoff records. There is nothing stale
  for this item's pull request to report.
- G-8: the 2026-09-14 taps repeat the shape exactly: `b30feff` (`advance-push`, on `main`) committed two
  paths, `70437ab` (`approve-tap-regenerates-index`, a grant on `main`) three, no index in either; the
  two clean-ups took two pull requests (#80, #81) because the chain check reads one work item at a time.
  R-2's heal removes that pair from every future tap on `main`, which is where both of these were; a tap
  on a work branch leaves a foreign index stale, which is what the chain check requires of the branch.
- G-9: `run-name`, the role gate and the slug resolution run before the Approve step and do not read the
  tree's indexes, so nothing this item changes can alter which actor, slug or artifact a run records.
- G-10: `own_artifact` (`check_artifact_chain.py:645-648`) is the rule that makes a foreign index poison a
  branch's pull request, and the lesson `knowledge/lessons/human-commits-leave-indexes-stale.md` already
  says "the regeneration must ride under the item whose index it is"; the first signed R-2 contradicted
  both, and the intent's own wording ("When main already carries") never did.
- G-11: the workflow's Commit step has `REF` in its environment but not the default branch; only the role
  gate's step has `DEFAULT_BRANCH`. The runner sets `GITHUB_REF_NAME`, `GITHUB_REF_TYPE` and
  `GITHUB_EVENT_PATH` for every step, and `delegated_merge.py:1141-1142,892` already reads the default
  branch from that file, so the committer can decide the route without a workflow change (D6).
- G-12: `git status --porcelain` renders a staged rename as `R  old -> new` and never shows an unstaged
  one; `git add -- old` on the vanished source exits 128 with `pathspec ... did not match`, which
  `git(check=True)` turns into a `SystemExit` (revision 1). Hence two lists (D5).

## Not doing
- A regeneration step in `.github/workflows/approve.yml`: rejected by the owner in the intent (a protected
  path forces the label, the click, and the end of the queue). The header sentence there that C2 finds
  imprecise is reported in the pull request, not edited. Likewise a workflow input or env line for the
  default branch: the runner already provides it (D6).
- Widening `own_artifact` in `scripts/check_artifact_chain.py` to accept `work/*/index.md`: a
  `locked-paths` file, and its one-item-per-pull-request rule is what the lesson relies on.
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
